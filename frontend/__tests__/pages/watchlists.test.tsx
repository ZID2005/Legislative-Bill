/**
 * __tests__/pages/watchlists.test.tsx
 * ===================================
 * Unit and integration tests for the Watchlists page (Task 8.15).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WatchlistsPage from "@/app/watchlists/page";

// Mock Next.js navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/watchlists",
  useSearchParams: () => new URLSearchParams(""),
}));

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock watchlists API
vi.mock("@/lib/api/watchlists", () => ({
  watchlistsApi: {
    listWatchlists: vi.fn(),
    createWatchlist: vi.fn(),
    updateWatchlist: vi.fn(),
    deleteWatchlist: vi.fn(),
  },
}));

import { watchlistsApi } from "@/lib/api/watchlists";

describe("WatchlistsPage Component", () => {
  const mockWatchlists = [
    {
      watchlist_id: "wl_test_1",
      user_id: "user_test",
      tenant_id: "tenant_test",
      name: "Energy & Infrastructure",
      description: "Critical maritime and renewable energy bills",
      is_default: false,
      is_active: true,
      created_at: "2026-09-20T08:00:00Z",
      updated_at: "2026-09-20T08:00:00Z",
      items_count: 1,
      items: [
        {
          item_id: "it_1",
          watchlist_id: "wl_test_1",
          entity_type: "BILL",
          entity_id: "the-coastal-shipping-bill-2024",
          canonical_name: "The Coastal Shipping Bill, 2024",
          display_name: "The Coastal Shipping Bill, 2024",
          is_active: true,
          created_at: "2026-09-20T08:00:00Z",
        },
      ],
      rules: [
        {
          alert_rule_id: "r_1",
          rule_id: "r_1",
          user_id: "user_test",
          tenant_id: "tenant_test",
          watchlist_id: "wl_test_1",
          alert_type: "BILL_STATUS_CHANGE",
          minimum_severity: "MEDIUM",
          notification_channels: ["IN_APP"],
          enabled: true,
          created_at: "2026-09-20T08:00:00Z",
        },
      ],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(watchlistsApi.listWatchlists).mockResolvedValue(mockWatchlists);
  });

  it("renders watchlist cards with name, description, and item counts", async () => {
    render(<WatchlistsPage />);

    expect(await screen.findByText("Entity Watchlists")).toBeInTheDocument();
    expect(screen.getByText("Energy & Infrastructure")).toBeInTheDocument();
    expect(screen.getByText(/1 items/i)).toBeInTheDocument();
    expect(screen.getByText(/1 rules/i)).toBeInTheDocument();
  });

  it("opens create modal and submits new watchlist", async () => {
    vi.mocked(watchlistsApi.createWatchlist).mockResolvedValue({
      watchlist_id: "wl_test_2",
      user_id: "user_test",
      tenant_id: "tenant_test",
      name: "Pharma Portfolio",
      description: "Healthcare policy tracking",
      is_default: false,
      is_active: true,
      created_at: "2026-09-20T11:00:00Z",
      updated_at: "2026-09-20T11:00:00Z",
      items_count: 0,
      items: [],
      rules: [],
    });

    render(<WatchlistsPage />);

    const createBtn = await screen.findByText("Create Watchlist");
    fireEvent.click(createBtn);

    expect(screen.getByText("Create New Watchlist")).toBeInTheDocument();

    const nameInput = screen.getByPlaceholderText(/e.g. Energy & Critical Minerals Portfolio/i);
    fireEvent.change(nameInput, { target: { value: "Pharma Portfolio" } });

    const submitBtn = screen.getByRole("button", { name: "Create Watchlist" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(watchlistsApi.createWatchlist).toHaveBeenCalledWith({
        name: "Pharma Portfolio",
        description: undefined,
      });
    });
  });

  it("shows empty state when no watchlists are returned", async () => {
    vi.mocked(watchlistsApi.listWatchlists).mockResolvedValue([]);

    render(<WatchlistsPage />);

    expect(await screen.findByText("No Watchlists Yet")).toBeInTheDocument();
    expect(screen.getByText("Create Your First Watchlist")).toBeInTheDocument();
  });
});
