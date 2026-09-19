"""
schemas/monitoring.py
=====================
Data schemas for the Legislative Monitoring & Update Scheduler system.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.

Contains:
- ChangeEventType  — classification of detected legislative changes
- RunStatus        — outcome status of a monitoring run
- MonitoringSource — extended source descriptor with monitoring metadata
- ChangeEvent      — single detected change between two bill snapshots
- DocumentChangeEvent — PDF-specific change record with SHA-256 comparison
- MonitoringRun    — auditable record of a complete monitoring run
- NotificationEvent — backend event for future SaaS "What's New" feed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ChangeEventType(str, Enum):
    """Classification of a detected legislative change."""

    NEW_BILL = "NEW_BILL"
    STATUS_CHANGED = "STATUS_CHANGED"
    METADATA_CHANGED = "METADATA_CHANGED"
    DATE_CHANGED = "DATE_CHANGED"
    DOCUMENT_CHANGED = "DOCUMENT_CHANGED"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    NO_CHANGE = "NO_CHANGE"
    ERROR = "ERROR"


class RunStatus(str, Enum):
    """Overall outcome status of a monitoring run."""

    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    RUNNING = "RUNNING"


class FieldSupportLevel(str, Enum):
    """Degree to which a source supports a particular metadata field."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"


class SourceStatus(str, Enum):
    """Implementation and availability status of a monitoring source."""

    IMPLEMENTED = "IMPLEMENTED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    PLANNED = "PLANNED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


# ---------------------------------------------------------------------------
# MonitoringSource
# ---------------------------------------------------------------------------


@dataclass
class MonitoringSource:
    """
    Extended descriptor for a legislative source monitored by the scheduler.

    Combines the original StateBillSource configuration with monitoring-specific
    operational metadata (polling interval, last run timestamps, error tracking).
    """

    source_id: str
    jurisdiction: str  # "central" | "state"
    state: Optional[str]
    source_name: str
    source_url: str
    adapter: Optional[str]
    enabled: bool = True
    polling_interval_hours: int = 24
    priority: int = 10
    source_type: str = "html_table"
    status: str = SourceStatus.IMPLEMENTED.value
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error_at: Optional[str] = None
    last_error: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "adapter": self.adapter,
            "enabled": self.enabled,
            "polling_interval_hours": self.polling_interval_hours,
            "priority": self.priority,
            "source_type": self.source_type,
            "status": self.status,
            "last_checked_at": self.last_checked_at,
            "last_success_at": self.last_success_at,
            "last_error_at": self.last_error_at,
            "last_error": self.last_error,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MonitoringSource":
        return cls(
            source_id=data["source_id"],
            jurisdiction=data.get("jurisdiction", "central"),
            state=data.get("state"),
            source_name=data.get("source_name", ""),
            source_url=data.get("source_url", ""),
            adapter=data.get("adapter"),
            enabled=data.get("enabled", True),
            polling_interval_hours=data.get("polling_interval_hours", 24),
            priority=data.get("priority", 10),
            source_type=data.get("source_type", "html_table"),
            status=data.get("status", SourceStatus.IMPLEMENTED.value),
            last_checked_at=data.get("last_checked_at"),
            last_success_at=data.get("last_success_at"),
            last_error_at=data.get("last_error_at"),
            last_error=data.get("last_error"),
            notes=data.get("notes"),
        )


# ---------------------------------------------------------------------------
# ChangeEvent
# ---------------------------------------------------------------------------


@dataclass
class ChangeEvent:
    """
    Record of a single detected change in a legislative bill.

    Captures old and new values deterministically so that audit trails
    and the "What's New" feed can reconstruct exactly what changed.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bill_id: str = ""
    bill_title: str = ""
    jurisdiction: str = "central"
    state: Optional[str] = None
    source_id: str = ""
    event_type: ChangeEventType = ChangeEventType.NO_CHANGE
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_reference: Optional[str] = None
    confidence: float = 1.0
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "source_id": self.source_id,
            "event_type": self.event_type.value
            if isinstance(self.event_type, ChangeEventType)
            else str(self.event_type),
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "detected_at": self.detected_at,
            "source_reference": self.source_reference,
            "confidence": self.confidence,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChangeEvent":
        try:
            event_type = ChangeEventType(data.get("event_type", "NO_CHANGE"))
        except ValueError:
            event_type = ChangeEventType.NO_CHANGE
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            bill_id=data.get("bill_id", ""),
            bill_title=data.get("bill_title", ""),
            jurisdiction=data.get("jurisdiction", "central"),
            state=data.get("state"),
            source_id=data.get("source_id", ""),
            event_type=event_type,
            field_name=data.get("field_name"),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            detected_at=data.get("detected_at", datetime.now(timezone.utc).isoformat()),
            source_reference=data.get("source_reference"),
            confidence=data.get("confidence", 1.0),
            error_message=data.get("error_message"),
        )


# ---------------------------------------------------------------------------
# DocumentChangeEvent
# ---------------------------------------------------------------------------


@dataclass
class DocumentChangeEvent:
    """
    Extended change event specifically for PDF document changes.

    Uses SHA-256 hashes to detect genuine document content changes,
    separate from bill metadata changes.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bill_id: str = ""
    source_id: str = ""
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    previous_sha256: Optional[str] = None
    new_sha256: Optional[str] = None
    previous_url: Optional[str] = None
    new_url: Optional[str] = None
    document_size_bytes: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "bill_id": self.bill_id,
            "source_id": self.source_id,
            "detected_at": self.detected_at,
            "previous_sha256": self.previous_sha256,
            "new_sha256": self.new_sha256,
            "previous_url": self.previous_url,
            "new_url": self.new_url,
            "document_size_bytes": self.document_size_bytes,
        }


