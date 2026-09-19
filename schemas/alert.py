"""
schemas/alert.py
================
Alert rules, alert events, notifications, and alert preferences schemas.

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any, Optional
import uuid

from schemas.watchlist import WatchlistEntityType


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AlertType(str, Enum):
    """Supported alert classification types according to Task 8.13.1 design."""

    NEW_BILL = "NEW_BILL"
    BILL_STATUS_CHANGE = "BILL_STATUS_CHANGE"
    BILL_VERSION_CHANGE = "BILL_VERSION_CHANGE"
    BILL_DOCUMENT_CHANGE = "BILL_DOCUMENT_CHANGE"
    NEW_COMPANY_EXPOSURE = "NEW_COMPANY_EXPOSURE"
    EXPOSURE_CHANGE = "EXPOSURE_CHANGE"
    SECTOR_IMPACT = "SECTOR_IMPACT"
    STATE_IMPACT = "STATE_IMPACT"
    LEGISLATIVE_MONITORING_CHANGE = "LEGISLATIVE_MONITORING_CHANGE"


class AlertSeverity(str, Enum):
    """Severity tier for alert events."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationChannel(str, Enum):
    """Delivery channels for alert notifications."""

    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"


class NotificationStatus(str, Enum):
    """Status of notification delivery."""

    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    READ = "READ"
    SUPPRESSED = "SUPPRESSED"


class NotificationType(str, Enum):
    """Supported notification types for in-app center and dispatch."""

    ALERT = "ALERT"
    DIGEST = "DIGEST"
    LEGISLATIVE_UPDATE = "LEGISLATIVE_UPDATE"
    COMPANY_EXPOSURE = "COMPANY_EXPOSURE"
    BILL_UPDATE = "BILL_UPDATE"
    STATE_UPDATE = "STATE_UPDATE"
    SYSTEM = "SYSTEM"


class NotificationSourceType(str, Enum):
    """Source object classification generating the notification."""

    ALERT_EVENT = "ALERT_EVENT"
    ALERT_GROUP = "ALERT_GROUP"
    DIGEST = "DIGEST"
    SYSTEM = "SYSTEM"


class DigestFrequency(str, Enum):
    """Cadence for alert delivery."""

    REAL_TIME = "REAL_TIME"
    DAILY_DIGEST = "DAILY_DIGEST"
    WEEKLY_DIGEST = "WEEKLY_DIGEST"


# ---------------------------------------------------------------------------
# Deduplication Key Helper
# ---------------------------------------------------------------------------


