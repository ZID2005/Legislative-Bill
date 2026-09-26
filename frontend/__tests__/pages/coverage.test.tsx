/**
 * __tests__/pages/coverage.test.tsx
 * ===================================
 * Comprehensive unit and integration tests for Coverage page.
 *
 * Validates:
 * - Loading state with skeletons
 * - API error state
 * - Research Integrity Statement rendering
 * - Central Parliament coverage metrics (20 production bills, 47 companies, 4,700 predictions)
 * - State Legislatures coverage metrics (4 states, 44 bills, 0 state stock predictions)
 * - State Stock Predictions firewall badge & explanation
 * - Company coverage metrics (70 total, 47 quantitative, 23 qualitative)
 * - Platform total metrics
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

// Mock coverage API
vi.mock("@/lib/api/coverage", () => ({
  coverageApi: {
    getCoverage: vi.fn(),
  },
}));

import { CoverageContent } from "@/app/coverage/CoverageContent";
import { coverageApi } from "@/lib/api/coverage";
import type { CoverageReportResponse } from "@/types/api";

const mockCoverageData: CoverageReportResponse = {
  central: {
    production_bills: 20,
    total_bills_in_repo: 20,
    quantitative_companies: 47,
    bill_company_pairs: 940,
    predictions_count: 4700,
    decisions_count: 4700,
    anticipation_scores_count: 940,
    stakeholder_reports_count: 4700,
    event_windows_count: 4700,
  },
  state: {
    implemented_states_count: 4,
    implemented_states_list: ["Delhi", "Maharashtra", "Karnataka", "Tamil Nadu"],
    planned_states_count: 8,
    state_bills_count: 44,
    state_official_pdfs_count: 44,
    state_knowledge_records_count: 44,
    state_corporate_exposures_count: 88,
    state_stock_predictions_count: 0,
  },
  company: {
    total_companies: 70,
    quantitative_companies: 47,
    intelligence_companies: 19,
    reference_companies: 4,
  },
  unified: {
    total_legislative_records: 64,
    total_corporate_exposures: 88,
  },
};

describe("CoverageContent Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeletons initially", () => {
    vi.mocked(coverageApi.getCoverage).mockReturnValue(new Promise(() => {}));
    render(<CoverageContent />);

    expect(screen.getByRole("generic", { name: /loading coverage data/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Platform Coverage & Research Integrity/i })).toBeInTheDocument();
  });

  it("renders error state when coverage API fails", async () => {
    vi.mocked(coverageApi.getCoverage).mockRejectedValue(new Error("Database connection failed"));
    render(<CoverageContent />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/Failed to load coverage data/i)).toBeInTheDocument();
    expect(screen.getByText(/Database connection failed/i)).toBeInTheDocument();
  });

  it("renders research integrity notice and statement", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(mockCoverageData);
    render(<CoverageContent />);

    await waitFor(() => {
      expect(screen.getByRole("note", { name: /research integrity statement/i })).toBeInTheDocument();
    });

    expect(screen.getByText(/Research Integrity Statement/i)).toBeInTheDocument();
    expect(screen.getByText(/State stock predictions remain permanently and verifiably 0/i)).toBeInTheDocument();
  });

  it("renders Central Parliament coverage metrics", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(mockCoverageData);
    render(<CoverageContent />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Central Parliament/i })).toBeInTheDocument();
    });

    expect(screen.getByText("QUANTITATIVE MODELLED")).toBeInTheDocument();
    expect(screen.getByText("Production Bills")).toBeInTheDocument();
    expect(screen.getByText("Quantitative Companies")).toBeInTheDocument();
    expect(screen.getAllByText("4,700").length).toBeGreaterThan(0);
  });

  it("renders State Legislatures coverage with 0 state predictions guarantee", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(mockCoverageData);
    render(<CoverageContent />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /State Legislatures/i })).toBeInTheDocument();
    });

    expect(screen.getByText("LEGISLATIVE INTELLIGENCE")).toBeInTheDocument();
    expect(screen.getByText("Implemented States")).toBeInTheDocument();
    expect(screen.getByText("Delhi, Maharashtra, Karnataka, Tamil Nadu")).toBeInTheDocument();
    expect(screen.getByText("State Bills")).toBeInTheDocument();
    expect(screen.getByText("State Stock Predictions")).toBeInTheDocument();
    expect(screen.getByText("Always and verifiably 0. State monitoring does not generate predictions.")).toBeInTheDocument();
  });

  it("renders Company coverage metrics", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(mockCoverageData);
    render(<CoverageContent />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Company Coverage/i })).toBeInTheDocument();
    });

    expect(screen.getByText("Total Companies")).toBeInTheDocument();
    expect(screen.getByText("Quantitative")).toBeInTheDocument();
    expect(screen.getByText("Corporate Intelligence")).toBeInTheDocument();
    expect(screen.getByText("Reference")).toBeInTheDocument();
  });

  it("renders Unified Coverage summary cards", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(mockCoverageData);
    render(<CoverageContent />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Unified Coverage/i })).toBeInTheDocument();
    });

    expect(screen.getByText("Total Legislative Records")).toBeInTheDocument();
    expect(screen.getByText("Total Corporate Exposures")).toBeInTheDocument();
    expect(screen.getByText("64")).toBeInTheDocument();
    expect(screen.getAllByText("88").length).toBeGreaterThan(0);
  });

  it("confirms 0 state predictions is strictly enforced in the rendered output", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(mockCoverageData);
    render(<CoverageContent />);

    await waitFor(() => {
      expect(screen.getByText("Always and verifiably 0. State monitoring does not generate predictions.")).toBeInTheDocument();
    });

    // Verify there are no stock buy/sell/prediction badges for state bills
    expect(screen.queryByText(/buy/i)).toBeNull();
    expect(screen.queryByText(/sell/i)).toBeNull();
    expect(screen.queryByText(/outperform/i)).toBeNull();
  });
});
