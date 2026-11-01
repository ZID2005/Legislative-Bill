/**
 * components/onboarding/showcase/WatchlistIntelligenceVisual.tsx
 * =============================================================
 * TASK 1.15C — Stage 05: Priority Watchlist Intelligence Visualization.
 *
 * Visual elements:
 * - High-density institutional watchlist interface
 * - Monitored bill entries & listed company securities
 * - Live surveillance indicators and category chips
 * - Interactive tab switching between Statutory Measures and Listed Equities
 * - Grounded illustrative demo catalog data
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

interface WatchlistItem {
  id: string;
  symbolOrCode: string;
  title: string;
  category: string;
  jurisdiction: string;
  status: string;
  exposureTag: string;
  active: boolean;
}

const STATUTORY_ITEMS: WatchlistItem[] = [
  {
    id: "act-44",
    symbolOrCode: "ACT 44/2023",
    title: "The Telecommunications Act, 2023",
    category: "Spectrum & Networks",
    jurisdiction: "CENTRAL",
    status: "ENACTED",
    exposureTag: "Direct Statutory Mandate",
    active: true,
  },
  {
    id: "act-22",
    symbolOrCode: "ACT 22/2023",
    title: "Digital Personal Data Protection Act",
    category: "Privacy & Data",
    jurisdiction: "CENTRAL",
    status: "ENACTED",
    exposureTag: "Cross-Sector Compliance",
    active: true,
  },
  {
    id: "ka-elec",
    symbolOrCode: "KA ACT 14",
    title: "Karnataka Electricity Reform Amendment",
    category: "Power & Grid",
    jurisdiction: "KARNATAKA",
    status: "GAZETTED",
    exposureTag: "Sub-National Utility Scope",
    active: true,
  },
];

const EQUITY_ITEMS: WatchlistItem[] = [
  {
    id: "bhartiartl",
    symbolOrCode: "BHARTIARTL",
    title: "Bharti Airtel Limited",
    category: "Telecommunications",
    jurisdiction: "NSE / BSE",
    status: "QUANT ACTIVE",
    exposureTag: "High Direct Beta (+0.84)",
    active: true,
  },
  {
    id: "hdfcbank",
    symbolOrCode: "HDFCBANK",
    title: "HDFC Bank Limited",
    category: "Banking & Financials",
    jurisdiction: "NSE / BSE",
    status: "QUANT ACTIVE",
    exposureTag: "Regulatory Capital Rules",
    active: true,
  },
  {
    id: "tatapower",
    symbolOrCode: "TATAPOWER",
    title: "Tata Power Company Limited",
    category: "Power Utilities",
    jurisdiction: "NSE / BSE",
    status: "QUANT ACTIVE",
    exposureTag: "Clean Energy Grid Expansion",
    active: true,
  },
];

export function WatchlistIntelligenceVisual({ className }: { className?: string }) {
  const [activeTab, setActiveTab] = useState<"BILLS" | "EQUITIES">("BILLS");
  const items = activeTab === "BILLS" ? STATUTORY_ITEMS : EQUITY_ITEMS;

  return (
    <div
      className={cn(
        "relative w-full h-full flex flex-col justify-between p-4 sm:p-5 select-none text-white",
        className
      )}
      role="region"
      aria-label="Priority Watchlist Intelligence Visualization"
    >
      {/* Top Header & Tab Controls */}
      <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
        <div>
          <span className="text-[10px] font-mono uppercase text-[#A3A3A3] tracking-wider block">
            Surveillance Architecture
          </span>
          <h3 className="text-xs font-semibold text-[#F4F4F4]">
            Priority Regulatory Watchlists
          </h3>
        </div>

        {/* Segmented Tab Switcher */}
        <div className="flex p-0.5 rounded-lg glass-elevated border border-white/10">
          <button
            type="button"
            onClick={() => setActiveTab("BILLS")}
            className={cn(
              "px-2.5 py-1 rounded text-[10px] font-mono font-medium transition-colors",
              activeTab === "BILLS"
                ? "bg-white text-black font-bold shadow-xs"
                : "text-[#A3A3A3] hover:text-white"
            )}
          >
            Statutory Acts
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("EQUITIES")}
            className={cn(
              "px-2.5 py-1 rounded text-[10px] font-mono font-medium transition-colors",
              activeTab === "EQUITIES"
                ? "bg-white text-black font-bold shadow-xs"
                : "text-[#A3A3A3] hover:text-white"
            )}
          >
            Quant Equities
          </button>
        </div>
      </div>

      {/* Watchlist Stream Items */}
      <div className="space-y-2 my-2 sm:my-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="p-3 rounded-xl glass-panel border border-white/[0.10] hover:border-white/20 transition-all flex items-center justify-between gap-3 group"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-white group-hover:text-emerald-300 transition-colors">
                  {item.symbolOrCode}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/[0.06] text-[#A3A3A3]">
                  {item.jurisdiction}
                </span>
                <span className="text-[10px] text-emerald-400 font-mono">
                  {item.status}
                </span>
              </div>
              <div className="text-xs text-[#F4F4F4] font-medium leading-tight">
                {item.title}
              </div>
              <div className="text-[10px] text-[#A3A3A3]">
                {item.exposureTag}
              </div>
            </div>

            <div className="flex flex-col items-end gap-1.5 shrink-0">
              <span className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                SURVEILLANCE ACTIVE
              </span>
              <span className="text-[9px] font-mono text-[#666666]">
                {item.category}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Watchlist Telemetry Metrics Bar */}
      <div className="p-2.5 rounded-xl bg-[#161616] border border-white/[0.08] flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-[#666666]">FILTER:</span>
          <span className="text-white font-semibold">
            {activeTab === "BILLS" ? "CENTRAL + 4 STATES" : "47 QUANT SECURITIES"}
          </span>
        </div>
        <div className="text-emerald-400 font-medium">
          AUTO-INGESTION: ACTIVE
        </div>
      </div>

      {/* Footer */}
      <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#666666] border-t border-white/[0.06]">
        <span>APPROVED SEANCE CATALOG ENTRIES</span>
        <span>ZERO MANUAL RE-INDEXING</span>
      </div>
    </div>
  );
}

export default WatchlistIntelligenceVisual;

