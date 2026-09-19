"""
services/monitoring/notification_events.py
============================================
Backend legislative event feed for the "What's New" feature.

Maintains an in-memory + file-backed log of legislative events
(new bills, status changes, document changes, etc.) for future
SaaS frontend consumption.

NO email, push, WhatsApp, or external notification delivery is
implemented here. This is the backend event layer only.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import uuid

from config.logging_config import get_logger
from config.settings import settings
from schemas.monitoring import ChangeEvent, ChangeEventType, NotificationEvent
from utils.file_utils import ensure_dir

logger = get_logger(__name__)

_DEFAULT_EVENTS_DIR = settings.PROJECT_ROOT / "storage" / "monitoring" / "notification_events"


class LegislativeEventFeed:
    """
    Backend event feed for legislative monitoring notifications.

    Persists events to storage/monitoring/notification_events/ as JSON files.
    Provides `get_recent_events()` for dashboard and future API consumption.

    Designed to be:
    - Append-only (events are never deleted/modified)
    - Idempotent (duplicate event_ids are ignored)
    - Restartable (events survive process crashes)
    """

    def __init__(self, events_dir: Optional[Path] = None) -> None:
        self._events_dir = events_dir or _DEFAULT_EVENTS_DIR
        ensure_dir(self._events_dir)
        self._seen_ids: set[str] = self._load_seen_ids()

    def _load_seen_ids(self) -> set[str]:
        """Load existing event IDs from disk to ensure idempotency."""
        seen: set[str] = set()
        try:
            for f in self._events_dir.glob("event_*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    eid = data.get("event_id")
                    if eid:
                        seen.add(eid)
                except Exception:
                    pass
        except Exception as e:
            logger.warning("Could not load existing event IDs: %s", e)
        return seen

    def publish(self, event: NotificationEvent) -> bool:
        """
        Publish a notification event to the feed.

        Returns True if the event was persisted, False if it was a duplicate.
        """
        if event.event_id in self._seen_ids:
            logger.debug("Duplicate notification event skipped: %s", event.event_id)
            return False

        path = self._events_dir / f"event_{event.event_id}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(event.to_dict(), f, indent=2, default=str)
            self._seen_ids.add(event.event_id)
            logger.debug(
                "Published notification event %s: %s",
                event.event_type,
                event.bill_title,
            )
            return True
        except Exception as e:
            logger.error("Failed to persist notification event: %s", e)
            return False

    def publish_from_change_event(self, change_event: ChangeEvent) -> bool:
        """Convenience method: convert a ChangeEvent to NotificationEvent and publish."""
        affected = resolve_affected_companies(change_event.bill_id)
        notif = NotificationEvent(
            event_id=change_event.event_id,
            event_type=change_event.event_type,
            bill_id=change_event.bill_id,
            bill_title=change_event.bill_title,
            jurisdiction=change_event.jurisdiction,
            state=change_event.state,
            source=change_event.source_id,
            summary=_build_summary(change_event),
            metadata={
                "field_name": change_event.field_name,
                "old_value": change_event.old_value,
                "new_value": change_event.new_value,
                "source_reference": change_event.source_reference,
                "affected_companies": affected,
                "affected_company_count": len(affected),
            },
        )
        return self.publish(notif)

    def get_recent_events(
        self,
        limit: int = 50,
        jurisdiction: Optional[str] = None,
        state: Optional[str] = None,
        event_type: Optional[ChangeEventType] = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve recent notification events for dashboard display.

        Returns events sorted by detected_at descending (most recent first).
        """
        events: list[dict[str, Any]] = []
        try:
            files = sorted(
                self._events_dir.glob("event_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            for f in files:
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    # Apply filters
                    if jurisdiction and data.get("jurisdiction") != jurisdiction:
                        continue
                    if state and data.get("state") != state:
                        continue
                    if event_type and data.get("event_type") != event_type.value:
                        continue
                    events.append(data)
                    if len(events) >= limit:
                        break
                except Exception:
                    pass
        except Exception as e:
            logger.error("Failed to retrieve notification events: %s", e)
        return events

    def get_event_count(self) -> int:
        """Return total number of persisted events."""
        try:
            return len(list(self._events_dir.glob("event_*.json")))
        except Exception:
            return 0

    def create_new_bill_event(
        self,
        bill_id: str,
        title: str,
        jurisdiction: str,
        state: Optional[str],
        source: str,
    ) -> NotificationEvent:
        """Factory method for NEW_BILL notification events."""
        affected = resolve_affected_companies(bill_id)
        return NotificationEvent(
            event_type=ChangeEventType.NEW_BILL,
            bill_id=bill_id,
            bill_title=title,
            jurisdiction=jurisdiction,
            state=state,
            source=source,
            summary=f"New {'State' if state else 'Central'} bill detected: {title}",
            metadata={
                "affected_companies": affected,
                "affected_company_count": len(affected),
            },
        )

    def create_status_changed_event(
        self,
        bill_id: str,
        title: str,
        jurisdiction: str,
        state: Optional[str],
        source: str,
        old_status: str,
        new_status: str,
    ) -> NotificationEvent:
        """Factory method for STATUS_CHANGED notification events."""
        affected = resolve_affected_companies(bill_id)
        return NotificationEvent(
            event_type=ChangeEventType.STATUS_CHANGED,
            bill_id=bill_id,
            bill_title=title,
            jurisdiction=jurisdiction,
            state=state,
            source=source,
            summary=f"Bill status changed: {old_status!r} → {new_status!r}",
            metadata={
                "old_status": old_status,
                "new_status": new_status,
                "affected_companies": affected,
                "affected_company_count": len(affected),
            },
        )


def resolve_affected_companies(bill_id: str) -> list[dict[str, Any]]:
    """
    Resolve corporate exposure intelligence for a legislative bill.
    Allows monitoring events to resolve Bill -> affected companies.
    """
    try:
        from storage.company_exposure_repository import CompanyExposureRepository
        repo = CompanyExposureRepository()
        exps = repo.get_companies_for_bill(bill_id)
        results: list[dict[str, Any]] = []
        for e in exps:
            results.append({
                "company_id": e.company_id,
                "company_name": e.company_name,
                "ticker": e.ticker,
                "sector": e.sector,
                "business_activity": e.business_activity,
                "exposure_type": e.exposure_type,
                "direct_indirect": e.direct_indirect,
                "exposure_strength": e.exposure_strength,
                "mechanism": e.mechanism,
                "market_relevance": e.market_relevance,
            })
        return results
    except Exception as exc:
        logger.debug("Failed resolving affected companies for bill %s: %s", bill_id, exc)
        return []


def _build_summary(event: ChangeEvent) -> str:
    """Build a human-readable summary for a change event."""
    if event.event_type == ChangeEventType.NEW_BILL:
        return f"New bill detected: {event.bill_title}"
    if event.event_type == ChangeEventType.STATUS_CHANGED:
        return f"Status changed: {event.old_value!r} → {event.new_value!r}"
    if event.event_type == ChangeEventType.DATE_CHANGED:
        return f"Date updated ({event.field_name}): {event.old_value!r} → {event.new_value!r}"
    if event.event_type == ChangeEventType.DOCUMENT_CHANGED:
        return "Bill document (PDF) updated"
    if event.event_type == ChangeEventType.METADATA_CHANGED:
        return f"Metadata changed ({event.field_name})"
    return f"Change detected: {event.event_type}"
