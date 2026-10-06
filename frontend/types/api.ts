/**
 * types/api.ts
 * ============
 * TypeScript interfaces mirroring all FastAPI Pydantic response schemas.
 *
 * DO NOT add computed/derived fields here — these types represent
 * server responses only. All business logic lives in the FastAPI backend.
 */

// ---------------------------------------------------------------------------
// Generic
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface HealthResponse {
  status: string;
  api_version: string;
  environment: string;
  timestamp: string;
}

export interface SuccessStatusResponse {
  success: boolean;
  message?: string;
}

// ---------------------------------------------------------------------------
// Legislative Bills
// ---------------------------------------------------------------------------

export interface BillSummaryItem {
  bill_id: string;
  jurisdiction: string; // "central" | "state"
  state?: string | null;
  title: string;
  short_title: string;
  bill_number?: string | null;
  legislature: string;
  house: string;
  year?: number | null;
  introduction_date?: string | null;
  assent_date?: string | null;
  status: string;
  policy_domain?: string | null;
  economic_sectors: string[];
  secondary_sectors: string[];
  stakeholders: string[];
  summary: string;
  company_exposure_count: number;
  listed_company_exposure_count: number;
  market_relevance: string; // "HIGH" | "MEDIUM" | "LOW" | "NONE"
  modeling_eligibility: string; // "ELIGIBLE" | "NOT_ELIGIBLE"
  data_sufficiency: string; // "COMPLETE" | "INSUFFICIENT"
  source_url?: string | null;
  pdf_url?: string | null;
  data_quality: string; // "VERIFIED"
}

export interface CorporateExposureEvidence {
  claim: string;
  reference: string;
  url?: string | null;
  statutory_section?: string | null;
}

export interface BillCompanyExposure {
  bill_id: string;
  bill_title: string;
  company_id: string;
  company_name: string;
  bill_number?: string | null;
  jurisdiction: string;
  state?: string | null;
  bill_status: string;
  sector: string;
  sub_sector: string;
  business_activity: string;
  exposure_type: string;
  exposure_direction: string;
  exposure_strength: string; // "HIGH" | "MEDIUM" | "LOW"
  direct_indirect: string; // "DIRECT" | "INDIRECT"
  geographic_scope: string;
  mechanism: string;
  market_relevance: string;
  confidence: string;
  has_evidence: boolean;
  evidence: CorporateExposureEvidence[];
  source_urls: string[];
}

export interface BillKnowledge {
  amended_acts: string[];
  regulatory_authority?: string | null;
  financial_terms?: string | null;
  penalties_or_enforcement?: string | null;
  objective?: string | null;
  key_provisions: string[];
}

export interface BillDetailResponse {
  bill: BillSummaryItem;
  provisions: string[];
  knowledge?: BillKnowledge | null;
  provenance: Record<string, string>;
  prediction_available: boolean;
  related_bills: BillSummaryItem[];
}

export interface BillPredictionStatusResponse {
  available: boolean;
  has_predictions: boolean;
  bill_id: string;
  reason?: string | null;
  firewall_status?: string | null;
  message?: string | null;
  jurisdiction: string;
  predictions: Record<string, unknown>[];
  items: Record<string, unknown>[];
  total: number;
}

// ---------------------------------------------------------------------------
// Task 8.27 — Legislative Intelligence Enrichment & Bill Dossier 2.0
// ---------------------------------------------------------------------------

export interface TimelineEventItem {
  event_id: string;
  stage: string;
  stage_label: string;
  date?: string | null;
  source_authority: string;
  description: string;
  evidence_type: string;
  document_url?: string | null;
  chamber?: string | null;
  verified: boolean;
}

export interface DocumentChangeDetail {
  document_url: string;
  previous_hash?: string | null;
  new_hash?: string | null;
  detected_at: string;
  change_type: string;
  file_size_bytes?: number | null;
  notes: string;
}

export interface LegislativeChangeDetail {
  field_name: string;
  old_value?: string | null;
  new_value?: string | null;
  detected_at: string;
  source_authority: string;
  change_type: string;
  description: string;
}

export interface BillChangeSummary {
  has_changes: boolean;
  total_changes: number;
  last_change_detected_at?: string | null;
  document_changes: DocumentChangeDetail[];
  legislative_changes: LegislativeChangeDetail[];
  summary_text: string;
  separation_notice: string;
}

export interface PlainLanguageExplanation {
  what_is_this_bill: string;
  what_does_it_change: string;
  who_could_be_affected: string;
  why_could_it_matter_economically: string;
  what_is_still_unknown: string;
  grounded_sources: string[];
  epistemic_level: string;
  epistemic_notice: string;
}

export interface StakeholderPersonaView {
  persona: string;
  persona_title: string;
  icon: string;
  fact: string;
  interpretation: string;
  prediction: string;
  caveats: string;
}

export interface SectorExposureItem {
  sector: string;
  industries: string[];
  relevance: string;
  business_activities: string[];
  exposure_type: string;
  transmission_channel?: string | null;
}

