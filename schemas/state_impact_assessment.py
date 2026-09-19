"""
schemas/state_impact_assessment.py
==================================
Typed data model for an Indian State Legislative Bill Economic and Market Impact Assessment.

Establishes a rigorous methodology layer evaluating:
1. Economic mechanisms (real economy transmission)
2. Economic impact direction and strength
3. Market relevance (presence of listed corporate exposure and financial transmission)
4. State market-modeling eligibility (strict 10-point deterministic scorecard)
5. Data sufficiency assessment (14 dimensions)
6. Event date quality and roles (primary vs alternative)
7. Anticipation / pricing-in readiness
8. Market data readiness

Guarantees:
- ZERO stock price predictions
- ZERO price targets or alpha forecasts
- ZERO event studies or abnormal return calculations
- Strict preservation of the distinction: Economic Impact != Stock Market Impact
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
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


# ==============================================================================
# 1. Enums
# ==============================================================================

class EconomicMechanism(str, Enum):
    """Taxonomy of underlying economic transmission mechanisms."""
    TAXATION = "taxation"
    SUBSIDY = "subsidy"
    COMPLIANCE_COST = "compliance_cost"
    LABOUR_COST = "labour_cost"
    LICENSING = "licensing"
    REGULATION = "regulation"
    PRICING = "pricing"
    DEMAND = "demand"
    SUPPLY = "supply"
    INVESTMENT = "investment"
    INFRASTRUCTURE = "infrastructure"
    LAND = "land"
    ELECTRICITY_COST = "electricity_cost"
    TRANSPORTATION_COST = "transportation_cost"
    FINANCING = "financing"
    CREDIT = "credit"
    PROCUREMENT = "procurement"
    MARKET_ACCESS = "market_access"
    ENVIRONMENTAL_COST = "environmental_cost"
    PUBLIC_SPENDING = "public_spending"
    PRODUCTIVITY = "productivity"
    EMPLOYMENT = "employment"
    WAGES = "wages"
    CONSUMER_COST = "consumer_cost"
    OTHER = "other"
    UNKNOWN = "unknown"


class EconomicImpactDirection(str, Enum):
    """Direction of estimated real-economy impact (distinct from stock direction)."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class EconomicImpactStrength(str, Enum):
    """Strength of estimated economic impact based on statutory magnitude and scope."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class MarketRelevance(str, Enum):
    """
    Degree of relevance to listed financial markets.
    NOT a prediction; represents whether listed corporate exposure exists.
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class ModelingEligibility(str, Enum):
    """Strict eligibility classification for future State stock modeling pipelines."""
    ELIGIBLE = "ELIGIBLE"
    CONDITIONALLY_ELIGIBLE = "CONDITIONALLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class DataSufficiency(str, Enum):
    """Overall data readiness classification across 14 audit dimensions."""
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


