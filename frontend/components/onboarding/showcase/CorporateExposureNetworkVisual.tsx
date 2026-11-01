/**
 * components/onboarding/showcase/CorporateExposureNetworkVisual.tsx
 * ================================================================
 * TASK 1.15C — Stage 03: Corporate Exposure Network Visualization.
 *
 * Visual elements:
 * - Central legislative act node
 * - Sector hubs (Telecommunications, Digital Infra, Power Utilities)
 * - Corporate nodes (Bharti Airtel, Tata Comm, Vodafone Idea, Tata Power)
 * - Direct exposure vectors (solid emerald stroke) & indirect vectors (dashed amber stroke)
 * - Interactive node inspection on hover/click
 * - SVG progressive vector drawing and node pulse
 * - Illustrative demo mapping notice
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

interface ExposureNode {
  id: string;
  name: string;
  ticker: string;
  sector: string;
  type: "DIRECT" | "INDIRECT";
  clause: string;
  impactScore: string;
  x: number;
  y: number;
}

const NODES: ExposureNode[] = [
  {
    id: "bharti",
    name: "Bharti Airtel Ltd",
    ticker: "BHARTIARTL",
    sector: "Telecommunications",
    type: "DIRECT",
    clause: "Section 14: Spectrum Assignment & Right of Way",
    impactScore: "+0.84 High Exposure",
    x: 80,
    y: 50,
  },
  {
    id: "tatacomm",
    name: "Tata Communications",
    ticker: "TATACOMM",
    sector: "Digital Infra",
    type: "DIRECT",
    clause: "Section 22: Submarine Cable Landing & National Security",
    impactScore: "+0.68 Moderate Exposure",
    x: 420,
    y: 55,
  },
  {
    id: "tatapower",
    name: "Tata Power Co",
    ticker: "TATAPOWER",
    sector: "Power Utilities",
    type: "INDIRECT",
    clause: "Section 31: Shared Infrastructure & Right-of-Way Grid",
    impactScore: "+0.32 Indirect Exposure",
    x: 100,
    y: 190,
  },
  {
    id: "idea",
    name: "Vodafone Idea Ltd",
    ticker: "IDEA",
    sector: "Telecommunications",
    type: "DIRECT",
    clause: "Section 19: Regulatory Relief & Insolvency Frameworks",
    impactScore: "+0.76 High Exposure",
    x: 400,
    y: 185,
  },
];

export function CorporateExposureNetworkVisual({ className }: { className?: string }) {
  const [activeNode, setActiveNode] = useState<ExposureNode>(NODES[0]);

  // Center coordinate of Legislative Act
  const centerX = 250;
  const centerY = 120;

  return (
    <div
      className={cn(
        "relative w-full h-full flex flex-col justify-between p-4 sm:p-5 select-none text-white",
        className
      )}
      role="region"
      aria-label="Corporate Exposure Network Visualization"
    >
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
        <div>
          <span className="text-[10px] font-mono uppercase text-[#A3A3A3] tracking-wider block">
            Statutory Beta Mapping
          </span>
          <h3 className="text-xs font-semibold text-[#F4F4F4]">
            Legislative Corporate Exposure Graph
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-[9px] font-mono text-emerald-400">
            <span className="w-2 h-0.5 bg-emerald-400" /> DIRECT
          </span>
          <span className="flex items-center gap-1 text-[9px] font-mono text-amber-400">
            <span className="w-2 h-0.5 bg-amber-400 border-b border-dashed" /> INDIRECT
          </span>
        </div>
      </div>

      {/* SVG Interactive Network Canvas */}
      <div className="relative w-full h-[220px] sm:h-[240px] my-1 flex items-center justify-center overflow-hidden">
        <svg
          viewBox="0 0 500 240"
          className="w-full h-full"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Gradients */}
            <radialGradient id="hubGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Ambient Network Ring */}
          <circle
            cx={centerX}
            cy={centerY}
            r="110"
            fill="none"
            stroke="rgba(255,255,255,0.04)"
            strokeDasharray="4 4"
          />

          {/* Progressive Connecting Lines */}
          {NODES.map((node) => {
            const isSelected = activeNode.id === node.id;
            const isDirect = node.type === "DIRECT";

            return (
              <g key={`edge-${node.id}`}>
                <line
                  x1={centerX}
                  y1={centerY}
                  x2={node.x}
                  y2={node.y}
                  stroke={isDirect ? (isSelected ? "#34d399" : "#10b981") : isSelected ? "#fbbf24" : "#f59e0b"}
                  strokeWidth={isSelected ? "2.5" : "1.5"}
                  strokeDasharray={isDirect ? "none" : "5 4"}
                  strokeOpacity={isSelected ? 1 : 0.65}
                  className="transition-all duration-300"
                />
                {/* Mid-vector particle */}
                <circle
                  cx={(centerX + node.x) / 2}
                  cy={(centerY + node.y) / 2}
                  r="2"
                  fill={isDirect ? "#34d399" : "#fbbf24"}
                  opacity={isSelected ? "1" : "0.5"}
                />
              </g>
            );
          })}

          {/* Center Hub: Central Legislative Act */}
          <g transform={`translate(${centerX}, ${centerY})`}>
            <circle r="36" fill="url(#hubGlow)" />
            <circle
              r="26"
              fill="#181818"
              stroke="rgba(255,255,255,0.3)"
              strokeWidth="1.5"
              className="shadow-lg"
            />
            <text
              textAnchor="middle"
              y="-4"
              fill="#FFFFFF"
              fontSize="9"
              fontWeight="bold"
              fontFamily="monospace"
            >
              CENTRAL ACT
            </text>
            <text
              textAnchor="middle"
              y="8"
              fill="#A3A3A3"
              fontSize="7.5"
              fontFamily="monospace"
            >
              Act 44 / 2023
            </text>
          </g>

          {/* Corporate Entity Nodes */}
          {NODES.map((node) => {
            const isSelected = activeNode.id === node.id;
            const isDirect = node.type === "DIRECT";

            return (
              <g
                key={`node-${node.id}`}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => setActiveNode(node)}
                className="cursor-pointer group"
              >
                {/* Node Outer Glow on hover/active */}
                <circle
                  r={isSelected ? "24" : "18"}
                  fill={isSelected ? (isDirect ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)") : "transparent"}
                  className="transition-all duration-300"
                />

                {/* Node Core Circle */}
                <circle
                  r={isSelected ? "18" : "14"}
                  fill="#151515"
                  stroke={isSelected ? (isDirect ? "#34d399" : "#fbbf24") : "rgba(255,255,255,0.2)"}
                  strokeWidth={isSelected ? "2" : "1.2"}
                  className="transition-all duration-300 group-hover:stroke-white"
                />

                {/* Ticker Symbol inside node */}
                <text
                  textAnchor="middle"
                  y="3"
                  fill={isSelected ? "#FFFFFF" : "#A3A3A3"}
                  fontSize="7.5"
                  fontWeight="bold"
                  fontFamily="monospace"
                  className="group-hover:fill-white"
                >
                  {node.ticker.slice(0, 4)}
                </text>

                {/* Label below node */}
                <text
                  textAnchor="middle"
                  y="26"
                  fill={isSelected ? "#FFFFFF" : "#666666"}
                  fontSize="8"
                  fontWeight="500"
                  fontFamily="sans-serif"
                >
                  {node.ticker}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Entity Exposure Details Card */}
      <div className="p-2.5 sm:p-3 rounded-xl glass-panel border border-white/[0.10] flex items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-white">{activeNode.ticker}</span>
            <span className="text-[10px] text-[#A3A3A3]">({activeNode.name})</span>
            <span
              className={cn(
                "px-1.5 py-0.2 rounded text-[8.5px] font-mono font-semibold uppercase",
                activeNode.type === "DIRECT"
                  ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
              )}
            >
              {activeNode.type}
            </span>
          </div>
          <div className="text-[11px] text-[#A3A3A3] line-clamp-1">
            {activeNode.clause}
          </div>
        </div>

        <div className="text-right shrink-0">
          <span className="text-[9px] font-mono text-[#666666] block">EXPOSURE VECTOR</span>
          <span className="text-xs font-mono font-semibold text-emerald-400">
            {activeNode.impactScore}
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#666666] border-t border-white/[0.06]">
        <span>ILLUSTRATIVE DEMO NETWORK</span>
        <span>47 QUANT SECURITIES UNIVERSE</span>
      </div>
    </div>
  );
}

export default CorporateExposureNetworkVisual;