export interface LinkedCompanyExposureItem {
  company_id: string;
  company_name: string;
  isin?: string | null;
  ticker_nse?: string | null;
  sector: string;
  industry: string;
  linkage_reasons: string[];
  exposure_type: string;
  exposure_direction: string;
  exposure_strength: string;
  mechanism: string;
  evidence_summary: string;
  source_urls: string[];
  is_quant_eligible: boolean;
  has_market_predictions: boolean;
}

export interface BillDocumentItem {
  document_id: string;
  title: string;
  url?: string | null;
  hash_sha256?: string | null;
  format: string;
  retrieved_at?: string | null;
  retrieval_status: string;
  provenance: string;
  page_count?: number | null;
  source_authority: string;
}

export interface EnrichedBillDossier {
  identity: {
    bill_id: string;
    title: string;
    short_title: string;
    bill_number?: string | null;
    jurisdiction: string;
    state?: string | null;
    house: string;
    legislature: string;
    ministry?: string | null;
    bill_type: string;
    year?: number | null;
  };
  status: {
    current_status: string;
    current_legislative_stage: string;
    introduction_date?: string | null;
    passage_date?: string | null;
    assent_date?: string | null;
    latest_verified_update?: string | null;
    status_history: Record<string, unknown>[];
  };
  content: {
    executive_summary: string;
    plain_language: PlainLanguageExplanation;
    key_provisions: string[];
    obligations: string[];
    affected_activities: string[];
    implementation_info?: string | null;
  };
  impact_context: {
    affected_sectors: string[];
    affected_industries: string[];
    economic_themes: string[];
    potentially_exposed_business_activities: string[];
    company_exposure_count: number;
    listed_company_exposure_count: number;
    market_relevance: string;
  };
  provenance: {
    official_source: string;
    source_authority: string;
    source_url?: string | null;
    document_url?: string | null;
    document_hash?: string | null;
    discovered_at: string;
    verified_at?: string | null;
    last_updated_at: string;
    data_quality: string;
    provenance_map: Record<string, string>;
  };
  model_status: string;
  model_status_label: string;
  model_status_description: string;
  prediction_available: boolean;
  timeline: TimelineEventItem[];
  change_summary: BillChangeSummary;
  stakeholder_views: Record<string, StakeholderPersonaView>;
  sector_exposures: SectorExposureItem[];
  company_exposures: LinkedCompanyExposureItem[];
  documents: BillDocumentItem[];
  ai_explanation?: Record<string, unknown> | null;
}

export interface BillTimelineResponse {
  bill_id: string;
  total_events: number;
  events: TimelineEventItem[];
}

export interface BillChangesResponse {
  bill_id: string;
  changes: BillChangeSummary;
}

export interface PlainLanguageResponse {
  bill_id: string;
  plain_language: PlainLanguageExplanation;
}

export interface BillStakeholdersResponse {
  bill_id: string;
  stakeholder_views: Record<string, StakeholderPersonaView>;
}

export interface BillSectorExposureResponse {
  bill_id: string;
  sector_exposures: SectorExposureItem[];
}

export interface BillDocumentsResponse {
  bill_id: string;
  total_documents: number;
  documents: BillDocumentItem[];
}

export interface BillModelStatusResponse {
  bill_id: string;
  model_status: string;
  model_status_label: string;
  model_status_description: string;
  prediction_available: boolean;
  is_central: boolean;
  is_state: boolean;
  jurisdiction: string;
  state?: string | null;
  firewall_active: boolean;
}

// ---------------------------------------------------------------------------
// Corporate Intelligence
// ---------------------------------------------------------------------------

export interface CompanySummaryItem {
  company_id: string;
  company_name: string;
  ticker_nse?: string | null;
  ticker_bse?: string | null;
  isin: string;
  sector: string;
  industry: string;
  sub_industry?: string | null;
  entity_type: string;
  universe_type: string; // "quantitative" | "intelligence" | "both" | "reference"
  ownership_type: string;
  is_active: boolean;
  listing_status: string;
  hq_state?: string | null;
  watchlist_eligible: boolean;
  is_quant_eligible: boolean;
  market_prediction_available: boolean;
  documented_exposure_count: number;
}

export interface CompanyDetailResponse {
  company_id: string;
  company_name: string;
  legal_identity: string;
  aliases: string[];
  ticker_nse: string;
  ticker_bse: string;
  bse_code: string;
  isin: string;
  entity_type: string;
  universe_type: string;
  group_name?: string | null;
  ownership_type: string;
  is_active: boolean;
  listing_status: string;
  sector: string;
  industry: string;
  sub_industry: string;
  business_description: string;
  business_activities: string[];
  hq_state: string;
  hq_city: string;
  operating_states: string[];
  state_presences: Record<string, unknown>[];
  facilities: Record<string, unknown>[];
  data_sources: string[];
  data_quality_score?: number | null;
  data_quality_label: string;
  related_bills: BillCompanyExposure[];
  total_exposures: number;
  central_exposures_count: number;
  state_exposures_count: number;
  direct_exposures_count: number;
  indirect_exposures_count: number;
  exposure_types: string[];
  mechanisms: string[];
  affected_sectors: string[];
  watchlist_eligible: boolean;
  is_quant_eligible: boolean;
  market_prediction_available: boolean;
  quantitative_firewall_status: string;
}

