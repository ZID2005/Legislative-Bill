/**
 * __tests__/components/task-1-5b-2-workflow-connectivity.test.tsx
 * ==============================================================
 * Verification test suite for Task 1.5B.2:
 * Seance Dashboard Unification & Workflow Connectivity
 *
 * Verifies:
 * 1. Root Landing Page (/) Unified Decision Hubs switcher & cross-links (/workspace, /overview, /portfolio)
 * 2. Overview (/overview) cross-links to Workspace and Portfolio
 * 3. Workspace (/workspace) cross-links to Portfolio and Overview
 * 4. Bill Corporate Exposure table inline prediction link and drawer cross-links (Company, Predictions, Portfolio)
 * 5. Bill Central Prediction Section direct links to Company Profile and Prediction Dossier
 * 6. Company Exposure Matrix statutory distinction: Central bill (Market Modelled ↗) vs State bill (Statutory Fact firewall)
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: any }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

const mockCoverageStats = {
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

// Mock @/lib/hooks/useCoverage (used in Landing Page)
vi.mock("@/lib/hooks/useCoverage", () => ({
  useCoverage: () => ({
    data: {
      central_bills_count: 20,
      state_bills_count: 44,
      total_bills_count: 64,
      quant_modelled_companies_count: 47,
      total_predictions_count: 4700,
      total_companies_count: 70,
      total_exposures_count: 104,
      model_accuracy_pct: 78.4,
      directional_accuracy_pct: 78.4,
      high_impact_accuracy_pct: 82.1,
      calibration_brier_score: 0.162,
      last_updated: "2026-10-28T00:00:00Z",
    },
    loading: false,
    error: null,
  }),
}));

// Mock @/hooks/useCoverage (used in OverviewContent)
vi.mock("@/hooks/useCoverage", () => ({
  useCoverage: () => ({
    coverage: mockCoverageStats,
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("@/lib/hooks/useWorkspace", () => ({
  useWorkspace: () => ({
    savedBills: [
      {
        bill_id: "the-banking-laws-amendment-bill-2024",
        jurisdiction: "central",
        title: "The Banking Laws (Amendment) Bill, 2024",
        status: "passed_both",
        economic_sectors: ["Banking & Financial Services"],
        saved_at: "2026-10-28T10:00:00Z",
      },
    ],
    savedPredictions: [],
    recentSearches: [],
    savedNotes: [],
    savedCompanies: [],
    isBillSaved: () => true,
    isPredictionSaved: () => false,
    isCompanySaved: () => false,
    saveBill: vi.fn(),
    removeBill: vi.fn(),
    savePrediction: vi.fn(),
    removePrediction: vi.fn(),
    saveCompany: vi.fn(),
    removeCompany: vi.fn(),
    addRecentSearch: vi.fn(),
    clearRecentSearches: vi.fn(),
    saveNote: vi.fn(),
    deleteNote: vi.fn(),
    totalSavedCount: 1,
  }),
}));

vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    listBills: vi.fn().mockResolvedValue({
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
          status: "passed_both",
          economic_sectors: ["Shipping"],
          secondary_sectors: [],
          stakeholders: [],
          summary: "Summary text",
          company_exposure_count: 5,
          listed_company_exposure_count: 5,
          market_relevance: "HIGH",
          modeling_eligibility: "ELIGIBLE",
          data_sufficiency: "COMPLETE",
          data_quality: "VERIFIED",
        },
      ],
      total: 1,
    }),
  },
}));

vi.mock("@/lib/api/companies", () => ({
  companiesApi: {
    listCompanies: vi.fn().mockResolvedValue({
      items: [
        {
          company_id: "INE002A01018",
          company_name: "Reliance Industries Limited",
          ticker_nse: "RELIANCE",
          ticker_bse: "500325",
          isin: "INE002A01018",
          sector: "Energy & Petrochemicals",
          universe_type: "quantitative",
          is_active: true,
          listing_status: "Listed",
          is_quant_eligible: true,
          market_prediction_available: true,
          documented_exposure_count: 8,
        },
      ],
      total: 1,
    }),
  },
}));

vi.mock("@/lib/api/monitoring", () => ({
  monitoringApi: {
    getStatus: vi.fn().mockResolvedValue({
      system_status: "OPERATIONAL",
      total_sources: 5,
      enabled_sources: 5,
      last_run_id: "run-001",
      last_run_timestamp: "2026-09-19T06:00:00Z",
      sources_summary: [],
    }),
  },
}));

vi.mock("@/lib/api/overview", () => ({
  overviewApi: {
    getOverviewSummary: vi.fn().mockResolvedValue({
      total_bills: 64,
      central_bills: 20,
      state_bills: 44,
      quant_companies: 47,
      total_predictions: 4700,
      last_updated: "2026-10-28T00:00:00Z",
    }),
  },
}));

vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    getPredictionDecision: vi.fn().mockResolvedValue(null),
    getPrediction: vi.fn().mockResolvedValue(null),
    getStakeholderReportByKey: vi.fn().mockResolvedValue(null),
    listPredictions: vi.fn().mockResolvedValue({
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
    }),
  },
}));

import LandingPage from "@/app/page";
import OverviewContent from "@/app/overview/OverviewContent";
import WorkspacePage from "@/app/workspace/page";
import { CorporateExposureTable } from "@/components/bills/CorporateExposureTable";
import { CentralPredictionSection } from "@/components/bills/CentralPredictionSection";
import { CompanyExposureMatrix } from "@/components/companies/CompanyExposureMatrix";
import type {
  BillSummaryItem,
  BillPredictionStatusResponse,
  BillCompanyExposure,
} from "@/types/api";

describe("Task 1.5B.2 — Dashboard Unification & Workflow Connectivity", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("1. Root Landing Page (/) Navigation & Unified Hubs", () => {
    it("renders quick-switcher to Workspace, Overview, and Portfolio", () => {
      render(<LandingPage />);

      expect(screen.getByText(/Unified Decision Hubs/i)).toBeInTheDocument();

      const workspaceLink = screen.getByRole("link", { name: /Legislative Workspace/i });
      expect(workspaceLink).toHaveAttribute("href", "/workspace");

      const overviewLink = screen.getByRole("link", { name: /System Observatory/i });
      expect(overviewLink).toHaveAttribute("href", "/overview");

      const portfolioLink = screen.getByRole("link", { name: /Portfolio Legislative Exposure/i });
      expect(portfolioLink).toHaveAttribute("href", "/portfolio");
    });

    it("renders dynamic coverage metrics from hook", () => {
      render(<LandingPage />);
      expect(screen.getByText("4,700")).toBeInTheDocument();
      expect(screen.getByText("47")).toBeInTheDocument();
    });
  });

  describe("2. Overview (/overview) & Workspace (/workspace) Hub Cross-links", () => {
    it("renders cross-links from Overview to Personal Workspace and Portfolio Exposure", async () => {
      render(<OverviewContent />);

      await waitFor(() => {
        const workspaceLink = screen.getByRole("link", { name: /Personal Workspace →/i });
        expect(workspaceLink).toHaveAttribute("href", "/workspace");

        const portfolioLink = screen.getByRole("link", { name: /Portfolio Exposure →/i });
        expect(portfolioLink).toHaveAttribute("href", "/portfolio");
      });
    });

    it("renders cross-links from Workspace action bar to Portfolio and Overview", () => {
      render(<WorkspacePage />);

      const portfolioLinks = screen.getAllByRole("link", { name: /Portfolio Exposure/i });
      expect(portfolioLinks.some((l) => l.getAttribute("href") === "/portfolio")).toBe(true);

      const overviewLinks = screen.getAllByRole("link", { name: /Overview/i });
      expect(overviewLinks.some((l) => l.getAttribute("href") === "/overview")).toBe(true);
    });
  });

  describe("3. Bill Corporate Exposure Table Workflow Connections", () => {
    const mockExposures: BillCompanyExposure[] = [
      {
        bill_id: "the-banking-laws-amendment-bill-2024",
        bill_title: "The Banking Laws (Amendment) Bill, 2024",
        company_id: "INE002A01018",
        company_name: "State Bank of India",
        bill_number: "Bill No. 125 of 2024",
        jurisdiction: "central",
        state: null,
        bill_status: "passed_both",
        sector: "Banking & Financial Services",
        sub_sector: "Public Sector Banks",
        business_activity: "Retail & Corporate Banking",
        exposure_type: "DIRECT",
        exposure_direction: "POSITIVE",
        exposure_strength: "HIGH",
        direct_indirect: "DIRECT",
        geographic_scope: "National",
        mechanism: "Regulatory reserve threshold reduction",
        market_relevance: "HIGH",
        confidence: "HIGH",
        has_evidence: true,
        evidence: [
          {
            claim: "Section 42 amendment directly impacts public sector banks liquidity management.",
            reference: "Section 42",
            statutory_section: "42",
          },
        ],
        source_urls: ["https://sbi.co.in"],
      },
    ];

    it("renders inline Predictions link for exposed company", () => {
      render(<CorporateExposureTable exposures={mockExposures} />);

      const predLink = screen.getByRole("link", { name: /Predictions ↗/i });
      expect(predLink).toHaveAttribute("href", "/predictions?search=State%20Bank%20of%20India");
    });

    it("renders company profile, predictions, and portfolio cross-links when evidence drawer opens", () => {
      render(<CorporateExposureTable exposures={mockExposures} />);

      // Click "Details" / "Toggle evidence" button to expand row
      const expandBtn = screen.getByRole("button", { name: /Toggle evidence for State Bank of India/i });
      fireEvent.click(expandBtn);

      const profileLink = screen.getByRole("link", { name: /🏢 View Company Profile →/i });
      expect(profileLink).toHaveAttribute("href", "/companies/INE002A01018");

      const predDossierLink = screen.getByRole("link", { name: /📈 Check Market Predictions →/i });
      expect(predDossierLink).toHaveAttribute("href", "/predictions?search=State%20Bank%20of%20India");

      const portfolioLink = screen.getByRole("link", { name: /💼 Check Portfolio Exposure/i });
      expect(portfolioLink).toHaveAttribute("href", "/portfolio");
    });
  });

  describe("4. Central Prediction Section Links to Company & Prediction Dossier", () => {
    const mockBill: BillSummaryItem = {
      bill_id: "the-banking-laws-amendment-bill-2024",
      jurisdiction: "central",
      title: "The Banking Laws (Amendment) Bill, 2024",
      short_title: "Banking Laws Amendment Bill",
      bill_number: "Bill No. 125 of 2024",
      legislature: "Parliament of India",
      house: "Lok Sabha",
      year: 2024,
      status: "passed_both",
      economic_sectors: ["Banking & Financial Services"],
      secondary_sectors: [],
      stakeholders: [],
      summary: "Amendments to commercial banking regulation.",
      company_exposure_count: 5,
      listed_company_exposure_count: 5,
      market_relevance: "HIGH",
      modeling_eligibility: "ELIGIBLE",
      data_sufficiency: "COMPLETE",
      data_quality: "VERIFIED",
    };

    const mockPredictionStatus: BillPredictionStatusResponse = {
      available: true,
      has_predictions: true,
      bill_id: "the-banking-laws-amendment-bill-2024",
      jurisdiction: "central",
      total: 1,
      predictions: [
        {
          prediction_id: "pred-sbin-2024",
          bill_id: "the-banking-laws-amendment-bill-2024",
          company_isin: "INE002A01018",
          company_name: "State Bank of India",
          company_symbol: "SBIN",
          event_window: "[-1,+1]",
          predicted_direction: "POSITIVE",
          predicted_market_moving: true,
          market_moving_probability: 0.72,
          predicted_impact_strength: "HIGH",
          predicted_confidence: "HIGH",
          model_confidence: 0.88,
          model_version: "v1.0.0",
        },
      ],
      items: [],
    };

    it("links company name to company profile and provides direct Dossier ↗ link", () => {
      render(
        <CentralPredictionSection
          bill={mockBill}
          predictionStatus={mockPredictionStatus}
        />
      );

      // Company name links to /companies/INE002A01018
      const companyLink = screen.getByRole("link", { name: /State Bank of India/i });
      expect(companyLink).toHaveAttribute("href", "/companies/INE002A01018");

      // Dossier link navigates directly to /predictions/pred-sbin-2024
      const dossierLink = screen.getByRole("link", { name: /Dossier ↗/i });
      expect(dossierLink).toHaveAttribute("href", "/predictions/pred-sbin-2024");
    });
  });

  describe("5. Company Exposure Matrix Statutory Context & Cross-links", () => {
    const mockCentralExposure: BillCompanyExposure = {
      bill_id: "the-banking-laws-amendment-bill-2024",
      bill_title: "The Banking Laws (Amendment) Bill, 2024",
      company_id: "sbin",
      company_name: "State Bank of India",
      bill_number: "Bill No. 125 of 2024",
      jurisdiction: "central",
      state: null,
      bill_status: "passed_both",
      sector: "Banking & Financial Services",
      sub_sector: "Public Sector Banks",
      business_activity: "Retail & Corporate Banking",
      exposure_type: "DIRECT",
      exposure_direction: "POSITIVE",
      exposure_strength: "HIGH",
      direct_indirect: "DIRECT",
      geographic_scope: "National",
      mechanism: "Direct reserve requirement alteration",
      market_relevance: "HIGH",
      confidence: "HIGH",
      has_evidence: true,
      evidence: [],
      source_urls: [],
    };

    const mockStateExposure: BillCompanyExposure = {
      bill_id: "bihar-agricultural-produce-bill-2024",
      bill_title: "The Bihar Agricultural Produce Bill, 2024",
      company_id: "sbin",
      company_name: "State Bank of India",
      bill_number: "Bill No. 12 of 2024",
      jurisdiction: "state",
      state: "Bihar",
      bill_status: "passed_both",
      sector: "Agriculture & Rural",
      sub_sector: "Rural Credit",
      business_activity: "Agricultural Produce Trading",
      exposure_type: "INDIRECT",
      exposure_direction: "NEUTRAL",
      exposure_strength: "MODERATE",
      direct_indirect: "INDIRECT",
      geographic_scope: "Statewide (Bihar)",
      mechanism: "Rural branch compliance requirements",
      market_relevance: "MEDIUM",
      confidence: "HIGH",
      has_evidence: true,
      evidence: [],
      source_urls: [],
    };

    it("distinguishes Central modelled bill with Market Modelled link and State bill with statutory badge", () => {
      render(
        <CompanyExposureMatrix
          exposures={[mockCentralExposure, mockStateExposure]}
        />
      );

      // Central bill has "Market Modelled ↗" link to the bill's predictions tab
      const centralMarketLink = screen.getByRole("link", { name: /• Market Modelled ↗/i });
      expect(centralMarketLink).toHaveAttribute(
        "href",
        "/bills/the-banking-laws-amendment-bill-2024?tab=predictions"
      );

      // State bill displays statutory fact disclaimer badge without stock prediction link
      expect(screen.getByText(/• Statutory Fact \(0 Stock Predictions\)/i)).toBeInTheDocument();
    });
  });
});
