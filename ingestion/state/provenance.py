"""
ingestion/state/provenance.py
=============================
Provenance and data quality tracking for Indian State legislative bills.

Distinguishes:
- AUTHORITATIVE: Extracted verbatim or directly from official legislative records.
- DERIVED: Safely derived by deterministic rules (e.g. slugifying, state normalization).
- UNAVAILABLE: Not present in the source; strictly preserved as None or empty without fabrication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ProvenanceLevel(str, Enum):
    """Classification of data provenance and authority."""

    AUTHORITATIVE = "authoritative"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"


@dataclass
class FieldProvenance:
    """Provenance record for an individual bill metadata field."""

    field_name: str
    level: ProvenanceLevel
    value: Any
    source_detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "level": self.level.value,
            "value": str(self.value) if self.value is not None else None,
            "source_detail": self.source_detail,
        }


@dataclass
class BillProvenanceRecord:
    """Provenance audit record for a single State legislative bill."""

    bill_id: str
    state: str
    legislature: str
    source_url: str
    fields: dict[str, FieldProvenance] = field(default_factory=dict)

    def add_field(
        self,
        field_name: str,
        level: ProvenanceLevel,
        value: Any,
        source_detail: str,
    ) -> None:
        self.fields[field_name] = FieldProvenance(
            field_name=field_name,
            level=level,
            value=value,
            source_detail=source_detail,
        )

    def get_coverage_summary(self) -> dict[str, int]:
        counts = {
            ProvenanceLevel.AUTHORITATIVE.value: 0,
            ProvenanceLevel.DERIVED.value: 0,
            ProvenanceLevel.UNAVAILABLE.value: 0,
        }
        for fp in self.fields.values():
            counts[fp.level.value] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "state": self.state,
            "legislature": self.legislature,
            "source_url": self.source_url,
            "coverage": self.get_coverage_summary(),
            "fields": {k: v.to_dict() for k, v in self.fields.items()},
        }


class StateProvenanceTracker:
    """Tracks and generates provenance reports across a State bill ingestion batch."""

    def __init__(self) -> None:
        self._records: dict[str, BillProvenanceRecord] = {}

    def record_bill(self, record: BillProvenanceRecord) -> None:
        self._records[record.bill_id] = record

    def get_record(self, bill_id: str) -> Optional[BillProvenanceRecord]:
        return self._records.get(bill_id)

    def generate_report(self) -> dict[str, Any]:
        """Generate a complete provenance audit report for all ingested State bills."""
        total_bills = len(self._records)
        authoritative_counts: dict[str, int] = {}
        derived_counts: dict[str, int] = {}
        unavailable_counts: dict[str, int] = {}

        for rec in self._records.values():
            for name, fp in rec.fields.items():
                if fp.level == ProvenanceLevel.AUTHORITATIVE:
                    authoritative_counts[name] = authoritative_counts.get(name, 0) + 1
                elif fp.level == ProvenanceLevel.DERIVED:
                    derived_counts[name] = derived_counts.get(name, 0) + 1
                elif fp.level == ProvenanceLevel.UNAVAILABLE:
                    unavailable_counts[name] = unavailable_counts.get(name, 0) + 1

        return {
            "total_state_bills": total_bills,
            "field_summary": {
                "authoritative": authoritative_counts,
                "derived": derived_counts,
                "unavailable": unavailable_counts,
            },
            "records": [rec.to_dict() for rec in self._records.values()],
        }
