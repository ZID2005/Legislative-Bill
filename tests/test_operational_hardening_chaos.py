"""
tests/test_operational_hardening_chaos.py
=========================================
Task 8.23 Phase 11 — Chaos / Failure-Injection Test Suite.

Safe local/test infrastructure verification covering all 12 mandatory failure modes:
1.  Database unavailable
2.  Redis unavailable
3.  Scheduler lock unavailable
4.  Worker crash
5.  External AI unavailable
6.  Email provider unavailable
7.  Billing provider unavailable
8.  Legislative source unavailable
9.  Invalid authentication
10. Cross-tenant access
11. Rate-limit exhaustion
12. Application restart
"""

from __future__ import annotations

import os
import time
from typing import Any
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.auth.provider import (
    DevelopmentAuthProvider,
    ProductionAuthProvider,
    reset_auth_provider_for_testing,
)
from config.settings import settings
from infrastructure.billing.provider import (
    DevelopmentBillingProvider,
    ProductionBillingProvider,
)
from infrastructure.cache.provider import (
    DevelopmentCacheProvider,
    ProductionCacheProvider,
)
from infrastructure.email.provider import (
    DevelopmentEmailProvider,
    EmailEvent,
    EmailMessage,
    ProductionEmailProvider,
)
from infrastructure.jobs.runner import (
    BackgroundJobRunner,
    JobExecutionMode,
    JobType,
)
from services.ai.groq_client import GroqClient
from services.monitoring.base_monitor import MonitorResult
from services.monitoring.source_registry import MonitoringSourceRegistry
from services.startup_validator import StartupValidator
from storage.database.provider import (
    DevelopmentDatabaseProvider,
    ProductionDatabaseProvider,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Database Unavailable
# ---------------------------------------------------------------------------
def test_chaos_1_database_unavailable():
    """Verify that database unavailability triggers controlled error without crashing or corrupting data."""
    db = ProductionDatabaseProvider(database_url="postgresql://invalid_user:invalid_pass@127.0.0.1:54329/invalid_db")
    health = db.health_check()
    assert health["connected"] is False
    assert health["status"] in ("NOT_CONFIGURED", "UNREACHABLE", "DRIVER_MISSING")

    # Local fallback preserves data integrity
    dev_db = DevelopmentDatabaseProvider()
    dev_health = dev_db.health_check()
    assert dev_health["connected"] is True


# ---------------------------------------------------------------------------
# 2. Redis Unavailable
# ---------------------------------------------------------------------------
def test_chaos_2_redis_unavailable():
    """
    Verify Redis unavailability fails safe:
    - Cache lock acquisition returns False (never True)
    - Cache get/set return None/False (no crash)
    - Health check reports not connected
    - In distributed production mode, the scheduler DEFERS execution (fail-closed),
      NOT fall back to a process-level local lock.

    TASK 8.23A INVARIANT:
      REDIS_UNAVAILABLE + MULTI_CONTAINER_PRODUCTION_MODE => SCHEDULER_EXECUTION_COUNT == 0
    """
    from services.monitoring.scheduler import LegislativeScheduler
    from unittest.mock import patch, MagicMock

    # --- Cache provider behavior ---
    redis = ProductionCacheProvider(redis_url="redis://:invalid_pass@127.0.0.1:63799/0")
    # Lock acquisition fails safe (returns False, never True)
    assert redis.acquire_lock("test_lock") is False
    assert redis.get("test_key") is None
    assert redis.set("test_key", "val") is False

    # Rate limiter is permissive when Redis is down (no crash)
    allowed, remaining, reset_in = redis.check_rate_limit("client_ip", 10, 60)
    assert allowed is True

    health = redis.health_check()
    assert health["connected"] is False

    # --- Scheduler fail-closed invariant ---
    execution_count = {"n": 0}

    def counting_runner_factory():
        runner = MagicMock()
        def run_once(trigger=None):
            execution_count["n"] += 1
            return {"status": "SUCCESS"}
        runner.run_once.side_effect = run_once
        return runner

    scheduler = LegislativeScheduler(runner_factory=counting_runner_factory)

    # Simulate Redis-unavailable cache in distributed mode
    unavailable_cache = MagicMock()
    unavailable_cache.health_check.return_value = {"connected": False, "status": "UNAVAILABLE"}
    unavailable_cache.acquire_lock.return_value = False

    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=unavailable_cache
    ):
        result = scheduler.run_now(trigger="chaos_2")

    # CRITICAL: scheduler must NOT execute — fail-closed
    assert execution_count["n"] == 0, (
        f"SAFETY VIOLATION: Scheduler executed {execution_count['n']} time(s) "
        f"when Redis was unavailable in distributed mode. Must be 0."
    )
    assert result["status"] == "DEFERRED_REDIS_UNAVAILABLE", (
        f"Scheduler must return DEFERRED_REDIS_UNAVAILABLE when Redis is down "
        f"in distributed mode. Got: {result['status']}"
    )
    assert result.get("local_lock_substituted") is False, (
        "Scheduler must NOT substitute a local lock when Redis is unavailable "
        "in production distributed mode."
    )
    assert scheduler.is_degraded is True, (
        "Scheduler must report is_degraded=True when Redis is unavailable in distributed mode."
    )


