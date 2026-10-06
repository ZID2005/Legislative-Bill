"""
schemas/personalized_intelligence.py
====================================
Task 8.28 — Decision Intelligence & Personalized Impact Workspace.

Core domain contracts for deterministic relevance matching, explainable linkages,
personalized impact tiers, and live/frozen model separation.

Architectural Rules:
1. Decision support only — never automated investment advice.
2. Relevance tiers: DIRECT, HIGH RELEVANCE, MODERATE RELEVANCE, INDIRECT, INFORMATIONAL.
   These are INFORMATION/RELEVANCE tiers, NOT Buy/Sell/Hold or price targets.
3. Model status: MODELLED, KNOWLEDGE ONLY, NOT ELIGIBLE, PENDING REVIEW.
4. Strict separation: FACT, INTERPRETATION, PREDICTION.
5. Invariant: State stock predictions MUST remain 0. Live bills remain KNOWLEDGE ONLY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RelevanceTier(str, Enum):
    """
    Transparent relevance tiers categorizing information linkage depth.
    These are purely INFORMATION/RELEVANCE tiers and NOT investment recommendations.
    """

    DIRECT = "DIRECT"
    HIGH_RELEVANCE = "HIGH RELEVANCE"
    MODERATE_RELEVANCE = "MODERATE RELEVANCE"
    INDIRECT = "INDIRECT"
    INFORMATIONAL = "INFORMATIONAL"


class RelevanceSignal(str, Enum):
    """Specific deterministic signals establishing relevance."""

    DIRECT_COMPANY_EXPOSURE = "direct_company_exposure"
    DIRECT_COMPANY_MATCH = "direct_company_match"
    INDIRECT_COMPANY_EXPOSURE = "indirect_company_exposure"
    INDUSTRY_EXPOSURE = "industry_exposure"
    INDUSTRY_MATCH = "industry_match"
    SECTOR_EXPOSURE = "sector_exposure"
    SECTOR_MATCH = "sector_match"
    GEOGRAPHIC_EXPOSURE = "geographic_exposure"
    GEOGRAPHY_MATCH = "geography_match"
    STATE_JURISDICTION_MATCH = "state_jurisdiction_match"
    STATE_POLICY_DOMAIN_MATCH = "state_policy_domain_match"
    REGULATORY_ACTIVITY = "regulatory_activity"
    PRODUCT_SERVICE_EXPOSURE = "product_service_exposure"
    SUPPLY_CHAIN_EXPOSURE = "supply_chain_exposure"
    QUANTITATIVE_MODEL_COVERAGE = "quantitative_model_coverage"
    WATCHLIST_MEMBERSHIP = "watchlist_membership"


class PersonalizedModelStatus(str, Enum):
    """Epistemic model readiness status for personalized presentation."""

    MODELLED = "MODELLED"
    KNOWLEDGE_ONLY = "KNOWLEDGE ONLY"
    NOT_ELIGIBLE = "NOT ELIGIBLE"
    PENDING_REVIEW = "PENDING REVIEW"


@dataclass
class RelevanceReason:
    """Evidence-backed explanation of why a legislative item was surfaced."""

    tier: RelevanceTier
    primary_reason: str
    evidence_statements: list[str] = field(default_factory=list)
    signals: list[RelevanceSignal] = field(default_factory=list)
    matched_entity_id: str = ""
    matched_entity_name: str = ""
    matched_entity_type: str = "COMPANY"  # COMPANY, SECTOR, INDUSTRY, STATE, BILL

    @property
    def signal(self) -> str:
        if self.signals:
            first = self.signals[0]
            return first.value if hasattr(first, "value") else str(first)
        return ""

    @property
    def description(self) -> str:
        return self.primary_reason

    @property
    def evidence(self) -> list[str]:
        return self.evidence_statements

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier.value if hasattr(self.tier, "value") else str(self.tier),
            "primary_reason": self.primary_reason,
            "evidence_statements": self.evidence_statements,
            "signals": [s.value if hasattr(s, "value") else str(s) for s in self.signals],
            "matched_entity_id": self.matched_entity_id,
            "matched_entity_name": self.matched_entity_name,
            "matched_entity_type": self.matched_entity_type,
        }


@dataclass
class AuthoritativePredictionSummary:
    """Surfaced frozen analytical quantitative predictions (47 companies, 20 Central bills only)."""

    isin: str
    company_name: str
    bill_id: str
    predicted_direction: str  # POSITIVE / NEGATIVE / NEUTRAL
    predicted_confidence: str  # HIGH / MEDIUM / LOW
    probability: Optional[float] = None
    event_window: str = "[-1,+1]"  # Must be one of the 5 authoritative horizons
    all_horizons: dict[str, dict[str, Any]] = field(default_factory=dict)
    risk_category: Optional[str] = None
    anticipation_tier: Optional[str] = None
    anticipation_score: Optional[float] = None
    anticipation_evidence_context: Optional[dict[str, Any]] = None
    pre_event_public_information: Optional[dict[str, Any]] = None
    data_source: str = "Verified Central Quantitative Baseline"

    @property
    def available(self) -> bool:
        return bool(self.all_horizons)

    @property
    def predictions_count(self) -> int:
        return len(self.all_horizons)

    @property
    def event_horizons(self) -> list[str]:
        return list(self.all_horizons.keys())

    @property
    def horizon_breakdown(self) -> dict[str, dict[str, Any]]:
        return self.all_horizons

    @property
    def notice(self) -> str:
        if not self.available:
            return "Zero stock predictions for non-modelled or state bills."
        return "Authoritative predictions across 5 event horizons."

    def to_dict(self) -> dict[str, Any]:
        return {
            "isin": self.isin,
            "company_name": self.company_name,
            "bill_id": self.bill_id,
            "predicted_direction": self.predicted_direction,
            "predicted_confidence": self.predicted_confidence,
            "probability": self.probability,
            "event_window": self.event_window,
            "all_horizons": self.all_horizons,
            "available": self.available,
            "predictions_count": self.predictions_count,
            "event_horizons": self.event_horizons,
            "horizon_breakdown": self.horizon_breakdown,
            "notice": self.notice,
            "risk_category": self.risk_category,
            "anticipation_tier": self.anticipation_tier,
            "anticipation_score": self.anticipation_score,
            "anticipation_evidence_context": self.anticipation_evidence_context,
            "pre_event_public_information": self.pre_event_public_information,
            "data_source": self.data_source,
        }


@dataclass
class PersonalizedBillImpact:
    """Structured impact linkage between legislation and personal portfolio/watchlist."""

    bill_id: str
    bill_title: str
    bill_number: Optional[str] = None
    jurisdiction: str = "central"
    state: Optional[str] = None
    status: str = "introduced"
    latest_verified_update: Optional[str] = None
    relevance_tier: RelevanceTier = RelevanceTier.INFORMATIONAL
    relevance_reasons: list[RelevanceReason] = field(default_factory=list)
    primary_linkage_reason: str = ""
    affected_sectors: list[str] = field(default_factory=list)
    affected_industries: list[str] = field(default_factory=list)
    affected_companies: list[str] = field(default_factory=list)
    model_status: PersonalizedModelStatus = PersonalizedModelStatus.KNOWLEDGE_ONLY
    prediction_availability: bool = False
    source_provenance: list[str] = field(default_factory=list)
    authoritative_prediction: Optional[AuthoritativePredictionSummary] = None
    pre_event_public_information: Optional[dict[str, Any]] = None
    epistemic_level: str = "INTERPRETATION"  # FACT / INTERPRETATION / PREDICTION

    @property
    def reasons(self) -> list[RelevanceReason]:
        return self.relevance_reasons

    @property
    def confidence_score(self) -> float:
        tier_val = self.relevance_tier.value if hasattr(self.relevance_tier, "value") else str(self.relevance_tier)
        if tier_val == "DIRECT":
            return 0.95
        if tier_val == "HIGH RELEVANCE":
            return 0.85
        if tier_val == "MODERATE RELEVANCE":
            return 0.70
        return 0.50

    @property
    def model_status_label(self) -> str:
        st = self.model_status.value if hasattr(self.model_status, "value") else str(self.model_status)
        if st == "MODELLED":
            return "MODELLED — CENTRAL QUANTITATIVE"
        if st == "NOT ELIGIBLE":
            return "NOT ELIGIBLE FOR STOCK MODEL"
        if st == "KNOWLEDGE ONLY":
            return "LIVE — KNOWLEDGE ONLY"
        return st

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "bill_number": self.bill_number,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "status": self.status,
            "latest_verified_update": self.latest_verified_update,
            "relevance_tier": self.relevance_tier.value if hasattr(self.relevance_tier, "value") else str(self.relevance_tier),
            "relevance_reasons": [r.to_dict() for r in self.relevance_reasons],
            "primary_linkage_reason": self.primary_linkage_reason,
            "affected_sectors": self.affected_sectors,
            "affected_industries": self.affected_industries,
            "affected_companies": self.affected_companies,
            "model_status": self.model_status.value if hasattr(self.model_status, "value") else str(self.model_status),
            "prediction_availability": self.prediction_availability,
            "source_provenance": self.source_provenance,
            "authoritative_prediction": self.authoritative_prediction.to_dict() if self.authoritative_prediction else None,
            "pre_event_public_information": self.pre_event_public_information,
            "epistemic_level": self.epistemic_level,
        }


@dataclass
class PersonalizedChangeFeedItem:
    """Meaningful legislative change event tailored to the user's portfolio or watchlist."""

    event_id: str
    event_type: str  # NEW_BILL, BILL_STATUS_CHANGED, DOCUMENT_CHANGED, COMPANY_EXPOSURE_UPDATED, SECTOR_ACTIVITY
    bill_id: str
    bill_title: str
    jurisdiction: str = "central"
    state: Optional[str] = None
    relevance_tier: RelevanceTier = RelevanceTier.HIGH_RELEVANCE
    relevance_reason: str = ""
    detected_at: str = field(default_factory=_utcnow_iso)
    model_status: PersonalizedModelStatus = PersonalizedModelStatus.KNOWLEDGE_ONLY
    deep_link: str = ""
    source_name: str = ""
    provenance_url: Optional[str] = None
    epistemic_status: str = "OBSERVED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "relevance_tier": self.relevance_tier.value if hasattr(self.relevance_tier, "value") else str(self.relevance_tier),
            "relevance_reason": self.relevance_reason,
            "detected_at": self.detected_at,
            "model_status": self.model_status.value if hasattr(self.model_status, "value") else str(self.model_status),
            "deep_link": self.deep_link,
            "source_name": self.source_name,
            "provenance_url": self.provenance_url,
            "epistemic_status": self.epistemic_status,
        }


