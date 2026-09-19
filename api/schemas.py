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


class BillDetailResponse(BaseModel):
    bill: BillSummaryItem
    provisions: list[str] = Field(default_factory=list)
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
    end_time: Optional[str] = None
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
    context_type: str = Field("bill", description="bill | company | comparison")
    context_id: str = Field(..., description="Target bill_id, company_id, or comma-separated bill_ids")
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
