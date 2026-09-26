/**
 * components/firewalls/StatePredictionFirewall.tsx
 * =================================================
 * Renders when a State bill's predictions are requested.
 *
 * CRITICAL: This component must NEVER show:
 *   - predicted return
 *   - abnormal return forecast
 *   - buy/sell signal
 *   - confidence prediction
 *   - market direction prediction
 *
 * It communicates available capabilities clearly without presenting
 * the absence as an error.
 */

import React from "react";
import { cn } from "@/lib/utils";
import type { BillPredictionStatusResponse } from "@/types/api";

export interface StatePredictionFirewallProps {
  state?: string | null;
  bill?: { title?: string; state?: string | null };
  predictionStatus?: BillPredictionStatusResponse | null;
  className?: string;
}

export function StatePredictionFirewall({
  state,
  bill,
  predictionStatus,
  className,
}: StatePredictionFirewallProps) {
  const stateName = state ?? bill?.state ?? "State";

  return (
    <section
      className={cn(
        "rounded-lg border border-slate-700 bg-slate-900 p-6",
        className
      )}
      aria-label="State prediction status"
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-5">
        <div
          className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-900/40 border border-blue-700/40"
          aria-hidden="true"
        >
          <span className="text-base">🗺</span>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Market prediction is not currently available for State legislation
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {stateName} Assembly — Level 2 Legislative Intelligence
          </p>
        </div>
      </div>

      {/* Explanation */}
      <p className="text-sm text-slate-400 mb-5 leading-relaxed">
        State bills are governed by a strict statutory and econometric boundary:
        they are not processed through Central Parliamentary stock market models.
        Quantitative return predictions, abnormal return forecasts, and buy/sell signals
        remain strictly <span className="text-slate-300 font-medium">zero</span> for all State legislation.
        This is a deliberate research integrity constraint, not a system limitation.
      </p>

      {/* Available capabilities */}
      <div className="rounded-md border border-slate-800 bg-slate-800/40 p-4 mb-4">
        <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Available for this State bill
        </p>
        <ul className="space-y-2" role="list">
          {[
            {
              icon: "📜",
              label: "Legislative Intelligence",
              desc: "Full text, provisions, assembly records, and official source documents",
            },
            {
              icon: "📊",
              label: "Economic Impact Analysis",
              desc: "Sector-level economic mechanisms, policy domain classification, and regulatory context",
            },
            {
              icon: "🏢",
              label: "Corporate Exposure",
              desc: "Evidence-backed corporate exposure records with business activity mapping",
            },
            {
              icon: "📈",
              label: "Market Relevance Classification",
              desc: "Qualitative HIGH / MEDIUM / LOW / NONE relevance scoring",
            },
          ].map(({ icon, label, desc }) => (
            <li key={label} className="flex items-start gap-2">
              <span className="text-sm mt-0.5 flex-shrink-0" aria-hidden="true">
                {icon}
              </span>
              <div>
                <span className="text-xs font-medium text-slate-300">{label}</span>
                <p className="text-xs text-slate-500">{desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Explicitly not available */}
      <div className="rounded-md border border-rose-900/40 bg-rose-950/20 p-3">
        <p className="text-xs font-medium text-rose-400 mb-1.5">
          Not available for State legislation
        </p>
        <ul className="space-y-1 text-xs text-slate-500">
          {[
            "Predicted stock return / abnormal return forecast",
            "Market direction prediction (Bullish / Bearish)",
            "Buy / Sell / Hold signal",
            "Confidence score / model probability",
            "Event window analysis",
          ].map((item) => (
            <li key={item} className="flex items-center gap-1.5">
              <span className="text-rose-700" aria-hidden="true">✕</span>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* Backend message if available */}
      {predictionStatus?.message && (
        <p className="mt-3 text-xs text-slate-600 italic">
          System note: {predictionStatus.message}
        </p>
      )}
    </section>
  );
}

export default StatePredictionFirewall;
