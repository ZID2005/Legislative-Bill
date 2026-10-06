"""
schemas/monitoring.py
=====================
Data schemas for the Legislative Monitoring & Update Scheduler system.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
Task 8.26 — Live Legislative Intelligence & Automatic Update Pipeline.

Contains:
- ChangeEventType      — classification of detected legislative changes
- RunStatus            — outcome status of a monitoring run
- SourceCategory       — [8.26] type of legislative source authority
- LiveStatus           — [8.26] verification state of a live record
- AnalyticalModelStatus — [8.26] whether a bill is in the frozen quant model
- MonitoringSource     — extended source descriptor with monitoring metadata
- ChangeEvent          — single detected change between two bill snapshots
- DocumentChangeEvent  — PDF-specific change record with SHA-256 comparison
- MonitoringRun        — auditable record of a complete monitoring run
- NotificationEvent    — backend event for future SaaS "What's New" feed
- LiveKnowledgeRecord  — [8.26] live discovery record SEPARATE from frozen model
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


class SourceCategory(str, Enum):
    """
    [Task 8.26] Categorical type of a legislative source authority.

    Only PARLIAMENTARY, LEGISLATIVE_DEPARTMENT, and GAZETTE sources
    are considered authoritative legislative truth. NEWS/MEDIA sources
    may be used as anticipation/diffusion signals only.
    """

    CENTRAL = "CENTRAL"
    STATE = "STATE"
    GAZETTE = "GAZETTE"
    PARLIAMENTARY = "PARLIAMENTARY"
    LEGISLATIVE_DEPARTMENT = "LEGISLATIVE_DEPARTMENT"
    OTHER_AUTHORITATIVE = "OTHER_AUTHORITATIVE"
    NEWS_MEDIA = "NEWS_MEDIA"          # NOT authoritative; signal only


class LiveStatus(str, Enum):
    """
    [Task 8.26] Verification state of a live legislative discovery record.

    DISCOVERED   — found by the pipeline, not yet independently verified
    VERIFIED     — confirmed by at least one authoritative official source
    UPDATED      — a previously verified record has received new information
    WITHDRAWN    — explicitly documented as withdrawn / lapsed
    SUPERSEDED   — replaced by a newer version or renumbered bill
    UNKNOWN      — status cannot be determined from available sources
    KNOWLEDGE_ONLY — in live knowledge base, explicitly NOT in analytical model
    """

    DISCOVERED = "DISCOVERED"
    VERIFIED = "VERIFIED"
    UPDATED = "UPDATED"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"
    KNOWLEDGE_ONLY = "KNOWLEDGE_ONLY"


class AnalyticalModelStatus(str, Enum):
    """
    [Task 8.26] Whether a legislative item is part of the frozen quantitative
    prediction model or simply lives in the live knowledge base.

    CRITICAL: A newly discovered bill MUST start as KNOWLEDGE_ONLY.
    Only an explicitly approved ingestion process may set MODELLED.
    No automated pipeline may assign MODELLED to a newly discovered bill.
    """

    MODELLED = "MODELLED"              # Frozen analytical baseline — do NOT auto-assign
    KNOWLEDGE_ONLY = "KNOWLEDGE_ONLY"  # Default for all live discoveries
    PENDING_REVIEW = "PENDING_REVIEW"  # Queued for analytical review
    NOT_ELIGIBLE = "NOT_ELIGIBLE"      # Explicitly ineligible (state, non-legislative, etc.)


# ---------------------------------------------------------------------------
# MonitoringSource
# ---------------------------------------------------------------------------


@dataclass
class MonitoringSource:
    """
    Extended descriptor for a legislative source monitored by the scheduler.

    Combines the original StateBillSource configuration with monitoring-specific
    operational metadata (polling interval, last run timestamps, error tracking).

    Task 8.26 additions:
    - authority_name: human-readable authority (e.g. 'Parliament of India')
    - source_category: SourceCategory enum classifying the authority type
    - health_status: computed health classification string
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
    # Task 8.26 fields
    authority_name: Optional[str] = None
    source_category: str = SourceCategory.PARLIAMENTARY.value
    health_status: Optional[str] = None  # computed; HEALTHY | DEGRADED | ERROR | NEVER_CHECKED | DISABLED

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
            # Task 8.26
            "authority_name": self.authority_name,
            "source_category": self.source_category,
            "health_status": self.health_status,
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
            # Task 8.26
            authority_name=data.get("authority_name"),
            source_category=data.get("source_category", SourceCategory.PARLIAMENTARY.value),
            health_status=data.get("health_status"),
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


# ---------------------------------------------------------------------------
# Task 8.26 — LiveKnowledgeRecord
# ---------------------------------------------------------------------------


