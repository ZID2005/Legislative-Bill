/**
 * components/portfolio/PortfolioImpactReport.tsx
 * ===============================================
 * Executive Legislative Impact Report view for print / PDF generation.
 *
 * Implements:
 * - Scoped statutory exposure summary across user's authorized holdings
 * - High-density tabular layout with print-optimized styles
 * - Window print trigger (window.print())
 * - Immutable epistemic disclaimers and methodology boundaries
 */

"use client";

import React from "react";
import type { PersonalizedImpactReportResponse } from "@/types/api";

export interface PortfolioImpactReportProps {
  reportData: PersonalizedImpactReportResponse;
  onBackToWorkspace: () => void;
}

export function PortfolioImpactReport({
  reportData,
  onBackToWorkspace,
}: PortfolioImpactReportProps) {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Report Header Card */}
      <div className="p-6 rounded-xl bg-[var(--bg-card)] border border-[var(--border-default)] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[var(--border-default)]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] uppercase font-bold tracking-widest text-blue-600 dark:text-blue-400 font-mono">
                Executive Intelligence Briefing
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25">
                Verified
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)] font-headline">
              {reportData.report_title}
            </h2>
            <p className="text-xs text-[var(--text-muted)] mt-1 font-mono">
              Generated: {reportData.generated_at} • Scoped strictly to your authorized holdings
            </p>
          </div>

          <div className="flex items-center gap-2.5 print:hidden">
            <button
              type="button"
              onClick={onBackToWorkspace}
              className="px-3.5 py-1.5 rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-xs font-semibold text-[var(--text-secondary)] border border-[var(--border-default)] transition-colors"
            >
              ← Back to Workspace
            </button>
            <button
              type="button"
              onClick={() => window.print()}
              className="px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-xs transition-colors"
            >
              Print / Save PDF
            </button>
          </div>
        </div>

        {/* Section 1: Portfolio Summary */}
        <div className="space-y-2.5">
          <h3 className="text-xs uppercase font-bold text-blue-600 dark:text-blue-400 tracking-wider font-headline">
            1. Portfolio Exposure Summary
          </h3>
          <div className="p-4 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Total Holdings</span>
              <strong className="text-base font-bold font-tabular text-[var(--text-primary)]">
                {reportData.portfolio_summary.total_holdings}
              </strong>
            </div>
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Exposed Holdings</span>
              <strong className="text-base font-bold font-tabular text-emerald-600 dark:text-emerald-400">
                {reportData.portfolio_summary.exposed_holdings_count}
              </strong>
            </div>
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Relevant Measures</span>
              <strong className="text-base font-bold font-tabular text-blue-600 dark:text-blue-400">
                {reportData.portfolio_summary.total_relevant_bills}
              </strong>
            </div>
            <div>
              <span className="text-[var(--text-muted)] block text-[11px]">Direct Statutory Ties</span>
              <strong className="text-base font-bold font-tabular text-rose-600 dark:text-rose-400">
                {reportData.portfolio_summary.direct_bills_count}
              </strong>
            </div>
          </div>
        </div>

        {/* Section 2: Relevant Legislation Table */}
        <div className="space-y-2.5 pt-2">
          <h3 className="text-xs uppercase font-bold text-blue-600 dark:text-blue-400 tracking-wider font-headline">
            2. Correlated Legislative Measures &amp; Linkage Reasons
          </h3>
          <div className="rounded-lg border border-[var(--border-default)] overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--bg-base)] text-[var(--text-muted)] font-semibold border-b border-[var(--border-default)]">
                <tr>
                  <th className="p-3">Legislative Measure</th>
                  <th className="p-3">Jurisdiction</th>
                  <th className="p-3">Relevance Tier</th>
                  <th className="p-3">Model Status</th>
                  <th className="p-3">Primary Linkage Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-hairline)] bg-[var(--bg-card)]">
                {reportData.relevant_bills.map((b) => (
                  <tr key={b.bill_id} className="hover:bg-[var(--bg-card-hover)]">
                    <td className="p-3 font-semibold text-[var(--text-primary)]">
                      <div>{b.bill_title}</div>
                      {b.bill_number && (
                        <span className="text-[10px] font-mono text-[var(--text-muted)] font-tabular">
                          {b.bill_number}
                        </span>
                      )}
                    </td>
                    <td className="p-3 capitalize text-[var(--text-secondary)]">
                      {b.jurisdiction} {b.state ? `(${b.state})` : ""}
                    </td>
                    <td className="p-3 font-bold text-amber-600 dark:text-amber-400">
                      {b.relevance_tier}
                    </td>
                    <td className="p-3 font-mono text-cyan-600 dark:text-cyan-400 text-[11px]">
                      {b.model_status}
                    </td>
                    <td className="p-3 text-[var(--text-secondary)] max-w-sm leading-relaxed">
                      {b.primary_linkage_reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 3: Disclaimers & Governance Boundaries */}
        <div className="p-3.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-hairline)] text-[11px] text-[var(--text-muted)] space-y-1.5 leading-relaxed">
          <strong className="block text-xs text-[var(--text-secondary)] font-semibold">
            Methodology &amp; Regulatory Boundaries
          </strong>
          {reportData.disclaimers.map((d, i) => (
            <p key={i}>• {d}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default PortfolioImpactReport;

