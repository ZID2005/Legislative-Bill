/**
 * app/onboarding/layout.tsx
 * =========================
 * Dedicated full-screen layout for Seance's eight-step onboarding experience.
 *
 * TASK 1.15E: Single-Viewport Desktop Layout & Ghost Fibers Background.
 * - Mounts GhostFibersBackground once at the route layout level (zero remounts).
 * - Enforces single-viewport desktop fit (lg:h-screen lg:overflow-hidden) at 1440x900.
 * - Allows natural vertical scrolling on mobile/tablet when required.
 */

import React from "react";
import type { Metadata } from "next";
import { GhostFibersBackground } from "@/components/onboarding/GhostFibersBackground";

export const metadata: Metadata = {
  title: "Workspace Setup · Seance",
  description:
    "Configure your Seance workspace for Indian legislative bill impact, corporate exposure, and econometric decision intelligence.",
};

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen lg:h-screen lg:max-h-screen lg:overflow-hidden w-full bg-[#080808] text-[#F4F4F4] flex flex-col justify-between selection:bg-white/20 selection:text-white overflow-x-hidden">
      {/* Full-viewport Ghost Fibers animated canvas behind all surfaces */}
      <GhostFibersBackground />

      {/* Layered foreground content with translucent liquid glass surfaces */}
      <div className="relative z-10 flex flex-col flex-1 w-full min-h-screen lg:min-h-0 lg:h-full justify-between">
        {children}
      </div>
    </div>
  );
}
