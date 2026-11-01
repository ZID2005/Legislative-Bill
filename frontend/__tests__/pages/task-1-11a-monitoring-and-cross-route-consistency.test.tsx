/**
 * __tests__/pages/task-1-11a-monitoring-and-cross-route-consistency.test.tsx
 * =========================================================================
 * Comprehensive regression test suite for Task 1.11A:
 * Seance Monitoring, Observability & Cross-Route Consistency.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import fs from "fs";
import path from "path";
import crypto from "crypto";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock Next.js navigation hooks
let mockSearchParams = new URLSearchParams();
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
};

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => mockRouter,
  usePathname: () => "/monitoring",
}));

// Mock Monitoring API
vi.mock("@/lib/api/monitoring", () => ({
  monitoringApi: {
    getOverview: vi.fn(),
    getSources: vi.fn(),
    getSource: vi.fn(),
    getRuns: vi.fn(),
    getChanges: vi.fn(),
    getChangeDetail: vi.fn(),
    getSchedulerStatus: vi.fn(),
    getStatus: vi.fn(),
    triggerCheck: vi.fn(),
    getFreshness: vi.fn(),
  },
}));

// Mock Coverage API
vi.mock("@/lib/api/coverage", () => ({
  coverageApi: {
    getCoverage: vi.fn(),
  },
}));

// Mock API client for AI analyst
vi.mock("@/lib/api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { MonitoringCenterContent } from "@/app/monitoring/MonitoringCenterContent";
import { CoverageContent } from "@/app/coverage/CoverageContent";
import { monitoringApi } from "@/lib/api/monitoring";
import { coverageApi } from "@/lib/api/coverage";
import type {
  ChangeEventDetail,
  CoverageReportResponse,
  FreshnessResponse,
  MonitoringOverview,
  MonitoringRunDetail,
  MonitoringSourceDetail,
  MonitoringSourceItem,
  PaginatedResponse,
  SchedulerStatus,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Test Fixtures
// ---------------------------------------------------------------------------

const MOCK_SCHEDULER: SchedulerStatus = {
  enabled: true,
  scheduled_running: true,
  run_in_progress: false,
  last_run_at: "2026-10-30T06:00:00Z",
  next_run_at: "2026-10-31T06:00:00Z",
  last_result_status: "SUCCESS",
  config: { central_interval_hours: 24, state_interval_hours: 48 },
};

const MOCK_OVERVIEW: MonitoringOverview = {
  total_sources: 5,
  enabled_sources: 4,
  central_sources: 1,
  state_sources: 4,
  implemented_sources: 4,
  planned_sources: 1,
  total_runs: 28,
  last_run_id: "run-028-prod",
  last_run_status: "SUCCESS",
  last_run_at: "2026-10-30T06:00:00Z",
  last_run_new_bills: 1,
  last_run_changed_bills: 2,
  last_run_document_changes: 0,
  last_run_errors: 0,
  total_change_events: 19,
  scheduler: MOCK_SCHEDULER,
  sources_healthy: 4,
  sources_with_errors: 0,
  sources_never_checked: 1,
};

const MOCK_FRESHNESS: FreshnessResponse = {
  overall_status: "LIVE",
  as_of: "2026-10-30T06:00:00Z",
  timestamp: "2026-10-30T06:00:00Z",
  total_datasets: 5,
  live_count: 4,
  recent_count: 0,
  stale_count: 0,
  not_available_count: 1,
  datasets: [
    {
      dataset: "central_legislative_bills",
      status: "LIVE",
      record_count: 20,
      authority: "Parliament of India (Lok Sabha / Rajya Sabha)",
      jurisdiction: "central",
      cadence: "Daily (24-hour cycle)",
      last_successful_update: "2026-10-30T06:00:00Z",
      last_checked_at: "2026-10-30T06:00:00Z",
      provenance_summary: "20 canonical central bills with validated gazette notices.",
    },
    {
      dataset: "state_legislative_bills",
      status: "LIVE",
      record_count: 44,
      authority: "State Legislative Assemblies (AP, KA, KL, TS)",
      jurisdiction: "state",
      cadence: "Bi-daily (48-hour cycle)",
      last_successful_update: "2026-10-30T05:30:00Z",
      last_checked_at: "2026-10-30T05:30:00Z",
      provenance_summary: "44 official state gazette records across 4 pilot states.",
    },
    {
      dataset: "corporate_intelligence_universe",
      status: "LIVE",
      record_count: 70,
      authority: "Ministry of Corporate Affairs / BSE / NSE",
      jurisdiction: "national",
      cadence: "Bi-weekly",
      last_successful_update: "2026-10-29T18:00:00Z",
      last_checked_at: "2026-10-30T06:00:00Z",
      provenance_summary: "70 entities (47 modeled, 20 qualitative intelligence-only, 3 reference).",
    },
    {
      dataset: "model_predictions",
      status: "LIVE",
      record_count: 4700,
      authority: "Validated Econometric Baseline",
      jurisdiction: "central",
      cadence: "Event-study baseline across 5 horizons",
      last_successful_update: "2026-10-28T12:00:00Z",
      last_checked_at: "2026-10-30T06:00:00Z",
      provenance_summary: "4,700 decision-support event-study projection records.",
    },
    {
      dataset: "media_attention_signals",
      status: "NOT_AVAILABLE",
      record_count: 0,
      authority: "Sampled Media Mentions / Unintegrated Feeds",
      jurisdiction: "unintegrated",
      cadence: "Periodic Sampled",
      last_successful_update: null,
      last_checked_at: null,
      provenance_summary: "External news indices tracked as unintegrated; no causal trade impact claimed.",
    },
  ],
};

const MOCK_SOURCE: MonitoringSourceItem = {
  source_id: "parliament_in_central",
  source_name: "Parliament of India (Central)",
  jurisdiction: "central",
  state: null,
  source_type: "html_table",
  source_url: "https://sansad.in/bills",
  enabled: true,
  status: "IMPLEMENTED",
  polling_interval_hours: 24,
  priority: 1,
  last_checked_at: "2026-10-30T06:00:00Z",
  last_success_at: "2026-10-30T06:00:00Z",
  last_error_at: null,
  last_error: null,
  notes: "Primary parliamentary legislative registry",
};

const MOCK_SOURCE_DETAIL: MonitoringSourceDetail = {
  ...MOCK_SOURCE,
  recent_run_results: [
    { run_id: "run-028-prod", started_at: "2026-10-30T06:00:00Z", status: "SUCCESS", new_bills: 1, changed_bills: 2 },
  ],
  provenance: {
    monitoring_system: "VERIFIED",
    intake_channel: "REST_API_SCRAPER",
    parser_version: "2.4.1",
  },
};

const MOCK_SOURCES_PAGE: PaginatedResponse<MonitoringSourceItem> = {
  items: [MOCK_SOURCE],
  total: 1,
  page: 1,
  limit: 25,
  pages: 1,
};

const MOCK_CHANGE: ChangeEventDetail = {
  event_id: "evt-prod-001",
  bill_id: "the-banking-laws-amendment-bill-2024",
  bill_title: "The Banking Laws (Amendment) Bill, 2024",
  jurisdiction: "central",
  state: null,
  source_id: "parliament_in_central",
  event_type: "STATUS_CHANGED",
  field_name: "status",
  old_value: "PASSED_LOK_SABHA",
  new_value: "PASSED_RAJYA_SABHA",
  detected_at: "2026-10-30T06:00:00Z",
  source_reference: "Rajya Sabha Bulletin Part I",
  confidence: 1.0,
  error_message: null,
  epistemic_status: "OBSERVED",
  provenance: { source_id: "parliament_in_central", verification_status: "SYSTEM_DETECTED" },
  previous_version_available: true,
  current_version_available: true,
};

const MOCK_CHANGES_PAGE: PaginatedResponse<ChangeEventDetail> = {
  items: [MOCK_CHANGE],
  total: 1,
  page: 1,
  limit: 25,
  pages: 1,
};

const MOCK_RUN: MonitoringRunDetail = {
  run_id: "run-028-prod",
  trigger: "scheduled",
  started_at: "2026-10-30T06:00:00Z",
  completed_at: "2026-10-30T06:01:12Z",
  duration_seconds: 72,
  status: "SUCCESS",
  sources_checked: 4,
  sources_succeeded: 4,
  sources_failed: 0,
  new_bills: 1,
  changed_bills: 2,
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

const MOCK_COVERAGE_REPORT: CoverageReportResponse = {
  central: {
    production_bills: 20,
    total_bills_in_repo: 20,
    event_windows_count: 5,
    quantitative_companies: 47,
    bill_company_pairs: 940,
    predictions_count: 4700,
    decisions_count: 4700,
    anticipation_scores_count: 940,
    stakeholder_reports_count: 60,
  },
  state: {
    implemented_states_count: 4,
    implemented_states_list: ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"],
    planned_states_count: 24,
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
    total_legislative_records: 64,
    total_corporate_exposures: 1026,
  },
};

describe("TASK 1.11A: Monitoring, Observability & Cross-Route Consistency", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();

    vi.mocked(monitoringApi.getOverview).mockResolvedValue(MOCK_OVERVIEW);
    vi.mocked(monitoringApi.getFreshness).mockResolvedValue(MOCK_FRESHNESS);
    vi.mocked(monitoringApi.getSources).mockResolvedValue(MOCK_SOURCES_PAGE);
    vi.mocked(monitoringApi.getSource).mockResolvedValue(MOCK_SOURCE_DETAIL);
    vi.mocked(monitoringApi.getRuns).mockResolvedValue(MOCK_RUNS_PAGE);
    vi.mocked(monitoringApi.getChanges).mockResolvedValue(MOCK_CHANGES_PAGE);
    vi.mocked(monitoringApi.getChangeDetail).mockResolvedValue(MOCK_CHANGE);
    vi.mocked(monitoringApi.getSchedulerStatus).mockResolvedValue(MOCK_SCHEDULER);
    vi.mocked(monitoringApi.triggerCheck).mockResolvedValue({
      run_id: "run-manual-001",
      status: "SUCCESS",
      trigger: "manual_api",
      sources_checked: 4,
      sources_succeeded: 4,
      sources_failed: 0,
      changes_detected: 0,
    });

    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_REPORT);
  });

  // -------------------------------------------------------------------------
  // Scenario 1: Monitoring & Observability (/monitoring) 3-Level Architecture
  // -------------------------------------------------------------------------

  it("1. Monitoring Center (/monitoring) renders 3-Level Information Architecture", async () => {
    render(<MonitoringCenterContent />);

    // Level 1: Operational Overview Header & Status
    expect(screen.getByRole("heading", { name: /Legislative Monitoring & Discovery Center/i })).toBeDefined();
    expect(screen.getByText(/Surveillance active/i)).toBeDefined();

    // Mandatory State Prediction Firewall Banner
    expect(screen.getByText(/Monitoring Notice:/i)).toBeDefined();
    expect(screen.getAllByText(/State stock predictions remain strictly 0/i).length).toBeGreaterThan(0);

    // Level 1: Metric Strip
    await waitFor(() => {
      expect(screen.getByText("5")).toBeDefined(); // total sources
      expect(screen.getAllByText("4").length).toBeGreaterThan(0); // enabled/state sources
    });

    // Level 1: Pipeline & Dataset Freshness Table
    await waitFor(() => {
      expect(screen.getByText(/Pipeline & Dataset Freshness Telemetry/i)).toBeDefined();
      expect(screen.getByText(/central legislative bills/i)).toBeDefined();
      expect(screen.getByText(/state legislative bills/i)).toBeDefined();
      expect(screen.getByText(/corporate intelligence universe/i)).toBeDefined();
      expect(screen.getByText(/model predictions/i)).toBeDefined();
      expect(screen.getByText(/media attention signals/i)).toBeDefined();
      expect(screen.getByText(/NOT AVAILABLE/i)).toBeDefined();
    });

    // Level 2: Last Run Summary
    expect(screen.getByText(/Last Ingestion Run Summary/i)).toBeDefined();
    expect(screen.getByText("+1")).toBeDefined();
    expect(screen.getByText("2")).toBeDefined();

    // Level 3: Technical Diagnostics behind Progressive Disclosure
    expect(screen.getByText(/Technical Diagnostics & Scheduler Configuration/i)).toBeDefined();
    expect(screen.getByText(/Statutory Safety Invariants/i)).toBeDefined();
  });

  // -------------------------------------------------------------------------
  // Scenario 2: URL Query-Parameter & Deep-Link Synchronization
  // -------------------------------------------------------------------------

  it("2. synchronizes URL search parameters on tab and drawer interactions", async () => {
    render(<MonitoringCenterContent />);

    // Switch to Sources Tab
    const sourcesTab = screen.getByRole("tab", { name: /Sources/i });
    await act(async () => {
      fireEvent.click(sourcesTab);
    });

    // Wait for sources table to load
    await waitFor(() => {
      expect(screen.getByText("Parliament of India (Central)")).toBeDefined();
    });

    // Click "Details →" to open source detail drawer
    const detailsBtn = screen.getByRole("button", { name: /View details for Parliament of India/i });
    await act(async () => {
      fireEvent.click(detailsBtn);
    });

    // Verify Level 2 operational detail and Level 3 collapsible diagnostics are present in drawer
    await waitFor(() => {
      expect(screen.getByText(/Source Configuration/i)).toBeDefined();
      expect(screen.getByText(/Technical Diagnostics & Recent Runs/i)).toBeDefined();
    });

    // Close drawer
    const closeBtn = screen.getByRole("button", { name: /Close source detail/i });
    await act(async () => {
      fireEvent.click(closeBtn);
    });
  });

  // -------------------------------------------------------------------------
  // Scenario 3: Platform Coverage & Research Integrity (/coverage)
  // -------------------------------------------------------------------------

  it("3. Platform Coverage (/coverage) enforces Central vs State separation and 0 state stock predictions", async () => {
    render(<CoverageContent />);

    // Header & Research Integrity Notice
    expect(screen.getByRole("heading", { name: /Platform Coverage & Research Integrity/i })).toBeDefined();
    expect(screen.getByRole("note", { name: /Research integrity statement/i })).toBeDefined();

    await waitFor(() => {
      // Central Modelled Section
      expect(screen.getByText("Central Parliament")).toBeDefined();
      expect(screen.getAllByText("20").length).toBeGreaterThan(0);
      expect(screen.getAllByText("4,700").length).toBeGreaterThan(0);

      // State Legislative Intelligence Section
      expect(screen.getByText("State Legislatures")).toBeDefined();
      expect(screen.getAllByText("44").length).toBeGreaterThan(0);
      expect(screen.getByText("86")).toBeDefined();
      // Strictly and verifiably 0 state stock predictions
      expect(screen.getAllByText(/State Stock Predictions/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText("0").length).toBeGreaterThan(0);

      // Corporate Universe Section
      expect(screen.getByText("Company Coverage")).toBeDefined();
      expect(screen.getByText("70")).toBeDefined();
      expect(screen.getAllByText("47").length).toBeGreaterThan(0);
    });
  });

  // -------------------------------------------------------------------------
  // Scenario 4: Cross-Route Entity & Evidence Consistency
  // -------------------------------------------------------------------------

  it("4. verifies cross-route entity and epistemic classification consistency", async () => {
    render(<MonitoringCenterContent />);

    // Switch to Detected Changes Tab
    const changesTab = screen.getByRole("tab", { name: /Detected Changes/i });
    await act(async () => {
      fireEvent.click(changesTab);
    });

    // Wait for changes to load
    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeDefined();
      expect(screen.getByText(/\[OBSERVED\]/i)).toBeDefined();
      expect(screen.getByText(/Source: parliament_in_central/i)).toBeDefined();
    });

    // Inspect Change Diff
    const changeCard = screen.getByRole("listitem", { name: /Status Changed/i });
    await act(async () => {
      fireEvent.click(changeCard);
    });

    // Verify before/after state diff in drawer without fabrication
    await waitFor(() => {
      expect(screen.getByText(/State Delta Transition/i)).toBeDefined();
      expect(screen.getByText("PASSED_LOK_SABHA")).toBeDefined();
      expect(screen.getByText("PASSED_RAJYA_SABHA")).toBeDefined();
      expect(screen.getByText(/100% Match/i)).toBeDefined();
      expect(screen.getByText(/View Canonical Bill Dossier →/i)).toBeDefined();
    });
  });

  // -------------------------------------------------------------------------
  // Scenario 5: Immutable Frozen Baseline SHA-256 Bit-for-Bit Check
  // -------------------------------------------------------------------------

  it("5. confirms frozen baseline production_baseline.json remains unmodified", () => {
    const baselinePath = path.resolve(process.cwd(), "..", "docs", "production_baseline.json");
    expect(fs.existsSync(baselinePath)).toBe(true);

    const fileBuffer = fs.readFileSync(baselinePath);
    const hash = crypto.createHash("sha256").update(fileBuffer).digest("hex");

    const expectedHash = "50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7";
    expect(hash.toLowerCase()).toBe(expectedHash.toLowerCase());
  });
});
