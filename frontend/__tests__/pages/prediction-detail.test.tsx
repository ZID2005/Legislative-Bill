/**
 * __tests__/pages/prediction-detail.test.tsx
 * ==========================================
 * Unit and integration tests for Single Prediction Dossier (/predictions/[predictionId]).
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
    getPrediction: vi.fn(),
    getPredictionDecision: vi.fn(),
    compareHorizons: vi.fn(),
    getStakeholderReport: vi.fn(),
  },
}));

vi.mock("@/lib/api/anticipation", () => ({
  anticipationApi: {
    getByPair: vi.fn(),
    getPairDetail: vi.fn(),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
  },
}));

import PredictionDetailContent from "@/app/predictions/[predictionId]/PredictionDetailContent";
import { predictionsApi } from "@/lib/api/predictions";
import { anticipationApi } from "@/lib/api/anticipation";
import { aiApi } from "@/lib/api/ai";

const mockGetPrediction = predictionsApi.getPrediction as ReturnType<typeof vi.fn>;
const mockGetDecision = predictionsApi.getPredictionDecision as ReturnType<typeof vi.fn>;
const mockCompareHorizons = predictionsApi.compareHorizons as ReturnType<typeof vi.fn>;
const mockGetReport = predictionsApi.getStakeholderReport as ReturnType<typeof vi.fn>;
const mockGetAnticipation = anticipationApi.getByPair as ReturnType<typeof vi.fn>;
const mockAskAi = aiApi.ask as ReturnType<typeof vi.fn>;

const samplePrediction = {
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

const sampleDecision = {
  decision_id: "dec_banking_sbi_01",
  prediction_id: "pred_banking_sbi_01",
  bill_id: "the-banking-laws-amendment-bill-2024",
  company_isin: "INE062A01020",
  event_window: "[-1,+1]",
  risk_category: "MODERATE",
  pricing_in_risk: "PARTIALLY_PRICED_IN",
  impact_category: "HIGH",
  impact_score: 0.72,
  risk_score: 0.45,
  decision_reason: "Standard cross-sectional risk weighting based on reserve ratio flexibility.",
  investor_summary: "Favorable capital adequacy flexibility for public sector banks.",
  business_summary: "Reduced regulatory friction on overnight reserve management.",
  public_summary: "Enhanced depositor safety standards.",
  created_at: "2024-12-01T00:00:00Z",
};

const sampleAnticipation = {
  bill_id: "the-banking-laws-amendment-bill-2024",
  company_isin: "INE062A01020",
  anticipation_score: 0.42,
  anticipation_tier: "WEAK_EVIDENCE",
  diffusion_index: 0.38,
  pre_event_volume_ratio: 0.45,
  pre_event_car: 0.012,
  leakage_indicator: false,
  evidence_summary: ["Public consultation paper published 30 days prior"],
};

const sampleHorizonComparison = {
  bill_id: "the-banking-laws-amendment-bill-2024",
  bill_title: "The Banking Laws (Amendment) Bill, 2024",
  company_isin: "INE062A01020",
  company_name: "State Bank of India",
  company_symbol: "SBIN",
  modeled_windows: ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"],
  comparisons: [
    { event_window: "[-1,+1]", is_modeled: true, predicted_direction: "POSITIVE" },
    { event_window: "[-3,+3]", is_modeled: true, predicted_direction: "POSITIVE" },
  ],
  unmodeled_note: "Temporal windows outside the 5 validated event horizons are unmodeled.",
};

const sampleReport = {
  report_id: "rep_01",
  bill_id: "the-banking-laws-amendment-bill-2024",
  company_isin: "INE062A01020",
  event_window: "[-1,+1]",
  stakeholder_type: "investor",
  executive_summary: "Positive outlook supported by improved regulatory clarity.",
  key_takeaways: ["Liquidity reserve flexibility", "Enhanced governance standards"],
  key_factors: ["Regulatory compliance cost reduction"],
  transmission_channels: ["Credit growth rate", "Net interest margins"],
  created_at: "2024-12-01T00:00:00Z",
};

describe("Single Prediction Dossier (/predictions/[predictionId])", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetPrediction.mockResolvedValue(samplePrediction);
    mockGetDecision.mockResolvedValue(sampleDecision);
    mockGetAnticipation.mockResolvedValue(sampleAnticipation);
    mockCompareHorizons.mockResolvedValue(sampleHorizonComparison);
    mockGetReport.mockResolvedValue(sampleReport);
    mockAskAi.mockResolvedValue({
      content: "Model forecasts reflect estimated abnormal returns over the [-1,+1] window.",
      success: true,
    });
  });

  it("renders the single prediction dossier with non-financial advice notice and epistemic zones", async () => {
    render(<PredictionDetailContent predictionId="pred_banking_sbi_01" />);

    await waitFor(() => {
      expect(screen.getByText("State Bank of India")).toBeInTheDocument();
      expect(screen.getByText(/Institutional Non-Financial Advice Notice/i)).toBeInTheDocument();
      expect(screen.getByText(/Projections are empirical econometric outputs/i)).toBeInTheDocument();
    });

    // Epistemic Zones
    expect(screen.getByText("Statutory & Entity Facts")).toBeInTheDocument();
    expect(screen.getByText("Model Projections")).toBeInTheDocument();
    expect(screen.getByText(/Decision Support & Risk Classification/i)).toBeInTheDocument();
    expect(screen.getByText(/Pre-Event Information Diffusion/i)).toBeInTheDocument();
  });

  it("renders decision support details and stakeholder reports", async () => {
    render(<PredictionDetailContent predictionId="pred_banking_sbi_01" />);

    await waitFor(() => {
      expect(screen.getByText("Risk Band: MODERATE")).toBeInTheDocument();
      expect(screen.getByText("PARTIALLY_PRICED_IN")).toBeInTheDocument();
      expect(screen.getByText("Favorable capital adequacy flexibility for public sector banks.")).toBeInTheDocument();
      expect(screen.getByText("Positive outlook supported by improved regulatory clarity.")).toBeInTheDocument();
    });
  });

  it("renders pre-event anticipation context with verbatim legal disclaimer", async () => {
    render(<PredictionDetailContent predictionId="pred_banking_sbi_01" />);

    await waitFor(() => {
      expect(screen.getByText("WEAK EVIDENCE")).toBeInTheDocument();
      expect(screen.getByText(/Pre-event diagnostics measure aggregate public information diffusion only/i)).toBeInTheDocument();
    });
  });

  it("renders 404 error state when prediction record does not exist", async () => {
    mockGetPrediction.mockRejectedValue(new Error("Record not found"));

    render(<PredictionDetailContent predictionId="invalid_id" />);

    await waitFor(() => {
      expect(screen.getByText("Prediction Record Not Found")).toBeInTheDocument();
      expect(screen.getByText("← Return to Predictions Dashboard")).toBeInTheDocument();
    });
  });
});
