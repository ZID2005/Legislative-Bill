/**
 * app/coverage/CoverageContent.tsx
 * ==================================
 * Data-driven platform coverage page.
 * All numbers are from the /api/v1/coverage endpoint — not hardcoded.
 *
 * Displays:
 * - Central Parliament coverage
 * - State legislative coverage (with 0-prediction guarantee)
 * - Company coverage
 * - Unified statistics
 *
 * Task 8.14.9 — Legislative Monitoring & Discovery Center.
 */

"use client";

import React, { useEffect, useState } from "react";
import type { CoverageReportResponse } from "@/types/api";
import { coverageApi } from "@/lib/api/coverage";
import { Skeleton } from "@/components/ui/Skeleton";

interface StatCardProps {
  label: string;
  value: number | string;
  description?: string;
  accent?: string;
  icon?: string;
}

function StatCard({ label, value, description, accent = "text-slate-200", icon }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 hover:border-slate-700 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</span>
        {icon && <span className="text-lg" aria-hidden="true">{icon}</span>}
      </div>
      <div className={`text-3xl font-bold tabular-nums ${accent}`}>{value}</div>
      {description && <p className="text-xs text-slate-600 mt-1">{description}</p>}
    </div>
  );
}

function SectionHeader({ icon, title, badge }: { icon: string; title: string; badge?: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <span className="text-2xl" aria-hidden="true">{icon}</span>
      <h2 className="text-base font-semibold text-slate-100">{title}</h2>
      {badge && (
        <span className="ml-auto text-xs px-2 py-0.5 rounded border border-slate-700 text-slate-500 font-mono">
          {badge}
        </span>
      )}
    </div>
  );
}

