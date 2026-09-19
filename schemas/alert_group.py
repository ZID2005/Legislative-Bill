"""
schemas/alert_group.py
======================
AlertGroup schema and deterministic aggregation identity models.

Groups related AlertEvents along technical and entity dimensions
(BILL, COMPANY, SECTOR, INDUSTRY, STATE, JURISDICTION, WATCHLIST, EVENT)
within a configurable aggregation window to reduce alert fatigue.

Task 8.13.5 — Alert Aggregation & Digest Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any, Optional
import uuid

from schemas.alert import AlertEvent, AlertSeverity
from schemas.watchlist import WatchlistEntityType


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_SEVERITY_ORDER: dict[AlertSeverity, int] = {
    AlertSeverity.INFO: 1,
    AlertSeverity.LOW: 2,
    AlertSeverity.MEDIUM: 3,
    AlertSeverity.HIGH: 4,
    AlertSeverity.CRITICAL: 5,
}


def severity_rank(sev: AlertSeverity | str) -> int:
    """Return integer rank (1-5) for severity comparison."""
    if isinstance(sev, AlertSeverity):
        return _SEVERITY_ORDER.get(sev, 2)
    try:
        norm = AlertSeverity(str(sev).strip().upper())
        return _SEVERITY_ORDER.get(norm, 2)
    except ValueError:
        return 2


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AlertGroupType(str, Enum):
    """Supported technical and business grouping dimensions."""

    BILL = "BILL"
    COMPANY = "COMPANY"
    SECTOR = "SECTOR"
    INDUSTRY = "INDUSTRY"
    STATE = "STATE"
    JURISDICTION = "JURISDICTION"
    WATCHLIST = "WATCHLIST"
    EVENT = "EVENT"


class AlertGroupStatus(str, Enum):
    """Lifecycle state of an alert group."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# Aggregation Key Computation
# ---------------------------------------------------------------------------


def compute_aggregation_key(
    tenant_id: str,
    user_id: str,
    watchlist_id: Optional[str],
    group_type: AlertGroupType | str,
    entity_type: Optional[WatchlistEntityType | str],
    entity_id: Optional[str],
    window_id: str,
) -> str:
    """
    Compute a deterministic aggregation key preventing unrelated events from merging.

    Key structure:
      SHA-256(tenant_id || user_id || watchlist_id || group_type || entity_type || entity_id || window_id)
    """
    t = (tenant_id or "").strip()
    u = (user_id or "").strip()
    w = (watchlist_id or "").strip()
    gt = group_type.value if isinstance(group_type, AlertGroupType) else str(group_type).strip().upper()
    et = (
        entity_type.value
        if isinstance(entity_type, WatchlistEntityType)
        else (str(entity_type).strip().upper() if entity_type else "")
    )
    ei = (entity_id or "").strip().lower()
    win = (window_id or "").strip()

    payload = f"{t}|{u}|{w}|{gt}|{et}|{ei}|{win}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# AlertGroup Dataclass
# ---------------------------------------------------------------------------


