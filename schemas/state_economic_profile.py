"""
schemas/state_economic_profile.py
=================================
Typed data model for an Indian State Legislative Bill Economic Impact Profile.

Encapsulates structured sector intelligence, grounded stakeholder impacts,
statutory evidence linking, direct/indirect impact classifications,
geographic relevance, and company exposure readiness.

Strictly bounded to factual legislative analysis and qualitative interpretation;
zero stock market predictions, price targets, or financial returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class EvidenceReference:
    """
    Traceable textual evidence supporting a sector or stakeholder classification.
    Grounded strictly in official bill text, provisions, or corpus location.
    """
    source_type: str = "bill_text"  # "bill_text" | "corpus" | "provision" | "metadata"
    section: Optional[str] = None
    text_reference: str = ""
    location: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "section": self.section,
            "text_reference": self.text_reference,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceReference":
        return cls(
            source_type=data.get("source_type", "bill_text"),
            section=data.get("section"),
            text_reference=data.get("text_reference", ""),
            location=data.get("location"),
        )


@dataclass
class StakeholderImpact:
    """
    Structured impact profile for a single stakeholder group.
    """
    stakeholder: str
    category: str = "people"  # "people" | "businesses" | "institutions" | "economic_groups" | "other"
    role: str = "affected"  # e.g. "primary_affected", "potential_beneficiary", "potential_cost_bearer"
    direction: str = "unknown"  # "positive" | "negative" | "mixed" | "neutral" | "unknown"
    mechanism: str = "regulation"  # e.g. "compliance", "taxation", "labour_requirement"
    impact_type: str = "DIRECT"  # "DIRECT" | "INDIRECT" | "UNKNOWN"
    evidence: EvidenceReference = field(default_factory=EvidenceReference)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "stakeholder": self.stakeholder,
            "category": self.category,
            "role": self.role,
            "direction": self.direction,
            "mechanism": self.mechanism,
            "impact_type": self.impact_type,
            "evidence": self.evidence.to_dict() if isinstance(self.evidence, EvidenceReference) else self.evidence,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StakeholderImpact":
        ev_data = data.get("evidence", {})
        evidence = EvidenceReference.from_dict(ev_data) if isinstance(ev_data, dict) else EvidenceReference()
        return cls(
            stakeholder=data.get("stakeholder", ""),
            category=data.get("category", "people"),
            role=data.get("role", "affected"),
            direction=data.get("direction", "unknown"),
            mechanism=data.get("mechanism", "regulation"),
            impact_type=data.get("impact_type", "DIRECT"),
            evidence=evidence,
            description=data.get("description", ""),
        )


@dataclass
class FactualStakeholderSummary:
    """
    Human-readable factual summary formatted for stakeholders.
    Employs cautious statutory framing ('the bill requires', 'may affect', 'could affect').
    """
    who_may_be_affected: list[str] = field(default_factory=list)
    how_affected: list[str] = field(default_factory=list)
    who_may_benefit: list[str] = field(default_factory=list)
    who_may_bear_costs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "who_may_be_affected": self.who_may_be_affected,
            "how_affected": self.how_affected,
            "who_may_benefit": self.who_may_benefit,
            "who_may_bear_costs": self.who_may_bear_costs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FactualStakeholderSummary":
        return cls(
            who_may_be_affected=data.get("who_may_be_affected", []),
            how_affected=data.get("how_affected", []),
            who_may_benefit=data.get("who_may_benefit", []),
            who_may_bear_costs=data.get("who_may_bear_costs", []),
        )


@dataclass
class StateBillEconomicProfile:
    """
    Canonical representation of structured economic and stakeholder intelligence
    for an Indian State legislative bill.
    """
    bill_id: str
    state: str
    policy_domain: str
    primary_sector: Optional[str] = None
    secondary_sectors: list[str] = field(default_factory=list)
    sub_sectors: list[str] = field(default_factory=list)
    economic_activities: list[str] = field(default_factory=list)
    business_types: list[str] = field(default_factory=list)
    stakeholders: list[StakeholderImpact] = field(default_factory=list)
    geographic_scope: str = "state-wide"
    direct_impacts: list[str] = field(default_factory=list)
    indirect_impacts: list[str] = field(default_factory=list)
    impact_mechanisms: list[str] = field(default_factory=list)
    company_exposure_readiness: str = "UNKNOWN"  # "HIGH" | "MEDIUM" | "LOW" | "NONE" | "UNKNOWN"
    evidence: list[EvidenceReference] = field(default_factory=list)
    confidence: str = "HIGH"  # "HIGH" | "MEDIUM" | "LOW"
    factual_summary: FactualStakeholderSummary = field(default_factory=FactualStakeholderSummary)
    provenance: dict[str, str] = field(default_factory=dict)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize StateBillEconomicProfile to a JSON-compatible dictionary."""
        return {
            "bill_id": self.bill_id,
            "state": self.state,
            "policy_domain": self.policy_domain,
            "primary_sector": self.primary_sector,
            "secondary_sectors": self.secondary_sectors,
            "sub_sectors": self.sub_sectors,
            "economic_activities": self.economic_activities,
            "business_types": self.business_types,
            "stakeholders": [
                s.to_dict() if isinstance(s, StakeholderImpact) else s
                for s in self.stakeholders
            ],
            "geographic_scope": self.geographic_scope,
            "direct_impacts": self.direct_impacts,
            "indirect_impacts": self.indirect_impacts,
            "impact_mechanisms": self.impact_mechanisms,
            "company_exposure_readiness": self.company_exposure_readiness,
            "evidence": [
                e.to_dict() if isinstance(e, EvidenceReference) else e
                for e in self.evidence
            ],
            "confidence": self.confidence,
            "factual_summary": (
                self.factual_summary.to_dict()
                if isinstance(self.factual_summary, FactualStakeholderSummary)
                else self.factual_summary
            ),
            "provenance": self.provenance,
            "generated_at": self.generated_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateBillEconomicProfile":
        """Deserialize StateBillEconomicProfile from a dictionary."""
        stakeholders_raw = data.get("stakeholders", [])
        stakeholders = [
            StakeholderImpact.from_dict(s) if isinstance(s, dict) else s
            for s in stakeholders_raw
        ]

        evidence_raw = data.get("evidence", [])
        evidence = [
            EvidenceReference.from_dict(e) if isinstance(e, dict) else e
            for e in evidence_raw
        ]

        factual_sum_raw = data.get("factual_summary", {})
        factual_summary = (
            FactualStakeholderSummary.from_dict(factual_sum_raw)
            if isinstance(factual_sum_raw, dict)
            else FactualStakeholderSummary()
        )

        return cls(
            bill_id=data.get("bill_id", ""),
            state=data.get("state", ""),
            policy_domain=data.get("policy_domain", ""),
            primary_sector=data.get("primary_sector"),
            secondary_sectors=data.get("secondary_sectors", []),
            sub_sectors=data.get("sub_sectors", []),
            economic_activities=data.get("economic_activities", []),
            business_types=data.get("business_types", []),
            stakeholders=stakeholders,
            geographic_scope=data.get("geographic_scope", "state-wide"),
            direct_impacts=data.get("direct_impacts", []),
            indirect_impacts=data.get("indirect_impacts", []),
            impact_mechanisms=data.get("impact_mechanisms", []),
            company_exposure_readiness=data.get("company_exposure_readiness", "UNKNOWN"),
            evidence=evidence,
            confidence=data.get("confidence", "HIGH"),
            factual_summary=factual_summary,
            provenance=data.get("provenance", {}),
            generated_at=data.get("generated_at", datetime.now(timezone.utc).isoformat()),
            schema_version=data.get("schema_version", "1.0.0"),
        )
