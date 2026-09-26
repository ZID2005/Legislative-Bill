"""
api/schemas.py
==============
Pydantic v2 schemas for all API request and response bodies.
"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Generic Pagination & Base Responses
# ---------------------------------------------------------------------------


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(..., description="List of items in the current page")
    total: int = Field(..., description="Total count of items matching the query")
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="Application health status")
    api_version: str = Field("1.0.0", description="API version")
    environment: str = Field("production", description="Runtime environment")
    timestamp: str = Field(..., description="Current ISO UTC timestamp")


class SuccessStatusResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Legislative Bills Schemas
# ---------------------------------------------------------------------------


class BillSummaryItem(BaseModel):
    bill_id: str
    jurisdiction: str
    state: Optional[str] = None
    title: str
    short_title: str
    bill_number: Optional[str] = None
    legislature: str
    house: str
    year: Optional[int] = None
    introduction_date: Optional[str] = None
    assent_date: Optional[str] = None
    status: str
    policy_domain: Optional[str] = None
    economic_sectors: list[str] = Field(default_factory=list)
    secondary_sectors: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    summary: str
    company_exposure_count: int = 0
    listed_company_exposure_count: int = 0
    market_relevance: str = "NONE"
    modeling_eligibility: str = "NOT_ELIGIBLE"
    data_sufficiency: str = "INSUFFICIENT"
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
    data_quality: str = "VERIFIED"


class BillKnowledgeSchema(BaseModel):
    amended_acts: list[str] = Field(default_factory=list)
    regulatory_authority: Optional[str] = None
    financial_terms: Optional[str] = None
    penalties_or_enforcement: Optional[str] = None
    objective: Optional[str] = None
    key_provisions: list[str] = Field(default_factory=list)


class BillDetailResponse(BaseModel):
    bill: BillSummaryItem
    provisions: list[str] = Field(default_factory=list)
    knowledge: Optional[BillKnowledgeSchema] = None
    provenance: dict[str, str] = Field(default_factory=dict)
    prediction_available: bool = False
    related_bills: list[BillSummaryItem] = Field(default_factory=list)


class CorporateExposureEvidenceSchema(BaseModel):
    claim: str
    reference: str
    url: Optional[str] = None
    statutory_section: Optional[str] = None


class BillCompanyExposureSchema(BaseModel):
    bill_id: str
    bill_title: str
    company_id: str
    company_name: str
    bill_number: Optional[str] = None
    jurisdiction: str
    state: Optional[str] = None
    bill_status: str
    sector: str
    sub_sector: str
    business_activity: str
    exposure_type: str
    exposure_direction: str
    exposure_strength: str
    direct_indirect: str
    geographic_scope: str
    mechanism: str
    market_relevance: str
    confidence: str
    has_evidence: bool = True
    evidence: list[CorporateExposureEvidenceSchema] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class BillPredictionStatusResponse(BaseModel):
    available: bool
    has_predictions: bool = False
    bill_id: str
    reason: Optional[str] = None
    firewall_status: Optional[str] = None
    message: Optional[str] = None
    jurisdiction: str
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


# ---------------------------------------------------------------------------
# Corporate Intelligence Schemas
# ---------------------------------------------------------------------------


class CompanySummaryItem(BaseModel):
    company_id: str
    company_name: str
    ticker_nse: Optional[str] = None
    ticker_bse: Optional[str] = None
    isin: str
    sector: str
    industry: str
    sub_industry: Optional[str] = None
    entity_type: str
    universe_type: str
    ownership_type: str
    is_active: bool
    listing_status: str
    hq_state: Optional[str] = None
    watchlist_eligible: bool
    is_quant_eligible: bool
    market_prediction_available: bool
    documented_exposure_count: int = 0


class CompanyDetailResponse(BaseModel):
    company_id: str
    company_name: str
    legal_identity: str
    aliases: list[str] = Field(default_factory=list)
    ticker_nse: str = ""
    ticker_bse: str = ""
    bse_code: str = ""
    isin: str = ""
    entity_type: str = "listed_company"
    universe_type: str = "quantitative"
    group_name: Optional[str] = None
    ownership_type: str = "unknown"
    is_active: bool = True
    listing_status: str = "Listed"
    sector: str = ""
    industry: str = ""
    sub_industry: str = ""
    business_description: str = ""
    business_activities: list[str] = Field(default_factory=list)
    hq_state: str = ""
    hq_city: str = ""
    operating_states: list[str] = Field(default_factory=list)
    state_presences: list[dict[str, Any]] = Field(default_factory=list)
    facilities: list[dict[str, Any]] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    data_quality_score: Optional[float] = None
    data_quality_label: str = "VERIFIED"
    related_bills: list[BillCompanyExposureSchema] = Field(default_factory=list)
    total_exposures: int = 0
    central_exposures_count: int = 0
    state_exposures_count: int = 0
    direct_exposures_count: int = 0
    indirect_exposures_count: int = 0
    exposure_types: list[str] = Field(default_factory=list)
    mechanisms: list[str] = Field(default_factory=list)
    affected_sectors: list[str] = Field(default_factory=list)
    watchlist_eligible: bool = False
    is_quant_eligible: bool = False
    market_prediction_available: bool = False
    quantitative_firewall_status: str = "ACTIVE"


class CompanyPredictionStatusResponse(BaseModel):
    available: bool
    has_predictions: bool = False
    company_id: str
    reason: Optional[str] = None
    firewall_status: Optional[str] = None
    message: Optional[str] = None
    universe_type: str
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class CompanyAnticipationResponse(BaseModel):
    available: bool
    has_anticipation: bool = False
    company_id: str
    reason: Optional[str] = None
    firewall_status: Optional[str] = None
    message: Optional[str] = None
    scores: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class CompanyExposureExplanationResponse(BaseModel):
    company_name: str
    company_id: str
    bill_id: str
    bill_title: str
    has_exposure: bool
    exposure_type: str = "NONE"
    direct_indirect: str = "NONE"
    exposure_strength: str = "NONE"
    business_activity: str = ""
    geographic_relevance: str = ""
    economic_mechanism: str = ""
    evidence_claims: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    market_relevance: str = "NONE"
    why_explanation: str = ""
    data_quality: str = "VERIFIED"
    provenance_sources: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Market Predictions Schemas (Central Level 1)
# ---------------------------------------------------------------------------


class PredictionItem(BaseModel):
    prediction_id: str
    bill_id: str
    company_isin: str
    company_name: Optional[str] = None
    company_symbol: Optional[str] = None
    sector: Optional[str] = None
    event_window: str
    predicted_direction: str = "NEUTRAL"
    predicted_market_moving: bool = False
    market_moving_probability: float = 0.0
    predicted_impact_strength: str = "LOW"
    predicted_confidence: str = "LOW"
    confidence_score: float = 0.0
    model_version: str = "v1.0"
    created_at: str = ""


class DecisionRecordResponse(BaseModel):
    decision_id: str
    prediction_id: str
    bill_id: str
    company_isin: str
    event_window: str
    risk_category: str
    pricing_in_risk: str
    impact_category: str
    impact_score: float
    risk_score: float
    decision_reason: str
    investor_summary: str
    business_summary: str
    public_summary: str
    created_at: str


class AnticipationScoreResponse(BaseModel):
    bill_id: str
    company_isin: str
    anticipation_score: float
    anticipation_tier: str
    diffusion_index: float
    pre_event_volume_ratio: float
    pre_event_car: float
    leakage_indicator: bool
    evidence_summary: list[str] = Field(default_factory=list)


class StakeholderReportResponse(BaseModel):
    report_id: str
    bill_id: str
    company_isin: str
    event_window: str
    stakeholder_type: str
    executive_summary: str
    impact_summary: Optional[str] = None
    risk_summary: Optional[str] = None
    anticipation_summary: Optional[str] = None
    confidence_summary: Optional[str] = None
    key_takeaways: list[str] = Field(default_factory=list)
    key_factors: list[str] = Field(default_factory=list)
    transmission_channels: list[str] = Field(default_factory=list)
    methodology_note: Optional[str] = None
    disclaimer: Optional[str] = None
    created_at: str


class HorizonComparisonItem(BaseModel):
    event_window: str
    is_modeled: bool = True
    predicted_direction: Optional[str] = None
    direction_probability: dict[str, float] = Field(default_factory=dict)
    predicted_market_moving: Optional[bool] = None
    market_moving_probability: Optional[float] = None
    predicted_impact_strength: Optional[str] = None
    predicted_confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    impact_score: Optional[float] = None
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    pricing_in_risk: Optional[str] = None
    note: Optional[str] = None


class HorizonComparisonResponse(BaseModel):
    bill_id: str
    bill_title: str
    company_isin: str
    company_name: str
    company_symbol: str
    modeled_windows: list[str] = Field(default_factory=list)
    comparisons: list[HorizonComparisonItem] = Field(default_factory=list)
    unmodeled_note: str = (
        "Windows [0,1], [0,2], [0,5] are not part of the validated Central econometric dataset. "
        "Modeled windows are [-1,+1], [-3,+3], [-5,+5], [-5,+10], and [-10,+10]."
    )


# ---------------------------------------------------------------------------
# Risk Analytics Schemas (Task 8.14.7)
# ---------------------------------------------------------------------------


class RiskBandDistribution(BaseModel):
    VERY_LOW: int = 0
    LOW: int = 0
    MODERATE: int = 0
    HIGH: int = 0
    VERY_HIGH: int = 0


class SectorRiskSummary(BaseModel):
    sector: str
    avg_risk_score: float
    record_count: int
    band_distribution: RiskBandDistribution


class EventWindowRiskSummary(BaseModel):
    event_window: str
    avg_risk_score: float
    record_count: int
    band_distribution: RiskBandDistribution


class BillRiskSummary(BaseModel):
    bill_id: str
    bill_title: str
    jurisdiction: str = "central"
    avg_risk_score: float
    max_risk_score: float
    high_risk_count: int
    record_count: int
    dominant_risk_band: str


class CompanyRiskSummary(BaseModel):
    company_isin: str
    company_name: str
    company_symbol: str
    sector: str
    universe_type: str = "quantitative"
    avg_risk_score: float
    max_risk_score: float
    record_count: int
    dominant_risk_band: str
    market_prediction_available: bool = True


class RiskSummaryResponse(BaseModel):
    total_decisions: int
    avg_overall_risk: float
    risk_band_distribution: RiskBandDistribution
    pricing_in_distribution: dict[str, int] = Field(default_factory=dict)
    risk_by_sector: list[SectorRiskSummary] = Field(default_factory=list)
    risk_by_event_window: list[EventWindowRiskSummary] = Field(default_factory=list)
    risk_by_bill: list[BillRiskSummary] = Field(default_factory=list)
    risk_by_company: list[CompanyRiskSummary] = Field(default_factory=list)
    thresholds: dict[str, str] = Field(default_factory=lambda: {
        "VERY_LOW": "< 0.20",
        "LOW": "0.20 - 0.40",
        "MODERATE": "0.40 - 0.60",
        "HIGH": "0.60 - 0.80",
        "VERY_HIGH": ">= 0.80"
    })
    disclaimer: str = "This is a model-derived risk indicator, not a recommendation."


class PortfolioRiskRequest(BaseModel):
    company_isins: list[str] = Field(default_factory=list)
    watchlist_id: Optional[str] = None


class PortfolioCompanyRiskItem(BaseModel):
    company_isin: str
    company_name: str
    company_symbol: str
    sector: str
    universe_type: str
    is_modeled: bool
    record_count: int
    avg_risk_score: Optional[float] = None
    dominant_risk_band: Optional[str] = None


class PortfolioRiskResponse(BaseModel):
    selected_companies_count: int
    modeled_companies_count: int
    unmodeled_companies_count: int
    total_exposure_records: int
    avg_portfolio_risk_score: Optional[float] = None
    portfolio_risk_band: Optional[str] = None
    has_sufficient_data: bool
    data_status: str  # "SUFFICIENT_DATA" | "INSUFFICIENT_DATA"
    risk_band_distribution: RiskBandDistribution
    sector_breakdown: list[SectorRiskSummary] = Field(default_factory=list)
    jurisdiction_breakdown: dict[str, int] = Field(default_factory=lambda: {"central": 0, "state": 0})
    companies: list[PortfolioCompanyRiskItem] = Field(default_factory=list)
    message: str = ""
    disclaimer: str = "This is a model-derived portfolio risk indicator, not investment advice or portfolio VaR."


# ---------------------------------------------------------------------------
# Anticipation Analytics Schemas (Task 8.14.7)
# ---------------------------------------------------------------------------


class AnticipationItem(BaseModel):
    bill_id: str
    bill_title: Optional[str] = None
    company_isin: str
    company_name: Optional[str] = None
    company_symbol: Optional[str] = None
    sector: Optional[str] = None
    official_introduction_date: str
    anticipation_score: float
    classification: str  # NO_EVIDENCE, WEAK_EVIDENCE, MODERATE_EVIDENCE, STRONG_EVIDENCE
    anticipation_flag: bool
    confidence: str
    market_signal_score: float
    information_signal_score: float
    evidence_count: int
    media_data_available: bool
    decision_reason: str
    detected_signals: list[str] = Field(default_factory=list)
    calculation_timestamp: str = ""


class AnticipationSectorSummary(BaseModel):
    sector: str
    pair_count: int
    avg_anticipation_score: float
    flagged_count: int
    classification_counts: dict[str, int] = Field(default_factory=dict)


class PreEventWindowSummary(BaseModel):
    window: str  # e.g. "[-30,-21]", "[-20,-11]", etc.
    mean_mar: float
    mean_car: float
    significant_pairs_count: int
    observation_count: int


class FlaggedAnticipationPair(BaseModel):
    bill_id: str
    bill_title: str
    company_isin: str
    company_name: str
    company_symbol: str
    sector: str
    anticipation_score: float
    classification: str
    detected_signals: list[str] = Field(default_factory=list)


class AnticipationSummaryResponse(BaseModel):
    total_pairs: int = 940
    flagged_pairs_count: int
    avg_anticipation_score: float
    avg_market_signal: float
    avg_information_signal: float
    classification_distribution: dict[str, int] = Field(default_factory=dict)
    sector_distribution: list[AnticipationSectorSummary] = Field(default_factory=list)
    window_stats_distribution: list[PreEventWindowSummary] = Field(default_factory=list)
    top_flagged_pairs: list[FlaggedAnticipationPair] = Field(default_factory=list)
    disclaimer: str = (
        "Pre-event diagnostics measure aggregate public information diffusion only. "
        "They do not allege or imply insider trading or illicit market conduct under securities law."
    )



# ---------------------------------------------------------------------------
# State Economic Intelligence Schemas (State Level 2)
# ---------------------------------------------------------------------------


class StateCoverageItem(BaseModel):
    state: str
    bills_count: int = 0
    status: str = "PLANNED"  # "IMPLEMENTED" or "PLANNED"
    authority: Optional[str] = "Official Portal"
    legislative_source: Optional[str] = None
    feasibility: Optional[str] = None
    notes: Optional[str] = None


class StateCoverageResponse(BaseModel):
    total_states_in_union: int = 28
    implemented_count: int = 4
    planned_count: int = 24
    implemented_states_list: list[str] = Field(
        default_factory=lambda: ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"]
    )
    implemented_states: list[StateCoverageItem] = Field(default_factory=list)
    planned_states: list[StateCoverageItem] = Field(default_factory=list)
    semantics_clarification: str = (
        "Strictly 4 states (Andhra Pradesh, Karnataka, Kerala, Telangana) have implemented legislative corpora "
        "(44 bills total) and active corporate exposure intelligence. The remaining 24 states in the coverage "
        "registry are planned roadmap states with 0 ingested bills. State stock price predictions remain strictly 0."
    )


class StateDetailResponse(BaseModel):
    state: str
    status: str
    bills_count: int
    legislative_source: str
    authority: str
    assembly_chamber: str
    statutory_guarantee: str = "STATE_STOCK_PREDICTIONS_STRICTLY_ZERO"
    economic_sectors_active: list[str] = Field(default_factory=list)
    total_corporate_exposures: int = 0


# ---------------------------------------------------------------------------
# Search Schemas
# ---------------------------------------------------------------------------


class SearchResultItem(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    category: str = Field(..., description="bills_central | bills_state | companies_quant | companies_intel | sectors | states")
    jurisdiction: Optional[str] = None
    state: Optional[str] = None
    relevance_score: int = 0
    url: str


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    items: list[SearchResultItem]
    categories: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Coverage Schemas
# ---------------------------------------------------------------------------


class CentralCoverageStats(BaseModel):
    production_bills: int = 20
    total_bills_in_repo: int = 22
    quantitative_companies: int = 47
    bill_company_pairs: int = 940
    predictions_count: int = 4700
    decisions_count: int = 4700
    anticipation_scores_count: int = 940
    stakeholder_reports_count: int = 14100
    event_windows_count: int = 5


class StateCoverageStats(BaseModel):
    implemented_states_count: int = 4
    planned_states_count: int = 24
    implemented_states_list: list[str] = Field(
        default_factory=lambda: ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"]
    )
    state_bills_count: int = 44
    state_official_pdfs_count: int = 44
    state_knowledge_records_count: int = 44
    state_corporate_exposures_count: int = 86
    state_stock_predictions_count: int = 0


class CompanyCoverageStats(BaseModel):
    total_companies: int = 70
    quantitative_companies: int = 47
    intelligence_companies: int = 20
    reference_companies: int = 3


class UnifiedCoverageStats(BaseModel):
    total_legislative_records: int = 66
    total_corporate_exposures: int = 104


class CoverageReportResponse(BaseModel):
    central: CentralCoverageStats
    state: StateCoverageStats
    company: CompanyCoverageStats
    unified: UnifiedCoverageStats


# ---------------------------------------------------------------------------
# Monitoring Schemas
# ---------------------------------------------------------------------------


class MonitoringStatusResponse(BaseModel):
    system_status: str
    total_sources: int
    enabled_sources: int
    last_run_id: Optional[str] = None
    last_run_timestamp: Optional[str] = None
    sources_summary: list[dict[str, Any]] = Field(default_factory=list)


class MonitoringRunResponse(BaseModel):
    run_id: str
    trigger: str
    start_time: str
    started_at: Optional[str] = None
    end_time: Optional[str] = None
    completed_at: Optional[str] = None
    status: str
    sources_checked: int
    sources_succeeded: int
    sources_failed: int
    changes_detected: int
    error_summary: Optional[str] = None


class MonitoringEventResponse(BaseModel):
    event_id: str
    event_type: str
    bill_id: str
    bill_title: str
    jurisdiction: str
    state: Optional[str] = None
    detected_at: str
    description: str
    severity: str


class MonitoringCheckResponse(BaseModel):
    run_id: str
    status: str
    trigger: str
    sources_checked: int
    sources_succeeded: int
    sources_failed: int
    changes_detected: int


# ---------------------------------------------------------------------------
# Watchlists Schemas
# ---------------------------------------------------------------------------


class WatchlistItemCreateRequest(BaseModel):
    entity_type: str = Field(..., description="company | bill | state | sector | industry | jurisdiction")
    entity_id: str = Field(..., description="Canonical ID or name of entity")
    display_name: str = Field("", description="Optional custom display label")
    notes: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    item_id: str
    watchlist_id: str
    entity_type: str
    entity_id: str
    canonical_name: str
    state: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: str


class AlertRuleCreateRequest(BaseModel):
    alert_type: str = Field("BILL_STATUS_CHANGE", description="AlertType enum")
    minimum_severity: str = Field("LOW", description="INFO | LOW | MEDIUM | HIGH | CRITICAL")
    enabled: bool = True


class AlertRuleUpdateRequest(BaseModel):
    alert_type: Optional[str] = None
    minimum_severity: Optional[str] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    alert_rule_id: str
    user_id: str
    tenant_id: str
    watchlist_id: Optional[str] = None
    alert_type: str
    minimum_severity: str
    enabled: bool
    created_at: str


class WatchlistCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: bool = False


class WatchlistUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WatchlistResponse(BaseModel):
    watchlist_id: str
    user_id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    is_default: bool
    is_active: bool
    created_at: str
    updated_at: str
    items_count: int = 0
    items: list[WatchlistItemResponse] = Field(default_factory=list)
    rules: list[AlertRuleResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Alerts Schemas
# ---------------------------------------------------------------------------


class AlertEventResponse(BaseModel):
    alert_event_id: str
    user_id: str
    tenant_id: str
    watchlist_id: Optional[str] = None
    alert_type: str
    severity: str
    title: str
    summary: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    created_at: str
    is_read: bool
    is_archived: bool
    deep_link: Optional[str] = None


class UnreadCountResponse(BaseModel):
    unread_count: int
    user_id: str
    tenant_id: str


# ---------------------------------------------------------------------------
# Notifications Schemas
# ---------------------------------------------------------------------------


class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    tenant_id: str
    notification_type: str
    severity: str
    title: str
    message: str
    status: str
    is_read: bool
    is_archived: bool
    created_at: str
    delivered_at: Optional[str] = None
    action_url: Optional[str] = None


class NotificationSummaryResponse(BaseModel):
    tenant_id: str
    user_id: str
    total_active: int
    unread_count: int
    archived_count: int
    alert_count: int
    digest_count: int
    latest_notification_at: Optional[str] = None
    counts_by_type: dict[str, int] = Field(default_factory=dict)
    counts_by_severity: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# AI Copilot Schemas
# ---------------------------------------------------------------------------


class AIAskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Grounded query for AI analyst")
    context_type: Optional[str] = Field("bill", description="bill | company | comparison | watchlist | workspace | monitoring")
    context_id: Optional[str] = Field(None, description="Target bill_id, company_id, or comma-separated bill_ids")
    watchlist_id: Optional[str] = Field(None, description="Optional target watchlist_id for watchlist-scoped queries")
    persona: str = Field("GENERAL_PUBLIC", description="GENERAL_PUBLIC | INVESTOR | POLICY_RESEARCHER")


class AIAskResponse(BaseModel):
    content: str
    context_type: str
    context_id: str
    persona: str
    operation: str
    success: bool
    is_cached: bool = False
    disclaimer: str
    provenance_sources: list[str] = Field(default_factory=list)
    answer: Optional[str] = None
    context_sources: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Industry & Sector Intelligence Schemas (Task 8.14.8)
# ---------------------------------------------------------------------------


class IndustrySummaryResponse(BaseModel):
    industry_id: str
    name: str
    sector: str
    coverage_level: int = Field(..., description="1: Quantitative Modelled, 2: Corporate Intelligence, 3: Legislative/Economic")
    related_bills_count: int = 0
    exposed_companies_count: int = 0
    central_exposures_count: int = 0
    state_exposures_count: int = 0
    quantitative_companies_count: int = 0
    intelligence_companies_count: int = 0
    market_analysis_available: bool = False
    economic_mechanisms: list[str] = Field(default_factory=list)
    latest_legislative_activity: Optional[str] = None
    sub_industries: list[str] = Field(default_factory=list)


class IndustryBillItemResponse(BaseModel):
    bill_id: str
    bill_title: str
    jurisdiction: str
    state: Optional[str] = None
    policy_domain: str = ""
    legislative_status: str = "introduced"
    exposure_strength: str = "MEDIUM"
    economic_mechanism: str = "compliance"
    provisions_summary: str = ""
    exposed_company_ids: list[str] = Field(default_factory=list)
    exposed_company_names: list[str] = Field(default_factory=list)
    provenance_sources: list[str] = Field(default_factory=list)


class IndustryCompanyItemResponse(BaseModel):
    company_id: str
    company_name: str
    ticker_nse: Optional[str] = None
    ticker_bse: Optional[str] = None
    sector: str
    industry: str
    universe_type: str
    entity_type: str
    ownership_type: str
    listing_status: str
    is_quant_eligible: bool
    market_prediction_available: bool
    exposure_count: int = 0
    exposure_strength: str = "NONE"
    direct_indirect: str = "NONE"
    primary_mechanism: str = "Unspecified"
    market_relevance: str = "NONE"
    evidence_reference: str = ""


class IndustryRiskSummaryResponse(BaseModel):
    epistemic_badge: str = "DERIVED"
    explanation: str
    risk_band_distribution: dict[str, int] = Field(default_factory=dict)
    high_risk_count: int = 0


class IndustryAnticipationSummaryResponse(BaseModel):
    epistemic_badge: str = "DERIVED"
    verbatim_disclaimer: str
    diffusion_tier_distribution: dict[str, int] = Field(default_factory=dict)
    flagged_pairs_count: int = 0


class IndustryDossierResponse(BaseModel):
    industry_id: str
    name: str
    sector: str
    coverage_level: int
    description: str
    total_bills_count: int
    central_bills_count: int
    state_bills_count: int
    total_companies_count: int
    quantitative_companies_count: int
    intelligence_companies_count: int
    reference_companies_count: int
    central_exposures_count: int
    state_exposures_count: int
    market_analysis_available: bool
    dominant_mechanism: str
    facts: list[str] = Field(default_factory=list)
    derived: list[str] = Field(default_factory=list)
    interpretations: list[str] = Field(default_factory=list)
    predictions: list[str] = Field(default_factory=list)
    central_bills: list[IndustryBillItemResponse] = Field(default_factory=list)
    state_bills: list[IndustryBillItemResponse] = Field(default_factory=list)
    quantitative_companies: list[IndustryCompanyItemResponse] = Field(default_factory=list)
    intelligence_companies: list[IndustryCompanyItemResponse] = Field(default_factory=list)
    reference_companies: list[IndustryCompanyItemResponse] = Field(default_factory=list)
    transmission_chains: list[list[dict[str, Any]]] = Field(default_factory=list)
    active_mechanisms: list[str] = Field(default_factory=list)
    market_intelligence: dict[str, Any] = Field(default_factory=dict)
    state_intelligence: dict[str, Any] = Field(default_factory=dict)
    risk_summary: IndustryRiskSummaryResponse
    anticipation_summary: IndustryAnticipationSummaryResponse
    related_industries: list[dict[str, Any]] = Field(default_factory=list)
    provenance_sources: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Legislative Monitoring & Discovery Center Schemas (Task 8.14.9)
# ---------------------------------------------------------------------------


class MonitoringSourceItem(BaseModel):
    """Single monitoring source entry from the source registry."""
    source_id: str
    source_name: str
    jurisdiction: str = Field(..., description="central | state")
    state: Optional[str] = None
    source_type: str = Field(..., description="Adapter/scraper type")
    source_url: str
    enabled: bool
    status: str = Field(..., description="IMPLEMENTED | NOT_IMPLEMENTED | PLANNED | ERROR | DISABLED")
    polling_interval_hours: int
    priority: int
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error_at: Optional[str] = None
    last_error: Optional[str] = None
    notes: Optional[str] = None


class MonitoringSourceDetailResponse(BaseModel):
    """Expanded detail view for a single monitoring source."""
    source_id: str
    source_name: str
    jurisdiction: str
    state: Optional[str] = None
    source_type: str
    source_url: str
    enabled: bool
    status: str
    polling_interval_hours: int
    priority: int
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error_at: Optional[str] = None
    last_error: Optional[str] = None
    notes: Optional[str] = None
    recent_run_results: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    source: Optional[MonitoringSourceItem] = None
    operational_status: Optional[str] = None
    uptime_ratio: Optional[float] = None
    recent_runs: Optional[list[dict[str, Any]]] = None
    provenance_requirements: Optional[list[str]] = None


class SchedulerStatusResponse(BaseModel):
    """Scheduler observability — read-only telemetry."""
    enabled: bool
    scheduled_running: bool
    run_in_progress: bool
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    last_result_status: Optional[str] = None
    config: dict[str, Any] = Field(default_factory=dict)


class MonitoringOverviewResponse(BaseModel):
    """Combined monitoring telemetry for the Overview panel."""
    # System / Task 8.18 fields
    system_status: str = "OPERATIONAL"
    total_sources: int
    enabled_sources: int
    central_sources: int
    state_sources: int
    implemented_states: list[str] = Field(default_factory=list)
    total_bills_monitored: int = 0
    central_bills_monitored: int = 0
    state_bills_monitored: int = 0
    last_run_id: Optional[str] = None
    last_run_timestamp: Optional[str] = None
    total_events_detected: int = 0
    sources_summary: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: Optional[str] = None

    # Task 8.17 / earlier fields
    implemented_sources: int = 0
    planned_sources: int = 0
    total_runs: int = 0
    last_run_status: Optional[str] = None
    last_run_at: Optional[str] = None
    last_run_new_bills: int = 0
    last_run_changed_bills: int = 0
    last_run_document_changes: int = 0
    last_run_errors: int = 0
    total_change_events: int = 0
    scheduler: Optional[SchedulerStatusResponse] = None
    sources_healthy: int = 0
    sources_with_errors: int = 0
    sources_never_checked: int = 0



class ChangeEventDetailResponse(BaseModel):
    """Detailed change event with before/after provenance."""
    event_id: str
    bill_id: str
    bill_title: str
    jurisdiction: str
    state: Optional[str] = None
    source_id: str
    event_type: str
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    detected_at: str
    source_reference: Optional[str] = None
    confidence: float = 1.0
    error_message: Optional[str] = None
    # Epistemic classification
    epistemic_status: str = Field("OBSERVED", description="OBSERVED | DERIVED | INTERPRETATION")
    # Provenance
    provenance: dict[str, Any] = Field(default_factory=dict)
    # Bill version context if available
    previous_version_available: bool = False
    current_version_available: bool = False


class BillVersionItem(BaseModel):
    """A single bill version snapshot."""
    version: str
    captured_at: str
    source_id: str
    event_type: Optional[str] = None
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    jurisdiction: Optional[str] = None
    state: Optional[str] = None


class BillVersionHistoryResponse(BaseModel):
    """Bill version history from the monitoring repository."""
    bill_id: str
    versions_count: int = 0
    total_versions: int = 0
    latest_version: Optional[Any] = None
    versions: list[BillVersionItem] = Field(default_factory=list)


# Fixed MonitoringRunResponse — uses started_at/completed_at from MonitoringRun.to_dict()
class MonitoringRunDetailResponse(BaseModel):
    """Full monitoring run record with per-source results."""
    run_id: str
    trigger: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str
    sources_checked: int
    sources_succeeded: int
    sources_failed: int
    new_bills: int = 0
    changed_bills: int = 0
    document_changes: int = 0
    errors: int = 0
    source_results: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Task 8.15 — Personalized Workspace, Alert & Decision Workspace Schemas
# ---------------------------------------------------------------------------


class WorkspaceSummaryResponse(BaseModel):
    """Attention summary counts for authenticated user."""
    user_id: str
    tenant_id: str
    unread_notifications: int
    active_alerts: int
    total_alerts: int
    watched_bills: int
    watched_companies: int
    watched_industries: int
    watched_sectors: int
    watched_states: int
    watched_jurisdictions: int
    total_watchlists: int
    recent_changes_count: int
    last_activity_at: Optional[str] = None


class WorkspaceActivityItem(BaseModel):
    """Activity event stream item tailored to watched entities."""
    activity_id: str
    activity_type: str
    epistemic_status: str = Field("OBSERVED", description="OBSERVED | DERIVED | PREDICTION")
    title: str
    summary: str
    entity_type: str
    entity_id: str
    entity_name: str
    jurisdiction: str = "central"
    state: Optional[str] = None
    severity: str = "LOW"
    timestamp: str
    deep_link: str
    provenance: dict[str, Any] = Field(default_factory=dict)


class WorkspaceActivityResponse(BaseModel):
    """Recent activity feed for user workspace."""
    items: list[WorkspaceActivityItem] = Field(default_factory=list)
    total: int = 0


class WorkspaceEntityCard(BaseModel):
    """A single watched entity card categorized in workspace."""
    entity_type: str
    entity_id: str
    entity_name: str
    jurisdiction: str = "central"
    state: Optional[str] = None
    watchlist_id: str
    watchlist_name: str
    notes: Optional[str] = None
    latest_activity: Optional[str] = None
    last_activity_at: Optional[str] = None
    alert_count: int = 0
    deep_link: str
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class WorkspaceGroupedActivityResponse(BaseModel):
    """Watched entities grouped by entity type."""
    bills: list[WorkspaceEntityCard] = Field(default_factory=list)
    companies: list[WorkspaceEntityCard] = Field(default_factory=list)
    industries: list[WorkspaceEntityCard] = Field(default_factory=list)
    jurisdictions: list[WorkspaceEntityCard] = Field(default_factory=list)
    total_watched: int = 0


class WorkspaceAnalyticsItem(BaseModel):
    """Risk, anticipation, or prediction snapshot for a watched entity."""
    entity_type: str
    entity_id: str
    entity_name: str
    epistemic_label: str  # "[DERIVED]" | "[PREDICTION]"
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    anticipation_tier: Optional[str] = None
    anticipation_score: Optional[float] = None
    prediction_record: Optional[dict[str, Any]] = None
    is_state_firewall_active: bool = False
    is_intelligence_firewall_active: bool = False
    firewall_note: Optional[str] = None
    updated_at: Optional[str] = None


class WorkspaceAnalyticsSnapshotResponse(BaseModel):
    """Aggregated analytics snapshot for watched entities."""
    items: list[WorkspaceAnalyticsItem] = Field(default_factory=list)
    total_items: int = 0
    epistemic_disclaimer: str = (
        "Analytical decision support only. Risk bands and anticipation metrics are [DERIVED]. "
        "Central model outputs are [PREDICTION]. State stock predictions remain strictly 0. "
        "Not investment, trading, or political advice."
    )


class AlertPreferenceResponse(BaseModel):
    """User alert preferences configuration."""
    user_id: str
    tenant_id: str
    enabled: bool
    minimum_severity: str
    allowed_alert_types: list[str] = Field(default_factory=list)
    allowed_channels: list[str] = Field(default_factory=list)
    digest_frequency: str
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AlertPreferenceUpdateRequest(BaseModel):
    """User alert preferences mutation request."""
    enabled: Optional[bool] = None
    minimum_severity: Optional[str] = None
    allowed_alert_types: Optional[list[str]] = None
    allowed_channels: Optional[list[str]] = None
    digest_frequency: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class AlertGroupDigestResponse(BaseModel):
    """Grouped notification digest item."""
    group_id: str
    user_id: str
    tenant_id: str
    group_type: str
    title: str
    summary: str
    severity: str
    event_count: int
    created_at: str
    alert_event_ids: list[str] = Field(default_factory=list)
    sample_events: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Freshness Telemetry Schemas
# ---------------------------------------------------------------------------


class FreshnessItem(BaseModel):
    dataset: str
    status: str  # LIVE | RECENT | STALE | NOT_AVAILABLE
    record_count: int
    authority: str
    jurisdiction: str
    cadence: str
    last_successful_update: Optional[str] = None
    last_checked_at: Optional[str] = None
    provenance_summary: str


class FreshnessResponse(BaseModel):
    overall_status: str
    as_of: str
    timestamp: Optional[str] = None
    total_datasets: int
    live_count: int
    recent_count: int
    stale_count: int
    not_available_count: int
    datasets: list[FreshnessItem]