@dataclass
class PortfolioLegislativeExposureSummary:
    """Aggregated portfolio-to-legislation exposure view."""

    total_holdings: int
    exposed_holdings_count: int
    total_relevant_bills: int
    direct_bills_count: int
    high_relevance_bills_count: int
    moderate_relevance_bills_count: int
    indirect_bills_count: int
    modelled_central_bills_count: int
    knowledge_only_bills_count: int
    state_bills_count: int
    sector_distribution: dict[str, int] = field(default_factory=dict)
    relevant_bills: list[PersonalizedBillImpact] = field(default_factory=list)
    holdings_exposure_map: dict[str, list[str]] = field(default_factory=dict)  # company -> bill_ids
    portfolio_id: Optional[str] = None
    sectors_affected: list[str] = field(default_factory=list)
    industries_affected: list[str] = field(default_factory=list)
    disclaimer: str = (
        "DECISION SUPPORT NOTICE: Personalized legislative intelligence is provided strictly for "
        "informational and decision-support purposes. It does not constitute investment advice, financial planning, "
        "or a recommendation to buy, sell, or hold any security. State bills and qualitative entities carry zero stock predictions."
    )
    generated_at: str = field(default_factory=_utcnow_iso)

    @property
    def total_holdings_count(self) -> int:
        return self.total_holdings

    @property
    def total_relevant_bills_count(self) -> int:
        return self.total_relevant_bills

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "total_holdings": self.total_holdings,
            "total_holdings_count": self.total_holdings,
            "exposed_holdings_count": self.exposed_holdings_count,
            "total_relevant_bills": self.total_relevant_bills,
            "total_relevant_bills_count": self.total_relevant_bills,
            "direct_bills_count": self.direct_bills_count,
            "high_relevance_bills_count": self.high_relevance_bills_count,
            "moderate_relevance_bills_count": self.moderate_relevance_bills_count,
            "indirect_bills_count": self.indirect_bills_count,
            "modelled_central_bills_count": self.modelled_central_bills_count,
            "knowledge_only_bills_count": self.knowledge_only_bills_count,
            "state_bills_count": self.state_bills_count,
            "sector_distribution": self.sector_distribution,
            "sectors_affected": self.sectors_affected or list(self.sector_distribution.keys()),
            "industries_affected": self.industries_affected,
            "relevant_bills": [b.to_dict() if hasattr(b, "to_dict") else b for b in self.relevant_bills],
            "holdings_exposure_map": self.holdings_exposure_map,
            "disclaimer": self.disclaimer,
            "generated_at": self.generated_at,
        }