export interface CompanyPredictionStatusResponse {
  available: boolean;
  has_predictions: boolean;
  company_id: string;
  reason?: string | null;
  firewall_status?: string | null;
  message?: string | null;
  universe_type: string;
  predictions: Record<string, unknown>[];
  items: Record<string, unknown>[];
  total: number;
}

export interface CompanyAnticipationScoreItem {
  bill_id: string;
  company_isin: string;
  company_symbol: string;
  official_introduction_date: string;
  market_signal_score: number;
  information_signal_score: number;
  anticipation_score: number;
  classification: string;
  anticipation_flag: boolean;
  confidence: string;
  evidence_count: number;
  media_data_available: boolean;
  decision_reason: string;
  window_stats?: Record<string, unknown>;
  detected_signals?: string[];
  calculation_timestamp?: string;
}

export interface CompanyAnticipationResponse {
  available: boolean;
  has_anticipation: boolean;
  company_id: string;
  reason?: string | null;
  firewall_status?: string | null;
  message?: string | null;
  scores: CompanyAnticipationScoreItem[];
  total: number;
}

export interface CompanyExposureExplanation {
  company_name: string;
  company_id: string;
  bill_id: string;
  bill_title: string;
  has_exposure: boolean;
  exposure_type: string;
  direct_indirect: string;
  exposure_strength: string;
  business_activity: string;
  geographic_relevance: string;
  economic_mechanism: string;
  evidence_claims: string[];
  evidence_references: string[];
  market_relevance: string;
  why_explanation: string;
  data_quality: string;
  provenance_sources: string[];
}

// ---------------------------------------------------------------------------
// Market Predictions (Central Level 1 only)
// ---------------------------------------------------------------------------

export interface PredictionItem {
  prediction_id: string;
  bill_id: string;
  company_isin: string;
  company_name?: string | null;
  company_symbol?: string | null;
  sector?: string | null;
  event_window: string;
  predicted_direction: string; // "POSITIVE" | "NEGATIVE" | "NEUTRAL"
  predicted_market_moving: boolean;
  market_moving_probability: number;
  predicted_impact_strength: string; // "HIGH" | "MEDIUM" | "LOW"
  predicted_confidence: string; // "HIGH" | "MEDIUM" | "LOW"
  confidence_score: number;
  model_version: string;
  created_at: string;
}

export interface HorizonComparisonItem {
  event_window: string;
  is_modeled: boolean;
  predicted_direction?: string | null;
  direction_probability?: Record<string, number>;
  predicted_market_moving?: boolean | null;
  market_moving_probability?: number | null;
  predicted_impact_strength?: string | null;
  predicted_confidence?: string | null;
  confidence_score?: number | null;
  impact_score?: number | null;
  risk_score?: number | null;
  risk_category?: string | null;
  pricing_in_risk?: string | null;
  note?: string | null;
}

export interface HorizonComparisonResponse {
  bill_id: string;
  bill_title: string;
  company_isin: string;
  company_name: string;
  company_symbol: string;
  modeled_windows: string[];
  comparisons: HorizonComparisonItem[];
  unmodeled_note: string;
}

// ---------------------------------------------------------------------------
// Risk Analytics Types (Task 8.14.7)
// ---------------------------------------------------------------------------

export interface RiskBandDistribution {
  VERY_LOW: number;
  LOW: number;
  MODERATE: number;
  HIGH: number;
  VERY_HIGH: number;
}

export interface SectorRiskSummary {
  sector: string;
  avg_risk_score: number;
  record_count: number;
  band_distribution: RiskBandDistribution;
}

export interface EventWindowRiskSummary {
  event_window: string;
  avg_risk_score: number;
  record_count: number;
  band_distribution: RiskBandDistribution;
}

export interface BillRiskSummary {
  bill_id: string;
  bill_title: string;
  jurisdiction: string;
  avg_risk_score: number;
  max_risk_score: number;
  high_risk_count: number;
  record_count: number;
  dominant_risk_band: string;
}

export interface CompanyRiskSummary {
  company_isin: string;
  company_name: string;
  company_symbol: string;
  sector: string;
  universe_type: string;
  avg_risk_score: number;
  max_risk_score: number;
  record_count: number;
  dominant_risk_band: string;
  market_prediction_available: boolean;
}

export interface RiskSummaryResponse {
  total_decisions: number;
  avg_overall_risk: number;
  risk_band_distribution: RiskBandDistribution;
  pricing_in_distribution: Record<string, number>;
  risk_by_sector: SectorRiskSummary[];
  risk_by_event_window: EventWindowRiskSummary[];
  risk_by_bill: BillRiskSummary[];
  risk_by_company: CompanyRiskSummary[];
  thresholds: Record<string, string>;
  disclaimer: string;
}

export interface PortfolioRiskRequest {
  company_isins?: string[];
  watchlist_id?: string | null;
}

export interface PortfolioCompanyRiskItem {
  company_isin: string;
  company_name: string;
  company_symbol: string;
  sector: string;
  universe_type: string;
  is_modeled: boolean;
  record_count: number;
  avg_risk_score?: number | null;
  dominant_risk_band?: string | null;
}

