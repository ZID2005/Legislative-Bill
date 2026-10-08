/**
 * __tests__/pages/companies.test.tsx
 * ===================================
 * Test suite for the Modern Institutional Corporate Intelligence Directory.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import CompaniesPage from "@/app/companies/page";
import { companiesApi } from "@/lib/api/companies";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock companiesApi
vi.mock("@/lib/api/companies", () => ({
  companiesApi: {
    listCompanies: vi.fn(),
  },
}));

const mockCompanies = [
  {
    company_id: "INE002A01018",
    company_name: "Reliance Industries Limited",
    ticker_nse: "RELIANCE",
    ticker_bse: "500325",
    isin: "INE002A01018",
    sector: "Energy & Utilities",
    industry: "Oil & Gas Refining",
    sub_industry: "Integrated Oil & Gas",
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
  {
    company_id: "NPCI001",
    company_name: "National Payments Corporation of India",
    ticker_nse: null,
    ticker_bse: null,
    isin: "IN_NPCI_001",
    sector: "Financial Services",
    industry: "Payments Infrastructure",
    sub_industry: "Retail Payments",
    entity_type: "quasi_public",
    universe_type: "intelligence",
    ownership_type: "consortium",
    is_active: true,
    listing_status: "Unlisted",
    hq_state: "Maharashtra",
    watchlist_eligible: true,
    is_quant_eligible: false,
    market_prediction_available: false,
    documented_exposure_count: 5,
  },
];

describe("Companies Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (companiesApi.listCompanies as any).mockResolvedValue({
      items: mockCompanies,
      total: 2,
      page: 1,
      size: 25,
      pages: 1,
    });
  });

  it("renders heading and 4 stat cards with 70/47/20 invariants", async () => {
    render(<CompaniesPage />);

    expect(screen.getByText("Corporate Intelligence Universe")).toBeInTheDocument();
    expect(screen.getAllByText("70").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("47").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("20").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("104")).toBeInTheDocument();
  });

  it("renders quantitative company with 5 Horizons prediction badge", async () => {
    render(<CompaniesPage />);

    await waitFor(() => {
      expect(screen.getByText("Reliance Industries Limited")).toBeInTheDocument();
      expect(screen.getByText("QUANTITATIVE")).toBeInTheDocument();
      expect(screen.getByText("5 Horizons")).toBeInTheDocument();
    });
  });

  it("renders intelligence company with FIREWALLED (KNOWLEDGE ONLY) badge", async () => {
    render(<CompaniesPage />);

    await waitFor(() => {
      expect(screen.getByText("National Payments Corporation of India")).toBeInTheDocument();
      expect(screen.getByText("INTELLIGENCE")).toBeInTheDocument();
      expect(screen.getByText("FIREWALLED (KNOWLEDGE ONLY)")).toBeInTheDocument();
    });
  });

  it("opens inspection ContextDrawer when Inspect button is clicked", async () => {
    render(<CompaniesPage />);

    await waitFor(() => {
      expect(screen.getByText("Reliance Industries Limited")).toBeInTheDocument();
    });

    const inspectButtons = screen.getAllByRole("button", { name: "Inspect" });
    fireEvent.click(inspectButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("ISIN: INE002A01018")).toBeInTheDocument();
      expect(screen.getByText("Open Full Company Dossier")).toBeInTheDocument();
    });
  });

  it("filters universe by tab selection", async () => {
    render(<CompaniesPage />);

    await waitFor(() => {
      expect(screen.getByText("Reliance Industries Limited")).toBeInTheDocument();
    });

    const intelTab = screen.getByRole("button", { name: /Intelligence Entities/i });
    fireEvent.click(intelTab);

    expect(companiesApi.listCompanies).toHaveBeenCalledWith(
      expect.objectContaining({
        universe_type: "intelligence",
      })
    );
  });
});
