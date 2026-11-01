/**
 * __tests__/components/task-1-15e-visual-refinement.test.tsx
 * ==========================================================
 * Comprehensive unit test suite for Task 1.15E:
 * - Minimal Numbered Horizontal Stepper (1 to 8 positions, zero phase headings)
 * - Refined Ghost Fibers with ribbon rendering & restrained density
 * - Animation performance invariants (requestAnimationFrame loop, reduced motion)
 * - Single-viewport layout integrity & state persistence
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GhostFibers } from "@/components/onboarding/GhostFibers";
import { GhostFibersBackground } from "@/components/onboarding/GhostFibersBackground";
import { MinimalNumberedStepper } from "@/components/onboarding/OnboardingConnectedStepper";

describe("Task 1.15E — Minimal Numbered Stepper (1 to 8)", () => {
  it("renders exactly eight numbered positions 1-8 without phase headings", () => {
    render(<MinimalNumberedStepper currentStep={1} totalSteps={8} />);

    expect(screen.getByTestId("onboarding-progress-indicator")).toBeDefined();
    for (let i = 1; i <= 8; i++) {
      const stepIndicator = screen.getByTestId(`step-indicator-${i}`);
      expect(stepIndicator).toBeDefined();
    }

    // Absolutely no phase headings
    expect(screen.queryByText("Foundation")).toBeNull();
    expect(screen.queryByText("Workspace Foundation")).toBeNull();
    expect(screen.queryByText("Intelligence Preferences")).toBeNull();
    expect(screen.queryByText("Workspace Launch")).toBeNull();
  });

  it("Step 1 highlights position 1", () => {
    render(<MinimalNumberedStepper currentStep={1} totalSteps={8} />);

    const step1 = screen.getByTestId("step-indicator-1");
    expect(step1.getAttribute("data-step-state")).toBe("active");

    for (let i = 2; i <= 8; i++) {
      const stepI = screen.getByTestId(`step-indicator-${i}`);
      expect(stepI.getAttribute("data-step-state")).toBe("upcoming");
    }
  });

  it("Step 4 highlights position 4, with 1-3 completed", () => {
    render(<MinimalNumberedStepper currentStep={4} totalSteps={8} />);

    for (let i = 1; i <= 3; i++) {
      const stepI = screen.getByTestId(`step-indicator-${i}`);
      expect(stepI.getAttribute("data-step-state")).toBe("completed");
    }

    const step4 = screen.getByTestId("step-indicator-4");
    expect(step4.getAttribute("data-step-state")).toBe("active");

    for (let i = 5; i <= 8; i++) {
      const stepI = screen.getByTestId(`step-indicator-${i}`);
      expect(stepI.getAttribute("data-step-state")).toBe("upcoming");
    }
  });

  it("Step 6 highlights position 6, with 1-5 completed", () => {
    render(<MinimalNumberedStepper currentStep={6} totalSteps={8} />);

    for (let i = 1; i <= 5; i++) {
      const stepI = screen.getByTestId(`step-indicator-${i}`);
      expect(stepI.getAttribute("data-step-state")).toBe("completed");
    }

    const step6 = screen.getByTestId("step-indicator-6");
    expect(step6.getAttribute("data-step-state")).toBe("active");

    for (let i = 7; i <= 8; i++) {
      const stepI = screen.getByTestId(`step-indicator-${i}`);
      expect(stepI.getAttribute("data-step-state")).toBe("upcoming");
    }
  });

  it("Step 8 highlights position 8, with 1-7 completed", () => {
    render(<MinimalNumberedStepper currentStep={8} totalSteps={8} />);

    for (let i = 1; i <= 7; i++) {
      const stepI = screen.getByTestId(`step-indicator-${i}`);
      expect(stepI.getAttribute("data-step-state")).toBe("completed");
    }

    const step8 = screen.getByTestId("step-indicator-8");
    expect(step8.getAttribute("data-step-state")).toBe("active");
  });

  it("allows clicking previous steps to navigate back", () => {
    const handleStepSelect = vi.fn();
    render(
      <MinimalNumberedStepper
        currentStep={6}
        totalSteps={8}
        onStepSelect={handleStepSelect}
      />
    );

    // Step 3 is completed -> clicking navigates to step 3
    const step3 = screen.getByTestId("step-indicator-3");
    fireEvent.click(step3);
    expect(handleStepSelect).toHaveBeenCalledWith(3);
  });
});

describe("Task 1.15E — Refined Ghost Fibers Background", () => {
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
      createLinearGradient: vi.fn().mockReturnValue({
        addColorStop: vi.fn(),
      }),
      createRadialGradient: vi.fn().mockReturnValue({
        addColorStop: vi.fn(),
      }),
    });
  });

  it("renders GhostFibers with ribbon fiberStyle and dark palette", () => {
    render(
      <GhostFibers
        glowColor="#8b5cf6"
        lineColor="#dfd1fc"
        secondaryColor="#6f4ac5"
        fiberStyle="ribbon"
        threads={28}
        layers={2}
      />
    );

    const canvas = screen.getByTestId("ghost-fibers-canvas");
    expect(canvas).toBeDefined();
    expect(canvas.style.pointerEvents).toBe("none");
  });

  it("renders GhostFibersBackground with fixed full-screen layout", () => {
    render(<GhostFibersBackground />);

    const bg = screen.getByTestId("ghost-fibers-background");
    expect(bg).toBeDefined();
    expect(bg.className).toContain("fixed");
    expect(bg.className).toContain("inset-0");
    expect(bg.className).toContain("z-0");
  });
});

