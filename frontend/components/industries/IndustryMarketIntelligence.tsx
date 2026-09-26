/**
 * components/industries/IndustryMarketIntelligence.tsx
 * ===================================================
 * Central Market Intelligence projections for quantitative industries or Intelligence Firewall for qualitative industries.
 */

import React from "react";
import Link from "next/link";
import { PredictionBadge } from "@/components/ui/Badge";
import { IntelligenceCompanyFirewall } from "@/components/firewalls/IntelligenceCompanyFirewall";
import type { IndustryDossierResponse } from "@/types/api";

export interface IndustryMarketIntelligenceProps {
  dossier: IndustryDossierResponse;
}

export function IndustryMarketIntelligence({ dossier }: IndustryMarketIntelligenceProps) {
  const isModeled = dossier.market_intelligence.modeled;

  if (!isModeled) {
    return (
      <section aria-labelledby="market-intelligence-heading" className="space-y-4">
        <h2 id="market-intelligence-heading" className="text-lg font-semibold text-white">
          Central Market Intelligence
        </h2>
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 space-y-4">
          <IntelligenceCompanyFirewall
            company={{
              company_id: dossier.industry_id,
              company_name: dossier.name,
              entity_type: "industry sector aggregate",
              universe_type: "intelligence",
              total_exposures: dossier.central_exposures_count + dossier.state_exposures_count,
              operating_states: [],
              mechanisms: dossier.active_mechanisms,
            } as any}
            predictionStatus={{
              is_modeled: false,
              message: "Industry-level prediction is not modeled. Member corporate intelligence profiles are available.",
            } as any}
          />
        </div>
      </section>
    );
  }

  const intel = dossier.market_intelligence;
  const samplePreds = intel.sample_predictions || [];

  return (
    <section aria-labelledby="market-intelligence-heading" className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 id="market-intelligence-heading" className="text-lg font-semibold text-white">
            Central Market Intelligence
          </h2>
          <p className="text-xs text-slate-400">
            Empirical econometric projections for member quantitative securities across 5 event horizons
          </p>
        </div>

        {/* Deep Links */}
        <div className="flex items-center gap-2 text-xs">
          <Link
            href="/predictions"
            className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-slate-300 hover:text-white hover:border-slate-600 transition-colors"
          >
            All Predictions →
          </Link>
          <Link
            href="/risk"
            className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-slate-300 hover:text-white hover:border-slate-600 transition-colors"
          >
            Risk Matrix →
          </Link>
          <Link
            href="/anticipation"
            className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-slate-300 hover:text-white hover:border-slate-600 transition-colors"
          >
            Anticipation →
          </Link>
        </div>
      </div>

      {/* Explicit Architecture & Integrity Notice */}
      <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-4 text-xs text-amber-200 flex items-start gap-2.5">
        <span className="text-base mt-0.5">ℹ</span>
        <div>
          <p className="font-semibold text-amber-300">Methodology & Model Scope Notice</p>
          <p className="mt-0.5 text-slate-400 leading-relaxed">
            {intel.notice} Econometric models evaluate individual listed securities against specific Parliamentary acts.
            Outputs represent historical research projections, NOT investment advice or Buy/Sell/Hold recommendations.
          </p>
        </div>
      </div>

      {/* Metric Breakdown Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-3.5">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Total Model Records</span>
          <p className="mt-1 text-xl font-bold text-white">{intel.total_predictions ?? 0}</p>
          <span className="text-[10px] text-slate-500">Across 5 event horizons</span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900 p-3.5">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Positive Direction</span>
          <p className="mt-1 text-xl font-bold text-emerald-400">{intel.positive_count ?? 0}</p>
          <span className="text-[10px] text-slate-500">Predicted abnormal return &gt; 0</span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900 p-3.5">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Negative Direction</span>
          <p className="mt-1 text-xl font-bold text-rose-400">{intel.negative_count ?? 0}</p>
          <span className="text-[10px] text-slate-500">Predicted abnormal return &lt; 0</span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900 p-3.5">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Neutral / Absorption</span>
          <p className="mt-1 text-xl font-bold text-slate-300">{intel.neutral_count ?? 0}</p>
          <span className="text-[10px] text-slate-500">Within statistical noise bounds</span>
        </div>
      </div>

      {/* Member Predictions Sample Table */}
      {samplePreds.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/60">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th scope="col" className="px-4 py-2.5">Target Security</th>
                <th scope="col" className="px-4 py-2.5">Event Horizon</th>
                <th scope="col" className="px-4 py-2.5">Predicted Direction</th>
                <th scope="col" className="px-4 py-2.5">Confidence</th>
                <th scope="col" className="px-4 py-2.5">Impact Strength</th>
                <th scope="col" className="px-4 py-2.5 text-right">Dossier Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {samplePreds.map((p) => (
                <tr key={p.prediction_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-2.5">
                    <span className="font-semibold text-white">{p.company_isin}</span>
                    <span className="block text-[10px] text-slate-400 truncate max-w-[180px]">{p.bill_id}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] text-slate-300">
                      {p.event_window}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <PredictionBadge direction={p.predicted_direction} size="xs" />
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-slate-300 font-medium">{p.predicted_confidence}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-slate-400">{p.impact_strength}</span>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <Link
                      href={`/predictions/${encodeURIComponent(p.prediction_id)}`}
                      className="rounded bg-slate-800 px-2 py-1 text-[11px] text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                    >
                      Prediction →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default IndustryMarketIntelligence;
