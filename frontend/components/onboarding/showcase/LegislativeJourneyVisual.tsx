/**
 * components/onboarding/showcase/LegislativeJourneyVisual.tsx
 * ==========================================================
 * TASK 1.15C — Stage 01: Native Animated Legislative Journey Visualization.
 *
 * Visual elements:
 * - Bill introduced -> Committee review -> Legislative passage -> Presidential assent
 * - Animated progressive connecting timeline
 * - Active milestone indicator with subtle pulsing halo
 * - Evidence-backed institutional terminology (Lok Sabha, Rajya Sabha, Gazette Assent)
 * - Illustrative generic lifecycle notice
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

interface Milestone {
  id: string;
  stepNumber: number;
  label: string;
  sublabel: string;
  house: string;
  date: string;
  status: "completed" | "active" | "upcoming";
  details: string;
}

const MILESTONES: Milestone[] = [
  {
    id: "introduced",
    stepNumber: 1,
    label: "Bill Introduced",
    sublabel: "Formal Introduction",
    house: "Lok Sabha (Lower House)",
    date: "18 Dec 2023",
    status: "completed",
    details: "First reading completed; bill tabled and published in Gazette Part II.",
  },
  {
    id: "committee",
    stepNumber: 2,
    label: "Parliamentary Review",
    sublabel: "Standing Committee on Communications",
    house: "Joint Review Panel",
    date: "20 Dec 2023",
    status: "completed",
    details: "Clause-by-clause scrutiny; stakeholder memoranda evaluated.",
  },
  {
    id: "passage",
    stepNumber: 3,
    label: "Bicameral Passage",
    sublabel: "Lok Sabha & Rajya Sabha Affirmation",
    house: "Both Chambers of Parliament",
    date: "21 Dec 2023",
    status: "completed",
    details: "Passed by Lok Sabha (voice vote) and Rajya Sabha with statutory amendments.",
  },
  {
    id: "assent",
    stepNumber: 4,
    label: "Presidential Assent",
    sublabel: "Enactment & Statutory Notification",
    house: "Office of the President of India",
    date: "24 Dec 2023",
    status: "active",
    details: "Assent granted under Article 111 of Constitution; enacted as Act No. 44 of 2023.",
  },
];

export function LegislativeJourneyVisual({ className }: { className?: string }) {
  const [selectedMilestone, setSelectedMilestone] = useState<Milestone>(MILESTONES[3]);

  return (
    <div
      className={cn(
        "relative w-full h-full flex flex-col justify-between p-4 sm:p-5 select-none text-white",
        className
      )}
      role="region"
      aria-label="Legislative Journey Visualization"
    >
      {/* Top Dossier Header Card */}
      <div className="flex items-start justify-between gap-3 p-3 rounded-xl glass-elevated border border-white/[0.12] shadow-md">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-semibold">
              ENACTED ACT
            </span>
            <span className="text-[11px] font-mono text-[#A3A3A3]">Act No. 44 of 2023</span>
          </div>
          <h3 className="text-sm font-semibold text-[#F4F4F4] tracking-tight">
            The Telecommunications Act, 2023
          </h3>
          <p className="text-[11px] text-[#A3A3A3]">
            Ministry of Communications · Parliament of India
          </p>
        </div>

        <div className="text-right hidden sm:block">
          <div className="text-[10px] font-mono text-[#666666] uppercase">Legislative Route</div>
          <div className="text-xs font-mono font-medium text-emerald-400">4 / 4 Milestones Reached</div>
        </div>
      </div>

      {/* Main Procedural Timeline Visualization */}
      <div className="relative my-3 sm:my-5 px-2">
        {/* Subtle connecting track line */}
        <div className="absolute top-4 left-6 right-6 h-[2px] bg-white/10 z-0">
          {/* Animated active progress fill */}
          <div
            className="h-full bg-gradient-to-r from-emerald-500 via-blue-500 to-emerald-400 transition-all duration-700 ease-out"
            style={{ width: "100%" }}
          />
        </div>

        {/* Milestone Nodes */}
        <div className="relative z-10 grid grid-cols-4 gap-2">
          {MILESTONES.map((m) => {
            const isSelected = selectedMilestone.id === m.id;
            const isActive = m.status === "active";

            return (
              <button
                key={m.id}
                type="button"
                onClick={() => setSelectedMilestone(m)}
                className="group flex flex-col items-center text-center focus:outline-none"
              >
                {/* Node Circle */}
                <div
                  className={cn(
                    "relative w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300",
                    "border text-xs font-mono font-bold shadow-lg",
                    isSelected
                      ? "bg-white text-black border-white ring-2 ring-white/40 scale-110"
                      : "bg-[#181818] border-white/20 text-[#A3A3A3] hover:border-white/50 hover:text-white"
                  )}
                >
                  {isActive && (
                    <span className="absolute -inset-1 rounded-full bg-emerald-400/30 animate-ping" />
                  )}
                  {m.stepNumber}
                </div>

                {/* Milestone Label */}
                <span
                  className={cn(
                    "mt-2 text-[11px] font-medium leading-tight transition-colors line-clamp-1",
                    isSelected ? "text-white font-semibold" : "text-[#A3A3A3] group-hover:text-white"
                  )}
                >
                  {m.label}
                </span>

                <span className="text-[9px] font-mono text-[#666666] hidden sm:block">
                  {m.date}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Milestone Inspection Drawer */}
      <div className="p-3 sm:p-3.5 rounded-xl glass-panel border border-white/[0.10] space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-xs font-semibold text-[#F4F4F4]">
              {selectedMilestone.label}
            </span>
            <span className="text-[10px] font-mono text-[#666666]">
              · {selectedMilestone.house}
            </span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {selectedMilestone.date}
          </span>
        </div>
        <p className="text-xs text-[#A3A3A3] leading-relaxed line-clamp-2">
          {selectedMilestone.details}
        </p>
      </div>

      {/* Illustrative Notice Footer */}
      <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#666666] border-t border-white/[0.06]">
        <span>GENERIC LEGISLATIVE LIFECYCLE MODEL</span>
        <span className="text-[#A3A3A3]">AUTHORITATIVE PARLIAMENTARY TERMS</span>
      </div>
    </div>
  );
}

export default LegislativeJourneyVisual;

