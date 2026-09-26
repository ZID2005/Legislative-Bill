/**
 * __tests__/pages/industries.test.tsx
 * ====================================
 * Comprehensive unit and integration test suite for the Industry Intelligence Discovery Page.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import IndustriesContent from "@/app/industries/IndustriesContent";
import type { IndustrySummaryItem, PaginatedResponse } from "@/types/api";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock industries API
vi.mock("@/lib/api/industries", () => ({
  industriesApi: {
    listIndustries: vi.fn(),
    getIndustry: vi.fn(),
    getIndustryBills: vi.fn(),
    getIndustryCompanies: vi.fn(),
  },
}));

const { industriesApi } = await import("@/lib/api/industries");

const MOCK_INDUSTRIES: IndustrySummaryItem[] = [
  {
    industry_id: "pharmaceuticals",
    name: "Pharmaceuticals",
    sector: "Healthcare & Pharmaceuticals",
    coverage_level: 1,
    related_bills_count: 5,
    central_exposures_count: 3,
    state_exposures_count: 2,
    exposed_companies_count: 7,
    quantitative_companies_count: 6,
    intelligence_companies_count: 1,
    market_analysis_available: true,
    sub_industries: ["Formulations", "APIs", "Contract Manufacturing"],
    economic_mechanisms: ["Price capping under DPCO", "Mandatory GMP compliance", "Clinical trial approvals"],
  },
  {
    industry_id: "gig-economy-platforms",
    name: "Gig Economy Platforms",
    sector: "Consumer / Digital",
    coverage_level: 2,
    related_bills_count: 3,
    central_exposures_count: 0,
    state_exposures_count: 3,
    exposed_companies_count: 2,
    quantitative_companies_count: 0,
    intelligence_companies_count: 2,
    market_analysis_available: false,
    sub_industries: ["Food Delivery", "Ride-Hailing", "Hyperlocal Delivery"],
    economic_mechanisms: ["Welfare cess per transaction", "Aggregator algorithmic registration"],
  },
  {
    industry_id: "banking",
    name: "Commercial Banking",
    sector: "Banking & Financial Services",
    coverage_level: 1,
    related_bills_count: 6,
    central_exposures_count: 6,
    state_exposures_count: 0,
    exposed_companies_count: 10,
    quantitative_companies_count: 10,
    intelligence_companies_count: 0,
    market_analysis_available: true,
    sub_industries: ["Public Sector Banks", "Private Sector Banks"],
    economic_mechanisms: ["Statutory liquidity ratios", "Priority sector lending"],
  },
];

const mockPaginated = (items: IndustrySummaryItem[]): PaginatedResponse<IndustrySummaryItem> => ({
  items,
  total: items.length,
  page: 1,
  limit: 100,
  pages: 1,
});

describe("IndustriesContent (Industry Discovery Page)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the discovery header, KPI metrics, and items", async () => {
    vi.mocked(industriesApi.listIndustries).mockResolvedValue(mockPaginated(MOCK_INDUSTRIES));

    render(<IndustriesContent />);

    // Header title and badge
    expect(screen.getByRole("heading", { name: "Industry Intelligence" })).toBeDefined();
    expect(screen.getByText("Platform Discovery")).toBeDefined();

    // Wait for data load
    await waitFor(() => {
      expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    });

    // Check items rendered
    expect(screen.getByText("Commercial Banking")).toBeDefined();
    expect(screen.getByText("Gig Economy Platforms")).toBeDefined();

    // Verify KPI cards
    expect(screen.getByText("Total Industries")).toBeDefined();
    expect(screen.getByText("Level 1 Modelled")).toBeDefined();
    expect(screen.getByText("Level 2 Intelligence")).toBeDefined();
  });

  it("renders industry cards with capability badges and transmission mechanisms", async () => {
    vi.mocked(industriesApi.listIndustries).mockResolvedValue(mockPaginated(MOCK_INDUSTRIES));

    render(<IndustriesContent />);

    await waitFor(() => {
      expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    });

    // Check capability level badges
    expect(screen.getAllByText(/Market Modelled/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Corporate Intelligence/i).length).toBeGreaterThan(0);

    // Check transmission mechanisms
    expect(screen.getByText(/Price capping under DPCO/i)).toBeDefined();
    expect(screen.getByText(/Welfare cess per transaction/i)).toBeDefined();
  });

  it("filters industries dynamically by search keyword", async () => {
    vi.mocked(industriesApi.listIndustries).mockResolvedValue(mockPaginated(MOCK_INDUSTRIES));

    render(<IndustriesContent />);

    await waitFor(() => {
      expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    });

    const searchInput = screen.getByLabelText(/Search Industry \/ Mechanism/i);
    fireEvent.change(searchInput, { target: { value: "gig" } });

    expect(screen.getByText("Gig Economy Platforms")).toBeDefined();
    expect(screen.queryByText("Pharmaceuticals")).toBeNull();
    expect(screen.queryByText("Commercial Banking")).toBeNull();
  });

  it("filters industries by sector dropdown", async () => {
    vi.mocked(industriesApi.listIndustries).mockResolvedValue(mockPaginated(MOCK_INDUSTRIES));

    render(<IndustriesContent />);

    await waitFor(() => {
      expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    });

    const sectorSelect = screen.getByLabelText(/Sector Classification/i);
    fireEvent.change(sectorSelect, { target: { value: "Healthcare & Pharmaceuticals" } });

    expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    expect(screen.queryByText("Gig Economy Platforms")).toBeNull();
    expect(screen.queryByText("Commercial Banking")).toBeNull();
  });

  it("filters industries by jurisdiction tab and shows statutory notice", async () => {
    vi.mocked(industriesApi.listIndustries).mockResolvedValue(mockPaginated(MOCK_INDUSTRIES));

    render(<IndustriesContent />);

    await waitFor(() => {
      expect(screen.getByText("Commercial Banking")).toBeDefined();
    });

    // Click "State" filter button
    const stateButton = screen.getByRole("button", { name: "State" });
    fireEvent.click(stateButton);

    expect(screen.getByText("Gig Economy Platforms")).toBeDefined();
    expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    expect(screen.queryByText("Commercial Banking")).toBeNull();

    // Verify statutory notice appears under State
    expect(screen.getByText(/State stock predictions remain strictly 0/i)).toBeDefined();
  });

  it("filters industries by universe type", async () => {
    vi.mocked(industriesApi.listIndustries).mockResolvedValue(mockPaginated(MOCK_INDUSTRIES));

    render(<IndustriesContent />);

    await waitFor(() => {
      expect(screen.getByText("Commercial Banking")).toBeDefined();
    });

    // Click "Intel" universe button
    const intelButton = screen.getByRole("button", { name: "Intel" });
    fireEvent.click(intelButton);

    expect(screen.getByText("Gig Economy Platforms")).toBeDefined();
    expect(screen.queryByText("Commercial Banking")).toBeNull();
  });

  it("displays empty state when no industries match criteria and resets filters", async () => {
    vi.mocked(industriesApi.listIndustries).mockResolvedValue(mockPaginated(MOCK_INDUSTRIES));

    render(<IndustriesContent />);

    await waitFor(() => {
      expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    });

    const searchInput = screen.getByLabelText(/Search Industry \/ Mechanism/i);
    fireEvent.change(searchInput, { target: { value: "nonexistentquery123xyz" } });

    expect(screen.getByText(/No Matching Industries Found/i)).toBeDefined();
    const resetBtn = screen.getByRole("button", { name: /Reset Filters/i });
    expect(resetBtn).toBeDefined();

    fireEvent.click(resetBtn);
    expect(screen.getByText("Pharmaceuticals")).toBeDefined();
  });

  it("displays error state with retry button on API failure", async () => {
    vi.mocked(industriesApi.listIndustries).mockRejectedValueOnce(
      new Error("Database connection timed out")
    );

    render(<IndustriesContent />);

    await waitFor(() => {
      expect(screen.getByText("Database connection timed out")).toBeDefined();
    });

    // Check retry button exists
    const retryBtn = screen.getByRole("button", { name: /Retry Loading/i });
    expect(retryBtn).toBeDefined();

    // Now make next call succeed
    vi.mocked(industriesApi.listIndustries).mockResolvedValueOnce(mockPaginated(MOCK_INDUSTRIES));

    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByText("Pharmaceuticals")).toBeDefined();
    });
  });
});
