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
        <h2 id="market-intelligence-heading" className="text-lg font-semibold text-[var(--text-primary)]">
          Central Market Intelligence
        </h2>
        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] p-6 space-y-4">
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
          <h2 id="market-intelligence-heading" className="text-lg font-semibold text-[var(--text-primary)]">
            Central Market Intelligence
          </h2>
          <p className="text-xs text-[var(--text-secondary)]">
            Empirical econometric projections for member quantitative securities across 5 event horizons
          </p>
        </div>

        {/* Deep Links */}
        <div className="flex items-center gap-2 text-xs">
          <Link
            href="/predictions"
            className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-elevated)] px-2.5 py-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
          >
            All Predictions →
          </Link>
          <Link
            href="/risk"
            className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-elevated)] px-2.5 py-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
          >
            Risk Matrix →
          </Link>
          <Link
            href="/anticipation"
            className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-elevated)] px-2.5 py-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
          >
            Anticipation →
          </Link>
        </div>
      </div>

      {/* Explicit Architecture & Integrity Notice */}
      <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-4 text-xs text-amber-200 flex items-start gap-2.5">
        <span className="text-base mt-0.5" aria-hidden="true">ℹ</span>
        <div>
          <p className="font-semibold text-amber-300">Methodology &amp; Model Scope Notice</p>
          <p className="mt-0.5 text-[var(--text-secondary)] leading-relaxed">
            {intel.notice} Econometric models evaluate individual listed securities against specific Parliamentary acts.
            Outputs represent historical research projections, NOT investment advice or Buy/Sell/Hold recommendations.
          </p>
        </div>
      </div>

      {/* Metric Breakdown Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] p-3.5">
          <span className="text-[11px] font-medium text-[var(--text-secondary)] uppercase tracking-wider">Total Model Records</span>
          <p className="mt-1 text-xl font-bold font-tabular font-mono text-[var(--text-primary)]">{intel.total_predictions ?? 0}</p>
          <span className="text-[10px] text-[var(--text-muted)]">Across 5 event horizons</span>
        </div>

        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] p-3.5">
          <span className="text-[11px] font-medium text-[var(--text-secondary)] uppercase tracking-wider">Positive Direction</span>
          <p className="mt-1 text-xl font-bold font-tabular font-mono text-[var(--color-positive)] flex items-center gap-1">
            <span aria-hidden="true" className="text-sm">▲</span>
            <span>{intel.positive_count ?? 0}</span>
          </p>
          <span className="text-[10px] text-[var(--text-muted)]">Predicted abnormal return &gt; 0</span>
        </div>

        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] p-3.5">
          <span className="text-[11px] font-medium text-[var(--text-secondary)] uppercase tracking-wider">Negative Direction</span>
          <p className="mt-1 text-xl font-bold font-tabular font-mono text-[var(--color-negative)] flex items-center gap-1">
            <span aria-hidden="true" className="text-sm">▼</span>
            <span>{intel.negative_count ?? 0}</span>
          </p>
          <span className="text-[10px] text-[var(--text-muted)]">Predicted abnormal return &lt; 0</span>
        </div>

        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] p-3.5">
          <span className="text-[11px] font-medium text-[var(--text-secondary)] uppercase tracking-wider">Neutral / Absorption</span>
          <p className="mt-1 text-xl font-bold font-tabular font-mono text-[var(--text-secondary)] flex items-center gap-1">
            <span aria-hidden="true" className="text-sm">◆</span>
            <span>{intel.neutral_count ?? 0}</span>
          </p>
          <span className="text-[10px] text-[var(--text-muted)]">Within statistical noise bounds</span>
        </div>
      </div>

      {/* Member Predictions Sample Table */}
      {samplePreds.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)]">
          <table className="financial-table w-full text-left text-xs text-[var(--text-secondary)]">
            <thead className="bg-[var(--bg-surface-elevated)] text-[11px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider border-b border-[var(--border-default)]">
              <tr>
                <th scope="col" className="px-4 py-2.5">Target Security</th>
                <th scope="col" className="px-4 py-2.5 font-tabular">Event Horizon</th>
                <th scope="col" className="px-4 py-2.5">Predicted Direction</th>
                <th scope="col" className="px-4 py-2.5">Confidence</th>
                <th scope="col" className="px-4 py-2.5">Impact Strength</th>
                <th scope="col" className="px-4 py-2.5 text-right">Dossier Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-default)]">
              {samplePreds.map((p) => (
                <tr key={p.prediction_id} className="hover:bg-[var(--bg-surface-elevated)]/60 transition-colors">
                  <td className="px-4 py-2.5">
                    <span className="font-semibold text-[var(--text-primary)] font-mono">{p.company_isin}</span>
                    <span className="block text-[10px] text-[var(--text-muted)] truncate max-w-[180px]">{p.bill_id}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="rounded bg-[var(--bg-surface-elevated)] px-1.5 py-0.5 font-mono font-tabular text-[11px] text-[var(--text-secondary)] border border-[var(--border-default)]">
                      {p.event_window}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <PredictionBadge direction={p.predicted_direction} size="xs" />
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-[var(--text-primary)] font-medium font-tabular">{p.predicted_confidence}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-[var(--text-secondary)]">{p.impact_strength}</span>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <Link
                      href={`/predictions/${encodeURIComponent(p.prediction_id)}`}
                      className="rounded bg-[var(--bg-surface-elevated)] px-2 py-1 text-[11px] text-[var(--text-secondary)] hover:bg-[var(--action-primary)] hover:text-white transition-colors border border-[var(--border-default)]"
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
