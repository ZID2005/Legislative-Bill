/**
 * components/industries/EconomicTransmissionMap.tsx
 * ==================================================
 * Visual representation of the economic transmission chain:
 * LEGISLATION → POLICY CHANGE → ECONOMIC MECHANISM → INDUSTRY → COMPANY EXPOSURE → MARKET ANALYSIS
 */

import React, { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import type { TransmissionChainNode } from "@/types/api";

export interface EconomicTransmissionMapProps {
  transmissionChains: TransmissionChainNode[][];
  activeMechanisms: string[];
}

export function EconomicTransmissionMap({
  transmissionChains,
  activeMechanisms,
}: EconomicTransmissionMapProps) {
  const [selectedChainIdx, setSelectedChainIdx] = useState(0);

  if (!transmissionChains || transmissionChains.length === 0) {
    return (
      <section aria-labelledby="transmission-map-heading" className="space-y-4">
        <h2 id="transmission-map-heading" className="text-lg font-semibold text-white">
          Economic Transmission Map
        </h2>
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 text-center text-xs text-slate-400">
          No active transmission chains documented for this industry.
        </div>
      </section>
    );
  }

  const currentChain = transmissionChains[selectedChainIdx] || transmissionChains[0];

  return (
    <section aria-labelledby="transmission-map-heading" className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 id="transmission-map-heading" className="text-lg font-semibold text-white">
            Economic Transmission Map
          </h2>
          <p className="text-xs text-slate-400">
            Traced statutory transmission channels connecting legislative intervention to market outcomes
          </p>
        </div>

        {/* Mechanism filter pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-slate-500 font-medium">Active Channels:</span>
          {activeMechanisms.map((mech) => (
            <span
              key={mech}
              className="rounded bg-slate-800 border border-slate-700 px-2 py-0.5 text-[10px] font-medium text-slate-300 capitalize"
            >
              {mech.replace("_", " ")}
            </span>
          ))}
        </div>
      </div>

      {/* Chain Selector Tabs if multiple */}
      {transmissionChains.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-400 flex-shrink-0 text-[11px]">Select Pathway:</span>
          {transmissionChains.map((chain, idx) => {
            const billTitle = chain.find((c) => c.stage === "LEGISLATION")?.title || `Pathway ${idx + 1}`;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedChainIdx(idx)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedChainIdx === idx
                    ? "bg-blue-900/60 text-blue-200 border border-blue-700/50"
                    : "bg-slate-800/80 text-slate-400 hover:text-slate-200 border border-slate-700"
                }`}
              >
                {billTitle.slice(0, 24)}...
              </button>
            );
          })}
        </div>
      )}

      {/* Visual Flow Container */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-3 relative">
          {currentChain.map((node, idx) => {
            const isLast = idx === currentChain.length - 1;
            const stageLabels: Record<string, { label: string; color: string; icon: string }> = {
              LEGISLATION: { label: "1. Legislation", color: "border-amber-700/50 bg-amber-950/20 text-amber-300", icon: "📜" },
              POLICY_CHANGE: { label: "2. Policy Change", color: "border-sky-700/50 bg-sky-950/20 text-sky-300", icon: "⚖️" },
              ECONOMIC_MECHANISM: { label: "3. Economic Mechanism", color: "border-purple-700/50 bg-purple-950/20 text-purple-300", icon: "⚙️" },
              INDUSTRY: { label: "4. Industry Impact", color: "border-indigo-700/50 bg-indigo-950/20 text-indigo-300", icon: "🏭" },
              COMPANY_EXPOSURE: { label: "5. Corporate Exposure", color: "border-blue-700/50 bg-blue-950/20 text-blue-300", icon: "🏢" },
              MARKET_ANALYSIS: { label: "6. Market Analytics", color: "border-emerald-700/50 bg-emerald-950/20 text-emerald-300", icon: "📈" },
            };

            const stageMeta = stageLabels[node.stage] || { label: node.stage, color: "border-slate-700 bg-slate-800 text-slate-300", icon: "•" };

            return (
              <div key={idx} className="flex flex-col relative">
                <div className={`flex-1 rounded-lg border p-3.5 ${stageMeta.color} flex flex-col justify-between`}>
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1.5">
                      <span className="text-[10px] font-bold tracking-wider uppercase opacity-90">
                        {stageMeta.icon} {stageMeta.label}
                      </span>
                      {node.badge && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-black/40 border border-white/10 uppercase">
                          {node.badge}
                        </span>
                      )}
                    </div>
                    <h4 className="text-xs font-semibold text-white mt-1 leading-snug line-clamp-2">
                      {node.title}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                      {node.description}
                    </p>
                  </div>

                  {node.stage === "MARKET_ANALYSIS" && (
                    <div className="mt-3 pt-2 border-t border-white/10 text-[10px]">
                      {node.status === "MODELLED" ? (
                        <span className="text-emerald-300 font-medium">✓ Empirical Model Active</span>
                      ) : (
                        <span className="text-slate-400 italic">Quantitative Firewall (0 predictions)</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Arrow to next stage on desktop */}
                {!isLast && (
                  <div className="hidden md:flex absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-slate-500 text-xs">
                    ▶
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default EconomicTransmissionMap;
