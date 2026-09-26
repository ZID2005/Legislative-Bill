/**
 * __tests__/pages/alerts.test.tsx
 * ===============================
 * Unit and integration tests for the Alerts Center page (Task 8.15).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AlertsPage from "@/app/alerts/page";

// Mock Next.js navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/alerts",
  useSearchParams: () => new URLSearchParams(""),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock alerts API
vi.mock("@/lib/api/alerts", () => ({
  alertsApi: {
    listAlerts: vi.fn(),
    getUnreadCount: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    archive: vi.fn(),
  },
}));

import { alertsApi } from "@/lib/api/alerts";

describe("AlertsPage Component", () => {
  const mockAlerts = {
    items: [
      {
        alert_event_id: "evt_1",
        user_id: "u_1",
        tenant_id: "t_1",
        watchlist_id: "wl_1",
        alert_type: "BILL_STATUS_CHANGE",
        severity: "HIGH",
        title: "Status Change - Coastal Shipping Bill",
        summary: "Passed Lok Sabha with official amendments.",
        entity_type: "BILL",
        entity_id: "the-coastal-shipping-bill-2024",
        is_read: false,
        is_archived: false,
        created_at: "2026-09-20T10:00:00Z",
        metadata: {},
      },
      {
        alert_event_id: "evt_2",
        user_id: "u_1",
        tenant_id: "t_1",
        watchlist_id: "wl_1",
        alert_type: "RISK_LEVEL_UPGRADE",
        severity: "MEDIUM",
        title: "Risk Upgrade - Zomato Limited",
        summary: "Elevated compliance risk identified.",
        entity_type: "COMPANY",
        entity_id: "INE758T01015",
        is_read: true,
        is_archived: false,
        created_at: "2026-09-20T09:00:00Z",
        metadata: {},
      },
    ],
    total: 2,
    page: 1,
    limit: 20,
    pages: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(alertsApi.listAlerts).mockResolvedValue(mockAlerts);
    vi.mocked(alertsApi.getUnreadCount).mockResolvedValue({ unread_count: 1, user_id: "u_1", tenant_id: "t_1" });
  });

  it("renders alerts with title, severity badges, and unread indicator", async () => {
    render(<AlertsPage />);

    expect(await screen.findByText("Legislative Alerts")).toBeInTheDocument();
    expect(screen.getByText("Status Change - Coastal Shipping Bill")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText("MEDIUM")).toBeInTheDocument();
  });

  it("calls markAsRead when 'Mark Read' button is clicked", async () => {
    vi.mocked(alertsApi.markAsRead).mockResolvedValue(undefined);

    render(<AlertsPage />);

    const markReadBtn = await screen.findByText("Mark Read");
    fireEvent.click(markReadBtn);

    await waitFor(() => {
      expect(alertsApi.markAsRead).toHaveBeenCalledWith("evt_1");
    });
  });

  it("calls markAllAsRead when 'Mark All As Read' is clicked", async () => {
    vi.mocked(alertsApi.markAllAsRead).mockResolvedValue(undefined);

    render(<AlertsPage />);

    const markAllBtn = await screen.findByText(/Mark All As Read \(1\)/i);
    fireEvent.click(markAllBtn);

    await waitFor(() => {
      expect(alertsApi.markAllAsRead).toHaveBeenCalled();
    });
  });
});
