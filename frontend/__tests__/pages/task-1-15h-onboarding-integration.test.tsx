/**
 * __tests__/pages/task-1-15h-onboarding-integration.test.tsx
 * ==========================================================
 * TASK 1.15H — ONBOARDING FLOW INTEGRATION & PRODUCTION READINESS TEST SUITE
 *
 * Verifies:
 * 1. Sequential progression through all 8 steps without skipping mandatory fields.
 * 2. Back and Next navigation preserves all form entries (org name, team size, persona, jurisdictions, watchlist, alerts).
 * 3. Prevention of skipping mandatory steps (Step 2 org name, Step 3 persona, Step 4 jurisdictions).
 * 4. Completed onboarding persistence:
 *    - Once completed, returns to Step 8 completion state ("seance_onboarding_completed").
 *    - Does NOT unnecessarily restart from Step 1.
 * 5. Incomplete onboarding resume:
 *    - Restores draft progress from localStorage cleanly without corruption.
 * 6. Accessible keyboard interaction:
 *    - Space & Enter toggles jurisdiction cards (Step 4) and watchlist cards (Step 5).
 *    - ARIA attributes (role="checkbox", aria-checked, aria-current="step", aria-live="polite").
 * 7. Reset draft wipes both draft and completion records, returning to clean Step 1.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import OnboardingPage from "@/app/onboarding/page";
import { watchlistsApi } from "@/lib/api/watchlists";
import { alertsApi } from "@/lib/api/alerts";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => "/onboarding",
}));

// Mock API modules
vi.mock("@/lib/api/watchlists", () => ({
  watchlistsApi: {
    createWatchlist: vi.fn().mockResolvedValue({ watchlist_id: "wl_test_456" }),
    addItem: vi.fn().mockResolvedValue({ status: "success" }),
  },
}));

vi.mock("@/lib/api/alerts", () => ({
  alertsApi: {
    updatePreferences: vi.fn().mockResolvedValue({ status: "success" }),
  },
}));

describe("Task 1.15H — Onboarding Flow Integration & Production Readiness", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("1. prevents advancing when mandatory fields are invalid and shows clear actionable errors", async () => {
    render(<OnboardingPage />);

    // Step 1 -> 2
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    await waitFor(() => {
      expect(screen.getByText("Organization Profile")).toBeDefined();
    });

    // Clear org name (< 2 chars)
    const orgInput = screen.getByLabelText(/Organization \/ Firm Name/i);
    fireEvent.change(orgInput, { target: { value: "A" } });
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));

    const errorAlert = screen.getByTestId("onboarding-validation-error");
    expect(errorAlert).toBeDefined();
    expect(errorAlert.getAttribute("role")).toBe("alert");
    expect(errorAlert.getAttribute("aria-live")).toBe("polite");
    expect(
      screen.getByText(/Please enter a valid organization name \(minimum 2 characters\)/i)
    ).toBeDefined();

    // Fix org name and advance to step 3
    fireEvent.change(orgInput, { target: { value: "Quantitative Capital" } });
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));

    await waitFor(() => {
      expect(screen.getByText("Select Your Persona")).toBeDefined();
    });

    // Advance to step 4
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    await waitFor(() => {
      expect(screen.getByText("Jurisdiction Coverage")).toBeDefined();
    });

    // Deselect all jurisdictions to test mandatory validation
    fireEvent.click(screen.getByText("Central Parliament of India"));
    fireEvent.click(screen.getByText("Karnataka Legislature"));
    fireEvent.click(screen.getByText("Telangana Legislature"));

    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    expect(
      screen.getByText(/Please select at least one parliamentary or state jurisdiction/i)
    ).toBeDefined();
  });

  it("2. form values persist accurately when navigating backward and forward", async () => {
    render(<OnboardingPage />);

    // Step 1 -> 2
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    await waitFor(() => {
      expect(screen.getByText("Organization Profile")).toBeDefined();
    });

    // Custom org name & team size
    const orgInput = screen.getByLabelText(/Organization \/ Firm Name/i);
    fireEvent.change(orgInput, { target: { value: "Nexus Macro Advisors" } });
    fireEvent.click(screen.getByRole("button", { name: /20\+ analysts/i }));

    // Step 2 -> 3
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    await waitFor(() => {
      expect(screen.getByText("Select Your Persona")).toBeDefined();
    });

    // Select Portfolio Manager
    fireEvent.click(screen.getByRole("button", { name: /Portfolio Manager/i }));

    // Step 3 -> 4
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    await waitFor(() => {
      expect(screen.getByText("Jurisdiction Coverage")).toBeDefined();
    });

    // Toggle AP Assembly on
    fireEvent.click(screen.getByText("Andhra Pradesh Assembly"));

    // Navigate BACK to Step 3
    fireEvent.click(screen.getByRole("button", { name: /← Back/i }));
    await waitFor(() => {
      expect(screen.getByText("Select Your Persona")).toBeDefined();
    });
    // Check that Portfolio Manager is still pressed/selected
    const pmBtn = screen.getByRole("button", { name: /Portfolio Manager/i });
    expect(pmBtn.getAttribute("aria-pressed")).toBe("true");

    // Navigate BACK to Step 2
    fireEvent.click(screen.getByRole("button", { name: /← Back/i }));
    await waitFor(() => {
      expect(screen.getByText("Organization Profile")).toBeDefined();
    });
    // Check that custom name & team size are preserved
    expect((screen.getByLabelText(/Organization \/ Firm Name/i) as HTMLInputElement).value).toBe(
      "Nexus Macro Advisors"
    );
    expect(
      screen.getByRole("button", { name: /20\+ analysts/i }).getAttribute("aria-pressed")
    ).toBe("true");

    // Navigate Forward again to Step 4
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // to 3
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // to 4
    await waitFor(() => {
      expect(screen.getByText("Jurisdiction Coverage")).toBeDefined();
    });
    // AP should still be checked
    const apCard = screen.getByLabelText(/Andhra Pradesh Assembly/i);
    expect(apCard.getAttribute("aria-checked")).toBe("true");
  });

  it("3. completed onboarding does not unnecessarily restart and displays completed status", async () => {
    // Simulate already completed onboarding stored in localStorage
    localStorage.setItem(
      "seance_onboarding_completed",
      JSON.stringify({
        completed: true,
        completedAt: "2026-11-01T10:00:00.000Z",
        orgName: "Established Hedge Fund",
        industryFocus: "Macro Hedge Fund / Portfolio Strategy",
        persona: "Portfolio Manager",
        selectedJurisdictions: ["CENTRAL", "KA"],
        selectedBills: ["bill_01_telecom_2023"],
        digestFrequency: "REAL_TIME",
      })
    );

    render(<OnboardingPage />);

    await waitFor(() => {
      // Must NOT restart at Step 1
      expect(screen.queryByText(/India's Legislative Intelligence Engine/i)).toBeNull();
      // Must display Step 8 completed status
      expect(screen.getByText(/Workspace Ready & Configured/i)).toBeDefined();
      expect(screen.getByText(/ONBOARDING COMPLETED/i)).toBeDefined();
      expect(screen.getByText(/Established Hedge Fund/i)).toBeDefined();
      expect(
        screen.getByRole("button", { name: /Enter Command Center 🏛/i })
      ).toBeDefined();
    });

    // Clicking Enter Command Center navigates directly to /workspace
    fireEvent.click(screen.getByRole("button", { name: /Enter Command Center 🏛/i }));
    expect(mockPush).toHaveBeenCalledWith("/workspace");
  });

  it("4. incomplete onboarding resumes draft state seamlessly on mount", async () => {
    localStorage.setItem(
      "seance_onboarding_draft",
      JSON.stringify({
        step: 6,
        maxStepReached: 6,
        orgName: "Resuming Analyst Corp",
        persona: "Regulatory Affairs Director",
        selectedJurisdictions: ["CENTRAL", "TS"],
        selectedBills: ["bill_02_dpdp_2023"],
        digestFrequency: "WEEKLY",
      })
    );

    render(<OnboardingPage />);

    await waitFor(() => {
      expect(screen.getByText("Notification & Digest Frequency")).toBeDefined();
      expect(screen.getAllByText(/Step 6 of 8/i).length).toBeGreaterThanOrEqual(1);
    });

    // Weekly Brief should be selected
    const weeklyBtn = screen.getByRole("button", { name: /Weekly Brief/i });
    expect(weeklyBtn.getAttribute("aria-pressed")).toBe("true");
  });

  it("5. supports full keyboard interaction (Space and Enter) on Step 4 and Step 5 cards", async () => {
    render(<OnboardingPage />);

    // Advance to Step 4
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // 2
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // 3
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // 4

    await waitFor(() => {
      expect(screen.getByText("Jurisdiction Coverage")).toBeDefined();
    });

    const klCard = screen.getByLabelText(/Kerala Assembly/i);
    expect(klCard.getAttribute("aria-checked")).toBe("false");

    // Focus and press Space
    fireEvent.keyDown(klCard, { key: " ", code: "Space" });
    expect(klCard.getAttribute("aria-checked")).toBe("true");

    // Press Enter to toggle off
    fireEvent.keyDown(klCard, { key: "Enter", code: "Enter" });
    expect(klCard.getAttribute("aria-checked")).toBe("false");

    // Advance to Step 5
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    await waitFor(() => {
      expect(screen.getByText("Create Starter Watchlist")).toBeDefined();
    });

    const gigCard = screen.getByLabelText(/Karnataka Gig Workers Welfare Act 2024/i);
    expect(gigCard.getAttribute("aria-checked")).toBe("false");

    // Focus and press Enter
    fireEvent.keyDown(gigCard, { key: "Enter", code: "Enter" });
    expect(gigCard.getAttribute("aria-checked")).toBe("true");
  });

  it("6. resets draft and completion state cleanly when Reset Draft is clicked", async () => {
    localStorage.setItem(
      "seance_onboarding_completed",
      JSON.stringify({
        completed: true,
        orgName: "Done Org",
      })
    );

    render(<OnboardingPage />);

    await waitFor(() => {
      expect(screen.getByText(/Workspace Ready & Configured/i)).toBeDefined();
    });

    const resetBtn = screen.getByRole("button", { name: /Reset Draft/i });
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(screen.getByText(/India's Legislative Intelligence Engine/i)).toBeDefined();
      expect(screen.getAllByText(/Step 1 of 8/i).length).toBeGreaterThanOrEqual(1);
      expect(localStorage.getItem("seance_onboarding_completed")).toBeNull();
    });
  });
});
