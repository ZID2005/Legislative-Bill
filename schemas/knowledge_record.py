"""
schemas/knowledge_record.py
===========================
Typed data model for a Legislative Bill Knowledge Record.

Represents the structured domain knowledge extracted and assigned for a bill.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KnowledgeRecord:
    """
    Canonical representation of structured domain knowledge for a legislative bill.
    """

    bill_id: str
    ministry: str
    department: str
    policy_domain: str
    economic_domain: str
    primary_sector: str
    secondary_sectors: list[str] = field(default_factory=list)
    stakeholder_groups: list[str] = field(default_factory=list)
    regulatory_authority: str = ""
    geographic_scope: str = "National"
    bill_type: str = "Ordinary Bill"
    keywords: list[str] = field(default_factory=list)
    related_acts: list[str] = field(default_factory=list)
    related_ministries: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    searchable_tags: list[str] = field(default_factory=list)
    generated_at: str = ""
    rules_version: str = "1.0"
    source_metadata_checksum: Optional[str] = None
    source_text_checksum: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialise the KnowledgeRecord to a JSON-compatible dictionary."""
        return {
            "bill_id": self.bill_id,
            "ministry": self.ministry,
            "department": self.department,
            "policy_domain": self.policy_domain,
            "economic_domain": self.economic_domain,
            "primary_sector": self.primary_sector,
            "secondary_sectors": self.secondary_sectors,
            "stakeholder_groups": self.stakeholder_groups,
            "regulatory_authority": self.regulatory_authority,
            "geographic_scope": self.geographic_scope,
            "bill_type": self.bill_type,
            "keywords": self.keywords,
            "related_acts": self.related_acts,
            "related_ministries": self.related_ministries,
            "confidence_score": self.confidence_score,
            "searchable_tags": self.searchable_tags,
            "generated_at": self.generated_at,
            "rules_version": self.rules_version,
            "source_metadata_checksum": self.source_metadata_checksum,
            "source_text_checksum": self.source_text_checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeRecord":
        """Deserialise a KnowledgeRecord from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            ministry=data["ministry"],
            department=data["department"],
            policy_domain=data["policy_domain"],
            economic_domain=data["economic_domain"],
            primary_sector=data["primary_sector"],
            secondary_sectors=data.get("secondary_sectors", []),
            stakeholder_groups=data.get("stakeholder_groups", []),
            regulatory_authority=data.get("regulatory_authority", ""),
            geographic_scope=data.get("geographic_scope", "National"),
            bill_type=data.get("bill_type", "Ordinary Bill"),
            keywords=data.get("keywords", []),
            related_acts=data.get("related_acts", []),
            related_ministries=data.get("related_ministries", []),
            confidence_score=data.get("confidence_score", 0.0),
            searchable_tags=data.get("searchable_tags", []),
            generated_at=data.get("generated_at", ""),
            rules_version=data.get("rules_version", "1.0"),
            source_metadata_checksum=data.get("source_metadata_checksum"),
            source_text_checksum=data.get("source_text_checksum"),
        )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeRecord bill_id={self.bill_id!r} primary_sector={self.primary_sector!r} "
            f"confidence_score={self.confidence_score:.2f}>"
        )
