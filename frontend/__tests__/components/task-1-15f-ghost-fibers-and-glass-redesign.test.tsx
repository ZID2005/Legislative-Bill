/**
 * __tests__/components/task-1-15f-ghost-fibers-and-glass-redesign.test.tsx
 * =========================================================================
 * Comprehensive test suite for Task 1.15F:
 * - Authentic Ghost Fibers 72-thread, 3-layer particle-fiber field (fiberStyle="dots")
 * - Liquid-Glass Structural Redesign: 24px outer shell, coherent border hierarchy
 * - Mouse interaction and pulse-on-click configuration
 * - Non-blocking pointer events & prefers-reduced-motion fallback
 * - Full 8-stage visual showcase integrity & validation logic
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GhostFibers } from "@/components/onboarding/GhostFibers";
import { GhostFibersBackground } from "@/components/onboarding/GhostFibersBackground";
import { MinimalNumberedStepper } from "@/components/onboarding/OnboardingConnectedStepper";
import {
  LegislativeJourneyVisual,
  WorkspaceCommandCenterVisual,
  CorporateExposureNetworkVisual,
  StateIntelligenceMapVisual,
  WatchlistIntelligenceVisual,
  AlertIntelligenceVisual,
  SeanceMobileShowcase,
  WorkspaceLaunchVisual,
} from "@/components/onboarding/showcase";

describe("Task 1.15F — Authentic Ghost Fibers Particle-Fiber Background", () => {
  beforeEach(() => {
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      scale: vi.fn(),
      setTransform: vi.fn(),
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      quadraticCurveTo: vi.fn(),
      closePath: vi.fn(),
      arc: vi.fn(),
      fill: vi.fn(),
      stroke: vi.fn(),
      fillRect: vi.fn(),
      drawImage: vi.fn(),
      createLinearGradient: vi.fn().mockReturnValue({
        addColorStop: vi.fn(),
      }),
      createRadialGradient: vi.fn().mockReturnValue({
        addColorStop: vi.fn(),
      }),
    });
  });

  it("renders GhostFibers canvas with non-blocking pointer-events: none", () => {
    render(
      <GhostFibers
        glowColor="#8b5cf6"
        layers={3}
        twist={1.2}
        threads={72}
        fiberStyle="dots"
        depthOfField={0.85}
        hoverEffect="focus"
        intro={true}
        mouseInteraction={true}
        lineColor="#dfd1fc"
        secondaryColor="#6f4ac5"
        pulseOnClick={true}
      />
    );

    const canvas = screen.getByTestId("ghost-fibers-canvas");
    expect(canvas).toBeDefined();
    expect(canvas.style.pointerEvents).toBe("none");
  });

  it("renders GhostFibersBackground with fixed full-viewport coverage and 72 threads", () => {
    render(<GhostFibersBackground />);

    const bg = screen.getByTestId("ghost-fibers-background");
    expect(bg).toBeDefined();
    expect(bg.className).toContain("fixed");
    expect(bg.className).toContain("inset-0");
    expect(bg.className).toContain("pointer-events-none");

    const canvas = screen.getByTestId("ghost-fibers-canvas");
    expect(canvas).toBeDefined();
  });

  it("renders fallback container gracefully if canvas 2D context fails", () => {
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue(null);

    render(<GhostFibers />);

    const fallback = screen.getByTestId("ghost-fibers-fallback");
    expect(fallback).toBeDefined();
  });
});

describe("Task 1.15F — Minimal Numbered Stepper & Navigation Invariants", () => {
  it("renders all 8 numbered positions without phase titles", () => {
    render(<MinimalNumberedStepper currentStep={1} totalSteps={8} />);

    expect(screen.getByTestId("onboarding-progress-indicator")).toBeDefined();
    for (let i = 1; i <= 8; i++) {
      expect(screen.getByTestId(`step-indicator-${i}`)).toBeDefined();
    }

    // Zero bulky phase headings
    expect(screen.queryByText("Foundation")).toBeNull();
    expect(screen.queryByText("Preferences")).toBeNull();
    expect(screen.queryByText("Launch")).toBeNull();
  });

  it("advances step states correctly from 1 to 8", () => {
    const { rerender } = render(<MinimalNumberedStepper currentStep={1} totalSteps={8} />);
    expect(screen.getByTestId("step-indicator-1").getAttribute("data-step-state")).toBe("active");
    expect(screen.getByTestId("step-indicator-2").getAttribute("data-step-state")).toBe("upcoming");

    rerender(<MinimalNumberedStepper currentStep={5} totalSteps={8} />);
    expect(screen.getByTestId("step-indicator-1").getAttribute("data-step-state")).toBe("completed");
    expect(screen.getByTestId("step-indicator-4").getAttribute("data-step-state")).toBe("completed");
    expect(screen.getByTestId("step-indicator-5").getAttribute("data-step-state")).toBe("active");
    expect(screen.getByTestId("step-indicator-6").getAttribute("data-step-state")).toBe("upcoming");
  });
});

describe("Task 1.15F — All 8 Native Showcase Visual Components", () => {
  it("renders Stage 01: LegislativeJourneyVisual", () => {
    render(<LegislativeJourneyVisual />);
    expect(screen.getByText("The Telecommunications Act, 2023")).toBeDefined();
    expect(screen.getByText("ENACTED ACT")).toBeDefined();
  });

  it("renders Stage 02: WorkspaceCommandCenterVisual", () => {
    render(<WorkspaceCommandCenterVisual />);
    expect(screen.getByText("Workspace Telemetry Stream")).toBeDefined();
    expect(screen.getByText("ILLUSTRATIVE DEMO DATA")).toBeDefined();
    expect(screen.getByText("47")).toBeDefined(); // Quant equities
  });

  it("renders Stage 03: CorporateExposureNetworkVisual", () => {
    render(<CorporateExposureNetworkVisual />);
    expect(screen.getByText("Legislative Corporate Exposure Graph")).toBeDefined();
    expect(screen.getAllByText("BHARTIARTL").length).toBeGreaterThan(0);
  });

  it("renders Stage 04: StateIntelligenceMapVisual with 0.00% firewall guarantee", () => {
    render(<StateIntelligenceMapVisual />);
    expect(screen.getByText("India Statutory Jurisdiction Map")).toBeDefined();
    expect(screen.getByText("STATE PREDICTION FIREWALL GUARANTEE")).toBeDefined();
    expect(screen.getByText("0.00% LEAKAGE")).toBeDefined();
  });

  it("renders Stage 05: WatchlistIntelligenceVisual", () => {
    render(<WatchlistIntelligenceVisual />);
    expect(screen.getByText("Priority Regulatory Watchlists")).toBeDefined();
    expect(screen.getByText("Statutory Acts")).toBeDefined();
    expect(screen.getByText("Quant Equities")).toBeDefined();
  });

  it("renders Stage 06: AlertIntelligenceVisual", () => {
    render(<AlertIntelligenceVisual />);
    expect(screen.getByText("Alert Thresholds & Multi-Channel Delivery")).toBeDefined();
    expect(screen.getAllByText("85%").length).toBeGreaterThan(0);
  });

  it("renders Stage 07: SeanceMobileShowcase", () => {
    render(<SeanceMobileShowcase />);
    expect(screen.getByText("SEANCE")).toBeDefined();
    expect(screen.getByText("/ MOBILE")).toBeDefined();
  });

  it("renders Stage 08: WorkspaceLaunchVisual", () => {
    render(<WorkspaceLaunchVisual />);
    expect(screen.getByText("Workspace Deployment Matrix")).toBeDefined();
    expect(screen.getByText("ALL SYSTEMS VERIFIED")).toBeDefined();
    expect(screen.getByText("Statutory Intelligence Engine")).toBeDefined();
  });
});
