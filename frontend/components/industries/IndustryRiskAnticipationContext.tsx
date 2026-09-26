/**
 * components/industries/IndustryRiskAnticipationContext.tsx
 * ========================================================
 * Summarizes derived institutional risk profiles and pre-event information diffusion metrics for the industry.
 */

import React from "react";
import Link from "next/link";
import { SourceBadge } from "@/components/ui/Badge";
import type { IndustryAnticipationSummary, IndustryRiskSummary } from "@/types/api";

export interface IndustryRiskAnticipationContextProps {
  riskSummary: IndustryRiskSummary;
  anticipationSummary: IndustryAnticipationSummary;
}

export function IndustryRiskAnticipationContext({
  riskSummary,
  anticipationSummary,
}: IndustryRiskAnticipationContextProps) {
  const riskDist = riskSummary.risk_band_distribution || {};
  const antDist = anticipationSummary.diffusion_tier_distribution || {};

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Risk Context Card */}
      <section aria-labelledby="industry-risk-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 id="industry-risk-heading" className="text-lg font-semibold text-white">
              Industry Risk Context
            </h2>
            <SourceBadge type="DERIVED" size="xs" />
          </div>
          <Link href="/risk" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
            Risk Dashboard →
          </Link>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-5 space-y-4">
          <p className="text-xs text-slate-400 italic">
            {riskSummary.explanation}
          </p>

          <div className="grid grid-cols-5 gap-2 pt-1">
            {[
              { label: "VERY LOW", key: "VERY_LOW", color: "text-emerald-400", bg: "bg-emerald-950/40 border-emerald-800/40" },
              { label: "LOW", key: "LOW", color: "text-blue-400", bg: "bg-blue-950/40 border-blue-800/40" },
              { label: "MODERATE", key: "MODERATE", color: "text-amber-400", bg: "bg-amber-950/40 border-amber-800/40" },
              { label: "HIGH", key: "HIGH", color: "text-orange-400", bg: "bg-orange-950/40 border-orange-800/40" },
              { label: "VERY HIGH", key: "VERY_HIGH", color: "text-rose-400", bg: "bg-rose-950/40 border-rose-800/40" },
            ].map((band) => (
              <div key={band.key} className={`rounded-lg border p-2.5 text-center ${band.bg}`}>
                <span className="text-[10px] font-semibold tracking-wider text-slate-400 block truncate">
                  {band.label}
                </span>
                <p className={`mt-1 text-base font-bold ${band.color}`}>
                  {riskDist[band.key] ?? 0}
                </p>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
            <span className="text-slate-400">High / Very-High Risk Exposure Evaluations:</span>
            <span className="font-semibold text-rose-300">
              {riskSummary.high_risk_count} records
            </span>
          </div>
        </div>
      </section>

      {/* Anticipation Context Card */}
      <section aria-labelledby="industry-anticipation-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 id="industry-anticipation-heading" className="text-lg font-semibold text-white">
              Pre-Event Information Diffusion
            </h2>
            <SourceBadge type="DERIVED" size="xs" />
          </div>
          <Link href="/anticipation" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
            Anticipation Explorer →
          </Link>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-5 space-y-4">
          {/* Mandatory Verbatim Legal Disclaimer */}
          <div className="rounded border border-slate-700/50 bg-slate-800/40 p-2.5 text-[11px] text-slate-300 leading-relaxed italic">
            "{anticipationSummary.verbatim_disclaimer}"
          </div>

          <div className="grid grid-cols-4 gap-2 pt-1">
            {[
              { label: "NO EVIDENCE", key: "NO_EVIDENCE", color: "text-slate-400", bg: "bg-slate-800/40 border-slate-700" },
              { label: "WEAK", key: "WEAK_EVIDENCE", color: "text-blue-400", bg: "bg-blue-950/40 border-blue-800/40" },
              { label: "MODERATE", key: "MODERATE_EVIDENCE", color: "text-amber-400", bg: "bg-amber-950/40 border-amber-800/40" },
              { label: "STRONG", key: "STRONG_EVIDENCE", color: "text-purple-400", bg: "bg-purple-950/40 border-purple-800/40" },
            ].map((tier) => (
              <div key={tier.key} className={`rounded-lg border p-2.5 text-center ${tier.bg}`}>
                <span className="text-[10px] font-semibold tracking-wider text-slate-400 block truncate">
                  {tier.label}
                </span>
                <p className={`mt-1 text-base font-bold ${tier.color}`}>
                  {antDist[tier.key] ?? 0}
                </p>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
            <span className="text-slate-400">Pre-Event Detected Public Signals:</span>
            <span className="font-semibold text-purple-300">
              {anticipationSummary.flagged_pairs_count} flagged pairs
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default IndustryRiskAnticipationContext;
