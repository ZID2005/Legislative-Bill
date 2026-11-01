/**
 * components/onboarding/GhostFibersBackground.tsx
 * ==============================================
 * TASK 1.15G — Authentic React Bits Ghost Fibers Background Integration.
 *
 * Full-Viewport Background Configuration:
 * - Fixed viewport coverage: inset: 0, w-full, h-full, z-0.
 * - Deep charcoal base environment (#080808) with authentic violet/lavender particle-fiber ribbons.
 * - Exact Task 1.15G parameters: 3 layers, 72 threads, 1.2 twist, 18 deg rotation, fiberStyle="dots".
 * - Atmospheric glow (#8b5cf6), primary fiber (#dfd1fc), secondary fiber (#6f4ac5).
 * - Real interactive mouse focus response & click ripple pulse via original WebGL2 shader pipeline.
 * - Preserves onboarding accessibility, stepper, and form controls without blocking glass shell.
 */

"use client";

import React from "react";
import { GhostFibers } from "./GhostFibers";
import { cn } from "@/lib/utils";

export interface GhostFibersBackgroundProps {
  className?: string;
  glowColor?: string;
  lineColor?: string;
  secondaryColor?: string;
}

export function GhostFibersBackground({
  className,
  glowColor = "#8b5cf6",
  lineColor = "#dfd1fc",
  secondaryColor = "#6f4ac5",
}: GhostFibersBackgroundProps) {
  return (
    <div
      aria-hidden="true"
      data-testid="ghost-fibers-background"
      className={cn(
        "fixed inset-0 w-full h-full pointer-events-none overflow-hidden select-none z-0 bg-[#080808]",
        className
      )}
    >
      {/* Subtle atmospheric ambient glow behind fibers */}
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(139,92,246,0.15),rgba(8,8,8,0))] opacity-60 pointer-events-none"
      />

      {/* Ghost Fibers Authentic Particle-Fiber Wave Field (Exact Task 1.15G Configuration) */}
      <div className="relative w-full h-full">
        <GhostFibers
          glowColor={glowColor}
          layers={3}
          twist={1.2}
          threads={72}
          fiberStyle="dots"
          depthOfField={0.85}
          hoverEffect="focus"
          intro
          mouseInteraction
          lineColor={lineColor}
          secondaryColor={secondaryColor}
          gradient="depth"
          waves={1}
          volume={0.7}
          spread={1}
          scale={1}
          rotation={18}
          perspective={0.65}
          density={1}
          thickness={1}
          tips={0}
          foldGlow={1}
          speed={0.5}
          flow={0.4}
          rollSpeed={0.15}
          focusDepth={0}
          particles={0.5}
          sparkle={0.5}
          glow={0.8}
          brightness={1}
          vignette={0.3}
          grain={0.06}
          mouseStrength={1}
          pulseOnClick
          lightMode={false}
        />
      </div>
    </div>
  );
}

export default GhostFibersBackground;