export interface PortfolioRiskResponse {
  selected_companies_count: number;
  modeled_companies_count: number;
  unmodeled_companies_count: number;
  total_exposure_records: number;
  avg_portfolio_risk_score?: number | null;
  portfolio_risk_band?: string | null;
  has_sufficient_data: boolean;
  data_status: "SUFFICIENT_DATA" | "INSUFFICIENT_DATA" | string;
  risk_band_distribution: RiskBandDistribution;
  sector_breakdown: SectorRiskSummary[];
  jurisdiction_breakdown: Record<string, number>;
  companies: PortfolioCompanyRiskItem[];
  message: string;
  disclaimer: string;
}

// ---------------------------------------------------------------------------
// Anticipation Analytics Types (Task 8.14.7)
// ---------------------------------------------------------------------------

export interface AnticipationItem {
  bill_id: string;
  bill_title?: string | null;
  company_isin: string;
  company_name?: string | null;
  company_symbol?: string | null;
  sector?: string | null;
  official_introduction_date: string;
  anticipation_score: number;
  classification: string;
  anticipation_flag: boolean;
  confidence: string;
  market_signal_score: number;
  information_signal_score: number;
  evidence_count: number;
  media_data_available: boolean;
  decision_reason: string;
  detected_signals: string[];
  calculation_timestamp?: string;
}

export interface AnticipationSectorSummary {
  sector: string;
  pair_count: number;
  avg_anticipation_score: number;
  flagged_count: number;
  classification_counts: Record<string, number>;
}

export interface PreEventWindowSummary {
  window: string;
  mean_mar: number;
  mean_car: number;
  significant_pairs_count: number;
  observation_count: number;
}

export interface FlaggedAnticipationPair {
  bill_id: string;
  bill_title: string;
  company_isin: string;
  company_name: string;
  company_symbol: string;
  sector: string;
  anticipation_score: number;
  classification: string;
  detected_signals: string[];
}

export interface AnticipationSummaryResponse {
  total_pairs: number;
  flagged_pairs_count: number;
  avg_anticipation_score: number;
  avg_market_signal: number;
  avg_information_signal: number;
  classification_distribution: Record<string, number>;
  sector_distribution: AnticipationSectorSummary[];
  window_stats_distribution: PreEventWindowSummary[];
  top_flagged_pairs: FlaggedAnticipationPair[];
  disclaimer: string;
}


export interface DecisionRecordResponse {
  decision_id: string;
  prediction_id: string;
  bill_id: string;
  company_isin: string;
  event_window: string;
  risk_category: string;
  pricing_in_risk: string;
  impact_category: string;
  impact_score: number;
  risk_score: number;
  decision_reason: string;
  investor_summary: string;
  business_summary: string;
  public_summary: string;
  created_at: string;
}

export interface AnticipationScoreResponse {
  bill_id: string;
  company_isin: string;
  anticipation_score: number;
  anticipation_tier: string;
  diffusion_index: number;
  pre_event_volume_ratio: number;
  pre_event_car: number;
  leakage_indicator: boolean;
  evidence_summary: string[];
}

