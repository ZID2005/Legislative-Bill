/**
 * components/onboarding/showcase/WorkspaceCommandCenterVisual.tsx
 * ==============================================================
 * TASK 1.15C — Stage 02: Native Workspace Command Center Visualization.
 *
 * Visual elements:
 * - Monitored entities counters (Central Acts, State Enactments, Quant Equities)
 * - Source freshness indicators (Lok Sabha, Gazette of India, State Feeds)
 * - Compact activity feed stream
 * - Active alert telemetry indicator
 * - Explicit illustrative demo data disclaimer
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";

export function WorkspaceCommandCenterVisual({ className }: { className?: string }) {
  const sources = [
    { name: "Lok Sabha / Digital Sansad", freshness: "4m ago", status: "ONLINE", ping: "emerald" },
    { name: "Gazette of India Central", freshness: "12m ago", status: "SYNCED", ping: "emerald" },
    { name: "Sub-National State Gazettes", freshness: "28m ago", status: "POLLING", ping: "amber" },
  ];

  const activities = [
    { time: "09:41", type: "GAZETTE", text: "Act No. 44 of 2023 published in Extraordinary Gazette", badge: "CENTRAL" },
    { time: "09:35", type: "BETA", text: "Exposure vector mapped for 47 liquid NSE/BSE securities", badge: "QUANT" },
    { time: "09:20", type: "FIREWALL", text: "Zero-prediction firewall affirmed on 44 State enactments", badge: "SECURITY" },
  ];

  return (
    <div
      className={cn(
        "relative w-full h-full flex flex-col justify-between p-4 sm:p-5 select-none text-white",
        className
      )}
      role="region"
      aria-label="Workspace Command Center Visualization"
    >
      {/* Top Header & Telemetry Status */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-xs font-mono font-semibold text-[#F4F4F4] uppercase tracking-wider">
            Workspace Telemetry Stream
          </span>
        </div>
        <div className="px-2 py-0.5 rounded text-[9px] font-mono font-semibold bg-white/[0.08] text-[#A3A3A3] border border-white/10">
          ILLUSTRATIVE DEMO DATA
        </div>
      </div>

      {/* Monitored Universe Counters Grid */}
      <div className="grid grid-cols-3 gap-2.5 my-3">
        <div className="p-2.5 sm:p-3 rounded-xl glass-elevated border border-white/[0.10] flex flex-col justify-between">
          <span className="text-[10px] font-mono text-[#666666] uppercase">Central Acts</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold font-mono text-white">20</span>
            <span className="text-[10px] font-mono text-[#A3A3A3]">Acts</span>
          </div>
          <span className="text-[9px] text-emerald-400 font-mono mt-0.5">22 Dossiers</span>
        </div>

        <div className="p-2.5 sm:p-3 rounded-xl glass-elevated border border-white/[0.10] flex flex-col justify-between">
          <span className="text-[10px] font-mono text-[#666666] uppercase">State Acts</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold font-mono text-white">44</span>
            <span className="text-[10px] font-mono text-[#A3A3A3]">Enacted</span>
          </div>
          <span className="text-[9px] text-blue-400 font-mono mt-0.5">4 Assemblies</span>
        </div>

        <div className="p-2.5 sm:p-3 rounded-xl glass-elevated border border-white/[0.10] flex flex-col justify-between">
          <span className="text-[10px] font-mono text-[#666666] uppercase">Quant Equities</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold font-mono text-white">47</span>
            <span className="text-[10px] font-mono text-[#A3A3A3]">Equities</span>
          </div>
          <span className="text-[9px] text-emerald-400 font-mono mt-0.5">13 Macro Sectors</span>
        </div>
      </div>

      {/* Source Freshness & Ingestion Rows */}
      <div className="p-3 rounded-xl glass-panel border border-white/[0.10] space-y-2">
        <div className="text-[10px] font-mono text-[#666666] uppercase tracking-wider flex items-center justify-between">
          <span>Official Ingestion Pipelines</span>
          <span>Latency</span>
        </div>

        <div className="space-y-1.5">
          {sources.map((s, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-[#181818]/60 border border-white/[0.04]"
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "w-1.5 h-1.5 rounded-full",
                    s.ping === "emerald" ? "bg-emerald-400" : "bg-amber-400"
                  )}
                />
                <span className="text-[#F4F4F4] text-[11px] font-medium">{s.name}</span>
              </div>
              <div className="flex items-center gap-2 font-mono text-[10px]">
                <span className="text-[#A3A3A3]">{s.freshness}</span>
                <span className="text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded">
                  {s.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Compact Activity Timeline Feed */}
      <div className="mt-2 space-y-1">
        <div className="text-[10px] font-mono text-[#666666] uppercase tracking-wider px-1">
          Recent Institutional Activity
        </div>
        <div className="space-y-1">
          {activities.slice(0, 2).map((act, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-2 rounded-lg bg-[#161616]/70 border border-white/[0.04] text-[11px]"
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <span className="font-mono text-[10px] text-[#666666]">{act.time}</span>
                <span className="text-[#A3A3A3] truncate">{act.text}</span>
              </div>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/[0.06] text-white/80 shrink-0">
                {act.badge}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#666666] border-t border-white/[0.06]">
        <span>CENTRAL MONITORED PIPELINES</span>
        <span className="text-emerald-400">STATUS: NOMINAL</span>
      </div>
    </div>
  );
}

export default WorkspaceCommandCenterVisual;

