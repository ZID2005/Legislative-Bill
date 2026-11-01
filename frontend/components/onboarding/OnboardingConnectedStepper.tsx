/**
 * components/onboarding/OnboardingConnectedStepper.tsx
 * ====================================================
 * TASK 1.15E — Minimal Numbered Horizontal Progress Stepper (1 to 8).
 *
 * Minimal horizontal numbered progress bar matching Reference Image 1:
 * - Exactly eight numbered positions: 1 — 2 — 3 — 4 — 5 — 6 — 7 — 8.
 * - Completed steps: filled indicator with a subtle checkmark.
 * - Current step: clearly highlighted numbered circle with purple halo.
 * - Upcoming steps: subdued numbered circles.
 * - Thin connecting lines that progressively fill as user advances.
 * - Restrained lavender/purple accents (#8b5cf6 / #dfd1fc / #6f4ac5).
 * - Overall completion percentage displayed separately in small mono typography.
 * - Absolutely zero phase headings, zero phase descriptions, zero large cards.
 * - Compact height (<44px) to preserve desktop single-viewport requirement.
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";

// Backward-compatible metadata export (no longer rendered visually)
export interface OnboardingPhase {
  id: number;
  label: string;
  category: string;
  description: string;
  steps: number[];
}

export const ONBOARDING_PHASES: OnboardingPhase[] = [
  {
    id: 1,
    category: "FOUNDATION",
    label: "Workspace Foundation",
    description: "Establish your institutional workspace and analytical scope.",
    steps: [1, 2, 3],
  },
  {
    id: 2,
    category: "PREFERENCES",
    label: "Intelligence Preferences",
    description: "Configure the intelligence and monitoring experience.",
    steps: [4, 5, 6, 7],
  },
  {
    id: 3,
    category: "LAUNCH",
    label: "Workspace Launch",
    description: "Review your configuration and enter Seance.",
    steps: [8],
  },
];

export interface OnboardingConnectedStepperProps {
  currentStep: number; // 1..8
  totalSteps?: number; // default 8
  stepTitle?: string;
  onPhaseSelect?: (step: number) => void;
  onStepSelect?: (step: number) => void;
  className?: string;
  maxStepReached?: number;
}

export function OnboardingConnectedStepper({
  currentStep,
  totalSteps = 8,
  stepTitle,
  onPhaseSelect,
  onStepSelect,
  className,
  maxStepReached,
}: OnboardingConnectedStepperProps) {
  const percentComplete = Math.round((currentStep / totalSteps) * 100);
  const handleSelect = onStepSelect || onPhaseSelect;

  const steps = Array.from({ length: totalSteps }, (_, i) => i + 1);

  return (
    <nav
      className={cn("w-full max-w-2xl mx-auto my-1 sm:my-2 px-2 flex-shrink-0", className)}
      aria-label="Onboarding Progress Stepper"
      data-testid="onboarding-progress-indicator"
    >
      {/* -------------------------------------------------------------------
       * Minimal Glass Stepper Bar: Compact, Centered, Numbered 1 to 8
       * ------------------------------------------------------------------- */}
      <div
        className="glass-panel rounded-full px-3 sm:px-4 py-1.5 sm:py-2 border border-white/[0.10] shadow-lg shadow-black/40 flex items-center justify-between"
        data-testid="onboarding-progress-stepper"
      >
        <div className="flex items-center justify-between w-full relative">
          {steps.map((stepNum, idx) => {
            const isCompleted = stepNum < currentStep;
            const isActive = stepNum === currentStep;
            const isUpcoming = stepNum > currentStep;
            const isVisited = typeof maxStepReached === "number" && stepNum <= maxStepReached;
            const isClickable = Boolean(handleSelect && (isCompleted || isActive || isVisited));

            return (
              <React.Fragment key={stepNum}>
                {/* Thin connecting line between steps */}
                {idx > 0 && (
                  <div
                    aria-hidden="true"
                    className="relative flex-1 h-[2px] mx-1 sm:mx-2 bg-white/[0.10] rounded-full overflow-hidden self-center"
                    data-testid={`stepper-line-${idx}`}
                  >
                    <div
                      className="h-full bg-gradient-to-r from-purple-400 via-indigo-300 to-[#dfd1fc] transition-all duration-400 ease-out rounded-full"
                      style={{
                        width: currentStep >= stepNum ? "100%" : "0%",
                      }}
                    />
                  </div>
                )}

                {/* Numbered Step Circle */}
                <button
                  type="button"
                  onClick={() => isClickable && handleSelect?.(stepNum)}
                  disabled={!isClickable}
                  aria-label={`Step ${stepNum} of ${totalSteps}${
                    isCompleted ? " (Completed)" : isActive ? " (Active)" : " (Upcoming)"
                  }`}
                  aria-current={isActive ? "step" : undefined}
                  data-testid={`step-indicator-${stepNum}`}
                  data-step-state={
                    isCompleted ? "completed" : isActive ? "active" : "upcoming"
                  }
                  className={cn(
                    "relative w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center font-mono text-xs transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-purple-400/50 flex-shrink-0",
                    isClickable ? "cursor-pointer" : "cursor-default",
                    isCompleted
                      ? "bg-gradient-to-br from-purple-200 to-white text-[#080808] font-bold shadow-md shadow-white/20 ring-1 ring-white/80"
                      : isActive
                      ? "bg-[#1f1b2e] text-white border-2 border-purple-400 ring-4 ring-purple-500/25 shadow-lg shadow-purple-500/30 font-bold scale-105"
                      : isVisited
                      ? "bg-white/[0.08] text-white/90 border border-white/[0.24] hover:bg-white/[0.14]"
                      : "bg-white/[0.04] text-[#737373] border border-white/[0.12]"
                  )}
                >
                  {isCompleted ? (
                    /* Subtle Checkmark */
                    <svg
                      className="w-3.5 h-3.5 text-[#080808]"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={3}
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : (
                    /* Step Number */
                    <span>{stepNum}</span>
                  )}

                  {/* Active pulse aura */}
                  {isActive && (
                    <span className="absolute inset-0 rounded-full border border-purple-400/60 animate-ping opacity-35 pointer-events-none" />
                  )}
                </button>
              </React.Fragment>
            );
          })}
        </div>

        {/* Small Completion Percentage Display */}
        <span
          className="ml-3 pl-3 border-l border-white/[0.10] text-[10px] sm:text-[11px] font-mono text-[#A3A3A3] tracking-wider whitespace-nowrap flex-shrink-0 hidden sm:inline-block"
          data-testid="onboarding-completion-percentage"
        >
          {percentComplete}%
        </span>
      </div>
    </nav>
  );
}

// Named alias for semantic clarity
export const MinimalNumberedStepper = OnboardingConnectedStepper;

export default OnboardingConnectedStepper;
