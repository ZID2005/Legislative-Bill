/**
 * __tests__/pages/portfolio.test.tsx
 * ===================================
 * Focused Unit and Integration Test Suite for Task 1.8A:
 * Portfolio Legislative Exposure Workspace Redesign (/portfolio).
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import PortfolioPage from "@/app/portfolio/page";
import { portfolioApi } from "@/lib/api/portfolio";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: any }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

// Mock portfolioApi
vi.mock("@/lib/api/portfolio", () => ({
  portfolioApi: {
    listPortfolios: vi.fn(),
    getExposure: vi.fn(),
    addHolding: vi.fn(),
    removeHolding: vi.fn(),
    importHoldings: vi.fn(),
    explainRelevance: vi.fn(),
    generateReport: vi.fn(),
  },
}));

const mockPortfolios = [
  {
    portfolio_id: "pf_institutional_01",
    name: "Core Institutional Fund",
    description: "Primary equity holdings",
    is_default: true,
    is_active: true,
    holdings: [
      {
        holding_id: "h_sbi",
        portfolio_id: "pf_institutional_01",
        company_name: "State Bank of India",
        isin: "INE062A01020",
        ticker: "SBIN",
        sector: "Banking & Financial Services",
        industry: "Public Sector Banks",
        quantity: 10000,
        avg_purchase_price: 780.5,
      },
      {
        holding_id: "h_reliance",
        portfolio_id: "pf_institutional_01",
        company_name: "Reliance Industries Limited",
        isin: "INE002A01018",
        ticker: "RELIANCE",
        sector: "Energy",
        industry: "Oil & Gas Refining",
        quantity: 5000,
        avg_purchase_price: 2850.0,
      },
      {
        holding_id: "h_sci",
        portfolio_id: "pf_institutional_01",
        company_name: "Shipping Corporation of India",
        isin: "INE063A01019",
        ticker: "SCI",
        sector: "Transport & Logistics",
        industry: "Shipping",
        quantity: 2500,
        avg_purchase_price: 210.0,
      },
    ],
  },
];

const mockExposure = {
  portfolio_id: "pf_institutional_01",
  portfolio_name: "Core Institutional Fund",
  total_holdings: 3,
  exposed_holdings_count: 3,
  total_relevant_bills: 3,
  direct_bills_count: 2,
  high_relevance_bills_count: 1,
  moderate_relevance_bills_count: 0,
  indirect_bills_count: 0,
  informational_bills_count: 0,
  modelled_central_bills_count: 2,
  knowledge_only_bills_count: 0,
  state_bills_count: 1,
  holdings_exposure_map: {
    "State Bank of India": ["the-banking-laws-amendment-bill-2024"],
    "Shipping Corporation of India": ["the-merchant-shipping-bill-2024"],
    "Reliance Industries Limited": ["andhra-pradesh-clean-energy-duty-act-2024"],
  },
  sector_exposure_map: {
    "Banking & Financial Services": 1,
    "Transport & Logistics": 1,
    Energy: 1,
  },
  epistemic_notice: "Verified Central econometric event studies. State bills strictly carry zero stock predictions.",
  relevant_bills: [
    {
      bill_id: "the-banking-laws-amendment-bill-2024",
      bill_title: "The Banking Laws (Amendment) Bill, 2024",
      bill_number: "Bill No. 125 of 2024",
      jurisdiction: "central",
      status: "passed_both",
      relevance_tier: "DIRECT",
      primary_linkage_reason: "Direct statutory amendments to commercial banking reserves and tenure rules.",
      affected_companies: ["State Bank of India"],
      affected_sectors: ["Banking & Financial Services"],
      affected_industries: ["Public Sector Banks"],
      model_status: "MODELLED",
      authoritative_prediction: {
        isin: "INE062A01020",
        predicted_direction: "POSITIVE",
        predicted_confidence: "HIGH",
        event_window: "[-5,+5]",
        risk_category: "LOW RISK",
      },
      source_provenance: ["https://prsindia.org/billtrack/the-banking-laws-amendment-bill-2024"],
      latest_verified_update: "2024-09-18",
    },
    {
      bill_id: "the-merchant-shipping-bill-2024",
      bill_title: "The Merchant Shipping Bill, 2024",
      bill_number: "Bill No. 114 of 2024",
      jurisdiction: "central",
      status: "introduced",
      relevance_tier: "DIRECT",
      primary_linkage_reason: "Comprehensive modernization of vessel safety and coastal cabotage rules.",
      affected_companies: ["Shipping Corporation of India"],
      affected_sectors: ["Transport & Logistics"],
      affected_industries: ["Shipping"],
      model_status: "MODELLED",
      authoritative_prediction: {
        isin: "INE063A01019",
        predicted_direction: "POSITIVE",
        predicted_confidence: "HIGH",
        event_window: "[-1,+1]",
        risk_category: "MODERATE RISK",
      },
      source_provenance: ["https://prsindia.org/billtrack/the-merchant-shipping-bill-2024"],
      latest_verified_update: "2024-08-14",
    },
    {
      bill_id: "andhra-pradesh-clean-energy-duty-act-2024",
      bill_title: "Andhra Pradesh Clean Energy Duty Act, 2024",
      bill_number: "AP Act 12 of 2024",
      jurisdiction: "state",
      state: "Andhra Pradesh",
      status: "assented",
      relevance_tier: "HIGH RELEVANCE",
      primary_linkage_reason: "Captive generation tariffs affecting commercial refinery energy inputs.",
      affected_companies: ["Reliance Industries Limited"],
      affected_sectors: ["Energy"],
      affected_industries: ["Oil & Gas Refining"],
      model_status: "KNOWLEDGE ONLY",
      source_provenance: ["https://apegazette.cgg.gov.in"],
      latest_verified_update: "2024-10-02",
    },
  ],
};

describe("Portfolio Legislative Exposure Workspace (/portfolio)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (portfolioApi.listPortfolios as any).mockResolvedValue(mockPortfolios);
    (portfolioApi.getExposure as any).mockResolvedValue(mockExposure);
    (portfolioApi.explainRelevance as any).mockResolvedValue({
      bill_id: "the-banking-laws-amendment-bill-2024",
      relevance_tier: "DIRECT",
      explanation: "Direct regulatory amendment directly affecting public sector banking capital ratios.",
      affected_holdings: ["State Bank of India"],
      model_status: "MODELLED",
      grounded: true,
      disclaimer: "Non-financial decision support only.",
    });
    (portfolioApi.generateReport as any).mockResolvedValue({
      report_id: "rep_123",
      report_title: "My Legislative Impact Report — Core Institutional Fund",
      generated_at: "2026-10-29 18:00 IST",
      portfolio_summary: {
        total_holdings: 3,
        exposed_holdings_count: 3,
        total_relevant_bills: 3,
        direct_bills_count: 2,
      },
      relevant_bills: mockExposure.relevant_bills,
      disclaimers: [
        "Decision support intelligence only.",
        "State stock predictions strictly equal zero under methodology invariants.",
      ],
    });
  });

  it("1. renders executive workspace header, high-density metric summary, and governance banner", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Portfolio Legislative Exposure Workspace/i })
      ).toBeInTheDocument();
    });

    // High-density tabular metric strip checks
    expect(screen.getByText("Tracked Holdings")).toBeInTheDocument();
    expect(screen.getByText("3 Exposed")).toBeInTheDocument();
    expect(screen.getByText("Direct Exposures")).toBeInTheDocument();
    expect(screen.getByText("Chartered links")).toBeInTheDocument();

    // Decision-Support Governance banner check
    expect(screen.getByText(/Decision-Support Governance:/i)).toBeInTheDocument();
    expect(screen.getByText(/0 stock market predictions/i)).toBeInTheDocument();
  });

  it("2. renders two-column workspace layout with Holdings Roster and Legislative Impact Inspector", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /Tracked Holdings Roster/i })).toBeInTheDocument();
      expect(
        screen.getByRole("region", { name: /Legislative Impact Inspector/i })
      ).toBeInTheDocument();
    });

    const roster = screen.getByRole("region", { name: /Tracked Holdings Roster/i });
    expect(within(roster).getByText("State Bank of India")).toBeInTheDocument();
    expect(within(roster).getByText("Reliance Industries Limited")).toBeInTheDocument();
    expect(within(roster).getByText("Shipping Corporation of India")).toBeInTheDocument();
  });

  it("3. filters holdings in roster by search query", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /Tracked Holdings Roster/i })).toBeInTheDocument();
    });

    const roster = screen.getByRole("region", { name: /Tracked Holdings Roster/i });
    const searchInput = screen.getByPlaceholderText(/Filter by company, ISIN, sector/i);
    fireEvent.change(searchInput, { target: { value: "Shipping" } });

    expect(within(roster).getByText("Shipping Corporation of India")).toBeInTheDocument();
    expect(within(roster).queryByText("State Bank of India")).not.toBeInTheDocument();
    expect(within(roster).queryByText("Reliance Industries Limited")).not.toBeInTheDocument();
  });

  it("4. selecting a holding synchronizes and filters the Legislative Impact Inspector", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /Tracked Holdings Roster/i })).toBeInTheDocument();
    });

    const roster = screen.getByRole("region", { name: /Tracked Holdings Roster/i });
    const sbiRow = within(roster).getByText("State Bank of India");
    fireEvent.click(sbiRow);

    // Verify filter indicator appears
    expect(screen.getByText(/Filtering:/i)).toBeInTheDocument();

    const inspector = screen.getByRole("region", { name: /Legislative Impact Inspector/i });
    expect(within(inspector).getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();

    // Other bills should not be shown when SBI is selected
    expect(within(inspector).queryByText("The Merchant Shipping Bill, 2024")).not.toBeInTheDocument();
    expect(
      within(inspector).queryByText("Andhra Pradesh Clean Energy Duty Act, 2024")
    ).not.toBeInTheDocument();

    // Click "Show All" to reset
    const showAllBtn = screen.getByRole("button", { name: /^Show All$/i });
    fireEvent.click(showAllBtn);

    expect(within(inspector).getByText("The Merchant Shipping Bill, 2024")).toBeInTheDocument();
  });

  it("5. groups measures into supported relevance categories and supports tier filtering", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("Direct Statutory Exposures")).toBeInTheDocument();
      expect(screen.getByText("High Relevance Regulatory Shifts")).toBeInTheDocument();
    });

    // Click High Relevance filter
    const highBtn = screen.getByRole("button", { name: "HIGH" });
    fireEvent.click(highBtn);

    expect(screen.getByText("Andhra Pradesh Clean Energy Duty Act, 2024")).toBeInTheDocument();
    expect(
      screen.queryByText("The Banking Laws (Amendment) Bill, 2024")
    ).not.toBeInTheDocument();
  });

  it("6. displays authoritative Central model forecast and sub-national state firewall notice", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    // Central model output checks
    const centralOutputs = screen.getAllByText(/Authoritative Central Model Output \(Frozen Baseline\)/i);
    expect(centralOutputs.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("[-5,+5]")).toBeInTheDocument();
    expect(screen.getByText("LOW RISK")).toBeInTheDocument();

    // State legislation firewall notice checks
    expect(
      screen.getByText(/State Stock Predictions = 0 \(Statutory Methodology Invariant\)/i)
    ).toBeInTheDocument();
  });

  it("7. opens Grounded AI Explain Relevance modal when clicked", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const explainBtns = screen.getAllByRole("button", { name: /✦ Explain Relevance/i });
    fireEvent.click(explainBtns[0]);

    await waitFor(() => {
      expect(portfolioApi.explainRelevance).toHaveBeenCalledWith(
        "the-banking-laws-amendment-bill-2024"
      );
      expect(screen.getByText(/Grounded Relevance Analysis/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Direct regulatory amendment directly affecting public sector banking/i)
      ).toBeInTheDocument();
    });
  });

  it("8. generates Impact Report and toggles to printable view", async () => {
    render(<PortfolioPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Generate Report/i })).toBeInTheDocument();
    });

    const genBtn = screen.getByRole("button", { name: /Generate Report/i });
    fireEvent.click(genBtn);

    await waitFor(() => {
      expect(portfolioApi.generateReport).toHaveBeenCalledWith("pf_institutional_01");
      expect(
        screen.getByText(/My Legislative Impact Report — Core Institutional Fund/i)
      ).toBeInTheDocument();
      expect(screen.getByText("1. Portfolio Exposure Summary")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Print \/ Save PDF/i })).toBeInTheDocument();
    });
  });
});
