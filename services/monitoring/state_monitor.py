"""
services/monitoring/state_monitor.py
======================================
Monitor for Indian State legislative sources.

Wraps the four existing State adapters (AP, Karnataka, Kerala, Telangana)
and detects changes in state bills by comparing against the
StateKnowledgeRepository as the "known" baseline.

CRITICAL PROTECTIONS:
- NEVER creates State market predictions.
- State predictions must remain EXACTLY 0.
- Monitoring may update: state knowledge, economic assessment,
  company exposure, and discovery records ONLY.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from schemas.monitoring import ChangeEvent, ChangeEventType
from services.monitoring.base_monitor import BaseMonitor
from services.monitoring.change_detector import LegislativeChangeDetector
from storage.state_knowledge_repository import StateKnowledgeRepository

logger = get_logger(__name__)

# Mapping from source_id to state name (for the four implemented pilot states)
_STATE_SOURCE_MAP: dict[str, str] = {
    "state_andhra_pradesh": "Andhra Pradesh",
    "state_karnataka": "Karnataka",
    "state_kerala": "Kerala",
    "state_telangana": "Telangana",
}


class StateMonitor(BaseMonitor):
    """
    Monitor for a single Indian State legislative source.

    Designed for the four implemented pilot states:
    Andhra Pradesh, Karnataka, Kerala, Telangana.

    Uses the existing State adapters (via inject or direct import) and
    compares discovered bill listings against the StateKnowledgeRepository.

    In production, `source_snapshot_fn` would call the real adapter's
    `discover_bills()` asynchronously. For testing, fixture data is injected.
    """

    def __init__(
        self,
        source_id: str,
        state_name: Optional[str] = None,
        knowledge_repository: Optional[StateKnowledgeRepository] = None,
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
        self._state_name = state_name or _STATE_SOURCE_MAP.get(source_id, "")
        self._repo = knowledge_repository or StateKnowledgeRepository()
        self._source_snapshot_fn = source_snapshot_fn
        self._detector = LegislativeChangeDetector()

    def _do_check(self) -> list[ChangeEvent]:
        """
        Check a State legislative source for new or changed bills.

        IMPORTANT: State predictions are NEVER created here.
        """
        events: list[ChangeEvent] = []

        if self._source_snapshot_fn is not None:
            try:
                current_bills = self._source_snapshot_fn()
            except Exception as e:
                logger.error(
                    "StateMonitor[%s] source snapshot failed: %s",
                    self.source_id,
                    e,
                )
                raise

            known_bills = self._load_known_state_bills()

            for current_rec in current_bills:
                bill_id = current_rec.get("bill_id") or current_rec.get("id", "")
                title = current_rec.get("title", "")

                # Build a canonical ID if not provided
                if not bill_id:
                    bill_id = _make_state_bill_id(self._state_name, current_rec)
                if not bill_id:
                    continue

                if bill_id not in known_bills:
                    # NEW State bill detected
                    event = self._detector.detect_new_bill(
                        bill_id=bill_id,
                        current=current_rec,
                        source_id=self.source_id,
                        jurisdiction="state",
                        state=self._state_name,
                        source_reference=current_rec.get("source_url"),
                    )
                    events.append(event)
                    logger.info(
                        "State[%s]: NEW_BILL detected — %r",
                        self._state_name,
                        bill_id,
                    )
                else:
                    # Compare fields
                    field_events = self._detector.detect(
                        bill_id=bill_id,
                        previous=known_bills[bill_id],
                        current=current_rec,
                        source_id=self.source_id,
                        bill_title=title,
                        jurisdiction="state",
                        state=self._state_name,
                        source_reference=current_rec.get("source_url"),
                    )
                    events.extend(field_events)

                    # Check PDF SHA-256
                    pdf_event = self._detector.detect_pdf_change(
                        bill_id=bill_id,
                        old_sha256=known_bills[bill_id].get("pdf_sha256"),
                        new_sha256=current_rec.get("pdf_sha256"),
                        source_id=self.source_id,
                        jurisdiction="state",
                        state=self._state_name,
                        old_url=known_bills[bill_id].get("pdf_url"),
                        new_url=current_rec.get("pdf_url"),
                    )
                    if pdf_event:
                        events.append(pdf_event)
        else:
            logger.info(
                "StateMonitor[%s]: no live source injected — running self-check (no-op)",
                self.source_id,
            )

        return events

    def _load_known_state_bills(self) -> dict[str, dict[str, Any]]:
        """Load known state bills from StateKnowledgeRepository as normalized dicts."""
        known: dict[str, dict[str, Any]] = {}
        try:
            records = self._repo.get_by_state(self._state_name)
            for rec in records:
                if hasattr(rec, "to_dict"):
                    d = rec.to_dict()
                elif isinstance(rec, dict):
                    d = dict(rec)
                else:
                    continue
                bill_id = d.get("bill_id") or d.get("id", "")
                if bill_id:
                    known[bill_id] = d
        except Exception as e:
            logger.error(
                "Failed to load known State bills for %s: %s",
                self._state_name,
                e,
            )
        return known

    def get_source_id(self) -> str:
        return self.source_id


def _make_state_bill_id(state: str, rec: dict[str, Any]) -> str:
    """Generate a stable ID for a State bill record if none is provided."""
    from utils.text_utils import slugify
    from utils.state_normalizer import normalize_state

    state_slug = slugify(normalize_state(state) or state)
    bill_num = rec.get("bill_number", "")
    year = rec.get("year", "")
    title = rec.get("title", "")

    if bill_num and year:
        return f"{state_slug}-bill-{bill_num}-{year}".lower().replace(" ", "-")
    if title:
        return f"{state_slug}-{slugify(title)}"
    return ""
