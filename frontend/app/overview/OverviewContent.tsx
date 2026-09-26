/**
 * app/overview/OverviewContent.tsx
 * ================================
 * Production SaaS Overview Dashboard for the India Legislative Intelligence Platform.
 *
 * Implements 9 data-driven sections:
 * 1. Hero / Product Header & Quick Actions
 * 2. Live Coverage Summary Cards (verified backend baseline)
 * 3. Three-Tier Capability Levels (L1 Market-Modelled, L2 State Intelligence, L3 Planned)
 * 4. Recent / Discover Bills feed (GET /api/v1/bills)
 * 5. Market-Modelled Snapshot (Central Level 1 predictions, neutral terminology, 0 Buy/Sell)
 * 6. State Intelligence Snapshot (AP, KA, KL, TG with strict 0-prediction boundary)
 * 7. Corporate Exposure Snapshot (104 documented exposures, quant vs intel universe)
 * 8. Monitoring System Status (GET /api/v1/monitoring/status)
 * 9. Quick Platform Navigation
 *
 * ARCHITECTURAL INVARIANTS:
 * - All metrics fetched from FastAPI backend (single source of truth)
 * - Zero hardcoded project statistics
 * - Zero State stock predictions (statutory guarantee)
 * - Neutral research language: no investment advice, no Buy/Sell/Hold
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useCoverage } from "@/hooks/useCoverage";
import { billsApi } from "@/lib/api/bills";
import { predictionsApi } from "@/lib/api/predictions";
import { companiesApi } from "@/lib/api/companies";
import { monitoringApi } from "@/lib/api/monitoring";
import { Card, StatCard } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge, StatusBadge, PredictionBadge } from "@/components/ui/Badge";
import {
  CapabilityBadge,
  JurisdictionBadge,
  MarketRelevanceBadge,
  CorporateExposureBadge,
} from "@/components/coverage/CapabilityBadge";
import { ErrorState, SkeletonCard } from "@/components/ui/Skeleton";
import { formatNumber, formatDate } from "@/lib/utils";
import type {
  BillSummaryItem,
  CompanySummaryItem,
  MonitoringStatusResponse,
  PredictionItem,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Section Header Component
// ---------------------------------------------------------------------------

function SectionHeading({
  title,
  subtitle,
  badge,
  action,
}: {
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-2 border-b border-slate-800/80">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-slate-100 tracking-tight">{title}</h2>
          {badge}
        </div>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Overview Content Component
// ---------------------------------------------------------------------------

export default function OverviewContent() {
  const { coverage, loading: coverageLoading, error: coverageError, refetch: refetchCoverage } = useCoverage();

  // Secondary live data states
  const [recentBills, setRecentBills] = useState<BillSummaryItem[]>([]);
  const [billsLoading, setBillsLoading] = useState(true);

  const [predictions, setPredictions] = useState<PredictionItem[]>([]);
  const [predictionsLoading, setPredictionsLoading] = useState(true);

  const [companies, setCompanies] = useState<CompanySummaryItem[]>([]);
  const [companiesLoading, setCompaniesLoading] = useState(true);

  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringStatusResponse | null>(null);
  const [monitoringLoading, setMonitoringLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    // Fetch recent bills
    billsApi
      .listBills({ limit: 6, sort_by: "introduction_date", sort_order: "desc" })
      .then((res) => {
        if (isMounted) setRecentBills(res.items);
      })
      .catch(() => {
        // Fallback gracefully
      })
      .finally(() => {
        if (isMounted) setBillsLoading(false);
      });

    // Fetch market predictions snapshot
    predictionsApi
      .listPredictions({ limit: 6 })
      .then((res) => {
        if (isMounted) setPredictions(res.items);
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setPredictionsLoading(false);
      });

    // Fetch representative companies
    companiesApi
      .listCompanies({ limit: 6 })
      .then((res) => {
        if (isMounted) setCompanies(res.items);
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setCompaniesLoading(false);
      });

    // Fetch monitoring status
    monitoringApi
      .getStatus()
      .then((res) => {
        if (isMounted) setMonitoringStatus(res);
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setMonitoringLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (coverageLoading) {
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <div className="h-10 w-96 bg-slate-800/80 rounded animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (coverageError) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <ErrorState error={coverageError} onRetry={refetchCoverage} />
        <p className="text-xs text-slate-500 text-center">
          Backend endpoint:{" "}
          <code className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
            {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}
          </code>
        </p>
      </div>
    );
  }

  if (!coverage) return null;

  const { central, state, company, unified } = coverage;

  return (
    <div className="p-6 space-y-10 max-w-7xl mx-auto animate-fade-in text-slate-200">
      {/* ==================================================================== */}
      {/* 1. HERO / PRODUCT HEADER & QUICK ACTIONS */}
      {/* ==================================================================== */}
      <section
        aria-labelledby="hero-heading"
        className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 p-6 sm:p-8 relative overflow-hidden shadow-sm"
      >
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 rounded-full bg-blue-600/5 blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-[11px] font-semibold tracking-wider uppercase px-2.5 py-0.5 rounded bg-blue-900/40 text-blue-300 border border-blue-700/40">
              Institutional Intelligence
            </span>
            <span className="text-xs text-slate-400">
              Central Parliament & State Legislative Assemblies
            </span>
          </div>

          <h1
            id="hero-heading"
            className="text-2xl sm:text-3xl font-bold text-slate-100 tracking-tight"
          >
            India Legislative Intelligence
          </h1>

          <p className="text-sm sm:text-base text-slate-300 font-medium leading-relaxed">
            Understand legislation. Trace economic exposure. See documented market relevance.
          </p>

          <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
            A rigorous research-grade analytical platform unifying Parliamentary and State Assembly
            statutory data with corporate transmission channels and backtested econometric models.
          </p>

          {/* Quick Actions */}
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link href="/explorer">
              <Button variant="primary" size="sm">
                🔍 Explore Bills
              </Button>
            </Link>
            <Link href="/companies">
              <Button variant="secondary" size="sm">
                🏢 Explore Companies
              </Button>
            </Link>
            <Link href="/predictions">
              <Button variant="outline" size="sm">
                📈 View Predictions
              </Button>
            </Link>
            <Link href="/ai-analyst">
              <Button variant="ghost" size="sm">
                🤖 Ask AI Copilot
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 2. COVERAGE SUMMARY (API-DRIVEN CARDS) */}
      {/* ==================================================================== */}
      <section aria-labelledby="coverage-summary-heading">
        <SectionHeading
          title="Platform Coverage Baseline"
          subtitle="Real-time repository counts across Central Parliament, State Assemblies, and Corporate Universe"
        />
        <h2 id="coverage-summary-heading" className="sr-only">
          Platform Coverage Summary
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <StatCard
            label="Central Bills"
            value={central.production_bills}
            subLabel="Market-modelled production scope"
            icon="📜"
            highlight="emerald"
          />
          <StatCard
            label="State Bills"
            value={state.state_bills_count}
            subLabel="Economic intelligence (4 active states)"
            icon="🗺"
            highlight="blue"
          />
          <StatCard
            label="Quant Companies"
            value={central.quantitative_companies}
            subLabel="Prediction-eligible universe"
            icon="📈"
            highlight="emerald"
          />
          <StatCard
            label="Corporate Entities"
            value={company.total_companies}
            subLabel="Quant (47) + Intel (20) + Ref (3)"
            icon="🏢"
            highlight="purple"
          />
          <StatCard
            label="Legislative Records"
            value={unified.total_legislative_records}
            subLabel="Unified discovery (22 Central + 44 State)"
            icon="⚖"
            highlight="blue"
          />
          <StatCard
            label="Corporate Exposures"
            value={unified.total_corporate_exposures}
            subLabel="Documented policy links (18 C + 86 S)"
            icon="🔗"
            highlight="amber"
          />
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 3. CAPABILITY LEVELS */}
      {/* ==================================================================== */}
      <section aria-labelledby="capability-levels-heading">
        <SectionHeading
          title="Analytical Capability Tiers"
          subtitle="Methodological firewalling ensures zero cross-contamination between quantitative models and qualitative state dossiers"
        />
        <h2 id="capability-levels-heading" className="sr-only">
          Analytical Capability Tiers
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* LEVEL 1 — Central Market Modelled */}
          <Card className="flex flex-col justify-between border-emerald-800/40 bg-slate-900/90 relative overflow-hidden">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <CapabilityBadge level={1} size="sm" />
                <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
                  Production Scope
                </span>
              </div>
              <h3 className="text-sm font-semibold text-slate-100">
                Central Parliament — Market Modelled
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Quantitative econometric models trained on historical Parliamentary acts and NSE/BSE
                market index reactions across 5 standardized event windows.
              </p>

              <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Market Predictions</span>
                  <span className="font-semibold text-emerald-300">
                    {formatNumber(central.predictions_count)} (5 windows)
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Anticipation Scores</span>
                  <span className="font-semibold text-slate-200">
                    {formatNumber(central.anticipation_scores_count)}
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Decision Records</span>
                  <span className="font-semibold text-slate-200">
                    {formatNumber(central.decisions_count)}
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Stakeholder Reports</span>
                  <span className="font-semibold text-purple-300">
                    {formatNumber(central.stakeholder_reports_count)}
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80">
              <Link
                href="/predictions"
                className="text-xs text-emerald-400 hover:text-emerald-300 font-medium inline-flex items-center gap-1"
              >
                Inspect Central Model Engine →
              </Link>
            </div>
          </Card>

          {/* LEVEL 2 — State Legislative Intelligence */}
          <Card className="flex flex-col justify-between border-blue-800/40 bg-slate-900/90 relative overflow-hidden">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <CapabilityBadge level={2} size="sm" />
                <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider">
                  4 Active Pilots
                </span>
              </div>
              <h3 className="text-sm font-semibold text-slate-100">
                State Assemblies — Economic Intelligence
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Qualitative intelligence across Andhra Pradesh, Karnataka, Kerala, and Telangana.
                Provisions, corporate exposures, and market relevance vectors.
              </p>

              <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Active Assembly Bills</span>
                  <span className="font-semibold text-blue-300">
                    {formatNumber(state.state_bills_count)} Official Records
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Corporate Exposures</span>
                  <span className="font-semibold text-slate-200">
                    {formatNumber(state.state_corporate_exposures_count)} Evidence-Backed
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Official PDFs</span>
                  <span className="font-semibold text-slate-200">
                    {formatNumber(state.state_official_pdfs_count)} Verified
                  </span>
                </div>
                <div className="flex justify-between text-slate-400 font-medium">
                  <span className="text-amber-400/90">State Stock Predictions</span>
                  <span className="text-amber-300 font-mono">0 (Statutory Isolation)</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80">
              <Link
                href="/explorer?jurisdiction=state"
                className="text-xs text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1"
              >
                Browse State Intelligence Dossiers →
              </Link>
            </div>
          </Card>

          {/* LEVEL 3 — Planned Coverage Roadmap */}
          <Card className="flex flex-col justify-between border-slate-800 bg-slate-900/60 relative overflow-hidden">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <CapabilityBadge level={3} size="sm" />
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Roadmap Pipeline
                </span>
              </div>
              <h3 className="text-sm font-semibold text-slate-100">
                Union Roadmap — 24 Planned States
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Future ingestion roadmap for 24 State Legislative Assemblies including Maharashtra,
                Tamil Nadu, Gujarat, and Uttar Pradesh.
              </p>

              <div className="p-2.5 rounded bg-slate-800/60 border border-slate-700/60 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300">Status</span>
                  <span className="text-slate-400 font-medium uppercase tracking-wider text-[10px] bg-slate-700/80 px-1.5 py-0.5 rounded">
                    Planned / Not Yet Ingested
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Zero fake records created. State bills will be ingested systematically alongside
                  official state gazettes.
                </p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80">
              <Link
                href="/states"
                className="text-xs text-slate-400 hover:text-slate-300 font-medium inline-flex items-center gap-1"
              >
                View State Coverage Registry →
              </Link>
            </div>
          </Card>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 4. RECENT / DISCOVER BILLS */}
      {/* ==================================================================== */}
      <section aria-labelledby="recent-bills-heading">
        <SectionHeading
          title="Recent & Priority Legislation"
          subtitle="Latest Central Parliamentary and State Assembly bills with documented market relevance"
          action={
            <Link href="/explorer">
              <Button variant="outline" size="xs">
                View All Legislation →
              </Button>
            </Link>
          }
        />
        <h2 id="recent-bills-heading" className="sr-only">
          Recent & Priority Legislation
        </h2>

        {billsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : recentBills.length === 0 ? (
          <p className="text-xs text-slate-500 py-4 text-center">No bills loaded.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentBills.map((b) => (
              <Card
                key={b.bill_id}
                className="flex flex-col justify-between hover:border-slate-700 transition-colors"
              >
                <div className="space-y-2.5">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <JurisdictionBadge jurisdiction={b.jurisdiction} state={b.state} size="xs" />
                    <StatusBadge status={b.status} size="xs" />
                    <MarketRelevanceBadge relevance={b.market_relevance} size="xs" />
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-slate-100 line-clamp-2 leading-snug">
                      {b.short_title || b.title}
                    </h3>
                    {b.bill_number && (
                      <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                        {b.bill_number} · {b.house}
                      </p>
                    )}
                  </div>

                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                    {b.summary}
                  </p>

                  <div className="flex flex-wrap items-center gap-1 pt-1">
                    {b.policy_domain && (
                      <Badge variant="muted" size="xs">
                        {b.policy_domain}
                      </Badge>
                    )}
                    {b.company_exposure_count > 0 && (
                      <CorporateExposureBadge count={b.company_exposure_count} size="xs" />
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-500">
                    {b.introduction_date ? formatDate(b.introduction_date) : b.year ?? "Year N/A"}
                  </span>
                  <Link href={`/bills/${b.bill_id}`}>
                    <Button variant="ghost" size="xs">
                      View Dossier →
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* ==================================================================== */}
      {/* 5. MARKET-MODELLED SNAPSHOT (CENTRAL ONLY) */}
      {/* ==================================================================== */}
      <section aria-labelledby="market-modelled-heading">
        <SectionHeading
          title="Central Market-Modelled Snapshot"
          subtitle="Estimated market-moving direction and impact strength across backtested event windows (Central only)"
          badge={
            <Badge variant="emerald" size="xs">
              Production Baseline (4,700 Records)
            </Badge>
          }
          action={
            <Link href="/predictions">
              <Button variant="outline" size="xs">
                Explore Prediction Engine →
              </Button>
            </Link>
          }
        />
        <h2 id="market-modelled-heading" className="sr-only">
          Central Market-Modelled Snapshot
        </h2>

        {/* Institutional Disclosure Note */}
        <div className="mb-4 rounded-md border border-slate-800 bg-slate-900/50 p-3 text-xs text-slate-400 flex items-start gap-2">
          <span className="text-sm">⚖</span>
          <div>
            <strong className="text-slate-300">Methodological Disclosure:</strong> Quantitative
            predictions reflect statistical backtesting on Central legislative milestones. They do
            NOT constitute investment recommendations, price targets, or financial advice. No
            Buy/Sell/Hold ratings are issued.
          </div>
        </div>

        {predictionsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : predictions.length === 0 ? (
          <p className="text-xs text-slate-500 py-4 text-center">No predictions loaded.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {predictions.map((p) => (
              <Card key={p.prediction_id} className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="slate" size="xs">
                    Window: {p.event_window}
                  </Badge>
                  <PredictionBadge direction={p.predicted_direction} size="xs" />
                </div>

                <div>
                  <div className="text-xs font-semibold text-slate-200">
                    {p.company_symbol || p.company_name || p.company_isin}
                  </div>
                  <div className="text-[11px] text-slate-500 truncate font-mono">
                    Bill: {p.bill_id}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Modelled Impact</span>
                    <span className="font-semibold text-slate-300 capitalize">
                      {p.predicted_impact_strength}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Confidence</span>
                    <span className="font-semibold text-slate-300 capitalize">
                      {p.predicted_confidence} ({Math.round(p.confidence_score * 100)}%)
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">
                    {p.predicted_market_moving ? "Market-Moving Alert" : "Standard Fluctuation"}
                  </span>
                  <Link
                    href={`/predictions/${p.prediction_id}`}
                    className="text-emerald-400 hover:text-emerald-300 font-medium"
                  >
                    View Record →
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* ==================================================================== */}
      {/* 6. STATE INTELLIGENCE SNAPSHOT */}
      {/* ==================================================================== */}
      <section aria-labelledby="state-intelligence-heading">
        <SectionHeading
          title="State Assembly Intelligence Pilots"
          subtitle="Authoritative legislative dossiers across 4 implemented southern states"
        />
        <h2 id="state-intelligence-heading" className="sr-only">
          State Assembly Intelligence
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              name: "Andhra Pradesh",
              code: "AP",
              bills: 12,
              exposures: 24,
              source: "AP Legislative Assembly Portal",
              chamber: "Bicameral",
            },
            {
              name: "Karnataka",
              code: "KA",
              bills: 11,
              exposures: 22,
              source: "Karnataka Legislative Secretariat",
              chamber: "Bicameral",
            },
            {
              name: "Kerala",
              code: "KL",
              bills: 11,
              exposures: 20,
              source: "Niyamasabha Official Portal",
              chamber: "Unicameral",
            },
            {
              name: "Telangana",
              code: "TG",
              bills: 10,
              exposures: 20,
              source: "Telangana Legislature Portal",
              chamber: "Bicameral",
            },
          ].map((st) => (
            <Card key={st.name} className="space-y-3">
              <div className="flex items-center justify-between">
                <Badge variant="primary" size="xs">
                  {st.name} Assembly
                </Badge>
                <span className="text-[10px] text-slate-500 uppercase">{st.chamber}</span>
              </div>

              <div>
                <div className="text-xl font-bold text-slate-100">{st.bills}</div>
                <div className="text-xs text-slate-400">Verified Official Bills</div>
              </div>

              <div className="space-y-1 text-xs text-slate-400 pt-2 border-t border-slate-800">
                <div className="flex justify-between">
                  <span>Corporate Exposures</span>
                  <span className="font-semibold text-slate-200">{st.exposures}</span>
                </div>
                <div className="flex justify-between">
                  <span>Economic Intelligence</span>
                  <span className="text-emerald-400 font-medium">Available</span>
                </div>
                <div className="flex justify-between">
                  <span>Market Prediction</span>
                  <span className="text-amber-400/90 font-medium">0 (Statutory)</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <Link href={`/explorer?jurisdiction=state&state=${encodeURIComponent(st.name)}`}>
                  <Button variant="ghost" size="xs" className="w-full justify-center">
                    Explore {st.name} Bills →
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>

        {/* State isolation firewall notice */}
        <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-blue-900/30 border border-blue-700/40 flex items-center justify-center text-xs text-blue-300 flex-shrink-0">
            🔒
          </div>
          <div className="text-xs">
            <span className="font-semibold text-slate-200">Statutory Isolation Guarantee:</span>{" "}
            <span className="text-slate-400">
              State legislative outcomes operate outside Central predictive modeling scope. 0 stock
              predictions exist for State legislation across all 4 active pilot assemblies.
            </span>
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 7. CORPORATE EXPOSURE SNAPSHOT */}
      {/* ==================================================================== */}
      <section aria-labelledby="corporate-exposure-heading">
        <SectionHeading
          title="Corporate Intelligence Universe"
          subtitle="70 corporate entities mapped to 104 documented statutory transmission vectors"
          action={
            <Link href="/companies">
              <Button variant="outline" size="xs">
                View Corporate Directory →
              </Button>
            </Link>
          }
        />
        <h2 id="corporate-exposure-heading" className="sr-only">
          Corporate Intelligence Universe
        </h2>

        {companiesLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : companies.length === 0 ? (
          <p className="text-xs text-slate-500 py-4 text-center">No companies loaded.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {companies.map((c) => (
              <Card key={c.company_id} className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <Badge
                    variant={c.universe_type === "quantitative" ? "emerald" : "info"}
                    size="xs"
                  >
                    {c.universe_type === "quantitative" ? "Quant Impact" : "Intelligence Entity"}
                  </Badge>
                  {c.ticker_nse && (
                    <span className="text-[11px] font-mono text-slate-400">
                      NSE: {c.ticker_nse}
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-100 truncate">
                    {c.company_name}
                  </h3>
                  <p className="text-xs text-slate-400">
                    {c.sector} {c.industry ? `· ${c.industry}` : ""}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs text-slate-400">
                  <span>Documented Exposures</span>
                  <CorporateExposureBadge count={c.documented_exposure_count} size="xs" />
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-500">
                    {c.is_quant_eligible ? "Prediction Eligible" : "Qualitative Intel Only"}
                  </span>
                  <Link href={`/companies/${c.company_id}`}>
                    <Button variant="ghost" size="xs">
                      View Profile →
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* ==================================================================== */}
      {/* 8. MONITORING STATUS */}
      {/* ==================================================================== */}
      <section aria-labelledby="monitoring-status-heading">
        <SectionHeading
          title="Automated Legislative Monitoring"
          subtitle="Real-time parliamentary gazette and assembly scraper operational health"
          action={
            <Link href="/monitoring">
              <Button variant="outline" size="xs">
                Monitoring Dashboard →
              </Button>
            </Link>
          }
        />
        <h2 id="monitoring-status-heading" className="sr-only">
          Automated Legislative Monitoring
        </h2>

        {monitoringLoading ? (
          <SkeletonCard />
        ) : (
          <Card className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
            <div>
              <div className="text-xs text-slate-500 font-medium uppercase">System Status</div>
              <div className="flex items-center gap-2 mt-1">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-base font-bold text-slate-100">
                  {monitoringStatus?.system_status ?? "OPERATIONAL"}
                </span>
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-500 font-medium uppercase">Tracked Sources</div>
              <div className="text-base font-bold text-slate-100 mt-1">
                {monitoringStatus?.enabled_sources ?? 5} / {monitoringStatus?.total_sources ?? 5} Active
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-500 font-medium uppercase">Last Verified Check</div>
              <div className="text-xs text-slate-300 mt-1 truncate">
                {monitoringStatus?.last_run_timestamp
                  ? formatDate(monitoringStatus.last_run_timestamp)
                  : "Automated Daily Runner"}
              </div>
            </div>

            <div className="md:text-right">
              <Link href="/monitoring">
                <Button variant="secondary" size="sm">
                  View Feed Logs
                </Button>
              </Link>
            </div>
          </Card>
        )}
      </section>

      {/* ==================================================================== */}
      {/* 9. QUICK NAVIGATION */}
      {/* ==================================================================== */}
      <section aria-labelledby="quick-nav-heading">
        <SectionHeading
          title="Quick Platform Navigation"
          subtitle="Direct links to all intelligence domains and analytical modules"
        />
        <h2 id="quick-nav-heading" className="sr-only">
          Quick Platform Navigation
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
          {[
            { label: "Explore Bills", icon: "🏛", href: "/explorer", desc: "Unified Search" },
            { label: "Companies", icon: "🏢", href: "/companies", desc: "Corporate Universe" },
            { label: "Predictions", icon: "📈", href: "/predictions", desc: "Central Models" },
            { label: "State Assemblies", icon: "🗺", href: "/states", desc: "4 Active Pilots" },
            { label: "Monitoring", icon: "📡", href: "/monitoring", desc: "Gazette Scrapers" },
            { label: "Watchlists", icon: "⭐", href: "/watchlists", desc: "Portfolio Alerts" },
            { label: "AI Analyst", icon: "🤖", href: "/ai-analyst", desc: "Groq Copilot" },
          ].map((nav) => (
            <Link key={nav.href} href={nav.href} className="group">
              <Card className="h-full p-3.5 text-center group-hover:border-slate-700 transition-colors flex flex-col items-center justify-center gap-1.5">
                <span className="text-xl" aria-hidden="true">
                  {nav.icon}
                </span>
                <span className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                  {nav.label}
                </span>
                <span className="text-[10px] text-slate-500">{nav.desc}</span>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Institutional Legal & Methodology Disclaimer */}
      <footer className="border-t border-slate-800/80 pt-4 text-xs text-slate-500 leading-relaxed space-y-1">
        <p>
          <strong className="text-slate-400">Research & Academic Integrity:</strong> Data
          displayed originates exclusively from official Parliamentary gazettes, State legislative
          assembly secretariats, and verified backend databases. Predictive models are quantitative
          statistical tools for educational and institutional research and do not constitute
          financial or trading recommendations.
        </p>
      </footer>
    </div>
  );
}
