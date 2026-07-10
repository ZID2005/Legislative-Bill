"""
schemas/mapping_record.py
==========================
Typed data model for a Bill-to-Company mapping record.

Represents the mapping of a legislative bill to potentially affected listed companies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BillCompanyMapping:
    """
    Canonical representation of the mapping of a bill to candidate companies.
    """

    bill_id: str
    bill_title: str
    ministry: str
    policy_domain: str
    economic_domain: str
    primary_sector: str
    secondary_sectors: list[str] = field(default_factory=list)
    candidate_companies: list[dict] = field(default_factory=list)
    mapping_confidence: float = 0.0
    mapping_reason: str = ""

    def to_dict(self) -> dict:
        """Serialise the mapping record to a JSON-compatible dictionary."""
        return {
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "ministry": self.ministry,
            "policy_domain": self.policy_domain,
            "economic_domain": self.economic_domain,
            "primary_sector": self.primary_sector,
            "secondary_sectors": self.secondary_sectors,
            "candidate_companies": self.candidate_companies,
            "mapping_confidence": self.mapping_confidence,
            "mapping_reason": self.mapping_reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BillCompanyMapping:
        """Deserialise a mapping record from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            bill_title=data.get("bill_title") or data.get("title") or "",
            ministry=data["ministry"],
            policy_domain=data["policy_domain"],
            economic_domain=data["economic_domain"],
            primary_sector=data["primary_sector"],
            secondary_sectors=data.get("secondary_sectors", []),
            candidate_companies=data.get("candidate_companies", []),
            mapping_confidence=data.get("mapping_confidence", 0.0),
            mapping_reason=data.get("mapping_reason", ""),
        )

    def __repr__(self) -> str:
        return (
            f"<BillCompanyMapping bill_id={self.bill_id!r} "
            f"primary_sector={self.primary_sector!r} "
            f"candidate_count={len(self.candidate_companies)} "
            f"confidence={self.mapping_confidence:.2f}>"
        )
