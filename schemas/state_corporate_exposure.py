"""
schemas/state_corporate_exposure.py
===================================
Typed data model for an Indian State Legislative Bill Corporate Exposure Record.

Encapsulates structured corporate exposure intelligence linking State legislative
bills to corporate entities (listed and unlisted) based on verified:
    Business Activity + State Presence + Bill Provision Grounding.

Strictly bounded to factual corporate analysis and qualitative exposure interpretation;
guarantees ZERO stock market predictions, price targets, or financial return forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


_FORBIDDEN_PREDICTIVE_TERMS = {
    "price target",
    "target price",
    "buy rating",
    "sell rating",
    "hold rating",
    "stock prediction",
    "market return",
    "abnormal return",
    "abnormal returns",
    "cumulative abnormal return",
    "average abnormal return",
    "alpha forecast",
    "trading strategy",
    "portfolio recommendation",
}


@dataclass
class CorporateExposureEvidence:
    """
    Traceable evidence supporting a corporate exposure claim.
    Grounded in statutory provisions, company filings, annual reports,
    or authoritative official sources.
    """
    source_type: str = "bill_text"  # "bill_text" | "company_filing" | "annual_report" | "regulatory_filing" | "government_record" | "official_website"
    reference: str = ""             # Section/clause or annual report page/disclosure reference
    claim: str = ""                 # Factual statement substantiated by the reference
    url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "reference": self.reference,
            "claim": self.claim,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CorporateExposureEvidence":
        return cls(
            source_type=data.get("source_type", "bill_text"),
            reference=data.get("reference", ""),
            claim=data.get("claim", ""),
            url=data.get("url"),
        )


@dataclass
class StatePresenceRecord:
    """
    Structured classification of a company's operational presence in a State.
    """
    state: str
    presence_types: list[str] = field(default_factory=list)  # e.g. ["manufacturing", "office", "retail"]
    facility_locations: list[str] = field(default_factory=list)  # Specific districts/cities
    description: str = ""
    evidence_source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "presence_types": self.presence_types,
            "facility_locations": self.facility_locations,
            "description": self.description,
            "evidence_source": self.evidence_source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StatePresenceRecord":
        return cls(
            state=data.get("state", ""),
            presence_types=data.get("presence_types", []),
            facility_locations=data.get("facility_locations", []),
            description=data.get("description", ""),
            evidence_source=data.get("evidence_source", ""),
        )


@dataclass
class StateCorporateExposure:
    """
    Canonical representation of a single corporate exposure to an Indian State legislative bill.
    """
    bill_id: str
    state: str
    company_id: str                      # ISIN or unique identifier
    company_name: str
    ticker: str = ""                     # NSE/BSE ticker if listed; empty if unlisted
    exchange: str = ""                   # "NSE", "BSE", "NSE/BSE", or empty
    listed_status: str = "listed"        # "listed" | "unlisted" | "subsidiary_of_listed" | "private" | "public_sector_entity" | "unknown"
    sector: str = ""                     # Primary economic sector (from State taxonomy)
    sub_sector: str = ""                 # Specific sub-sector
    business_activity: str = ""          # Activity creating exposure
    state_presence: list[str] = field(default_factory=list)   # Presence types in this State
    presence_type: str = "office"        # Dominant presence type
    exposure_type: str = "regulatory"    # "regulatory" | "taxation" | "labour" | "licensing" | "infrastructure" | "procurement" | "environmental" | "land" | "energy" | "transport" | "consumer" | "agriculture" | "healthcare" | "education" | "financial" | "other"
    exposure_direction: str = "neutral"  # "positive" | "negative" | "mixed" | "neutral" | "unknown" (Qualitative business exposure direction, NOT stock return)
    exposure_strength: str = "MEDIUM"    # "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    direct_indirect: str = "DIRECT"      # "DIRECT" | "INDIRECT" | "UNKNOWN"
    geographic_scope: str = "state_specific"  # "state_specific" | "regional" | "multi_state" | "national_with_state_operations" | "unknown"
    mechanism: str = "compliance"        # Statutory mechanism (e.g. compliance, taxation, labour_requirement)
    evidence: list[CorporateExposureEvidence] = field(default_factory=list)
    confidence: str = "HIGH"             # "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    jurisdiction: str = "state"          # "central" | "state"
    market_relevance: str = "UNKNOWN"    # "HIGH" | "MEDIUM" | "LOW" | "NONE" | "UNKNOWN" (Strictly non-predictive)
    provenance: dict[str, str] = field(default_factory=dict)
    source_urls: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)  # Information missing before market-impact modeling
    verified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        """Enforce guardrails against predictive financial terms."""
        import re

        text_content = f"{self.company_name} {self.business_activity} {self.exposure_type} {self.mechanism} {self.market_relevance}".lower()
        for ev in self.evidence:
            text_content += f" {ev.claim} {ev.reference}".lower()
        for forbidden in _FORBIDDEN_PREDICTIVE_TERMS:
            # Word boundary search to prevent matching 'car' in 'healthcare' or 'care'
            pattern = rf"\b{re.escape(forbidden)}\b"
            if re.search(pattern, text_content):
                raise ValueError(
                    f"Forbidden predictive term '{forbidden}' detected in corporate exposure for {self.company_name}."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "state": self.state,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "ticker": self.ticker,
            "exchange": self.exchange,
            "listed_status": self.listed_status,
            "sector": self.sector,
            "sub_sector": self.sub_sector,
            "business_activity": self.business_activity,
            "state_presence": self.state_presence,
            "presence_type": self.presence_type,
            "exposure_type": self.exposure_type,
            "exposure_direction": self.exposure_direction,
            "exposure_strength": self.exposure_strength,
            "direct_indirect": self.direct_indirect,
            "geographic_scope": self.geographic_scope,
            "mechanism": self.mechanism,
            "evidence": [e.to_dict() if isinstance(e, CorporateExposureEvidence) else e for e in self.evidence],
            "confidence": self.confidence,
            "jurisdiction": self.jurisdiction,
            "market_relevance": self.market_relevance,
            "provenance": self.provenance,
            "source_urls": self.source_urls,
            "missing_information": self.missing_information,
            "verified_at": self.verified_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateCorporateExposure":
        ev_list = []
        for e in data.get("evidence", []):
            if isinstance(e, dict):
                ev_list.append(CorporateExposureEvidence.from_dict(e))
            elif isinstance(e, CorporateExposureEvidence):
                ev_list.append(e)

        state_val = data.get("state", "")
        default_jurisdiction = "central" if (not state_val or state_val.lower() == "central") else "state"

        return cls(
            bill_id=data["bill_id"],
            state=state_val,
            company_id=data.get("company_id", ""),
            company_name=data.get("company_name", ""),
            ticker=data.get("ticker", ""),
            exchange=data.get("exchange", ""),
            listed_status=data.get("listed_status", "listed"),
            sector=data.get("sector", ""),
            sub_sector=data.get("sub_sector", ""),
            business_activity=data.get("business_activity", ""),
            state_presence=data.get("state_presence", []),
            presence_type=data.get("presence_type", "office"),
            exposure_type=data.get("exposure_type", "regulatory"),
            exposure_direction=data.get("exposure_direction", "neutral"),
            exposure_strength=data.get("exposure_strength", "MEDIUM"),
            direct_indirect=data.get("direct_indirect", "DIRECT"),
            geographic_scope=data.get("geographic_scope", "state_specific"),
            mechanism=data.get("mechanism", "compliance"),
            evidence=ev_list,
            confidence=data.get("confidence", "HIGH"),
            jurisdiction=data.get("jurisdiction", default_jurisdiction),
            market_relevance=data.get("market_relevance", "UNKNOWN"),
            provenance=data.get("provenance", {}),
            source_urls=data.get("source_urls", []),
            missing_information=data.get("missing_information", []),
            verified_at=data.get("verified_at", datetime.now(timezone.utc).isoformat()),
            schema_version=data.get("schema_version", "1.0.0"),
        )


# Unified alias for multi-jurisdictional company exposure modeling
CompanyExposureRecord = StateCorporateExposure