@dataclass
class AlertGroup:
    """
    Aggregated collection of related AlertEvents belonging to a single user.

    Attributes
    ----------
    group_id : str
        Deterministic or unique identifier for the group.
    tenant_id : str
        Tenant identifier for multi-tenant isolation.
    user_id : str
        Owner user ID.
    watchlist_id : Optional[str]
        Associated watchlist ID if scoped to a specific watchlist.
    group_type : AlertGroupType
        Primary dimension of aggregation (BILL, COMPANY, SECTOR, etc.).
    aggregation_key : str
        Deterministic key ensuring idempotent grouping.
    title : str
        Headline summarizing the aggregated alert group.
    summary : str
        Structured or aggregated summary of underlying events.
    alert_count : int
        Count of aggregated underlying AlertEvents.
    first_event_at : str
        Timestamp of the earliest event in the group.
    latest_event_at : str
        Timestamp of the most recent event in the group.
    severity : AlertSeverity
        Maximum severity among all aggregated events.
    event_ids : list[str]
        Ordered, deduplicated list of underlying AlertEvent IDs.
    affected_entity_ids : list[str]
        Canonical identifiers of entities impacted.
    status : AlertGroupStatus
        Active or archived lifecycle status.
    created_at : str
        UTC ISO timestamp of group creation.
    updated_at : str
        UTC ISO timestamp of most recent group update.
    metadata : dict[str, Any]
        Supplementary context, entity attributes, and structured content.
    """

    group_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    watchlist_id: Optional[str] = None
    group_type: AlertGroupType = AlertGroupType.BILL
    aggregation_key: str = ""
    title: str = ""
    summary: str = ""
    alert_count: int = 0
    first_event_at: str = field(default_factory=_utcnow_iso)
    latest_event_at: str = field(default_factory=_utcnow_iso)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    event_ids: list[str] = field(default_factory=list)
    affected_entity_ids: list[str] = field(default_factory=list)
    status: AlertGroupStatus = AlertGroupStatus.ACTIVE
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.group_id:
            if self.aggregation_key:
                self.group_id = f"grp_{self.aggregation_key[:16]}"
            else:
                self.group_id = str(uuid.uuid4())
        self.alert_count = len(self.event_ids)

    def validate(self) -> None:
        """Validate group invariants."""
        if not self.group_id or not self.group_id.strip():
            raise ValueError("group_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not isinstance(self.group_type, AlertGroupType):
            try:
                self.group_type = AlertGroupType(str(self.group_type).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid group_type '{self.group_type}'")
        if not isinstance(self.severity, AlertSeverity):
            try:
                self.severity = AlertSeverity(str(self.severity).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid severity '{self.severity}'")
        if not isinstance(self.status, AlertGroupStatus):
            try:
                self.status = AlertGroupStatus(str(self.status).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid status '{self.status}'")

    def add_event(self, event: AlertEvent) -> bool:
        """
        Add an AlertEvent to this group idempotently.

        Returns True if the event was newly added, False if it was already present.
        """
        if event.alert_event_id in self.event_ids:
            return False

        self.event_ids.append(event.alert_event_id)
        self.alert_count = len(self.event_ids)

        # Update timestamps
        if not self.first_event_at or event.created_at < self.first_event_at:
            self.first_event_at = event.created_at
        if not self.latest_event_at or event.created_at > self.latest_event_at:
            self.latest_event_at = event.created_at

        # Update severity to max
        if severity_rank(event.severity) > severity_rank(self.severity):
            self.severity = event.severity

        # Track affected entity
        if event.entity_id and event.entity_id not in self.affected_entity_ids:
            self.affected_entity_ids.append(event.entity_id)

        self.updated_at = _utcnow_iso()
        return True

    def mark_as_archived(self) -> None:
        """Archive the group."""
        self.status = AlertGroupStatus.ARCHIVED
        self.updated_at = _utcnow_iso()

    def mark_as_active(self) -> None:
        """Re-activate the group."""
        self.status = AlertGroupStatus.ACTIVE
        self.updated_at = _utcnow_iso()

    def to_dict(self) -> dict[str, Any]:
        """Serialize AlertGroup to dictionary."""
        return {
            "group_id": self.group_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "watchlist_id": self.watchlist_id,
            "group_type": self.group_type.value
            if isinstance(self.group_type, AlertGroupType)
            else str(self.group_type),
            "aggregation_key": self.aggregation_key,
            "title": self.title,
            "summary": self.summary,
            "alert_count": self.alert_count,
            "first_event_at": self.first_event_at,
            "latest_event_at": self.latest_event_at,
            "severity": self.severity.value
            if isinstance(self.severity, AlertSeverity)
            else str(self.severity),
            "event_ids": list(self.event_ids),
            "affected_entity_ids": list(self.affected_entity_ids),
            "status": self.status.value
            if isinstance(self.status, AlertGroupStatus)
            else str(self.status),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertGroup":
        """Deserialize AlertGroup from dictionary."""
        raw_gt = data.get("group_type", AlertGroupType.BILL.value)
        if isinstance(raw_gt, AlertGroupType):
            gt = raw_gt
        else:
            try:
                gt = AlertGroupType(str(raw_gt).strip().upper())
            except ValueError:
                gt = AlertGroupType.BILL

        raw_sev = data.get("severity", AlertSeverity.MEDIUM.value)
        if isinstance(raw_sev, AlertSeverity):
            sev = raw_sev
        else:
            try:
                sev = AlertSeverity(str(raw_sev).strip().upper())
            except ValueError:
                sev = AlertSeverity.MEDIUM

        raw_st = data.get("status", AlertGroupStatus.ACTIVE.value)
        if isinstance(raw_st, AlertGroupStatus):
            st = raw_st
        else:
            try:
                st = AlertGroupStatus(str(raw_st).strip().upper())
            except ValueError:
                st = AlertGroupStatus.ACTIVE

        ev_ids = list(data.get("event_ids", []))
        obj = cls(
            group_id=data.get("group_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            watchlist_id=data.get("watchlist_id"),
            group_type=gt,
            aggregation_key=data.get("aggregation_key", ""),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            alert_count=data.get("alert_count", len(ev_ids)),
            first_event_at=data.get("first_event_at", _utcnow_iso()),
            latest_event_at=data.get("latest_event_at", _utcnow_iso()),
            severity=sev,
            event_ids=ev_ids,
            affected_entity_ids=list(data.get("affected_entity_ids", [])),
            status=st,
            created_at=data.get("created_at", _utcnow_iso()),
            updated_at=data.get("updated_at", _utcnow_iso()),
            metadata=data.get("metadata", {}),
        )
        obj.validate()
        return obj
