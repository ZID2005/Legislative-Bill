/**
 * __tests__/pages/task-1-10a-decision-support-redesign.test.tsx
 * ==============================================================
 * Comprehensive regression test suite for Task 1.10A:
 * Decision Support, Risk, Anticipation & State Intelligence Redesign.
 *
 * Validates:
 * 1. Risk Intelligence (/risk) editorial layout, 5-tier model, portfolio aggregator, and regulatory notice.
 * 2. Anticipation Intelligence (/anticipation) chronological timeline, diffusion spectrum, and verbatim disclaimers.
 * 3. State Intelligence Registry (/states) invariant metrics, dual view mode (dossier cards vs tabular registry), and firewall.
 * 4. State Detail Dossier (/states/[state]) assembly enactments register, corporate transmission footprint, and firewall.
 * 5. Immutable Canonical Baseline Hash invariant bit-for-bit check.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import fs from "fs";
import path from "path";
import crypto from "crypto";

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
vi.mock("@/lib/api/risk", () => ({
  riskApi: {
    getRiskSummary: vi.fn(),
    listRiskBills: vi.fn(),
    listRiskCompanies: vi.fn(),
    analyzePortfolioRisk: vi.fn(),
  },
}));

vi.mock("@/lib/api/watchlists", () => ({
  watchlistsApi: {
    listWatchlists: vi.fn(),
  },
}));

vi.mock("@/lib/api/anticipation", () => ({
  anticipationApi: {
    getAnticipationSummary: vi.fn(),
    listAnticipation: vi.fn(),
    getContext: vi.fn().mockResolvedValue({
      bill_id: "the-banking-laws-amendment-bill-2024",
      company_isin: "INE002A01018",
      jurisdiction: "central",
      market_signal: {
        level: "HIGH",
        market_signal_score: 0.62,
        car_magnitude: 0.041,
        z_score: 2.34,
        directional_persistence: 0.70,
        volatility: 0.018,
        signals_detected: ["positive_car_drift"],
      },
      public_information_signal: {
        level: "MEDIUM",
        public_information_evidence_score: 0.58,
        verified_pre_event_count: 2,
        credibility_score: 0.75,
        temporal_proximity_score: 0.80,
        independent_source_count: 2,
        source_diversity_ratio: 1.0,
        verified_evidence: [],
      },
      combined_context: {
        classification: "PUBLIC_INFORMATION_SUPPORTED",
        rationale: "Observable public-information evidence was present prior to official event date.",
        interpretation_headline: "Public information diffusion accompanied by observable pre-event market signal",
        data_quality_state: "VERIFIED",
        anti_leakage_enforced: true,
      },
    }),
    getEvidence: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  },
}));

vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    listBills: vi.fn(),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
  },
}));

import RiskContent from "@/app/risk/RiskContent";
import AnticipationContent from "@/app/anticipation/AnticipationContent";
import StatesPage from "@/app/states/page";
import StateDetailPage from "@/app/states/[state]/page";
import { riskApi } from "@/lib/api/risk";
import { watchlistsApi } from "@/lib/api/watchlists";
import { anticipationApi } from "@/lib/api/anticipation";
import { billsApi } from "@/lib/api/bills";
import { aiApi } from "@/lib/api/ai";

const MANDATORY_LEGAL_DISCLAIMER =
  "Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law.";

describe("Task 1.10A: Decision Support, Risk, Anticipation & State Intelligence Redesign", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    (riskApi.getRiskSummary as ReturnType<typeof vi.fn>).mockResolvedValue({
      total_decisions: 4700,
      avg_overall_risk: 0.442,
      risk_band_distribution: {
        VERY_LOW: 1200,
        LOW: 1400,
        MODERATE: 1300,
        HIGH: 600,
        VERY_HIGH: 200,
      },
      pricing_in_distribution: {
        PRICED_IN: 1100,
        PARTIALLY_PRICED_IN: 1800,
        UNPRICED: 1200,
        NOT_APPLICABLE: 600,
      },
      risk_by_sector: [
        {
          sector: "Banking & Financial Services",
          avg_risk_score: 0.52,
          record_count: 500,
          band_distribution: { VERY_LOW: 50, LOW: 100, MODERATE: 200, HIGH: 120, VERY_HIGH: 30 },
        },
      ],
      risk_by_event_window: [
        {
          event_window: "[-1,+1]",
          avg_risk_score: 0.46,
          record_count: 940,
          band_distribution: { VERY_LOW: 240, LOW: 280, MODERATE: 260, HIGH: 120, VERY_HIGH: 40 },
        },
      ],
      risk_by_bill: [],
      risk_by_company: [],
      thresholds: {},
    });

    (riskApi.listRiskBills as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        bill_id: "the-banking-laws-amendment-bill-2024",
        bill_title: "The Banking Laws (Amendment) Bill, 2024",
        jurisdiction: "central",
        avg_risk_score: 0.51,
        max_risk_score: 0.85,
        high_risk_count: 24,
        record_count: 235,
        dominant_risk_band: "MODERATE",
      },
    ]);

    (riskApi.listRiskCompanies as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        company_isin: "INE062A01020",
        company_name: "State Bank of India",
        company_symbol: "SBIN",
        sector: "Banking & Financial Services",
        universe_type: "QUANTITATIVE",
        avg_risk_score: 0.53,
        max_risk_score: 0.82,
        record_count: 100,
        dominant_risk_band: "MODERATE",
        market_prediction_available: true,
      },
    ]);

    (watchlistsApi.listWatchlists as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        watchlist_id: "wl_01",
        name: "Core Nifty Banks",
        items_count: 5,
      },
    ]);

    (riskApi.analyzePortfolioRisk as ReturnType<typeof vi.fn>).mockResolvedValue({
      selected_companies_count: 2,
      modeled_companies_count: 1,
      unmodeled_companies_count: 1,
      total_exposure_records: 100,
      avg_portfolio_risk_score: 0.53,
      portfolio_risk_band: "MODERATE",
      data_status: "SUFFICIENT_DATA",
      companies: [
        {
          company_isin: "INE062A01020",
          company_name: "State Bank of India",
          sector: "Banking & Financial Services",
          universe_type: "QUANTITATIVE",
          is_modeled: true,
          record_count: 100,
          avg_risk_score: 0.53,
          dominant_risk_band: "MODERATE",
        },
        {
          company_isin: "INTEL001",
          company_name: "Qualitative Entity X",
          sector: "Infrastructure",
          universe_type: "INTELLIGENCE_ONLY",
          is_modeled: false,
          record_count: 0,
        },
      ],
    });

    (anticipationApi.getAnticipationSummary as ReturnType<typeof vi.fn>).mockResolvedValue({
      total_pairs: 940,
      flagged_pairs_count: 82,
      avg_anticipation_score: 0.384,
      avg_market_signal: 0.412,
      avg_information_signal: 0.356,
      classification_distribution: {
        NO_EVIDENCE: 450,
        WEAK_EVIDENCE: 320,
        MODERATE_EVIDENCE: 110,
        STRONG_EVIDENCE: 60,
      },
      sector_distribution: [
        {
          sector: "Banking & Financial Services",
          pair_count: 100,
          avg_anticipation_score: 0.44,
          flagged_count: 18,
          classification_counts: { NO_EVIDENCE: 40, WEAK_EVIDENCE: 35, MODERATE_EVIDENCE: 15, STRONG_EVIDENCE: 10 },
        },
      ],
      window_stats_distribution: [
        {
          window: "[-30,-21]",
          mean_mar: 0.0012,
          mean_car: 0.0105,
          significant_pairs_count: 15,
          observation_count: 10,
        },
        {
          window: "[-30,-1]",
          mean_mar: 0.0018,
          mean_car: 0.042,
          significant_pairs_count: 45,
          observation_count: 30,
        },
      ],
      top_flagged_pairs: [
        {
          bill_id: "the-banking-laws-amendment-bill-2024",
          bill_title: "The Banking Laws (Amendment) Bill, 2024",
          company_isin: "INE062A01020",
          company_name: "State Bank of India",
          company_symbol: "SBIN",
          sector: "Banking & Financial Services",
          anticipation_score: 0.82,
          classification: "STRONG_EVIDENCE",
          detected_signals: ["Pre-event volume spike"],
        },
      ],
      disclaimer: MANDATORY_LEGAL_DISCLAIMER,
    });

    (anticipationApi.listAnticipation as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [
        {
          bill_id: "the-banking-laws-amendment-bill-2024",
          bill_title: "The Banking Laws (Amendment) Bill, 2024",
          company_isin: "INE062A01020",
          company_name: "State Bank of India",
          company_symbol: "SBIN",
          sector: "Banking & Financial Services",
          anticipation_score: 0.82,
          classification: "STRONG_EVIDENCE",
          anticipation_flag: true,
          confidence: "HIGH",
          market_signal_score: 0.79,
          information_signal_score: 0.85,
          evidence_count: 3,
          media_data_available: true,
          decision_reason: "Elevated trading activity aligned with public committee release.",
          detected_signals: ["Pre-event volume spike"],
        },
      ],
      total: 1,
      page: 1,
      limit: 25,
      pages: 1,
    });

    (billsApi.listBills as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [
        {
          bill_id: "karnataka-vs-bill-33-2024",
          title: "Karnataka Platform Based Gig Workers Bill, 2024",
          bill_number: "LA-33-2024",
          year: 2024,
          status: "ENACTED",
          jurisdiction: "state",
          state: "Karnataka",
          company_exposure_count: 5,
        },
      ],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    });

    (aiApi.ask as ReturnType<typeof vi.fn>).mockResolvedValue({
      content: "Empirical analysis confirms grounded statutory research findings.",
      success: true,
    });
  });

  it("1. Risk Intelligence (/risk) enforces editorial hierarchy, non-financial advice notice, and portfolio calculator", async () => {
    render(<RiskContent />);

    expect(screen.getByText(/Institutional Risk Analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/Regulatory Integrity Notice/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("4,700")).toBeInTheDocument();
      expect(screen.getByText("Very Low Risk")).toBeInTheDocument();
      expect(screen.getByText(/PARTIALLY PRICED IN/i)).toBeInTheDocument();
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    // Check Portfolio Calculator
    const isinInput = screen.getByPlaceholderText(/e.g. INE002A01018/i);
    fireEvent.change(isinInput, { target: { value: "INE062A01020, INTEL001" } });
    const computeBtn = screen.getByText("Compute Risk");
    fireEvent.click(computeBtn);

    await waitFor(() => {
      expect(screen.getByText("SUFFICIENT DATA")).toBeInTheDocument();
      expect(screen.getByText(/Qualitative Intelligence Entities in Portfolio/i)).toBeInTheDocument();
    });
  });

  it("2. Anticipation Intelligence (/anticipation) enforces verbatim legal disclaimers, neutral tiers, and evidence inspector", async () => {
    render(<AnticipationContent />);

    expect(screen.getByText(/Pre-Event Information Diffusion/i)).toBeInTheDocument();

    await waitFor(() => {
      const disclaimers = screen.getAllByText(new RegExp(MANDATORY_LEGAL_DISCLAIMER, "i"));
      expect(disclaimers.length).toBeGreaterThanOrEqual(2);
      expect(screen.getByText("940")).toBeInTheDocument();
      expect(screen.getByText("Strong Evidence")).toBeInTheDocument();
      expect(screen.getByText("[-30,-21]")).toBeInTheDocument();
      expect(screen.getByText(/Chronological Diffusion & Evidence Inspector/i)).toBeInTheDocument();
    });
  });

  it("3. State Intelligence Registry (/states) displays 4 pilot states, 0 stock predictions, and supports dual views", async () => {
    render(<StatesPage />);

    expect(screen.getByText("Sub-National Legislative Intelligence Registry")).toBeInTheDocument();
    expect(screen.getByText("Implemented States")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("44")).toBeInTheDocument();
    expect(screen.getByText("State Stock Predictions")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("24")).toBeInTheDocument();

    // Toggle Tabular Registry view
    const tableBtn = screen.getByRole("button", { name: "Tabular Registry" });
    fireEvent.click(tableBtn);

    expect(screen.getByText("State / Code")).toBeInTheDocument();
    expect(screen.getByText("Capital & Assembly")).toBeInTheDocument();
  });

  it("4. State Detail Dossier (/states/[state]) displays assembly acts and corporate operational footprint with firewall", async () => {
    const pageComponent = await StateDetailPage({
      params: Promise.resolve({ state: "Karnataka" }),
    });
    render(pageComponent);

    expect(screen.getByRole("heading", { level: 1, name: "Karnataka" })).toBeInTheDocument();
    expect(screen.getByText(/Karnataka Legislative Assembly/i)).toBeInTheDocument();
    expect(screen.getByText(/Market prediction is not currently available for State legislation/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Karnataka Platform Based Gig Workers Bill, 2024")).toBeInTheDocument();
      expect(screen.getByText(/Documented Corporate Operational Footprint in Karnataka/i)).toBeInTheDocument();
      expect(screen.getByText("Infosys Limited")).toBeInTheDocument();
    });
  });

  it("5. Verifies Canonical Frozen Baseline Hash remains exactly 50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7", () => {
    const manifestPath = path.resolve(__dirname, "../../../docs/production_baseline.json");
    expect(fs.existsSync(manifestPath)).toBe(true);

    const content = fs.readFileSync(manifestPath);
    const hash = crypto.createHash("sha256").update(content).digest("hex");

    expect(hash).toBe("50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7");
  });
});

