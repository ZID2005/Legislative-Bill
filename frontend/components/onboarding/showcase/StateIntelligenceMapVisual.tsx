/**
 * components/onboarding/showcase/StateIntelligenceMapVisual.tsx
 * ============================================================
 * TASK 1.15C — Stage 04: State Statutory Intelligence & Firewall Visualization.
 *
 * Visual elements:
 * - Stylized India jurisdiction schematic (Central Parliament + 4 State Assemblies: AP, KA, KL, TS)
 * - Central vs Sub-National statutory coverage metrics
 * - Critical StatePredictionFirewall visualization with 0.00% prediction leakage guarantee
 * - Verified state statutory data, zero speculative stock predictions
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

interface JurisdictionNode {
  id: string;
  code: string;
  name: string;
  tier: "CENTRAL" | "STATE";
  actsCount: number;
  firewallStatus: string;
  description: string;
  x: number;
  y: number;
}

const JURISDICTIONS: JurisdictionNode[] = [
  {
    id: "central",
    code: "CENTRAL",
    name: "Parliament of India (New Delhi)",
    tier: "CENTRAL",
    actsCount: 20,
    firewallStatus: "4,700 Quant Predictions Active",
    description: "Central Parliament Acts with econometric market event studies across 47 liquid securities.",
    x: 230,
    y: 55,
  },
  {
    id: "ap",
    code: "AP",
    name: "Andhra Pradesh Legislative Assembly",
    tier: "STATE",
    actsCount: 11,
    firewallStatus: "Strict Firewall Enforced",
    description: "Sub-national gazette coverage. Governed by zero-stock-prediction architectural firewall.",
    x: 230,
    y: 165,
  },
  {
    id: "ka",
    code: "KA",
    name: "Karnataka Legislative Assembly",
    tier: "STATE",
    actsCount: 12,
    firewallStatus: "Strict Firewall Enforced",
    description: "State enactments tracked for statutory compliance; no speculative equity return models.",
    x: 180,
    y: 175,
  },
  {
    id: "kl",
    code: "KL",
    name: "Kerala Legislative Assembly",
    tier: "STATE",
    actsCount: 10,
    firewallStatus: "Strict Firewall Enforced",
    description: "Official Kerala Gazette monitoring with verified statutory clause extraction.",
    x: 170,
    y: 215,
  },
  {
    id: "ts",
    code: "TS",
    name: "Telangana Legislative Assembly",
    tier: "STATE",
    actsCount: 11,
    firewallStatus: "Strict Firewall Enforced",
    description: "State gazette monitoring unpolluted by quantitative stock forecasts.",
    x: 220,
    y: 135,
  },
];

export function StateIntelligenceMapVisual({ className }: { className?: string }) {
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<JurisdictionNode>(
    JURISDICTIONS[0]
  );

  return (
    <div
      className={cn(
        "relative w-full h-full flex flex-col justify-between p-4 sm:p-5 select-none text-white",
        className
      )}
      role="region"
      aria-label="State Statutory Intelligence & Firewall Visualization"
    >
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
        <div>
          <span className="text-[10px] font-mono uppercase text-[#A3A3A3] tracking-wider block">
            Sub-National Architecture
          </span>
          <h3 className="text-xs font-semibold text-[#F4F4F4]">
            India Statutory Jurisdiction Map
          </h3>
        </div>
        <div className="px-2 py-0.5 rounded text-[9px] font-mono font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          5 JURISDICTIONS ACTIVE
        </div>
      </div>

      {/* Main Map & Schematic Layout */}
      <div className="relative w-full h-[180px] sm:h-[195px] my-1 flex items-center justify-between px-2">
        {/* Left Side: India Silhouette / Node Schematic */}
        <div className="relative w-[180px] sm:w-[210px] h-full flex items-center justify-center">
          <svg
            viewBox="120 20 180 220"
            className="w-full h-full"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Simplified Stylized India Geographic Contours */}
            <path
              d="M 210 35 L 235 45 L 260 65 L 270 95 L 255 125 L 245 155 L 225 195 L 205 230 L 180 200 L 165 170 L 155 130 L 175 90 L 195 55 Z"
              fill="rgba(255,255,255,0.02)"
              stroke="rgba(255,255,255,0.12)"
              strokeWidth="1.5"
              strokeDasharray="3 3"
            />

            {/* Connecting Rays from Central to States */}
            {JURISDICTIONS.slice(1).map((j) => (
              <line
                key={`line-${j.id}`}
                x1={JURISDICTIONS[0].x}
                y1={JURISDICTIONS[0].y}
                x2={j.x}
                y2={j.y}
                stroke="rgba(255,255,255,0.15)"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
            ))}

            {/* Jurisdiction Nodes on Map */}
            {JURISDICTIONS.map((j) => {
              const isSelected = selectedJurisdiction.id === j.id;
              const isCentral = j.tier === "CENTRAL";

              return (
                <g
                  key={`jur-${j.id}`}
                  transform={`translate(${j.x}, ${j.y})`}
                  onClick={() => setSelectedJurisdiction(j)}
                  className="cursor-pointer group"
                >
                  {/* Ping ring for Central */}
                  {isCentral && (
                    <circle r="14" fill="rgba(59, 130, 246, 0.2)" className="animate-pulse" />
                  )}

                  <circle
                    r={isSelected ? "11" : "8"}
                    fill={isCentral ? "#2563eb" : isSelected ? "#34d399" : "#181818"}
                    stroke={isSelected ? "#FFFFFF" : isCentral ? "#60a5fa" : "rgba(255,255,255,0.3)"}
                    strokeWidth={isSelected ? "2" : "1"}
                    className="transition-all duration-200"
                  />

                  <text
                    textAnchor="middle"
                    y="3"
                    fill={isSelected || isCentral ? "#FFFFFF" : "#A3A3A3"}
                    fontSize="7"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {j.code === "CENTRAL" ? "IN" : j.code}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Right Side: Interactive Jurisdiction Selector & Detail */}
        <div className="flex-1 pl-3 space-y-1.5 flex flex-col justify-center">
          <div className="flex flex-wrap gap-1">
            {JURISDICTIONS.map((j) => (
              <button
                key={j.id}
                type="button"
                onClick={() => setSelectedJurisdiction(j)}
                className={cn(
                  "px-2 py-1 rounded text-[10px] font-mono transition-colors border",
                  selectedJurisdiction.id === j.id
                    ? "bg-white text-black border-white font-bold"
                    : "bg-[#181818] text-[#A3A3A3] border-white/10 hover:border-white/30 hover:text-white"
                )}
              >
                {j.code}
              </button>
            ))}
          </div>

          <div className="p-2.5 rounded-lg glass-panel border border-white/[0.10] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white truncate max-w-[170px]">
                {selectedJurisdiction.name}
              </span>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded shrink-0">
                {selectedJurisdiction.actsCount} Acts
              </span>
            </div>
            <p className="text-[10.5px] text-[#A3A3A3] leading-relaxed line-clamp-2">
              {selectedJurisdiction.description}
            </p>
          </div>
        </div>
      </div>

      {/* Critical Zero-Stock-Prediction Firewall Banner */}
      <div className="p-3 rounded-xl glass-elevated border border-amber-500/40 text-amber-200 space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-amber-300">
            <span>🛡</span>
            <span>STATE PREDICTION FIREWALL GUARANTEE</span>
          </div>
          <span className="text-[9.5px] font-mono bg-amber-400/20 px-2 py-0.5 rounded border border-amber-400/30 text-amber-200 font-bold">
            0.00% LEAKAGE
          </span>
        </div>
        <p className="text-[11px] text-amber-200/90 leading-tight">
          Sub-national state legislation (AP, KA, KL, TS) is strictly firewalled. Zero speculative financial returns or equity predictions are ever generated for state acts.
        </p>
      </div>

      {/* Footer */}
      <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#666666] border-t border-white/[0.06]">
        <span>CENTRAL (47 EQUITIES) + 4 STATES (STATUTORY COMPLIANCE)</span>
        <span className="text-emerald-400">FIREWALL: ENFORCED</span>
      </div>
    </div>
  );
}

export default StateIntelligenceMapVisual;

