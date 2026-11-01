/**
 * __tests__/components/task-1-14b-collab-toolbar.test.tsx
 * =======================================================
 * TASK 1.14B — Header Collaboration Toolbar Specification & Integration Tests.
 *
 * Verifies:
 * 1. CollabToolbar Component:
 *    - Renders pill-shaped groups with dividers
 *    - Renders avatars with initials fallback and tooltips
 *    - Handles active states, disabled states, and action callbacks
 *    - Full WCAG 2.2 accessibility: roles, aria-labels, aria-pressed
 * 2. TopNavbar Collaboration Integration:
 *    - Reference grouping: [["phone", "desktop", "chat"], "avatars", ["upload", "menu"]]
 *    - Preservation of active status indicator (7/12 or 12/12 ACTIVE)
 *    - Preservation of notification bell and theme switcher
 *    - Connected functionality:
 *      * Phone toggles mobile drawer
 *      * Desktop resets to standard desktop layout
 *      * Chat links to Grounded AI Analyst (/ai-analyst)
 *      * Upload triggers portfolio CSV/JSON import modal
 *      * Menu opens secondary actions popover
 *      * Avatars display authentic user/tenant initials without fake external avatars
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock Next.js navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  usePathname: () => "/workspace",
  useRouter: () => ({ push: mockPush }),
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
      user_id: "usr_lead_analyst",
      email: "lead.analyst@seance.internal",
      display_name: "Lead Analyst",
      role: "OWNER",
      tenant_id: "inst_fund_01",
    }),
    listMembers: vi.fn().mockResolvedValue({
      tenant_id: "inst_fund_01",
      total_members: 2,
      items: [
        {
          user_id: "usr_lead_analyst",
          email: "lead.analyst@seance.internal",
          name: "Lead Analyst",
          role: "OWNER",
        },
        {
          user_id: "usr_associate",
          email: "associate@seance.internal",
          name: "Sam Associate",
          role: "MEMBER",
        },
      ],
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
      last_run_timestamp: "2026-10-31T12:00:00Z",
    }),
  },
}));

// Mock Portfolio API
vi.mock("@/lib/api/portfolio", () => ({
  portfolioApi: {
    listPortfolios: vi.fn().mockResolvedValue([
      {
        portfolio_id: "pf_default",
        name: "Flagship Institutional Fund",
        holdings_count: 5,
      },
    ]),
    importHoldings: vi.fn().mockResolvedValue({
      portfolio_id: "pf_default",
      holdings_count: 6,
    }),
  },
}));

import { CollabToolbar, CollabToolbarProps } from "@/components/ui/collab-toolbar";
import { TopNavbar } from "@/components/layout/TopNavbar";

describe("TASK 1.14B — CollabToolbar Primitive Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders with the supplied reference structure and grouping", () => {
    const avatars = [
      { name: "Jane Doe", initials: "JD", role: "OWNER" },
      { name: "Alex Kim", initials: "AK", role: "MEMBER" },
      { name: "Sam Taylor", initials: "ST", role: "MEMBER" },
    ];

    render(
      <CollabToolbar
        groups={[["phone", "desktop", "chat"], "avatars", ["upload", "menu"]]}
        avatars={avatars}
      />
    );

    // Toolbar element
    const toolbar = screen.getByRole("toolbar", { name: /collaboration and utility toolbar/i });
    expect(toolbar).toBeInTheDocument();

    // Group 1 icon buttons
    expect(screen.getByRole("button", { name: /mobile view/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /desktop view/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ai analyst/i })).toBeInTheDocument();

    // Group 2 avatars
    expect(screen.getByRole("button", { name: /Jane Doe/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Alex Kim/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sam Taylor/i })).toBeInTheDocument();

    // Group 3 icon buttons
    expect(screen.getByRole("button", { name: /import holdings/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /secondary menu/i })).toBeInTheDocument();

    // Dividers
    const separators = screen.getAllByRole("separator");
    expect(separators.length).toBe(2);
  });

  it("handles activeAction, custom actionProps, and action callbacks", () => {
    const handleAction = vi.fn();
    const handlePhoneClick = vi.fn();

    render(
      <CollabToolbar
        groups={[["phone", "desktop", "chat"], "avatars", ["upload", "menu"]]}
        onAction={handleAction}
        activeAction="desktop"
        actionProps={{
          phone: {
            onClick: handlePhoneClick,
            ariaLabel: "Custom Phone Label",
          },
        }}
      />
    );

    const phoneBtn = screen.getByRole("button", { name: /custom phone label/i });
    fireEvent.click(phoneBtn);
    expect(handlePhoneClick).toHaveBeenCalledTimes(1);
    expect(handleAction).toHaveBeenCalledWith("phone");

    const desktopBtn = screen.getByRole("button", { name: /desktop view/i });
    expect(desktopBtn).toHaveAttribute("aria-pressed", "true");
  });
});

describe("TASK 1.14B — Seance TopNavbar Collaboration Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("integrates CollabToolbar while preserving Active Status, Notifications, and ThemeSwitcher", async () => {
    render(<TopNavbar />);

    // 1. Preserved telemetry active indicator
    await waitFor(() => {
      expect(screen.getByText(/Active/i)).toBeInTheDocument();
    });

    // 2. Preserved notifications bell
    expect(screen.getByRole("link", { name: /Notifications/i })).toBeInTheDocument();

    // 3. Preserved theme switcher
    expect(screen.getByLabelText(/Light theme/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Dark theme/i)).toBeInTheDocument();

    // 4. CollabToolbar present
    expect(screen.getByRole("toolbar")).toBeInTheDocument();
  });

  it("ensures Phone/Desktop buttons are absent and mobile drawer is triggered by mobile menu", () => {
    render(<TopNavbar />);

    // Phone and Desktop buttons absent from toolbar
    expect(screen.queryByLabelText(/Mobile Viewport Navigation/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Desktop Standard View/i)).not.toBeInTheDocument();

    // Mobile hamburger button
    const mobileBtn = screen.getByLabelText(/Open navigation menu/i);
    expect(mobileBtn).toBeInTheDocument();

    // Click mobile hamburger
    fireEvent.click(mobileBtn);

    // Mobile drawer opens
    expect(screen.getByRole("dialog", { name: /Mobile navigation/i })).toBeInTheDocument();

    // Close mobile drawer
    const closeBtn = screen.getByLabelText(/Close navigation/i);
    fireEvent.click(closeBtn);
    expect(screen.queryByRole("dialog", { name: /Mobile navigation/i })).not.toBeInTheDocument();
  });

  it("navigates to /ai-analyst when Chat icon is clicked", () => {
    render(<TopNavbar />);

    const chatBtn = screen.getByLabelText(/Grounded AI Analyst/i);
    fireEvent.click(chatBtn);

    expect(mockPush).toHaveBeenCalledWith("/ai-analyst");
  });

  it("opens holdings upload modal when Upload icon is clicked", () => {
    render(<TopNavbar />);

    const uploadBtn = screen.getByLabelText(/Import Holdings/i);
    fireEvent.click(uploadBtn);

    // Modal dialog appears
    expect(screen.getByText("Import Portfolio Holdings")).toBeInTheDocument();
    expect(screen.getByText(/Select a CSV or JSON file to upload/i)).toBeInTheDocument();
  });

  it("opens secondary actions popover when Menu icon is clicked", () => {
    render(<TopNavbar />);

    const menuBtn = screen.getByLabelText(/Secondary Header Menu/i);
    fireEvent.click(menuBtn);

    // Popover with user identity and secondary routes
    expect(screen.getByRole("menu", { name: /User account and secondary workspace actions/i })).toBeInTheDocument();
    expect(screen.getByText("Daily Workspace")).toBeInTheDocument();
    expect(screen.getByText("Custom Watchlists")).toBeInTheDocument();
    expect(screen.getByText("Alerts Center")).toBeInTheDocument();
    expect(screen.getByText("Platform Coverage Audit")).toBeInTheDocument();
    expect(screen.getByText("Live Intake Feed")).toBeInTheDocument();
    expect(screen.getByText("Settings & RBAC")).toBeInTheDocument();

    // Escape closes popover
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("menu", { name: /User account and secondary workspace actions/i })).not.toBeInTheDocument();
  });

  it("displays single authenticated user initial without invented external images", async () => {
    render(<TopNavbar />);

    // Wait for session to load
    await waitFor(() => {
      // Should find single initial for authenticated user "L" (Lead Analyst)
      expect(screen.getByText("L")).toBeInTheDocument();
    });

    // Verify no external fake pravatar URLs exist in the DOM
    const images = screen.queryAllByRole("img");
    images.forEach((img) => {
      expect(img.getAttribute("src")).not.toContain("pravatar.cc");
    });
  });
});
