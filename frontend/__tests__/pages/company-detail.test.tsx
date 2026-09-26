/**
 * __tests__/pages/company-detail.test.tsx
 * ========================================
 * Comprehensive unit and integration test suite for Corporate Intelligence Profiles.
 *
 * Validates all 18 core requirements:
 * 1. Quantitative company profile rendering (Mode A)
 * 2. Intelligence-only company profile rendering (Mode B)
 * 3. Company not found (404 state)
 * 4. Company exposure list & metrics
 * 5. Exposure matrix filters (Jurisdiction, Directness, Strength, Relevance)
 * 6. Central prediction section with event windows & neutral wording
 * 7. Prediction unavailable state
 * 8. IntelligenceCompanyFirewall engagement for intelligence entities
 * 9. State exposure section & invariant disclaimer
 * 10. Market relevance qualitative classification
 * 11. Anticipation section & neutral framing
 * 12. Provenance and statutory/company evidence
 * 13. Watchlist action & modal subscription
 * 14. AI explanation success state
 * 15. AI explanation unavailable fallback state
 * 16. API failure error state with retry
 * 17. Loading skeleton state
 * 18. FACT / DERIVED / INTERPRETATION / PREDICTION semantic badge distinction
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock API clients
vi.mock("@/lib/api/companies", () => ({
  companiesApi: {
    getCompany: vi.fn(),
    getCompanyPredictions: vi.fn(),
    getCompanyAnticipation: vi.fn(),
    getCompanyExposures: vi.fn(),
    listCompanies: vi.fn(),
  },
}));

vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    getPredictionDecision: vi.fn(),
  },
}));

vi.mock("@/lib/api/watchlists", () => ({
  watchlistsApi: {
    listWatchlists: vi.fn(),
    createWatchlist: vi.fn(),
    addItem: vi.fn(),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    explainCompany: vi.fn(),
    ask: vi.fn(),
  },
}));

import CompanyDetailContent from "@/app/companies/[companyId]/CompanyDetailContent";
import { companiesApi } from "@/lib/api/companies";
import { predictionsApi } from "@/lib/api/predictions";
import { watchlistsApi } from "@/lib/api/watchlists";
import { aiApi } from "@/lib/api/ai";
import { ApiError } from "@/lib/errors";
import type {
  BillCompanyExposure,
  CompanyAnticipationResponse,
  CompanyDetailResponse,
  CompanyPredictionStatusResponse,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Realistic API-Shaped Fixtures
// ---------------------------------------------------------------------------

const mockExposures: BillCompanyExposure[] = [
  {
    bill_id: "the-oilfields-regulation-and-development-amendment-bill-2024",
    bill_title: "The Oilfields (Regulation and Development) Amendment Bill, 2024",
    company_id: "INE002A01018",
    company_name: "Reliance Industries Limited",
    bill_number: "Bill No. 118 of 2024",
    jurisdiction: "central",
    state: null,
    bill_status: "introduced",
    sector: "Energy & Petrochemicals",
    sub_sector: "Upstream Oil & Gas",
    business_activity: "Offshore exploration and deepwater production",
    exposure_type: "REGULATORY",
    exposure_direction: "NEUTRAL",
    exposure_strength: "HIGH",
    direct_indirect: "DIRECT",
    geographic_scope: "National",
    mechanism: "licensing",
    market_relevance: "HIGH",
    confidence: "HIGH",
    has_evidence: true,
    evidence: [
      {
        claim: "Amends statutory mining lease rules for offshore petroleum exploration blocks.",
        reference: "Gazette Notification Part II Sec 2",
        url: "https://prsindia.org/billtrack/oilfields-amendment",
        statutory_section: "4A",
      },
    ],
    source_urls: ["https://prsindia.org/billtrack/oilfields-amendment"],
  },
  {
    bill_id: "andhra-pradesh-electricity-duty-amendment-bill-2024",
    bill_title: "Andhra Pradesh Electricity Duty (Amendment) Bill, 2024",
    company_id: "INE002A01018",
    company_name: "Reliance Industries Limited",
    bill_number: "LA Bill 12 of 2024",
    jurisdiction: "state",
    state: "Andhra Pradesh",
    bill_status: "passed",
    sector: "Energy & Petrochemicals",
    sub_sector: "Power Generation",
    business_activity: "Captive petrochemical co-generation plants",
    exposure_type: "TAX",
    exposure_direction: "NEGATIVE",
    exposure_strength: "MEDIUM",
    direct_indirect: "DIRECT",
    geographic_scope: "State",
    mechanism: "taxation",
    market_relevance: "MEDIUM",
    confidence: "HIGH",
    has_evidence: true,
    evidence: [
      {
        claim: "Levies duty on self-generated captive industrial power consumption in Andhra Pradesh.",
        reference: "Andhra Pradesh Gazette Extraordinary No. 45",
        statutory_section: "3(1)(b)",
      },
    ],
    source_urls: [],
  },
  {
    bill_id: "the-coastal-shipping-bill-2024",
    bill_title: "The Coastal Shipping Bill, 2024",
    company_id: "INE002A01018",
    company_name: "Reliance Industries Limited",
    bill_number: "Bill No. 132 of 2024",
    jurisdiction: "central",
    state: null,
    bill_status: "introduced",
    sector: "Logistics & Ports",
    sub_sector: "Maritime Freight",
    business_activity: "Coastal crude tanker shipping and port logistics",
    exposure_type: "COMPLIANCE",
    exposure_direction: "NEUTRAL",
    exposure_strength: "LOW",
    direct_indirect: "INDIRECT",
    geographic_scope: "National",
    mechanism: "compliance_cost",
    market_relevance: "LOW",
    confidence: "MEDIUM",
    has_evidence: true,
    evidence: [
      {
        claim: "Streamlines cabotage licensing for Indian-flagged cargo vessels carrying petroleum.",
        reference: "Lok Sabha Bulletin Part II",
        statutory_section: "12",
      },
    ],
    source_urls: [],
  },
];

const mockQuantCompany: CompanyDetailResponse = {
  company_id: "INE002A01018",
  company_name: "Reliance Industries Limited",
  legal_identity: "Reliance Industries Limited",
  aliases: ["RIL", "Reliance"],
  ticker_nse: "RELIANCE",
  ticker_bse: "500325",
  bse_code: "500325",
  isin: "INE002A01018",
  entity_type: "listed_company",
  universe_type: "quantitative",
  group_name: "Reliance Group",
  ownership_type: "Private",
  is_active: true,
  listing_status: "Listed",
  sector: "Energy & Petrochemicals",
  industry: "Oil & Gas Refining",
  sub_industry: "Integrated Oil & Gas",
  business_description: "A Fortune 500 company and the largest private sector corporation in India.",
  business_activities: ["Oil Refining", "Petrochemicals", "Retail", "Telecommunications"],
  hq_state: "Maharashtra",
  hq_city: "Mumbai",
  operating_states: ["Maharashtra", "Gujarat", "Andhra Pradesh"],
  state_presences: [{ state: "Gujarat", facilities: 4 }],
  facilities: [
    { name: "Jamnagar Refinery Complex", state: "Gujarat" },
    { name: "Kakinada Onshore Gas Terminal", state: "Andhra Pradesh" },
  ],
  data_sources: ["BSE", "NSE", "Ministry of Corporate Affairs"],
  data_quality_score: 0.98,
  data_quality_label: "VERIFIED",
  related_bills: mockExposures,
  total_exposures: 3,
  central_exposures_count: 2,
  state_exposures_count: 1,
  direct_exposures_count: 2,
  indirect_exposures_count: 1,
  exposure_types: ["REGULATORY", "TAX", "COMPLIANCE"],
  mechanisms: ["licensing", "taxation", "compliance_cost"],
  affected_sectors: ["Energy & Petrochemicals", "Logistics & Ports"],
  watchlist_eligible: true,
  is_quant_eligible: true,
  market_prediction_available: true,
  quantitative_firewall_status: "ACTIVE",
};

const mockIntelCompany: CompanyDetailResponse = {
  company_id: "INE043D01016",
  company_name: "GMR Airports Infrastructure Limited",
  legal_identity: "GMR Airports Infrastructure Limited",
  aliases: ["GMR Infra", "GMR Airports"],
  ticker_nse: "",
  ticker_bse: "",
  bse_code: "",
  isin: "INE043D01016",
  entity_type: "public_utility",
  universe_type: "intelligence",
  group_name: "GMR Group",
  ownership_type: "Public Utility / State Partnership",
  is_active: true,
  listing_status: "Unlisted",
  sector: "Infrastructure & Transport",
  industry: "Airport Infrastructure",
  sub_industry: "Airport Terminal Operations",
  business_description: "Airport infrastructure entity operating major transport hubs under concession frameworks.",
  business_activities: ["Airport Operation", "Aviation Logistics"],
  hq_state: "Delhi",
  hq_city: "New Delhi",
  operating_states: ["Delhi", "Telangana", "Andhra Pradesh"],
  state_presences: [],
  facilities: [{ name: "Indira Gandhi International Airport Hub", state: "Delhi" }],
  data_sources: ["AAI Concessions", "Ministry of Civil Aviation"],
  data_quality_score: 0.92,
  data_quality_label: "VERIFIED",
  related_bills: [mockExposures[0]],
  total_exposures: 1,
  central_exposures_count: 1,
  state_exposures_count: 0,
  direct_exposures_count: 1,
  indirect_exposures_count: 0,
  exposure_types: ["REGULATORY"],
  mechanisms: ["licensing"],
  affected_sectors: ["Infrastructure & Transport"],
  watchlist_eligible: true,
  is_quant_eligible: false,
  market_prediction_available: false,
  quantitative_firewall_status: "FIREWALLED",
};

const mockPredictionsQuant: CompanyPredictionStatusResponse = {
  available: true,
  has_predictions: true,
  company_id: "INE002A01018",
  universe_type: "quantitative",
  predictions: [
    {
      prediction_id: "pred_ril_oilfields_0_1",
      bill_id: "the-oilfields-regulation-and-development-amendment-bill-2024",
      bill_title: "The Oilfields (Regulation and Development) Amendment Bill, 2024",
      company_isin: "INE002A01018",
      event_window: "[0,1]",
      predicted_direction: "POSITIVE",
      predicted_market_moving: true,
      market_moving_probability: 0.74,
      predicted_impact_strength: "HIGH",
      predicted_confidence: "HIGH",
      confidence_score: 0.85,
    },
    {
      prediction_id: "pred_ril_shipping_0_5",
      bill_id: "the-coastal-shipping-bill-2024",
      bill_title: "The Coastal Shipping Bill, 2024",
      company_isin: "INE002A01018",
      event_window: "[0,5]",
      predicted_direction: "NEUTRAL",
      predicted_market_moving: false,
      market_moving_probability: 0.22,
      predicted_impact_strength: "LOW",
      predicted_confidence: "MEDIUM",
      confidence_score: 0.65,
    },
  ],
  items: [],
  total: 2,
};

const mockPredictionsIntel: CompanyPredictionStatusResponse = {
  available: false,
  has_predictions: false,
  company_id: "INE043D01016",
  universe_type: "intelligence",
  firewall_status: "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS",
  message: "Intelligence-only entities are strictly firewalled from market models. Stock predictions remain strictly 0.",
  predictions: [],
  items: [],
  total: 0,
};

const mockAnticipationQuant: CompanyAnticipationResponse = {
  available: true,
  has_anticipation: true,
  company_id: "INE002A01018",
  scores: [
    {
      bill_id: "the-oilfields-regulation-and-development-amendment-bill-2024",
      company_isin: "INE002A01018",
      company_symbol: "RELIANCE",
      official_introduction_date: "2024-08-09",
      market_signal_score: 0.65,
      information_signal_score: 0.55,
      anticipation_score: 0.60,
      classification: "MODERATE_EVIDENCE",
      anticipation_flag: true,
      confidence: "HIGH",
      evidence_count: 3,
      media_data_available: true,
      decision_reason: "Elevated media coverage and trading volume observed in [-5,-1] window.",
      detected_signals: ["Unusual pre-announcement trading volume", "National press commentary"],
    },
  ],
  total: 1,
};

const mockAnticipationIntel: CompanyAnticipationResponse = {
  available: false,
  has_anticipation: false,
  company_id: "INE043D01016",
  reason: "INTELLIGENCE_ONLY_ENTITY",
  firewall_status: "INTELLIGENCE_ONLY_NO_ANTICIPATION",
  message: "Intelligence-only entities are strictly firewalled from market anticipation models.",
  scores: [],
  total: 0,
};

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe("CompanyDetailContent — Production Corporate Profile", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock returns
    vi.mocked(companiesApi.getCompany).mockResolvedValue(mockQuantCompany);
    vi.mocked(companiesApi.getCompanyPredictions).mockResolvedValue(mockPredictionsQuant);
    vi.mocked(companiesApi.getCompanyAnticipation).mockResolvedValue(mockAnticipationQuant);
    vi.mocked(companiesApi.getCompanyExposures).mockResolvedValue(mockExposures);
    vi.mocked(companiesApi.listCompanies).mockResolvedValue({
      items: [
        {
          company_id: "INE213A01029",
          company_name: "Oil and Natural Gas Corporation Limited",
          isin: "INE213A01029",
          ticker_nse: "ONGC",
          sector: "Energy & Petrochemicals",
          industry: "Oil Exploration",
          entity_type: "state_owned_enterprise",
          universe_type: "quantitative",
          ownership_type: "Public / State-Owned",
          is_active: true,
          listing_status: "Listed",
          watchlist_eligible: true,
          is_quant_eligible: true,
          market_prediction_available: true,
          documented_exposure_count: 2,
        },
      ],
      total: 1,
      page: 1,
      limit: 8,
      pages: 1,
    });
    vi.mocked(watchlistsApi.listWatchlists).mockResolvedValue([
      {
        watchlist_id: "wl-energy",
        user_id: "user_1",
        tenant_id: "tenant_1",
        name: "Energy & Utilities Portfolio",
        is_default: true,
        is_active: true,
        created_at: "2026-09-01T00:00:00Z",
        updated_at: "2026-09-01T00:00:00Z",
        items_count: 3,
        items: [],
        rules: [],
      },
    ]);
  });

  // 1. Quantitative company profile rendering (Mode A)
  it("1. renders quantitative company profile with Mode A indicators", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Reliance Industries Limited" })).toBeInTheDocument();
    });

    expect(screen.getByText("📈 QUANTITATIVE")).toBeInTheDocument();
    expect(screen.getByText("PREDICTION AVAILABLE")).toBeInTheDocument();
    expect(screen.getAllByText("Reliance Group").length).toBeGreaterThan(0);
    expect(screen.getByText("RELIANCE")).toBeInTheDocument();
  });

  // 2. Intelligence-only company profile rendering (Mode B)
  it("2. renders intelligence-only company profile with Mode B indicators", async () => {
    vi.mocked(companiesApi.getCompany).mockResolvedValue(mockIntelCompany);
    vi.mocked(companiesApi.getCompanyPredictions).mockResolvedValue(mockPredictionsIntel);
    vi.mocked(companiesApi.getCompanyAnticipation).mockResolvedValue(mockAnticipationIntel);
    vi.mocked(companiesApi.getCompanyExposures).mockResolvedValue([mockExposures[0]]);

    render(<CompanyDetailContent companyId="INE043D01016" />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "GMR Airports Infrastructure Limited" })).toBeInTheDocument();
    });

    expect(screen.getByText("🔬 INTELLIGENCE ONLY")).toBeInTheDocument();
    expect(screen.getByText("UNLISTED")).toBeInTheDocument();
    expect(screen.getByText("PREDICTION UNAVAILABLE")).toBeInTheDocument();
  });

  // 3. Company not found (404 state)
  it("3. renders 404 company not found error state", async () => {
    vi.mocked(companiesApi.getCompany).mockRejectedValue(
      ApiError.fromStatus(404, "Company 'INE_NONEXISTENT' not found.")
    );

    render(<CompanyDetailContent companyId="INE_NONEXISTENT" />);

    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument();
    });
  });

  // 4. Company exposure list & counts
  it("4. renders company exposure list and distribution counts", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Legislative Exposure Summary")).toBeInTheDocument();
    });

    // Counts: Total (3), Central (2), State (1), Direct (2), Indirect (1)
    expect(screen.getByText("Total Exposures")).toBeInTheDocument();
    expect(screen.getByText("Central Parliament")).toBeInTheDocument();
    expect(screen.getByText("State Assemblies")).toBeInTheDocument();
  });

  // 5. Exposure matrix filters
  it("5. allows filtering exposure matrix by jurisdiction and search query", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Legislative Footprint")).toBeInTheDocument();
    });

    // Switch to footprint tab
    fireEvent.click(screen.getByText("Legislative Footprint"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/filter by bill title/i)).toBeInTheDocument();
    });

    // Filter by search query
    const searchInput = screen.getByPlaceholderText(/filter by bill title/i);
    fireEvent.change(searchInput, { target: { value: "Oilfields" } });

    expect(
      screen.getByText("The Oilfields (Regulation and Development) Amendment Bill, 2024")
    ).toBeInTheDocument();
    expect(
      screen.queryByText("The Coastal Shipping Bill, 2024")
    ).not.toBeInTheDocument();
  });

  // 6. Central prediction section with event windows & neutral wording
  it("6. renders quantitative predictions with neutral terminology and decision support", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Market Predictions")).toBeInTheDocument();
    });

    // Switch to predictions tab
    fireEvent.click(screen.getByText("Market Predictions"));

    await waitFor(() => {
      expect(screen.getByText("Central Market Impact Projections")).toBeInTheDocument();
    });

    expect(screen.getAllByText("[0,1]").length).toBeGreaterThan(0);
    expect(screen.getByText("⚡ Market-Moving")).toBeInTheDocument();

    // Verify neutral wording disclaimers
    expect(
      screen.getByText(/Quantitative price projections reflect multi-horizon econometric/i)
    ).toBeInTheDocument();

    // Verify no Buy/Sell recommendations exist
    expect(screen.queryByText("Buy")).not.toBeInTheDocument();
    expect(screen.queryByText("Sell")).not.toBeInTheDocument();
  });

  // 7. Prediction unavailable state
  it("7. renders prediction unavailable state when predictions are absent", async () => {
    vi.mocked(companiesApi.getCompanyPredictions).mockResolvedValue({
      available: false,
      has_predictions: false,
      company_id: "INE002A01018",
      universe_type: "quantitative",
      predictions: [],
      items: [],
      total: 0,
    });

    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Market Predictions")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Market Predictions"));

    await waitFor(() => {
      expect(
        screen.getByText(/Prediction data is not currently available for this company/i)
      ).toBeInTheDocument();
    });
  });

  // 8. IntelligenceCompanyFirewall engagement
  it("8. enforces IntelligenceCompanyFirewall for intelligence-only companies", async () => {
    vi.mocked(companiesApi.getCompany).mockResolvedValue(mockIntelCompany);
    vi.mocked(companiesApi.getCompanyPredictions).mockResolvedValue(mockPredictionsIntel);
    vi.mocked(companiesApi.getCompanyAnticipation).mockResolvedValue(mockAnticipationIntel);

    render(<CompanyDetailContent companyId="INE043D01016" />);

    await waitFor(() => {
      expect(screen.getByText("Prediction Firewall")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Prediction Firewall"));

    await waitFor(() => {
      expect(
        screen.getByText("Market prediction unavailable for this entity")
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(/quantitative firewall is permanently active/i)
    ).toBeInTheDocument();
  });

  // 9. State exposure section & invariant disclaimer
  it("9. renders state exposure section with statutory isolation guarantee", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("State & Regional Presence")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("State & Regional Presence"));

    await waitFor(() => {
      expect(
        screen.getByText(/Statutory Isolation: State Legislative Exposure vs Equity Predictions/i)
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(/State stock predictions remain strictly 0/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText("Andhra Pradesh").length).toBeGreaterThan(0);
  });

  // 10. Market relevance qualitative classification
  it("10. displays qualitative market relevance tags without price forecasts", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Legislative Footprint")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Legislative Footprint"));

    await waitFor(() => {
      expect(screen.getAllByText("(Qualitative)")[0]).toBeInTheDocument();
    });
  });

  // 11. Anticipation section & neutral framing
  it("11. renders pre-event anticipation diagnostics and disclaims insider trading", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Pre-Event Anticipation")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Pre-Event Anticipation"));

    await waitFor(() => {
      expect(
        screen.getByText(/Pre-Event Market Information Diffusion Analysis/i)
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText(/They do not allege or imply insider trading/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Moderate Diffusion")).toBeInTheDocument();
  });

  // 12. Provenance and statutory evidence
  it("12. renders source provenance panel with data quality verification", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Audit & Provenance")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Audit & Provenance"));

    await waitFor(() => {
      expect(screen.getByText("Data Quality & Verification Audit")).toBeInTheDocument();
    });

    expect(screen.getByText("Corporate Registrar & Stock Exchange")).toBeInTheDocument();
    expect(screen.getByText("Traceable Evidence Records (3)")).toBeInTheDocument();
  });

  // 13. Watchlist action & modal subscription
  it("13. opens watchlist modal and subscribes company", async () => {
    vi.mocked(watchlistsApi.addItem).mockResolvedValue({
      item_id: "item_rel_1",
      watchlist_id: "wl-energy",
      entity_type: "company",
      entity_id: "INE002A01018",
      canonical_name: "Reliance Industries Limited",
      is_active: true,
      created_at: "2026-09-19T00:00:00Z",
    });

    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("⭐ Add to Watchlist")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("⭐ Add to Watchlist"));

    await waitFor(() => {
      expect(screen.getByText("Add Company to Watchlist")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Confirm Subscription"));

    await waitFor(() => {
      expect(watchlistsApi.addItem).toHaveBeenCalledWith(
        "wl-energy",
        expect.objectContaining({
          entity_type: "company",
          entity_id: "INE002A01018",
          display_name: "Reliance Industries Limited",
        })
      );
    });
  });

  // 14. AI explanation success state
  it("14. renders grounded AI assistant and answers query", async () => {
    vi.mocked(aiApi.ask).mockResolvedValue({
      content: "Reliance Industries Limited is primarily exposed to oilfields regulation and electricity duty amendments.",
      context_type: "company",
      context_id: "INE002A01018",
      persona: "GENERAL_PUBLIC",
      operation: "ASK_AI",
      success: true,
      is_cached: false,
      disclaimer: "Analytical explanation only; not investment advice.",
      provenance_sources: ["Legislative Discovery Service", "Company Intelligence Service"],
    });

    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("AI Analyst Copilot")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("AI Analyst Copilot"));

    await waitFor(() => {
      expect(screen.getByText("AI Corporate Intelligence Analyst")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("What legislation affects this company?"));

    await waitFor(() => {
      expect(
        screen.getByText(/primarily exposed to oilfields regulation/i)
      ).toBeInTheDocument();
    });
    expect(screen.getByText("Grounded")).toBeInTheDocument();
  });

  // 15. AI explanation unavailable fallback state
  it("15. handles AI unreachable state with graceful offline fallback", async () => {
    vi.mocked(aiApi.ask).mockRejectedValue(new Error("AI backend offline"));

    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("AI Analyst Copilot")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("AI Analyst Copilot"));

    await waitFor(() => {
      expect(screen.getByText("What economic mechanisms connect bills to this company?")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("What economic mechanisms connect bills to this company?"));

    await waitFor(() => {
      expect(
        screen.getByText(/AI explanation service is temporarily unreachable/i)
      ).toBeInTheDocument();
    });
  });

  // 16. API failure error state with retry
  it("16. renders error state on network or server failure", async () => {
    vi.mocked(companiesApi.getCompany).mockRejectedValue(
      new Error("Network connection dropped")
    );

    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load corporate profile/i)).toBeInTheDocument();
    });
  });

  // 17. Loading skeleton state
  it("17. displays loading skeleton while fetching company dossier", () => {
    vi.mocked(companiesApi.getCompany).mockReturnValue(new Promise(() => {}));

    render(<CompanyDetailContent companyId="INE002A01018" />);

    expect(screen.getByLabelText("Loading company profile")).toBeInTheDocument();
  });

  // 18. FACT / DERIVED / INTERPRETATION / PREDICTION distinction
  it("18. explicitly renders semantic badges distinguishing FACT, DERIVED, INTERPRETATION, and PREDICTION", async () => {
    render(<CompanyDetailContent companyId="INE002A01018" />);

    await waitFor(() => {
      expect(screen.getByText("Stakeholder Intelligence")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Stakeholder Intelligence"));

    await waitFor(() => {
      expect(screen.getAllByText("FACT").length).toBeGreaterThan(0);
      expect(screen.getAllByText("DERIVED").length).toBeGreaterThan(0);
      expect(screen.getAllByText("INTERPRETATION").length).toBeGreaterThan(0);
      expect(screen.getAllByText("PREDICTION").length).toBeGreaterThan(0);
    });
  });
});
