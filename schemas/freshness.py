"""
schemas/freshness.py
====================
Typed data contracts for data freshness and stale data detection (Tasks 8.17.10 & 8.17.11).

Strictly supports only honest, backend-supported freshness states:
- LIVE          : Actively updated by live monitoring or scheduled pipelines.
- RECENT        : Up to date within operational freshness thresholds.
- STALE         : Exceeds operational freshness threshold; requires refresh.
- NOT_AVAILABLE : Data point or timestamp unrecorded / not supported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class FreshnessStatus(str, Enum):
    """Authoritative freshness status classification."""

    LIVE = "LIVE"
    RECENT = "RECENT"
    STALE = "STALE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


@dataclass
class DatasetFreshnessRecord:
    """Freshness metadata for a specific dataset or subsystem."""

    dataset_name: str
    status: FreshnessStatus
    last_updated: Optional[str] = None
    last_verified: Optional[str] = None
    source_checked: Optional[str] = None
    data_age_hours: Optional[float] = None
    threshold_hours: Optional[float] = None
    is_live_pipeline: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "status": self.status.value,
            "last_updated": self.last_updated,
            "last_verified": self.last_verified,
            "source_checked": self.source_checked,
            "data_age_hours": round(self.data_age_hours, 1) if self.data_age_hours is not None else None,
            "threshold_hours": self.threshold_hours,
            "is_live_pipeline": self.is_live_pipeline,
            "notes": self.notes,
        }


@dataclass
class SystemFreshnessOverview:
    """Consolidated platform data freshness diagnostic."""

    timestamp: str
    overall_status: FreshnessStatus
    datasets: list[DatasetFreshnessRecord] = field(default_factory=list)
    stale_count: int = 0
    live_count: int = 0
    recent_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "stale_count": self.stale_count,
            "live_count": self.live_count,
            "recent_count": self.recent_count,
            "datasets": [d.to_dict() for d in self.datasets],
        }
