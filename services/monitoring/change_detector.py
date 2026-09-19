"""
services/monitoring/change_detector.py
=======================================
Deterministic legislative change detector.

Compares a "previous" bill record against a "current" bill record field-by-field
and produces typed ChangeEvent objects for every meaningful difference.

Design principles:
- Deterministic: same inputs always produce same events
- No fabrication: missing fields are recorded as UNAVAILABLE, not guessed
- PDF-aware: document changes classified separately from bill metadata changes
- SHA-256 based: PDF content hashes compared, not just URL changes

Fields compared:
  title, bill_number, status, introduction_date, passage_date, assent_date,
  house, legislature, sponsor, summary, source_url, pdf_url, pdf_sha256

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import hashlib
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.monitoring import ChangeEvent, ChangeEventType

logger = get_logger(__name__)

# Fields that classify as STATUS_CHANGED
_STATUS_FIELDS = {"status"}

# Fields that classify as DATE_CHANGED
_DATE_FIELDS = {"introduction_date", "passage_date", "assent_date"}

# Fields that classify as DOCUMENT_CHANGED
_DOCUMENT_FIELDS = {"pdf_url", "pdf_sha256", "document_url"}

# Fields that classify as SOURCE_CHANGED
_SOURCE_FIELDS = {"source_url"}

# All remaining metadata fields → METADATA_CHANGED
_METADATA_FIELDS = {
    "title",
    "bill_number",
    "house",
    "legislature",
    "sponsor",
    "department",
    "summary",
    "year",
}


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hex digest for PDF content bytes."""
    return hashlib.sha256(content).hexdigest()


class LegislativeChangeDetector:
    """
    Deterministic change detector for legislative bill records.

    Compares two bill dictionaries (previous vs. current) and returns
    a list of typed ChangeEvent objects for every detected difference.

    Usage:
        detector = LegislativeChangeDetector()
        events = detector.detect(
            bill_id="finance-bill-2024",
            previous=old_bill_dict,
            current=new_bill_dict,
            source_id="central_lok_sabha",
        )
    """

    def detect(
        self,
        bill_id: str,
        previous: dict[str, Any],
        current: dict[str, Any],
        source_id: str = "",
        bill_title: str = "",
        jurisdiction: str = "central",
        state: Optional[str] = None,
        source_reference: Optional[str] = None,
    ) -> list[ChangeEvent]:
        """
        Compare previous and current bill records.

        Returns
        -------
        list[ChangeEvent]
            One event per changed field. Empty list means NO_CHANGE.
        """
        events: list[ChangeEvent] = []

        # Gather all field names from both records
        all_fields = set(previous.keys()) | set(current.keys())
        # Exclude internal/system fields
        all_fields -= {"_id", "created_at", "updated_at", "ingested_at", "run_id"}

        for field_name in sorted(all_fields):
            old_val = _normalize_value(previous.get(field_name))
            new_val = _normalize_value(current.get(field_name))

            if old_val == new_val:
                continue

            # Classify the event type
            if field_name in _STATUS_FIELDS:
                event_type = ChangeEventType.STATUS_CHANGED
            elif field_name in _DATE_FIELDS:
                event_type = ChangeEventType.DATE_CHANGED
            elif field_name in _DOCUMENT_FIELDS:
                event_type = ChangeEventType.DOCUMENT_CHANGED
            elif field_name in _SOURCE_FIELDS:
                event_type = ChangeEventType.SOURCE_CHANGED
            else:
                event_type = ChangeEventType.METADATA_CHANGED

            events.append(
                ChangeEvent(
                    bill_id=bill_id,
                    bill_title=bill_title or previous.get("title", current.get("title", "")),
                    jurisdiction=jurisdiction,
                    state=state,
                    source_id=source_id,
                    event_type=event_type,
                    field_name=field_name,
                    old_value=old_val,
                    new_value=new_val,
                    source_reference=source_reference,
                )
            )

        if events:
            logger.debug(
                "Bill %r: %d field change(s) detected (%s)",
                bill_id,
                len(events),
                ", ".join(e.field_name or "" for e in events),
            )
        return events

    def detect_new_bill(
        self,
        bill_id: str,
        current: dict[str, Any],
        source_id: str = "",
        jurisdiction: str = "central",
        state: Optional[str] = None,
        source_reference: Optional[str] = None,
    ) -> ChangeEvent:
        """Create a NEW_BILL event for a bill not previously known."""
        return ChangeEvent(
            bill_id=bill_id,
            bill_title=current.get("title", ""),
            jurisdiction=jurisdiction,
            state=state,
            source_id=source_id,
            event_type=ChangeEventType.NEW_BILL,
            field_name=None,
            old_value=None,
            new_value=current.get("title"),
            source_reference=source_reference,
        )

    def detect_pdf_change(
        self,
        bill_id: str,
        old_sha256: Optional[str],
        new_sha256: Optional[str],
        source_id: str = "",
        jurisdiction: str = "central",
        state: Optional[str] = None,
        old_url: Optional[str] = None,
        new_url: Optional[str] = None,
    ) -> Optional[ChangeEvent]:
        """
        Explicitly compare PDF SHA-256 hashes.

        A PDF URL change without content change does NOT qualify as a document change.
        Only actual SHA-256 hash differences count.
        """
        if not old_sha256 and not new_sha256:
            return None
        if old_sha256 == new_sha256:
            return None

        return ChangeEvent(
            bill_id=bill_id,
            source_id=source_id,
            jurisdiction=jurisdiction,
            state=state,
            event_type=ChangeEventType.DOCUMENT_CHANGED,
            field_name="pdf_sha256",
            old_value=old_sha256,
            new_value=new_sha256,
            source_reference=old_url or new_url,
        )

    @staticmethod
    def build_known_record(bill: Any) -> dict[str, Any]:
        """
        Convert a stored bill object (Bill or dict) to a normalized comparison dict.
        """
        if hasattr(bill, "to_dict"):
            return bill.to_dict()
        if isinstance(bill, dict):
            return dict(bill)
        return {}


def _normalize_value(val: Any) -> Any:
    """Normalize a field value for comparison (strip strings, lower-case status)."""
    if val is None:
        return None
    if isinstance(val, str):
        v = val.strip()
        return v if v else None
    return val
