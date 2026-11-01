/**
 * __tests__/pages/onboarding.test.tsx
 * =====================================
 * Unit & Integration Test Suite for Task 1.15A:
 * Seance Immersive Full-Screen Onboarding Redesign.
 *
 * Verifies:
 * 1. Isolated Route & Seance Wordmark rendering.
 * 2. Eight-stage progress stepper and step indicator.
 * 3. Step 1 (Welcome & Platform Introduction).
 * 4. Step 2 (Organization Profile & Validation).
 * 5. Step 3 (Role & Persona Selection).
 * 6. Step 4 (Jurisdiction Coverage & Multi-State Toggle).
 * 7. Step 5 (Starter Watchlist Seeding).
 * 8. Step 6 (Alert Preferences & Digest Frequency).
 * 9. Step 7 (Platform Capabilities Overview).
 * 10. Step 8 (Launch Command Center & API Persistence).
 * 11. FeatureCarousel 4-stage and 8-stage extensibility.
 * 12. LocalStorage draft persistence and rehydration.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import OnboardingPage from "@/app/onboarding/page";
import {
  FeatureCarousel,
  DEFAULT_FOUR_STAGES,
  SEANCE_EIGHT_STAGES,
} from "@/components/ui/feature-carousel";
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
    createWatchlist: vi.fn().mockResolvedValue({ watchlist_id: "wl_test_123" }),
    addItem: vi.fn().mockResolvedValue({ status: "success" }),
  },
}));

vi.mock("@/lib/api/alerts", () => ({
  alertsApi: {
    updatePreferences: vi.fn().mockResolvedValue({ status: "success" }),
  },
}));

describe("Task 1.15A — Seance Immersive Onboarding Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders Seance institutional wordmark and progress stepper on Step 1", () => {
    render(<OnboardingPage />);

    expect(screen.getByTestId("seance-onboarding-wordmark")).toBeDefined();
    expect(screen.getByText("SEANCE")).toBeDefined();
    expect(screen.getByText(/India's Legislative Intelligence Engine/i)).toBeDefined();
    expect(screen.getAllByText(/Step 1 of 8/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: /Continue →/i })).toBeDefined();
  });

  it("advances to Step 2 and validates required organization name", async () => {
    render(<OnboardingPage />);

    // Step 1 -> Step 2
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));

    await waitFor(() => {
      expect(screen.getByText("Organization Profile")).toBeDefined();
    });

    const orgInput = screen.getByLabelText(/Organization \/ Firm Name/i);
    expect(orgInput).toBeDefined();

    // Clear org input to test validation
    fireEvent.change(orgInput, { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));

    expect(
      screen.getByText(/Please enter a valid organization name/i)
    ).toBeDefined();

    // Provide valid input and continue to Step 3
    fireEvent.change(orgInput, { target: { value: "Apex Capital Research" } });
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));

    await waitFor(() => {
      expect(screen.getByText("Select Your Persona")).toBeDefined();
    });
  });

  it("selects persona in Step 3 and allows moving back and forward", async () => {
    render(<OnboardingPage />);

    // Jump or advance to step 3
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // to step 2
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // to step 3

    await waitFor(() => {
      expect(screen.getByText("Select Your Persona")).toBeDefined();
    });

    // Select Regulatory Affairs Director
    const regAffairsBtn = screen.getByRole("button", {
      name: /Regulatory Affairs Director/i,
    });
    fireEvent.click(regAffairsBtn);

    // Test Back button
    const backBtn = screen.getByRole("button", { name: /← Back/i });
    fireEvent.click(backBtn);

    await waitFor(() => {
      expect(screen.getByText("Organization Profile")).toBeDefined();
    });

    // Continue again to Step 3
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    await waitFor(() => {
      expect(screen.getByText("Select Your Persona")).toBeDefined();
    });
  });

  it("toggles jurisdictions on Step 4 and prevents proceeding with 0 jurisdictions", async () => {
    render(<OnboardingPage />);

    // Advance to step 4
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // 2
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // 3
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i })); // 4

    await waitFor(() => {
      expect(screen.getByText("Jurisdiction Coverage")).toBeDefined();
    });

    // Default jurisdictions: CENTRAL, KA, TS. Deselect them to test validation
    const centralItem = screen.getByText("Central Parliament of India");
    const kaItem = screen.getByText("Karnataka Legislature");
    const tsItem = screen.getByText("Telangana Legislature");

    fireEvent.click(centralItem);
    fireEvent.click(kaItem);
    fireEvent.click(tsItem);

    // Attempt to continue with 0 jurisdictions
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    expect(
      screen.getByText(/Please select at least one parliamentary or state jurisdiction/i)
    ).toBeDefined();

    // Re-select Central Parliament
    fireEvent.click(centralItem);
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));

    await waitFor(() => {
      expect(screen.getByText("Create Starter Watchlist")).toBeDefined();
    });
  });

  it("completes full 8-step wizard and executes API persistence on Finish", async () => {
    render(<OnboardingPage />);

    // Step 1 -> 2
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    // Step 2 -> 3
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    // Step 3 -> 4
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    // Step 4 -> 5
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    // Step 5 -> 6
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    // Step 6 -> 7
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));
    // Step 7 -> 8
    fireEvent.click(screen.getByRole("button", { name: /Continue →/i }));

    await waitFor(() => {
      expect(screen.getByText("You're All Set!")).toBeDefined();
      expect(
        screen.getByRole("button", { name: /Launch Command Center 🏛/i })
      ).toBeDefined();
    });

    // Click Launch
    const launchBtn = screen.getByRole("button", {
      name: /Launch Command Center 🏛/i,
    });
    fireEvent.click(launchBtn);

    await waitFor(() => {
      expect(watchlistsApi.createWatchlist).toHaveBeenCalledWith({
        name: "Priority Regulatory Watchlist",
        description: "Curated during initial onboarding wizard",
      });
      expect(watchlistsApi.addItem).toHaveBeenCalled();
      expect(alertsApi.updatePreferences).toHaveBeenCalledWith({
        digest_frequency: "DAILY",
        allowed_channels: ["IN_APP"],
      });
      expect(mockPush).toHaveBeenCalledWith("/workspace");
    });
  });

  it("rehydrates draft state from localStorage on mount", async () => {
    localStorage.setItem(
      "seance_onboarding_draft",
      JSON.stringify({
        step: 5,
        orgName: "Hydrated Org",
        persona: "Portfolio Manager",
        selectedBills: ["bill_01_telecom_2023"],
        selectedJurisdictions: ["CENTRAL"],
      })
    );

    render(<OnboardingPage />);

    await waitFor(() => {
      expect(screen.getByText("Create Starter Watchlist")).toBeDefined();
      expect(screen.getAllByText(/Step 5 of 8/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("resets draft state when Reset Draft button is clicked", async () => {
    localStorage.setItem(
      "seance_onboarding_draft",
      JSON.stringify({ step: 4, orgName: "Old Org" })
    );

    render(<OnboardingPage />);

    await waitFor(() => {
      expect(screen.getByText("Jurisdiction Coverage")).toBeDefined();
    });

    const resetBtn = screen.getByRole("button", { name: /Reset Draft/i });
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(screen.getByText(/India's Legislative Intelligence Engine/i)).toBeDefined();
      expect(screen.getAllByText(/Step 1 of 8/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});

describe("FeatureCarousel Component", () => {
  it("renders with 4-stage standard default export without crashing", () => {
    render(<FeatureCarousel stages={DEFAULT_FOUR_STAGES} />);
    expect(screen.getByRole("region", { name: /Product Showcase Carousel/i })).toBeDefined();
    expect(screen.getByText("STATUTORY INTELLIGENCE")).toBeDefined();
  });

  it("renders with 8-stage Seance configuration and reacts to activeStep prop", () => {
    const { rerender } = render(
      <FeatureCarousel stages={SEANCE_EIGHT_STAGES} activeStep={1} />
    );
    expect(screen.getByText("STAGE 01 · FOUNDATION")).toBeDefined();

    rerender(<FeatureCarousel stages={SEANCE_EIGHT_STAGES} activeStep={4} />);
    expect(screen.getByText("STAGE 04 · SUB-NATIONAL JURISDICTION")).toBeDefined();
  });
});
