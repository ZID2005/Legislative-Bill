/**
 * components/firewalls/StatePredictionFirewall.tsx
 * =================================================
 * Renders when a State bill's predictions are requested.
 *
 * CRITICAL STATUTORY FIREWALL: This component must NEVER show:
 *   - predicted return
 *   - abnormal return forecast
 *   - buy/sell signal
 *   - confidence prediction
 *   - market direction prediction
 *
 * It communicates available capabilities clearly without presenting
 * the absence as an error.
 * Dual-theme synchronized for Seance.
 */

import React from "react";
import { cn } from "@/lib/utils";
import type { BillPredictionStatusResponse } from "@/types/api";

export interface StatePredictionFirewallProps {
  state?: string | null;
  bill?: { title?: string; state?: string | null };
  billId?: string;
  billTitle?: string;
  predictionStatus?: BillPredictionStatusResponse | null;
  className?: string;
}

export function StatePredictionFirewall({
  state,
  bill,
  billId,
  billTitle,
  predictionStatus,
  className,
}: StatePredictionFirewallProps) {
  const stateName = state ?? bill?.state ?? "State";

  return (
    <section
      className={cn(
        "rounded-2xl border border-[var(--border-default)] bg-[var(--bg-card)] p-6 shadow-xs transition-colors",
        className
      )}
      role="region"
      aria-label="State prediction status"
    >
      {/* Header */}
      <div className="flex items-start gap-3.5 mb-5">
        <div
          className="mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-[var(--color-info-bg)] border border-[var(--color-info-border)] text-[var(--color-info)]"
          aria-hidden="true"
        >
          <span className="text-base">🗺</span>
        </div>
        <div>
          <h3 className="text-sm font-bold text-[var(--text-primary)] tracking-tight">
            Market prediction is not currently available for State legislation
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            {stateName} Assembly — Level 2 Legislative Intelligence
          </p>
        </div>
      </div>

      {/* Explanation */}
      <p className="text-sm text-[var(--text-secondary)] mb-5 leading-relaxed">
        State bills are governed by a strict statutory and econometric boundary:
        they are not processed through Central Parliamentary stock market models.
        Quantitative return predictions, abnormal return forecasts, and buy/sell signals
        remain strictly <span className="text-[var(--text-primary)] font-semibold">zero</span> for all State legislation.
        This is a deliberate research integrity constraint, not a system limitation.
      </p>

      {/* Available capabilities */}
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)]/50 p-4 mb-4">
        <p className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider mb-3">
          Available for this State bill
        </p>
        <ul className="space-y-2.5" role="list">
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
            <li key={label} className="flex items-start gap-2.5">
              <span className="text-sm mt-0.5 flex-shrink-0" aria-hidden="true">
                {icon}
              </span>
              <div>
                <span className="text-xs font-semibold text-[var(--text-primary)]">{label}</span>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">{desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Explicitly not available */}
      <div className="rounded-xl border border-[var(--color-danger-border)] bg-[var(--color-danger-bg)] p-4">
        <p className="text-xs font-semibold text-[var(--color-danger)] mb-2">
          Not available for State legislation
        </p>
        <ul className="space-y-1.5 text-xs text-[var(--text-muted)]">
          {[
            "Predicted stock return / abnormal return forecast",
            "Market direction prediction (Bullish / Bearish)",
            "Buy / Sell / Hold signal",
            "Confidence score / model probability",
            "Event window analysis",
          ].map((item) => (
            <li key={item} className="flex items-center gap-2">
              <span className="text-[var(--color-danger)] font-bold" aria-hidden="true">✕</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Backend message if available */}
      {predictionStatus?.message && (
        <p className="mt-3.5 text-xs text-[var(--text-muted)] italic">
          System note: {predictionStatus.message}
        </p>
      )}
    </section>
  );
}

export default StatePredictionFirewall;
