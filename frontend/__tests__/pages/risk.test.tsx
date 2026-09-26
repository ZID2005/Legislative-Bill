/**
 * __tests__/pages/risk.test.tsx
 * ==============================
 * Unit and integration tests for Institutional Risk Analytics (/risk).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
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

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
  },
}));

import RiskContent from "@/app/risk/RiskContent";
import { riskApi } from "@/lib/api/risk";
import { watchlistsApi } from "@/lib/api/watchlists";
import { aiApi } from "@/lib/api/ai";

const mockGetRiskSummary = riskApi.getRiskSummary as ReturnType<typeof vi.fn>;
const mockListRiskBills = riskApi.listRiskBills as ReturnType<typeof vi.fn>;
const mockListRiskCompanies = riskApi.listRiskCompanies as ReturnType<typeof vi.fn>;
const mockAnalyzePortfolio = riskApi.analyzePortfolioRisk as ReturnType<typeof vi.fn>;
const mockListWatchlists = watchlistsApi.listWatchlists as ReturnType<typeof vi.fn>;
const mockAskAi = aiApi.ask as ReturnType<typeof vi.fn>;

const sampleRiskSummary = {
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
    {
      sector: "Energy",
      avg_risk_score: 0.48,
      record_count: 450,
      band_distribution: { VERY_LOW: 60, LOW: 120, MODERATE: 180, HIGH: 70, VERY_HIGH: 20 },
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
  disclaimer: "Institutional risk disclaimer",
};

const sampleBills = [
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
];

const sampleCompanies = [
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
];

const sampleWatchlists = [
  {
    watchlist_id: "wl_01",
    user_id: "user_01",
    tenant_id: "default",
    name: "Core Nifty Banks",
    items_count: 5,
    items: [],
    rules: [],
    is_default: true,
    is_active: true,
    created_at: "2024-12-01T00:00:00Z",
    updated_at: "2024-12-01T00:00:00Z",
  },
];

const samplePortfolioResponse = {
  selected_companies_count: 2,
  modeled_companies_count: 1,
  unmodeled_companies_count: 1,
  total_exposure_records: 100,
  avg_portfolio_risk_score: 0.53,
  portfolio_risk_band: "MODERATE",
  has_sufficient_data: true,
  data_status: "SUFFICIENT_DATA",
  risk_band_distribution: { VERY_LOW: 10, LOW: 20, MODERATE: 50, HIGH: 15, VERY_HIGH: 5 },
  sector_breakdown: [],
  jurisdiction_breakdown: {},
  companies: [
    {
      company_isin: "INE062A01020",
      company_name: "State Bank of India",
      company_symbol: "SBIN",
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
      company_symbol: "QUALX",
      sector: "Infrastructure",
      universe_type: "INTELLIGENCE_ONLY",
      is_modeled: false,
      record_count: 0,
    },
  ],
  message: "Portfolio evaluation successful",
  disclaimer: "Portfolio disclaimer",
};

describe("Institutional Risk Analytics (/risk)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetRiskSummary.mockResolvedValue(sampleRiskSummary);
    mockListRiskBills.mockResolvedValue(sampleBills);
    mockListRiskCompanies.mockResolvedValue(sampleCompanies);
    mockListWatchlists.mockResolvedValue(sampleWatchlists);
    mockAnalyzePortfolio.mockResolvedValue(samplePortfolioResponse);
    mockAskAi.mockResolvedValue({
      content: "Banking sector risk is moderately elevated due to compliance adaptation.",
      success: true,
    });
  });

  it("renders risk summary header, 5 deterministic risk bands, and pricing-in metrics", async () => {
    render(<RiskContent />);

    expect(screen.getByText(/Institutional Risk Analytics/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("4,700")).toBeInTheDocument();
      expect(screen.getByText("Very Low Risk")).toBeInTheDocument();
      expect(screen.getByText("High Risk")).toBeInTheDocument();
      expect(screen.getByText("Very High Risk")).toBeInTheDocument();
      expect(screen.getByText(/PARTIALLY PRICED IN/i)).toBeInTheDocument();
    });
  });

  it("renders tabbed bill risk profiles and switches to company risk profiles", async () => {
    render(<RiskContent />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
      expect(screen.getByText("Inspect Bill →")).toBeInTheDocument();
    });

    const companyTab = screen.getByText(/🏢 Company Risk Profiles/i);
    fireEvent.click(companyTab);

    await waitFor(() => {
      expect(screen.getByText("State Bank of India")).toBeInTheDocument();
      expect(screen.getByText("Profile →")).toBeInTheDocument();
    });
  });

  it("computes portfolio risk and warns about qualitative unmodeled entities", async () => {
    render(<RiskContent />);

    await waitFor(() => {
      expect(screen.getByText(/Portfolio Legislative Risk Aggregation/i)).toBeInTheDocument();
    });

    // Enter ISINs
    const isinInput = screen.getByPlaceholderText(/e.g. INE002A01018/i);
    fireEvent.change(isinInput, { target: { value: "INE062A01020, INTEL001" } });

    const computeBtn = screen.getByText("Compute Risk");
    fireEvent.click(computeBtn);

    await waitFor(() => {
      expect(mockAnalyzePortfolio).toHaveBeenCalled();
      expect(screen.getByText("SUFFICIENT DATA")).toBeInTheDocument();
      expect(screen.getAllByText("53.0%").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Qualitative Intelligence Entities in Portfolio/i)).toBeInTheDocument();
    });
  });


  it("triggers AI risk analyst inquiry", async () => {
    render(<RiskContent />);

    await waitFor(() => {
      expect(screen.getByText(/AI Legislative Risk Analyst/i)).toBeInTheDocument();
    });

    const askBtn = screen.getByRole("button", { name: "Analyze" });
    fireEvent.click(askBtn);

    await waitFor(() => {
      expect(mockAskAi).toHaveBeenCalled();
      expect(screen.getByText(/Banking sector risk is moderately elevated/i)).toBeInTheDocument();
    });
  });
});
