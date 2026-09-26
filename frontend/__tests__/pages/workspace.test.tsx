/**
 * __tests__/pages/workspace.test.tsx
 * ===================================
 * Unit and component tests for the Personalized Legislative Workspace (Task 8.15).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { WorkspacePage } from "@/app/workspace/page";

// Mock Next.js navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/workspace",
  useSearchParams: () => new URLSearchParams(""),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock Workspace API
vi.mock("@/lib/api/workspace", () => ({
  workspaceApi: {
    getSummary: vi.fn(),
    getActivity: vi.fn(),
    getWatchlistActivity: vi.fn(),
    getAnalyticsSnapshot: vi.fn(),
    getDigests: vi.fn(),
  },
}));

// Mock AI API
vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
  },
}));

import { workspaceApi } from "@/lib/api/workspace";
import { aiApi } from "@/lib/api/ai";

describe("WorkspacePage Component", () => {
  const mockSummary = {
    user_id: "user_test",
    tenant_id: "tenant_test",
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
    last_activity_at: "2026-09-20T10:00:00Z",
  };

  const mockActivity = {
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
        timestamp: "2026-09-20T10:00:00Z",
        deep_link: "/bills/the-coastal-shipping-bill-2024",
        provenance: {},
      },
      {
        activity_id: "alert_102",
        activity_type: "RISK_LEVEL_UPGRADE",
        epistemic_status: "DERIVED",
        title: "Risk Upgrade: Zomato Limited",
        summary: "Regulatory compliance exposure elevated.",
        entity_type: "COMPANY",
        entity_id: "INE758T01015",
        entity_name: "Zomato Limited",
        jurisdiction: "central",
        state: null,
        severity: "MEDIUM",
        timestamp: "2026-09-20T09:30:00Z",
        deep_link: "/companies/INE758T01015",
        provenance: {},
      },
    ],
    total: 2,
    epistemic_notice: "Verified",
  };

  const mockGrouped = {
    bills: [
      {
        entity_type: "BILL",
        entity_id: "the-coastal-shipping-bill-2024",
        entity_name: "The Coastal Shipping Bill, 2024",
        jurisdiction: "central",
        state: null,
        watchlist_id: "wl_1",
        watchlist_name: "Maritime & Trade",
        notes: "High priority",
        latest_activity: "Added to 'Maritime & Trade'",
        last_activity_at: "2026-09-20T08:00:00Z",
        alert_count: 2,
        deep_link: "/bills/the-coastal-shipping-bill-2024",
        extra_metadata: {},
      },
    ],
    companies: [
      {
        entity_type: "COMPANY",
        entity_id: "INE758T01015",
        entity_name: "Zomato Limited",
        jurisdiction: "central",
        state: null,
        watchlist_id: "wl_1",
        watchlist_name: "Maritime & Trade",
        notes: null,
        latest_activity: "Added to 'Maritime & Trade'",
        last_activity_at: "2026-09-20T08:00:00Z",
        alert_count: 1,
        deep_link: "/companies/INE758T01015",
        extra_metadata: {
          sector: "Consumer Services",
          is_quant_eligible: true,
          universe_type: "QUANTITATIVE",
        },
      },
    ],
    industries: [],
    jurisdictions: [],
    total_watched: 2,
  };

  const mockAnalytics = {
    items: [
      {
        entity_type: "COMPANY",
        entity_id: "INE758T01015",
        entity_name: "Zomato Limited",
        epistemic_label: "[PREDICTION]",
        risk_level: "MODERATE",
        risk_score: 0.54,
        anticipation_tier: "MODERATE_EVIDENCE",
        anticipation_score: 0.62,
        prediction_record: {
          prediction_id: "pred_1",
          direction: "POSITIVE",
          confidence: "HIGH",
          bill_id: "the-coastal-shipping-bill-2024",
        },
        is_state_firewall_active: false,
        is_intelligence_firewall_active: false,
        firewall_note: null,
        updated_at: "2026-09-20T08:00:00Z",
      },
      {
        entity_type: "BILL",
        entity_id: "mh-state-bill-1",
        entity_name: "Maharashtra Land Revenue Amendment Bill",
        epistemic_label: "[DERIVED]",
        risk_level: "MEDIUM",
        risk_score: null,
        anticipation_tier: null,
        anticipation_score: null,
        prediction_record: null,
        is_state_firewall_active: true,
        is_intelligence_firewall_active: false,
        firewall_note: "State stock predictions remain strictly 0.",
        updated_at: "2026-09-20T08:00:00Z",
      },
    ],
    total_items: 2,
    epistemic_disclaimer: "Strict Epistemic Governance",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceApi.getSummary).mockResolvedValue(mockSummary);
    vi.mocked(workspaceApi.getActivity).mockResolvedValue(mockActivity);
    vi.mocked(workspaceApi.getWatchlistActivity).mockResolvedValue(mockGrouped);
    vi.mocked(workspaceApi.getAnalyticsSnapshot).mockResolvedValue(mockAnalytics);
  });

  it("renders workspace title, description, and attention summary metrics", async () => {
    render(<WorkspacePage />);

    expect(await screen.findByText("Your Legislative Workspace")).toBeInTheDocument();
    expect(screen.getByText("Personalized Decision Center")).toBeInTheDocument();

    // Check attention summary numbers
    expect(screen.getByText("3")).toBeInTheDocument(); // unread notifs
    expect(screen.getByText("5")).toBeInTheDocument(); // active alerts
    expect(screen.getByText("4")).toBeInTheDocument(); // watched bills
    expect(screen.getByText("6")).toBeInTheDocument(); // watched companies
  });

  it("renders epistemic badges [OBSERVED], [DERIVED], and [PREDICTION]", async () => {
    render(<WorkspacePage />);

    await waitFor(() => {
      expect(screen.getByText("[OBSERVED]")).toBeInTheDocument();
      expect(screen.getAllByText("[DERIVED]").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("[PREDICTION]").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("enforces and displays the State Prediction Firewall notice", async () => {
    render(<WorkspacePage />);

    await waitFor(() => {
      expect(
        screen.getByText(/State Prediction Firewall Active/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/State stock predictions remain strictly 0/i)
      ).toBeInTheDocument();
    });
  });

  it("renders the grounded AI Workspace Assistant with prompt chips", async () => {
    render(<WorkspacePage />);

    expect(await screen.findByText("Workspace AI Assistant")).toBeInTheDocument();
    expect(screen.getByText("What changed in my watchlists?")).toBeInTheDocument();
    expect(screen.getByText("Summarize my unread alerts.")).toBeInTheDocument();
  });

  it("submits AI question when prompt chip is clicked", async () => {
    vi.mocked(aiApi.ask).mockResolvedValue({
      question: "What changed in my watchlists?",
      context_type: "workspace",
      context_id: "workspace_home",
      persona: "INVESTOR",
      content: "Recent legislative updates: The Coastal Shipping Bill passed Lok Sabha.",
      operation: "ask",
      success: true,
      is_cached: false,
      disclaimer: "Institutional research only.",
      provenance_sources: ["the-coastal-shipping-bill-2024"],
      grounding_sources: ["the-coastal-shipping-bill-2024"],
      model: "Groq LLaMA 3.3 70B",
    });

    render(<WorkspacePage />);

    const chip = await screen.findByText("What changed in my watchlists?");
    fireEvent.click(chip);

    await waitFor(() => {
      expect(aiApi.ask).toHaveBeenCalledWith({
        question: "What changed in my watchlists?",
        context_type: "workspace",
        context_id: "workspace_home",
        persona: "INVESTOR",
      });
    });

    expect(
      await screen.findByText(/Recent legislative updates: The Coastal Shipping Bill passed Lok Sabha/i)
    ).toBeInTheDocument();
  });
});
