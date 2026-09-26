/**
 * __tests__/pages/industry-detail.test.tsx
 * =========================================
 * Comprehensive test suite for the Industry Intelligence Dossier.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import IndustryDetailContent from "@/app/industry/[industryId]/IndustryDetailContent";
import type { IndustryDossierResponse } from "@/types/api";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock industries API
vi.mock("@/lib/api/industries", () => ({
  industriesApi: {
    getIndustry: vi.fn(),
    listIndustries: vi.fn(),
    getIndustryBills: vi.fn(),
    getIndustryCompanies: vi.fn(),
  },
}));

// Mock AI API
vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
    explainBill: vi.fn(),
    explainCompany: vi.fn(),
    explainCompanyBill: vi.fn(),
  },
}));

const { industriesApi } = await import("@/lib/api/industries");
const { aiApi } = await import("@/lib/api/ai");

const MOCK_QUANT_DOSSIER: IndustryDossierResponse = {
  industry_id: "pharmaceuticals",
  name: "Pharmaceuticals",
  sector: "Healthcare & Pharmaceuticals",
  coverage_level: 1,
  description: "Indian pharmaceuticals sector is heavily impacted by central price controls and drug quality standards.",
  total_bills_count: 4,
  central_bills_count: 3,
  state_bills_count: 1,
  total_companies_count: 5,
  quantitative_companies_count: 4,
  intelligence_companies_count: 1,
  reference_companies_count: 0,
  central_exposures_count: 3,
  state_exposures_count: 1,
  market_analysis_available: true,
  dominant_mechanism: "compliance",
  facts: [
    "4 legislative instruments enacted (3 Central, 1 State).",
    "5 corporate exposures registered across NSE/BSE and MCA-21.",
  ],
  derived: [
    "High exposure concentration in active pharmaceutical ingredient (API) manufacturers.",
  ],
  interpretations: [
    "Tightening quality norms favor large listed exporters with existing USFDA clearance.",
  ],
  predictions: [
    "Central market analytics indicate moderate negative short-term margin compression across 4 quantitative stocks.",
  ],
  central_bills: [
    {
      bill_id: "BILL-2023-DRUGS-01",
      bill_title: "Drugs, Medical Devices and Cosmetics Bill, 2023",
      jurisdiction: "CENTRAL",
      state: null,
      policy_domain: "Health & Pharmaceuticals",
      legislative_status: "PASSED",
      exposure_strength: "HIGH",
      economic_mechanism: "compliance",
      provisions_summary: "Comprehensive revision of drug quality standards and clinical trial licensing.",
      exposed_company_ids: ["SUNPHARMA"],
      exposed_company_names: ["Sun Pharmaceutical Industries Ltd"],
      provenance_sources: ["Gazette of India"],
    },
  ],
  state_bills: [
    {
      bill_id: "STATE-MH-2023-01",
      bill_title: "Maharashtra Medical Supplies Procurement Authority Act, 2023",
      jurisdiction: "STATE",
      state: "Maharashtra",
      policy_domain: "Health Procurement",
      legislative_status: "ENACTED",
      exposure_strength: "MEDIUM",
      economic_mechanism: "fiscal_procurement",
      provisions_summary: "Centralized state-level drug rate contracting and supply auditing.",
      exposed_company_ids: ["SUNPHARMA"],
      exposed_company_names: ["Sun Pharmaceutical Industries Ltd"],
      provenance_sources: ["Maharashtra State Gazette"],
    },
  ],
  quantitative_companies: [
    {
      company_id: "SUNPHARMA",
      company_name: "Sun Pharmaceutical Industries Ltd",
      ticker_nse: "SUNPHARMA",
      ticker_bse: "524715",
      sector: "Healthcare & Pharmaceuticals",
      industry: "Pharmaceuticals",
      universe_type: "QUANTITATIVE",
      entity_type: "Listed Public Company",
      ownership_type: "Private",
      listing_status: "LISTED",
      is_quant_eligible: true,
      market_prediction_available: true,
      exposure_count: 2,
      exposure_strength: "HIGH",
      direct_indirect: "DIRECT",
      primary_mechanism: "compliance",
      market_relevance: "HIGH",
      evidence_reference: "Annual Report 2023",
    },
  ],
  intelligence_companies: [
    {
      company_id: "INTEL-PHARMA-01",
      company_name: "Bharat Serums & Vaccines Research",
      ticker_nse: null,
      ticker_bse: null,
      sector: "Healthcare & Pharmaceuticals",
      industry: "Pharmaceuticals",
      universe_type: "INTELLIGENCE",
      entity_type: "Unlisted Public Company",
      ownership_type: "Private",
      listing_status: "UNLISTED",
      is_quant_eligible: false,
      market_prediction_available: false,
      exposure_count: 1,
      exposure_strength: "HIGH",
      direct_indirect: "DIRECT",
      primary_mechanism: "licensing",
      market_relevance: "MEDIUM",
      evidence_reference: "MCA-21 Filings",
    },
  ],
  reference_companies: [],
  transmission_chains: [
    [
      {
        stage: "LEGISLATION",
        title: "Statutory Anchor",
        description: "Drugs and Cosmetics Amendment mandate for Schedule M revised standards.",
        badge: "FACT",
      },
      {
        stage: "ECONOMIC_MECHANISM",
        title: "Compliance Channel",
        description: "Mandatory qualification of all manufacturing facilities within 12 months.",
        badge: "DERIVED",
      },
    ],
  ],
  active_mechanisms: ["compliance", "fiscal_procurement"],
  market_intelligence: {
    modeled: true,
    notice: "Central econometric projections active.",
    quantitative_companies_count: 1,
    event_windows: ["5d", "10d", "30d", "60d", "90d"],
    total_predictions: 5,
    positive_count: 1,
    negative_count: 3,
    neutral_count: 1,
    sample_predictions: [
      {
        prediction_id: "PRED-001",
        bill_id: "BILL-2023-DRUGS-01",
        company_isin: "INE044A01036",
        event_window: "90d",
        predicted_direction: "NEGATIVE",
        predicted_confidence: "0.84",
        impact_strength: "HIGH",
      },
    ],
  },
  state_intelligence: {
    state_bills_count: 1,
    states_covered: ["Maharashtra"],
    state_stock_predictions: 0,
    firewall_statement: "State legislative bills have strictly 0 stock market predictions under the constitutional firewall.",
    bills: [],
  },
  risk_summary: {
    epistemic_badge: "DERIVED",
    explanation: "Moderate regulatory compliance risk concentrated in small-batch formulation units.",
    risk_band_distribution: { LOW: 1, MEDIUM: 2, HIGH: 1 },
    high_risk_count: 1,
  },
  anticipation_summary: {
    epistemic_badge: "DERIVED",
    verbatim_disclaimer: "Anticipation classifications are based on statistical market diffusion models and do not indicate non-public information flow or insider trading.",
    diffusion_tier_distribution: { LOW: 0, MODERATE: 1, HIGH: 0 },
    flagged_pairs_count: 1,
  },
  related_industries: [
    {
      industry_id: "biotechnology",
      name: "Biotechnology",
      sector: "Healthcare & Pharmaceuticals",
      related_bills_count: 2,
    },
  ],
  provenance_sources: [
    {
      source: "Ministry of Health and Family Welfare Gazette Notifications",
      source_type: "OFFICIAL_REGISTRY",
      verification_status: "VERIFIED",
      evidence_text: "Schedule M revised GMP mandate published in the Official Gazette.",
      verified_at: "2024-03-15",
    },
  ],
};

const MOCK_INTEL_DOSSIER: IndustryDossierResponse = {
  ...MOCK_QUANT_DOSSIER,
  industry_id: "gig-economy-platforms",
  name: "Gig Economy Platforms",
  sector: "Consumer / Digital",
  coverage_level: 2,
  market_analysis_available: false,
  quantitative_companies_count: 0,
  intelligence_companies_count: 2,
  central_bills_count: 0,
  state_bills_count: 3,
  central_bills: [],
  quantitative_companies: [],
  market_intelligence: {
    modeled: false,
    notice: "Quantitative market predictions disabled for intelligence-only corporate universe.",
    quantitative_companies_count: 0,
    event_windows: [],
    sample_predictions: [],
  },
  anticipation_summary: {
    epistemic_badge: "DERIVED",
    verbatim_disclaimer: "Anticipation classifications are based on statistical market diffusion models and do not indicate non-public information flow or insider trading.",
    diffusion_tier_distribution: {},
    flagged_pairs_count: 0,
  },
};

describe("IndustryDetailContent (Industry Intelligence Dossier)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a complete quantitative industry dossier with all sections", async () => {
    vi.mocked(industriesApi.getIndustry).mockResolvedValue(MOCK_QUANT_DOSSIER);

    render(<IndustryDetailContent industryId="pharmaceuticals" />);

    // Wait for full render
    expect(await screen.findByRole("heading", { name: "Pharmaceuticals" })).toBeDefined();

    // Check capability level 1 badge
    expect(screen.getByText(/Market Modelled/i)).toBeDefined();

    // Check Epistemic 4-way separation sections
    expect(screen.getByText("Verified Legal & Entity Facts")).toBeDefined();
    expect(screen.getByText("Derived Aggregations & Transmissions")).toBeDefined();
    expect(screen.getByText("Economic & Regulatory Interpretation")).toBeDefined();
    expect(screen.getByText("Econometric Model Projections")).toBeDefined();

    // Check Legislative footprint (Central Bill)
    expect(screen.getByText("Drugs, Medical Devices and Cosmetics Bill, 2023")).toBeDefined();

    // Check Corporate exposure
    expect(screen.getAllByText("Sun Pharmaceutical Industries Ltd").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Bharat Serums & Vaccines Research").length).toBeGreaterThan(0);

    // Check Economic Transmission Map
    expect(screen.getByText("Statutory Anchor")).toBeDefined();

    // Check Market Intelligence
    expect(screen.getByText("Central Market Intelligence")).toBeDefined();

    // Check Anticipation section and legal disclaimer
    expect(
      screen.getByText(/Anticipation classifications are based on statistical market diffusion models/i)
    ).toBeDefined();

    // Check Peer industries
    expect(screen.getByText("Biotechnology")).toBeDefined();
  });

  it("engages IntelligenceCompanyFirewall for intelligence-only industries (Mode B)", async () => {
    vi.mocked(industriesApi.getIndustry).mockResolvedValue(MOCK_INTEL_DOSSIER);

    render(<IndustryDetailContent industryId="gig-economy-platforms" />);

    expect(await screen.findByRole("heading", { name: "Gig Economy Platforms" })).toBeDefined();

    // Expect Level 2 badge
    expect(screen.getAllByText(/Legislative Intelligence/i).length).toBeGreaterThan(0);

    // Market intelligence firewall message should be displayed
    expect(
      screen.getByText(/Market prediction unavailable for this entity/i)
    ).toBeDefined();
  });

  it("switches tabs in the Legislative Footprint between Central and State bills", async () => {
    vi.mocked(industriesApi.getIndustry).mockResolvedValue(MOCK_QUANT_DOSSIER);

    render(<IndustryDetailContent industryId="pharmaceuticals" />);

    expect(await screen.findByRole("heading", { name: "Pharmaceuticals" })).toBeDefined();
    expect(screen.getByText("Drugs, Medical Devices and Cosmetics Bill, 2023")).toBeDefined();

    // Switch to State Assemblies tab
    const stateTab = screen.getByRole("button", { name: /State Assemblies/i });
    fireEvent.click(stateTab);

    // State bill should now be visible
    expect(
      screen.getByText("Maharashtra Medical Supplies Procurement Authority Act, 2023")
    ).toBeDefined();
  });

  it("submits grounded AI analyst query when prompt chip is clicked", async () => {
    vi.mocked(industriesApi.getIndustry).mockResolvedValue(MOCK_QUANT_DOSSIER);
    vi.mocked(aiApi.ask).mockResolvedValue({
      content: "The primary transmission channel is through statutory price capping under DPCO Schedule M.",
      context_type: "industry",
      context_id: "pharmaceuticals",
      persona: "INVESTOR",
      operation: "ASK",
      success: true,
      is_cached: false,
      disclaimer: "Not financial advice.",
      provenance_sources: ["Drugs and Cosmetics Bill, 2023"],
    });

    render(<IndustryDetailContent industryId="pharmaceuticals" />);

    expect(await screen.findByRole("heading", { name: "Pharmaceuticals" })).toBeDefined();

    // Find prompt chip
    const chip = screen.getByRole("button", {
      name: /Explain the economic transmission mechanisms/i,
    });
    fireEvent.click(chip);

    // Verify ask API called
    await waitFor(() => {
      expect(aiApi.ask).toHaveBeenCalledWith(
        expect.objectContaining({
          context_type: "industry",
          context_id: "pharmaceuticals",
        })
      );
    });

    // Response rendered
    expect(
      await screen.findByText(/The primary transmission channel is through statutory price capping/i)
    ).toBeDefined();
  });

  it("displays 404 state when industry is not found", async () => {
    vi.mocked(industriesApi.getIndustry).mockRejectedValueOnce({
      status: 404,
      message: "Industry nonexistent-ind not found",
    });

    render(<IndustryDetailContent industryId="nonexistent-ind" />);

    await waitFor(() => {
      expect(screen.getByText(/Industry Dossier Not Found/i)).toBeDefined();
    });

    expect(screen.getByText(/Back to Industries/i)).toBeDefined();
  });

  it("displays error banner with retry button on network failure", async () => {
    vi.mocked(industriesApi.getIndustry).mockRejectedValueOnce(
      new Error("Network connection lost")
    );

    render(<IndustryDetailContent industryId="pharmaceuticals" />);

    expect(await screen.findByText(/Network connection lost/i)).toBeDefined();

    const retryBtn = screen.getByRole("button", { name: "Retry" });
    expect(retryBtn).toBeDefined();

    // Allow retry to succeed
    vi.mocked(industriesApi.getIndustry).mockResolvedValue(MOCK_QUANT_DOSSIER);
    fireEvent.click(retryBtn);

    expect(await screen.findByRole("heading", { name: "Pharmaceuticals" })).toBeDefined();
  });
});