export interface StakeholderReportResponse {
  report_id: string;
  bill_id: string;
  company_isin: string;
  event_window: string;
  stakeholder_type: string;
  executive_summary: string;
  impact_summary?: string | null;
  risk_summary?: string | null;
  anticipation_summary?: string | null;
  confidence_summary?: string | null;
  key_takeaways: string[];
  key_factors: string[];
  transmission_channels: string[];
  methodology_note?: string | null;
  disclaimer?: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// State Coverage
// ---------------------------------------------------------------------------

export interface StateCoverageItem {
  state: string;
  bills_count: number;
  status: string; // "IMPLEMENTED" | "PLANNED"
  authority?: string | null;
  legislative_source?: string | null;
  feasibility?: string | null;
  notes?: string | null;
}

export interface StateCoverageResponse {
  total_states_in_union: number;
  implemented_count: number;
  planned_count: number;
  implemented_states_list: string[];
  implemented_states: StateCoverageItem[];
  planned_states: StateCoverageItem[];
  semantics_clarification: string;
}

export interface StateDetailResponse {
  state: string;
  status: string;
  bills_count: number;
  legislative_source: string;
  authority: string;
  assembly_chamber: string;
  statutory_guarantee: string;
  economic_sectors_active: string[];
  total_corporate_exposures: number;
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export type SearchCategory =
  | "bills_central"
  | "bills_state"
  | "companies_quant"
  | "companies_intel"
  | "industries"
  | "sectors"
  | "states"
  | "monitoring";

export interface SearchResultItem {
  id: string;
  title: string;
  subtitle?: string | null;
  category: SearchCategory;
  jurisdiction?: string | null;
  state?: string | null;
  relevance_score: number;
  url: string;
  data_layer?: string | null;
  model_status?: string | null;
}

export interface SearchResponse {
  query: string;
  total_matches: number;
  items: SearchResultItem[];
  categories: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Coverage
// ---------------------------------------------------------------------------

export interface CentralCoverageStats {
  production_bills: number;
  total_bills_in_repo: number;
  quantitative_companies: number;
  bill_company_pairs: number;
  predictions_count: number;
  decisions_count: number;
  anticipation_scores_count: number;
  stakeholder_reports_count: number;
  event_windows_count: number;
}

export interface StateCoverageStats {
  implemented_states_count: number;
  planned_states_count: number;
  implemented_states_list: string[];
  state_bills_count: number;
  state_official_pdfs_count: number;
  state_knowledge_records_count: number;
  state_corporate_exposures_count: number;
  state_stock_predictions_count: number; // Always 0
}

export interface CompanyCoverageStats {
  total_companies: number;
  quantitative_companies: number;
  intelligence_companies: number;
  reference_companies: number;
}

export interface UnifiedCoverageStats {
  total_legislative_records: number;
  total_corporate_exposures: number;
}

export interface CoverageReportResponse {
  central: CentralCoverageStats;
  state: StateCoverageStats;
  company: CompanyCoverageStats;
  unified: UnifiedCoverageStats;
}

// ---------------------------------------------------------------------------
// Monitoring
// ---------------------------------------------------------------------------

export interface MonitoringStatusResponse {
  system_status: string;
  total_sources: number;
  enabled_sources: number;
  last_run_id?: string | null;
  last_run_timestamp?: string | null;
  sources_summary: Record<string, unknown>[];
}

export interface MonitoringRunResponse {
  run_id: string;
  trigger: string;
  start_time: string;
  end_time?: string | null;
  status: string;
  sources_checked: number;
  sources_succeeded: number;
  sources_failed: number;
  changes_detected: number;
  error_summary?: string | null;
}

/** Full run record with started_at/completed_at from Task 8.14.9 router */
export interface MonitoringRunDetail {
  run_id: string;
  trigger: string;
  started_at: string;
  completed_at?: string | null;
  duration_seconds?: number | null;
  status: string;
  sources_checked: number;
  sources_succeeded: number;
  sources_failed: number;
  new_bills: number;
  changed_bills: number;
  document_changes: number;
  errors: number;
  source_results: Record<string, unknown>[];
}

export interface MonitoringEventResponse {
  event_id: string;
  event_type: string;
  bill_id: string;
  bill_title: string;
  jurisdiction: string;
  state?: string | null;
  detected_at: string;
  description: string;
  severity: string;
}

export interface SchedulerStatus {
  enabled: boolean;
  scheduled_running: boolean;
  run_in_progress: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  last_result_status?: string | null;
  config: Record<string, unknown>;
}

export interface MonitoringSourceItem {
  source_id: string;
  source_name: string;
  jurisdiction: string; // "central" | "state"
  state?: string | null;
  source_type: string;
  source_url: string;
  enabled: boolean;
  status: string; // "IMPLEMENTED" | "NOT_IMPLEMENTED" | "PLANNED" | "ERROR" | "DISABLED"
  polling_interval_hours: number;
  priority: number;
  last_checked_at?: string | null;
  last_success_at?: string | null;
  last_error_at?: string | null;
  last_error?: string | null;
  notes?: string | null;
}

export interface MonitoringSourceDetail extends MonitoringSourceItem {
  recent_run_results: Record<string, unknown>[];
  provenance: Record<string, unknown>;
}

export interface MonitoringOverview {
  total_sources: number;
  enabled_sources: number;
  central_sources: number;
  state_sources: number;
  implemented_sources: number;
  planned_sources: number;
  total_runs: number;
  last_run_id?: string | null;
  last_run_status?: string | null;
  last_run_at?: string | null;
  last_run_new_bills: number;
  last_run_changed_bills: number;
  last_run_document_changes: number;
  last_run_errors: number;
  total_change_events: number;
  scheduler: SchedulerStatus;
  sources_healthy: number;
  sources_with_errors: number;
  sources_never_checked: number;
}

export interface ChangeEventDetail {
  event_id: string;
  bill_id: string;
  bill_title: string;
  jurisdiction: string;
  state?: string | null;
  source_id: string;
  event_type: string;
  field_name?: string | null;
  old_value?: unknown;
  new_value?: unknown;
  detected_at: string;
  source_reference?: string | null;
  confidence: number;
  error_message?: string | null;
  epistemic_status: string; // "OBSERVED" | "DERIVED" | "INTERPRETATION"
  provenance: Record<string, unknown>;
  previous_version_available: boolean;
  current_version_available: boolean;
}

export interface BillVersionItem {
  version: string;
  captured_at: string;
  source_id: string;
  event_type?: string | null;
  field_name?: string | null;
  old_value?: unknown;
  new_value?: unknown;
  jurisdiction?: string | null;
  state?: string | null;
}

export interface BillVersionHistory {
  bill_id: string;
  versions_count: number;
  versions: BillVersionItem[];
}


// ---------------------------------------------------------------------------
// Watchlists
// ---------------------------------------------------------------------------

export interface WatchlistItemResponse {
  item_id: string;
  watchlist_id: string;
  entity_type: string;
  entity_id: string;
  canonical_name: string;
  display_name?: string;
  state?: string | null;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AlertRuleResponse {
  alert_rule_id: string;
  rule_id?: string;
  user_id: string;
  tenant_id: string;
  watchlist_id?: string | null;
  alert_type: string;
  minimum_severity: string;
  notification_channels?: string[];
  enabled: boolean;
  created_at: string;
}

export interface WatchlistResponse {
  watchlist_id: string;
  user_id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  items_count: number;
  items: WatchlistItemResponse[];
  rules: AlertRuleResponse[];
  alert_rules?: AlertRuleResponse[];
}

export interface WatchlistCreateRequest {
  name: string;
  description?: string;
  is_default?: boolean;
}

export interface WatchlistUpdateRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface WatchlistItemCreateRequest {
  entity_type: string;
  entity_id: string;
  display_name?: string;
  notes?: string;
}

export interface AlertRuleCreateRequest {
  alert_type?: string;
  minimum_severity?: string;
  notification_channels?: string[];
  enabled?: boolean;
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

export interface AlertEventResponse {
  alert_event_id: string;
  user_id: string;
  tenant_id: string;
  watchlist_id?: string | null;
  alert_type: string;
  severity: string; // "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  title: string;
  summary: string;
  entity_type?: string | null;
  entity_id?: string | null;
  created_at: string;
  is_read: boolean;
  is_archived: boolean;
  deep_link?: string | null;
}

export interface UnreadCountResponse {
  unread_count: number;
  user_id: string;
  tenant_id: string;
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export interface NotificationResponse {
  notification_id: string;
  user_id: string;
  tenant_id: string;
  notification_type: string;
  severity: string;
  title: string;
  message: string;
  status: string;
  is_read: boolean;
  is_archived: boolean;
  created_at: string;
  delivered_at?: string | null;
  action_url?: string | null;
}

export interface NotificationSummaryResponse {
  tenant_id: string;
  user_id: string;
  total_active: number;
  unread_count: number;
  archived_count: number;
  alert_count: number;
  digest_count: number;
  latest_notification_at?: string | null;
  counts_by_type: Record<string, number>;
  counts_by_severity: Record<string, number>;
}

// ---------------------------------------------------------------------------
// AI Analyst
// ---------------------------------------------------------------------------

export type AIPersona =
  | "GENERAL_PUBLIC"
  | "INVESTOR"
  | "CORPORATE_POLICY"
  | "POLICY_RESEARCHER";

export interface AIAskRequest {
  question: string;
  context_type: string; // "bill" | "company" | "comparison" | "workspace"
  context_id: string;
  persona?: string; // "GENERAL_PUBLIC" | "INVESTOR" | "CORPORATE_POLICY" | "POLICY_RESEARCHER"
}

export interface AIAskResponse {
  content: string;
  context_type: string;
  context_id: string;
  persona: string;
  operation: string;
  success: boolean;
  is_cached: boolean;
  disclaimer: string;
  provenance_sources: string[];
  model?: string;
  grounding_sources?: string[];
  question?: string;
}

// ---------------------------------------------------------------------------
// Industry & Sector Intelligence (Task 8.14.8)
// ---------------------------------------------------------------------------

export interface IndustrySummaryItem {
  industry_id: string;
  name: string;
  sector: string;
  coverage_level: number; // 1 | 2 | 3
  related_bills_count: number;
  exposed_companies_count: number;
  central_exposures_count: number;
  state_exposures_count: number;
  quantitative_companies_count: number;
  intelligence_companies_count: number;
  market_analysis_available: boolean;
  economic_mechanisms: string[];
  latest_legislative_activity?: string | null;
  sub_industries: string[];
}

export interface IndustryBillItem {
  bill_id: string;
  bill_title: string;
  jurisdiction: string;
  state?: string | null;
  policy_domain: string;
  legislative_status: string;
  exposure_strength: string;
  economic_mechanism: string;
  provisions_summary: string;
  exposed_company_ids: string[];
  exposed_company_names: string[];
  provenance_sources: string[];
}

export interface IndustryCompanyItem {
  company_id: string;
  company_name: string;
  ticker_nse?: string | null;
  ticker_bse?: string | null;
  sector: string;
  industry: string;
  universe_type: string;
  entity_type: string;
  ownership_type: string;
  listing_status: string;
  is_quant_eligible: boolean;
  market_prediction_available: boolean;
  exposure_count: number;
  exposure_strength: string;
  direct_indirect: string;
  primary_mechanism: string;
  market_relevance: string;
  evidence_reference: string;
}

export interface TransmissionChainNode {
  stage: "LEGISLATION" | "POLICY_CHANGE" | "ECONOMIC_MECHANISM" | "INDUSTRY" | "COMPANY_EXPOSURE" | "MARKET_ANALYSIS";
  title: string;
  description: string;
  badge?: string;
  status?: string;
}

export interface IndustryRiskSummary {
  epistemic_badge: string;
  explanation: string;
  risk_band_distribution: Record<string, number>;
  high_risk_count: number;
}

export interface IndustryAnticipationSummary {
  epistemic_badge: string;
  verbatim_disclaimer: string;
  diffusion_tier_distribution: Record<string, number>;
  flagged_pairs_count: number;
}

export interface RelatedIndustryItem {
  industry_id: string;
  name: string;
  sector: string;
  related_bills_count: number;
}

export interface ProvenanceSourceItem {
  source: string;
  source_type: string;
  verification_status: string;
  evidence_text: string;
  verified_at?: string;
}

export interface IndustryDossierResponse {
  industry_id: string;
  name: string;
  sector: string;
  coverage_level: number;
  description: string;
  total_bills_count: number;
  central_bills_count: number;
  state_bills_count: number;
  total_companies_count: number;
  quantitative_companies_count: number;
  intelligence_companies_count: number;
  reference_companies_count: number;
  central_exposures_count: number;
  state_exposures_count: number;
  market_analysis_available: boolean;
  dominant_mechanism: string;
  facts: string[];
  derived: string[];
  interpretations: string[];
  predictions: string[];
  central_bills: IndustryBillItem[];
  state_bills: IndustryBillItem[];
  quantitative_companies: IndustryCompanyItem[];
  intelligence_companies: IndustryCompanyItem[];
  reference_companies: IndustryCompanyItem[];
  transmission_chains: TransmissionChainNode[][];
  active_mechanisms: string[];
  market_intelligence: {
    modeled: boolean;
    notice: string;
    quantitative_companies_count: number;
    event_windows: string[];
    total_predictions?: number;
    positive_count?: number;
    negative_count?: number;
    neutral_count?: number;
    sample_predictions?: Array<{
      prediction_id: string;
      bill_id: string;
      company_isin: string;
      event_window: string;
      predicted_direction: string;
      predicted_confidence: string;
      impact_strength: string;
    }>;
  };
  state_intelligence: {
    state_bills_count: number;
    states_covered: string[];
    state_stock_predictions: number;
    firewall_statement: string;
    bills: IndustryBillItem[];
  };
  risk_summary: IndustryRiskSummary;
  anticipation_summary: IndustryAnticipationSummary;
  related_industries: RelatedIndustryItem[];
  provenance_sources: ProvenanceSourceItem[];
}

// ---------------------------------------------------------------------------
// Task 8.15 — Personalized Workspace & Decision Center Interfaces
// ---------------------------------------------------------------------------

export interface WorkspaceSummaryResponse {
  user_id: string;
  tenant_id: string;
  unread_notifications: number;
  active_alerts: number;
  total_alerts: number;
  watched_bills: number;
  watched_companies: number;
  watched_industries: number;
  watched_sectors: number;
  watched_states: number;
  watched_jurisdictions: number;
  total_watchlists: number;
  recent_changes_count: number;
  last_activity_at?: string | null;
}

export interface WorkspaceActivityItem {
  activity_id: string;
  activity_type: string;
  epistemic_status: "OBSERVED" | "DERIVED" | "PREDICTION" | string;
  title: string;
  summary: string;
  entity_type: string;
  entity_id: string;
  entity_name: string;
  jurisdiction: string;
  state?: string | null;
  severity: string;
  timestamp: string;
  deep_link: string;
  provenance: Record<string, any>;
}

export interface WorkspaceActivityResponse {
  items: WorkspaceActivityItem[];
  total: number;
}

export interface WorkspaceEntityCard {
  entity_type: string;
  entity_id: string;
  entity_name: string;
  jurisdiction: string;
  state?: string | null;
  watchlist_id: string;
  watchlist_name: string;
  notes?: string | null;
  latest_activity?: string | null;
  last_activity_at?: string | null;
  alert_count: number;
  deep_link: string;
  extra_metadata: Record<string, any>;
}

export interface WorkspaceGroupedActivityResponse {
  bills: WorkspaceEntityCard[];
  companies: WorkspaceEntityCard[];
  industries: WorkspaceEntityCard[];
  jurisdictions: WorkspaceEntityCard[];
  total_watched: number;
}

export interface WorkspaceAnalyticsItem {
  entity_type: string;
  entity_id: string;
  entity_name: string;
  epistemic_label: string; // "[DERIVED]" | "[PREDICTION]"
  risk_level?: string | null;
  risk_score?: number | null;
  anticipation_tier?: string | null;
  anticipation_score?: number | null;
  prediction_record?: Record<string, any> | null;
  is_state_firewall_active: boolean;
  is_intelligence_firewall_active: boolean;
  firewall_note?: string | null;
  updated_at?: string | null;
}

export interface WorkspaceAnalyticsSnapshotResponse {
  items: WorkspaceAnalyticsItem[];
  total_items: number;
  epistemic_disclaimer: string;
}

export interface AlertPreferenceResponse {
  user_id: string;
  tenant_id: string;
  enabled: boolean;
  minimum_severity: string;
  allowed_alert_types: string[];
  allowed_channels: string[];
  digest_frequency: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AlertPreferenceUpdateRequest {
  enabled?: boolean;
  minimum_severity?: string;
  allowed_alert_types?: string[];
  allowed_channels?: string[];
  digest_frequency?: string;
  quiet_hours_enabled?: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
}

export interface AlertGroupDigestResponse {
  group_id: string;
  user_id: string;
  tenant_id: string;
  group_type: string;
  title: string;
  summary: string;
  severity: string;
  event_count: number;
  created_at: string;
  alert_event_ids: string[];
  sample_events: Record<string, any>[];
}

// ---------------------------------------------------------------------------
// Type Aliases for Backward & Client Compatibility
// ---------------------------------------------------------------------------
export type BillDetailItem = BillDetailResponse;
export type CompanyDetailItem = CompanyDetailResponse;
export type IndustryDetailItem = IndustryDossierResponse;
export type PredictionDetailItem = PredictionItem;
export type PredictionSummaryItem = PredictionItem;
export type CoverageStatusResponse = CoverageReportResponse;

// ---------------------------------------------------------------------------
// Task 8.28 — Decision Intelligence & Personalized Impact Workspace Types
// ---------------------------------------------------------------------------

export type RelevanceTierType = "DIRECT" | "HIGH RELEVANCE" | "MODERATE RELEVANCE" | "INDIRECT" | "INFORMATIONAL";

export type PersonalizedModelStatusType = "MODELLED" | "KNOWLEDGE ONLY" | "NOT ELIGIBLE" | "PENDING REVIEW";

export interface PortfolioHoldingItem {
  holding_id: string;
  company_name: string;
  ticker?: string | null;
  isin?: string | null;
  quantity?: number | null;
  avg_purchase_price?: number | null;
  current_value?: number | null;
  sector?: string | null;
  industry?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserPortfolioItem {
  portfolio_id: string;
  user_id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  holdings: PortfolioHoldingItem[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RelevanceReasonItem {
  tier: string;
  primary_reason: string;
  evidence_statements: string[];
  signals: string[];
  matched_entity_id: string;
  matched_entity_name: string;
  matched_entity_type: string;
}

export interface AuthoritativePredictionSummaryItem {
  isin: string;
  company_name: string;
  bill_id: string;
  predicted_direction: string;
  predicted_confidence: string;
  probability?: number | null;
  event_window: string;
  all_horizons: Record<string, Record<string, any>>;
  risk_category?: string | null;
  anticipation_tier?: string | null;
  anticipation_score?: number | null;
  data_source: string;
}

export interface PersonalizedBillImpactItem {
  bill_id: string;
  bill_title: string;
  bill_number?: string | null;
  jurisdiction: string;
  state?: string | null;
  status: string;
  latest_verified_update?: string | null;
  relevance_tier: RelevanceTierType | string;
  relevance_reasons: RelevanceReasonItem[];
  primary_linkage_reason: string;
  affected_sectors: string[];
  affected_industries: string[];
  affected_companies: string[];
  model_status: PersonalizedModelStatusType | string;
  prediction_availability: boolean;
  source_provenance: string[];
  authoritative_prediction?: AuthoritativePredictionSummaryItem | null;
  epistemic_level: string;
}

export interface PortfolioLegislativeExposureResponse {
  total_holdings: number;
  exposed_holdings_count: number;
  total_relevant_bills: number;
  direct_bills_count: number;
  high_relevance_bills_count: number;
  moderate_relevance_bills_count: number;
  indirect_bills_count: number;
  modelled_central_bills_count: number;
  knowledge_only_bills_count: number;
  state_bills_count: number;
  sector_distribution: Record<string, number>;
  relevant_bills: PersonalizedBillImpactItem[];
  holdings_exposure_map: Record<string, string[]>;
  generated_at: string;
  disclaimer: string;
}

export interface PersonalizedChangeFeedItem {
  event_id: string;
  event_type: string;
  bill_id: string;
  bill_title: string;
  jurisdiction: string;
  state?: string | null;
  relevance_tier: string;
  relevance_reason: string;
  detected_at: string;
  model_status: string;
  deep_link: string;
  source_name: string;
  provenance_url?: string | null;
  epistemic_status: string;
}

export interface PersonalizedDashboardResponse {
  user_id: string;
  tenant_id: string;
  relevant_new_bills: PersonalizedBillImpactItem[];
  recent_bill_changes: PersonalizedChangeFeedItem[];
  relevant_state_legislation: PersonalizedBillImpactItem[];
  companies_exposed: Array<{
    company_name: string;
    exposed_bill_count: number;
    bill_ids: string[];
  }>;
  sectors_affected: Array<{
    sector: string;
    count: number;
  }>;
  modelled_central_bills: PersonalizedBillImpactItem[];
  knowledge_only_developments: PersonalizedBillImpactItem[];
  upcoming_verified_legislation: Array<{
    bill_id: string;
    title: string;
    jurisdiction: string;
    state?: string | null;
    expected_stage: string;
    model_status: string;
  }>;
  recent_document_changes: Record<string, any>[];
  stats: Record<string, number>;
  generated_at: string;
  disclaimer: string;
}

export interface PersonalizedImpactReportResponse {
  report_id: string;
  user_id: string;
  tenant_id: string;
  report_title: string;
  portfolio_summary: Record<string, any>;
  relevant_bills: PersonalizedBillImpactItem[];
  new_developments: PersonalizedChangeFeedItem[];
  company_exposures: Array<{
    company: string;
    bills_count: number;
    bills: string[];
  }>;
  sector_exposures: Array<{
    sector: string;
    holdings_count: number;
  }>;
  modelled_central_results: Record<string, any>[];
  knowledge_only_developments: Record<string, any>[];
  upcoming_verified_legislation: Record<string, any>[];
  sources_and_provenance: string[];
  disclaimers: string[];
  generated_at: string;
}

export interface ExplainRelevanceResponse {
  bill_id: string;
  bill_title?: string | null;
  relevance_tier: string;
  primary_reason?: string | null;
  explanation: string;
  affected_holdings: string[];
  model_status: string;
  grounded: boolean;
  disclaimer: string;
}


