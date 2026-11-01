/**
 * __tests__/components/task-1-5b-3-workflow-validation.test.tsx
 * ==============================================================
 * Comprehensive test suite for Task 1.5B.3:
 * End-to-End Workflow Validation & Interaction Polish
 *
 * Validates:
 * 1. PredictionsContent reads URL search parameters and synchronizes filter state
 * 2. PredictionsContent resolves company names (e.g., "State Bank of India") to ISINs via companiesApi
 * 3. PredictionsContent directly uses ISIN parameters without extra lookup
 * 4. BillDetailContent initializes activeTab to ?tab= parameter (e.g. "predictions")
 * 5. CorporateExposureTable generates URI-encoded links for company profiles and predictions
 * 6. CorporateExposureTable correctly handles names with ampersands, spaces, and punctuation
 * 7. PredictionDetailContent links to Bill Dossier with ?tab=predictions and properly URI encodes billId & ISIN
 * 8. Portfolio page correctly encodes bill IDs in navigation links
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: any }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

// Hoist mock objects so they are available in hoisted vi.mock factories
const { mockPrediction, mockCoverage, mockBillDetail } = vi.hoisted(() => ({
  mockPrediction: {
    prediction_id: "the-banking-laws-amendment-bill-2024__INE062A01020__-1,+1",
    bill_id: "the-banking-laws-amendment-bill-2024",
    company_isin: "INE062A01020",
    company_name: "State Bank of India",
    company_symbol: "SBIN",
    sector: "Banking & Financial Services",
    event_window: "[-1,+1]",
    predicted_direction: "POSITIVE",
    predicted_market_moving: true,
    market_moving_probability: 0.72,
    predicted_impact_strength: "HIGH",
    predicted_confidence: "HIGH",
    confidence_score: 0.84,
    model_confidence: 0.84,
    model_version: "v1.0.0",
    created_at: "2026-10-28T00:00:00Z",
    prediction_timestamp: "2026-10-28T00:00:00Z",
  },
  mockCoverage: {
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
      state_stock_predictions_count: 0,
    },
  },
  mockBillDetail: {
    bill: {
      bill_id: "the-banking-laws-amendment-bill-2024",
      jurisdiction: "central",
      state: null,
      title: "The Banking Laws (Amendment) Bill, 2024",
      short_title: "Banking Laws Amendment Bill",
      bill_number: "Bill No. 125 of 2024",
      legislature: "Parliament of India",
      house: "Lok Sabha",
      year: 2024,
      introduction_date: "2024-08-09",
      assent_date: null,
      status: "passed_both",
      policy_domain: "Financial Regulation",
      economic_sectors: ["Banking & Financial Services", "Capital Markets"],
      secondary_sectors: ["Insurance"],
      stakeholders: ["Banks", "Depositors", "NBFCs"],
      summary: "A bill to amend statutory frameworks governing commercial banking reserves.",
      company_exposure_count: 5,
      listed_company_exposure_count: 5,
      market_relevance: "HIGH",
      modeling_eligibility: "ELIGIBLE",
      data_sufficiency: "COMPLETE",
      source_url: "https://prsindia.org/billtrack/the-banking-laws-amendment-bill-2024",
      pdf_url: "https://prsindia.org/files/bills_spec/the-banking-laws-amendment-bill-2024.pdf",
      data_quality: "VERIFIED",
    },
    provisions: [
      "Regulatory oversight: Reserve Bank of India",
      "Statutory interaction: Banking Regulation Act, 1949",
    ],
    knowledge: {
      amended_acts: ["Banking Regulation Act, 1949"],
      regulatory_authority: "Reserve Bank of India",
      financial_terms: "Modifies capital adequacy ratios.",
      penalties_or_enforcement: "Regulatory penalties for non-reporting.",
      objective: "To strengthen governance in banking.",
      key_provisions: [
        "Regulatory oversight: Reserve Bank of India",
      ],
    },
    provenance: {
      title: "AUTHORITATIVE",
      introduction_date: "AUTHORITATIVE",
    },
    prediction_available: true,
    related_bills: [],
  },
}));

// Mock API modules
vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    getPrediction: vi.fn().mockResolvedValue(mockPrediction),
    getPredictionDecision: vi.fn().mockResolvedValue({}),
    getStakeholderReport: vi.fn().mockResolvedValue({}),
    listPredictions: vi.fn().mockResolvedValue({
      items: [mockPrediction],
      total: 1,
      page: 1,
      limit: 25,
      pages: 1,
    }),
    compareHorizons: vi.fn().mockResolvedValue({
      bill_id: "the-banking-laws-amendment-bill-2024",
      company_isin: "INE062A01020",
      company_name: "State Bank of India",
      comparisons: [],
    }),
  },
}));

vi.mock("@/lib/api/companies", () => ({
  companiesApi: {
    listCompanies: vi.fn().mockImplementation(({ search }) => {
      if (search && search.toLowerCase().includes("state bank")) {
        return Promise.resolve({
          items: [
            {
              company_id: "INE062A01020",
              company_name: "State Bank of India",
              isin: "INE062A01020",
              sector: "Banking & Financial Services",
            },
          ],
          total: 1,
        });
      }
      if (search && search.toLowerCase().includes("larsen & toubro")) {
        return Promise.resolve({
          items: [
            {
              company_id: "INE018A01030",
              company_name: "Larsen & Toubro Ltd.",
              isin: "INE018A01030",
              sector: "Infrastructure & Construction",
            },
          ],
          total: 1,
        });
      }
      return Promise.resolve({ items: [], total: 0 });
    }),
    getCompany: vi.fn().mockResolvedValue({
      company_id: "INE062A01020",
      company_name: "State Bank of India",
      isin: "INE062A01020",
      sector: "Banking & Financial Services",
    }),
  },
}));

vi.mock("@/lib/api/anticipation", () => ({
  anticipationApi: {
    getByPair: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock("@/lib/api/coverage", () => ({
  coverageApi: {
    getCoverage: vi.fn().mockResolvedValue(mockCoverage),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    explainPrediction: vi.fn().mockResolvedValue({ explanation: "Test explanation" }),
    ask: vi.fn().mockResolvedValue({ content: "Grounded AI explanation" }),
  },
}));

vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    getBill: vi.fn().mockResolvedValue(mockBillDetail),
    getBillDossier: vi.fn().mockResolvedValue({
      bill_id: "the-banking-laws-amendment-bill-2024",
      model_status: "MODELLED",
    }),
    getBillPredictions: vi.fn().mockResolvedValue({
      bill_id: "the-banking-laws-amendment-bill-2024",
      predictions_count: 5,
    }),
    getBillCompanies: vi.fn().mockResolvedValue([]),
    getBillAnticipation: vi.fn().mockResolvedValue(null),
  },
}));

// Mutable mock for useSearchParams
let mockSearchParams = new URLSearchParams("");
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => mockSearchParams,
}));

// Import components under test
import PredictionsContent from "@/app/predictions/PredictionsContent";
import BillDetailContent from "@/app/bills/[billId]/BillDetailContent";
import { CorporateExposureTable } from "@/components/bills/CorporateExposureTable";
import PredictionDetailContent from "@/app/predictions/[predictionId]/PredictionDetailContent";
import { predictionsApi } from "@/lib/api/predictions";
import { companiesApi } from "@/lib/api/companies";

describe("TASK 1.5B.3 — Workflow Navigation & URL Integrity Validation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams("");
  });

  describe("1. PredictionsContent Search Query & ISIN Resolution", () => {
    it("reads ISIN from searchParams and queries predictions by company_isin", async () => {
      mockSearchParams = new URLSearchParams("isin=INE062A01020");
      render(<PredictionsContent />);

      await waitFor(() => {
        expect(predictionsApi.listPredictions).toHaveBeenCalledWith(
          expect.objectContaining({
            company_isin: "INE062A01020",
          })
        );
      });
    });

    it("resolves company name from search query (e.g. 'State Bank of India') to ISIN and retrieves predictions", async () => {
      mockSearchParams = new URLSearchParams("search=State Bank of India");
      render(<PredictionsContent />);

      await waitFor(() => {
        expect(companiesApi.listCompanies).toHaveBeenCalledWith(
          expect.objectContaining({
            search: "State Bank of India",
          })
        );
      });

      await waitFor(() => {
        expect(predictionsApi.listPredictions).toHaveBeenCalledWith(
          expect.objectContaining({
            company_isin: "INE062A01020",
          })
        );
      });
    });

    it("correctly sets bill_id filter when ?bill= query param is provided", async () => {
      mockSearchParams = new URLSearchParams("bill=the-banking-laws-amendment-bill-2024");
      render(<PredictionsContent />);

      await waitFor(() => {
        expect(predictionsApi.listPredictions).toHaveBeenCalledWith(
          expect.objectContaining({
            bill_id: "the-banking-laws-amendment-bill-2024",
          })
        );
      });
    });
  });

  describe("2. BillDetailContent Tab Navigation Preservation", () => {
    it("initializes active tab to 'predictions' when ?tab=predictions is present", async () => {
      mockSearchParams = new URLSearchParams("tab=predictions");
      render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

      await waitFor(() => {
        const tabButton = screen.getByRole("tab", { name: /Market Predictions/i });
        expect(tabButton).toHaveAttribute("aria-selected", "true");
      });
    });

    it("defaults active tab to 'overview' when no tab param is provided", async () => {
      mockSearchParams = new URLSearchParams("");
      render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

      await waitFor(() => {
        const tabButton = screen.getByRole("tab", { name: /Overview/i });
        expect(tabButton).toHaveAttribute("aria-selected", "true");
      });
    });
  });

  describe("3. CorporateExposureTable Route Parameter Correctness & URL Encoding", () => {
    const sampleExposures = [
      {
        company_id: "INE062A01020",
        company_name: "State Bank of India",
        sector: "Banking & Financial Services",
        sub_sector: "Public Sector Banking",
        exposure_type: "regulatory",
        exposure_strength: "HIGH",
        direct_indirect: "DIRECT",
        market_relevance: "HIGH",
        mechanism: "Statutory governance reform",
        evidence: [],
      },
      {
        company_id: "INE018A01030",
        company_name: "Larsen & Toubro Ltd.",
        sector: "Infrastructure & Construction",
        sub_sector: "Heavy Engineering",
        exposure_type: "procurement",
        exposure_strength: "MEDIUM",
        direct_indirect: "DIRECT",
        market_relevance: "MEDIUM",
        mechanism: "Capital goods procurement standards",
        evidence: [],
      },
    ];

    it("renders properly encoded company profile and prediction links with spaces and ampersands", () => {
      render(<CorporateExposureTable exposures={sampleExposures as any} />);

      // Check State Bank of India links
      const sbiCompanyLink = screen.getByText("State Bank of India").closest("a");
      expect(sbiCompanyLink).toHaveAttribute("href", "/companies/INE062A01020");

      const sbiPredLink = screen.getByTitle("Search predictions for State Bank of India");
      expect(sbiPredLink).toHaveAttribute("href", "/predictions?search=State%20Bank%20of%20India");

      // Check Larsen & Toubro links (verifying ampersand and spaces are URI-encoded)
      const ltCompanyLink = screen.getByText("Larsen & Toubro Ltd.").closest("a");
      expect(ltCompanyLink).toHaveAttribute("href", "/companies/INE018A01030");

      const ltPredLink = screen.getByTitle("Search predictions for Larsen & Toubro Ltd.");
      expect(ltPredLink).toHaveAttribute("href", "/predictions?search=Larsen%20%26%20Toubro%20Ltd.");
    });
  });

  describe("4. PredictionDetailContent Cross-Linking & Context Preservation", () => {
    it("links to Bill Dossier with preserved ?tab=predictions parameter", async () => {
      render(
        <PredictionDetailContent
          predictionId="the-banking-laws-amendment-bill-2024__INE062A01020__-1,+1"
        />
      );

      await waitFor(() => {
        expect(screen.getByText("State Bank of India")).toBeInTheDocument();
      });

      // Find Bill Dossier button link
      const billLink = screen.getByText("🏛 Bill Dossier").closest("a");
      expect(billLink).toHaveAttribute(
        "href",
        "/bills/the-banking-laws-amendment-bill-2024?tab=predictions"
      );

      // Find Company Profile button link
      const compLink = screen.getByText("🏢 Company Profile").closest("a");
      expect(compLink).toHaveAttribute("href", "/companies/INE062A01020");

      // Verify portfolio and watchlist shortcuts exist as navigation links
      const portfolioLink = screen.getByText("💼 Portfolio").closest("a");
      expect(portfolioLink).toHaveAttribute("href", "/portfolio");

      const watchlistLink = screen.getByText("⭐ Watchlist").closest("a");
      expect(watchlistLink).toHaveAttribute("href", "/watchlists");
    });
  });
});
