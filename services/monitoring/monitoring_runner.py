"""
services/monitoring/monitoring_runner.py
==========================================
Legislative Monitoring Run Orchestrator.

Coordinates a complete monitoring run across all enabled sources.
Handles per-source failures gracefully (one failed source does NOT
abort other sources). Creates an auditable MonitoringRun record.

Run status:
- SUCCESS       — all sources succeeded
- PARTIAL_SUCCESS — some sources failed, others succeeded
- FAILED        — all sources failed

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.monitoring import (
    ChangeEventType,
    MonitoringRun,
    RunStatus,
)
from services.monitoring.base_monitor import BaseMonitor
from services.monitoring.central_monitor import CentralMonitor
from services.monitoring.notification_events import LegislativeEventFeed
from services.monitoring.source_registry import MonitoringSourceRegistry
from services.monitoring.state_monitor import StateMonitor
from services.monitoring.update_processor import UpdateProcessor
from storage.monitoring_repository import MonitoringRepository

logger = get_logger(__name__)


class MonitoringRunner:
    """
    Orchestrates a complete legislative monitoring run.

    On each run:
    1. Load enabled sources from MonitoringSourceRegistry
    2. For each source, instantiate the appropriate monitor
    3. Call check_for_updates() — failures are isolated per source
    4. Process all detected change events via UpdateProcessor
    5. Publish events to LegislativeEventFeed
    6. Record full MonitoringRun to MonitoringRepository
    7. Return concise summary dict

    The runner is idempotent and safe to call repeatedly.
    """

    def __init__(
        self,
        source_registry: Optional[MonitoringSourceRegistry] = None,
        monitoring_repo: Optional[MonitoringRepository] = None,
        update_processor: Optional[UpdateProcessor] = None,
        event_feed: Optional[LegislativeEventFeed] = None,
        max_retries: int = 3,
        timeout_seconds: int = 60,
        source_overrides: Optional[dict[str, Any]] = None,
    ) -> None:
        self._registry = source_registry or MonitoringSourceRegistry()
        self._repo = monitoring_repo or MonitoringRepository()
        self._processor = update_processor or UpdateProcessor(
            monitoring_repo=self._repo
        )
        self._event_feed = event_feed or LegislativeEventFeed()
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        # source_overrides: {source_id: callable} for injecting snapshot functions
        self._source_overrides: dict[str, Any] = source_overrides or {}

    def run_once(self, trigger: str = "manual") -> dict[str, Any]:
        """
        Execute a single monitoring run.

        Returns a concise summary dict suitable for Streamlit display.
        """
        run = MonitoringRun(trigger=trigger)
        logger.info(
            "Starting monitoring run %s (trigger=%s)", run.run_id, trigger
        )

        enabled_sources = self._registry.get_enabled()
        run.sources_checked = len(enabled_sources)

        for source in enabled_sources:
            source_result = self._check_source(source.source_id, source.jurisdiction)
            run.source_results.append(source_result)

            if source_result["success"]:
                run.sources_succeeded += 1
                self._registry.mark_checked(source.source_id, success=True)
            else:
                run.sources_failed += 1
                self._registry.mark_checked(
                    source.source_id,
                    success=False,
                    error=source_result.get("error"),
                )

            run.new_bills += source_result.get("new_bills", 0)
            run.changed_bills += source_result.get("changed_bills", 0)
            run.document_changes += source_result.get("document_changes", 0)
            run.errors += 1 if not source_result["success"] else 0

        run.mark_complete()
        self._repo.save_run(run)

        logger.info(
            "Monitoring run %s complete: %s | %d new, %d changed, %d doc, %d errors",
            run.run_id,
            run.status.value,
            run.new_bills,
            run.changed_bills,
            run.document_changes,
            run.errors,
        )

        return self._build_summary(run)

    def _check_source(self, source_id: str, jurisdiction: str) -> dict[str, Any]:
        """Check a single source, process events, and return result."""
        logger.info("Checking source: %s", source_id)

        # Build the appropriate monitor
        monitor = self._build_monitor(source_id, jurisdiction)
        monitor_result = monitor.check_for_updates()

        if monitor_result.success:
            # Process each detected change event
            for event in monitor_result.events:
                if event.event_type == ChangeEventType.NO_CHANGE:
                    continue
                # Process the update
                self._processor.process(event)
                # Publish to notification feed
                if event.event_type != ChangeEventType.ERROR:
                    self._event_feed.publish_from_change_event(event)
                    try:
                        from services.alert_pipeline_service import AlertPipelineService
                        AlertPipelineService().process_event(event)
                    except Exception as e:
                        logger.warning("Alert pipeline dispatch for event %s encountered: %s", event.event_id, e)

        result = monitor_result.to_dict()
        return result

    def _build_monitor(self, source_id: str, jurisdiction: str) -> BaseMonitor:
        """Instantiate the correct monitor for a source."""
        snapshot_fn = self._source_overrides.get(source_id)

        if jurisdiction == "central":
            from storage.bill_repository import BillRepository
            return CentralMonitor(
                source_id=source_id,
                bill_repository=BillRepository(),
                source_snapshot_fn=snapshot_fn,
                max_retries=self._max_retries,
                timeout_seconds=self._timeout_seconds,
            )
        else:
            # State monitor
            from storage.state_knowledge_repository import StateKnowledgeRepository
            from services.monitoring.source_registry import MonitoringSourceRegistry

            state_name = None
            src = self._registry.get(source_id)
            if src:
                state_name = src.state

            return StateMonitor(
                source_id=source_id,
                state_name=state_name,
                knowledge_repository=StateKnowledgeRepository(),
                source_snapshot_fn=snapshot_fn,
                max_retries=self._max_retries,
                timeout_seconds=self._timeout_seconds,
            )

    def _build_summary(self, run: MonitoringRun) -> dict[str, Any]:
        """Build a concise summary dict for display."""
        return {
            "run_id": run.run_id,
            "status": run.status.value
            if isinstance(run.status, RunStatus)
            else str(run.status),
            "trigger": run.trigger,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "duration_seconds": run.duration_seconds,
            "sources_checked": run.sources_checked,
            "sources_succeeded": run.sources_succeeded,
            "sources_failed": run.sources_failed,
            "new_bills": run.new_bills,
            "changed_bills": run.changed_bills,
            "document_changes": run.document_changes,
            "errors": run.errors,
            "source_results": run.source_results,
        }

    def get_last_run(self) -> Optional[dict[str, Any]]:
        """Return the most recent monitoring run record."""
        run = self._repo.get_last_run()
        if run:
            return run.to_dict()
        return None

    def get_source_statuses(self) -> list[dict[str, Any]]:
        """Return current status of all monitoring sources for dashboard display."""
        sources = self._registry.get_all()
        return [s.to_dict() for s in sources]