@dataclass
class PersonalizedDashboardData:
    """Dashboard aggregator for 'YOUR LEGISLATIVE INTELLIGENCE'."""

    user_id: str
    tenant_id: str
    relevant_new_bills: list[PersonalizedBillImpact] = field(default_factory=list)
    recent_bill_changes: list[PersonalizedChangeFeedItem] = field(default_factory=list)
    relevant_state_legislation: list[PersonalizedBillImpact] = field(default_factory=list)
    companies_exposed: list[dict[str, Any]] = field(default_factory=list)
    sectors_affected: list[dict[str, Any]] = field(default_factory=list)
    modelled_central_bills: list[PersonalizedBillImpact] = field(default_factory=list)
    knowledge_only_developments: list[PersonalizedBillImpact] = field(default_factory=list)
    upcoming_verified_legislation: list[dict[str, Any]] = field(default_factory=list)
    recent_document_changes: list[dict[str, Any]] = field(default_factory=list)
    portfolio_exposure: Optional[dict[str, Any]] = None
    watchlist_exposure: list[Any] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)
    disclaimer: str = (
        "DECISION SUPPORT NOTICE: Personalized legislative intelligence is provided strictly for "
        "informational and decision-support purposes. It does not constitute investment advice, financial planning, "
        "or a recommendation to buy, sell, or hold any security. State bills and qualitative entities carry zero stock predictions."
    )
    generated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        port_exp = self.portfolio_exposure or {
            "total_holdings": self.stats.get("total_holdings", 0),
            "exposed_holdings_count": len(self.companies_exposed),
            "total_relevant_bills": self.stats.get("total_relevant_bills", 0),
            "direct_bills_count": self.stats.get("direct_matches", 0),
            "high_relevance_bills_count": self.stats.get("high_relevance_matches", 0),
            "moderate_relevance_bills_count": 0,
            "indirect_bills_count": 0,
            "modelled_central_bills_count": len(self.modelled_central_bills),
            "knowledge_only_bills_count": len(self.knowledge_only_developments),
            "state_bills_count": len(self.relevant_state_legislation),
            "sector_distribution": {s.get("sector", ""): s.get("count", 0) for s in self.sectors_affected},
            "sectors_affected": [s.get("sector", "") for s in self.sectors_affected],
            "industries_affected": [],
            "relevant_bills": [b.to_dict() if hasattr(b, "to_dict") else b for b in self.relevant_new_bills],
            "holdings_exposure_map": {c.get("company_name", ""): c.get("bill_ids", []) for c in self.companies_exposed},
            "disclaimer": self.disclaimer,
            "generated_at": self.generated_at,
        }
        rel_new = [b.to_dict() if hasattr(b, "to_dict") else b for b in self.relevant_new_bills]
        rel_state = [b.to_dict() if hasattr(b, "to_dict") else b for b in self.relevant_state_legislation]
        rel_central = [b.to_dict() if hasattr(b, "to_dict") else b for b in (self.modelled_central_bills or self.relevant_new_bills)]
        recent_changes = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.recent_bill_changes]

        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "portfolio_exposure": port_exp,
            "watchlist_exposure": self.watchlist_exposure,
            "relevant_central_bills": rel_central,
            "relevant_state_bills": rel_state,
            "change_feed_highlights": recent_changes,
            "relevant_new_bills": rel_new,
            "recent_bill_changes": recent_changes,
            "relevant_state_legislation": rel_state,
            "companies_exposed": self.companies_exposed,
            "sectors_affected": self.sectors_affected,
            "modelled_central_bills": [b.to_dict() if hasattr(b, "to_dict") else b for b in self.modelled_central_bills],
            "knowledge_only_developments": [b.to_dict() if hasattr(b, "to_dict") else b for b in self.knowledge_only_developments],
            "upcoming_verified_legislation": self.upcoming_verified_legislation,
            "recent_document_changes": self.recent_document_changes,
            "stats": self.stats,
            "disclaimer": self.disclaimer,
            "generated_at": self.generated_at,
        }


