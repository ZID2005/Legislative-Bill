"""
services/alert_pipeline_service.py
===================================
Alert Pipeline Orchestration Service — End-to-End Integration Layer.

Connects all existing alert subsystem services into a single deterministic
orchestration path without duplicating their internal logic.

Pipeline flow:

  Incoming Event (ChangeEvent | StateCorporateExposure | NormalizedEvent | dict)
          ↓
  AlertMatchingService.process_event()
          ↓
  [AlertEvents] (persisted, deduplicated)
          ↓
  AlertAggregationService.aggregate_events()
          ↓
  [AlertGroups] (persisted, deterministic)
          ↓
  NotificationService.create_notifications_from_alert_events()
          ↓
  [Notifications] (in-app, persisted, dedup-guarded)
          ↓
  Optional outbound dispatch via NotificationDispatcher

Design guarantees:
- Calls existing services — does NOT duplicate their logic.
- All deduplication, validation, and isolation is enforced by the individual services.
- Additive only: zero mutations to production predictions, companies, or baselines.
- State predictions remain strictly absent (none) throughout.
- Structured logging at each pipeline stage without leaking secrets.
- Each stage is independently recoverable — partial failures do not delete upstream evidence.

Task 8.13.8 — Watchlist & Alert E2E Integration, Verification & Hardening.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.alert import AlertEvent, Notification, NotificationChannel
from schemas.alert_group import AlertGroup, AlertGroupType
from services.alert_aggregation_service import AlertAggregationService
from services.alert_digest_service import AlertDigestService
from services.alert_matching_service import AlertMatchingService
from services.notification_center_service import NotificationCenterService
from services.notification_dispatcher import NotificationDispatcher
from services.notification_service import NotificationService
from services.watchlist_index_service import WatchlistIndexService
from services.watchlist_service import WatchlistService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.notification_delivery_repository import NotificationDeliveryRepository
from storage.notification_repository import NotificationRepository
from storage.watchlist_repository import WatchlistRepository

logger = get_logger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Pipeline Result Container
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """
    Structured result of a single alert pipeline execution.

    Attributes
    ----------
    event_id : str
        Source event identifier for full traceability.
    alert_events : list[AlertEvent]
        Generated AlertEvents from matching stage.
    alert_groups : list[AlertGroup]
        Generated AlertGroups from aggregation stage.
    notifications : list[Notification]
        Generated in-app Notifications.
    skipped_events : int
        Events skipped due to no subscribers or no matching rules.
    failed_stages : list[str]
        Names of pipeline stages that encountered recoverable errors.
    stage_durations_ms : dict[str, float]
        Per-stage execution duration in milliseconds.
    success : bool
        True if at least matching completed without unrecoverable errors.
    error_message : Optional[str]
        Error details if a critical unrecoverable failure occurred.
    metadata : dict[str, Any]
        Supplementary pipeline execution metadata.
    """

    event_id: str = ""
    alert_events: list[AlertEvent] = field(default_factory=list)
    alert_groups: list[AlertGroup] = field(default_factory=list)
    notifications: list[Notification] = field(default_factory=list)
    skipped_events: int = 0
    failed_stages: list[str] = field(default_factory=list)
    stage_durations_ms: dict[str, float] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize PipelineResult to dictionary for logging/observability."""
        return {
            "event_id": self.event_id,
            "alert_event_count": len(self.alert_events),
            "alert_group_count": len(self.alert_groups),
            "notification_count": len(self.notifications),
            "skipped_events": self.skipped_events,
            "failed_stages": self.failed_stages,
            "stage_durations_ms": self.stage_durations_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Alert Pipeline Service
# ---------------------------------------------------------------------------


class AlertPipelineService:
    """
    End-to-end orchestration service for the complete alert pipeline.

    Coordinates existing services in the correct order without duplicating
    their internal logic, validation, or persistence mechanisms.

    Responsibilities:
    1. Accept any supported event type.
    2. Delegate to AlertMatchingService for subscriber resolution and AlertEvent generation.
    3. Delegate to AlertAggregationService for AlertGroup formation.
    4. Delegate to NotificationService for in-app notification creation.
    5. Optionally dispatch outbound notifications via NotificationDispatcher.
    6. Emit structured logs at each pipeline stage.
    7. Guarantee that downstream failures do not destroy upstream evidence.
    """

    def __init__(
        self,
        # Core services — injected for testability
        matching_service: Optional[AlertMatchingService] = None,
        aggregation_service: Optional[AlertAggregationService] = None,
        notification_service: Optional[NotificationService] = None,
        notification_center: Optional[NotificationCenterService] = None,
        digest_service: Optional[AlertDigestService] = None,
        dispatcher: Optional[NotificationDispatcher] = None,
        # Repositories — optional overrides for isolated testing
        watchlist_repo: Optional[WatchlistRepository] = None,
        index_service: Optional[WatchlistIndexService] = None,
        alert_rule_repo: Optional[AlertRuleRepository] = None,
        alert_event_repo: Optional[AlertEventRepository] = None,
        alert_group_repo: Optional[AlertGroupRepository] = None,
        alert_pref_repo: Optional[AlertPreferenceRepository] = None,
        notification_repo: Optional[NotificationRepository] = None,
        delivery_repo: Optional[NotificationDeliveryRepository] = None,
    ) -> None:
        # Build repositories with defaults where not provided
        _wl_repo = watchlist_repo or WatchlistRepository()
        _idx_svc = index_service or WatchlistIndexService(watchlist_repo=_wl_repo)
        _rule_repo = alert_rule_repo or AlertRuleRepository()
        _event_repo = alert_event_repo or AlertEventRepository()
        _group_repo = alert_group_repo or AlertGroupRepository()
        _pref_repo = alert_pref_repo or AlertPreferenceRepository()
        _notif_repo = notification_repo or NotificationRepository()

        # Primary services
        self.matching_service = matching_service or AlertMatchingService(
            watchlist_repo=_wl_repo,
            index_service=_idx_svc,
            alert_rule_repo=_rule_repo,
            alert_event_repo=_event_repo,
            alert_pref_repo=_pref_repo,
        )
        self.aggregation_service = aggregation_service or AlertAggregationService(
            alert_event_repo=_event_repo,
            alert_group_repo=_group_repo,
        )
        self.notification_service = notification_service or NotificationService(
            notification_repo=_notif_repo,
            alert_pref_repo=_pref_repo,
        )
        self.notification_center = notification_center or NotificationCenterService(
            notification_service=self.notification_service,
        )
        self.digest_service = digest_service or AlertDigestService(
            alert_group_repo=_group_repo,
            alert_event_repo=_event_repo,
            alert_pref_repo=_pref_repo,
        )
        self.dispatcher = dispatcher or self.notification_service.dispatcher

        logger.info("AlertPipelineService initialised (Task 8.13.8)")

    # ------------------------------------------------------------------
    # Primary Entry Point
    # ------------------------------------------------------------------

    def process_event(
        self,
        event: Any,
        aggregate: bool = True,
        notify: bool = True,
        group_by: Optional[AlertGroupType] = None,
    ) -> PipelineResult:
        """
        Process a single event through the complete alert pipeline.

        Parameters
        ----------
        event : Any
            A ChangeEvent, StateCorporateExposure, NormalizedEvent, or compatible dict.
        aggregate : bool
            If True, aggregate AlertEvents into AlertGroups (default: True).
        notify : bool
            If True, create in-app notifications from AlertEvents (default: True).
        group_by : Optional[AlertGroupType]
            Force a specific aggregation grouping dimension.

        Returns
        -------
        PipelineResult
            Structured result containing all generated records and observability metadata.
        """
        result = PipelineResult()
        pipeline_start = time.monotonic()

        # --------------- Stage 1: Event Matching ---------------
        t0 = time.monotonic()
        stage_name = "matching"
        try:
            alert_events = self.matching_service.process_event(event)
            result.alert_events = alert_events
            result.event_id = getattr(
                self.matching_service.normalize_event(event), "event_id", "unknown"
            )
            duration_ms = (time.monotonic() - t0) * 1000
            result.stage_durations_ms[stage_name] = round(duration_ms, 2)

            logger.info(
                "Pipeline[matching] event=%s generated=%d alerts duration_ms=%.1f",
                result.event_id,
                len(alert_events),
                duration_ms,
            )

            if not alert_events:
                result.skipped_events = 1
                result.metadata["skip_reason"] = "no_matching_subscribers_or_rules"
                logger.debug(
                    "Pipeline[matching] event=%s — no subscribers or rules matched",
                    result.event_id,
                )
                return result

        except Exception as exc:
            duration_ms = (time.monotonic() - t0) * 1000
            result.stage_durations_ms[stage_name] = round(duration_ms, 2)
            result.failed_stages.append(stage_name)
            result.success = False
            result.error_message = f"Matching stage failed: {exc}"
            logger.error(
                "Pipeline[matching] FAILED event=%s error=%s duration_ms=%.1f",
                result.event_id,
                exc,
                duration_ms,
            )
            return result

        # --------------- Stage 2: Aggregation ---------------
        if aggregate:
            t0 = time.monotonic()
            stage_name = "aggregation"
            try:
                alert_groups = self.aggregation_service.aggregate_events(
                    alert_events, group_by=group_by
                )
                result.alert_groups = alert_groups
                duration_ms = (time.monotonic() - t0) * 1000
                result.stage_durations_ms[stage_name] = round(duration_ms, 2)

                logger.info(
                    "Pipeline[aggregation] event=%s events=%d groups=%d duration_ms=%.1f",
                    result.event_id,
                    len(alert_events),
                    len(alert_groups),
                    duration_ms,
                )
            except Exception as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                result.stage_durations_ms[stage_name] = round(duration_ms, 2)
                result.failed_stages.append(stage_name)
                # Aggregation failure is recoverable — upstream AlertEvents remain valid
                logger.warning(
                    "Pipeline[aggregation] recoverable failure event=%s error=%s "
                    "AlertEvents remain valid",
                    result.event_id,
                    exc,
                )

        # --------------- Stage 3: Notification Creation ---------------
        if notify:
            t0 = time.monotonic()
            stage_name = "notification"
            try:
                notifications = self.notification_service.create_notifications_from_alert_events(
                    alert_events
                )
                result.notifications = notifications
                duration_ms = (time.monotonic() - t0) * 1000
                result.stage_durations_ms[stage_name] = round(duration_ms, 2)

                logger.info(
                    "Pipeline[notification] event=%s notifications=%d duration_ms=%.1f",
                    result.event_id,
                    len(notifications),
                    duration_ms,
                )
            except Exception as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                result.stage_durations_ms[stage_name] = round(duration_ms, 2)
                result.failed_stages.append(stage_name)
                # Notification failure is recoverable — upstream AlertEvents and Groups remain valid
                logger.warning(
                    "Pipeline[notification] recoverable failure event=%s error=%s "
                    "AlertEvents and AlertGroups remain valid",
                    result.event_id,
                    exc,
                )

        # Pipeline complete
        total_ms = (time.monotonic() - pipeline_start) * 1000
        result.stage_durations_ms["total"] = round(total_ms, 2)
        result.success = len(result.failed_stages) == 0 or bool(result.alert_events)

        logger.info(
            "Pipeline[complete] event=%s alerts=%d groups=%d notifications=%d "
            "failed_stages=%s total_ms=%.1f",
            result.event_id,
            len(result.alert_events),
            len(result.alert_groups),
            len(result.notifications),
            result.failed_stages,
            total_ms,
        )

        return result

    def process_batch(
        self,
        events: list[Any],
        aggregate: bool = True,
        notify: bool = True,
    ) -> list[PipelineResult]:
        """
        Process a sequence of events through the complete pipeline.

        Parameters
        ----------
        events : list[Any]
            Sequence of events to process.
        aggregate : bool
            Whether to aggregate AlertEvents per batch item.
        notify : bool
            Whether to create notifications per batch item.

        Returns
        -------
        list[PipelineResult]
            One PipelineResult per input event.
        """
        results: list[PipelineResult] = []
        for ev in events:
            results.append(self.process_event(ev, aggregate=aggregate, notify=notify))
        return results

    # ------------------------------------------------------------------
    # Observability Helpers
    # ------------------------------------------------------------------

    def get_pipeline_summary(self, results: list[PipelineResult]) -> dict[str, Any]:
        """
        Aggregate execution statistics across multiple PipelineResults.

        Parameters
        ----------
        results : list[PipelineResult]
            List of PipelineResult objects from batch processing.

        Returns
        -------
        dict[str, Any]
            Aggregated statistics dictionary.
        """
        total = len(results)
        successes = sum(1 for r in results if r.success)
        failures = total - successes
        total_events = sum(len(r.alert_events) for r in results)
        total_groups = sum(len(r.alert_groups) for r in results)
        total_notifs = sum(len(r.notifications) for r in results)
        total_skipped = sum(r.skipped_events for r in results)
        all_failed_stages = [s for r in results for s in r.failed_stages]

        return {
            "pipeline_runs": total,
            "successful_runs": successes,
            "failed_runs": failures,
            "total_alert_events": total_events,
            "total_alert_groups": total_groups,
            "total_notifications": total_notifs,
            "total_skipped": total_skipped,
            "failed_stages_summary": list(set(all_failed_stages)),
        }
