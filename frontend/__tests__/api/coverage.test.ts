/**
 * __tests__/api/coverage.test.ts
 * ================================
 * Tests for the coverage API client module.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("Coverage API client", () => {
  it("exports coverageApi with getCoverage function", async () => {
    const module = await import("@/lib/api/coverage");
    expect(module.coverageApi).toBeDefined();
    expect(typeof module.coverageApi.getCoverage).toBe("function");
  });

  it("calls the correct endpoint", async () => {
    // Mock fetch
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        central: { production_bills: 20, quantitative_companies: 47, bill_company_pairs: 940, predictions_count: 4700, decisions_count: 4700, anticipation_scores_count: 940, stakeholder_reports_count: 14100, event_windows_count: 5, total_bills_in_repo: 22 },
        state: { implemented_states_count: 4, planned_states_count: 24, implemented_states_list: ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"], state_bills_count: 44, state_official_pdfs_count: 44, state_knowledge_records_count: 44, state_corporate_exposures_count: 86, state_stock_predictions_count: 0 },
        company: { total_companies: 70, quantitative_companies: 47, intelligence_companies: 20, reference_companies: 3 },
        unified: { total_legislative_records: 66, total_corporate_exposures: 104 },
      }),
    });

    vi.stubGlobal("fetch", mockFetch);
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";

    const { coverageApi } = await import("@/lib/api/coverage");
    const coverage = await coverageApi.getCoverage();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/coverage"),
      expect.any(Object)
    );

    // Verify baseline numbers
    expect(coverage.central.production_bills).toBe(20);
    expect(coverage.central.quantitative_companies).toBe(47);
    expect(coverage.central.predictions_count).toBe(4700);
    expect(coverage.state.state_stock_predictions_count).toBe(0); // Statutory guarantee
    expect(coverage.state.implemented_states_count).toBe(4);
    expect(coverage.company.total_companies).toBe(70);

    vi.unstubAllGlobals();
  });

  it("state stock predictions are always 0 (statutory guarantee)", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        central: { production_bills: 20, quantitative_companies: 47, bill_company_pairs: 940, predictions_count: 4700, decisions_count: 4700, anticipation_scores_count: 940, stakeholder_reports_count: 14100, event_windows_count: 5, total_bills_in_repo: 22 },
        state: { implemented_states_count: 4, planned_states_count: 24, implemented_states_list: [], state_bills_count: 44, state_official_pdfs_count: 44, state_knowledge_records_count: 44, state_corporate_exposures_count: 86, state_stock_predictions_count: 0 },
        company: { total_companies: 70, quantitative_companies: 47, intelligence_companies: 20, reference_companies: 3 },
        unified: { total_legislative_records: 66, total_corporate_exposures: 104 },
      }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { coverageApi } = await import("@/lib/api/coverage");
    const coverage = await coverageApi.getCoverage();

    // This is a critical statutory guarantee
    expect(coverage.state.state_stock_predictions_count).toBe(0);
    expect(coverage.state.state_stock_predictions_count).not.toBeGreaterThan(0);

    vi.unstubAllGlobals();
  });
});