@dataclass
class PersonalizedImpactReportData:
    """Full data payload for 'MY LEGISLATIVE IMPACT REPORT'."""

    report_id: str
    user_id: str
    tenant_id: str
    report_title: str = "MY LEGISLATIVE IMPACT REPORT"
    portfolio_id: Optional[str] = None
    executive_summary: dict[str, Any] = field(default_factory=dict)
    portfolio_holdings: list[dict[str, Any]] = field(default_factory=list)
    legislative_exposures: list[PersonalizedBillImpact] = field(default_factory=list)
    sector_breakdown: list[dict[str, Any]] = field(default_factory=list)
    governance_disclaimer: str = (
        "DECISION SUPPORT NOTICE: Personalized legislative intelligence is provided strictly for "
        "informational and decision-support purposes. It does not constitute investment advice, financial planning, "
        "or a recommendation to buy, sell, or hold any security. State bills and qualitative entities carry zero stock predictions."
    )
    portfolio_summary: dict[str, Any] = field(default_factory=dict)
    relevant_bills: list[PersonalizedBillImpact] = field(default_factory=list)
    new_developments: list[PersonalizedChangeFeedItem] = field(default_factory=list)
    company_exposures: list[dict[str, Any]] = field(default_factory=list)
    sector_exposures: list[dict[str, Any]] = field(default_factory=list)
    modelled_central_results: list[dict[str, Any]] = field(default_factory=list)
    knowledge_only_developments: list[dict[str, Any]] = field(default_factory=list)
    upcoming_verified_legislation: list[dict[str, Any]] = field(default_factory=list)
    sources_and_provenance: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        rel_bills = [b.to_dict() if hasattr(b, "to_dict") else b for b in (self.legislative_exposures or self.relevant_bills)]
        return {
            "report_id": self.report_id,
            "portfolio_id": self.portfolio_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "report_title": self.report_title,
            "executive_summary": self.executive_summary or {"title": self.report_title, "summary": "Legislative portfolio impact overview."},
            "portfolio_holdings": self.portfolio_holdings,
            "legislative_exposures": rel_bills,
            "sector_breakdown": self.sector_breakdown or self.sector_exposures,
            "governance_disclaimer": self.governance_disclaimer,
            "portfolio_summary": self.portfolio_summary,
            "relevant_bills": rel_bills,
            "new_developments": [d.to_dict() if hasattr(d, "to_dict") else d for d in self.new_developments],
            "company_exposures": self.company_exposures,
            "sector_exposures": self.sector_exposures,
            "modelled_central_results": self.modelled_central_results,
            "knowledge_only_developments": [k.to_dict() if hasattr(k, "to_dict") else k for k in self.knowledge_only_developments],
            "upcoming_verified_legislation": self.upcoming_verified_legislation,
            "sources_and_provenance": self.sources_and_provenance,
            "disclaimers": self.disclaimers,
            "generated_at": self.generated_at,
        }
