/**
 * __tests__/pages/anticipation.test.tsx
 * =====================================
 * Unit and integration tests for Pre-Event Information Diffusion (/anticipation).
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
vi.mock("@/lib/api/anticipation", () => ({
  anticipationApi: {
    getAnticipationSummary: vi.fn(),
    listAnticipation: vi.fn(),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
  },
}));

import AnticipationContent from "@/app/anticipation/AnticipationContent";
import { anticipationApi } from "@/lib/api/anticipation";
import { aiApi } from "@/lib/api/ai";

const mockGetSummary = anticipationApi.getAnticipationSummary as ReturnType<typeof vi.fn>;
const mockListAnticipation = anticipationApi.listAnticipation as ReturnType<typeof vi.fn>;
const mockAskAi = aiApi.ask as ReturnType<typeof vi.fn>;

const MANDATORY_LEGAL_DISCLAIMER =
  "Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law.";

const sampleSummary = {
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
      detected_signals: ["Pre-event volume spike", "Public consultation coverage"],
    },
  ],
  disclaimer: MANDATORY_LEGAL_DISCLAIMER,
};

const sampleTableData = {
  items: [
    {
      bill_id: "the-banking-laws-amendment-bill-2024",
      bill_title: "The Banking Laws (Amendment) Bill, 2024",
      company_isin: "INE062A01020",
      company_name: "State Bank of India",
      company_symbol: "SBIN",
      sector: "Banking & Financial Services",
      official_introduction_date: "2024-08-09",
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
};

describe("Pre-Event Information Diffusion Dashboard (/anticipation)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSummary.mockResolvedValue(sampleSummary);
    mockListAnticipation.mockResolvedValue(sampleTableData);
    mockAskAi.mockResolvedValue({
      content: "Information diffusion diagnostics show aggregate public information absorption.",
      success: true,
    });
  });

  it("renders mandatory verbatim institutional disclaimer prominently at both top and bottom", async () => {
    render(<AnticipationContent />);

    expect(screen.getByText(/Pre-Event Information Diffusion/i)).toBeInTheDocument();

    await waitFor(() => {
      const disclaimers = screen.getAllByText(new RegExp(MANDATORY_LEGAL_DISCLAIMER, "i"));
      expect(disclaimers.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("renders verified 940 pairs coverage baseline and 4 neutral tiers", async () => {
    render(<AnticipationContent />);

    await waitFor(() => {
      expect(screen.getByText("940")).toBeInTheDocument();
      expect(screen.getByText("No Evidence")).toBeInTheDocument();
      expect(screen.getByText("Weak Evidence")).toBeInTheDocument();
      expect(screen.getByText("Moderate Evidence")).toBeInTheDocument();
      expect(screen.getByText("Strong Evidence")).toBeInTheDocument();
    });
  });

  it("renders pre-event trading windows CAR statistics", async () => {
    render(<AnticipationContent />);

    await waitFor(() => {
      expect(screen.getByText("[-30,-21]")).toBeInTheDocument();
      expect(screen.getByText("[-30,-1]")).toBeInTheDocument();
      expect(screen.getByText("1.05%")).toBeInTheDocument();
      expect(screen.getByText("4.20%")).toBeInTheDocument();
    });
  });

  it("renders the 940-pair diffusion matrix with flagged filter and action links", async () => {
    render(<AnticipationContent />);

    await waitFor(() => {
      expect(screen.getAllByText("State Bank of India").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("82.0%").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("STRONG EVIDENCE").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("FLAG")).toBeInTheDocument();
      expect(screen.getByText("Predictions →")).toBeInTheDocument();
    });


    // Toggle flagged only
    const flaggedCheckbox = screen.getByLabelText(/Show Flagged Only/i);
    fireEvent.click(flaggedCheckbox);

    await waitFor(() => {
      expect(mockListAnticipation).toHaveBeenCalledWith(
        expect.objectContaining({ flagged_only: true })
      );
    });
  });

  it("triggers AI diffusion analyst inquiry", async () => {
    render(<AnticipationContent />);

    await waitFor(() => {
      expect(screen.getByText(/AI Information Diffusion Analyst/i)).toBeInTheDocument();
    });

    const analyzeBtn = screen.getByRole("button", { name: "Analyze" });
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(mockAskAi).toHaveBeenCalled();
      expect(screen.getByText(/Information diffusion diagnostics show aggregate public information/i)).toBeInTheDocument();
    });
  });
});
