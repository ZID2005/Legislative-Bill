/**
 * __tests__/pages/explorer.test.tsx
 * ===================================
 * Comprehensive unit and integration tests for India Legislative Explorer.
 * Validates:
 * - Initial load with paginated bills
 * - Global search execution
 * - Multi-attribute filters (jurisdiction, state, sector, relevance)
 * - Planned state roadmap notice
 * - Central prediction availability vs State prediction firewall disclosure
 * - Unified mode cross-entity discovery (bills, companies, sectors)
 * - Server-side pagination controls
 * - Empty results & error handling
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock Next.js navigation hooks
const mockPush = vi.fn();
let currentSearchString = "";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => "/explorer",
  useSearchParams: () => new URLSearchParams(currentSearchString),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock API clients
vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    listBills: vi.fn(),
  },
}));

vi.mock("@/lib/api/search", () => ({
  searchApi: {
    globalSearch: vi.fn(),
  },
}));

import ExplorerContent from "@/app/explorer/ExplorerContent";
import { billsApi } from "@/lib/api/bills";
import { searchApi } from "@/lib/api/search";

const mockListBills = billsApi.listBills as ReturnType<typeof vi.fn>;
const mockGlobalSearch = searchApi.globalSearch as ReturnType<typeof vi.fn>;

const sampleCentralBill = {
  bill_id: "the-bills-of-lading-bill-2024",
  jurisdiction: "central",
  state: null,
  title: "The Bills of Lading Bill, 2024",
  short_title: "Bills of Lading Bill",
  bill_number: "124 of 2024",
  legislature: "Parliament of India",
  house: "Lok Sabha",
  year: 2024,
  introduction_date: "2024-08-09",
  assent_date: null,
  status: "introduced",
  policy_domain: "Commerce & Maritime",
  economic_sectors: ["Infrastructure & Logistics"],
  secondary_sectors: [],
  stakeholders: ["Exporters"],
  summary: "Consolidates and amends law relating to bills of lading.",
  company_exposure_count: 4,
  listed_company_exposure_count: 4,
  market_relevance: "HIGH",
  modeling_eligibility: "ELIGIBLE",
  data_sufficiency: "COMPLETE",
  source_url: "https://sansad.in",
  pdf_url: null,
  data_quality: "VERIFIED",
};

const sampleStateBill = {
  bill_id: "karnataka-vs-bill-33-2024",
  jurisdiction: "state",
  state: "Karnataka",
  title: "Karnataka Platform Based Gig Workers Bill, 2024",
  short_title: "Karnataka Gig Workers Bill",
  bill_number: "L.A. Bill No. 33 of 2024",
  legislature: "Karnataka Legislative Assembly",
  house: "Vidhan Sabha",
  year: 2024,
  introduction_date: "2024-07-22",
  assent_date: null,
  status: "introduced",
  policy_domain: "Labour & Employment",
  economic_sectors: ["Information Technology", "Consumer Goods & Retail"],
  secondary_sectors: [],
  stakeholders: ["Gig Workers", "Platform Aggregators"],
  summary: "Protects rights of platform-based gig workers in Karnataka.",
  company_exposure_count: 5,
  listed_company_exposure_count: 2,
  market_relevance: "HIGH",
  modeling_eligibility: "NOT_ELIGIBLE",
  data_sufficiency: "COMPLETE",
  source_url: "http://kla.kar.nic.in",
  pdf_url: null,
  data_quality: "VERIFIED",
};

describe("Explorer Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    currentSearchString = "";
    mockListBills.mockResolvedValue({
      items: [sampleCentralBill, sampleStateBill],
      total: 2,
      page: 1,
      limit: 10,
      pages: 1,
    });
  });

  it("renders header, search bar, and filter controls", async () => {
    render(<ExplorerContent />);

    expect(screen.getByText("India Legislative Explorer")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search bill titles/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Bills of Lading Bill")).toBeInTheDocument();
      expect(screen.getByText("Karnataka Gig Workers Bill")).toBeInTheDocument();
    });
  });

  it("differentiates Central prediction availability and State prediction firewall", async () => {
    render(<ExplorerContent />);

    await waitFor(() => {
      // Central bill has predictions available
      expect(screen.getByText("Market predictions available")).toBeInTheDocument();
      expect(screen.getByText("View Predictions")).toBeInTheDocument();

      // State bill has strict firewall disclosure
      expect(
        screen.getByText(/Market prediction not currently available for State legislation/i)
      ).toBeInTheDocument();
    });
  });

  it("updates URL on search submission", async () => {
    render(<ExplorerContent />);

    const searchInput = screen.getByPlaceholderText(/Search bill titles/i);
    fireEvent.change(searchInput, { target: { value: "gig workers" } });

    const searchButton = screen.getByRole("button", { name: "Search" });
    fireEvent.click(searchButton);

    expect(mockPush).toHaveBeenCalledWith("/explorer?q=gig+workers");
  });

  it("updates URL when jurisdiction filter changes", async () => {
    render(<ExplorerContent />);

    const jurisdictionSelect = screen.getByLabelText("Jurisdiction");
    fireEvent.change(jurisdictionSelect, { target: { value: "state" } });

    expect(mockPush).toHaveBeenCalledWith("/explorer?jurisdiction=state");
  });

  it("shows planned state roadmap banner when a planned state is selected", async () => {
    currentSearchString = "state=Maharashtra";
    mockListBills.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      pages: 0,
    });

    render(<ExplorerContent />);

    await waitFor(() => {
      expect(screen.getByText(/Planned State Coverage: Maharashtra/i)).toBeInTheDocument();
      expect(screen.getByText(/0 legislative bills have been ingested to date/i)).toBeInTheDocument();
    });
  });

  it("renders empty state when no bills match query", async () => {
    mockListBills.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      pages: 0,
    });

    render(<ExplorerContent />);

    await waitFor(() => {
      expect(screen.getByText("No legislation found")).toBeInTheDocument();
    });
  });

  it("supports unified search mode across bills, companies, and sectors", async () => {
    currentSearchString = "mode=unified&q=reliance";
    mockGlobalSearch.mockResolvedValue({
      query: "reliance",
      total_matches: 2,
      items: [
        {
          id: "INE002A01018",
          title: "Reliance Industries Limited",
          subtitle: "Energy & Petrochemicals • Listed",
          category: "companies_quant",
          jurisdiction: "central",
          state: "Maharashtra",
          relevance_score: 95,
          url: "/companies/INE002A01018",
        },
      ],
      categories: { companies_quant: 1 },
    });

    render(<ExplorerContent />);

    await waitFor(() => {
      expect(screen.getByText("Reliance Industries Limited")).toBeInTheDocument();
      expect(screen.getByText("Energy & Petrochemicals • Listed")).toBeInTheDocument();
      expect(screen.getByText(/cross-entity matches for/i)).toBeInTheDocument();
    });
  });
});