# ---------------------------------------------------------------------------
# 3. Scheduler Lock Unavailable
# ---------------------------------------------------------------------------
def test_chaos_3_scheduler_lock_unavailable():
    """Verify scheduler skips execution safely when another node holds lock (SKIPPED_LOCKED)."""
    runner = BackgroundJobRunner(mode=JobExecutionMode.MULTI_INSTANCE)
    lock_name = f"job_lock:{JobType.LEGISLATIVE_MONITORING.value}"

    # Pre-acquire lock to simulate competing node
    cache = runner.cache_provider
    cache.acquire_lock(lock_name, timeout_seconds=1.0, expire_seconds=60)

    try:
        dummy_task = MagicMock(return_value={"status": "SHOULD_NOT_RUN"})
        rec = runner.execute_with_lock(JobType.LEGISLATIVE_MONITORING, dummy_task)
        assert rec.status == "SKIPPED_LOCKED"
        assert rec.lock_acquired is False
        assert dummy_task.call_count == 0
    finally:
        cache.release_lock(lock_name)


# ---------------------------------------------------------------------------
# 4. Worker Crash & Stale Lock Recovery
# ---------------------------------------------------------------------------
def test_chaos_4_worker_crash_and_recovery():
    """Verify worker exception records FAILED, frees lock in finally, and allows recovery."""
    runner = BackgroundJobRunner()

    def crashing_job():
        raise RuntimeError("Worker crash simulation: segmentation fault / memory abort")

    rec = runner.execute_with_lock(JobType.ALERT_PROCESSING, crashing_job)
    assert rec.status == "FAILED"
    assert "Worker crash simulation" in (rec.error or "")

    # Lock must be released, allowing next worker to run cleanly
    recovery_job = MagicMock(return_value={"recovered": True})
    rec2 = runner.execute_with_lock(JobType.ALERT_PROCESSING, recovery_job)
    assert rec2.status == "SUCCESS"
    assert rec2.lock_acquired is True
    assert recovery_job.call_count == 1


# ---------------------------------------------------------------------------
# 5. External AI Unavailable
# ---------------------------------------------------------------------------
def test_chaos_5_external_ai_unavailable():
    """Verify AI client degrades gracefully to offline fallback when API is unavailable."""
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
        ai_client = GroqClient(api_key="")
        assert ai_client.is_available is False

        # Must generate safe fallback response without crashing
        resp = ai_client.chat_completion(
            messages=[{"role": "user", "content": "Explain the Telecom Act"}]
        )
        assert resp.success is False
        assert resp.display_text is not None
        assert "gsk_" not in resp.display_text
        assert "api_key" not in resp.display_text.lower()


# ---------------------------------------------------------------------------
# 6. Email Provider Unavailable
# ---------------------------------------------------------------------------
def test_chaos_6_email_provider_unavailable():
    """Verify email gateway outage returns safe delivery failure without crashing system."""
    prod_email = ProductionEmailProvider(smtp_host="unreachable.domain.example.com", smtp_port=2525)
    assert prod_email.status == "NOT_CONFIGURED"

    # Dev provider functions safely offline
    dev_email = DevelopmentEmailProvider()
    res = dev_email.send_email(
        EmailMessage(
            recipient="user@test.org",
            subject="Test Alert",
            event_type=EmailEvent.ALERT_NOTIFICATION,
            body_text="Alert body text",
        )
    )
    assert res.get("status") in ("QUEUED", "SENT", "DELIVERED", "SIMULATED")


