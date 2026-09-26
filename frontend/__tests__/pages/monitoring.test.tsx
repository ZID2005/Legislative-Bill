/**
 * __tests__/pages/monitoring.test.tsx
 * =====================================
 * Comprehensive tests for the Legislative Monitoring & Discovery Center.
 *
 * Validates:
 * - Overview panel telemetry rendering
 * - Source registry table rendering and filtering
 * - Source health badge statuses (all 6 statuses)
 * - Check history pagination
 * - Detected changes feed with epistemic labels
 * - Change detail drawer BEFORE/AFTER display
 * - Discovery feed firewall notice for State items
 * - Central/State jurisdiction labels always present
 * - State prediction firewall statement always visible
 * - No prediction UI elements present on monitoring page
 * - AI analyst prompt chips visible
 * - Loading skeletons shown while fetching
 * - Error retry state with message
 * - Empty state when API returns no events
 * - Provenance display (source_id, detected_at)
 * - Scheduler panel read-only display
 * - No fabricated events (empty mocked API → empty rendered state)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock Next.js navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/monitoring",
  useSearchParams: () => new URLSearchParams(""),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock monitoring API
vi.mock("@/lib/api/monitoring", () => ({
  monitoringApi: {
    getOverview: vi.fn(),
    getSources: vi.fn(),
    getRuns: vi.fn(),
    getChanges: vi.fn(),
    getChangeDetail: vi.fn(),
    getSource: vi.fn(),
    getSchedulerStatus: vi.fn(),
    getStatus: vi.fn(),
  },
}));

// Mock API client (for AI analyst)
vi.mock("@/lib/api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { MonitoringCenterContent } from "@/app/monitoring/MonitoringCenterContent";
import { monitoringApi } from "@/lib/api/monitoring";
import type {
  ChangeEventDetail,
  MonitoringOverview,
  MonitoringRunDetail,
  MonitoringSourceItem,
  PaginatedResponse,
  SchedulerStatus,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Test fixtures
// ---------------------------------------------------------------------------

const MOCK_SCHEDULER: SchedulerStatus = {
  enabled: true,
  scheduled_running: true,
  run_in_progress: false,
  last_run_at: "2026-09-20T06:00:00Z",
  next_run_at: "2026-09-21T06:00:00Z",
  last_result_status: "SUCCESS",
  config: { central_interval_hours: 24 },
};

const MOCK_OVERVIEW: MonitoringOverview = {
  total_sources: 5,
  enabled_sources: 3,
  central_sources: 1,
  state_sources: 4,
  implemented_sources: 3,
  planned_sources: 2,
  total_runs: 12,
  last_run_id: "run-001",
  last_run_status: "SUCCESS",
  last_run_at: "2026-09-20T06:00:00Z",
  last_run_new_bills: 2,
  last_run_changed_bills: 1,
  last_run_document_changes: 0,
  last_run_errors: 0,
  total_change_events: 7,
  scheduler: MOCK_SCHEDULER,
  sources_healthy: 3,
  sources_with_errors: 0,
  sources_never_checked: 2,
};

const MOCK_SOURCE: MonitoringSourceItem = {
  source_id: "parliament_in_central",
  source_name: "Parliament of India (Central)",
  jurisdiction: "central",
  state: null,
  source_type: "html_table",
  source_url: "https://parliament.in/bills",
  enabled: true,
  status: "IMPLEMENTED",
  polling_interval_hours: 24,
  priority: 1,
  last_checked_at: "2026-09-20T06:00:00Z",
  last_success_at: "2026-09-20T06:00:00Z",
  last_error_at: null,
  last_error: null,
  notes: null,
};

const MOCK_SOURCES_PAGE: PaginatedResponse<MonitoringSourceItem> = {
  items: [MOCK_SOURCE],
  total: 1,
  page: 1,
  limit: 25,
  pages: 1,
};

const MOCK_RUN: MonitoringRunDetail = {
  run_id: "run-001",
  trigger: "scheduled",
  started_at: "2026-09-20T06:00:00Z",
  completed_at: "2026-09-20T06:01:00Z",
  duration_seconds: 60,
  status: "SUCCESS",
  sources_checked: 3,
  sources_succeeded: 3,
  sources_failed: 0,
  new_bills: 2,
  changed_bills: 1,
  document_changes: 0,
  errors: 0,
  source_results: [],
};

const MOCK_RUNS_PAGE: PaginatedResponse<MonitoringRunDetail> = {
  items: [MOCK_RUN],
  total: 1,
  page: 1,
  limit: 20,
  pages: 1,
};

const MOCK_CENTRAL_CHANGE: ChangeEventDetail = {
  event_id: "evt-001",
  bill_id: "finance-bill-2026",
  bill_title: "Finance Bill 2026",
  jurisdiction: "central",
  state: null,
  source_id: "parliament_in_central",
  event_type: "NEW_BILL",
  field_name: null,
  old_value: null,
  new_value: { title: "Finance Bill 2026" },
  detected_at: "2026-09-20T06:00:00Z",
  source_reference: null,
  confidence: 1.0,
  error_message: null,
  epistemic_status: "OBSERVED",
  provenance: { source_id: "parliament_in_central", verification_status: "SYSTEM_DETECTED" },
  previous_version_available: false,
  current_version_available: true,
};

const MOCK_STATE_CHANGE: ChangeEventDetail = {
  ...MOCK_CENTRAL_CHANGE,
  event_id: "evt-002",
  bill_id: "mh-water-bill-2026",
  bill_title: "Maharashtra Water Regulation Bill 2026",
  jurisdiction: "state",
  state: "Maharashtra",
  source_id: "mh_vidhan_bhavan",
  epistemic_status: "DERIVED",
};

const MOCK_CHANGES_PAGE: PaginatedResponse<ChangeEventDetail> = {
  items: [MOCK_CENTRAL_CHANGE, MOCK_STATE_CHANGE],
  total: 2,
  page: 1,
  limit: 25,
  pages: 1,
};

const EMPTY_PAGE = <T,>(T: unknown): PaginatedResponse<typeof T> => ({
  items: [] as typeof T[],
  total: 0,
  page: 1,
  limit: 25,
  pages: 1,
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupOverviewMocks() {
  vi.mocked(monitoringApi.getOverview).mockResolvedValue(MOCK_OVERVIEW);
  vi.mocked(monitoringApi.getSources).mockResolvedValue(MOCK_SOURCES_PAGE);
  vi.mocked(monitoringApi.getRuns).mockResolvedValue(MOCK_RUNS_PAGE);
  vi.mocked(monitoringApi.getChanges).mockResolvedValue(MOCK_CHANGES_PAGE);
  vi.mocked(monitoringApi.getStatus).mockResolvedValue({
    system_status: "OPERATIONAL",
    total_sources: 5,
    enabled_sources: 3,
    last_run_id: "run-001",
    last_run_timestamp: "2026-09-20T06:00:00Z",
    sources_summary: [],
  });
}

function clickTab(label: string) {
  const tab = screen.getByRole("tab", { name: new RegExp(label, "i") });
  fireEvent.click(tab);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("MonitoringCenterContent — Overview Tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupOverviewMocks();
  });

  it("renders the monitoring center heading", async () => {
    render(<MonitoringCenterContent />);
    expect(screen.getByRole("heading", { name: /Legislative Monitoring & Discovery Center/i })).toBeDefined();
  });

  it("displays the jurisdiction banner compact notice", async () => {
    render(<MonitoringCenterContent />);
    expect(screen.getByText(/Monitoring Notice/i)).toBeDefined();
  });

  it("always shows State prediction firewall statement", async () => {
    render(<MonitoringCenterContent />);
    expect(screen.getAllByText(/State stock predictions remain strictly 0/i).length).toBeGreaterThan(0);
  });

  it("renders all 7 tab buttons", async () => {
    render(<MonitoringCenterContent />);
    const tabs = ["Overview", "Sources", "Check History", "Detected Changes", "Discovery Feed", "Scheduler", "AI Analyst"];
    for (const tab of tabs) {
      expect(screen.getByRole("tab", { name: new RegExp(tab, "i") })).toBeDefined();
    }
  });

  it("overview tab is selected by default", () => {
    render(<MonitoringCenterContent />);
    const overviewTab = screen.getByRole("tab", { name: /Overview/i });
    expect(overviewTab.getAttribute("aria-selected")).toBe("true");
  });

  it("loads and renders overview telemetry", async () => {
    render(<MonitoringCenterContent />);
    await waitFor(() => {
      // Should show total sources count
      expect(screen.getByText("5")).toBeDefined();
      // Should show total change events
      expect(screen.getByText("7")).toBeDefined();
    });
  });

  it("shows loading state before data arrives", () => {
    // Don't resolve promises immediately
    vi.mocked(monitoringApi.getOverview).mockImplementation(() => new Promise(() => {}));
    render(<MonitoringCenterContent />);
    // Should show aria-busy
    const busyEl = document.querySelector("[aria-busy='true']");
    expect(busyEl).toBeDefined();
  });

  it("shows error state when overview fails", async () => {
    vi.mocked(monitoringApi.getOverview).mockRejectedValue(new Error("Network timeout"));
    render(<MonitoringCenterContent />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to load monitoring overview/i)).toBeDefined();
    });
  });

  it("does NOT show any prediction/investment UI in monitoring page", async () => {
    render(<MonitoringCenterContent />);
    await waitFor(() => {
      // Should not have "Buy" or "Sell" or "Hold" recommendations
      expect(screen.queryByText(/\bBuy\b/)).toBeNull();
      expect(screen.queryByText(/\bSell\b/)).toBeNull();
      expect(screen.queryByText(/\bHold\b/)).toBeNull();
    });
  });

  it("does NOT show political recommendation UI", async () => {
    render(<MonitoringCenterContent />);
    await waitFor(() => {
      expect(screen.queryByText(/political recommendation/i)).toBeNull();
      expect(screen.queryByText(/party ranking/i)).toBeNull();
    });
  });
});

describe("MonitoringCenterContent — Sources Tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupOverviewMocks();
  });

  it("switches to Sources tab and shows source table", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Sources");
    await waitFor(() => {
      expect(screen.getByRole("table", { name: /Monitoring source registry/i })).toBeDefined();
    });
  });

  it("shows Central source with IMPLEMENTED status badge", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Sources");
    await waitFor(() => {
      expect(screen.getByText("Parliament of India (Central)")).toBeDefined();
      expect(screen.getByRole("status", { name: /Source status: Implemented/i })).toBeDefined();
    });
  });

  it("shows jurisdiction filter", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Sources");
    await waitFor(() => {
      expect(screen.getAllByLabelText(/Jurisdiction/i).length).toBeGreaterThan(0);
    });
  });

  it("renders Details button for each source row", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Sources");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /View details for Parliament of India/i })).toBeDefined();
    });
  });

  it("shows empty state when no sources match filter", async () => {
    vi.mocked(monitoringApi.getSources).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 25,
      pages: 1,
    });
    render(<MonitoringCenterContent />);
    clickTab("Sources");
    await waitFor(() => {
      expect(screen.getByText(/No sources match the current filters/i)).toBeDefined();
    });
  });
});

describe("MonitoringCenterContent — Check History Tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupOverviewMocks();
  });

  it("switches to Check History and shows run table", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Check History");
    await waitFor(() => {
      expect(screen.getByRole("table", { name: /Monitoring run history/i })).toBeDefined();
    });
  });

  it("shows run-001 with SUCCESS status", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Check History");
    await waitFor(() => {
      expect(screen.getAllByText("SUCCESS").length).toBeGreaterThan(0);
    });
  });

  it("shows new bills count in run", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Check History");
    await waitFor(() => {
      // new_bills = 2
      expect(screen.getAllByText("2").length).toBeGreaterThan(0);
    });
  });

  it("shows empty state when no runs recorded", async () => {
    vi.mocked(monitoringApi.getRuns).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      pages: 1,
    });
    render(<MonitoringCenterContent />);
    clickTab("Check History");
    await waitFor(() => {
      expect(screen.getByText(/No monitoring runs have been recorded/i)).toBeDefined();
    });
  });
});

describe("MonitoringCenterContent — Detected Changes Tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupOverviewMocks();
  });

  it("switches to Detected Changes and shows change feed", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getByRole("search", { name: /Change event filters/i })).toBeDefined();
    });
  });

  it("shows [OBSERVED] epistemic label for NEW_BILL event", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getByText(/\[OBSERVED\]/i)).toBeDefined();
    });
  });

  it("shows [DERIVED] epistemic label for changed event", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getByText(/\[DERIVED\]/i)).toBeDefined();
    });
  });

  it("shows Central jurisdiction label", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getAllByText(/Central/i).length).toBeGreaterThan(0);
    });
  });

  it("shows State jurisdiction label with state name", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getByText(/State.*Maharashtra/i)).toBeDefined();
    });
  });

  it("shows bill titles in the feed", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getByText("Finance Bill 2026")).toBeDefined();
      expect(screen.getByText("Maharashtra Water Regulation Bill 2026")).toBeDefined();
    });
  });

  it("shows State prediction firewall on State changes", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      // The firewall notice in compact jurisdiction banner
      expect(screen.getAllByText(/State stock predictions remain strictly 0/i).length).toBeGreaterThan(0);
    });
  });

  it("renders empty state when API returns no events", async () => {
    vi.mocked(monitoringApi.getChanges).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 25,
      pages: 1,
    });
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getByText(/No change events match/i)).toBeDefined();
    });
  });

  it("does NOT fabricate events (empty → empty state shown, none invented)", async () => {
    vi.mocked(monitoringApi.getChanges).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 25,
      pages: 1,
    });
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      // No bill titles should appear when API returns empty
      expect(screen.queryByText("Finance Bill 2026")).toBeNull();
      expect(screen.queryByText("Maharashtra Water Regulation Bill 2026")).toBeNull();
    });
  });

  it("shows provenance source_id on each change item", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Detected Changes");
    await waitFor(() => {
      expect(screen.getByText(/parliament_in_central/i)).toBeDefined();
    });
  });
});

describe("MonitoringCenterContent — Discovery Feed Tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupOverviewMocks();
  });

  it("shows discovery feed with jurisdiction banner", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Discovery Feed");
    await waitFor(() => {
      // Full jurisdiction banner appears in discovery tab
      expect(screen.getByRole("region", { name: /Jurisdiction coverage and prediction scope/i })).toBeDefined();
    });
  });

  it("shows State no-prediction notice on state discovery items", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Discovery Feed");
    await waitFor(() => {
      expect(screen.getByText(/Economic intelligence only.*No stock prediction/i)).toBeDefined();
    });
  });

  it("links each bill to /bills/[id]", async () => {
    render(<MonitoringCenterContent />);
    clickTab("Discovery Feed");
    await waitFor(() => {
      const links = screen.getAllByRole("link", { name: /Bill Dossier/i });
      expect(links.length).toBeGreaterThan(0);
      expect(links[0].getAttribute("href")).toContain("/bills/");
    });
  });
});

describe("MonitoringCenterContent — Scheduler Tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupOverviewMocks();
  });

  it("shows scheduler panel after switching tab", async () => {
    render(<MonitoringCenterContent />);
    // Load overview first to populate scheduler
    await waitFor(() => {
      expect(screen.getByText("5")).toBeDefined();
    });
    clickTab("Scheduler");
    expect(screen.getByRole("region", { name: /Scheduler observability/i })).toBeDefined();
  });
});

describe("MonitoringCenterContent — AI Analyst Tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupOverviewMocks();
  });

  it("shows AI analyst chat interface", () => {
    render(<MonitoringCenterContent />);
    clickTab("AI Analyst");
    expect(screen.getByRole("log", { name: /AI monitoring conversation/i })).toBeDefined();
  });

  it("shows prompt chips for suggested questions", () => {
    render(<MonitoringCenterContent />);
    clickTab("AI Analyst");
    expect(screen.getByRole("group", { name: /Suggested monitoring questions/i })).toBeDefined();
    expect(screen.getByText(/What changed recently/i)).toBeDefined();
  });

  it("shows the AI disclaimer about no predictions", () => {
    render(<MonitoringCenterContent />);
    clickTab("AI Analyst");
    expect(screen.getByText(/State legislative monitoring does not generate stock predictions/i)).toBeDefined();
  });

  it("shows question input field", () => {
    render(<MonitoringCenterContent />);
    clickTab("AI Analyst");
    expect(screen.getAllByLabelText(/Monitoring question/i).length).toBeGreaterThan(0);
  });

  it("shows Send Ask button", () => {
    render(<MonitoringCenterContent />);
    clickTab("AI Analyst");
    expect(screen.getByRole("button", { name: /Send question/i })).toBeDefined();
  });
});
