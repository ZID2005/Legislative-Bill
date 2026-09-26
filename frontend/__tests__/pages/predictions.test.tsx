/**
 * __tests__/pages/predictions.test.tsx
 * =====================================
 * Unit and integration tests for Prediction Analytics dashboard (/predictions).
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
vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    listPredictions: vi.fn(),
    compareHorizons: vi.fn(),
  },
}));

vi.mock("@/lib/api/coverage", () => ({
  coverageApi: {
    getCoverage: vi.fn(),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
  },
}));

import PredictionsContent from "@/app/predictions/PredictionsContent";
import { predictionsApi } from "@/lib/api/predictions";
import { coverageApi } from "@/lib/api/coverage";
import { aiApi } from "@/lib/api/ai";

const mockListPredictions = predictionsApi.listPredictions as ReturnType<typeof vi.fn>;
const mockCompareHorizons = predictionsApi.compareHorizons as ReturnType<typeof vi.fn>;
const mockGetCoverage = coverageApi.getCoverage as ReturnType<typeof vi.fn>;
const mockAskAi = aiApi.ask as ReturnType<typeof vi.fn>;

const sampleCoverage = {
  central: {
    production_bills: 20,
    total_bills_in_repo: 20,
    quantitative_companies: 47,
    bill_company_pairs: 940,
    predictions_count: 4700,
    decisions_count: 4700,
    anticipation_scores_count: 940,
    stakeholder_reports_count: 14100,
    event_windows_count: 5,
  },
  state: {
    implemented_states_count: 3,
    planned_states_count: 25,
    implemented_states_list: ["karnataka", "maharashtra", "delhi"],
    state_bills_count: 10,
    state_official_pdfs_count: 10,
    state_knowledge_records_count: 10,
    state_corporate_exposures_count: 35,
    state_stock_predictions_count: 0,
  },
  company: {
    total_companies: 157,
    quantitative_companies: 47,
    intelligence_companies: 110,
    reference_companies: 0,
  },
  unified: {
    total_legislative_records: 30,
    total_corporate_exposures: 975,
  },
};

const samplePredictionsList = {
  items: [
    {
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
    },
    {
      prediction_id: "pred_oil_reliance_01",
      bill_id: "the-oilfields-regulation-bill-2024",
      company_isin: "INE002A01018",
      company_name: "Reliance Industries Limited",
      company_symbol: "RELIANCE",
      sector: "Energy",
      event_window: "[-3,+3]",
      predicted_direction: "NEGATIVE",
      predicted_market_moving: false,
      market_moving_probability: 0.38,
      predicted_impact_strength: "MEDIUM",
      predicted_confidence: "MEDIUM",
      confidence_score: 0.58,
      model_version: "v1.0.0",
      created_at: "2024-12-01T00:00:00Z",
    },
  ],
  total: 2,
  page: 1,
  limit: 25,
  pages: 1,
};

const sampleHorizonComparison = {
  bill_id: "the-banking-laws-amendment-bill-2024",
  bill_title: "The Banking Laws (Amendment) Bill, 2024",
  company_isin: "INE002A01018",
  company_name: "Reliance Industries Limited",
  company_symbol: "RELIANCE",
  modeled_windows: ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"],
  comparisons: [
    {
      event_window: "[-1,+1]",
      is_modeled: true,
      predicted_direction: "POSITIVE",
      market_moving_probability: 0.65,
      predicted_impact_strength: "HIGH",
      confidence_score: 0.78,
      impact_score: 0.72,
      risk_score: 0.45,
      risk_category: "MODERATE",
      pricing_in_risk: "PARTIALLY_PRICED_IN",
    },
    {
      event_window: "[0,1]",
      is_modeled: false,
      note: "Short-horizon post-announcement window [0,1] is unmodeled in the validated Central dataset.",
    },
  ],
  unmodeled_note: "Temporal windows outside the 5 validated event horizons are unmodeled.",
};

describe("Prediction Analytics Dashboard (/predictions)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetCoverage.mockResolvedValue(sampleCoverage);
    mockListPredictions.mockResolvedValue(samplePredictionsList);
    mockCompareHorizons.mockResolvedValue(sampleHorizonComparison);
    mockAskAi.mockResolvedValue({
      content: "Econometric projections indicate positive abnormal returns for banking securities.",
      success: true,
    });
  });

  it("renders the dashboard header, epistemic badges, and coverage baseline", async () => {
    render(<PredictionsContent />);

    expect(screen.getByText(/Prediction Analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/Empirical market impact projections for Central Parliamentary legislation/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Production Bills")).toBeInTheDocument();
      expect(screen.getByText("20")).toBeInTheDocument();
      expect(screen.getByText("47")).toBeInTheDocument();
      expect(screen.getByText("4,700")).toBeInTheDocument();
    });
  });

  it("renders the quantitative prediction matrix with items, badges, and dossier link", async () => {
    render(<PredictionsContent />);

    await waitFor(() => {
      expect(screen.getAllByText("State Bank of India").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Reliance Industries Limited").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("[-1,+1]").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("POSITIVE").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("NEGATIVE").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("View Dossier →")[0]).toBeInTheDocument();
    });
  });

  it("triggers StatePredictionFirewall when switching jurisdiction to state", async () => {
    render(<PredictionsContent />);

    await waitFor(() => {
      expect(screen.getByText("🗺 State Assembly")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("🗺 State Assembly"));

    await waitFor(() => {
      expect(screen.getByText(/Statutory Firewall/i)).toBeInTheDocument();
    });
  });

  it("renders event-horizon comparison panel and displays unmodeled note for unmodeled horizon", async () => {
    render(<PredictionsContent />);

    await waitFor(() => {
      expect(screen.getByText(/Event-Horizon Comparison/i)).toBeInTheDocument();
    });

    // Click on unmodeled horizon [0,1]
    const unmodeledBtn = screen.getByText(/\[0,1\]/i);
    fireEvent.click(unmodeledBtn);

    await waitFor(() => {
      expect(screen.getByText(/Horizon \[0,1\] is not modeled in the validated dataset/i)).toBeInTheDocument();
    });
  });

  it("triggers AI Analyst explanation on demand", async () => {
    render(<PredictionsContent />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Analyze Current Enactment/i })).toBeInTheDocument();
    });

    const analyzeBtn = screen.getByRole("button", { name: /Analyze Current Enactment/i });
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(mockAskAi).toHaveBeenCalled();
      expect(screen.getByText(/Econometric projections indicate positive abnormal returns/i)).toBeInTheDocument();
    });
  });
});


