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

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from config.logging_config import get_logger
from config.settings import settings

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


class LegislativeScheduler:
    """
    Scheduler for legislative monitoring runs.

    Safe to restart: a lock prevents duplicate concurrent runs.
    Configurable via environment variables.

    Usage:
        scheduler = LegislativeScheduler()
        # Manual trigger:
        result = scheduler.run_now()
        # Background scheduled execution:
        scheduler.start()
        # ...
        scheduler.stop()
    """

    def __init__(
        self,
        runner_factory: Optional[Callable] = None,
        config: Optional[SchedulerConfig] = None,
    ) -> None:
        self._config = config or SchedulerConfig()
        self._runner_factory = runner_factory or self._default_runner_factory
        self._running_lock = threading.Lock()
        self._is_running: bool = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_run_at: Optional[datetime] = None
        self._next_run_at: Optional[datetime] = None
        self._last_result: Optional[dict[str, Any]] = None

    @staticmethod
    def _default_runner_factory() -> Any:
        """Default factory: creates a MonitoringRunner with default settings."""
        from services.monitoring.monitoring_runner import MonitoringRunner
        return MonitoringRunner(
            max_retries=settings.MONITOR_MAX_RETRIES,
            timeout_seconds=settings.MONITOR_TIMEOUT,
        )

    def run_now(self, trigger: str = "manual") -> dict[str, Any]:
        """
        Execute a monitoring run immediately (blocking).

        Safe to call if scheduler thread is not running.
        Uses a lock to prevent duplicate concurrent runs.
        """
        if not self._running_lock.acquire(blocking=False):
            logger.warning("Monitoring run already in progress — skipping")
            return {
                "status": "SKIPPED",
                "reason": "Run already in progress",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        try:
            self._is_running = True
            logger.info("Starting monitoring run (trigger=%s)", trigger)
            runner = self._runner_factory()
            result = runner.run_once(trigger=trigger)
            self._last_run_at = datetime.now(timezone.utc)
            self._next_run_at = self._last_run_at + timedelta(
                hours=self._config.central_interval_hours
            )
            self._last_result = result
            return result
        except Exception as e:
            logger.error("Monitoring run failed: %s", e, exc_info=True)
            return {
                "status": "FAILED",
                "error": str(e),
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            self._is_running = False
            self._running_lock.release()

    def start(self) -> None:
        """
        Start the background scheduler thread.

        The thread polls at the configured interval and is safe to stop/restart.
        Only starts if LEGISLATIVE_MONITOR_ENABLED is True.
        """
        if not self._config.enabled:
            logger.info(
                "Legislative monitor scheduler is DISABLED "
                "(LEGISLATIVE_MONITOR_ENABLED=false)"
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
        logger.info("Legislative monitoring scheduler started")

    def stop(self) -> None:
        """Stop the background scheduler thread gracefully."""
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)
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

    def get_status(self) -> dict[str, Any]:
        """Return current scheduler status for dashboard display."""
        return {
            "enabled": self._config.enabled,
            "scheduled_running": self.is_scheduled,
            "run_in_progress": self._is_running,
            "last_run_at": self._last_run_at.isoformat()
            if self._last_run_at
            else None,
            "next_run_at": self._next_run_at.isoformat()
            if self._next_run_at
            else None,
            "config": self._config.to_dict(),
            "last_result_status": (self._last_result or {}).get("status"),
        }
