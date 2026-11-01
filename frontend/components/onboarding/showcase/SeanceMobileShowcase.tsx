/**
 * components/onboarding/showcase/SeanceMobileShowcase.tsx
 * ======================================================
 * TASK 1.15C — Stage 07: Premium Smartphone Presentation & Mobile Intelligence.
 *
 * Implements:
 * - Integration with @/components/ui/apple-iphone-17-pro (IPhone17ProMax)
 * - Native Seance mobile intelligence interface (no screenshots, real React DOM)
 * - Seance mobile branding & status header
 * - Compact legislative dossier feed card
 * - Corporate exposure badge & mini event-study AR chart
 * - Grounded AI Analyst statutory response preview with verified citation
 * - Interactive Dynamic Island toggle for live telemetry demonstration
 */

"use client";

import React, { useState } from "react";
import {
  IPhone17ProMax,
  type DynamicIslandSize,
} from "@/components/ui/apple-iphone-17-pro";
import { cn } from "@/lib/utils";

export function SeanceMobileShowcase({ className }: { className?: string }) {
  const [dynamicIslandSize, setDynamicIslandSize] =
    useState<DynamicIslandSize>("default");

  const handleDynamicIslandTap = () => {
    setDynamicIslandSize((curr) => (curr === "default" ? "expanded" : "default"));
  };

  return (
    <div
      className={cn(
        "relative w-full h-full flex items-center justify-center p-2 select-none",
        className
      )}
      role="region"
      aria-label="Seance Smartphone Intelligence Showcase"
    >
      {/* Smartphone Hardware Frame */}
      <IPhone17ProMax
        batteryLevel={96}
        dynamicIslandSize={dynamicIslandSize}
        frameColor="graphite"
        signalStrength={4}
        time="9:41"
        onDynamicIslandTap={handleDynamicIslandTap}
        className="transform scale-[0.88] sm:scale-[0.92] lg:scale-[0.95] origin-center transition-all duration-300"
      >
        {/* Mobile Screen Native App UI */}
        <div className="flex h-full flex-col justify-between px-3.5 py-1 text-white bg-[#09090b]">
          {/* Seance Mobile App Header */}
          <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-xs font-bold tracking-widest uppercase text-white">
                SEANCE
              </span>
              <span className="text-[9px] font-mono text-[#666666]">/ MOBILE</span>
            </div>
            <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[8.5px] font-mono text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              LIVE DOSSIER
            </div>
          </div>

          {/* Legislative Dossier Compact Card */}
          <div className="p-2.5 rounded-xl glass-panel border border-white/[0.10] space-y-1">
            <div className="flex items-center justify-between text-[9px] font-mono">
              <span className="text-emerald-400">CENTRAL ACT 44/2023</span>
              <span className="text-[#A3A3A3]">ENACTED</span>
            </div>
            <div className="text-xs font-semibold text-[#F4F4F4] leading-snug">
              The Telecommunications Act, 2023
            </div>
            <div className="flex items-center gap-1.5 text-[9.5px] text-[#A3A3A3]">
              <span>Section 14</span>
              <span>·</span>
              <span className="text-white font-medium">Spectrum Licensing Overhaul</span>
            </div>
          </div>

          {/* Corporate Exposure & Mini Event-Study Chart */}
          <div className="p-2.5 rounded-xl glass-panel border border-white/[0.10] space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-[11px] font-bold text-white">BHARTIARTL</span>
                <span className="px-1 py-0.2 rounded text-[8px] font-mono bg-emerald-500/15 text-emerald-400">
                  DIRECT
                </span>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                +2.4% CAR (t+5)
              </span>
            </div>

            {/* Event Study Mini SVG Sparkline */}
            <div className="w-full h-10 flex items-center justify-center">
              <svg viewBox="0 0 200 40" className="w-full h-full overflow-visible">
                {/* Zero line */}
                <line x1="0" y1="25" x2="200" y2="25" stroke="rgba(255,255,255,0.1)" strokeDasharray="2 2" />
                {/* Event Marker at t=0 */}
                <line x1="80" y1="0" x2="80" y2="40" stroke="rgba(59,130,246,0.5)" strokeWidth="1" strokeDasharray="2 2" />
                <text x="83" y="10" fill="#60a5fa" fontSize="6.5" fontFamily="monospace">t=0</text>
                {/* Cumulative Abnormal Return Line */}
                <polyline
                  fill="none"
                  stroke="#34d399"
                  strokeWidth="1.75"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points="10,25 35,27 60,24 80,25 105,18 130,12 160,9 190,7"
                />
                {/* End Point Dot */}
                <circle cx="190" cy="7" r="2.5" fill="#34d399" />
              </svg>
            </div>
            <div className="flex justify-between text-[8px] font-mono text-[#666666]">
              <span>t-5 Pre-Event</span>
              <span>Event Date</span>
              <span>t+10 Horizon</span>
            </div>
          </div>

          {/* Grounded AI Analyst Response Preview */}
          <div className="p-2.5 rounded-xl glass-elevated border border-white/[0.10] space-y-1">
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-blue-400 font-semibold">
              <span>✦</span>
              <span>GROUNDED AI ANALYST</span>
            </div>
            <p className="text-[10px] text-[#A3A3A3] leading-relaxed line-clamp-2">
              Statutory clause 14 transitions spectrum allocation to administrative assignment for satellite networks, reducing capital expenditure friction.
            </p>
            <div className="flex items-center gap-1 text-[8.5px] font-mono text-emerald-400 pt-0.5">
              <span>PROVENANCE:</span>
              <span className="text-white/80 bg-white/[0.06] px-1 rounded">
                Act 44 of 2023, §14(2)
              </span>
            </div>
          </div>

          {/* Minimal Bottom Mobile App Navigation */}
          <div className="pt-1.5 pb-0.5 border-t border-white/[0.08] flex items-center justify-around text-[9px] font-mono text-[#666666]">
            <span className="text-white font-semibold">Dossier</span>
            <span className="hover:text-white">Watchlist</span>
            <span className="hover:text-white">AI Analyst</span>
            <span className="hover:text-white">Alerts</span>
          </div>
        </div>
      </IPhone17ProMax>
    </div>
  );
}

export default SeanceMobileShowcase;