class EventDateQuality(str, Enum):
    """Quality and verification status of statutory event dates."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class EventDateRole(str, Enum):
    """Statutory role of an identified event date."""
    INTRODUCTION = "introduction"
    PASSAGE = "passage"
    ASSENT = "assent"
    GAZETTE = "gazette"
    COMMENCEMENT = "commencement"
    OTHER = "other"


class AnticipationReadiness(str, Enum):
    """Readiness of information channels for modeling legislative anticipation."""
    READY = "READY"
    PARTIAL = "PARTIAL"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    UNKNOWN = "UNKNOWN"


# ==============================================================================
# 2. Supporting Structures
# ==============================================================================

@dataclass
class EventDateRecord:
    """A verified or recorded statutory date and its procedural role."""
    role: str = EventDateRole.INTRODUCTION.value
    date: str = ""
    source: str = "official_gazette"
    is_primary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "date": self.date,
            "source": self.source,
            "is_primary": self.is_primary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventDateRecord:
        return cls(
            role=data.get("role", EventDateRole.INTRODUCTION.value),
            date=data.get("date", ""),
            source=data.get("source", "official_gazette"),
            is_primary=data.get("is_primary", False),
        )


@dataclass
class MarketDataReadinessSummary:
    """Summary of market data availability for candidate securities."""
    candidate_companies_count: int = 0
    listed_companies_count: int = 0
    unlisted_companies_count: int = 0
    companies_with_market_data: list[str] = field(default_factory=list)
    companies_missing_market_data: list[str] = field(default_factory=list)
    benchmark_available: bool = True
    benchmark_ticker: str = "^NSEI"
    trading_calendar_coverage: str = "COMPLETE"  # "COMPLETE" | "PARTIAL" | "INSUFFICIENT"

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_companies_count": self.candidate_companies_count,
            "listed_companies_count": self.listed_companies_count,
            "unlisted_companies_count": self.unlisted_companies_count,
            "companies_with_market_data": self.companies_with_market_data,
            "companies_missing_market_data": self.companies_missing_market_data,
            "benchmark_available": self.benchmark_available,
            "benchmark_ticker": self.benchmark_ticker,
            "trading_calendar_coverage": self.trading_calendar_coverage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketDataReadinessSummary:
        return cls(
            candidate_companies_count=data.get("candidate_companies_count", 0),
            listed_companies_count=data.get("listed_companies_count", 0),
            unlisted_companies_count=data.get("unlisted_companies_count", 0),
            companies_with_market_data=data.get("companies_with_market_data", []),
            companies_missing_market_data=data.get("companies_missing_market_data", []),
            benchmark_available=data.get("benchmark_available", True),
            benchmark_ticker=data.get("benchmark_ticker", "^NSEI"),
            trading_calendar_coverage=data.get("trading_calendar_coverage", "COMPLETE"),
        )


@dataclass
class EligibilityScorecard:
    """Deterministic 10-point scorecard determining market modeling eligibility."""
    bill_identity_verified: bool = False
    state_jurisdiction_verified: bool = False
    event_date_verified: bool = False
    economic_mechanism_identified: bool = False
    corporate_exposure_verified: bool = False
    listed_company_verified: bool = False
    historical_market_data_available: bool = False
    benchmark_data_available: bool = False
    event_date_identifiable: bool = False
    anticipation_readiness_sufficient: bool = False
    result: str = ModelingEligibility.NOT_ELIGIBLE.value
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_identity_verified": self.bill_identity_verified,
            "state_jurisdiction_verified": self.state_jurisdiction_verified,
            "event_date_verified": self.event_date_verified,
            "economic_mechanism_identified": self.economic_mechanism_identified,
            "corporate_exposure_verified": self.corporate_exposure_verified,
            "listed_company_verified": self.listed_company_verified,
            "historical_market_data_available": self.historical_market_data_available,
            "benchmark_data_available": self.benchmark_data_available,
            "event_date_identifiable": self.event_date_identifiable,
            "anticipation_readiness_sufficient": self.anticipation_readiness_sufficient,
            "result": self.result,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EligibilityScorecard:
        return cls(
            bill_identity_verified=data.get("bill_identity_verified", False),
            state_jurisdiction_verified=data.get("state_jurisdiction_verified", False),
            event_date_verified=data.get("event_date_verified", False),
            economic_mechanism_identified=data.get("economic_mechanism_identified", False),
            corporate_exposure_verified=data.get("corporate_exposure_verified", False),
            listed_company_verified=data.get("listed_company_verified", False),
            historical_market_data_available=data.get("historical_market_data_available", False),
            benchmark_data_available=data.get("benchmark_data_available", False),
            event_date_identifiable=data.get("event_date_identifiable", False),
            anticipation_readiness_sufficient=data.get("anticipation_readiness_sufficient", False),
            result=data.get("result", ModelingEligibility.NOT_ELIGIBLE.value),
            notes=data.get("notes", []),
        )

    def format_text(self, bill_id: str = "") -> str:
        """Render a clean, human-readable ASCII scorecard."""
        lines = [
            f"STATE BILL: {bill_id}",
            "↓",
            f"Bill identity verified: {'YES' if self.bill_identity_verified else 'NO'}",
            f"State jurisdiction verified: {'YES' if self.state_jurisdiction_verified else 'NO'}",
            f"Event date verified: {'YES' if self.event_date_verified else 'NO'}",
            f"Economic mechanism identified: {'YES' if self.economic_mechanism_identified else 'NO'}",
            f"Corporate exposure verified: {'YES' if self.corporate_exposure_verified else 'NO'}",
            f"Listed company verified: {'YES' if self.listed_company_verified else 'NO'}",
            f"Historical market data: {'YES' if self.historical_market_data_available else 'NO'}",
            f"Benchmark data: {'YES' if self.benchmark_data_available else 'NO'}",
            f"Event date identifiable: {'YES' if self.event_date_identifiable else 'NO'}",
            f"Anticipation readiness: {'PARTIAL' if self.anticipation_readiness_sufficient else 'NOT_AVAILABLE'}",
            "↓",
            f"Result: {self.result}",
        ]
        return "\n".join(lines)


# ==============================================================================
# 3. Canonical Model
# ==============================================================================

@dataclass
class StateImpactAssessment:
    """
    Canonical representation of an Indian State Legislative Bill Economic and Market Impact Assessment.
    """
    bill_id: str
    state: str
    title: str = ""
    bill_number: str = ""
    economic_mechanisms: list[str] = field(default_factory=list)
    economic_direction: str = EconomicImpactDirection.UNKNOWN.value
    economic_strength: str = EconomicImpactStrength.UNKNOWN.value
    market_relevance: str = MarketRelevance.NONE.value
    modeling_eligibility: str = ModelingEligibility.NOT_ELIGIBLE.value
    data_sufficiency: str = DataSufficiency.INSUFFICIENT.value
    event_date_quality: str = EventDateQuality.NONE.value
    primary_event_date: Optional[EventDateRecord] = None
    alternative_event_dates: list[EventDateRecord] = field(default_factory=list)
    anticipation_readiness: str = AnticipationReadiness.NOT_AVAILABLE.value
    candidate_anticipation_channels: list[str] = field(default_factory=list)
    market_data_readiness: Optional[MarketDataReadinessSummary] = None
    listed_company_count: int = 0
    exposure_count: int = 0
    direct_exposure_count: int = 0
    indirect_exposure_count: int = 0
    missing_requirements: list[str] = field(default_factory=list)
    scorecard: EligibilityScorecard = field(default_factory=EligibilityScorecard)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: str = "HIGH"  # "HIGH" | "MEDIUM" | "LOW"
    provenance: dict[str, str] = field(default_factory=dict)
    schema_version: str = "1.0.0"
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        """Enforce strict guardrails against predictive financial terms."""
        text_content = f"{self.title} {self.bill_number} {self.economic_direction} {self.economic_strength}".lower()
        for m in self.economic_mechanisms:
            text_content += f" {m}".lower()
        for ev in self.evidence:
            text_content += f" {ev.get('claim', '')} {ev.get('reference', '')}".lower()
        for note in self.scorecard.notes:
            text_content += f" {note}".lower()

        for forbidden in _FORBIDDEN_PREDICTIVE_TERMS:
            pattern = rf"\b{re.escape(forbidden)}\b"
            if re.search(pattern, text_content):
                raise ValueError(
                    f"Forbidden predictive term '{forbidden}' detected in StateImpactAssessment for {self.bill_id}."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "state": self.state,
            "title": self.title,
            "bill_number": self.bill_number,
            "economic_mechanisms": self.economic_mechanisms,
            "economic_direction": self.economic_direction,
            "economic_strength": self.economic_strength,
            "market_relevance": self.market_relevance,
            "modeling_eligibility": self.modeling_eligibility,
            "data_sufficiency": self.data_sufficiency,
            "event_date_quality": self.event_date_quality,
            "primary_event_date": self.primary_event_date.to_dict() if self.primary_event_date else None,
            "alternative_event_dates": [d.to_dict() if isinstance(d, EventDateRecord) else d for d in self.alternative_event_dates],
            "anticipation_readiness": self.anticipation_readiness,
            "candidate_anticipation_channels": self.candidate_anticipation_channels,
            "market_data_readiness": self.market_data_readiness.to_dict() if self.market_data_readiness else None,
            "listed_company_count": self.listed_company_count,
            "exposure_count": self.exposure_count,
            "direct_exposure_count": self.direct_exposure_count,
            "indirect_exposure_count": self.indirect_exposure_count,
            "missing_requirements": self.missing_requirements,
            "scorecard": self.scorecard.to_dict() if isinstance(self.scorecard, EligibilityScorecard) else self.scorecard,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateImpactAssessment:
        p_date = None
        if data.get("primary_event_date"):
            raw_p = data["primary_event_date"]
            p_date = EventDateRecord.from_dict(raw_p) if isinstance(raw_p, dict) else raw_p

        alt_dates = []
        for d in data.get("alternative_event_dates", []):
            if isinstance(d, dict):
                alt_dates.append(EventDateRecord.from_dict(d))
            elif isinstance(d, EventDateRecord):
                alt_dates.append(d)

        mkt_readiness = None
        if data.get("market_data_readiness"):
            raw_m = data["market_data_readiness"]
            mkt_readiness = MarketDataReadinessSummary.from_dict(raw_m) if isinstance(raw_m, dict) else raw_m

        scorecard_raw = data.get("scorecard", {})
        scorecard = (
            EligibilityScorecard.from_dict(scorecard_raw)
            if isinstance(scorecard_raw, dict)
            else EligibilityScorecard()
        )

        return cls(
            bill_id=data["bill_id"],
            state=data.get("state", ""),
            title=data.get("title", ""),
            bill_number=data.get("bill_number", ""),
            economic_mechanisms=data.get("economic_mechanisms", []),
            economic_direction=data.get("economic_direction", EconomicImpactDirection.UNKNOWN.value),
            economic_strength=data.get("economic_strength", EconomicImpactStrength.UNKNOWN.value),
            market_relevance=data.get("market_relevance", MarketRelevance.NONE.value),
            modeling_eligibility=data.get("modeling_eligibility", ModelingEligibility.NOT_ELIGIBLE.value),
            data_sufficiency=data.get("data_sufficiency", DataSufficiency.INSUFFICIENT.value),
            event_date_quality=data.get("event_date_quality", EventDateQuality.NONE.value),
            primary_event_date=p_date,
            alternative_event_dates=alt_dates,
            anticipation_readiness=data.get("anticipation_readiness", AnticipationReadiness.NOT_AVAILABLE.value),
            candidate_anticipation_channels=data.get("candidate_anticipation_channels", []),
            market_data_readiness=mkt_readiness,
            listed_company_count=data.get("listed_company_count", 0),
            exposure_count=data.get("exposure_count", 0),
            direct_exposure_count=data.get("direct_exposure_count", 0),
            indirect_exposure_count=data.get("indirect_exposure_count", 0),
            missing_requirements=data.get("missing_requirements", []),
            scorecard=scorecard,
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", "HIGH"),
            provenance=data.get("provenance", {}),
            schema_version=data.get("schema_version", "1.0.0"),
            generated_at=data.get("generated_at", datetime.now(timezone.utc).isoformat()),
        )