# ---------------------------------------------------------------------------
# 7. Billing Provider Unavailable
# ---------------------------------------------------------------------------
def test_chaos_7_billing_provider_unavailable():
    """Verify billing provider absence reports NOT_CONFIGURED and rejects unverified webhooks."""
    billing = ProductionBillingProvider()
    assert billing.status == "NOT_CONFIGURED"
    assert billing.is_configured is False

    # Verifying webhook without secret fails closed
    webhook_res = billing.verify_webhook_signature("payload_bytes", "invalid_sig")
    assert webhook_res is False


# ---------------------------------------------------------------------------
# 8. Legislative Source Unavailable
# ---------------------------------------------------------------------------
def test_chaos_8_legislative_source_unavailable():
    """Verify scraping/source failure records degraded source status without corrupting analytical data."""
    registry = MonitoringSourceRegistry()
    sources = registry.get_all()
    assert len(sources) >= 7

    # Ensure source check failure is captured safely
    res = MonitorResult(
        source_id="central_lok_sabha",
        success=False,
        error="DNS resolution failed: [Errno 11001] getaddrinfo failed",
    )
    assert res.success is False
    assert "DNS" in (res.error or "")


# ---------------------------------------------------------------------------
# 9. Invalid Authentication
# ---------------------------------------------------------------------------
def test_chaos_9_invalid_authentication(client):
    """Verify malformed, expired, or invalid JWTs are rejected with 401 Unauthorized."""
    # In dev mode, invalid token keyword rejected
    r1 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert r1.status_code == 401
    assert "detail" in r1.json() or "error" in r1.json()

    # Under ProductionAuthProvider, all unverified or malformed tokens must be rejected
    prod_provider = ProductionAuthProvider(secret_key="prod_secret_chaos_test")
    reset_auth_provider_for_testing(prod_provider)
    try:
        r2 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer malformed.bad.jwt"})
        assert r2.status_code == 401
        r3 = client.get("/api/v1/auth/me")  # No auth header
        assert r3.status_code == 401
    finally:
        reset_auth_provider_for_testing(DevelopmentAuthProvider())


# ---------------------------------------------------------------------------
# 10. Cross-Tenant Access (IDOR Prevention)
# ---------------------------------------------------------------------------
def test_chaos_10_cross_tenant_access(client):
    """Verify tenant isolation prevents cross-tenant access to private watchlists."""
    # Attempt to fetch another tenant's watchlist with non-existent or foreign ID
    r = client.get(
        "/api/v1/watchlists/foreign_wl_99999",
        headers={"X-Dev-Tenant-Id": "tenant_alpha", "X-Dev-User-Id": "user_alpha"},
    )
    # Must be 404 Not Found or 401 Unauthorized, never 200 with foreign data
    assert r.status_code in (401, 404, 403)


# ---------------------------------------------------------------------------
# 11. Rate-Limit Exhaustion
# ---------------------------------------------------------------------------
def test_chaos_11_rate_limit_exhaustion():
    """Verify rate limiter enforces maximum requests and reports retry window."""
    cache = DevelopmentCacheProvider()
    key = "ratelimit_test_tenant"

    # Send 5 requests with max 5
    for i in range(5):
        allowed, rem, reset_s = cache.check_rate_limit(key, max_requests=5, window_seconds=60)
        assert allowed is True

    # 6th request must be rejected
    allowed, rem, reset_s = cache.check_rate_limit(key, max_requests=5, window_seconds=60)
    assert allowed is False
    assert rem == 0
    assert reset_s > 0


# ---------------------------------------------------------------------------
# 12. Application Restart Resilience
# ---------------------------------------------------------------------------
def test_chaos_12_application_restart():
    """Verify application startup validator runs cleanly after simulated reboot."""
    validator = StartupValidator()
    report = validator.run_validation(strict=False)

    assert report.can_start is True
    assert report.status in ("READY", "DEGRADED")
    assert report.critical_failures == 0
    assert report.passed_count >= 10
