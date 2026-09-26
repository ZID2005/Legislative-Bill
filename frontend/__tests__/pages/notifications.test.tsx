/**
 * __tests__/pages/notifications.test.tsx
 * ======================================
 * Unit and integration tests for the Notification Center page (Task 8.15).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import NotificationsPage from "@/app/notifications/page";

// Mock Next.js navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/notifications",
  useSearchParams: () => new URLSearchParams(""),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock notifications API
vi.mock("@/lib/api/notifications", () => ({
  notificationsApi: {
    listNotifications: vi.fn(),
    getSummary: vi.fn(),
    getDigests: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    archive: vi.fn(),
  },
}));

import { notificationsApi } from "@/lib/api/notifications";

describe("NotificationsPage Component", () => {
  const mockNotifications = {
    items: [
      {
        notification_id: "notif_1",
        user_id: "u_1",
        tenant_id: "t_1",
        notification_type: "ALERT",
        severity: "MEDIUM",
        title: "Legislative Alert: Coastal Shipping Bill",
        message: "The Coastal Shipping Bill passed Lok Sabha with amendments.",
        status: "DELIVERED",
        is_read: false,
        is_archived: false,
        created_at: "2026-09-20T10:00:00Z",
      },
    ],
    total: 1,
    page: 1,
    limit: 20,
    pages: 1,
  };

  const mockSummary = {
    tenant_id: "t_1",
    user_id: "u_1",
    total_active: 5,
    unread_count: 1,
    archived_count: 0,
    alert_count: 5,
    digest_count: 1,
    counts_by_type: { ALERT: 5 },
    counts_by_severity: { HIGH: 1, MEDIUM: 4 },
  };

  const mockDigests = [
    {
      group_id: "grp_1",
      user_id: "u_1",
      tenant_id: "t_1",
      group_type: "ENTITY_BATCH",
      title: "Daily Digest - 3 Changes in Energy Portfolio",
      summary: "3 alerts occurred across monitored maritime and green energy bills.",
      severity: "MEDIUM",
      event_count: 3,
      created_at: "2026-09-20T08:00:00Z",
      alert_event_ids: ["evt_1", "evt_2", "evt_3"],
      sample_events: [],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockNotifications);
    vi.mocked(notificationsApi.getSummary).mockResolvedValue(mockSummary);
    vi.mocked(notificationsApi.getDigests).mockResolvedValue(mockDigests);
  });

  it("renders notification metrics and in-app feed item", async () => {
    render(<NotificationsPage />);

    expect(await screen.findByText("Notification Center")).toBeInTheDocument();
    expect(screen.getByText("Legislative Alert: Coastal Shipping Bill")).toBeInTheDocument();
    expect(screen.getByText("Unread In-App")).toBeInTheDocument();
    expect(screen.getByText("Total Delivered")).toBeInTheDocument();
  });

  it("switches to Aggregated Digests tab and displays digest cards", async () => {
    render(<NotificationsPage />);

    const digestTab = await screen.findByText(/Aggregated Digests \(1\)/i);
    fireEvent.click(digestTab);

    expect(
      await screen.findByText("Daily Digest - 3 Changes in Energy Portfolio")
    ).toBeInTheDocument();
    expect(screen.getByText(/3 alerts occurred across monitored maritime/i)).toBeInTheDocument();
  });

  it("calls markAsRead when 'Mark Read' is clicked", async () => {
    vi.mocked(notificationsApi.markAsRead).mockResolvedValue(undefined);

    render(<NotificationsPage />);

    const markReadBtn = await screen.findByText("Mark Read");
    fireEvent.click(markReadBtn);

    await waitFor(() => {
      expect(notificationsApi.markAsRead).toHaveBeenCalledWith("notif_1");
    });
  });
});