export function CoverageContent() {
  const [data, setData] = useState<CoverageReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    coverageApi.getCoverage()
      .then(setData)
      .catch((e: unknown) => setError((e as Error).message ?? "Failed to load coverage data"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-8 max-w-[1200px] mx-auto">
      {/* Header */}
      <header>
        <h1 className="text-xl font-bold text-slate-100">Platform Coverage & Research Integrity</h1>
        <p className="text-sm text-slate-400 mt-1">
          Repository-verified coverage metrics. All numbers are live from the platform backend.
        </p>
      </header>

      {/* Research Integrity Notice */}
      <div
        className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-5 py-4"
        role="note"
        aria-label="Research integrity statement"
      >
        <div className="flex items-start gap-3">
          <span className="text-emerald-400 text-xl shrink-0" aria-hidden="true">✓</span>
          <div>
            <p className="text-sm font-semibold text-emerald-300 mb-1">Research Integrity Statement</p>
            <p className="text-sm text-slate-400">
              Coverage statistics are derived from actual repository records, not estimates.
              Every number is verifiable against the underlying data.
              <span className="text-amber-400 font-semibold"> State stock predictions remain permanently and verifiably 0.</span>
            </p>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div aria-busy="true" aria-label="Loading coverage data" className="space-y-6">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
          <span className="font-semibold">⚠ Failed to load coverage data:</span> {error}
        </div>
      )}

      {/* Central Coverage */}
      {data && (
        <>
          <section aria-labelledby="central-heading">
            <div id="central-heading">
              <SectionHeader icon="🏛" title="Central Parliament" badge="QUANTITATIVE MODELLED" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              <StatCard
                label="Production Bills"
                value={data.central.production_bills}
                description="Validated, in-production bills"
                accent="text-blue-400"
                icon="📋"
              />
              <StatCard
                label="Total Bills in Repo"
                value={data.central.total_bills_in_repo}
                description="Including reference records"
                icon="🗃"
              />
              <StatCard
                label="Quantitative Companies"
                value={data.central.quantitative_companies}
                description="NSE/BSE listed securities"
                accent="text-blue-400"
                icon="🏢"
              />
              <StatCard
                label="Bill × Company Pairs"
                value={data.central.bill_company_pairs.toLocaleString()}
                description="Exposure coverage pairs"
                icon="🔗"
              />
              <StatCard
                label="Predictions"
                value={data.central.predictions_count.toLocaleString()}
                description="Validated market predictions"
                accent="text-purple-400"
                icon="📊"
              />
              <StatCard
                label="Decisions"
                value={data.central.decisions_count.toLocaleString()}
                description="Decision support records"
                accent="text-purple-400"
                icon="⚖"
              />
              <StatCard
                label="Anticipation Scores"
                value={data.central.anticipation_scores_count.toLocaleString()}
                description="Bill × company pairs"
                icon="🎯"
              />
              <StatCard
                label="Stakeholder Reports"
                value={data.central.stakeholder_reports_count.toLocaleString()}
                description="Cross-stakeholder analyses"
                icon="📑"
              />
            </div>
          </section>

          {/* State Coverage */}
          <section aria-labelledby="state-heading">
            <div id="state-heading">
              <SectionHeader icon="🗳" title="State Legislatures" badge="LEGISLATIVE INTELLIGENCE" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              <StatCard
                label="Implemented States"
                value={data.state.implemented_states_count}
                description={data.state.implemented_states_list.join(", ")}
                accent="text-emerald-400"
                icon="✓"
              />
              <StatCard
                label="Planned States"
                value={data.state.planned_states_count}
                description="Roadmap states"
                icon="◦"
              />
              <StatCard
                label="State Bills"
                value={data.state.state_bills_count}
                description="Monitored bills"
                icon="📋"
              />
              <StatCard
                label="Official PDFs"
                value={data.state.state_official_pdfs_count}
                description="Verified document archive"
                icon="📄"
              />
              <StatCard
                label="Knowledge Records"
                value={data.state.state_knowledge_records_count}
                description="Legislative intelligence"
                icon="🧠"
              />
              <StatCard
                label="Corporate Exposures"
                value={data.state.state_corporate_exposures_count}
                description="Company ↔ State bill links"
                icon="🔗"
              />
              <div className="col-span-2 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 flex items-center gap-3">
                <span className="text-2xl" aria-hidden="true">🔒</span>
                <div>
                  <div className="text-xs text-amber-400 font-semibold uppercase tracking-wide">State Stock Predictions</div>
                  <div className="text-3xl font-bold tabular-nums text-amber-400 mt-0.5">
                    {data.state.state_stock_predictions_count}
                  </div>
                  <p className="text-xs text-amber-500/70 mt-1">
                    Always and verifiably 0. State monitoring does not generate predictions.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Company Coverage */}
          <section aria-labelledby="company-heading">
            <div id="company-heading">
              <SectionHeader icon="🏢" title="Company Coverage" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard
                label="Total Companies"
                value={data.company.total_companies}
                description="All entity types"
                icon="🏢"
              />
              <StatCard
                label="Quantitative"
                value={data.company.quantitative_companies}
                description="Full model coverage"
                accent="text-blue-400"
                icon="📊"
              />
              <StatCard
                label="Corporate Intelligence"
                value={data.company.intelligence_companies}
                description="Qualitative analysis"
                icon="🔍"
              />
              <StatCard
                label="Reference"
                value={data.company.reference_companies}
                description="Exposure context only"
                icon="📖"
              />
            </div>
          </section>

          {/* Unified Coverage */}
          <section aria-labelledby="unified-heading">
            <div id="unified-heading">
              <SectionHeader icon="🌐" title="Unified Coverage" badge="CROSS-JURISDICTION" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-2 gap-3">
              <StatCard
                label="Total Legislative Records"
                value={data.unified.total_legislative_records}
                description="Central + State bills"
                accent="text-emerald-400"
                icon="📋"
              />
              <StatCard
                label="Total Corporate Exposures"
                value={data.unified.total_corporate_exposures}
                description="All jurisdictions"
                accent="text-emerald-400"
                icon="🔗"
              />
            </div>
          </section>

          {/* Provenance Footer */}
          <footer className="rounded-xl border border-slate-800 bg-slate-900/40 px-5 py-4">
            <div className="text-xs text-slate-500">
              <span className="font-semibold text-slate-400">Data Provenance: </span>
              All statistics are live reads from the production repository.
              Central: prediction, decision, anticipation, and report counts are from frozen validated datasets.
              State: exposure counts are from active monitoring. State predictions are architecturally impossible.
            </div>
          </footer>
        </>
      )}
    </div>
  );
}
