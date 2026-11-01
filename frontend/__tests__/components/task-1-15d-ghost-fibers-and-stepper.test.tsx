/**
 * __tests__/components/task-1-15d-ghost-fibers-and-stepper.test.tsx
 * =================================================================
 * Updated for Task 1.15E visual refinement:
 * - Ghost Fibers Canvas Component & Full-Viewport Background
 * - Minimal Numbered Horizontal Stepper (1 to 8)
 * - Confirms complete removal of legacy phase headings and cards
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GhostFibers } from "@/components/onboarding/GhostFibers";
import { GhostFibersBackground } from "@/components/onboarding/GhostFibersBackground";
import {
  OnboardingConnectedStepper,
  ONBOARDING_PHASES,
} from "@/components/onboarding/OnboardingConnectedStepper";

describe("Task 1.15E — Ghost Fibers Component", () => {
  beforeEach(() => {
    // Mock HTMLCanvasElement.getContext
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
      createLinearGradient: vi.fn().mockReturnValue({
        addColorStop: vi.fn(),
      }),
      createRadialGradient: vi.fn().mockReturnValue({
        addColorStop: vi.fn(),
      }),
    });
  });

  it("renders canvas element with pointer-events-none and correct testid", () => {
    render(
      <GhostFibers
        glowColor="#8b5cf6"
        layers={2}
        threads={28}
        fiberStyle="ribbon"
        lineColor="#dfd1fc"
        secondaryColor="#6f4ac5"
      />
    );

    const canvas = screen.getByTestId("ghost-fibers-canvas");
    expect(canvas).toBeDefined();
    expect(canvas.style.pointerEvents).toBe("none");
    expect(canvas.style.width).toMatch(/100%|\d+px/);
    expect(canvas.style.height).toMatch(/100%|\d+px/);
  });

  it("renders GhostFibersBackground with fixed full-screen layout and z-0", () => {
    render(<GhostFibersBackground />);

    const bg = screen.getByTestId("ghost-fibers-background");
    expect(bg).toBeDefined();
    expect(bg.className).toContain("fixed");
    expect(bg.className).toContain("inset-0");
    expect(bg.className).toContain("pointer-events-none");
    expect(bg.className).toContain("z-0");
  });
});

describe("Task 1.15E — Minimal Numbered Progress Stepper (1 to 8)", () => {
  it("renders all 8 numbered step indicators and no legacy phase headings", () => {
    render(<OnboardingConnectedStepper currentStep={1} totalSteps={8} />);

    expect(screen.getByTestId("onboarding-progress-indicator")).toBeDefined();
    for (let i = 1; i <= 8; i++) {
      expect(screen.getByTestId(`step-indicator-${i}`)).toBeDefined();
    }

    // Verify absolute removal of phase headings
    expect(screen.queryByText("Workspace Foundation")).toBeNull();
    expect(screen.queryByText("Intelligence Preferences")).toBeNull();
    expect(screen.queryByText("Workspace Launch")).toBeNull();
  });

  it("Step 1 highlights position 1 as active, upcoming 2-8", () => {
    render(<OnboardingConnectedStepper currentStep={1} totalSteps={8} />);

    const s1 = screen.getByTestId("step-indicator-1");
    const s2 = screen.getByTestId("step-indicator-2");

    expect(s1.getAttribute("data-step-state")).toBe("active");
    expect(s2.getAttribute("data-step-state")).toBe("upcoming");
    expect(screen.getByText("13%")).toBeDefined();
  });

  it("Step 3 highlights positions 1-2 completed, position 3 active", () => {
    render(<OnboardingConnectedStepper currentStep={3} totalSteps={8} />);

    const s1 = screen.getByTestId("step-indicator-1");
    const s2 = screen.getByTestId("step-indicator-2");
    const s3 = screen.getByTestId("step-indicator-3");
    const s4 = screen.getByTestId("step-indicator-4");

    expect(s1.getAttribute("data-step-state")).toBe("completed");
    expect(s2.getAttribute("data-step-state")).toBe("completed");
    expect(s3.getAttribute("data-step-state")).toBe("active");
    expect(s4.getAttribute("data-step-state")).toBe("upcoming");
    expect(screen.getByText("38%")).toBeDefined();
  });

  it("Step 4 highlights positions 1-3 completed, position 4 active", () => {
    render(<OnboardingConnectedStepper currentStep={4} totalSteps={8} />);

    const s3 = screen.getByTestId("step-indicator-3");
    const s4 = screen.getByTestId("step-indicator-4");
    const s5 = screen.getByTestId("step-indicator-5");

    expect(s3.getAttribute("data-step-state")).toBe("completed");
    expect(s4.getAttribute("data-step-state")).toBe("active");
    expect(s5.getAttribute("data-step-state")).toBe("upcoming");
    expect(screen.getByText("50%")).toBeDefined();
  });

  it("Step 6 highlights positions 1-5 completed, position 6 active", () => {
    render(<OnboardingConnectedStepper currentStep={6} totalSteps={8} />);

    const s5 = screen.getByTestId("step-indicator-5");
    const s6 = screen.getByTestId("step-indicator-6");
    const s7 = screen.getByTestId("step-indicator-7");

    expect(s5.getAttribute("data-step-state")).toBe("completed");
    expect(s6.getAttribute("data-step-state")).toBe("active");
    expect(s7.getAttribute("data-step-state")).toBe("upcoming");
    expect(screen.getByText("75%")).toBeDefined();
  });

  it("Step 8 highlights positions 1-7 completed, position 8 active", () => {
    render(<OnboardingConnectedStepper currentStep={8} totalSteps={8} />);

    const s7 = screen.getByTestId("step-indicator-7");
    const s8 = screen.getByTestId("step-indicator-8");

    expect(s7.getAttribute("data-step-state")).toBe("completed");
    expect(s8.getAttribute("data-step-state")).toBe("active");
    expect(screen.getByText("100%")).toBeDefined();
  });

  it("triggers onStepSelect / onPhaseSelect when clicking on a completed step", () => {
    const handleSelect = vi.fn();
    render(
      <OnboardingConnectedStepper
        currentStep={5}
        totalSteps={8}
        onStepSelect={handleSelect}
      />
    );

    // Step 2 is completed -> clickable
    const step2Btn = screen.getByTestId("step-indicator-2");
    fireEvent.click(step2Btn);
    expect(handleSelect).toHaveBeenCalledWith(2);
  });
});
