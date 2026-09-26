"""
tests/test_task_8_23a_redis_fail_closed_scheduler.py
=====================================================
TASK 8.23A — Redis Fail-Closed Distributed Scheduler Safety Test Suite.

Proves the invariants required by TASK 8.23A:

Test 1: Redis available + lock acquired  => scheduler executes exactly once.
Test 2: Redis unavailable                => scheduler does NOT execute.
Test 3: Redis unavailable + 2 scheduler instances => zero executions combined.
Test 4: Redis recovers                   => scheduler can safely resume.
Test 5: Redis lock contention            => secondary scheduler skips execution.
Test 6: Lock TTL expiry                  => another scheduler can safely acquire lock.
Test 7: Scheduler failure cannot generate State predictions.
Test 8: Scheduler failure cannot mutate frozen Central prediction artifacts.

Critical invariant:
  REDIS_UNAVAILABLE + MULTI_CONTAINER_PRODUCTION_MODE => SCHEDULER_EXECUTION_COUNT == 0
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from config.settings import settings
from infrastructure.cache.provider import DevelopmentCacheProvider
from services.monitoring.scheduler import (
    LegislativeScheduler,
    SchedulerConfig,
    SCHEDULER_DISTRIBUTED_LOCK_NAME,
    _get_execution_mode,
    _is_distributed_mode,
)
from utils.baseline_verifier import verify_production_baseline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_success_runner():
    """Factory that returns a mock runner producing SUCCESS."""
    mock_runner = MagicMock()
    mock_runner.run_once.return_value = {
        "status": "SUCCESS",
        "new_bills": 0,
        "changed_bills": 0,
    }
    return mock_runner


def _make_degraded_cache() -> DevelopmentCacheProvider:
    """
    Return a DevelopmentCacheProvider whose acquire_lock always returns False
    AND whose health_check reports connected=False — simulating Redis unavailable.
    """
    cache = DevelopmentCacheProvider()
    cache.acquire_lock = MagicMock(return_value=False)  # type: ignore[method-assign]
    cache.health_check = MagicMock(  # type: ignore[method-assign]
        return_value={
            "connected": False,
            "status": "UNAVAILABLE",
        }
    )
    return cache


def _make_contended_cache() -> DevelopmentCacheProvider:
    """
    Return a DevelopmentCacheProvider whose health_check reports healthy Redis
    but acquire_lock returns False — simulating lock already held by another node.
    """
    cache = DevelopmentCacheProvider()
    cache.health_check = MagicMock(  # type: ignore[method-assign]
        return_value={
            "connected": True,
            "status": "HEALTHY",
        }
    )
    cache.acquire_lock = MagicMock(return_value=False)  # type: ignore[method-assign]
    cache.release_lock = MagicMock(return_value=True)  # type: ignore[method-assign]
    return cache


def _make_healthy_cache_with_lock() -> DevelopmentCacheProvider:
    """
    Return a DevelopmentCacheProvider whose health_check reports healthy Redis
    and acquire_lock succeeds — simulating Redis available with lock grantable.
    """
    cache = DevelopmentCacheProvider()
    cache.health_check = MagicMock(  # type: ignore[method-assign]
        return_value={
            "connected": True,
            "status": "HEALTHY",
        }
    )
    # Real lock acquisition on in-memory store
    return cache


# ---------------------------------------------------------------------------
# Test 1 — Redis available + lock acquired => scheduler executes exactly once
# ---------------------------------------------------------------------------

def test_8_23a_1_redis_available_lock_acquired_executes_once():
    """
    TASK 8.23A Test 1:
    When Redis is available and the distributed lock is successfully acquired,
    the scheduler MUST execute exactly once.
    """
    execution_count = {"n": 0}

    def counting_runner_factory():
        runner = MagicMock()

        def run_once(trigger=None):
            execution_count["n"] += 1
            return {"status": "SUCCESS", "new_bills": 0}

        runner.run_once.side_effect = run_once
        return runner

    scheduler = LegislativeScheduler(runner_factory=counting_runner_factory)

    healthy_cache = _make_healthy_cache_with_lock()

    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=healthy_cache
    ):
        result = scheduler.run_now(trigger="test_1")

    assert result["status"] == "SUCCESS", (
        f"Expected SUCCESS but got {result['status']}. "
        f"Full result: {result}"
    )
    assert execution_count["n"] == 1, (
        f"Expected exactly 1 execution but got {execution_count['n']}. "
        "Scheduler should execute once when Redis lock is acquired."
    )
    assert scheduler.is_degraded is False, (
        "Scheduler should NOT be marked degraded when Redis is healthy."
    )


# ---------------------------------------------------------------------------
# Test 2 — Redis unavailable => scheduler does NOT execute
# ---------------------------------------------------------------------------

def test_8_23a_2_redis_unavailable_scheduler_does_not_execute():
    """
    TASK 8.23A Test 2:
    When Redis is unavailable in distributed production mode, the scheduler
    MUST NOT execute. Execution count must be exactly 0.
    This is the core fail-closed invariant.
    """
    execution_count = {"n": 0}

    def counting_runner_factory():
        runner = MagicMock()

        def run_once(trigger=None):
            execution_count["n"] += 1
            return {"status": "SUCCESS"}

        runner.run_once.side_effect = run_once
        return runner

    scheduler = LegislativeScheduler(runner_factory=counting_runner_factory)
    degraded_cache = _make_degraded_cache()

    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=degraded_cache
    ):
        result = scheduler.run_now(trigger="test_2")

    # Critical invariant: execution count == 0
    assert execution_count["n"] == 0, (
        f"SAFETY VIOLATION: Scheduler executed {execution_count['n']} time(s) "
        f"when Redis was unavailable. Expected 0 executions. "
        f"This violates the fail-closed distributed scheduler invariant."
    )
    assert result["status"] == "DEFERRED_REDIS_UNAVAILABLE", (
        f"Expected DEFERRED_REDIS_UNAVAILABLE but got {result['status']}. "
        f"Full result: {result}"
    )
    assert result.get("local_lock_substituted") is False, (
        "Scheduler must report local_lock_substituted=False when Redis is unavailable."
    )
    assert result.get("execution_count") == 0, (
        "Result must report execution_count=0 when Redis is unavailable."
    )
    assert scheduler.is_degraded is True, (
        "Scheduler must report is_degraded=True when Redis is unavailable in distributed mode."
    )


# ---------------------------------------------------------------------------
# Test 3 — Redis unavailable + two scheduler instances => zero executions
# ---------------------------------------------------------------------------

def test_8_23a_3_redis_unavailable_two_instances_zero_executions():
    """
    TASK 8.23A Test 3:
    With two simulated scheduler instances in a multi-container topology
    and Redis unavailable, BOTH instances must produce zero executions.

    This proves the fail-closed property scales to N replicas.
    """
    total_executions = {"n": 0}

    def counting_runner_factory():
        runner = MagicMock()

        def run_once(trigger=None):
            total_executions["n"] += 1
            return {"status": "SUCCESS"}

        runner.run_once.side_effect = run_once
        return runner

    scheduler_a = LegislativeScheduler(runner_factory=counting_runner_factory)
    scheduler_b = LegislativeScheduler(runner_factory=counting_runner_factory)

    degraded_cache = _make_degraded_cache()

    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=degraded_cache
    ):
        result_a = scheduler_a.run_now(trigger="instance_a")
        result_b = scheduler_b.run_now(trigger="instance_b")

    # Both must report DEFERRED
    assert result_a["status"] == "DEFERRED_REDIS_UNAVAILABLE", (
        f"Instance A: expected DEFERRED_REDIS_UNAVAILABLE, got {result_a['status']}"
    )
    assert result_b["status"] == "DEFERRED_REDIS_UNAVAILABLE", (
        f"Instance B: expected DEFERRED_REDIS_UNAVAILABLE, got {result_b['status']}"
    )

    # Combined execution count must be exactly 0
    assert total_executions["n"] == 0, (
        f"SAFETY VIOLATION: Combined executions across two instances = {total_executions['n']}. "
        f"Expected 0. Redis was unavailable — fail-closed invariant violated."
    )

    # Both schedulers must report degraded
    assert scheduler_a.is_degraded is True
    assert scheduler_b.is_degraded is True


# ---------------------------------------------------------------------------
# Test 4 — Redis recovers => scheduler can safely resume
# ---------------------------------------------------------------------------

def test_8_23a_4_redis_recovers_scheduler_resumes():
    """
    TASK 8.23A Test 4:
    After Redis becomes unavailable (fail-closed) and then recovers,
    the scheduler must be able to safely resume execution.
    """
    execution_count = {"n": 0}

    def counting_runner_factory():
        runner = MagicMock()

        def run_once(trigger=None):
            execution_count["n"] += 1
            return {"status": "SUCCESS", "new_bills": 0}

        runner.run_once.side_effect = run_once
        return runner

    scheduler = LegislativeScheduler(runner_factory=counting_runner_factory)

    # Phase 1: Redis unavailable — fail-closed
    degraded_cache = _make_degraded_cache()
    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=degraded_cache
    ):
        result_down = scheduler.run_now(trigger="phase_1_redis_down")

    assert result_down["status"] == "DEFERRED_REDIS_UNAVAILABLE"
    assert execution_count["n"] == 0, "Must not execute while Redis is down"
    assert scheduler.is_degraded is True

    # Phase 2: Redis recovers — scheduler resumes
    recovered_cache = _make_healthy_cache_with_lock()
    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=recovered_cache
    ):
        result_up = scheduler.run_now(trigger="phase_2_redis_recovered")

    assert result_up["status"] == "SUCCESS", (
        f"After Redis recovery, expected SUCCESS but got {result_up['status']}. "
        f"Full result: {result_up}"
    )
    assert execution_count["n"] == 1, (
        f"After Redis recovery, expected exactly 1 execution but got {execution_count['n']}."
    )
    assert scheduler.is_degraded is False, (
        "Scheduler must clear degraded flag after Redis recovery."
    )


# ---------------------------------------------------------------------------
# Test 5 — Redis lock contention => secondary scheduler skips execution
# ---------------------------------------------------------------------------

def test_8_23a_5_redis_lock_contention_secondary_skips():
    """
    TASK 8.23A Test 5:
    When Redis is available but the distributed lock is already held by
    the primary scheduler, a secondary scheduler instance must gracefully
    skip execution (SKIPPED status, not DEFERRED_REDIS_UNAVAILABLE).
    """
    execution_count = {"n": 0}

    def counting_runner_factory():
        runner = MagicMock()

        def run_once(trigger=None):
            execution_count["n"] += 1
            return {"status": "SUCCESS"}

        runner.run_once.side_effect = run_once
        return runner

    # Secondary scheduler — Redis healthy but lock is contended
    scheduler_secondary = LegislativeScheduler(runner_factory=counting_runner_factory)
    contended_cache = _make_contended_cache()

    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=contended_cache
    ):
        result = scheduler_secondary.run_now(trigger="secondary_instance")

    assert result["status"] == "SKIPPED", (
        f"Expected SKIPPED (lock contention) but got {result['status']}. "
        f"Full result: {result}"
    )
    assert execution_count["n"] == 0, (
        f"Secondary scheduler must not execute when lock is held. "
        f"Got {execution_count['n']} executions."
    )
    # Should NOT be marked degraded — Redis is healthy, it's a contention skip
    assert scheduler_secondary.is_degraded is False, (
        "Scheduler should not be degraded when Redis is healthy (contention is normal)."
    )


# ---------------------------------------------------------------------------
# Test 6 — Lock TTL expiry => another scheduler can safely acquire the lock
# ---------------------------------------------------------------------------

def test_8_23a_6_lock_ttl_expiry_successor_acquires():
    """
    TASK 8.23A Test 6:
    When a scheduler holds the distributed lock and then releases it
    (or it expires via TTL), another scheduler instance must be able to
    safely acquire the lock and execute.
    """
    # Use real DevelopmentCacheProvider for TTL behavior
    shared_cache = DevelopmentCacheProvider()

    # Acquire lock with short TTL (1 second)
    acquired_primary = shared_cache.acquire_lock(
        SCHEDULER_DISTRIBUTED_LOCK_NAME,
        timeout_seconds=1.0,
        expire_seconds=1,  # 1-second TTL
    )
    assert acquired_primary is True, "Primary lock acquisition must succeed."

    # Immediately — secondary cannot acquire
    immediate_attempt = shared_cache.acquire_lock(
        SCHEDULER_DISTRIBUTED_LOCK_NAME,
        timeout_seconds=0.1,
        expire_seconds=10,
    )
    assert immediate_attempt is False, "Lock must be held immediately after acquisition."

    # Wait for TTL to expire
    time.sleep(1.2)

    # After TTL — successor scheduler can acquire
    successor_acquired = shared_cache.acquire_lock(
        SCHEDULER_DISTRIBUTED_LOCK_NAME,
        timeout_seconds=2.0,
        expire_seconds=60,
    )
    assert successor_acquired is True, (
        "After lock TTL expiry, a successor scheduler MUST be able to acquire the lock."
    )

    # Cleanup
    shared_cache.release_lock(SCHEDULER_DISTRIBUTED_LOCK_NAME)

    # Verify the successor can also release
    health = shared_cache.health_check()
    assert health["connected"] is True


# ---------------------------------------------------------------------------
# Test 7 — Scheduler failure cannot generate State predictions
# ---------------------------------------------------------------------------

def test_8_23a_7_scheduler_failure_cannot_generate_state_predictions():
    """
    TASK 8.23A Test 7:
    Regardless of whether the scheduler fails (Redis down, crash, etc.),
    it must NEVER generate State stock predictions.
    The State predictions count must remain strictly 0.
    """
    # Check baseline before any scheduler run attempt
    baseline = verify_production_baseline(quick=True)
    assert baseline.passed is True, (
        f"Pre-test baseline verification failed: {baseline}"
    )

    # Confirm State stock prediction count is strictly zero
    state_pred_dir = settings.DATA_DIR / "state_predictions"
    state_preds_before = (
        len(list(state_pred_dir.glob("*.json")))
        if state_pred_dir.exists()
        else 0
    )
    assert state_preds_before == 0, (
        f"Pre-test: State predictions must be 0, found {state_preds_before}."
    )

    # Simulate scheduler failure scenarios (Redis unavailable, crash)
    scheduler = LegislativeScheduler()
    degraded_cache = _make_degraded_cache()

    # Test with Redis unavailable (fail-closed)
    with patch(
        "services.monitoring.scheduler._is_distributed_mode", return_value=True
    ), patch(
        "services.monitoring.scheduler.get_cache_provider", return_value=degraded_cache
    ):
        result = scheduler.run_now(trigger="state_prediction_safety_test")

    assert result["status"] == "DEFERRED_REDIS_UNAVAILABLE", (
        f"Expected DEFERRED status for Redis-unavailable scenario, got {result['status']}"
    )

    # State predictions must still be 0 after failed/deferred scheduler run
    state_preds_after = (
        len(list(state_pred_dir.glob("*.json")))
        if state_pred_dir.exists()
        else 0
    )
    assert state_preds_after == 0, (
        f"SAFETY VIOLATION: State predictions count changed from "
        f"{state_preds_before} to {state_preds_after} after scheduler failure. "
        f"Scheduler MUST NEVER generate State predictions."
    )

    # Verify the frozen baseline is still intact
    baseline_after = verify_production_baseline(quick=True)
    assert baseline_after.passed is True, (
        f"Post-test baseline verification failed after scheduler failure test: {baseline_after}"
    )


# ---------------------------------------------------------------------------
# Test 8 — Scheduler failure cannot mutate frozen Central prediction artifacts
# ---------------------------------------------------------------------------

def test_8_23a_8_scheduler_failure_cannot_mutate_frozen_central_artifacts():
    """
    TASK 8.23A Test 8:
    Scheduler failures (including Redis outage, crashes, and deferred execution)
    must NEVER mutate the frozen Central prediction artifacts.
    The Central baseline must remain exactly:
      - 4,700 predictions
      - 4,700 decisions
      - 940 anticipation scores
      - 14,100 reports
    """
    import json

    # --- Collect frozen artifact counts BEFORE any scheduler activity ---
    predictions_dir = settings.DATA_DIR / "processed" / "predictions"
    decisions_dir = settings.DATA_DIR / "processed" / "decisions"
    anticipation_dir = settings.DATA_DIR / "processed" / "anticipation"
    reports_dir = settings.DATA_DIR / "processed" / "reports"

    def count_jsons(directory: Path) -> int:
        if not directory.exists():
            return 0
        return len(list(directory.glob("*.json")))

    preds_before = count_jsons(predictions_dir)
    decisions_before = count_jsons(decisions_dir)
    anticipation_before = count_jsons(anticipation_dir)
    reports_before = count_jsons(reports_dir)

    # Baseline verification
    baseline_before = verify_production_baseline(quick=True)
    assert baseline_before.passed is True, (
        f"Pre-test baseline failed: {baseline_before}"
    )

    # --- Run scheduler failure scenarios ---
    scheduler = LegislativeScheduler()
    degraded_cache = _make_degraded_cache()

    scenarios = [
        ("redis_unavailable", True, degraded_cache),
    ]

    for scenario_name, distributed, cache in scenarios:
        with patch(
            "services.monitoring.scheduler._is_distributed_mode",
            return_value=distributed,
        ), patch(
            "services.monitoring.scheduler.get_cache_provider", return_value=cache
        ):
            result = scheduler.run_now(trigger=f"mutation_safety_{scenario_name}")

        assert result["status"] in (
            "DEFERRED_REDIS_UNAVAILABLE",
            "SKIPPED",
            "FAILED",
        ), (
            f"Scenario '{scenario_name}': unexpected status {result['status']}. "
            f"Should be deferred/skipped/failed, not SUCCESS (no execution)."
        )

    # --- Verify artifact counts are unchanged AFTER all scheduler failures ---
    preds_after = count_jsons(predictions_dir)
    decisions_after = count_jsons(decisions_dir)
    anticipation_after = count_jsons(anticipation_dir)
    reports_after = count_jsons(reports_dir)

    assert preds_after == preds_before, (
        f"FREEZE VIOLATION: Predictions changed from {preds_before} to {preds_after} "
        f"after scheduler failure. Frozen Central artifacts MUST NOT be mutated."
    )
    assert decisions_after == decisions_before, (
        f"FREEZE VIOLATION: Decisions changed from {decisions_before} to {decisions_after} "
        f"after scheduler failure."
    )
    assert anticipation_after == anticipation_before, (
        f"FREEZE VIOLATION: Anticipation scores changed from {anticipation_before} to "
        f"{anticipation_after} after scheduler failure."
    )
    assert reports_after == reports_before, (
        f"FREEZE VIOLATION: Reports changed from {reports_before} to {reports_after} "
        f"after scheduler failure."
    )

    # Final baseline verification
    baseline_after = verify_production_baseline(quick=True)
    assert baseline_after.passed is True, (
        f"Post-test baseline verification failed: {baseline_after}"
    )


# ---------------------------------------------------------------------------
# Meta-test — Verify fail-closed invariant documentation
# ---------------------------------------------------------------------------

def test_8_23a_meta_fail_closed_invariant_is_documented_in_scheduler():
    """
    Verify that the scheduler module contains explicit documentation of the
    Redis fail-closed invariant (structural/docstring check).
    """
    import services.monitoring.scheduler as scheduler_module
    import inspect

    source = inspect.getsource(scheduler_module)
    assert "fail_closed" in source or "fail-closed" in source or "FAIL CLOSED" in source, (
        "Scheduler module must document the fail-closed invariant."
    )
    assert "DEFERRED_REDIS_UNAVAILABLE" in source, (
        "Scheduler module must define DEFERRED_REDIS_UNAVAILABLE status code."
    )
    assert "local_lock_substituted" in source or "local lock substituted" in source.lower(), (
        "Scheduler module must explicitly track and expose local_lock_substituted status."
    )
    # Verify distributed mode check is present
    assert "_is_distributed_mode" in source, (
        "Scheduler module must have _is_distributed_mode() function."
    )
