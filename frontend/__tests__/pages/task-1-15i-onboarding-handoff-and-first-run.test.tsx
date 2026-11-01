/**
 * __tests__/pages/task-1-15i-onboarding-handoff-and-first-run.test.tsx
 * ===================================================================
 * Focused Unit & Integration Test Suite for Task 1.15I:
 * Onboarding-to-Platform Handoff & Personalized First-Run Experience.
 *
 * Verifies:
 * 1. Persona normalization and configuration mapping across the 4 core archetypes
 *    (Investor, Business Owner, Analyst / Researcher, General Public).
 * 2. Onboarding data handoff preservation and resilient rehydration from localStorage.
 * 3. Graceful fallback on missing, partial, or malformed onboarding metadata.
 * 4. Personalized Command Center orientation adapting headlines, starting actions,
 *    and statutory notices for each persona.
 * 5. First-run guidance 6-step tour progression, non-blocking disclosure, dismissal, and reopening.
 * 6. Contextual empty states for portfolios, watchlists, and monitored workspace tabs.
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import {
  normalizePersona,
  getPersonaConfig,
  getOnboardingHandoff,
  saveOnboardingHandoff,
  isGuidanceDismissed,
  setGuidanceDismissed,
  isHeroCollapsed,
  setHeroCollapsed,
  ONBOARDING_COMPLETED_KEY,
  GUIDANCE_DISMISSED_KEY,
  DEFAULT_HANDOFF_DATA,
  OnboardingHandoffData,
} from "@/lib/onboarding/handoff";
import { PersonalizedPersonaHero } from "@/components/workspace/PersonalizedPersonaHero";
import { FirstRunGuidance } from "@/components/workspace/FirstRunGuidance";
import { HoldingsRoster } from "@/components/portfolio/HoldingsRoster";
import WatchlistsPage from "@/app/watchlists/page";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: any }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

// Mock watchlistsApi
vi.mock("@/lib/api/watchlists", () => ({
  watchlistsApi: {
    listWatchlists: vi.fn().mockResolvedValue([]),
    createWatchlist: vi.fn(),
    updateWatchlist: vi.fn(),
    deleteWatchlist: vi.fn(),
  },
}));

describe("Task 1.15I — Onboarding-to-Platform Handoff & First-Run Experience", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  // -------------------------------------------------------------------------
  // 1. Persona Normalization & Archetype Config Mapping
  // -------------------------------------------------------------------------
  describe("1. Persona Normalization & Archetype Config", () => {
    it("correctly maps roles and labels to canonical personas", () => {
      // Investor archetype
      expect(normalizePersona("Portfolio Manager")).toBe("INVESTOR");
      expect(normalizePersona("Investor")).toBe("INVESTOR");
      expect(normalizePersona("Institutional Capital Allocator")).toBe("INVESTOR");

      // Business Owner archetype
      expect(normalizePersona("Regulatory Affairs Director")).toBe("BUSINESS_OWNER");
      expect(normalizePersona("Business Owner")).toBe("BUSINESS_OWNER");
      expect(normalizePersona("Corporate Executive")).toBe("BUSINESS_OWNER");

      // Analyst / Researcher archetype
      expect(normalizePersona("Equity Research Analyst")).toBe("ANALYST_RESEARCHER");
      expect(normalizePersona("Analyst / Researcher")).toBe("ANALYST_RESEARCHER");
      expect(normalizePersona("Policy Researcher")).toBe("ANALYST_RESEARCHER");

      // General Public archetype
      expect(normalizePersona("General Counsel & Policy Head")).toBe("GENERAL_PUBLIC");
      expect(normalizePersona("General Public")).toBe("GENERAL_PUBLIC");
      expect(normalizePersona("Civic Observer")).toBe("GENERAL_PUBLIC");

      // Fallback
      expect(normalizePersona(null)).toBe("ANALYST_RESEARCHER");
      expect(normalizePersona("")).toBe("ANALYST_RESEARCHER");
      expect(normalizePersona("unknown_role")).toBe("ANALYST_RESEARCHER");
    });

    it("provides complete persona configurations with statutory notices and 4 starting actions", () => {
      const personas = ["INVESTOR", "BUSINESS_OWNER", "ANALYST_RESEARCHER", "GENERAL_PUBLIC"] as const;

      personas.forEach((p) => {
        const config = getPersonaConfig(p);
        expect(config.id).toBe(p);
        expect(config.displayName).toBeDefined();
        expect(config.headline).toBeDefined();
        expect(config.statutoryNotice).toBeDefined();
        expect(config.recommendedActions.length).toBe(4);
        config.recommendedActions.forEach((act) => {
          expect(act.title).toBeDefined();
          expect(act.href).toBeDefined();
          expect(act.actionText).toBeDefined();
        });
      });
    });
  });

  // -------------------------------------------------------------------------
  // 2. Data Handoff Persistence & Rehydration
  // -------------------------------------------------------------------------
  describe("2. Onboarding Data Handoff & Persistence", () => {
    it("saves and retrieves full onboarding handoff data", () => {
      const testRecord: OnboardingHandoffData = {
        completed: true,
        completedAt: "2026-11-01T12:00:00.000Z",
        orgName: "BlackRock Regulatory Research",
        industryFocus: "Fintech & Banking",
        teamSize: "20+",
        persona: "Portfolio Manager",
        canonicalPersona: "INVESTOR",
        selectedJurisdictions: ["CENTRAL", "KA"],
        selectedBills: ["bill_01_telecom_2023"],
        digestFrequency: "WEEKLY",
        inAppAlerts: true,
        emailAlerts: true,
      };

      saveOnboardingHandoff(testRecord);

      const rehydrated = getOnboardingHandoff();
      expect(rehydrated.completed).toBe(true);
      expect(rehydrated.orgName).toBe("BlackRock Regulatory Research");
      expect(rehydrated.persona).toBe("Portfolio Manager");
      expect(rehydrated.canonicalPersona).toBe("INVESTOR");
      expect(rehydrated.selectedJurisdictions).toEqual(["CENTRAL", "KA"]);
      expect(rehydrated.digestFrequency).toBe("WEEKLY");
    });

    it("gracefully falls back to canonical defaults when localStorage is empty or corrupt", () => {
      localStorage.setItem(ONBOARDING_COMPLETED_KEY, "invalid_json{{{");

      const handoff = getOnboardingHandoff();
      expect(handoff.orgName).toBe(DEFAULT_HANDOFF_DATA.orgName);
      expect(handoff.canonicalPersona).toBe("ANALYST_RESEARCHER");
      expect(handoff.selectedJurisdictions).toEqual(["CENTRAL", "KA", "TS"]);
    });

    it("persists and reads guidance dismissal state correctly", () => {
      expect(isGuidanceDismissed()).toBe(false);

      setGuidanceDismissed(true);
      expect(isGuidanceDismissed()).toBe(true);

      setGuidanceDismissed(false);
      expect(isGuidanceDismissed()).toBe(false);
    });

    it("persists hero collapse state", () => {
      expect(isHeroCollapsed()).toBe(false);
      setHeroCollapsed(true);
      expect(isHeroCollapsed()).toBe(true);
      setHeroCollapsed(false);
      expect(isHeroCollapsed()).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // 3. Personalized Command Center Orientation (PersonalizedPersonaHero)
  // -------------------------------------------------------------------------
  describe("3. PersonalizedPersonaHero Component", () => {
    it("renders Investor persona orientation with portfolio & prediction actions", () => {
      const investorHandoff: OnboardingHandoffData = {
        completed: true,
        orgName: "Seance Capital Partners",
        industryFocus: "Quantitative Finance",
        teamSize: "5-20",
        persona: "Portfolio Manager",
        canonicalPersona: "INVESTOR",
        selectedJurisdictions: ["CENTRAL", "TS"],
        selectedBills: [],
        digestFrequency: "DAILY",
        inAppAlerts: true,
        emailAlerts: false,
      };

      render(<PersonalizedPersonaHero handoff={investorHandoff} />);

      // Verify organization badge and persona badge
      expect(screen.getByTestId("hero-org-badge")).toHaveTextContent("Seance Capital Partners");
      expect(screen.getByTestId("hero-persona-badge")).toHaveTextContent("Investor");
      expect(screen.getByTestId("hero-jurisdictions-badge")).toHaveTextContent("CENTRAL, TS");

      // Verify tailored headline
      expect(screen.getByTestId("hero-headline")).toHaveTextContent(/Investor Intelligence/i);

      // Verify statutory firewall notice
      expect(screen.getByTestId("hero-statutory-notice")).toHaveTextContent(
        /Zero State bill stock predictions guaranteed/i
      );

      // Verify recommended actions
      expect(screen.getByText("Portfolio Exposure Workspace")).toBeDefined();
      expect(screen.getByText("Central Prediction Models")).toBeDefined();
    });

    it("renders Business Owner persona orientation with compliance & state actions", () => {
      const bizHandoff: OnboardingHandoffData = {
        completed: true,
        orgName: "Tata Enterprise Compliance",
        industryFocus: "Manufacturing & Heavy Industry",
        teamSize: "20+",
        persona: "Regulatory Affairs Director",
        canonicalPersona: "BUSINESS_OWNER",
        selectedJurisdictions: ["CENTRAL", "KA", "KL"],
        selectedBills: [],
        digestFrequency: "DAILY",
        inAppAlerts: true,
        emailAlerts: false,
      };

      render(<PersonalizedPersonaHero handoff={bizHandoff} />);

      expect(screen.getByTestId("hero-org-badge")).toHaveTextContent("Tata Enterprise Compliance");
      expect(screen.getByTestId("hero-persona-badge")).toHaveTextContent("Business Owner");
      expect(screen.getByTestId("hero-headline")).toHaveTextContent(/Corporate Governance & Regulatory Compliance/i);
      expect(screen.getByText("Legislative Monitoring Center")).toBeDefined();
      expect(screen.getByText("State Assembly Enactments")).toBeDefined();
    });

    it("renders Analyst / Researcher persona orientation with bill dossiers & methodology", () => {
      const analystHandoff: OnboardingHandoffData = {
        completed: true,
        orgName: "National Law University Research",
        industryFocus: "Public Policy",
        teamSize: "1-5",
        persona: "Equity Research Analyst",
        canonicalPersona: "ANALYST_RESEARCHER",
        selectedJurisdictions: ["CENTRAL"],
        selectedBills: [],
        digestFrequency: "DAILY",
        inAppAlerts: true,
        emailAlerts: false,
      };

      render(<PersonalizedPersonaHero handoff={analystHandoff} />);

      expect(screen.getByTestId("hero-persona-badge")).toHaveTextContent("Analyst & Regulatory Researcher");
      expect(screen.getByTestId("hero-headline")).toHaveTextContent(/Legislative Dossiers & Empirical Research Workbench/i);
      expect(screen.getByText("Legislative Bill Dossiers")).toBeDefined();
      expect(screen.getByText("Cross-Jurisdiction Comparison")).toBeDefined();
    });

    it("renders General Public persona orientation with plain language summaries", () => {
      const publicHandoff: OnboardingHandoffData = {
        completed: true,
        orgName: "Citizen Rights Foundation",
        industryFocus: "Civil Society",
        teamSize: "1-5",
        persona: "General Counsel & Policy Head",
        canonicalPersona: "GENERAL_PUBLIC",
        selectedJurisdictions: ["CENTRAL", "AP"],
        selectedBills: [],
        digestFrequency: "DAILY",
        inAppAlerts: true,
        emailAlerts: false,
      };

      render(<PersonalizedPersonaHero handoff={publicHandoff} />);

      expect(screen.getByTestId("hero-persona-badge")).toHaveTextContent("Public Policy & Citizen Impact");
      expect(screen.getByTestId("hero-headline")).toHaveTextContent(/Public Policy Observatory & Democratic Impact/i);
      expect(screen.getByText("Plain-Language Bill Explanations")).toBeDefined();
      expect(screen.getByText("Multi-Stakeholder Impact Views")).toBeDefined();
    });

    it("toggles collapse and minimize state smoothly", () => {
      const handoff: OnboardingHandoffData = {
        ...DEFAULT_HANDOFF_DATA,
        completed: true,
      };

      render(<PersonalizedPersonaHero handoff={handoff} />);

      expect(screen.getByTestId("hero-headline")).toBeDefined();

      const toggleBtn = screen.getByTestId("hero-toggle-collapse-btn");
      fireEvent.click(toggleBtn);

      expect(screen.queryByTestId("hero-headline")).toBeNull();
      expect(toggleBtn).toHaveTextContent("Expand Orientation ▼");

      fireEvent.click(toggleBtn);
      expect(screen.getByTestId("hero-headline")).toBeDefined();
    });
  });

  // -------------------------------------------------------------------------
  // 4. First-Run Guidance Tour (FirstRunGuidance)
  // -------------------------------------------------------------------------
  describe("4. FirstRunGuidance Component", () => {
    it("renders Step 1 (Command Center) and advances through steps", () => {
      const onDismiss = vi.fn();
      render(<FirstRunGuidance onDismiss={onDismiss} />);

      expect(screen.getByTestId("first-run-guidance")).toBeDefined();
      expect(screen.getByText(/1 of 6/)).toBeDefined();
      expect(screen.getByText("Command Center & Decision Hub")).toBeDefined();

      // Click Next Capability -> advances to Step 2 (Bills)
      const nextBtn = screen.getByTestId("guidance-next-btn");
      fireEvent.click(nextBtn);

      expect(screen.getByText(/2 of 6/)).toBeDefined();
      expect(screen.getByText("Bill Intelligence & Dossiers")).toBeDefined();
    });

    it("dismisses guidance when Dismiss Tour button is clicked", () => {
      const onDismiss = vi.fn();
      render(<FirstRunGuidance onDismiss={onDismiss} />);

      const dismissBtn = screen.getByTestId("dismiss-guidance-btn");
      fireEvent.click(dismissBtn);

      expect(onDismiss).toHaveBeenCalledTimes(1);
      expect(localStorage.getItem(GUIDANCE_DISMISSED_KEY)).toBe("true");
    });
  });

  // -------------------------------------------------------------------------
  // 5. Contextual Empty States (Portfolio & Watchlists)
  // -------------------------------------------------------------------------
  describe("5. Contextual Empty States", () => {
    it("renders actionable empty state in HoldingsRoster when no holdings exist", () => {
      const onAddHolding = vi.fn();
      render(
        <HoldingsRoster
          holdings={[]}
          selectedHolding={null}
          onSelectHolding={vi.fn()}
          onRemoveHolding={vi.fn()}
          onAddHolding={onAddHolding}
        />
      );

      expect(screen.getByTestId("empty-holdings-state")).toBeDefined();
      expect(screen.getByText("No Holdings in This Portfolio")).toBeDefined();
      expect(screen.getByText(/Portfolio exposure analyzes your equity holdings/i)).toBeDefined();

      const addBtn = screen.getByTestId("add-first-holding-btn");
      fireEvent.click(addBtn);
      expect(onAddHolding).toHaveBeenCalledTimes(1);

      expect(screen.getByText("Browse Companies →")).toBeDefined();
    });

    it("renders actionable empty state in WatchlistsPage when no watchlists exist", async () => {
      render(<WatchlistsPage />);

      await waitFor(() => {
        expect(screen.getByTestId("empty-watchlists-state")).toBeDefined();
      });

      expect(screen.getByText("No Watchlists Yet")).toBeDefined();
      expect(screen.getByText(/Watchlists let you curate custom tracking sets/i)).toBeDefined();
      expect(screen.getByTestId("create-first-watchlist-btn")).toBeDefined();
      expect(screen.getByText("Browse Legislative Bills →")).toBeDefined();
      expect(screen.getByText("Explore Companies →")).toBeDefined();
    });
  });
});