@dataclass
class LiveKnowledgeRecord:
    """
    [Task 8.26] A legislative record in the LIVE KNOWLEDGE BASE.

    This is SEPARATE from the FROZEN ANALYTICAL DATASET.

    FIREWALL RULE
    =============
    - analytical_model_status ALWAYS defaults to KNOWLEDGE_ONLY.
    - No automated pipeline may set analytical_model_status = MODELLED.
    - Only an explicitly approved admin ingestion process may do so.
    - The guard method `assert_not_frozen_model()` enforces this at runtime.

    Lifecycle states (live_status)
    ==============================
    DISCOVERED   -> found by crawler, not verified
    VERIFIED     -> confirmed by >=1 authoritative source
    UPDATED      -> verified record received new data
    WITHDRAWN    -> explicitly lapsed / pulled back
    SUPERSEDED   -> replaced by a newer version / renumbering
    KNOWLEDGE_ONLY (terminal) -> in live KB, explicitly not in model
    """

    # Identity
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    canonical_bill_id: Optional[str] = None      # Matches existing bill if known
    bill_number: Optional[str] = None
    title: str = ""
    short_title: Optional[str] = None
    jurisdiction: str = "central"               # central | state
    state: Optional[str] = None

    # Live pipeline status
    live_status: str = LiveStatus.DISCOVERED.value
    discovered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    verified_at: Optional[str] = None
    last_updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    verification_source_id: Optional[str] = None
    verification_source_url: Optional[str] = None

    # *** Firewall: Frozen Model Status ***
    # MUST default to KNOWLEDGE_ONLY; never auto-changed by pipeline
    analytical_model_status: str = AnalyticalModelStatus.KNOWLEDGE_ONLY.value

    # Provenance
    discovered_by_source_id: str = ""
    discovered_by_run_id: Optional[str] = None
    source_url: Optional[str] = None
    source_category: str = SourceCategory.PARLIAMENTARY.value
    authority_name: Optional[str] = None

    # Document tracking (Task 8.26 Phase 9)
    document_url: Optional[str] = None
    document_hash_sha256: Optional[str] = None   # SHA-256 of fetched PDF/HTML
    document_retrieved_at: Optional[str] = None
    document_retrieval_failures: int = 0         # consecutive fetch failures
    document_retrieval_last_error: Optional[str] = None

    # Deduplication
    identity_matched: bool = False               # True if matched to existing bill
    duplicate_of_record_id: Optional[str] = None
    duplicate_discoveries: int = 0               # times this record was re-discovered

    # Content summary (normalized)
    introduction_date: Optional[str] = None
    assent_date: Optional[str] = None
    bill_status_text: Optional[str] = None       # raw status string from source
    summary: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    # Additional metadata
    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Guard                                                               #
    # ------------------------------------------------------------------ #

    def assert_not_frozen_model(self) -> None:
        """
        Raises ValueError if this record has been (incorrectly) marked MODELLED
        by any automated pipeline path.

        Call at the end of any automated ingestion step to enforce the firewall.
        Only skip this check in the explicit, human-approved analytical ingestion CLI.
        """
        if self.analytical_model_status == AnalyticalModelStatus.MODELLED.value:
            raise ValueError(
                f"LiveKnowledgeRecord {self.record_id!r} has analytical_model_status=MODELLED "
                "but was created/updated by an automated pipeline. "
                "Only the approved analytical ingestion process may set MODELLED. "
                "This is a Task 8.26 firewall violation."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "canonical_bill_id": self.canonical_bill_id,
            "bill_number": self.bill_number,
            "title": self.title,
            "short_title": self.short_title,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "live_status": self.live_status,
            "discovered_at": self.discovered_at,
            "verified_at": self.verified_at,
            "last_updated_at": self.last_updated_at,
            "verification_source_id": self.verification_source_id,
            "verification_source_url": self.verification_source_url,
            "analytical_model_status": self.analytical_model_status,
            "discovered_by_source_id": self.discovered_by_source_id,
            "discovered_by_run_id": self.discovered_by_run_id,
            "source_url": self.source_url,
            "source_category": self.source_category,
            "authority_name": self.authority_name,
            "document_url": self.document_url,
            "document_hash_sha256": self.document_hash_sha256,
            "document_retrieved_at": self.document_retrieved_at,
            "document_retrieval_failures": self.document_retrieval_failures,
            "document_retrieval_last_error": self.document_retrieval_last_error,
            "identity_matched": self.identity_matched,
            "duplicate_of_record_id": self.duplicate_of_record_id,
            "duplicate_discoveries": self.duplicate_discoveries,
            "introduction_date": self.introduction_date,
            "assent_date": self.assent_date,
            "bill_status_text": self.bill_status_text,
            "summary": self.summary,
            "tags": self.tags,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LiveKnowledgeRecord":
        return cls(
            record_id=data.get("record_id", str(uuid.uuid4())),
            canonical_bill_id=data.get("canonical_bill_id"),
            bill_number=data.get("bill_number"),
            title=data.get("title", ""),
            short_title=data.get("short_title"),
            jurisdiction=data.get("jurisdiction", "central"),
            state=data.get("state"),
            live_status=data.get("live_status", LiveStatus.DISCOVERED.value),
            discovered_at=data.get("discovered_at", datetime.now(timezone.utc).isoformat()),
            verified_at=data.get("verified_at"),
            last_updated_at=data.get("last_updated_at", datetime.now(timezone.utc).isoformat()),
            verification_source_id=data.get("verification_source_id"),
            verification_source_url=data.get("verification_source_url"),
            analytical_model_status=data.get(
                "analytical_model_status", AnalyticalModelStatus.KNOWLEDGE_ONLY.value
            ),
            discovered_by_source_id=data.get("discovered_by_source_id", ""),
            discovered_by_run_id=data.get("discovered_by_run_id"),
            source_url=data.get("source_url"),
            source_category=data.get("source_category", SourceCategory.PARLIAMENTARY.value),
            authority_name=data.get("authority_name"),
            document_url=data.get("document_url"),
            document_hash_sha256=data.get("document_hash_sha256"),
            document_retrieved_at=data.get("document_retrieved_at"),
            document_retrieval_failures=data.get("document_retrieval_failures", 0),
            document_retrieval_last_error=data.get("document_retrieval_last_error"),
            identity_matched=data.get("identity_matched", False),
            duplicate_of_record_id=data.get("duplicate_of_record_id"),
            duplicate_discoveries=data.get("duplicate_discoveries", 0),
            introduction_date=data.get("introduction_date"),
            assent_date=data.get("assent_date"),
            bill_status_text=data.get("bill_status_text"),
            summary=data.get("summary"),
            tags=data.get("tags", []),
            extra=data.get("extra", {}),
        )
