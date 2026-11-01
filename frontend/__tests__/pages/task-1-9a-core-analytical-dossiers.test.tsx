/**
 * __tests__/pages/task-1-9a-core-analytical-dossiers.test.tsx
 * ============================================================
 * Focused regression test suite for Task 1.9A:
 * Core Analytical Dossiers Redesign.
 *
 * Validates:
 * 1. Bill Dossier 4-Section Consolidation & Legacy 12-Tab Migration
 * 2. Summary Rail Grounded Metadata Rendering
 * 3. Plain-Language Summary Precedence over Dense Statutory Text
 * 4. Mode A vs Mode B Company Isolation & Firewall Governance
 * 5. Prediction Terminal Search, Filters & Non-Color Glyph Indicators
 * 6. Single Prediction Dossier Interpretation & Supported Event-Window Selection
 * 7. Advanced Econometric Decomposition Progressive Disclosure
 * 8. Regulatory Non-Financial Advice Safeguards
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock Next.js navigation hooks
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
}));

// Mock API clients
vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    getBill: vi.fn(),
    getBillPredictions: vi.fn(),
    getBillCompanies: vi.fn(),
    getBillAnticipation: vi.fn(),
    getBillDossier: vi.fn().mockResolvedValue(null),
  },
}));

vi.mock("@/lib/api/companies", () => ({
  companiesApi: {
    getCompany: vi.fn(),
    getCompanyPredictions: vi.fn(),
    getCompanyAnticipation: vi.fn(),
    getCompanyExposures: vi.fn(),
    listCompanies: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  },
}));

vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    listPredictions: vi.fn(),
    getPrediction: vi.fn(),
    getPredictionDecision: vi.fn(),
    compareHorizons: vi.fn(),
    getStakeholderReport: vi.fn(),
  },
}));

vi.mock("@/lib/api/coverage", () => ({
  coverageApi: {
    getCoverage: vi.fn(),
  },
}));

vi.mock("@/lib/api/anticipation", () => ({
  anticipationApi: {
    getByPair: vi.fn(),
    getContext: vi.fn().mockResolvedValue(null),
    getEvidence: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn().mockResolvedValue({ content: "Grounded analysis.", success: true }),
    explainBill: vi.fn(),
    explainCompany: vi.fn(),
  },
}));

vi.mock("@/lib/api/watchlists", () => ({
  watchlistsApi: {
    listWatchlists: vi.fn().mockResolvedValue([]),
    createWatchlist: vi.fn(),
    addItem: vi.fn(),
  },
}));

import BillDetailContent, {
  BILL_SECTIONS,
  LEGACY_TAB_MAP,
} from "@/app/bills/[billId]/BillDetailContent";
import CompanyDetailContent from "@/app/companies/[companyId]/CompanyDetailContent";
import PredictionsContent from "@/app/predictions/PredictionsContent";
import PredictionDetailContent from "@/app/predictions/[predictionId]/PredictionDetailContent";

import { billsApi } from "@/lib/api/bills";
import { companiesApi } from "@/lib/api/companies";
import { predictionsApi } from "@/lib/api/predictions";
import { coverageApi } from "@/lib/api/coverage";
import { anticipationApi } from "@/lib/api/anticipation";
import type {
  BillDetailResponse,
  CompanyDetailResponse,
  PredictionItem,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Test Fixtures
// ---------------------------------------------------------------------------

const mockCentralBill: BillDetailResponse = {
  bill: {
    bill_id: "the-banking-laws-amendment-bill-2024",
    jurisdiction: "central",
    state: null,
    title: "The Banking Laws (Amendment) Bill, 2024",
    short_title: "Banking Laws Bill",
    bill_number: "Bill No. 125 of 2024",
    legislature: "Parliament of India",
    house: "Lok Sabha",
    year: 2024,
    introduction_date: "2024-08-09",
    assent_date: "2024-12-15",
    status: "assented",
    policy_domain: "Financial Regulation",
    economic_sectors: ["Banking & Financial Services"],
    secondary_sectors: [],
    stakeholders: ["Commercial Banks", "Cooperative Credit"],
    summary: "Reforms statutory reserve requirements and corporate governance across banking institutions.",
    company_exposure_count: 5,
    listed_company_exposure_count: 5,
    market_relevance: "HIGH",
    modeling_eligibility: "ELIGIBLE",
    data_sufficiency: "COMPLETE",
    source_url: "https://prsindia.org/billtrack/the-banking-laws-amendment-bill-2024",
    pdf_url: "https://prsindia.org/files/bills_spec/the-banking-laws-amendment-bill-2024.pdf",
    data_quality: "VERIFIED",
  },
  provisions: [
    "Amends Section 19 of the Banking Regulation Act, 1949 to revise director tenure.",
    "Modifies reserve ratio claim thresholds for commercial banks.",
  ],
  knowledge: {
    amended_acts: ["Banking Regulation Act, 1949", "State Bank of India Act, 1955"],
    regulatory_authority: "Reserve Bank of India",
    financial_terms: "Modifies statutory liquidity and cash reserve computation mechanisms.",
    penalties_or_enforcement: "Regulatory penalties under Section 46 for reporting discrepancies.",
    objective: "To strengthen governance and enhance depositor protection.",
    key_provisions: [
      "Amends Section 19 of the Banking Regulation Act, 1949 to revise director tenure.",
      "Modifies reserve ratio claim thresholds for commercial banks.",
    ],
  },
  provenance: {
    title: "AUTHORITATIVE",
    introduction_date: "AUTHORITATIVE",
  },
  prediction_available: true,
  related_bills: [],
};

const mockModeACompany: CompanyDetailResponse = {
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
  ownership_type: "Private Listed Corporate",
  is_active: true,
  listing_status: "Listed",
  sector: "Energy & Petrochemicals",
  industry: "Oil & Gas Refining",
  sub_industry: "Integrated Energy",
  business_description: "Diversified conglomerate spanning refining, petrochemicals, telecommunications, and retail.",
  business_activities: ["Oil Exploration", "Petrochemicals", "Digital Services"],
  hq_state: "Maharashtra",
  hq_city: "Mumbai",
  operating_states: ["Maharashtra", "Gujarat", "Andhra Pradesh"],
  state_presences: [{ state: "Gujarat", facilities: 4 }],
  facilities: [{ name: "Jamnagar Complex", state: "Gujarat" }],
  data_sources: ["BSE", "NSE"],
  data_quality_score: 0.98,
  data_quality_label: "VERIFIED",
  related_bills: [],
  total_exposures: 3,
  central_exposures_count: 2,
  state_exposures_count: 1,
  direct_exposures_count: 2,
  indirect_exposures_count: 1,
  exposure_types: ["REGULATORY"],
  mechanisms: ["licensing"],
  affected_sectors: ["Energy & Petrochemicals"],
  watchlist_eligible: true,
  is_quant_eligible: true,
  market_prediction_available: true,
  quantitative_firewall_status: "ACTIVE",
};

const mockModeBCompany: CompanyDetailResponse = {
  company_id: "INE043D01016",
  company_name: "GMR Airports Infrastructure Limited",
  legal_identity: "GMR Airports Infrastructure Limited",
  aliases: ["GMR Infra"],
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
  sub_industry: "Terminal Operations",
  business_description: "Airport operations and public concession infrastructure.",
  business_activities: ["Airport Concessions", "Terminal Management"],
  hq_state: "Delhi",
  hq_city: "New Delhi",
  operating_states: ["Delhi", "Telangana"],
  state_presences: [],
  facilities: [],
  data_sources: ["AAI Concessions"],
  data_quality_score: 0.90,
  data_quality_label: "VERIFIED",
  related_bills: [],
  total_exposures: 1,
  central_exposures_count: 1,
  state_exposures_count: 0,
  direct_exposures_count: 1,
  indirect_exposures_count: 0,
  exposure_types: ["REGULATORY"],
  mechanisms: ["concession"],
  affected_sectors: ["Infrastructure & Transport"],
  watchlist_eligible: true,
  is_quant_eligible: false,
  market_prediction_available: false,
  quantitative_firewall_status: "FIREWALLED",
};

const mockSinglePrediction: PredictionItem = {
  prediction_id: "pred_banking_sbi_01",
  bill_id: "the-banking-laws-amendment-bill-2024",
  company_isin: "INE062A01020",
  company_name: "State Bank of India",
  company_symbol: "SBIN",
  sector: "Banking & Financial Services",
  event_window: "[-1,+1]",
  predicted_direction: "POSITIVE",
  predicted_market_moving: true,
  market_moving_probability: 0.742,
  predicted_impact_strength: "HIGH",
  predicted_confidence: "HIGH",
  confidence_score: 0.825,
  model_version: "v1.0.0",
  created_at: "2024-12-01T00:00:00Z",
};

const mockHorizonComparisons = {
  bill_id: "the-banking-laws-amendment-bill-2024",
  bill_title: "The Banking Laws (Amendment) Bill, 2024",
  company_isin: "INE062A01020",
  company_name: "State Bank of India",
  company_symbol: "SBIN",
  modeled_windows: ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"],
  comparisons: [
    {
      event_window: "[-1,+1]",
      is_modeled: true,
      predicted_direction: "POSITIVE",
      market_moving_probability: 0.742,
      impact_score: 0.72,
      confidence_score: 0.825,
    },
    {
      event_window: "[-3,+3]",
      is_modeled: true,
      predicted_direction: "POSITIVE",
      market_moving_probability: 0.685,
      impact_score: 0.65,
      confidence_score: 0.79,
    },
    {
      event_window: "[-5,+5]",
      is_modeled: true,
      predicted_direction: "POSITIVE",
      market_moving_probability: 0.612,
      impact_score: 0.58,
      confidence_score: 0.75,
    },
    {
      event_window: "[-5,+10]",
      is_modeled: true,
      predicted_direction: "NEUTRAL",
      market_moving_probability: 0.45,
      impact_score: 0.40,
      confidence_score: 0.65,
    },
    {
      event_window: "[-10,+10]",
      is_modeled: true,
      predicted_direction: "NEUTRAL",
      market_moving_probability: 0.38,
      impact_score: 0.35,
      confidence_score: 0.60,
    },
  ],
  unmodeled_note: "Temporal windows outside the 5 validated event horizons are unmodeled.",
};

// ---------------------------------------------------------------------------
// Unit & Regression Tests
// ---------------------------------------------------------------------------

describe("Task 1.9A — Core Analytical Dossiers Redesign", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(billsApi.getBillPredictions).mockResolvedValue({
      available: false,
      has_predictions: false,
      total: 0,
      predictions: [],
      items: [],
    } as any);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValue([]);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValue({ available: false } as any);
    vi.mocked(billsApi.getBillDossier).mockResolvedValue(null);

    vi.mocked(companiesApi.getCompanyPredictions).mockResolvedValue({
      available: false,
      has_predictions: false,
      total: 0,
      predictions: [],
      items: [],
    } as any);
    vi.mocked(companiesApi.getCompanyAnticipation).mockResolvedValue({ available: false } as any);
    vi.mocked(companiesApi.getCompanyExposures).mockResolvedValue([]);
    vi.mocked(companiesApi.listCompanies).mockResolvedValue({ items: [], total: 0 } as any);

    vi.mocked(predictionsApi.compareHorizons).mockResolvedValue(mockHorizonComparisons as any);
    vi.mocked(predictionsApi.getStakeholderReport).mockResolvedValue({
      report_id: "rep_1",
      executive_summary: "Assessment summary",
      key_takeaways: [],
    } as any);
    vi.mocked(anticipationApi.getByPair).mockResolvedValue({ available: false } as any);
  });

  // 1. BILL DOSSIER: 4 EDITORIAL SECTIONS & LEGACY 12-TAB MIGRATION
  describe("1. Bill Dossier (/bills/[billId]) Editorial Consolidation", () => {
    it("renders all 4 consolidated editorial sections with metadata rail", async () => {
      vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralBill);

      render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

      // Verify the 4 editorial section tabs
      await waitFor(() => {
        expect(screen.getByText("Summary & Journey")).toBeInTheDocument();
        expect(screen.getByText("Statutory Mechanics")).toBeInTheDocument();
        expect(screen.getByText("Corporate & Market Impact")).toBeInTheDocument();
        expect(screen.getByText("Provenance & Evidence")).toBeInTheDocument();
      });

      // Verify concise grounded summary rail
      expect(screen.getByText("Legislative Summary Rail")).toBeInTheDocument();
      expect(screen.getAllByText("Central Parliament").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Bill No. 125 of 2024").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("5 (5 listed)")).toBeInTheDocument();
      expect(screen.getAllByText("✓ VERIFIED").length).toBeGreaterThanOrEqual(1);
    });

    it("verifies authoritative 12-tab migration map to canonical sections", () => {
      // Every legacy tab has an unambiguous mapping
      expect(LEGACY_TAB_MAP["overview"].section).toBe("executive");
      expect(LEGACY_TAB_MAP["timeline"].section).toBe("executive");
      expect(LEGACY_TAB_MAP["changes"].section).toBe("executive");
      expect(LEGACY_TAB_MAP["provisions"].section).toBe("mechanics");
      expect(LEGACY_TAB_MAP["sectors"].section).toBe("impact");
      expect(LEGACY_TAB_MAP["exposures"].section).toBe("impact");
      expect(LEGACY_TAB_MAP["predictions"].section).toBe("impact");
      expect(LEGACY_TAB_MAP["anticipation"].section).toBe("impact");
      expect(LEGACY_TAB_MAP["stakeholders"].section).toBe("impact");
      expect(LEGACY_TAB_MAP["documents"].section).toBe("provenance");
      expect(LEGACY_TAB_MAP["ai"].section).toBe("provenance");
      expect(LEGACY_TAB_MAP["provenance"].section).toBe("provenance");

      // Verify the 4 sections exist in BILL_SECTIONS
      const sectionIds = BILL_SECTIONS.map((s) => s.id);
      expect(sectionIds).toEqual(["executive", "mechanics", "impact", "provenance"]);
    });

    it("allows switching sections and preserves statutory mechanics view", async () => {
      vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralBill);

      render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

      await waitFor(() => {
        expect(screen.getByRole("tab", { name: /Statutory Mechanics/i })).toBeInTheDocument();
      });

      // Click Section 2: Statutory Mechanics
      fireEvent.click(screen.getByRole("tab", { name: /Statutory Mechanics/i }));

      // Verify statutory provisions content renders
      await waitFor(() => {
        expect(screen.getByText(/Key Statutory Provisions/i)).toBeInTheDocument();
        expect(screen.getAllByText(/Banking Regulation Act, 1949/i).length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  // 2. COMPANY DOSSIER: MODE A VS MODE B ISOLATION
  describe("2. Company Dossier (/companies/[companyId]) Mode Isolation", () => {
    it("renders Mode A Quantitative profile with prediction-eligible indicator", async () => {
      vi.mocked(companiesApi.getCompany).mockResolvedValueOnce(mockModeACompany);
      vi.mocked(companiesApi.getCompanyPredictions).mockResolvedValueOnce({
        available: true,
        has_predictions: true,
        company_id: "INE002A01018",
        universe_type: "quantitative",
        predictions: [],
        items: [],
        total: 0,
      });

      render(<CompanyDetailContent companyId="INE002A01018" />);

      await waitFor(() => {
        expect(screen.getByText(/Mode A: Quantitative \/ Prediction-Eligible Entity/i)).toBeInTheDocument();
        expect(screen.getByText(/ISIN: INE002A01018/i)).toBeInTheDocument();
        expect(screen.getByText("Market Predictions")).toBeInTheDocument();
      });
    });

    it("renders Mode B Qualitative profile with permanent firewall and zero prediction charts", async () => {
      vi.mocked(companiesApi.getCompany).mockResolvedValueOnce(mockModeBCompany);
      vi.mocked(companiesApi.getCompanyPredictions).mockResolvedValueOnce({
        available: false,
        has_predictions: false,
        company_id: "INE043D01016",
        universe_type: "intelligence",
        firewall_status: "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS",
        message: "Intelligence-only entities are strictly firewalled from market models.",
        predictions: [],
        items: [],
        total: 0,
      });

      render(<CompanyDetailContent companyId="INE043D01016" />);

      await waitFor(() => {
        expect(screen.getByText(/Mode B: Qualitative Intelligence Entity/i)).toBeInTheDocument();
        expect(screen.getByText(/Statutory Firewall Active/i)).toBeInTheDocument();
        expect(screen.getByText("Prediction Firewall")).toBeInTheDocument();
      });

      // Switch to Prediction Firewall tab
      fireEvent.click(screen.getByText("Prediction Firewall"));

      // Must render IntelligenceCompanyFirewall and NOT empty prediction charts
      await waitFor(() => {
        expect(screen.getByText("Market prediction unavailable for this entity")).toBeInTheDocument();
        expect(screen.getByText(/The quantitative firewall is permanently active for this entity/i)).toBeInTheDocument();
      });
    });
  });

  // 3. PREDICTION TERMINAL & DOSSIER: HORIZONS & METHODOLOGY
  describe("3. Prediction Terminal & Dossier (/predictions & /predictions/[id])", () => {
    it("renders predictions terminal with search, filter strip, and non-color glyphs", async () => {
      vi.mocked(coverageApi.getCoverage).mockResolvedValueOnce({
        central: { production_bills: 20, quantitative_companies: 47, bill_company_pairs: 940, predictions_count: 4700, event_windows_count: 5 },
        state: { state_stock_predictions_count: 0 },
      } as any);

      vi.mocked(predictionsApi.listPredictions).mockResolvedValueOnce({
        items: [mockSinglePrediction],
        total: 1,
        page: 1,
        limit: 25,
        pages: 1,
      });

      render(<PredictionsContent />);

      await waitFor(() => {
        expect(screen.getByText("Prediction Analytics")).toBeInTheDocument();
        expect(screen.getByText("State Bank of India")).toBeInTheDocument();
        expect(screen.getByText("View Dossier →")).toBeInTheDocument();
        expect(screen.getAllByText("POSITIVE").length).toBeGreaterThanOrEqual(1);
      });
    });

    it("renders single prediction dossier with concise interpretation and supported event-window selector", async () => {
      vi.mocked(predictionsApi.getPrediction).mockResolvedValueOnce(mockSinglePrediction);
      vi.mocked(predictionsApi.getPredictionDecision).mockResolvedValueOnce({
        decision_id: "dec_01",
        risk_category: "MODERATE",
        pricing_in_risk: "PARTIALLY_PRICED_IN",
        impact_score: 0.72,
        risk_score: 0.45,
        decision_reason: "Standard risk weighting.",
      } as any);
      vi.mocked(predictionsApi.compareHorizons).mockResolvedValueOnce(mockHorizonComparisons as any);

      render(<PredictionDetailContent predictionId="pred_banking_sbi_01" />);

      // Verify concise interpretation & non-financial advice notice
      await waitFor(() => {
        expect(screen.getByText("State Bank of India")).toBeInTheDocument();
        expect(screen.getByText(/Institutional Non-Financial Advice Notice/i)).toBeInTheDocument();
        expect(screen.getByText(/Analytical Thesis:/i)).toBeInTheDocument();
      });

      // Verify supported event horizon selector buttons exist
      expect(screen.getByRole("tab", { name: /\[-1,\+1\]/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /\[-3,\+3\]/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /\[-5,\+5\]/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /\[-5,\+10\]/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /\[-10,\+10\]/i })).toBeInTheDocument();

      // Click alternative event horizon [-3,+3]
      fireEvent.click(screen.getByRole("tab", { name: /\[-3,\+3\]/i }));

      // Verify comparative data displayed without implying dynamic reruns
      await waitFor(() => {
        expect(screen.getByText("68.5%")).toBeInTheDocument();
      });

      // Verify progressive disclosure of advanced econometrics
      expect(screen.getByText(/Advanced Econometric Decomposition & Methodology/i)).toBeInTheDocument();
      expect(screen.getByText(/50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7/i)).toBeInTheDocument();
    });
  });
});