# ---------------------------------------------------------------------------
# MonitoringRun
# ---------------------------------------------------------------------------


@dataclass
class MonitoringRun:
    """
    Auditable record of a complete monitoring scheduler run.

    Created at the start of each run and updated as sources are processed.
    One failed source must not prevent other sources from completing.
    """

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: RunStatus = RunStatus.RUNNING
    sources_checked: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0
    new_bills: int = 0
    changed_bills: int = 0
    document_changes: int = 0
    errors: int = 0
    source_results: list[dict[str, Any]] = field(default_factory=list)
    trigger: str = "manual"  # "manual" | "scheduled"

    def mark_complete(self) -> None:
        """Set completion timestamp and duration."""
        self.completed_at = datetime.now(timezone.utc).isoformat()
        try:
            started = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            completed = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
            self.duration_seconds = (completed - started).total_seconds()
        except Exception:
            self.duration_seconds = None

        # Determine final status
        if self.sources_failed == 0:
            self.status = RunStatus.SUCCESS
        elif self.sources_succeeded > 0:
            self.status = RunStatus.PARTIAL_SUCCESS
        else:
            self.status = RunStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value
            if isinstance(self.status, RunStatus)
            else str(self.status),
            "sources_checked": self.sources_checked,
            "sources_succeeded": self.sources_succeeded,
            "sources_failed": self.sources_failed,
            "new_bills": self.new_bills,
            "changed_bills": self.changed_bills,
            "document_changes": self.document_changes,
            "errors": self.errors,
            "source_results": self.source_results,
            "trigger": self.trigger,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MonitoringRun":
        try:
            status = RunStatus(data.get("status", RunStatus.RUNNING.value))
        except ValueError:
            status = RunStatus.RUNNING
        obj = cls(
            run_id=data.get("run_id", str(uuid.uuid4())),
            started_at=data.get("started_at", datetime.now(timezone.utc).isoformat()),
            completed_at=data.get("completed_at"),
            duration_seconds=data.get("duration_seconds"),
            status=status,
            sources_checked=data.get("sources_checked", 0),
            sources_succeeded=data.get("sources_succeeded", 0),
            sources_failed=data.get("sources_failed", 0),
            new_bills=data.get("new_bills", 0),
            changed_bills=data.get("changed_bills", 0),
            document_changes=data.get("document_changes", 0),
            errors=data.get("errors", 0),
            source_results=data.get("source_results", []),
            trigger=data.get("trigger", "manual"),
        )
        return obj


# ---------------------------------------------------------------------------
# NotificationEvent
# ---------------------------------------------------------------------------


@dataclass
class NotificationEvent:
    """
    Backend event for the "What's New" legislative event feed.

    Designed for future SaaS frontend consumption. No email/push delivery yet.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: ChangeEventType = ChangeEventType.NEW_BILL
    bill_id: str = ""
    bill_title: str = ""
    jurisdiction: str = "central"
    state: Optional[str] = None
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: Optional[str] = None
    summary: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value
            if isinstance(self.event_type, ChangeEventType)
            else str(self.event_type),
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "detected_at": self.detected_at,
            "source": self.source,
            "summary": self.summary,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationEvent":
        try:
            event_type = ChangeEventType(data.get("event_type", "NEW_BILL"))
        except ValueError:
            event_type = ChangeEventType.NEW_BILL
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=event_type,
            bill_id=data.get("bill_id", ""),
            bill_title=data.get("bill_title", ""),
            jurisdiction=data.get("jurisdiction", "central"),
            state=data.get("state"),
            detected_at=data.get("detected_at", datetime.now(timezone.utc).isoformat()),
            source=data.get("source"),
            summary=data.get("summary"),
            metadata=data.get("metadata", {}),
        )
