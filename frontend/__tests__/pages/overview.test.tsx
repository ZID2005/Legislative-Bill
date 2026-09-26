/**
 * __tests__/pages/overview.test.tsx
 * ===================================
 * Comprehensive unit and integration tests for SaaS Overview page.
 * Validates:
 * - Loading state
 * - API error state with retry
 * - Real coverage baseline metrics rendering (20, 44, 47, 70, 66, 104)
 * - Three-tier capability rendering (L1, L2, L3)
 * - Statutory isolation guarantee (0 state stock predictions)
 * - Recent bills, market predictions snapshot, state pilots, corporate universe, and monitoring status
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

// Mock the useCoverage hook
vi.mock("@/hooks/useCoverage", () => ({
  useCoverage: vi.fn(),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock APIs
vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    listBills: vi.fn(),
  },
}));

vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    listPredictions: vi.fn(),
  },
}));

vi.mock("@/lib/api/companies", () => ({
  companiesApi: {
    listCompanies: vi.fn(),
  },
}));

vi.mock("@/lib/api/monitoring", () => ({
  monitoringApi: {
    getStatus: vi.fn(),
  },
}));

import OverviewContent from "@/app/overview/OverviewContent";
import { useCoverage } from "@/hooks/useCoverage";
import { billsApi } from "@/lib/api/bills";
import { predictionsApi } from "@/lib/api/predictions";
import { companiesApi } from "@/lib/api/companies";
import { monitoringApi } from "@/lib/api/monitoring";
import { ApiError } from "@/lib/errors";

const mockUseCoverage = useCoverage as ReturnType<typeof vi.fn>;
const mockListBills = billsApi.listBills as ReturnType<typeof vi.fn>;
const mockListPredictions = predictionsApi.listPredictions as ReturnType<typeof vi.fn>;
const mockListCompanies = companiesApi.listCompanies as ReturnType<typeof vi.fn>;
const mockGetMonitoringStatus = monitoringApi.getStatus as ReturnType<typeof vi.fn>;

const mockCoverageData = {
  central: {
    production_bills: 20,
    total_bills_in_repo: 22,
    quantitative_companies: 47,
    bill_company_pairs: 940,
    predictions_count: 4700,
    decisions_count: 4700,
    anticipation_scores_count: 940,
    stakeholder_reports_count: 14100,
    event_windows_count: 5,
  },
  state: {
    implemented_states_count: 4,
    planned_states_count: 24,
    implemented_states_list: ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"],
    state_bills_count: 44,
    state_official_pdfs_count: 44,
    state_knowledge_records_count: 44,
    state_corporate_exposures_count: 86,
    state_stock_predictions_count: 0,
  },
  company: {
    total_companies: 70,
    quantitative_companies: 47,
    intelligence_companies: 20,
    reference_companies: 3,
  },
  unified: {
    total_legislative_records: 66,
    total_corporate_exposures: 104,
  },
};

const mockBillsData = {
  items: [
    {
      bill_id: "the-bills-of-lading-bill-2024",
      jurisdiction: "central",
      state: null,
      title: "The Bills of Lading Bill, 2024",
      short_title: "Bills of Lading Bill",
      bill_number: "Bill No. 124 of 2024",
      legislature: "Parliament of India",
      house: "Lok Sabha",
      year: 2024,
      introduction_date: "2024-08-09",
      assent_date: null,
      status: "introduced",
      policy_domain: "Commerce & Maritime",
      economic_sectors: ["Infrastructure & Logistics", "Maritime"],
      secondary_sectors: [],
      stakeholders: ["Exporters", "Shipping Lines"],
      summary: "Consolidates and amends law relating to bills of lading.",
      company_exposure_count: 3,
      listed_company_exposure_count: 3,
      market_relevance: "HIGH",
      modeling_eligibility: "ELIGIBLE",
      data_sufficiency: "COMPLETE",
      source_url: "https://sansad.in",
      pdf_url: null,
      data_quality: "VERIFIED",
    },
  ],
  total: 1,
  page: 1,
  limit: 6,
  pages: 1,
};

const mockPredictionsData = {
  items: [
    {
      prediction_id: "pred-001",
      bill_id: "the-bills-of-lading-bill-2024",
      company_isin: "INE002A01018",
      company_name: "Reliance Industries",
      company_symbol: "RELIANCE",
      event_window: "[-1,+1]",
      predicted_direction: "POSITIVE",
      predicted_market_moving: true,
      market_moving_probability: 0.82,
      predicted_impact_strength: "HIGH",
      predicted_confidence: "HIGH",
      confidence_score: 0.87,
      model_version: "v1.0",
      created_at: "2026-09-18T12:00:00Z",
    },
  ],
  total: 1,
  page: 1,
  limit: 6,
  pages: 1,
};

const mockCompaniesData = {
  items: [
    {
      company_id: "INE002A01018",
      company_name: "Reliance Industries Limited",
      ticker_nse: "RELIANCE",
      ticker_bse: "500325",
      isin: "INE002A01018",
      sector: "Energy & Petrochemicals",
      industry: "Oil & Gas",
      sub_industry: "Refining",
      entity_type: "corporate",
      universe_type: "quantitative",
      ownership_type: "private",
      is_active: true,
      listing_status: "Listed",
      hq_state: "Maharashtra",
      watchlist_eligible: true,
      is_quant_eligible: true,
      market_prediction_available: true,
      documented_exposure_count: 8,
    },
  ],
  total: 1,
  page: 1,
  limit: 6,
  pages: 1,
};

const mockMonitoringStatus = {
  system_status: "OPERATIONAL",
  total_sources: 5,
  enabled_sources: 5,
  last_run_id: "run-001",
  last_run_timestamp: "2026-09-19T06:00:00Z",
  sources_summary: [],
};

describe("Overview Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListBills.mockResolvedValue(mockBillsData);
    mockListPredictions.mockResolvedValue(mockPredictionsData);
    mockListCompanies.mockResolvedValue(mockCompaniesData);
    mockGetMonitoringStatus.mockResolvedValue(mockMonitoringStatus);
  });

  it("shows loading state when coverage is being fetched", () => {
    mockUseCoverage.mockReturnValue({
      coverage: null,
      loading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<OverviewContent />);
    expect(screen.queryByText("India Legislative Intelligence")).not.toBeInTheDocument();
  });

  it("shows error state when coverage API fails", () => {
    const mockError = ApiError.fromStatus(500);
    mockUseCoverage.mockReturnValue({
      coverage: null,
      loading: false,
      error: mockError,
      refetch: vi.fn(),
    });

    render(<OverviewContent />);
    expect(screen.getByText(/Unable to load data/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("renders Hero Header and Quick Actions", () => {
    mockUseCoverage.mockReturnValue({
      coverage: mockCoverageData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<OverviewContent />);

    expect(screen.getByText("India Legislative Intelligence")).toBeInTheDocument();
    expect(
      screen.getByText("Understand legislation. Trace economic exposure. See documented market relevance.")
    ).toBeInTheDocument();

    expect(screen.getByText("🔍 Explore Bills")).toBeInTheDocument();
    expect(screen.getByText("🏢 Explore Companies")).toBeInTheDocument();
    expect(screen.getByText("📈 View Predictions")).toBeInTheDocument();
    expect(screen.getByText("🤖 Ask AI Copilot")).toBeInTheDocument();
  });

  it("renders real coverage baseline cards (20, 44, 47, 70, 66, 104)", () => {
    mockUseCoverage.mockReturnValue({
      coverage: mockCoverageData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<OverviewContent />);

    // Central bills
    expect(screen.getAllByText("20").length).toBeGreaterThanOrEqual(1);
    // State bills
    expect(screen.getAllByText("44").length).toBeGreaterThanOrEqual(1);
    // Quant companies
    expect(screen.getAllByText("47").length).toBeGreaterThanOrEqual(1);
    // Total companies
    expect(screen.getByText("70")).toBeInTheDocument();
    // Unified legislative records
    expect(screen.getByText("66")).toBeInTheDocument();
    // Total exposures
    expect(screen.getByText("104")).toBeInTheDocument();
  });

  it("renders capability tiers with statutory isolation guarantee", () => {
    mockUseCoverage.mockReturnValue({
      coverage: mockCoverageData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<OverviewContent />);

    // L1 Central
    expect(screen.getByText("Central Parliament — Market Modelled")).toBeInTheDocument();
    // L2 State
    expect(screen.getByText("State Assemblies — Economic Intelligence")).toBeInTheDocument();
    // L3 Planned
    expect(screen.getByText("Union Roadmap — 24 Planned States")).toBeInTheDocument();

    // Statutory guarantee
    expect(screen.getAllByText(/Statutory Isolation Guarantee/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/0 stock predictions exist for State legislation/i)).toBeInTheDocument();
  });

  it("renders secondary feeds: recent bills, predictions, and monitoring status", async () => {
    mockUseCoverage.mockReturnValue({
      coverage: mockCoverageData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<OverviewContent />);

    await waitFor(() => {
      expect(screen.getByText("Bills of Lading Bill")).toBeInTheDocument();
      expect(screen.getByText("RELIANCE")).toBeInTheDocument();
      expect(screen.getByText("Reliance Industries Limited")).toBeInTheDocument();
      expect(screen.getByText("OPERATIONAL")).toBeInTheDocument();
    });
  });
});
