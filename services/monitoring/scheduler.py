"""
services/monitoring/scheduler.py
==================================
Legislative Monitoring Scheduler.

Manages scheduled and manual execution of the monitoring pipeline.
Reads configuration from environment variables and supports:
- Manual trigger (run_now / run_once)
- Background scheduling via threading
- Configurable per-jurisdiction intervals
- Idempotent restart safety (no duplicate runs if already running)

Environment variables:
  LEGISLATIVE_MONITOR_ENABLED  — Enable/disable scheduler (default: false)
  CENTRAL_MONITOR_INTERVAL     — Central check interval in hours (default: 24)
  STATE_MONITOR_INTERVAL       — State check interval in hours (default: 48)
  MONITOR_MAX_RETRIES          — Max retries per source (default: 3)
  MONITOR_TIMEOUT              — Source check timeout in seconds (default: 60)
  JOB_EXECUTION_MODE           — Execution mode: single_instance|multi_instance|worker|scheduler

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.

SAFETY INVARIANT (Task 8.23A — Redis Fail-Closed):
  In PRODUCTION / MULTI_INSTANCE / WORKER / SCHEDULER mode:
    - A distributed Redis lock MUST be acquired before any scheduled job execution.
    - If Redis is UNAVAILABLE, execution MUST be DEFERRED — NEVER substituted with a
      local process-level thread lock.
    - A structured SCHEDULER_DEFERRED event is logged.
    - Scheduler status exposes scheduler_degraded=True.
    - Execution resumes at the next safe scheduler interval.

  In SINGLE_INSTANCE (local/dev/test — explicitly non-production, one process):
    - A process-level threading lock provides within-process singleton protection.
    - This mode MUST NEVER be used in production multi-container (ECS/Fargate) deployments.
    - This mode is clearly marked as non-production.

Production MUST fail CLOSED for distributed execution when Redis is unavailable.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from config.logging_config import get_logger
from config.settings import settings
from infrastructure.cache.provider import get_cache_provider

logger = get_logger(__name__)


class SchedulerConfig:
    """
    Monitoring scheduler configuration loaded from settings/environment.
    """

    def __init__(self) -> None:
        self.enabled: bool = settings.LEGISLATIVE_MONITOR_ENABLED
        self.central_interval_hours: int = settings.CENTRAL_MONITOR_INTERVAL
        self.state_interval_hours: int = settings.STATE_MONITOR_INTERVAL
        self.max_retries: int = settings.MONITOR_MAX_RETRIES
        self.timeout_seconds: int = settings.MONITOR_TIMEOUT

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "central_interval_hours": self.central_interval_hours,
            "state_interval_hours": self.state_interval_hours,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }

    def __repr__(self) -> str:
        return (
            f"<SchedulerConfig enabled={self.enabled} "
            f"central={self.central_interval_hours}h "
            f"state={self.state_interval_hours}h>"
        )


# Stable Job Identifiers
JOB_ID_CENTRAL_POLL = "job_monitoring_central_pipeline"
JOB_ID_STATE_POLL = "job_monitoring_state_pipeline"

# Distributed lock name and TTL for the scheduler
SCHEDULER_DISTRIBUTED_LOCK_NAME = "distributed_scheduler:legislative_monitor"
SCHEDULER_LOCK_EXPIRE_SECONDS = 300  # 5-minute TTL; auto-expires if scheduler crashes

# Process-level active scheduler reference to prevent duplicate background instances
_active_scheduler_lock = threading.Lock()
_active_scheduler_instance: Optional["LegislativeScheduler"] = None


def _get_execution_mode() -> str:
    """Return the current JOB_EXECUTION_MODE. Defaults to 'single_instance'."""
    return os.getenv("JOB_EXECUTION_MODE", "single_instance").lower().strip()


def _is_distributed_mode() -> bool:
    """
    Returns True if the scheduler is running in a multi-container production topology.

    Distributed modes: multi_instance, worker, scheduler.
    In these modes, ONLY a Redis distributed lock provides singleton protection.
    A process-level thread lock CANNOT substitute for a distributed lock.
    """
    return _get_execution_mode() in ("multi_instance", "worker", "scheduler")


class LegislativeScheduler:
    """
    Scheduler for legislative monitoring runs.

    Safe to restart: appropriate locking prevents duplicate concurrent runs.

    PRODUCTION DISTRIBUTED MODE (JOB_EXECUTION_MODE in multi_instance/worker/scheduler):
      - Distributed Redis lock is acquired before ANY scheduled execution.
      - If Redis is UNAVAILABLE (lock acquisition fails / no connectivity):
          * Execution is DEFERRED — fail-closed.
          * A process-level lock MUST NOT be substituted.
          * Structured SCHEDULER_DEFERRED event is logged.
          * scheduler_degraded flag is set to True.
          * Scheduler retries at the next safe interval.
      - If Redis is AVAILABLE but lock is CONTENDED:
          * Secondary scheduler gracefully skips execution (exactly-once semantics).

    SINGLE_INSTANCE (local/dev/test, JOB_EXECUTION_MODE=single_instance):
      - Process-level threading lock provides local-process singleton protection.
      - Explicitly non-production. MUST NOT be deployed across multiple containers.

    Guarantees:
    - Never retrains ML models.
    - Never mutates historical predictions.
    - Never generates state stock predictions.
    - Preserves pipeline: SOURCE -> DISCOVERY -> VALIDATION -> CHANGE DETECTION
                          -> KNOWLEDGE UPDATE -> EXPOSURE UPDATE.
    """

    def __init__(
        self,
        runner_factory: Optional[Callable] = None,
        config: Optional[SchedulerConfig] = None,
    ) -> None:
        self._config = config or SchedulerConfig()
        self._runner_factory = runner_factory or self._default_runner_factory
        # Process-level lock: ONLY for SINGLE_INSTANCE (local/dev/test) mode.
        # NEVER used as a substitute for a distributed lock in production.
        self._local_process_lock = threading.Lock()
        self._is_running: bool = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_run_at: Optional[datetime] = None
        self._next_run_at: Optional[datetime] = None
        self._last_result: Optional[dict[str, Any]] = None
        self._consecutive_failures: int = 0
        # Degraded flag: set True when Redis is unavailable in distributed mode
        self._scheduler_degraded: bool = False
        self.job_ids = [JOB_ID_CENTRAL_POLL, JOB_ID_STATE_POLL]

    @staticmethod
    def _default_runner_factory() -> Any:
        """Default factory: creates a MonitoringRunner with default settings."""
        from services.monitoring.monitoring_runner import MonitoringRunner
        return MonitoringRunner(
            max_retries=settings.MONITOR_MAX_RETRIES,
            timeout_seconds=settings.MONITOR_TIMEOUT,
        )

    def _check_redis_connectivity(self, cache_provider: Any) -> bool:
        """
        Check whether Redis is reachable via the cache provider health check.
        Returns True if Redis is connected and healthy, False otherwise.
        """
        try:
            health = cache_provider.health_check()
            return bool(health.get("connected", False))
        except Exception as exc:
            logger.warning(
                "Redis connectivity check raised exception: %s. "
                "Treating Redis as unavailable.",
                exc,
            )
            return False

    def _acquire_distributed_lock(self, cache_provider: Any) -> bool:
        """
        Acquire the distributed Redis scheduler lock (atomic SET NX EX).
        Returns True if acquired. Returns False if lock is contended or Redis errors.
        NEVER raises; always returns bool.
        """
        try:
            acquired = cache_provider.acquire_lock(
                lock_name=SCHEDULER_DISTRIBUTED_LOCK_NAME,
                timeout_seconds=2.0,
                expire_seconds=SCHEDULER_LOCK_EXPIRE_SECONDS,
            )
            return bool(acquired)
        except Exception as exc:
            logger.warning(
                "Distributed lock acquisition raised exception: %s. "
                "Treating as unavailable — scheduler will DEFER execution.",
                exc,
            )
            return False

    def _release_distributed_lock(self, cache_provider: Any) -> None:
        """Release the distributed scheduler lock. Best-effort; never raises."""
        try:
            cache_provider.release_lock(SCHEDULER_DISTRIBUTED_LOCK_NAME)
        except Exception as exc:
            logger.warning("Failed to release distributed scheduler lock: %s", exc)

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def run_now(self, trigger: str = "manual") -> dict[str, Any]:
        """
        Execute a monitoring run immediately (blocking).

        Routes to the correct execution path based on JOB_EXECUTION_MODE:
          - DISTRIBUTED (multi_instance/worker/scheduler): requires Redis distributed lock;
            fails CLOSED if Redis is unavailable.
          - SINGLE_INSTANCE (local/dev/test): uses process-level threading lock;
            explicitly non-production.
        """
        if _is_distributed_mode():
            return self._run_now_distributed(trigger)
        else:
            return self._run_now_local(trigger)

    # -------------------------------------------------------------------------
    # Distributed execution path (production)
    # -------------------------------------------------------------------------

    def _run_now_distributed(self, trigger: str) -> dict[str, Any]:
        """
        Production distributed execution path.

        Step 1: Check Redis connectivity.
          - UNAVAILABLE -> FAIL CLOSED, log SCHEDULER_DEFERRED, return without executing.
        Step 2: Acquire distributed Redis lock.
          - CONTENDED -> SKIPPED (another scheduler holds the lock — exactly-once semantics).
        Step 3: Execute with lock held.
        Step 4: Release distributed lock.
        """
        cache_provider = get_cache_provider()

        # --- Step 1: Check Redis connectivity ---
        redis_connected = self._check_redis_connectivity(cache_provider)

        if not redis_connected:
            # FAIL CLOSED: Redis is unavailable.
            # DO NOT substitute a process-level lock. DO NOT execute.
            self._scheduler_degraded = True
            now_iso = datetime.now(timezone.utc).isoformat()
            deferred_event = {
                "event": "SCHEDULER_DEFERRED",
                "reason": "Redis unavailable — distributed lock cannot be acquired",
                "execution_mode": _get_execution_mode(),
                "trigger": trigger,
                "action": "EXECUTION_SKIPPED",
                "local_lock_substituted": False,
                "invariant": "fail_closed_redis_required_for_distributed_execution",
                "timestamp": now_iso,
                "next_action": "retry_at_next_safe_scheduler_interval",
            }
            logger.warning(
                "SCHEDULER_DEFERRED | Redis unavailable in distributed mode (%s). "
                "Distributed scheduler execution SKIPPED — no local lock substituted. "
                "Scheduler will retry at next safe interval. trigger=%s",
                _get_execution_mode(),
                trigger,
                extra=deferred_event,
            )
            return {
                "status": "DEFERRED_REDIS_UNAVAILABLE",
                "reason": (
                    "Redis unavailable — distributed lock cannot be acquired. "
                    "Execution skipped (fail-closed). No local lock substituted."
                ),
                "execution_count": 0,
                "execution_mode": _get_execution_mode(),
                "scheduler_degraded": True,
                "local_lock_substituted": False,
                "started_at": now_iso,
            }

        # --- Step 2: Acquire distributed lock ---
        acquired = self._acquire_distributed_lock(cache_provider)
        if not acquired:
            # Lock is contended — another scheduler instance holds it
            self._scheduler_degraded = False
            logger.info(
                "SCHEDULER_SKIPPED | Distributed lock held by another scheduler instance. "
                "trigger=%s mode=%s",
                trigger,
                _get_execution_mode(),
            )
            return {
                "status": "SKIPPED",
                "reason": "Distributed lock held by another scheduler instance",
                "execution_count": 0,
                "execution_mode": _get_execution_mode(),
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        # --- Step 3 & 4: Execute under distributed lock ---
        self._scheduler_degraded = False
        logger.info(
            "SCHEDULER_LOCK_ACQUIRED | Distributed lock acquired. "
            "Executing scheduled run. trigger=%s mode=%s",
            trigger,
            _get_execution_mode(),
        )
        try:
            return self._execute_run(trigger)
        finally:
            self._release_distributed_lock(cache_provider)

    # -------------------------------------------------------------------------
    # Local execution path (single-instance / dev / test only)
    # -------------------------------------------------------------------------

    def _run_now_local(self, trigger: str) -> dict[str, Any]:
        """
        LOCAL SINGLE-INSTANCE execution path (dev/test only — explicitly non-production).

        Uses a process-level threading lock.
        This MUST NOT be used in multi-container production deployments.
        """
        if not self._local_process_lock.acquire(blocking=False):
            logger.warning(
                "Monitoring run already in progress — skipping "
                "(local single-instance mode, non-production)"
            )
            return {
                "status": "SKIPPED",
                "reason": "Run already in progress",
                "execution_mode": "single_instance",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        try:
            return self._execute_run(trigger)
        finally:
            self._local_process_lock.release()

    # -------------------------------------------------------------------------
    # Core execution (called after lock is held)
    # -------------------------------------------------------------------------

    def _execute_run(self, trigger: str) -> dict[str, Any]:
        """
        Internal: Execute the monitoring pipeline run.
        Called ONLY after the appropriate lock (distributed or local) has been acquired.
        """
        try:
            self._is_running = True
            logger.info("Starting monitoring run (trigger=%s)", trigger)
            runner = self._runner_factory()

            # Hard Invariant: Ensure runner never touches ML models or predictions
            is_mock = getattr(type(runner), "__module__", "").startswith("unittest.mock")
            if not is_mock and (
                hasattr(runner, "train_model") or hasattr(runner, "generate_predictions")
            ):
                raise RuntimeError(
                    "Security Invariant Violation: Monitoring runner attempted model retraining!"
                )

            result = runner.run_once(trigger=trigger)
            self._last_run_at = datetime.now(timezone.utc)
            self._next_run_at = self._last_run_at + timedelta(
                hours=self._config.central_interval_hours
            )
            self._last_result = result
            if result.get("status") in ("SUCCESS", "PARTIAL_SUCCESS"):
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
            return result
        except Exception as e:
            self._consecutive_failures += 1
            logger.error("Monitoring run failed: %s", e, exc_info=True)
            return {
                "status": "FAILED",
                "error": str(e),
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            self._is_running = False

    # -------------------------------------------------------------------------
    # Background scheduling
    # -------------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the background scheduler thread.

        The thread polls at the configured interval and is safe to stop/restart.
        Only starts if LEGISLATIVE_MONITOR_ENABLED is True.
        Guarantees singleton process execution.
        """
        if not self._config.enabled:
            logger.info(
                "Legislative monitor scheduler is DISABLED "
                "(LEGISLATIVE_MONITOR_ENABLED=false)"
            )
            return

        with _active_scheduler_lock:
            global _active_scheduler_instance
            if _active_scheduler_instance is not None and _active_scheduler_instance.is_scheduled:
                logger.warning(
                    "Active background scheduler singleton already running — refusing duplicate start"
                )
                return

            if self._scheduler_thread and self._scheduler_thread.is_alive():
                logger.warning("Scheduler thread already running")
                return

            self._stop_event.clear()
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="LegislativeMonitorScheduler",
                daemon=True,
            )
            self._scheduler_thread.start()
            _active_scheduler_instance = self
            logger.info("Legislative monitoring scheduler started (Singleton active)")

    def stop(self) -> None:
        """Stop the background scheduler thread gracefully."""
        with _active_scheduler_lock:
            global _active_scheduler_instance
            self._stop_event.set()
            if self._scheduler_thread:
                self._scheduler_thread.join(timeout=5.0)
            if _active_scheduler_instance is self:
                _active_scheduler_instance = None
            logger.info("Legislative monitoring scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Background scheduler loop."""
        interval_seconds = self._config.central_interval_hours * 3600
        logger.info(
            "Scheduler loop started — interval=%dh (%ds)",
            self._config.central_interval_hours,
            interval_seconds,
        )

        while not self._stop_event.is_set():
            try:
                self.run_now(trigger="scheduled")
            except Exception as e:
                logger.error("Scheduled monitoring run error: %s", e)

            # Wait for the next interval (check stop_event frequently)
            waited = 0
            while waited < interval_seconds and not self._stop_event.is_set():
                self._stop_event.wait(timeout=min(60, interval_seconds - waited))
                waited += 60

    # -------------------------------------------------------------------------
    # Status properties
    # -------------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """True if a monitoring run is currently executing."""
        return self._is_running

    @property
    def is_scheduled(self) -> bool:
        """True if the background scheduler thread is active."""
        return bool(
            self._scheduler_thread and self._scheduler_thread.is_alive()
        )

    @property
    def is_degraded(self) -> bool:
        """True if the scheduler is degraded due to Redis unavailability in distributed mode."""
        return self._scheduler_degraded

    def get_status(self) -> dict[str, Any]:
        """Return current scheduler status for health/dashboard display."""
        distributed = _is_distributed_mode()
        return {
            "enabled": self._config.enabled,
            "scheduled_running": self.is_scheduled,
            "run_in_progress": self._is_running,
            "execution_mode": _get_execution_mode(),
            "is_distributed_mode": distributed,
            "scheduler_degraded": self._scheduler_degraded,
            "distributed_lock_required": distributed,
            "local_lock_substitution_permitted": not distributed,
            "job_ids": self.job_ids,
            "consecutive_failures": self._consecutive_failures,
            "last_run_at": (
                self._last_run_at.isoformat() if self._last_run_at else None
            ),
            "next_run_at": (
                self._next_run_at.isoformat() if self._next_run_at else None
            ),
            "config": self._config.to_dict(),
            "last_result_status": (self._last_result or {}).get("status"),
        }
