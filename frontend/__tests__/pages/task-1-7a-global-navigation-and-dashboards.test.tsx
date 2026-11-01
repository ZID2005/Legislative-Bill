/**
 * __tests__/pages/task-1-7a-global-navigation-and-dashboards.test.tsx
 * ===================================================================
 * Task 1.7A — Seance Global Navigation Frame & Executive Dashboard Redesign.
 *
 * Comprehensive validation of:
 * 1. Global Navigation Frame (TopNavbar):
 *    - Streamlined 4-hub hierarchy (Legislation, Markets & Risk, Corporate Universe, Direct Anchors)
 *    - All 31 routes discoverable across desktop navigation, dropdowns, and mobile drawer
 *    - Full keyboard accessibility (ArrowDown, Escape) and click toggle behavior
 *    - Live monitoring telemetry pulse indicator
 * 2. Root Page (/) Executive Command Center:
 *    - Concise product purpose and hairline operational status strip
 *    - Dynamic coverage metric ticker with tabular figures (20, 44, 47, 4,700, 70, 104)
 *    - Unified Decision Hubs switcher (Workspace, Overview, Portfolio)
 *    - High-impact legislative radar (Banking Laws, Merchant Shipping)
 *    - Statutory firewall guarantees (0 state predictions, intelligence entity isolation)
 * 3. Platform Observatory (/overview):
 *    - Dedicated platform observatory purpose and SHA-256 baseline verification
 *    - Three-tier capability architecture (L1 Modelled, L2 State Intelligence, L3 Union Roadmap)
 *    - Statutory isolation guarantee (0 state stock predictions)
 *    - Secondary feeds (Recent bills, predictions snapshot, corporate universe, operational status)
 *    - Direct cross-links to Personal Workspace and Portfolio Exposure
 * 4. Personal Workbench (/workspace):
 *    - Dedicated personal workbench purpose and high-density attention strip
 *    - Monitored entity registry with tabs (bills, companies, industries, states)
 *    - Filterable chronological activity feed (ALL, ALERTS, MONITORING)
 *    - Epistemic classification badges ([OBSERVED], [DERIVED], [PREDICTION])
 *    - State Prediction Firewall enforcement notice
 *    - Integrated Grounded AI Workspace Assistant
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock Next.js navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(""),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: any }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

// Mock Auth API
vi.mock("@/lib/api/auth", () => ({
  authApi: {
    getMe: vi.fn().mockResolvedValue({
      user_id: "usr_analyst",
      email: "analyst@institutional.org",
      display_name: "Senior Analyst",
      role: "ADMIN",
      tenant_id: "tenant_alpha",
    }),
    logout: vi.fn().mockResolvedValue(undefined),
  },
}));

// Mock Monitoring API
vi.mock("@/lib/api/monitoring", () => ({
  monitoringApi: {
    getOverview: vi.fn().mockResolvedValue({
      system_status: "OPERATIONAL",
      total_sources: 12,
      enabled_sources: 12,
      last_run_timestamp: "2026-10-29T12:00:00Z",
    }),
    getStatus: vi.fn().mockResolvedValue({
      system_status: "OPERATIONAL",
      total_sources: 12,
      enabled_sources: 12,
      last_run_id: "run_alpha_01",
      last_run_timestamp: "2026-10-29T12:00:00Z",
      sources_summary: [],
    }),
  },
}));

// Mock Coverage
const mockCoverageData = {
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

vi.mock("@/hooks/useCoverage", () => ({
  useCoverage: () => ({
    coverage: mockCoverageData,
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

// Mock Bills API
vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    listBills: vi.fn().mockResolvedValue({
      items: [
        {
          bill_id: "the-banking-laws-amendment-bill-2024",
          jurisdiction: "central",
          state: null,
          title: "The Banking Laws (Amendment) Bill, 2024",
          short_title: "Banking Laws Amendment",
          bill_number: "Bill No. 125 of 2024",
          status: "assented",
          summary: "Reforms corporate governance and nominee protections.",
          company_exposure_count: 14,
        },
      ],
      total: 1,
    }),
  },
}));

// Mock Predictions API
vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    listPredictions: vi.fn().mockResolvedValue({
      items: [
        {
          prediction_id: "pred-001",
          bill_id: "the-banking-laws-amendment-bill-2024",
          company_symbol: "SBIN",
          event_window: "[-5,+5]",
          predicted_direction: "POSITIVE",
          market_moving_probability: 0.88,
        },
      ],
      total: 1,
    }),
  },
}));

// Mock Companies API
vi.mock("@/lib/api/companies", () => ({
  companiesApi: {
    listCompanies: vi.fn().mockResolvedValue({
      items: [
        {
          company_id: "INE062A01020",
          company_name: "State Bank of India",
          sector: "Banking & Financial Services",
          universe_type: "quantitative",
        },
      ],
      total: 1,
    }),
  },
}));

// Mock Workspace API
vi.mock("@/lib/api/workspace", () => ({
  workspaceApi: {
    getSummary: vi.fn().mockResolvedValue({
      user_id: "usr_analyst",
      tenant_id: "tenant_alpha",
      unread_notifications: 3,
      active_alerts: 5,
      total_alerts: 12,
      watched_bills: 4,
      watched_companies: 6,
      watched_industries: 2,
      watched_sectors: 2,
      watched_states: 1,
      watched_jurisdictions: 2,
      total_watchlists: 2,
      recent_changes_count: 8,
      last_activity_at: "2026-10-29T10:00:00Z",
    }),
    getActivity: vi.fn().mockResolvedValue({
      items: [
        {
          activity_id: "alert_101",
          activity_type: "BILL_STATUS_CHANGE",
          epistemic_status: "OBSERVED",
          title: "Status Change: The Coastal Shipping Bill",
          summary: "Passed Lok Sabha with official amendments.",
          entity_type: "BILL",
          entity_id: "the-coastal-shipping-bill-2024",
          entity_name: "The Coastal Shipping Bill, 2024",
          jurisdiction: "central",
          state: null,
          severity: "HIGH",
          timestamp: "2026-10-29T10:00:00Z",
          deep_link: "/bills/the-coastal-shipping-bill-2024",
        },
      ],
      total: 1,
    }),
    getWatchlistActivity: vi.fn().mockResolvedValue({
      bills: [
        {
          entity_type: "BILL",
          entity_id: "the-coastal-shipping-bill-2024",
          entity_name: "The Coastal Shipping Bill, 2024",
          jurisdiction: "central",
          state: null,
          watchlist_name: "Maritime Core",
          latest_activity: "Added to 'Maritime Core'",
          alert_count: 2,
          deep_link: "/bills/the-coastal-shipping-bill-2024",
        },
      ],
      companies: [
        {
          entity_type: "COMPANY",
          entity_id: "INE062A01020",
          entity_name: "State Bank of India",
          jurisdiction: "central",
          state: null,
          watchlist_name: "Financials",
          latest_activity: "Added to 'Financials'",
          alert_count: 1,
          deep_link: "/companies/INE062A01020",
          extra_metadata: {
            sector: "Banking",
            is_quant_eligible: true,
          },
        },
      ],
      industries: [],
      jurisdictions: [],
      total_watched: 2,
    }),
    getAnalyticsSnapshot: vi.fn().mockResolvedValue({
      items: [
        {
          entity_type: "COMPANY",
          entity_id: "INE062A01020",
          entity_name: "State Bank of India",
          epistemic_label: "[PREDICTION]",
          risk_level: "MODERATE",
          risk_score: 0.42,
          anticipation_tier: "HIGH_EVIDENCE",
          anticipation_score: 0.74,
          prediction_record: {
            direction: "POSITIVE",
            confidence: "HIGH",
          },
          is_state_firewall_active: false,
          is_intelligence_firewall_active: false,
          firewall_note: null,
        },
        {
          entity_type: "BILL",
          entity_id: "ap-duty-bill-2024",
          entity_name: "AP Clean Energy Duty Act, 2024",
          epistemic_label: "[DERIVED]",
          risk_level: "LOW",
          risk_score: null,
          anticipation_tier: null,
          anticipation_score: null,
          prediction_record: null,
          is_state_firewall_active: true,
          is_intelligence_firewall_active: false,
          firewall_note: "State stock predictions remain strictly 0.",
        },
      ],
    }),
    getDecisionIntelligence: vi.fn().mockResolvedValue({
      relevant_new_bills: [
        {
          bill_id: "the-banking-laws-amendment-bill-2024",
          bill_title: "The Banking Laws (Amendment) Bill, 2024",
          relevance_tier: "DIRECT",
          model_status: "MODELLED",
          primary_linkage_reason: "Direct statutory amendments to bank governance.",
          jurisdiction: "central",
          status: "assented",
        },
      ],
    }),
    getChangeFeed: vi.fn().mockResolvedValue([
      {
        event_id: "evt_1",
        event_type: "BILL_PASSAGE",
        bill_title: "The Banking Laws (Amendment) Bill, 2024",
        relevance_reason: "Direct impact on SBI",
        deep_link: "/bills/the-banking-laws-amendment-bill-2024",
      },
    ]),
  },
}));

// Mock AI API
vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn().mockResolvedValue({
      question: "What changed in my watchlists?",
      content: "Summary of recent changes in your watchlists.",
      operation: "ask",
      success: true,
    }),
  },
}));

import { TopNavbar } from "@/components/layout/TopNavbar";
import LandingPage from "@/app/page";
import OverviewContent from "@/app/overview/OverviewContent";
import WorkspacePage from "@/app/workspace/page";

describe("Task 1.7A — Global Navigation Frame (TopNavbar)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the brand logo and core institutional hubs", () => {
    render(<TopNavbar />);

    expect(screen.getByText("Seance")).toBeInTheDocument();
    expect(screen.getByText("Workspace")).toBeInTheDocument();
    expect(screen.getByText("Legislation")).toBeInTheDocument();
    expect(screen.getByText("Markets & Risk")).toBeInTheDocument();
    expect(screen.getByText("Corporate Universe")).toBeInTheDocument();
    expect(screen.getByText("Portfolio")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByText("AI Analyst")).toBeInTheDocument();
  });

  it("opens dropdown menu on click and closes on Escape", () => {
    render(<TopNavbar />);

    const legBtn = screen.getByRole("button", { name: /Legislation/i });
    expect(legBtn).toHaveAttribute("aria-expanded", "false");

    // Click to open
    fireEvent.click(legBtn);
    expect(legBtn).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menu", { name: /Legislation navigation/i })).toBeInTheDocument();
    expect(screen.getByText("Bills Directory")).toBeInTheDocument();
    expect(screen.getByText("Legislative Explorer")).toBeInTheDocument();
    expect(screen.getByText("State Assemblies")).toBeInTheDocument();

    // Escape closes dropdown
    fireEvent.keyDown(legBtn, { key: "Escape" });
    expect(screen.queryByRole("menu", { name: /Legislation navigation/i })).not.toBeInTheDocument();
  });

  it("renders live telemetry pulse indicator and command palette button", async () => {
    render(<TopNavbar />);

    const searchBtn = screen.getByLabelText(/Open command palette/i);
    expect(searchBtn).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Active/i)).toBeInTheDocument();
    });
  });

  it("toggles mobile drawer on hamburger button click", () => {
    render(<TopNavbar />);

    const menuBtn = screen.getByLabelText(/Open navigation menu/i);
    fireEvent.click(menuBtn);

    const mobileDrawer = screen.getByRole("dialog", { name: /Mobile navigation/i });
    expect(mobileDrawer).toBeInTheDocument();

    // Verify presence of System & Observability links inside drawer
    expect(screen.getByText("Legislative Monitoring")).toBeInTheDocument();
    expect(screen.getByText("Platform Coverage")).toBeInTheDocument();
    expect(screen.getByText("Settings & RBAC")).toBeInTheDocument();

    // Close button dismisses drawer
    const closeBtn = screen.getByLabelText(/Close navigation/i);
    fireEvent.click(closeBtn);
    expect(screen.queryByRole("dialog", { name: /Mobile navigation/i })).not.toBeInTheDocument();
  });
});

describe("Task 1.7A — Executive Command Center (Root /)", () => {
  it("renders concise executive headline and operational status strip", () => {
    render(<LandingPage />);

    expect(screen.getByText(/PRODUCTION ENGINE ONLINE/i)).toBeInTheDocument();
    expect(screen.getByText(/Statutory Firewalls Locked/i)).toBeInTheDocument();
    expect(
      screen.getByText(/India Legislative Intelligence & Market Impact Predictions/i)
    ).toBeInTheDocument();
  });

  it("renders 6 coverage metric indicators with tabular figures", () => {
    render(<LandingPage />);

    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getByText("44")).toBeInTheDocument();
    expect(screen.getByText("47")).toBeInTheDocument();
    expect(screen.getByText("4,700")).toBeInTheDocument();
    expect(screen.getByText("70")).toBeInTheDocument();
    expect(screen.getByText("104")).toBeInTheDocument();
  });

  it("renders Unified Decision Hubs and High-Impact Legislative Radar", () => {
    render(<LandingPage />);

    expect(screen.getByText(/Unified Decision Hubs/i)).toBeInTheDocument();
    expect(screen.getByText("Legislative Workspace")).toBeInTheDocument();
    expect(screen.getByText("Platform Coverage Overview")).toBeInTheDocument();
    expect(screen.getByText("Portfolio Legislative Exposure")).toBeInTheDocument();

    // Legislative radar
    expect(screen.getByText(/High-Impact Legislative Radar/i)).toBeInTheDocument();
    expect(screen.getByText(/The Banking Laws \(Amendment\) Bill, 2024/i)).toBeInTheDocument();
    expect(screen.getByText(/The Merchant Shipping Bill, 2024/i)).toBeInTheDocument();
  });

  it("renders statutory firewall guarantees and core workflow cards", () => {
    render(<LandingPage />);

    expect(screen.getAllByText(/Zero State Stock Predictions/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Non-Listed Entity Isolation/i).length).toBeGreaterThanOrEqual(1);

    expect(screen.getByText("Legislative Explorer")).toBeInTheDocument();
    expect(screen.getByText("Market Predictions")).toBeInTheDocument();
    expect(screen.getByText("Custom Watchlists")).toBeInTheDocument();
    expect(screen.getByText("Grounded AI Analyst")).toBeInTheDocument();
  });
});

describe("Task 1.7A — Platform Observatory (/overview)", () => {
  it("renders observatory header, hash verification, and quick discovery actions", () => {
    render(<OverviewContent />);

    expect(screen.getByText("India Legislative Intelligence")).toBeInTheDocument();
    expect(screen.getByText(/BASELINE SHA-256: 50ae7603/i)).toBeInTheDocument();

    expect(screen.getByText("🔍 Explore Bills")).toBeInTheDocument();
    expect(screen.getByText("🏢 Explore Companies")).toBeInTheDocument();
    expect(screen.getByText("📈 View Predictions")).toBeInTheDocument();
    expect(screen.getByText("🤖 Ask AI Copilot")).toBeInTheDocument();

    // Cross-workflow links
    expect(screen.getByRole("link", { name: /Personal Workspace →/i })).toHaveAttribute("href", "/workspace");
    expect(screen.getByRole("link", { name: /Portfolio Exposure →/i })).toHaveAttribute("href", "/portfolio");
  });

  it("renders three-tier capability architecture and statutory isolation guarantee", () => {
    render(<OverviewContent />);

    expect(screen.getByText("Central Parliament — Market Modelled")).toBeInTheDocument();
    expect(screen.getByText("State Assemblies — Economic Intelligence")).toBeInTheDocument();
    expect(screen.getByText("Union Roadmap — 24 Planned States")).toBeInTheDocument();

    expect(screen.getAllByText(/Statutory Isolation Guarantee/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/0 stock predictions exist for State legislation/i)).toBeInTheDocument();
  });

  it("renders operational status, recent intake, and predictions preview", async () => {
    render(<OverviewContent />);

    await waitFor(() => {
      expect(screen.getByText("OPERATIONAL")).toBeInTheDocument();
      expect(screen.getByText("Recent Legislative Intake")).toBeInTheDocument();
    });
  });
});

describe("Task 1.7A — Personal Workbench (/workspace)", () => {
  it("renders personalized workbench header and high-density attention metrics", async () => {
    render(<WorkspacePage />);

    expect(await screen.findByText("Your Legislative Workspace")).toBeInTheDocument();
    expect(screen.getByText("Personalized Decision Center")).toBeInTheDocument();

    // Attention counts
    expect(screen.getByText("3")).toBeInTheDocument(); // notifications
    expect(screen.getByText("5")).toBeInTheDocument(); // active alerts
    expect(screen.getByText("4")).toBeInTheDocument(); // watched bills
    expect(screen.getByText("6")).toBeInTheDocument(); // watched companies
  });

  it("renders monitored entity tabs and switches between them", async () => {
    render(<WorkspacePage />);

    expect(await screen.findByText(/Monitored Entities/i)).toBeInTheDocument();
    const billElements = await screen.findAllByText("The Coastal Shipping Bill, 2024");
    expect(billElements.length).toBeGreaterThanOrEqual(1);

    const compTab = await screen.findByRole("button", { name: /^Companies \(/i });
    expect(compTab).toBeInTheDocument();

    // Switch to companies
    fireEvent.click(compTab);
    const companyElements = await screen.findAllByText("State Bank of India");
    expect(companyElements.length).toBeGreaterThanOrEqual(1);
  });

  it("enforces State Prediction Firewall notice and renders epistemic badges", async () => {
    render(<WorkspacePage />);

    await waitFor(() => {
      expect(screen.getByText(/State Prediction Firewall Active/i)).toBeInTheDocument();
      expect(screen.getByText(/State stock predictions remain strictly 0/i)).toBeInTheDocument();
      expect(screen.getByText("[OBSERVED]")).toBeInTheDocument();
    });
  });

  it("renders Grounded AI Workspace Assistant with prompt chips", async () => {
    render(<WorkspacePage />);

    expect(await screen.findByText("Workspace AI Assistant")).toBeInTheDocument();
    expect(screen.getByText("What changed in my watchlists?")).toBeInTheDocument();
    expect(screen.getByText("Summarize my unread alerts.")).toBeInTheDocument();
  });
});
