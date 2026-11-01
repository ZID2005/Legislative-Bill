/**
 * components/onboarding/showcase/AlertIntelligenceVisual.tsx
 * =========================================================
 * TASK 1.15C — Stage 06: Alert Intelligence & Sensitivity Gauge Visualization.
 *
 * Visual elements:
 * - Animated radial sensitivity threshold gauge
 * - Impact severity level ladder (Low, Medium, High, Critical)
 * - Delivery channel indicators (In-App Telemetry, Scheduled Digest, Webhook)
 * - Frequency configuration preview (Real-time, Daily, Weekly)
 * - Explicit preview simulation disclaimer
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

export function AlertIntelligenceVisual({ className }: { className?: string }) {
  const [threshold, setThreshold] = useState<number>(85);
  const [selectedChannel, setSelectedChannel] = useState<string>("IN_APP");

  // Radial Gauge Calculations
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (threshold / 100) * circumference * 0.75; // 270 deg arc

  return (
    <div
      className={cn(
        "relative w-full h-full flex flex-col justify-between p-4 sm:p-5 select-none text-white",
        className
      )}
      role="region"
      aria-label="Alert Intelligence Visualization"
    >
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
        <div>
          <span className="text-[10px] font-mono uppercase text-[#A3A3A3] tracking-wider block">
            Intelligence Rules
          </span>
          <h3 className="text-xs font-semibold text-[#F4F4F4]">
            Alert Thresholds & Multi-Channel Delivery
          </h3>
        </div>
        <div className="px-2 py-0.5 rounded text-[9px] font-mono font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          LATENCY &lt; 2 MIN
        </div>
      </div>

      {/* Main Gauge & Configuration Area */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 my-2 items-center">
        {/* Left: SVG Radial Sensitivity Dial (5 cols) */}
        <div className="sm:col-span-5 flex flex-col items-center justify-center p-3 rounded-xl glass-panel border border-white/[0.10]">
          <div className="relative w-28 h-28 flex items-center justify-center">
            <svg className="w-full h-full -rotate-135" viewBox="0 0 120 120">
              {/* Background Arc */}
              <circle
                cx="60"
                cy="60"
                r={radius}
                fill="none"
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="8"
                strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
                strokeLinecap="round"
              />
              {/* Active Value Arc */}
              <circle
                cx="60"
                cy="60"
                r={radius}
                fill="none"
                stroke="url(#alertGradient)"
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="transition-all duration-500 ease-out"
              />
              <defs>
                <linearGradient id="alertGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="50%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#f59e0b" />
                </linearGradient>
              </defs>
            </svg>

            {/* Inner Gauge Text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="text-xl font-bold font-mono text-white tracking-tight">
                {threshold}%
              </span>
              <span className="text-[9px] font-mono uppercase text-emerald-400">
                HIGH SEVERITY
              </span>
            </div>
          </div>

          <div className="mt-2 text-center">
            <span className="text-[10px] font-mono text-[#A3A3A3] block">
              Dynamic Sensitivity Threshold
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              <button
                type="button"
                onClick={() => setThreshold(70)}
                className={cn(
                  "px-2 py-0.5 rounded text-[9px] font-mono transition-colors border",
                  threshold === 70
                    ? "bg-white text-black border-white font-bold"
                    : "bg-[#181818] text-[#A3A3A3] border-white/10 hover:text-white"
                )}
              >
                70%
              </button>
              <button
                type="button"
                onClick={() => setThreshold(85)}
                className={cn(
                  "px-2 py-0.5 rounded text-[9px] font-mono transition-colors border",
                  threshold === 85
                    ? "bg-white text-black border-white font-bold"
                    : "bg-[#181818] text-[#A3A3A3] border-white/10 hover:text-white"
                )}
              >
                85%
              </button>
              <button
                type="button"
                onClick={() => setThreshold(95)}
                className={cn(
                  "px-2 py-0.5 rounded text-[9px] font-mono transition-colors border",
                  threshold === 95
                    ? "bg-white text-black border-white font-bold"
                    : "bg-[#181818] text-[#A3A3A3] border-white/10 hover:text-white"
                )}
              >
                95%
              </button>
            </div>
          </div>
        </div>

        {/* Right: Delivery Channels & Severity Ladder (7 cols) */}
        <div className="sm:col-span-7 space-y-2">
          {/* Active Trigger Simulation Card */}
          <div className="p-2.5 rounded-xl glass-elevated border border-white/[0.10] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-amber-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                SIMULATED TRIGGER EVENT
              </span>
              <span className="text-[9px] font-mono text-[#666666]">PREVIEW</span>
            </div>
            <div className="text-xs font-semibold text-white">
              Bicameral Passage Confirmed: Act 44/2023
            </div>
            <div className="text-[10px] text-[#A3A3A3]">
              Exceeds 85% threshold · Automated briefing dispatched
            </div>
          </div>

          {/* Delivery Channels */}
          <div className="space-y-1">
            <div className="text-[10px] font-mono text-[#666666] uppercase px-1">
              Active Delivery Channels
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {[
                { id: "IN_APP", label: "In-App Telemetry", sub: "Live Socket", active: true },
                { id: "DIGEST", label: "Executive Digest", sub: "07:00 IST", active: true },
                { id: "EMAIL", label: "Email Dispatch", sub: "Instant Alert", active: false },
                { id: "WEBHOOK", label: "Webhook REST", sub: "JSON Payload", active: true },
              ].map((c) => (
                <div
                  key={c.id}
                  onClick={() => setSelectedChannel(c.id)}
                  className={cn(
                    "p-2 rounded-lg border text-left cursor-pointer transition-all",
                    selectedChannel === c.id
                      ? "bg-purple-950/40 border-purple-400/50 text-white"
                      : "glass-elevated border-white/[0.08] text-[#A3A3A3] hover:border-white/20"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-medium text-white">{c.label}</span>
                    <span
                      className={cn(
                        "w-1.5 h-1.5 rounded-full",
                        c.active ? "bg-emerald-400" : "bg-white/20"
                      )}
                    />
                  </div>
                  <span className="text-[9px] font-mono text-[#666666]">{c.sub}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#666666] border-t border-white/[0.06]">
        <span>PREVIEW SIMULATION · ZERO UNVERIFIED DISPATCH</span>
        <span className="text-emerald-400">RULES: VERIFIED</span>
      </div>
    </div>
  );
}

export default AlertIntelligenceVisual;

