"""
schemas/notification_delivery.py
=================================
Data models, results, and tracking records for outbound notification delivery.

Defines:
- NotificationErrorCode: Standardised taxonomy of provider failure modes.
- DeliveryResult: Structured outcome of a delivery attempt across any channel.
- NotificationDeliveryRecord: Persistent delivery attempt record for auditability and idempotency.
- compute_delivery_key: Deterministic delivery identity helper.

Task 8.13.7 — Outbound Notification Delivery Providers & Webhook Dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any, Optional
import uuid

from schemas.alert import NotificationChannel, NotificationStatus


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Error Codes Taxonomy
# ---------------------------------------------------------------------------


class NotificationErrorCode(str, Enum):
    """Standardised error codes for notification delivery failures."""

    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    HTTP_FAILURE = "HTTP_FAILURE"
    INVALID_DESTINATION = "INVALID_DESTINATION"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    CHANNEL_NOT_ALLOWED = "CHANNEL_NOT_ALLOWED"
    PREFERENCE_SUPPRESSED = "PREFERENCE_SUPPRESSED"


# ---------------------------------------------------------------------------
# Idempotency Helper
# ---------------------------------------------------------------------------


def compute_delivery_key(
    tenant_id: str,
    user_id: str,
    notification_id: str,
    channel: str | NotificationChannel,
) -> str:
    """
    Compute a deterministic delivery key for idempotency tracking:
    delivery_key = SHA-256(tenant_id || user_id || notification_id || channel)
    """
    t = (tenant_id or "").strip()
    u = (user_id or "").strip()
    n = (notification_id or "").strip()
    c = (
        channel.value
        if isinstance(channel, NotificationChannel)
        else str(channel).strip().upper()
    )
    payload = f"{t}|{u}|{n}|{c}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# DeliveryResult
# ---------------------------------------------------------------------------


@dataclass
class DeliveryResult:
    """
    Structured outcome of an outbound notification delivery operation.

    Attributes
    ----------
    success : bool
        True if delivery was accepted/completed by provider; False otherwise.
    status : NotificationStatus
        DELIVERED, FAILED, or SUPPRESSED.
    channel : NotificationChannel
        Channel attempted (IN_APP, EMAIL, PUSH, WEBHOOK).
    provider : str
        Name/identifier of the provider that handled the request.
    response_code : Optional[int]
        HTTP or protocol response code if applicable.
    error_code : Optional[str]
        Categorised error code (from NotificationErrorCode or string).
    error_message : Optional[str]
        Sanitised, human-readable error explanation (never containing secrets).
    attempted_at : str
        UTC ISO timestamp when dispatch was initiated.
    completed_at : Optional[str]
        UTC ISO timestamp when dispatch completed or failed.
    retry_count : int
        Number of retry attempts executed before final outcome.
    metadata : dict[str, Any]
        Supplementary delivery metadata (redacted of credentials/secrets).
    """

    success: bool
    status: NotificationStatus
    channel: NotificationChannel
    provider: str
    response_code: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    attempted_at: str = field(default_factory=_utcnow_iso)
    completed_at: Optional[str] = field(default_factory=_utcnow_iso)
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize DeliveryResult to dictionary."""
        return {
            "success": self.success,
            "status": (
                self.status.value
                if isinstance(self.status, NotificationStatus)
                else str(self.status)
            ),
            "channel": (
                self.channel.value
                if isinstance(self.channel, NotificationChannel)
                else str(self.channel)
            ),
            "provider": self.provider,
            "response_code": self.response_code,
            "error_code": (
                self.error_code.value
                if isinstance(self.error_code, NotificationErrorCode)
                else (str(self.error_code) if self.error_code else None)
            ),
            "error_message": self.error_message,
            "attempted_at": self.attempted_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeliveryResult:
        """Deserialize DeliveryResult from dictionary."""
        raw_st = data.get("status", NotificationStatus.DELIVERED.value)
        if isinstance(raw_st, NotificationStatus):
            st = raw_st
        else:
            try:
                st = NotificationStatus(str(raw_st).strip().upper())
            except ValueError:
                st = NotificationStatus.DELIVERED

        raw_ch = data.get("channel", NotificationChannel.IN_APP.value)
        if isinstance(raw_ch, NotificationChannel):
            ch = raw_ch
        else:
            try:
                ch = NotificationChannel(str(raw_ch).strip().upper())
            except ValueError:
                ch = NotificationChannel.IN_APP

        return cls(
            success=bool(data.get("success", False)),
            status=st,
            channel=ch,
            provider=str(data.get("provider", "unknown")),
            response_code=data.get("response_code"),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            attempted_at=data.get("attempted_at", _utcnow_iso()),
            completed_at=data.get("completed_at"),
            retry_count=int(data.get("retry_count", 0)),
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# NotificationDeliveryRecord
# ---------------------------------------------------------------------------


@dataclass
class NotificationDeliveryRecord:
    """
    Persistent record of a notification delivery attempt for auditing,
    idempotency, and provider diagnostics.

    Attributes
    ----------
    delivery_id : str
        Unique identifier for this delivery attempt.
    notification_id : str
        Referenced notification identifier.
    tenant_id : str
        Tenant identifier for multi-tenant scoping.
    user_id : str
        Recipient user identifier.
    channel : NotificationChannel
        Delivery channel (IN_APP, EMAIL, PUSH, WEBHOOK).
    attempt_number : int
        Sequence attempt counter (1-indexed).
    status : NotificationStatus
        DELIVERED, FAILED, or SUPPRESSED.
    timestamp : str
        UTC ISO timestamp of delivery attempt.
    provider : str
        Name of the provider executing the attempt.
    delivery_key : str
        Deterministic deduplication/idempotency key.
    response_code : Optional[int]
        HTTP or protocol response code.
    error_code : Optional[str]
        Failure error code.
    error_message : Optional[str]
        Sanitised error message (never containing secrets).
    response_metadata : dict[str, Any]
        Provider response payload / metadata.
    """

    delivery_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notification_id: str = ""
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    channel: NotificationChannel = NotificationChannel.IN_APP
    attempt_number: int = 1
    status: NotificationStatus = NotificationStatus.DELIVERED
    timestamp: str = field(default_factory=_utcnow_iso)
    provider: str = ""
    delivery_key: str = ""
    response_code: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    response_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.delivery_key and self.notification_id:
            self.delivery_key = compute_delivery_key(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                notification_id=self.notification_id,
                channel=self.channel,
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NotificationDeliveryRecord to dictionary."""
        return {
            "delivery_id": self.delivery_id,
            "notification_id": self.notification_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "channel": (
                self.channel.value
                if isinstance(self.channel, NotificationChannel)
                else str(self.channel)
            ),
            "attempt_number": self.attempt_number,
            "status": (
                self.status.value
                if isinstance(self.status, NotificationStatus)
                else str(self.status)
            ),
            "timestamp": self.timestamp,
            "provider": self.provider,
            "delivery_key": self.delivery_key,
            "response_code": self.response_code,
            "error_code": (
                self.error_code.value
                if isinstance(self.error_code, NotificationErrorCode)
                else (str(self.error_code) if self.error_code else None)
            ),
            "error_message": self.error_message,
            "response_metadata": dict(self.response_metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationDeliveryRecord:
        """Deserialize NotificationDeliveryRecord from dictionary."""
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

        return cls(
            delivery_id=data.get("delivery_id", str(uuid.uuid4())),
            notification_id=data.get("notification_id", ""),
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            channel=ch,
            attempt_number=int(data.get("attempt_number", 1)),
            status=st,
            timestamp=data.get("timestamp", _utcnow_iso()),
            provider=str(data.get("provider", "")),
            delivery_key=data.get("delivery_key", ""),
            response_code=data.get("response_code"),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            response_metadata=data.get("response_metadata", {}),
        )
