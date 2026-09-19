"""
services/monitoring/base_monitor.py
=====================================
Abstract base class for legislative source monitors.

Each monitor wraps a specific legislative source (Central or State) and
exposes a consistent `check_for_updates()` interface. Built-in retry logic
with exponential backoff ensures transient failures are handled gracefully.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.monitoring import ChangeEvent, ChangeEventType

logger = get_logger(__name__)


@dataclass
class MonitorResult:
    """
    Result returned by a monitor after checking a single source.

    Contains all change events detected, plus source-level metadata.
    """

    source_id: str
    success: bool
    events: list[ChangeEvent] = field(default_factory=list)
    new_bills: int = 0
    changed_bills: int = 0
    document_changes: int = 0
    bills_checked: int = 0
    error: Optional[str] = None
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "success": self.success,
            "new_bills": self.new_bills,
            "changed_bills": self.changed_bills,
            "document_changes": self.document_changes,
            "bills_checked": self.bills_checked,
            "error": self.error,
            "checked_at": self.checked_at,
            "duration_seconds": self.duration_seconds,
            "events_count": len(self.events),
        }


class BaseMonitor(ABC):
    """
    Abstract base for all legislative source monitors.

    Subclasses implement `_do_check()` to perform source-specific fetching
    and comparison. This base class provides:
    - Retry logic with exponential backoff
    - Error isolation (exceptions do not propagate to the runner)
    - Consistent result wrapping via MonitorResult
    """

    def __init__(
        self,
        source_id: str,
        max_retries: int = 3,
        retry_delay_seconds: float = 2.0,
        timeout_seconds: int = 60,
    ) -> None:
        self.source_id = source_id
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def _do_check(self) -> list[ChangeEvent]:
        """
        Perform the actual source check and return detected change events.

        Must NOT raise exceptions — catch internally and return ERROR events.
        """
        raise NotImplementedError

    def check_for_updates(self) -> MonitorResult:
        """
        Public interface: check this source for legislative updates.

        Implements retry logic. A single source failure returns a MonitorResult
        with success=False so the runner can continue with other sources.
        """
        start_time = time.monotonic()
        last_error: Optional[str] = None
        attempt = 0

        while attempt <= self.max_retries:
            try:
                logger.info(
                    "Checking source %s (attempt %d/%d)",
                    self.source_id,
                    attempt + 1,
                    self.max_retries + 1,
                )
                events = self._do_check()
                duration = time.monotonic() - start_time

                # Tally event types
                new_bills = sum(
                    1
                    for e in events
                    if e.event_type == ChangeEventType.NEW_BILL
                )
                changed_bills = sum(
                    1
                    for e in events
                    if e.event_type
                    in (
                        ChangeEventType.STATUS_CHANGED,
                        ChangeEventType.METADATA_CHANGED,
                        ChangeEventType.DATE_CHANGED,
                    )
                )
                doc_changes = sum(
                    1
                    for e in events
                    if e.event_type == ChangeEventType.DOCUMENT_CHANGED
                )

                logger.info(
                    "Source %s: %d new, %d changed, %d doc changes in %.1fs",
                    self.source_id,
                    new_bills,
                    changed_bills,
                    doc_changes,
                    duration,
                )

                return MonitorResult(
                    source_id=self.source_id,
                    success=True,
                    events=events,
                    new_bills=new_bills,
                    changed_bills=changed_bills,
                    document_changes=doc_changes,
                    duration_seconds=duration,
                )

            except Exception as exc:
                last_error = str(exc)
                attempt += 1
                if attempt <= self.max_retries:
                    delay = self.retry_delay_seconds * (2 ** (attempt - 1))
                    logger.warning(
                        "Source %s failed (attempt %d): %s — retrying in %.1fs",
                        self.source_id,
                        attempt,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Source %s failed after %d attempts: %s",
                        self.source_id,
                        self.max_retries + 1,
                        exc,
                    )

        duration = time.monotonic() - start_time
        # Return failure result — do NOT re-raise
        error_event = ChangeEvent(
            bill_id="",
            source_id=self.source_id,
            event_type=ChangeEventType.ERROR,
            error_message=last_error,
        )
        return MonitorResult(
            source_id=self.source_id,
            success=False,
            events=[error_event],
            error=last_error,
            duration_seconds=duration,
        )
