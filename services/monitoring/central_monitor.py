"""
services/monitoring/central_monitor.py
========================================
Monitor for Central Government legislative sources.

Checks the existing BillRepository for known bills, fetches current
listings from official Central sources, detects changes, and returns
typed ChangeEvent objects.

CRITICAL PROTECTIONS:
- Never modifies training data, prediction records, or backtest records.
- New Central bills are routed to knowledge/discovery only.
- No automatic re-training or prediction model changes.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.monitoring import ChangeEvent, ChangeEventType
from services.monitoring.base_monitor import BaseMonitor
from services.monitoring.change_detector import LegislativeChangeDetector
from storage.bill_repository import BillRepository

logger = get_logger(__name__)


class CentralMonitor(BaseMonitor):
    """
    Monitor for Central Government legislative sources.

    Reads the current production BillRepository as the "known" baseline,
    then compares against a fetched or cached snapshot from official sources.

    In the monitoring architecture the source check is intentionally
    conservative: we compare metadata available from the repository
    against what the source currently exposes, field-by-field.

    Since live HTTP fetching of Parliament portals happens in a sandboxed
    environment (tests use mocks), the monitor accepts an injectable
    `source_snapshot_fn` so tests can provide fixture data without live
    network calls.
    """

    def __init__(
        self,
        source_id: str = "central_lok_sabha",
        bill_repository: Optional[BillRepository] = None,
        source_snapshot_fn: Optional[Any] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 2.0,
        timeout_seconds: int = 60,
    ) -> None:
        super().__init__(
            source_id=source_id,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            timeout_seconds=timeout_seconds,
        )
        self._repo = bill_repository or BillRepository()
        self._source_snapshot_fn = source_snapshot_fn
        self._detector = LegislativeChangeDetector()

    def _do_check(self) -> list[ChangeEvent]:
        """
        Check Central sources for new or changed bills.

        If a source_snapshot_fn is provided (e.g. by tests), use it.
        Otherwise, compare existing repository records against themselves
        (no-op — real HTTP checks would be added via live adapters).
        """
        events: list[ChangeEvent] = []

        # Fetch current snapshot from source (injectable for testing)
        if self._source_snapshot_fn is not None:
            try:
                current_bills = self._source_snapshot_fn()
            except Exception as e:
                logger.error("Central source snapshot function failed: %s", e)
                raise

            # Load known bills from repository
            known_bills = self._load_known_bills()

            for current_rec in current_bills:
                bill_id = current_rec.get("bill_id") or current_rec.get("id", "")
                if not bill_id:
                    continue

                if bill_id not in known_bills:
                    # NEW_BILL
                    event = self._detector.detect_new_bill(
                        bill_id=bill_id,
                        current=current_rec,
                        source_id=self.source_id,
                        jurisdiction="central",
                        source_reference=current_rec.get("source_url"),
                    )
                    events.append(event)
                    logger.info("Central: NEW_BILL detected — %r", bill_id)
                else:
                    # Compare fields
                    field_events = self._detector.detect(
                        bill_id=bill_id,
                        previous=known_bills[bill_id],
                        current=current_rec,
                        source_id=self.source_id,
                        bill_title=current_rec.get("title", ""),
                        jurisdiction="central",
                        source_reference=current_rec.get("source_url"),
                    )
                    events.extend(field_events)

                    # Check PDF SHA-256
                    pdf_event = self._detector.detect_pdf_change(
                        bill_id=bill_id,
                        old_sha256=known_bills[bill_id].get("pdf_sha256"),
                        new_sha256=current_rec.get("pdf_sha256"),
                        source_id=self.source_id,
                        jurisdiction="central",
                        old_url=known_bills[bill_id].get("pdf_url"),
                        new_url=current_rec.get("pdf_url"),
                    )
                    if pdf_event:
                        events.append(pdf_event)
        else:
            # No live source injected — run a self-consistency check
            # (idempotent: known bills compared against themselves → NO_CHANGE)
            logger.info(
                "CentralMonitor[%s]: no live source injected — running self-check (no-op)",
                self.source_id,
            )

        return events

    def _load_known_bills(self) -> dict[str, dict[str, Any]]:
        """Load all known Central bills from repository as normalized dicts."""
        known: dict[str, dict[str, Any]] = {}
        try:
            bills = self._repo.get_all()
            for bill in bills:
                if hasattr(bill, "to_dict"):
                    d = bill.to_dict()
                elif isinstance(bill, dict):
                    d = dict(bill)
                else:
                    continue
                bill_id = d.get("bill_id") or d.get("id", "")
                if bill_id:
                    known[bill_id] = d
        except Exception as e:
            logger.error("Failed to load known Central bills: %s", e)
        return known

    def get_source_id(self) -> str:
        return self.source_id
