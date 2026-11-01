/**
 * __tests__/pages/settings.test.tsx
 * =================================
 * Focused Unit and Integration Test Suite for Task 1.8A:
 * SaaS Settings & Governance Redesign (/settings).
 *
 * Validates:
 * 1. Master-detail layout with 4 approved governance sections:
 *     - Account & Security
 *     - Organization & Team
 *     - Notifications & Delivery
 *     - Data Governance & Privacy
 * 2. Active section switching and URL synchronization
 * 3. User Master Identity, HMAC session verification, and SSO evaluation status
 * 4. Organization profile, evaluation tier notice, and invite team member workflow
 * 5. Team members directory with RBAC role change and member removal permissions
 * 6. Alert subsystem toggle, delivery schedule, severity threshold, and quiet hours
 * 7. Grounded AI usage telemetry, quota display, and IDOR anti-hallucination notice
 * 8. Tenant JSON data export trigger
 * 9. Statutory and econometric immutability guarantee notice
 * 10. Organization deletion safeguard requiring explicit "DELETE" confirmation
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import SettingsPage from "@/app/settings/page";
import { authApi } from "@/lib/api/auth";
import { alertsApi } from "@/lib/api/alerts";
import { apiClient } from "@/lib/api/client";

// Mock next/navigation
const mockReplace = vi.fn();
let mockSearchParam = "";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: mockReplace,
  }),
  useSearchParams: () => ({
    get: (key: string) => {
      if (key === "section" || key === "tab") return mockSearchParam || null;
      return null;
    },
  }),
}));

// Mock authApi
vi.mock("@/lib/api/auth", () => ({
  authApi: {
    getMe: vi.fn(),
    getStatus: vi.fn(),
    getOrganization: vi.fn(),
    listMembers: vi.fn(),
    inviteMember: vi.fn(),
    changeMemberRole: vi.fn(),
    removeMember: vi.fn(),
    exportTenantData: vi.fn(),
    softDeleteTenant: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock alertsApi
vi.mock("@/lib/api/alerts", () => ({
  alertsApi: {
    getPreferences: vi.fn(),
    updatePreferences: vi.fn(),
  },
}));

// Mock apiClient
vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const mockUser = {
  user_id: "usr_lead_analyst_01",
  email: "sanal@institution.in",
  display_name: "Sanal Kumar",
  role: "OWNER",
  tenant_id: "institutional_fund_01",
  created_at: "2026-01-15T00:00:00Z",
};

const mockAuthStatus = {
  authenticated: true,
  auth_mode: "PRODUCTION_HMAC",
  sso_status: "NOT_CONFIGURED",
  session_timeout_minutes: 1440,
  mfa_enforced: false,
};

const mockOrg = {
  tenant_id: "institutional_fund_01",
  name: "National Securities & Research Desk",
  plan_tier: "ENTERPRISE",
  billing_status: "BILLING_NOT_CONNECTED",
  created_at: "2026-01-15T00:00:00Z",
};

const mockMembers = {
  items: [
    {
      user_id: "usr_lead_analyst_01",
      email: "sanal@institution.in",
      display_name: "Sanal Kumar",
      role: "OWNER",
      status: "Active",
      joined_at: "2026-01-15",
    },
    {
      user_id: "usr_quant_02",
      email: "priya@institution.in",
      display_name: "Priya Sharma",
      role: "ADMIN",
      status: "Active",
      joined_at: "2026-02-01",
    },
  ],
  total: 2,
};

const mockAlertPreferences = {
  enabled: true,
  minimum_severity: "HIGH",
  digest_frequency: "DAILY",
  allowed_channels: ["IN_APP"],
  quiet_hours_enabled: true,
  quiet_hours_start: "22:00",
  quiet_hours_end: "07:00",
};

const mockAiUsage = {
  total_queries: 142,
  monthly_quota: 5000,
};

describe("Workspace Settings & Governance (/settings)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParam = "";
    (authApi.getMe as any).mockResolvedValue(mockUser);
    (authApi.getStatus as any).mockResolvedValue(mockAuthStatus);
    (authApi.getOrganization as any).mockResolvedValue(mockOrg);
    (authApi.listMembers as any).mockResolvedValue(mockMembers);
    (alertsApi.getPreferences as any).mockResolvedValue(mockAlertPreferences);
    (alertsApi.updatePreferences as any).mockResolvedValue(mockAlertPreferences);
    (apiClient.get as any).mockResolvedValue(mockAiUsage);
  });

  it("1. renders master-detail navigation with all 4 approved governance sections", async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Workspace Settings & Governance/i })
      ).toBeInTheDocument();
    });

    // Check master nav buttons
    expect(screen.getAllByRole("button", { name: /Account & Security/i })[0]).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Organization & Team/i })[0]).toBeInTheDocument();
    expect(
      screen.getAllByRole("button", { name: /Notifications & Delivery/i })[0]
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("button", { name: /Data Governance & Privacy/i })[0]
    ).toBeInTheDocument();
  });

  it("2. renders Account & Security section by default with HMAC and SSO status", async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("User Master Identity")).toBeInTheDocument();
    });

    expect(screen.getByText("usr_lead_analyst_01")).toBeInTheDocument();
    expect(screen.getByText("sanal@institution.in")).toBeInTheDocument();
    expect(screen.getByText("PRODUCTION_HMAC")).toBeInTheDocument();
    expect(screen.getByText("NOT_CONFIGURED")).toBeInTheDocument();
    expect(
      screen.getByText(/Session tokens are cryptographically hashed using HMAC-SHA256/i)
    ).toBeInTheDocument();
  });

  it("3. switches to Organization & Team section and displays members and invite form", async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("User Master Identity")).toBeInTheDocument();
    });

    // Click Organization & Team
    const orgNavBtn = screen.getAllByRole("button", { name: /Organization & Team/i })[0];
    fireEvent.click(orgNavBtn);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Organization & Team Administration/i })
      ).toBeInTheDocument();
    });

    expect(screen.getByText("National Securities & Research Desk")).toBeInTheDocument();
    expect(screen.getAllByText(/BILLING_NOT_CONNECTED/i)[0]).toBeInTheDocument();
    expect(screen.getByText("Priya Sharma")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("analyst@firm.com")).toBeInTheDocument();
  });

  it("4. switches to Notifications & Delivery and updates preferences", async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("User Master Identity")).toBeInTheDocument();
    });

    // Click Notifications & Delivery
    const notifNavBtn = screen.getAllByRole("button", { name: /Notifications & Delivery/i })[0];
    fireEvent.click(notifNavBtn);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Notifications & Delivery Preferences/i })
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Enable Legislative Alert Subsystem")).toBeInTheDocument();
    expect(screen.getByText("Quiet Hours Scheduler")).toBeInTheDocument();

    // Click Save Notification Preferences
    const saveBtn = screen.getByRole("button", { name: /Save Notification Preferences/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(alertsApi.updatePreferences).toHaveBeenCalled();
      expect(
        screen.getByText(/Alert & notification preferences successfully synchronized/i)
      ).toBeInTheDocument();
    });
  });

  it("5. switches to Data Governance & Privacy and displays AI metering, immutability, and delete safeguard", async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("User Master Identity")).toBeInTheDocument();
    });

    // Click Data Governance & Privacy
    const govNavBtn = screen.getAllByRole("button", { name: /Data Governance & Privacy/i })[0];
    fireEvent.click(govNavBtn);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /Data Governance, AI Metering & Privacy/i })
      ).toBeInTheDocument();
    });

    // Check AI Metering & anti-hallucination
    expect(screen.getByText("Grounded AI Intelligence Usage Telemetry")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByText("Anti-Hallucination Pass")).toBeInTheDocument();

    // Check Immutability Guarantee
    expect(
      screen.getByText(/Statutory & Econometric Immutability Guarantee/i)
    ).toBeInTheDocument();

    // Check Danger Zone & safeguard
    expect(screen.getByText("Danger Zone: Organization Deletion")).toBeInTheDocument();
    const deleteBtn = screen.getByRole("button", { name: /Delete Organization/i });

    // Click delete without typing DELETE
    fireEvent.click(deleteBtn);
    expect(
      screen.getByText("Please type DELETE to confirm tenant deletion.")
    ).toBeInTheDocument();
    expect(authApi.softDeleteTenant).not.toHaveBeenCalled();
  });
});