def compute_dedup_key(
    user_id: str,
    watchlist_id: Optional[str],
    source_event_id: str,
    alert_type: str | AlertType,
) -> str:
    """
    Deterministic deduplication identity designed in 8.13.1:

    dedup_key = SHA-256(user_id || watchlist_id || source_event_id || alert_type)
    """
    u = (user_id or "").strip()
    w = (watchlist_id or "").strip()
    s = (source_event_id or "").strip()
    a = alert_type.value if isinstance(alert_type, AlertType) else str(alert_type).strip()

    payload = f"{u}|{w}|{s}|{a}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_notification_dedup_key(
    tenant_id: str,
    user_id: str,
    source_type: str | NotificationSourceType,
    source_id: str,
    channel: str | NotificationChannel = NotificationChannel.IN_APP,
) -> str:
    """
    Deterministic deduplication identity for notifications:
    dedup_key = SHA-256(tenant_id || user_id || source_type || source_id || channel)
    """
    t = (tenant_id or "").strip()
    u = (user_id or "").strip()
    st = (
        source_type.value
        if isinstance(source_type, NotificationSourceType)
        else str(source_type).strip().upper()
    )
    si = (source_id or "").strip()
    ch = (
        channel.value
        if isinstance(channel, NotificationChannel)
        else str(channel).strip().upper()
    )
    payload = f"{t}|{u}|{st}|{si}|{ch}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_deep_link(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    destination_type: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Construct structured navigation metadata for future SaaS frontend routing.
    """
    e_type = (entity_type or "").upper()
    s_type = (source_type or "").upper()
    dest = destination_type or ""
    route = ""

    if not dest:
        if e_type == "BILL" or s_type == "BILL":
            dest = "BILL_DETAIL"
            route = f"/bills/{entity_id}" if entity_id else "/bills"
        elif e_type == "COMPANY" or s_type == "COMPANY":
            dest = "COMPANY_DETAIL"
            route = f"/companies/{entity_id}" if entity_id else "/companies"
        elif e_type == "STATE" or s_type == "STATE":
            dest = "STATE_EXPLORER"
            route = f"/states/{entity_id}" if entity_id else "/states"
        elif s_type in ("ALERT_GROUP", "GROUP"):
            dest = "ALERT_GROUP_DETAIL"
            route = f"/alerts/groups/{source_id}" if source_id else "/alerts/groups"
        elif s_type in ("DIGEST", "ALERT_DIGEST"):
            dest = "DIGEST_DETAIL"
            route = f"/digests/{source_id}" if source_id else "/digests"
        else:
            dest = "ALERT_DETAIL"
            route = f"/alerts/{source_id}" if source_id else "/alerts"

    return {
        "destination_type": dest,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "source_type": source_type,
        "source_id": source_id,
        "route": route,
        "params": metadata or {},
    }


# ---------------------------------------------------------------------------
# AlertRule
# ---------------------------------------------------------------------------


@dataclass
class AlertRule:
    """
    User subscription filter criteria for generating alerts.

    Attributes
    ----------
    alert_rule_id : str
        Unique rule identifier.
    user_id : str
        Owner user ID.
    tenant_id : str
        Tenant identifier.
    watchlist_id : Optional[str]
        Specific watchlist this rule applies to, or None for user-wide.
    alert_type : AlertType
        Type of event to watch.
    minimum_severity : AlertSeverity
        Minimum severity threshold to trigger alert.
    enabled : bool
        Rule active toggle.
    created_at : str
        UTC ISO timestamp.
    updated_at : str
        UTC ISO timestamp.
    """

    alert_rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    watchlist_id: Optional[str] = None
    alert_type: AlertType = AlertType.BILL_STATUS_CHANGE
    minimum_severity: AlertSeverity = AlertSeverity.LOW
    enabled: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Validate alert rule parameters deterministically."""
        if not self.alert_rule_id or not self.alert_rule_id.strip():
            raise ValueError("alert_rule_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not isinstance(self.alert_type, AlertType):
            try:
                self.alert_type = AlertType(str(self.alert_type).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid alert_type '{self.alert_type}'. Must be a valid AlertType")
        if not isinstance(self.minimum_severity, AlertSeverity):
            try:
                self.minimum_severity = AlertSeverity(str(self.minimum_severity).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid minimum_severity '{self.minimum_severity}'")

    def to_dict(self) -> dict[str, Any]:
        """Serialize AlertRule to dictionary."""
        return {
            "alert_rule_id": self.alert_rule_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "watchlist_id": self.watchlist_id,
            "alert_type": self.alert_type.value
            if isinstance(self.alert_type, AlertType)
            else str(self.alert_type),
            "minimum_severity": self.minimum_severity.value
            if isinstance(self.minimum_severity, AlertSeverity)
            else str(self.minimum_severity),
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertRule":
        """Deserialize AlertRule from dictionary."""
        raw_type = data.get("alert_type", AlertType.BILL_STATUS_CHANGE.value)
        if isinstance(raw_type, AlertType):
            atype = raw_type
        else:
            try:
                atype = AlertType(str(raw_type).strip().upper())
            except ValueError:
                atype = AlertType.BILL_STATUS_CHANGE

        raw_sev = data.get("minimum_severity", AlertSeverity.LOW.value)
        if isinstance(raw_sev, AlertSeverity):
            msev = raw_sev
        else:
            try:
                msev = AlertSeverity(str(raw_sev).strip().upper())
            except ValueError:
                msev = AlertSeverity.LOW

        obj = cls(
            alert_rule_id=data.get("alert_rule_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "default_user"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            watchlist_id=data.get("watchlist_id"),
            alert_type=atype,
            minimum_severity=msev,
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", _utcnow_iso()),
            updated_at=data.get("updated_at", _utcnow_iso()),
        )
        obj.validate()
        return obj


# ---------------------------------------------------------------------------
# AlertEvent
# ---------------------------------------------------------------------------


@dataclass
class AlertEvent:
    """
    User-relevant alert generated from an underlying monitoring or exposure change event.

    Attributes
    ----------
    alert_event_id : str
        Unique alert event ID.
    tenant_id : str
        Tenant identifier for multi-tenant isolation.
    user_id : str
        Owner user ID.
    watchlist_id : Optional[str]
        Associated watchlist ID if triggered by a watchlist.
    alert_rule_id : Optional[str]
        Matching alert rule ID if triggered by a rule.
    source_event_id : str
        ID of the underlying ChangeEvent/NotificationEvent for traceability.
    alert_type : AlertType
        Classification of alert.
    severity : AlertSeverity
        Assessed severity of the alert.
    title : str
        Concise headline for the alert.
    summary : str
        Detailed explanation / summary.
    entity_type : Optional[WatchlistEntityType]
        Primary entity type impacted.
    entity_id : Optional[str]
        Canonical entity identifier.
    created_at : str
        UTC ISO timestamp.
    is_read : bool
        Read status flag.
    read_at : Optional[str]
        Timestamp when user marked alert as read.
    is_archived : bool
        Archived status flag.
    archived_at : Optional[str]
        Timestamp when user archived the alert.
    dedup_key : str
        Deterministic deduplication hash.
    metadata : dict[str, Any]
        Arbitrary supplementary contextual metadata.
    """

    alert_event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    watchlist_id: Optional[str] = None
    alert_rule_id: Optional[str] = None
    source_event_id: str = ""
    alert_type: AlertType = AlertType.BILL_STATUS_CHANGE
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = ""
    summary: str = ""
    entity_type: Optional[WatchlistEntityType] = None
    entity_id: Optional[str] = None
    created_at: str = field(default_factory=_utcnow_iso)
    is_read: bool = False
    read_at: Optional[str] = None
    is_archived: bool = False
    archived_at: Optional[str] = None
    dedup_key: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.dedup_key:
            self.dedup_key = compute_dedup_key(
                user_id=self.user_id,
                watchlist_id=self.watchlist_id,
                source_event_id=self.source_event_id,
                alert_type=self.alert_type,
            )

    def validate(self) -> None:
        """Validate alert event integrity and ensure dedup key."""
        if not self.alert_event_id or not self.alert_event_id.strip():
            raise ValueError("alert_event_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("Alert title cannot be empty")
        if not isinstance(self.alert_type, AlertType):
            try:
                self.alert_type = AlertType(str(self.alert_type).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid alert_type '{self.alert_type}'")
        if not isinstance(self.severity, AlertSeverity):
            try:
                self.severity = AlertSeverity(str(self.severity).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid severity '{self.severity}'")
        if self.entity_type is not None and not isinstance(self.entity_type, WatchlistEntityType):
            try:
                self.entity_type = WatchlistEntityType(str(self.entity_type).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid entity_type '{self.entity_type}'")

        # Automatically compute dedup key if missing
        if not self.dedup_key:
            self.dedup_key = compute_dedup_key(
                user_id=self.user_id,
                watchlist_id=self.watchlist_id,
                source_event_id=self.source_event_id,
                alert_type=self.alert_type,
            )

    def mark_as_read(self) -> None:
        """Mark alert as read with current timestamp."""
        self.is_read = True
        self.read_at = _utcnow_iso()

    def mark_as_archived(self) -> None:
        """Archive alert with current timestamp."""
        self.is_archived = True
        self.archived_at = _utcnow_iso()

    def to_dict(self) -> dict[str, Any]:
        """Serialize AlertEvent to dictionary."""
        return {
            "alert_event_id": self.alert_event_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "watchlist_id": self.watchlist_id,
            "alert_rule_id": self.alert_rule_id,
            "source_event_id": self.source_event_id,
            "alert_type": self.alert_type.value
            if isinstance(self.alert_type, AlertType)
            else str(self.alert_type),
            "severity": self.severity.value
            if isinstance(self.severity, AlertSeverity)
            else str(self.severity),
            "title": self.title,
            "summary": self.summary,
            "entity_type": self.entity_type.value if self.entity_type else None,
            "entity_id": self.entity_id,
            "created_at": self.created_at,
            "is_read": self.is_read,
            "read_at": self.read_at,
            "is_archived": self.is_archived,
            "archived_at": self.archived_at,
            "dedup_key": self.dedup_key,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertEvent":
        """Deserialize AlertEvent from dictionary."""
        raw_type = data.get("alert_type", AlertType.BILL_STATUS_CHANGE.value)
        if isinstance(raw_type, AlertType):
            atype = raw_type
        else:
            try:
                atype = AlertType(str(raw_type).strip().upper())
            except ValueError:
                atype = AlertType.BILL_STATUS_CHANGE

        raw_sev = data.get("severity", AlertSeverity.MEDIUM.value)
        if isinstance(raw_sev, AlertSeverity):
            sev = raw_sev
        else:
            try:
                sev = AlertSeverity(str(raw_sev).strip().upper())
            except ValueError:
                sev = AlertSeverity.MEDIUM

        raw_etype = data.get("entity_type")
        if raw_etype:
            if isinstance(raw_etype, WatchlistEntityType):
                etype = raw_etype
            else:
                try:
                    etype = WatchlistEntityType(str(raw_etype).strip().upper())
                except ValueError:
                    etype = None
        else:
            etype = None

        obj = cls(
            alert_event_id=data.get("alert_event_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            watchlist_id=data.get("watchlist_id"),
            alert_rule_id=data.get("alert_rule_id"),
            source_event_id=data.get("source_event_id", ""),
            alert_type=atype,
            severity=sev,
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            entity_type=etype,
            entity_id=data.get("entity_id"),
            created_at=data.get("created_at", _utcnow_iso()),
            is_read=data.get("is_read", False),
            read_at=data.get("read_at"),
            is_archived=data.get("is_archived", False),
            archived_at=data.get("archived_at"),
            dedup_key=data.get("dedup_key", ""),
            metadata=data.get("metadata", {}),
        )
        obj.validate()
        return obj


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


@dataclass
class Notification:
    """
    Represents delivery, read state, and notification center record for an alert.

    Attributes
    ----------
    notification_id : str
        Unique notification delivery record ID.
    tenant_id : str
        Tenant identifier.
    user_id : str
        Target user ID.
    alert_event_id : str
        Foreign key referencing AlertEvent (or first event ID if from group/digest).
    channel : NotificationChannel
        Delivery channel (IN_APP, EMAIL, PUSH, WEBHOOK).
    status : NotificationStatus
        Delivery status (PENDING, DELIVERED, FAILED, READ, SUPPRESSED).
    created_at : str
        UTC ISO timestamp.
    delivered_at : Optional[str]
        Timestamp when delivery succeeded.
    read_at : Optional[str]
        Timestamp when recipient read notification.
    error_message : Optional[str]
        Failure reason if status is FAILED.
    title : str
        Human-readable title/headline.
    summary : str
        Concise summary/body text.
    notification_type : NotificationType
        Classification category (ALERT, DIGEST, LEGISLATIVE_UPDATE, etc.).
    severity : Optional[AlertSeverity]
        Severity tier if applicable.
    source_type : str
        Kind of source ('ALERT_EVENT', 'ALERT_GROUP', 'DIGEST', 'SYSTEM').
    source_id : str
        Source identifier.
    alert_group_id : Optional[str]
        Reference to AlertGroup if derived from a group.
    digest_id : Optional[str]
        Reference to AlertDigest if derived from a digest.
    entity_type : Optional[str]
        Impacted entity type (BILL, COMPANY, STATE, etc.).
    entity_id : Optional[str]
        Canonical entity identifier.
    state : Optional[str]
        State jurisdiction identifier if state-specific.
    jurisdiction : Optional[str]
        'central' or 'state'.
    is_read : bool
        Read status flag.
    is_archived : bool
        Archived flag for in-app center.
    archived_at : Optional[str]
        Timestamp when notification was archived.
    is_deleted : bool
        Soft delete flag.
    deleted_at : Optional[str]
        Timestamp when notification was deleted.
    deep_link : dict[str, Any]
        Structured navigation metadata for frontend.
    dedup_key : str
        Deterministic deduplication hash.
    metadata : dict[str, Any]
        Supplementary metadata (predictions, exposures, entity context).
    """

    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    alert_event_id: str = ""
    channel: NotificationChannel = NotificationChannel.IN_APP
    status: NotificationStatus = NotificationStatus.DELIVERED
    created_at: str = field(default_factory=_utcnow_iso)
    delivered_at: Optional[str] = field(default_factory=_utcnow_iso)
    read_at: Optional[str] = None
    error_message: Optional[str] = None
    title: str = ""
    summary: str = ""
    notification_type: NotificationType = NotificationType.ALERT
    severity: Optional[AlertSeverity] = None
    source_type: str = NotificationSourceType.ALERT_EVENT.value
    source_id: str = ""
    alert_group_id: Optional[str] = None
    digest_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    state: Optional[str] = None
    jurisdiction: Optional[str] = None
    is_read: bool = False
    is_archived: bool = False
    archived_at: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[str] = None
    deep_link: dict[str, Any] = field(default_factory=dict)
    dedup_key: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id:
            if self.alert_event_id:
                self.source_id = self.alert_event_id
            elif self.alert_group_id:
                self.source_id = self.alert_group_id
            elif self.digest_id:
                self.source_id = self.digest_id

        if not self.dedup_key and self.source_id:
            self.dedup_key = compute_notification_dedup_key(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                source_type=self.source_type,
                source_id=self.source_id,
                channel=self.channel,
            )

        if not self.deep_link and (self.entity_type or self.source_id):
            self.deep_link = build_deep_link(
                entity_type=self.entity_type,
                entity_id=self.entity_id,
                source_type=self.source_type,
                source_id=self.source_id,
                metadata=self.metadata,
            )

        if self.status == NotificationStatus.READ:
            self.is_read = True
        elif self.is_read and self.status == NotificationStatus.DELIVERED:
            self.status = NotificationStatus.READ

    def validate(self) -> None:
        """Validate notification invariants."""
        if not self.notification_id or not self.notification_id.strip():
            raise ValueError("notification_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if (
            not (self.alert_event_id and self.alert_event_id.strip())
            and not (self.source_id and self.source_id.strip())
            and not (self.alert_group_id and self.alert_group_id.strip())
            and not (self.digest_id and self.digest_id.strip())
        ):
            raise ValueError("alert_event_id or source_id cannot be empty")
        if not isinstance(self.channel, NotificationChannel):
            try:
                self.channel = NotificationChannel(str(self.channel).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid channel '{self.channel}'")
        if not isinstance(self.status, NotificationStatus):
            try:
                self.status = NotificationStatus(str(self.status).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid status '{self.status}'")
        if not isinstance(self.notification_type, NotificationType):
            try:
                self.notification_type = NotificationType(str(self.notification_type).strip().upper())
            except ValueError:
                self.notification_type = NotificationType.ALERT
        if self.severity is not None and not isinstance(self.severity, AlertSeverity):
            try:
                self.severity = AlertSeverity(str(self.severity).strip().upper())
            except ValueError:
                self.severity = None

    def mark_delivered(self) -> None:
        """Update status to DELIVERED."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = _utcnow_iso()

    def mark_read(self) -> None:
        """Update status to READ."""
        self.status = NotificationStatus.READ
        self.is_read = True
        self.read_at = _utcnow_iso()

    def mark_unread(self) -> None:
        """Revert status to DELIVERED and is_read to False."""
        self.status = NotificationStatus.DELIVERED
        self.is_read = False
        self.read_at = None

    def archive(self) -> None:
        """Mark notification as archived."""
        self.is_archived = True
        self.archived_at = _utcnow_iso()

    def unarchive(self) -> None:
        """Unarchive notification."""
        self.is_archived = False
        self.archived_at = None

    def soft_delete(self) -> None:
        """Mark notification as deleted without destroying source evidence."""
        self.is_deleted = True
        self.deleted_at = _utcnow_iso()

    def to_dict(self) -> dict[str, Any]:
        """Serialize Notification to dictionary."""
        return {
            "notification_id": self.notification_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "alert_event_id": self.alert_event_id,
            "channel": self.channel.value
            if isinstance(self.channel, NotificationChannel)
            else str(self.channel),
            "status": self.status.value
            if isinstance(self.status, NotificationStatus)
            else str(self.status),
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "read_at": self.read_at,
            "error_message": self.error_message,
            "title": self.title,
            "summary": self.summary,
            "notification_type": self.notification_type.value
            if isinstance(self.notification_type, NotificationType)
            else str(self.notification_type),
            "severity": self.severity.value
            if isinstance(self.severity, AlertSeverity)
            else (str(self.severity) if self.severity else None),
            "source_type": self.source_type,
            "source_id": self.source_id,
            "alert_group_id": self.alert_group_id,
            "digest_id": self.digest_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "state": self.state,
            "jurisdiction": self.jurisdiction,
            "is_read": self.is_read,
            "is_archived": self.is_archived,
            "archived_at": self.archived_at,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at,
            "deep_link": self.deep_link,
            "dedup_key": self.dedup_key,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Notification":
        """Deserialize Notification from dictionary."""
        raw_ch = data.get("channel", NotificationChannel.IN_APP.value)
        if isinstance(raw_ch, NotificationChannel):
            ch = raw_ch
        else:
            try:
                ch = NotificationChannel(str(raw_ch).strip().upper())
            except ValueError:
                ch = NotificationChannel.IN_APP

        raw_st = data.get("status", NotificationStatus.DELIVERED.value)
        if isinstance(raw_st, NotificationStatus):
            st = raw_st
        else:
            try:
                st = NotificationStatus(str(raw_st).strip().upper())
            except ValueError:
                st = NotificationStatus.DELIVERED

        raw_nt = data.get("notification_type", NotificationType.ALERT.value)
        if isinstance(raw_nt, NotificationType):
            nt = raw_nt
        else:
            try:
                nt = NotificationType(str(raw_nt).strip().upper())
            except ValueError:
                nt = NotificationType.ALERT

        raw_sev = data.get("severity")
        if raw_sev:
            if isinstance(raw_sev, AlertSeverity):
                sev = raw_sev
            else:
                try:
                    sev = AlertSeverity(str(raw_sev).strip().upper())
                except ValueError:
                    sev = None
        else:
            sev = None

        obj = cls(
            notification_id=data.get("notification_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            alert_event_id=data.get("alert_event_id", ""),
            channel=ch,
            status=st,
            created_at=data.get("created_at", _utcnow_iso()),
            delivered_at=data.get("delivered_at"),
            read_at=data.get("read_at"),
            error_message=data.get("error_message"),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            notification_type=nt,
            severity=sev,
            source_type=data.get("source_type", NotificationSourceType.ALERT_EVENT.value),
            source_id=data.get("source_id", ""),
            alert_group_id=data.get("alert_group_id"),
            digest_id=data.get("digest_id"),
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            state=data.get("state"),
            jurisdiction=data.get("jurisdiction"),
            is_read=data.get("is_read", (st == NotificationStatus.READ)),
            is_archived=data.get("is_archived", False),
            archived_at=data.get("archived_at"),
            is_deleted=data.get("is_deleted", False),
            deleted_at=data.get("deleted_at"),
            deep_link=data.get("deep_link", {}),
            dedup_key=data.get("dedup_key", ""),
            metadata=data.get("metadata", {}),
        )
        obj.validate()
        return obj


# ---------------------------------------------------------------------------
# AlertPreference
# ---------------------------------------------------------------------------


@dataclass
class AlertPreference:
    """
    User configuration for alert filtering and delivery cadence.

    Attributes
    ----------
    preference_id : str
        Unique preference ID.
    user_id : str
        Owner user ID.
    tenant_id : str
        Tenant identifier.
    enabled : bool
        Global master alert toggle for this user.
    minimum_severity : AlertSeverity
        Global minimum severity filter.
    allowed_alert_types : list[AlertType]
        List of permitted alert types.
    allowed_channels : list[NotificationChannel]
        List of permitted notification channels.
    digest_frequency : DigestFrequency
        Frequency of delivery (REAL_TIME, DAILY_DIGEST, WEEKLY_DIGEST).
    created_at : str
        UTC ISO timestamp.
    updated_at : str
        UTC ISO timestamp.
    """

    preference_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    enabled: bool = True
    minimum_severity: AlertSeverity = AlertSeverity.LOW
    allowed_alert_types: list[AlertType] = field(default_factory=lambda: list(AlertType))
    allowed_channels: list[NotificationChannel] = field(
        default_factory=lambda: [NotificationChannel.IN_APP]
    )
    digest_frequency: DigestFrequency = DigestFrequency.REAL_TIME
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Validate alert preference parameters."""
        if not self.preference_id or not self.preference_id.strip():
            raise ValueError("preference_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not isinstance(self.minimum_severity, AlertSeverity):
            try:
                self.minimum_severity = AlertSeverity(str(self.minimum_severity).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid minimum_severity '{self.minimum_severity}'")
        if not isinstance(self.digest_frequency, DigestFrequency):
            try:
                self.digest_frequency = DigestFrequency(str(self.digest_frequency).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid digest_frequency '{self.digest_frequency}'")

    def to_dict(self) -> dict[str, Any]:
        """Serialize AlertPreference to dictionary."""
        return {
            "preference_id": self.preference_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "enabled": self.enabled,
            "minimum_severity": self.minimum_severity.value
            if isinstance(self.minimum_severity, AlertSeverity)
            else str(self.minimum_severity),
            "allowed_alert_types": [
                t.value if isinstance(t, AlertType) else str(t) for t in self.allowed_alert_types
            ],
            "allowed_channels": [
                c.value if isinstance(c, NotificationChannel) else str(c) for c in self.allowed_channels
            ],
            "digest_frequency": self.digest_frequency.value
            if isinstance(self.digest_frequency, DigestFrequency)
            else str(self.digest_frequency),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertPreference":
        """Deserialize AlertPreference from dictionary."""
        raw_sev = data.get("minimum_severity", AlertSeverity.LOW.value)
        if isinstance(raw_sev, AlertSeverity):
            msev = raw_sev
        else:
            try:
                msev = AlertSeverity(str(raw_sev).strip().upper())
            except ValueError:
                msev = AlertSeverity.LOW

        raw_types = data.get("allowed_alert_types", [])
        types: list[AlertType] = []
        for t in raw_types:
            if isinstance(t, AlertType):
                types.append(t)
            else:
                try:
                    types.append(AlertType(str(t).strip().upper()))
                except ValueError:
                    pass
        if not types:
            types = list(AlertType)

        raw_chans = data.get("allowed_channels", [NotificationChannel.IN_APP.value])
        chans: list[NotificationChannel] = []
        for c in raw_chans:
            if isinstance(c, NotificationChannel):
                chans.append(c)
            else:
                try:
                    chans.append(NotificationChannel(str(c).strip().upper()))
                except ValueError:
                    pass
        if not chans:
            chans = [NotificationChannel.IN_APP]

        raw_freq = data.get("digest_frequency", DigestFrequency.REAL_TIME.value)
        if isinstance(raw_freq, DigestFrequency):
            freq = raw_freq
        else:
            try:
                freq = DigestFrequency(str(raw_freq).strip().upper())
            except ValueError:
                freq = DigestFrequency.REAL_TIME

        obj = cls(
            preference_id=data.get("preference_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "default_user"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            enabled=data.get("enabled", True),
            minimum_severity=msev,
            allowed_alert_types=types,
            allowed_channels=chans,
            digest_frequency=freq,
            created_at=data.get("created_at", _utcnow_iso()),
            updated_at=data.get("updated_at", _utcnow_iso()),
        )
        obj.validate()
        return obj
