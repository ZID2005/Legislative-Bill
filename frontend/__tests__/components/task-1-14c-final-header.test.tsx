/**
 * __tests__/components/task-1-14c-final-header.test.tsx
 * ======================================================
 * TASK 1.14C — Seance Final Header Toolbar Refinement:
 * Responsive Automation & Authenticated User Avatar Test Suite.
 *
 * Verifies:
 * 1. Initial Generation Fallback Ladder:
 *    - display_name ("Sanal" -> "S", "Alex" -> "A", "Rahul" -> "R", "Jane Doe" -> "J")
 *    - first_name fallback
 *    - email / user_id identifier fallback
 *    - neutral fallback "U" for missing/empty profile
 * 2. CollabToolbar Component:
 *    - Grouping: [["chat"], "avatar", ["upload", "menu"]]
 *    - Exactly one circular avatar
 *    - Phone and Desktop buttons completely removed
 *    - Exactly two separators between the three groups
 * 3. TopNavbar Header Integration:
 *    - Zero Phone/Desktop simulated toggle buttons
 *    - Responsive navigation driven by layout & CSS
 *    - Exactly one avatar matching authenticated user session
 *    - Avatar click toggles account & platform actions dropdown
 *    - Menu button toggles account & platform actions dropdown
 *    - Escape key closes dropdown
 *    - Outside click closes dropdown
 *    - Chat button navigates to /ai-analyst
 *    - Upload button triggers portfolio holdings import modal
 *    - Preserved telemetry pulse indicator (e.g. 12/12 Active)
 *    - Preserved notifications bell and ThemeSwitcher
 *    - Mobile drawer displays authenticated user initial
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

import {
  CollabToolbar,
  getAuthenticatedUserInitial,
} from "@/components/ui/collab-toolbar";
import { TopNavbar } from "@/components/layout/TopNavbar";

describe("TASK 1.14C — Initial Generation Fallback Ladder", () => {
  it("resolves uppercase first letter from authenticated user display_name", () => {
    expect(getAuthenticatedUserInitial({ display_name: "Sanal" })).toBe("S");
    expect(getAuthenticatedUserInitial({ display_name: "Alex" })).toBe("A");
    expect(getAuthenticatedUserInitial({ display_name: "Rahul" })).toBe("R");
    expect(getAuthenticatedUserInitial({ display_name: "Jane Doe" })).toBe("J");
  });

  it("resolves uppercase first letter from first_name or name when display_name is missing", () => {
    expect(getAuthenticatedUserInitial({ first_name: "sanal" })).toBe("S");
    expect(getAuthenticatedUserInitial({ name: "Alex Kumar" })).toBe("A");
  });

  it("resolves uppercase first letter from email or profile identifier when names are absent", () => {
    expect(getAuthenticatedUserInitial({ email: "rahul@institution.org" })).toBe("R");
    expect(getAuthenticatedUserInitial({ user_id: "usr_jane" })).toBe("J");
    expect(getAuthenticatedUserInitial({ id: "david" })).toBe("D");
  });

  it("falls back gracefully to neutral 'U' when profile identity is absent or empty", () => {
    expect(getAuthenticatedUserInitial(null)).toBe("U");
    expect(getAuthenticatedUserInitial(undefined)).toBe("U");
    expect(getAuthenticatedUserInitial({})).toBe("U");
    expect(getAuthenticatedUserInitial({ display_name: "   " })).toBe("U");
  });
});

describe("TASK 1.14C — CollabToolbar Refined Primitive", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders structure: [Chat] | [Single User Avatar] | [Upload] [Menu]", () => {
    const handleAvatarClick = vi.fn();
    const handleAction = vi.fn();

    render(
      <CollabToolbar
        groups={[["chat"], "avatar", ["upload", "menu"]]}
        userAvatar={{
          name: "Sanal Analyst",
          initials: "S",
          role: "OWNER",
          tenantId: "inst_alpha",
        }}
        onAvatarClick={handleAvatarClick}
        onAction={handleAction}
      />
    );

    // Toolbar element
    const toolbar = screen.getByRole("toolbar", { name: /collaboration and utility toolbar/i });
    expect(toolbar).toBeInTheDocument();

    // Verify phone and desktop buttons are completely absent
    expect(screen.queryByRole("button", { name: /mobile view/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /desktop view/i })).not.toBeInTheDocument();

    // Group 1: Chat button
    const chatBtn = screen.getByRole("button", { name: /ai analyst/i });
    expect(chatBtn).toBeInTheDocument();

    // Group 2: Exactly ONE Avatar button
    const avatarBtns = screen.getAllByRole("button", { name: /User account:/i });
    expect(avatarBtns.length).toBe(1);
    expect(avatarBtns[0]).toHaveTextContent("S");

    // Group 3: Upload and Menu buttons
    expect(screen.getByRole("button", { name: /import holdings/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /secondary menu/i })).toBeInTheDocument();

    // Verify exactly two vertical separators separating the three groups
    const separators = screen.getAllByRole("separator");
    expect(separators.length).toBe(2);

    // Verify avatar click triggers callback
    fireEvent.click(avatarBtns[0]);
    expect(handleAvatarClick).toHaveBeenCalledTimes(1);
  });
});

describe("TASK 1.14C — TopNavbar Header Integration & Responsive Automation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("verifies Phone/Desktop buttons are absent and exactly one authenticated user avatar appears", async () => {
    render(<TopNavbar />);

    // 1. Phone and Desktop buttons must be absent
    expect(screen.queryByLabelText(/Mobile Viewport Navigation/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Desktop Standard View/i)).not.toBeInTheDocument();

    // 2. Preserved telemetry active indicator
    await waitFor(() => {
      expect(screen.getByText(/Active/i)).toBeInTheDocument();
    });

    // 3. Preserved notifications bell and ThemeSwitcher
    expect(screen.getByRole("link", { name: /Notifications/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Light theme/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Dark theme/i)).toBeInTheDocument();

    // 4. Authenticated user avatar with initial 'L' (Lead Analyst)
    await waitFor(() => {
      expect(screen.getByText("L")).toBeInTheDocument();
    });

    // Verify only 1 avatar is rendered in the toolbar
    const avatar = screen.getByRole("button", { name: /User account: Lead Analyst/i });
    expect(avatar).toBeInTheDocument();
  });

  it("opens account dropdown when single user avatar is clicked and closes on Escape", async () => {
    render(<TopNavbar />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /User account: Lead Analyst/i })).toBeInTheDocument();
    });

    const avatar = screen.getByRole("button", { name: /User account: Lead Analyst/i });
    fireEvent.click(avatar);

    // Account dropdown is visible
    expect(screen.getByRole("menu", { name: /User account and secondary workspace actions/i })).toBeInTheDocument();
    expect(screen.getByText("Daily Workspace")).toBeInTheDocument();
    expect(screen.getByText("Custom Watchlists")).toBeInTheDocument();
    expect(screen.getByText("Alerts Center")).toBeInTheDocument();
    expect(screen.getByText("Platform Coverage Audit")).toBeInTheDocument();
    expect(screen.getByText("Live Intake Feed")).toBeInTheDocument();
    expect(screen.getByText("Settings & RBAC")).toBeInTheDocument();
    expect(screen.getByText("Sign Out")).toBeInTheDocument();

    // Escape closes dropdown
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("menu", { name: /User account and secondary workspace actions/i })).not.toBeInTheDocument();
  });

  it("opens account dropdown when Menu icon is clicked and closes on outside click", async () => {
    render(<TopNavbar />);

    const menuBtn = screen.getByLabelText(/Secondary Header Menu/i);
    fireEvent.click(menuBtn);

    expect(screen.getByRole("menu", { name: /User account and secondary workspace actions/i })).toBeInTheDocument();

    // Outside click closes dropdown
    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole("menu", { name: /User account and secondary workspace actions/i })).not.toBeInTheDocument();
  });

  it("navigates to /ai-analyst when Chat icon is clicked", () => {
    render(<TopNavbar />);

    const chatBtn = screen.getByLabelText(/Grounded AI Analyst/i);
    fireEvent.click(chatBtn);

    expect(mockPush).toHaveBeenCalledWith("/ai-analyst");
  });

  it("opens upload holdings modal when Upload icon is clicked", () => {
    render(<TopNavbar />);

    const uploadBtn = screen.getByLabelText(/Import Holdings/i);
    fireEvent.click(uploadBtn);

    expect(screen.getByText("Import Portfolio Holdings")).toBeInTheDocument();
    expect(screen.getByText(/Select a CSV or JSON file to upload/i)).toBeInTheDocument();
  });

  it("opens mobile drawer via mobile navigation hamburger with authenticated user initial", async () => {
    render(<TopNavbar />);

    const mobileBtn = screen.getByLabelText(/Open navigation menu/i);
    fireEvent.click(mobileBtn);

    expect(screen.getByRole("dialog", { name: /Mobile navigation/i })).toBeInTheDocument();

    // Mobile drawer displays initial 'L' once session resolves
    await waitFor(() => {
      const drawerInitials = screen.getAllByText("L");
      expect(drawerInitials.length).toBeGreaterThanOrEqual(1);
    });

    // Close mobile drawer
    const closeBtn = screen.getByLabelText(/Close navigation/i);
    fireEvent.click(closeBtn);
    expect(screen.queryByRole("dialog", { name: /Mobile navigation/i })).not.toBeInTheDocument();
  });
});
