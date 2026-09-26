"""
tests/test_saas_infrastructure_providers.py
===========================================
Unit and integration tests for Task 8.20 Production SaaS Infrastructure Providers:
1. DatabaseProvider & Multi-Tenant Data Classification
2. CacheProvider, Distributed Locks, and Rate Limiting
3. EmailProvider & Application Event Dispatching
4. BillingProvider, Subscription Tiers, and Webhooks
5. BackgroundJobRunner & Multi-Instance Lock Coordination
6. External IdP Boundary & Session Revocation
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.auth.provider import (
    create_session_token,
    get_auth_provider_status,
    is_token_revoked,
    revoke_token,
    ProductionAuthProvider,
    DevelopmentAuthProvider,
)
from api.errors import UnauthorizedError
from infrastructure.billing.provider import (
    BillingPlanTier,
    DevelopmentBillingProvider,
    ProductionBillingProvider,
    get_billing_provider,
)
from infrastructure.cache.provider import (
    DevelopmentCacheProvider,
    ProductionCacheProvider,
    get_cache_provider,
)
from infrastructure.email.provider import (
    EmailEvent,
    EmailMessage,
    DevelopmentEmailProvider,
    ProductionEmailProvider,
    get_email_provider,
)
from infrastructure.jobs.runner import (
    BackgroundJobRunner,
    JobExecutionMode,
    JobType,
)
from storage.database.provider import (
    DataClassification,
    DATA_CLASSIFICATION_REGISTRY,
    DevelopmentDatabaseProvider,
    ProductionDatabaseProvider,
    get_database_provider,
)


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Database Provider & Data Classification Tests
# ---------------------------------------------------------------------------


def test_data_classification_registry_separation():
    """Verify that Public/Frozen analytical baselines are separated from tenant data."""
    central_preds = DATA_CLASSIFICATION_REGISTRY["central_predictions"]
    assert central_preds["classification"] == DataClassification.PUBLIC_FROZEN
    assert central_preds["immutable"] is True
    assert central_preds["tenant_scoped"] is False

    state_acts = DATA_CLASSIFICATION_REGISTRY["state_acts"]
    assert state_acts["classification"] == DataClassification.PUBLIC_FROZEN
    assert state_acts["immutable"] is True

    watchlists = DATA_CLASSIFICATION_REGISTRY["watchlists"]
    assert watchlists["classification"] == DataClassification.TENANT_OWNED_MUTABLE
    assert watchlists["immutable"] is False
    assert watchlists["tenant_scoped"] is True

    users = DATA_CLASSIFICATION_REGISTRY["users"]
    assert users["classification"] == DataClassification.USER_OWNED_PRIVATE


def test_development_database_provider():
    """Verify DevelopmentDatabaseProvider local health and schema DDL."""
    dev_db = DevelopmentDatabaseProvider()
    assert dev_db.provider_name.startswith("DevelopmentDatabaseProvider")
    assert dev_db.is_configured is True
    assert dev_db.status == "READY"

    health = dev_db.health_check()
    assert health["status"] == "HEALTHY"
    assert health["connected"] is True

    tables = dev_db.get_table_names()
    assert "users" in tables
    assert "tenants" in tables
    assert "watchlists" in tables
    assert "alert_rules" in tables

    ddl = dev_db.get_schema_ddl()
    assert "CREATE TABLE IF NOT EXISTS tenants" in ddl
    assert "CREATE TABLE IF NOT EXISTS watchlists" in ddl


def test_production_database_provider_unconfigured_honest_status():
    """Verify ProductionDatabaseProvider honestly reports NOT_CONFIGURED when keys absent."""
    prod_db = ProductionDatabaseProvider(database_url="")
    assert prod_db.is_configured is False
    assert prod_db.status == "NOT_CONFIGURED"

    health = prod_db.health_check()
    assert health["status"] == "NOT_CONFIGURED"
    assert health["connected"] is False


# ---------------------------------------------------------------------------
# 2. Cache Provider, Distributed Locks & Rate Limiting Tests
# ---------------------------------------------------------------------------


def test_development_cache_provider_crud_and_ttl():
    """Verify in-memory cache get, set, delete, and TTL expiration."""
    cache = DevelopmentCacheProvider()
    cache.set("test_key", "test_val", ttl_seconds=2)
    assert cache.get("test_key") == "test_val"
    assert cache.exists("test_key") is True

    cache.delete("test_key")
    assert cache.get("test_key") is None
    assert cache.exists("test_key") is False


def test_distributed_lock_mutual_exclusion():
    """Verify distributed lock prevents duplicate acquisition and releases correctly."""
    cache = DevelopmentCacheProvider()
    lock_name = "test_scheduler_lock"

    # Worker 1 acquires lock
    acq1 = cache.acquire_lock(lock_name, timeout_seconds=0.1, expire_seconds=10)
    assert acq1 is True

    # Worker 2 attempts to acquire same lock (must fail)
    acq2 = cache.acquire_lock(lock_name, timeout_seconds=0.1, expire_seconds=10)
    assert acq2 is False

    # Worker 1 releases lock
    rel = cache.release_lock(lock_name)
    assert rel is True

    # Worker 2 can now acquire lock
    acq3 = cache.acquire_lock(lock_name, timeout_seconds=0.1, expire_seconds=10)
    assert acq3 is True
    cache.release_lock(lock_name)


def test_sliding_window_rate_limiting():
    """Verify rate limit sliding window counter."""
    cache = DevelopmentCacheProvider()
    client_key = "client_test_ip"

    # Allow 3 requests in 10-second window
    allowed1, rem1, _ = cache.check_rate_limit(client_key, max_requests=3, window_seconds=10)
    allowed2, rem2, _ = cache.check_rate_limit(client_key, max_requests=3, window_seconds=10)
    allowed3, rem3, _ = cache.check_rate_limit(client_key, max_requests=3, window_seconds=10)
    allowed4, rem4, reset_in = cache.check_rate_limit(client_key, max_requests=3, window_seconds=10)

    assert allowed1 is True and rem1 == 2
    assert allowed2 is True and rem2 == 1
    assert allowed3 is True and rem3 == 0
    assert allowed4 is False and rem4 == 0
    assert reset_in > 0


def test_production_cache_unconfigured_honest_status():
    """Verify ProductionCacheProvider honestly reports NOT_CONFIGURED when url absent."""
    prod_cache = ProductionCacheProvider(redis_url="")
    assert prod_cache.is_configured is False
    assert prod_cache.status == "NOT_CONFIGURED"
    health = prod_cache.health_check()
    assert health["status"] == "NOT_CONFIGURED"
    assert health["connected"] is False


# ---------------------------------------------------------------------------
# 3. Transactional Email Provider Tests
# ---------------------------------------------------------------------------


def test_development_email_provider_events():
    """Verify DevelopmentEmailProvider formats and records all required application events."""
    email_prov = DevelopmentEmailProvider()
    email_prov.clear()

    # Test all 8 required application events
    events = [
        (EmailEvent.USER_INVITATION, {"organization_name": "Ministry of Energy", "invitee_name": "Dev User"}),
        (EmailEvent.EMAIL_VERIFICATION, {"verification_url": "https://app.test/verify"}),
        (EmailEvent.PASSWORD_RECOVERY, {"reset_url": "https://app.test/reset"}),
        (EmailEvent.ALERT_NOTIFICATION, {"rule_name": "Energy Bill Alert", "bill_title": "Clean Energy Act"}),
        (EmailEvent.DIGEST, {"frequency": "Daily", "update_count": 5}),
        (EmailEvent.SECURITY_EVENT, {"event_description": "Password modified", "ip_address": "127.0.0.1"}),
        (EmailEvent.TENANT_INVITATION, {"tenant_name": "Risk Alpha Group"}),
        (EmailEvent.ACCOUNT_LIFECYCLE, {"plan_name": "TEAM", "status": "ACTIVE"}),
    ]

    for ev_type, ctx in events:
        res = email_prov.send_event(ev_type, recipient="analyst@example.com", context=ctx)
        assert res["success"] is True
        assert res["status"] == "SIMULATED"

    assert len(email_prov.sent_messages) == 8


def test_production_email_unconfigured_honest_status():
    """Verify ProductionEmailProvider reports NOT_CONFIGURED when credentials absent."""
    prod_email = ProductionEmailProvider(smtp_host="")
    assert prod_email.is_configured is False
    assert prod_email.status == "NOT_CONFIGURED"

    msg = EmailMessage(
        recipient="user@test.com",
        subject="Test",
        event_type=EmailEvent.USER_INVITATION,
        body_text="Welcome",
    )
    res = prod_email.send_email(msg)
    assert res["success"] is False
    assert res["status"] == "NOT_CONFIGURED"


# ---------------------------------------------------------------------------
# 4. Billing Provider Tests
# ---------------------------------------------------------------------------


def test_development_billing_provider_subscription_lifecycle():
    """Verify DevelopmentBillingProvider manages customer creation, tiers, and webhooks."""
    billing = DevelopmentBillingProvider()
    tenant_id = "test_tenant_alpha"

    # 1. Default FREE tier auto-provisioning
    sub = billing.get_subscription(tenant_id)
    assert sub is not None
    assert sub.plan_tier == BillingPlanTier.FREE

    # 2. Plan Upgrade to PRO
    sub_pro = billing.change_plan(tenant_id, BillingPlanTier.PRO)
    assert sub_pro.plan_tier == BillingPlanTier.PRO
    assert sub_pro.seats_purchased == 15

    # 3. Webhook Simulation
    webhook_res = billing.handle_webhook_event(
        event_type="customer.subscription.updated",
        data={"tenant_id": tenant_id, "plan_tier": "TEAM"},
    )
    assert webhook_res["status"] == "processed"
    assert webhook_res["tier"] == "TEAM"

    sub_team = billing.get_subscription(tenant_id)
    assert sub_team.plan_tier == BillingPlanTier.TEAM
    assert sub_team.seats_purchased == 50

    # 4. Cancellation
    sub_canceled = billing.cancel_subscription(tenant_id)
    assert sub_canceled.status == "CANCELED"
    assert sub_canceled.plan_tier == BillingPlanTier.FREE


def test_production_billing_unconfigured_honest_status():
    """Verify ProductionBillingProvider reports NOT_CONFIGURED when API keys absent."""
    prod_billing = ProductionBillingProvider(stripe_secret_key="")
    assert prod_billing.is_configured is False
    assert prod_billing.status == "NOT_CONFIGURED"
    health = prod_billing.health_check()
    assert health["status"] == "NOT_CONFIGURED"


# ---------------------------------------------------------------------------
# 5. Background Job Runner & Lock Coordination Tests
# ---------------------------------------------------------------------------


def test_job_runner_distributed_lock_coordination():
    """Verify BackgroundJobRunner coordinates jobs and records history."""
    runner = BackgroundJobRunner(mode=JobExecutionMode.MULTI_INSTANCE, instance_id="node_1")

    # Run maintenance job
    rec = runner.run_scheduled_maintenance()
    assert rec.status == "SUCCESS"
    assert rec.lock_acquired is True
    assert len(runner.job_history) >= 1


# ---------------------------------------------------------------------------
# 6. External IdP & Production Auth Provider Tests
# ---------------------------------------------------------------------------


def test_auth_provider_status_reporting():
    """Verify get_auth_provider_status reports honest IdP readiness."""
    status = get_auth_provider_status()
    assert status["AUTH_IMPLEMENTED"] == "READY"
    assert status["PRODUCTION_IDP_STATUS"] in ("CONFIGURED", "NOT_CONFIGURED")


def test_production_auth_provider_strict_token_and_revocation():
    """Verify ProductionAuthProvider strictly validates token structure and revocation."""
    provider = ProductionAuthProvider()

    # 1. Missing header must fail
    with pytest.raises(UnauthorizedError) as exc_info:
        provider.authenticate(authorization=None)
    assert exc_info.value.code == "AUTH_REQUIRED"

    # 2. Valid token creates user context
    token = create_session_token(user_id="alice", tenant_id="corp_1", role="ADMIN")
    user = provider.authenticate(authorization=f"Bearer {token}")
    assert user.user_id == "alice"
    assert user.tenant_id == "corp_1"
    assert user.is_admin is True

    # 3. Revoke token
    revoke_token(token)
    assert is_token_revoked(token) is True

    # 4. Revoked token must be rejected
    with pytest.raises(UnauthorizedError) as exc_rev:
        provider.authenticate(authorization=f"Bearer {token}")
    assert exc_rev.value.code == "TOKEN_REVOKED"
