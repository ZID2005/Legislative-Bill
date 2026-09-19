"""
schemas/alert_digest.py
=======================
Structured Digest schema for scheduled or real-time alert rollups.

Represents a presentation-ready collection of AlertGroups and AlertEvents
structured for notification centers, daily summaries, or weekly digests.

Task 8.13.5 — Alert Aggregation & Digest Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid

from schemas.alert import DigestFrequency


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DigestType(str, Enum):
    """Temporal delivery cadence of a digest."""

    REAL_TIME = "REAL_TIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


# ---------------------------------------------------------------------------
# AlertDigest Dataclass
# ---------------------------------------------------------------------------


@dataclass
class AlertDigest:
    """
    Structured, presentation-ready digest consolidating AlertGroups and events.

    Attributes
    ----------
    digest_id : str
        Unique identifier for the generated digest.
    tenant_id : str
        Tenant identifier for multi-tenant isolation.
    user_id : str
        Recipient user ID.
    digest_type : DigestType
        Cadence type (REAL_TIME, DAILY, WEEKLY).
    frequency : DigestFrequency
        Matching user preference frequency.
    period_start : str
        Start timestamp of the digest window (ISO UTC).
    period_end : str
        End timestamp of the digest window (ISO UTC).
    group_ids : list[str]
        Ordered list of AlertGroup IDs included in this digest.
    event_ids : list[str]
        Ordered, deduplicated list of all underlying AlertEvent IDs.
    group_count : int
        Count of aggregated groups.
    event_count : int
        Count of total underlying events represented.
    affected_companies : list[str]
        Unique list of company IDs/ISINs impacted.
    affected_bills : list[str]
        Unique list of bill IDs impacted.
    affected_sectors : list[str]
        Unique list of sectors impacted.
    affected_states : list[str]
        Unique list of States impacted.
    jurisdictions : list[str]
        List of jurisdictions present ('central', 'state').
    groups : list[dict[str, Any]]
        Serialized group summaries ready for frontend or notification channels.
    generated_at : str
        UTC ISO timestamp of digest construction.
    metadata : dict[str, Any]
        Supplementary digest metadata.
    """

    digest_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    digest_type: DigestType = DigestType.DAILY
    frequency: DigestFrequency = DigestFrequency.DAILY_DIGEST
    period_start: str = ""
    period_end: str = ""
    group_ids: list[str] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)
    group_count: int = 0
    event_count: int = 0
    affected_companies: list[str] = field(default_factory=list)
    affected_bills: list[str] = field(default_factory=list)
    affected_sectors: list[str] = field(default_factory=list)
    affected_states: list[str] = field(default_factory=list)
    jurisdictions: list[str] = field(default_factory=list)
    groups: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = field(default_factory=_utcnow_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.group_count:
            self.group_count = len(self.group_ids)
        if not self.event_count:
            self.event_count = len(self.event_ids)

    def validate(self) -> None:
        """Validate digest invariants."""
        if not self.digest_id or not self.digest_id.strip():
            raise ValueError("digest_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not isinstance(self.digest_type, DigestType):
            try:
                self.digest_type = DigestType(str(self.digest_type).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid digest_type '{self.digest_type}'")
        if not isinstance(self.frequency, DigestFrequency):
            try:
                self.frequency = DigestFrequency(str(self.frequency).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid frequency '{self.frequency}'")

    def to_dict(self) -> dict[str, Any]:
        """Serialize AlertDigest to dictionary."""
        return {
            "digest_id": self.digest_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "digest_type": self.digest_type.value
            if isinstance(self.digest_type, DigestType)
            else str(self.digest_type),
            "frequency": self.frequency.value
            if isinstance(self.frequency, DigestFrequency)
            else str(self.frequency),
            "period_start": self.period_start,
            "period_end": self.period_end,
            "group_ids": list(self.group_ids),
            "event_ids": list(self.event_ids),
            "group_count": self.group_count,
            "event_count": self.event_count,
            "affected_companies": list(self.affected_companies),
            "affected_bills": list(self.affected_bills),
            "affected_sectors": list(self.affected_sectors),
            "affected_states": list(self.affected_states),
            "jurisdictions": list(self.jurisdictions),
            "groups": list(self.groups),
            "generated_at": self.generated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertDigest":
        """Deserialize AlertDigest from dictionary."""
        raw_dtype = data.get("digest_type", DigestType.DAILY.value)
        if isinstance(raw_dtype, DigestType):
            dtype = raw_dtype
        else:
            try:
                dtype = DigestType(str(raw_dtype).strip().upper())
            except ValueError:
                dtype = DigestType.DAILY

        raw_freq = data.get("frequency", DigestFrequency.DAILY_DIGEST.value)
        if isinstance(raw_freq, DigestFrequency):
            freq = raw_freq
        else:
            try:
                freq = DigestFrequency(str(raw_freq).strip().upper())
            except ValueError:
                freq = DigestFrequency.DAILY_DIGEST

        g_ids = list(data.get("group_ids", []))
        e_ids = list(data.get("event_ids", []))

        obj = cls(
            digest_id=data.get("digest_id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            digest_type=dtype,
            frequency=freq,
            period_start=data.get("period_start", ""),
            period_end=data.get("period_end", ""),
            group_ids=g_ids,
            event_ids=e_ids,
            group_count=data.get("group_count", len(g_ids)),
            event_count=data.get("event_count", len(e_ids)),
            affected_companies=list(data.get("affected_companies", [])),
            affected_bills=list(data.get("affected_bills", [])),
            affected_sectors=list(data.get("affected_sectors", [])),
            affected_states=list(data.get("affected_states", [])),
            jurisdictions=list(data.get("jurisdictions", [])),
            groups=list(data.get("groups", [])),
            generated_at=data.get("generated_at", _utcnow_iso()),
            metadata=data.get("metadata", {}),
        )
        obj.validate()
        return obj
