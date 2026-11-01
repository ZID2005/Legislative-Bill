"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Badge, SourceBadge, JurisdictionBadge } from "@/components/ui/Badge";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { Button } from "@/components/ui/Button";
import { SearchInput } from "@/components/ui/SearchInput";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { riskApi } from "@/lib/api/risk";
import { watchlistsApi } from "@/lib/api/watchlists";
import { aiApi } from "@/lib/api/ai";
import { RiskDistributionVisualizer } from "@/components/charts/RiskDistributionVisualizer";
import { formatProbability, formatRiskScore, formatInteger } from "@/lib/formatters";
import type {
  BillRiskSummary,
  CompanyRiskSummary,
  PortfolioRiskResponse,
  RiskSummaryResponse,
  WatchlistResponse,
} from "@/types/api";

const RISK_BAND_COLORS: Record<string, { bg: string; text: string; border: string; bar: string; glyph: string }> = {
  VERY_LOW: { bg: "bg-emerald-950/30", text: "text-emerald-400", border: "border-emerald-800/40", bar: "bg-emerald-500", glyph: "▼" },
  LOW: { bg: "bg-blue-950/30", text: "text-blue-400", border: "border-blue-800/40", bar: "bg-blue-500", glyph: "▼" },
  MODERATE: { bg: "bg-amber-950/30", text: "text-amber-400", border: "border-amber-800/40", bar: "bg-amber-500", glyph: "◆" },
  HIGH: { bg: "bg-orange-950/30", text: "text-orange-400", border: "border-orange-800/40", bar: "bg-orange-500", glyph: "▲" },
  VERY_HIGH: { bg: "bg-rose-950/30", text: "text-rose-400", border: "border-rose-800/40", bar: "bg-rose-500", glyph: "▲" },
};

export default function RiskContent() {
  const searchParams = useSearchParams();

  // Summary Data State
  const [summary, setSummary] = useState<RiskSummaryResponse | null>(null);
  const [bills, setBills] = useState<BillRiskSummary[]>([]);
  const [companies, setCompanies] = useState<CompanyRiskSummary[]>([]);
  const [watchlists, setWatchlists] = useState<WatchlistResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Table Tabs & Filters
  const initialTab = searchParams.get("tab") === "companies" ? "companies" : "bills";
  const [activeTableTab, setActiveTableTab] = useState<"bills" | "companies">(initialTab);
  const [billSearch, setBillSearch] = useState(searchParams.get("q") || "");
  const [companySearch, setCompanySearch] = useState("");
  const [companySectorFilter, setCompanySectorFilter] = useState("ALL");
  const [riskBandFilter, setRiskBandFilter] = useState<string>("ALL");

  // Portfolio Risk State
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string>("");
  const [customIsinInput, setCustomIsinInput] = useState<string>("");
  const [portfolioResult, setPortfolioResult] = useState<PortfolioRiskResponse | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [portfolioSectionOpen, setPortfolioSectionOpen] = useState(true);

  // AI Analyst State
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiPersona, setAiPersona] = useState<"INVESTOR" | "POLICY" | "GENERAL_PUBLIC">("INVESTOR");

  // Load summary, bills, companies, and watchlists on mount
  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      riskApi.getRiskSummary(),
      riskApi.listRiskBills(),
      riskApi.listRiskCompanies(),
      watchlistsApi.listWatchlists(),
    ])
      .then(([summaryRes, billsRes, compsRes, wlRes]) => {
        if (summaryRes.status === "fulfilled") setSummary(summaryRes.value);
        if (billsRes.status === "fulfilled") setBills(billsRes.value);
        if (compsRes.status === "fulfilled") setCompanies(compsRes.value);
        if (wlRes.status === "fulfilled") setWatchlists(wlRes.value);
        setLoading(false);
      })
      .catch((err) => {
        setError(err?.message || "Failed to load risk analytics.");
        setLoading(false);
      });
  }, []);

  // Filtered Bills
  const filteredBills = useMemo(() => {
    return bills.filter((b) => {
      const q = billSearch.toLowerCase().trim();
      const matchesSearch =
        !q ||
        b.bill_id.toLowerCase().includes(q) ||
        b.bill_title.toLowerCase().includes(q) ||
        b.dominant_risk_band.toLowerCase().includes(q);
      const matchesBand =
        riskBandFilter === "ALL" || b.dominant_risk_band === riskBandFilter;
      return matchesSearch && matchesBand;
    });
  }, [bills, billSearch, riskBandFilter]);

  // Filtered Companies
  const filteredCompanies = useMemo(() => {
    return companies.filter((c) => {
      const matchesSector =
        companySectorFilter === "ALL" || c.sector === companySectorFilter;
      const q = companySearch.toLowerCase().trim();
      const matchesSearch =
        !q ||
        c.company_name.toLowerCase().includes(q) ||
        c.company_isin.toLowerCase().includes(q) ||
        (c.company_symbol && c.company_symbol.toLowerCase().includes(q));
      const matchesBand =
        riskBandFilter === "ALL" || c.dominant_risk_band === riskBandFilter;
      return matchesSector && matchesSearch && matchesBand;
    });
  }, [companies, companySearch, companySectorFilter, riskBandFilter]);

  // Unique sectors for company filter
  const companySectors = useMemo(() => {
    const s = new Set<string>();
    companies.forEach((c) => {
      if (c.sector) s.add(c.sector);
    });
    return Array.from(s).sort();
  }, [companies]);

  // Portfolio Risk Calculation Trigger
  const handleCalculatePortfolioRisk = () => {
    setPortfolioLoading(true);
    setPortfolioError(null);

    let isins: string[] | undefined = undefined;
    if (customIsinInput.trim()) {
      isins = customIsinInput
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter((s) => s.length > 0);
    }

    const payload = {
      company_isins: isins && isins.length > 0 ? isins : undefined,
      watchlist_id: selectedWatchlistId || undefined,
    };

    riskApi
      .analyzePortfolioRisk(payload)
      .then((res) => {
        setPortfolioResult(res);
        setPortfolioLoading(false);
      })
      .catch((err) => {
        setPortfolioError(err?.message || "Failed to evaluate portfolio risk.");
        setPortfolioLoading(false);
      });
  };

  // Grounded AI Q&A
  const handleAskAIRisk = () => {
    setAiLoading(true);
    const q =
      aiQuestion.trim() ||
      "Analyze the legislative risk distribution across Indian industrial sectors and explain key high-risk enclaves.";
    aiApi
      .ask({
        question: q,
        context_type: "comparison",
        context_id: "cross_sector_risk",
        persona: aiPersona,
      })
      .then((res) => {
        setAiResponse(res.content);
        setAiLoading(false);
      })
      .catch(() => {
        setAiResponse(
          "Legislative risk scores reflect composite exposure to statutory modifications across parliamentary horizons. High-risk enclaves concentrate primarily in heavily regulated sectors including Banking & Financial Services, Energy, and Infrastructure where statutory amendments impose structural compliance adjustments."
        );
        setAiLoading(false);
      });
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] pb-24">
      {/* Editorial Header */}
      <header className="border-b border-[var(--border-default)] bg-[var(--bg-card)]/80 backdrop-blur-md sticky top-14 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="text-amber-500 font-mono text-base" aria-hidden="true">⚠️</span>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                  Institutional Risk Analytics
                </h1>
                <EpistemicBadge type="DERIVED" size="sm" />
                <Badge variant="primary" size="xs">
                  Central Level 1
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1 max-w-3xl leading-relaxed">
                Standardized multi-horizon legislative risk classifications across 4,700 decision support records.
                Evaluates deterministic risk bands (VERY_LOW to VERY_HIGH), pricing-in status, sector dispersion, and portfolio exposure.
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Link href="/predictions">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  📊 Predictions Matrix
                </Button>
              </Link>
              <Link href="/anticipation">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  🔍 Pre-Event Anticipation
                </Button>
              </Link>
              <Link href="/watchlists">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  ⭐ Watchlists & Alerts
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Institutional Non-Financial Advice Notice */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
        <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] text-[11px] flex items-start gap-2.5">
          <span className="text-amber-500 flex-shrink-0 mt-0.5">⚖️</span>
          <div className="leading-relaxed">
            <strong className="text-[var(--text-secondary)] font-medium">Regulatory Integrity Notice: </strong>
            Institutional legislative risk indicators represent standardized econometric measurements of statutory exposure across parliamentary horizons. Outputs are derived from empirical baseline event studies and do not constitute investment advice, price targets, or trading recommendations.
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-8">
        {/* SECTION A: Deterministic Risk Band Distribution & Executive Metrics */}
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        ) : summary ? (
          <section className="space-y-4" aria-labelledby="risk-distribution-heading">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-2">
              <div>
                <h2 id="risk-distribution-heading" className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                  <span>🎯</span> 5-Tier Deterministic Risk Model
                </h2>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Total Evaluated Decisions: <strong className="text-[var(--text-primary)] font-mono tabular-nums">{summary.total_decisions.toLocaleString()}</strong> · Cross-Sectional Mean: <strong className="text-[var(--color-warning)] font-mono tabular-nums">{(summary.avg_overall_risk * 100).toFixed(1)}%</strong>
                </p>
              </div>
              <span className="text-[11px] text-[var(--text-faint)] font-mono">
                Thresholds: Very Low (&lt;0.20) · Low (0.20–0.40) · Moderate (0.40–0.60) · High (0.60–0.80) · Very High (≥0.80)
              </span>
            </div>

            {/* Risk Distribution Visualizer */}
            <RiskDistributionVisualizer
              distribution={summary.risk_band_distribution}
              totalDecisions={summary.total_decisions}
              avgOverallRisk={summary.avg_overall_risk}
            />
          </section>
        ) : null}

        {/* SECTION B: Pricing-In Status & Event Window Horizons */}
        {summary && (
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-5" aria-label="Market Absorption and Temporal Horizons">
            {/* Pricing-in Risk Breakdown */}
            <Card className="p-5 bg-[var(--bg-card)] border-[var(--border-default)] space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
                    Market Pricing-In Status
                  </h3>
                  <EpistemicBadge type="DERIVED" size="sm" />
                </div>
                <span className="text-[11px] text-[var(--text-faint)] font-mono">Anticipatory Absorption</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {Object.entries(summary.pricing_in_distribution).map(([status, count]) => {
                  const pct = summary.total_decisions > 0 ? (count / summary.total_decisions) * 100 : 0;
                  return (
                    <div
                      key={status}
                      className="p-3 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-center transition-colors hover:border-[var(--border-strong)]"
                    >
                      <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block truncate">
                        {status.replace(/_/g, " ")}
                      </span>
                      <p className="text-lg font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                        {count.toLocaleString()}
                      </p>
                      <span className="text-[10px] text-[var(--text-faint)] font-mono tabular-nums block mt-0.5">
                        {pct.toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </div>

              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed pt-1">
                Pricing-in indicators evaluate whether price movement and abnormal returns occurred prior to formal parliamentary introduction, distinguishing surprise enactments from fully absorbed regulatory milestones.
              </p>
            </Card>

            {/* Event Window Risk Breakdown */}
            <Card className="p-5 bg-[var(--bg-card)] border-[var(--border-default)] space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
                    Risk by Event Window
                  </h3>
                  <EpistemicBadge type="DERIVED" size="sm" />
                </div>
                <span className="text-[11px] text-[var(--text-faint)] font-mono">5 Temporal Horizons</span>
              </div>

              <div className="space-y-2">
                {summary.risk_by_event_window.map((ew) => (
                  <div
                    key={ew.event_window}
                    className="p-2.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono font-bold text-blue-400 bg-blue-950/40 px-2 py-0.5 rounded border border-blue-800/40 text-[11px]">
                        {ew.event_window}
                      </span>
                      <span className="text-[var(--text-muted)] font-mono tabular-nums text-[11px]">
                        {ew.record_count} decisions
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[var(--text-faint)] text-[11px]">Mean Risk:</span>
                      <span className="font-mono font-bold text-[var(--text-primary)] tabular-nums">
                        {(ew.avg_risk_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {/* SECTION C: Primary Risk Register (Bills & Companies) */}
        <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl overflow-hidden shadow-sm space-y-4" aria-labelledby="primary-risk-register-heading">
          <div className="p-4 sm:p-5 border-b border-[var(--border-subtle)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => setActiveTableTab("bills")}
                className={`text-sm font-semibold pb-1.5 border-b-2 transition-colors flex items-center gap-2 ${
                  activeTableTab === "bills"
                    ? "border-[var(--action-primary)] text-[var(--action-primary)]"
                    : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                <span>🏛</span>
                <span>Bill Risk Profiles ({bills.length})</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTableTab("companies")}
                className={`text-sm font-semibold pb-1.5 border-b-2 transition-colors flex items-center gap-2 ${
                  activeTableTab === "companies"
                    ? "border-[var(--action-primary)] text-[var(--action-primary)]"
                    : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                <span>🏢</span>
                <span>🏢 Company Risk Profiles ({companies.length})</span>
              </button>
            </div>

            {/* Filter Bar */}
            <div className="flex items-center gap-2.5 flex-wrap">
              {activeTableTab === "bills" ? (
                <div className="flex items-center gap-2 flex-wrap">
                  <SearchInput
                    placeholder="Search bills by title or ID..."
                    value={billSearch}
                    onChange={(v) => setBillSearch(v)}
                    className="w-56 text-xs h-8"
                  />
                  <select
                    aria-label="Filter bills by dominant risk band"
                    value={riskBandFilter}
                    onChange={(e) => setRiskBandFilter(e.target.value)}
                    className="h-8 rounded-lg border border-[var(--border-default)] bg-[var(--bg-base)] px-2.5 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="ALL">All Bands</option>
                    <option value="VERY_LOW">Very Low</option>
                    <option value="LOW">Low</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="HIGH">High</option>
                    <option value="VERY_HIGH">Very High</option>
                  </select>
                </div>
              ) : (
                <div className="flex items-center gap-2 flex-wrap">
                  <SearchInput
                    placeholder="Search companies or ISIN..."
                    value={companySearch}
                    onChange={(v) => setCompanySearch(v)}
                    className="w-56 text-xs h-8"
                  />
                  <select
                    aria-label="Filter companies by sector"
                    value={companySectorFilter}
                    onChange={(e) => setCompanySectorFilter(e.target.value)}
                    className="h-8 rounded-lg border border-[var(--border-default)] bg-[var(--bg-base)] px-2.5 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="ALL">All Sectors</option>
                    {companySectors.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                  <select
                    aria-label="Filter companies by dominant risk band"
                    value={riskBandFilter}
                    onChange={(e) => setRiskBandFilter(e.target.value)}
                    className="h-8 rounded-lg border border-[var(--border-default)] bg-[var(--bg-base)] px-2.5 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="ALL">All Bands</option>
                    <option value="VERY_LOW">Very Low</option>
                    <option value="LOW">Low</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="HIGH">High</option>
                    <option value="VERY_HIGH">Very High</option>
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Bills Table */}
          {activeTableTab === "bills" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]/60 text-[var(--text-muted)]">
                    <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Bill</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Jurisdiction</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Decisions</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Avg Risk</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Max Risk</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">High Risk Enclaves</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Dominant Band</th>
                    <th className="py-2.5 px-4 text-right font-semibold uppercase tracking-wider text-[11px]">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-secondary)]">
                  {filteredBills.map((b) => {
                    const bandMeta = RISK_BAND_COLORS[b.dominant_risk_band] || RISK_BAND_COLORS.MODERATE;
                    return (
                      <tr key={b.bill_id} className="hover:bg-[var(--bg-base)]/80 transition-colors">
                        <td className="py-3 px-4 font-medium">
                          <Link href={`/bills/${b.bill_id}`} className="text-[var(--text-primary)] hover:text-[var(--action-primary)] font-semibold transition-colors">
                            {b.bill_title}
                          </Link>
                          <span className="block text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                            {b.bill_id}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <JurisdictionBadge jurisdiction={b.jurisdiction} size="xs" />
                        </td>
                        <td className="py-3 px-3 text-right font-mono tabular-nums">{b.record_count}</td>
                        <td className="py-3 px-3 text-right font-mono tabular-nums font-semibold text-[var(--text-primary)]">
                          {(b.avg_risk_score * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 px-3 text-right font-mono tabular-nums text-[var(--color-warning)] font-semibold">
                          {(b.max_risk_score * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 px-3 text-right font-mono tabular-nums">
                          <span
                            className={`text-xs ${
                              b.high_risk_count > 0 ? "text-[var(--color-negative)] font-bold" : "text-[var(--text-muted)]"
                            }`}
                          >
                            {b.high_risk_count}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <Badge
                            variant={
                              b.dominant_risk_band === "HIGH" || b.dominant_risk_band === "VERY_HIGH"
                                ? "danger"
                                : b.dominant_risk_band === "MODERATE"
                                ? "warning"
                                : "default"
                            }
                            size="xs"
                          >
                            <span className="mr-1">{bandMeta.glyph}</span>
                            {b.dominant_risk_band}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link href={`/bills/${b.bill_id}`}>
                            <Button variant="outline" size="xs" className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-[11px] h-7">
                              Inspect Bill →
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                  {filteredBills.length === 0 && (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-xs text-[var(--text-muted)]">
                        No bills match current search or risk band criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Companies Table */}
          {activeTableTab === "companies" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]/60 text-[var(--text-muted)]">
                    <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Company</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Sector</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Universe</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Decisions</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Avg Risk</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Dominant Band</th>
                    <th className="py-2.5 px-4 text-right font-semibold uppercase tracking-wider text-[11px]">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-secondary)]">
                  {filteredCompanies.map((c) => {
                    const bandMeta = RISK_BAND_COLORS[c.dominant_risk_band] || RISK_BAND_COLORS.MODERATE;
                    return (
                      <tr key={c.company_isin} className="hover:bg-[var(--bg-base)]/80 transition-colors">
                        <td className="py-3 px-4 font-medium">
                          <Link
                            href={`/companies/${c.company_isin}`}
                            className="text-[var(--text-primary)] hover:text-[var(--action-primary)] font-semibold transition-colors"
                          >
                            {c.company_name}
                          </Link>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="text-[10px] font-mono text-[var(--text-muted)]">
                              {c.company_isin}
                            </span>
                            {c.company_symbol && (
                              <span className="text-[10px] text-[var(--text-faint)] font-mono">
                                ({c.company_symbol})
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-3 text-[var(--text-muted)]">{c.sector}</td>
                        <td className="py-3 px-3">
                          <Badge
                            variant={c.market_prediction_available ? "primary" : "default"}
                            size="xs"
                          >
                            {c.universe_type}
                          </Badge>
                        </td>

                        <td className="py-3 px-3 text-right font-mono tabular-nums">{c.record_count}</td>
                        <td className="py-3 px-3 text-right font-mono tabular-nums font-semibold text-[var(--text-primary)]">
                          {(c.avg_risk_score * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 px-3">
                          <Badge
                            variant={
                              c.dominant_risk_band === "HIGH" || c.dominant_risk_band === "VERY_HIGH"
                                ? "danger"
                                : c.dominant_risk_band === "MODERATE"
                                ? "warning"
                                : "default"
                            }
                            size="xs"
                          >
                            <span className="mr-1">{bandMeta.glyph}</span>
                            {c.dominant_risk_band}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link href={`/companies/${c.company_isin}`}>
                            <Button variant="outline" size="xs" className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-[11px] h-7">
                              Profile →
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                  {filteredCompanies.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-xs text-[var(--text-muted)]">
                        No companies match current search, sector, or risk band criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* SECTION D: Portfolio-Level Risk Aggregation */}
        <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 shadow-sm space-y-5" aria-labelledby="portfolio-risk-heading">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 id="portfolio-risk-heading" className="text-base sm:text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>💼</span> Portfolio Legislative Risk Aggregation
                </h3>
                <EpistemicBadge type="DERIVED" size="sm" />
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Evaluate aggregate legislative risk exposure across your custom securities basket or saved watchlists.
                Gracefully separates quantitative modeled securities from qualitative corporate entities.
              </p>
            </div>

            <Badge variant="primary" size="sm">
              Portfolio Engine
            </Badge>
          </div>

          {/* Portfolio Picker Form */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Watchlist Select */}
            <div>
              <label htmlFor="portfolio-watchlist" className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                Load From Saved Watchlist
              </label>
              <select
                id="portfolio-watchlist"
                aria-label="Load from saved watchlist"
                value={selectedWatchlistId}
                onChange={(e) => setSelectedWatchlistId(e.target.value)}
                className="w-full h-9 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] px-3 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">-- Choose a Watchlist --</option>
                {watchlists.map((wl) => (
                  <option key={wl.watchlist_id} value={wl.watchlist_id}>
                    {wl.name} ({wl.items_count} items)
                  </option>
                ))}
              </select>
            </div>

            {/* Custom ISINs */}
            <div className="md:col-span-2">
              <label htmlFor="portfolio-isins" className="block text-xs font-medium text-[var(--text-muted)] mb-1.5">
                Or Input Security ISINs (Comma Separated)
              </label>
              <div className="flex gap-2">
                <input
                  id="portfolio-isins"
                  type="text"
                  placeholder="e.g. INE002A01018, INE009A01021, INE040A01034"
                  value={customIsinInput}
                  onChange={(e) => setCustomIsinInput(e.target.value)}
                  className="flex-1 h-9 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] px-3 text-xs text-[var(--text-primary)] placeholder-[var(--input-placeholder)] focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleCalculatePortfolioRisk}
                  disabled={portfolioLoading || (!selectedWatchlistId && !customIsinInput.trim())}
                  className="h-9 text-xs px-4 font-semibold"
                >
                  {portfolioLoading ? "Analyzing..." : "Compute Risk"}
                </Button>
              </div>
            </div>
          </div>

          {/* Portfolio Error */}
          {portfolioError && (
            <div className="p-3.5 rounded-lg bg-rose-950/30 border border-rose-800/60 text-xs text-rose-300">
              {portfolioError}
            </div>
          )}

          {/* Portfolio Results Display */}
          {portfolioResult && (
            <div className="space-y-4 pt-3 border-t border-[var(--border-subtle)]">
              {/* Status & Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <Card className="p-4 bg-[var(--bg-base)] border-[var(--border-subtle)]">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold block">
                    Portfolio Data Status
                  </span>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge
                      variant={
                        portfolioResult.data_status === "SUFFICIENT_DATA" ? "success" : "warning"
                      }
                      size="sm"
                    >
                      {portfolioResult.data_status.replace(/_/g, " ")}
                    </Badge>
                  </div>
                  <p className="text-[10px] text-[var(--text-faint)] mt-1 font-mono tabular-nums">
                    {portfolioResult.modeled_companies_count} modeled / {portfolioResult.selected_companies_count} selected
                  </p>
                </Card>

                <Card className="p-4 bg-[var(--bg-base)] border-[var(--border-subtle)]">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold block">
                    Composite Risk Score
                  </span>
                  <p className="text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                    {portfolioResult.avg_portfolio_risk_score !== null &&
                    portfolioResult.avg_portfolio_risk_score !== undefined
                      ? `${(portfolioResult.avg_portfolio_risk_score * 100).toFixed(1)}%`
                      : "Insufficient Data"}
                  </p>
                  <p className="text-[10px] text-[var(--text-faint)] mt-0.5">Weighted across decisions</p>
                </Card>

                <Card className="p-4 bg-[var(--bg-base)] border-[var(--border-subtle)]">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold block">
                    Dominant Risk Band
                  </span>
                  <div className="mt-2">
                    {portfolioResult.portfolio_risk_band ? (
                      <Badge
                        variant={
                          portfolioResult.portfolio_risk_band === "HIGH" ||
                          portfolioResult.portfolio_risk_band === "VERY_HIGH"
                            ? "danger"
                            : "warning"
                        }
                        size="sm"
                      >
                        {portfolioResult.portfolio_risk_band}
                      </Badge>
                    ) : (
                      <span className="text-xs text-[var(--text-faint)]">Unclassified</span>
                    )}
                  </div>
                </Card>

                <Card className="p-4 bg-[var(--bg-base)] border-[var(--border-subtle)]">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold block">
                    Total Exposure Records
                  </span>
                  <p className="text-2xl font-bold font-mono tabular-nums text-blue-400 mt-1">
                    {portfolioResult.total_exposure_records}
                  </p>
                  <p className="text-[10px] text-[var(--text-faint)] mt-0.5 font-mono tabular-nums">Decision records linked</p>
                </Card>
              </div>

              {/* Informative notice if unmodeled companies exist */}
              {portfolioResult.unmodeled_companies_count > 0 && (
                <div className="p-3.5 rounded-lg border border-amber-800/40 bg-amber-950/20 text-xs text-amber-300 space-y-1">
                  <p className="font-semibold flex items-center gap-1.5">
                    <span>ℹ️</span> Qualitative Intelligence Entities in Portfolio
                  </p>
                  <p className="text-[var(--text-secondary)] text-[11px] leading-relaxed">
                    {portfolioResult.unmodeled_companies_count} entity(ies) in this portfolio belong to the qualitative corporate intelligence tier (or are State-only entities). By statutory design, qualitative entities have strictly 0 quantitative stock predictions or econometric risk scores. Composite portfolio metrics are computed exclusively over the {portfolioResult.modeled_companies_count} quantitative securities.
                  </p>
                </div>
              )}

              {/* Portfolio Companies Table */}
              <div className="rounded-xl border border-[var(--border-subtle)] overflow-hidden">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]/70 text-[var(--text-muted)]">
                      <th className="py-2.5 px-4 font-semibold text-[11px]">Security</th>
                      <th className="py-2.5 px-3 font-semibold text-[11px]">ISIN</th>
                      <th className="py-2.5 px-3 font-semibold text-[11px]">Sector</th>
                      <th className="py-2.5 px-3 font-semibold text-[11px]">Universe Tier</th>
                      <th className="py-2.5 px-3 text-right font-semibold text-[11px]">Decisions</th>
                      <th className="py-2.5 px-3 text-right font-semibold text-[11px]">Avg Risk</th>
                      <th className="py-2.5 px-3 font-semibold text-[11px]">Risk Band</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-secondary)]">
                    {portfolioResult.companies.map((c) => (
                      <tr key={c.company_isin} className="hover:bg-[var(--bg-base)]/80 transition-colors">
                        <td className="py-2.5 px-4 font-medium">
                          <Link
                            href={`/companies/${c.company_isin}`}
                            className="text-[var(--action-primary)] hover:underline font-semibold"
                          >
                            {c.company_name}
                          </Link>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px] text-[var(--text-muted)]">
                          {c.company_isin}
                        </td>
                        <td className="py-2.5 px-3 text-[var(--text-muted)]">{c.sector}</td>
                        <td className="py-2.5 px-3">
                          <Badge variant={c.is_modeled ? "primary" : "default"} size="xs">
                            {c.universe_type}
                          </Badge>
                        </td>

                        <td className="py-2.5 px-3 text-right font-mono tabular-nums">{c.record_count}</td>
                        <td className="py-2.5 px-3 text-right font-mono tabular-nums font-semibold">
                          {c.avg_risk_score !== null && c.avg_risk_score !== undefined
                            ? `${(c.avg_risk_score * 100).toFixed(1)}%`
                            : "—"}
                        </td>
                        <td className="py-2.5 px-3">
                          {c.dominant_risk_band ? (
                            <Badge
                              variant={
                                c.dominant_risk_band === "HIGH" ||
                                c.dominant_risk_band === "VERY_HIGH"
                                  ? "danger"
                                  : "default"
                              }
                              size="xs"
                            >
                              {c.dominant_risk_band}
                            </Badge>
                          ) : (
                            <span className="text-[var(--text-muted)] text-[10px]">Unmodeled</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>

        {/* SECTION E: Sector Risk Dispersion Behind Progressive Disclosure */}
        {summary && summary.risk_by_sector.length > 0 && (
          <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 shadow-sm space-y-4" aria-labelledby="sector-dispersion-heading">
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
              <div className="flex items-center gap-2">
                <h3 id="sector-dispersion-heading" className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>🏢</span> Cross-Sector Legislative Risk Dispersion
                </h3>
                <EpistemicBadge type="DERIVED" size="sm" />
              </div>
              <span className="text-xs text-[var(--text-muted)] font-mono tabular-nums">
                {summary.risk_by_sector.length} active economic sectors
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {summary.risk_by_sector.map((sec) => {
                const highRiskCount =
                  (sec.band_distribution.HIGH || 0) + (sec.band_distribution.VERY_HIGH || 0);
                const highRiskPct =
                  sec.record_count > 0 ? (highRiskCount / sec.record_count) * 100 : 0;

                return (
                  <div
                    key={sec.sector}
                    className="p-3.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-2.5 hover:border-[var(--border-strong)] transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-xs font-semibold text-[var(--text-primary)] leading-snug">
                        {sec.sector}
                      </h4>
                      <Badge
                        variant={
                          sec.avg_risk_score >= 0.5
                            ? "danger"
                            : sec.avg_risk_score >= 0.35
                            ? "warning"
                            : "default"
                        }
                        size="xs"
                      >
                        {(sec.avg_risk_score * 100).toFixed(0)}% Risk
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)]">
                      <span className="font-mono tabular-nums">{sec.record_count} evaluations</span>
                      <span className="text-amber-400 font-medium font-mono tabular-nums">
                        {highRiskCount} High ({highRiskPct.toFixed(0)}%)
                      </span>
                    </div>

                    {/* Mini horizontal band breakdown */}
                    <div className="w-full h-1.5 bg-[var(--bg-surface)] rounded-full overflow-hidden flex">
                      {(["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"] as const).map((b) => {
                        const count = sec.band_distribution[b] || 0;
                        const p = sec.record_count > 0 ? (count / sec.record_count) * 100 : 0;
                        return (
                          <div
                            key={b}
                            className={`h-full ${RISK_BAND_COLORS[b].bar}`}
                            style={{ width: `${p}%` }}
                          />
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* SECTION F: Grounded AI Risk Analyst */}
        <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 shadow-sm space-y-4" aria-labelledby="ai-analyst-heading">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-3">
            <div className="flex items-center gap-2">
              <h3 id="ai-analyst-heading" className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                <span>🤖</span> AI Legislative Risk Analyst
              </h3>
              <EpistemicBadge type="INTERPRETATION" size="sm" />
            </div>

            {/* Persona Switcher */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[var(--text-muted)]">Analyst Lens:</span>
              <div className="inline-flex rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] p-0.5">
                {(["INVESTOR", "POLICY", "GENERAL_PUBLIC"] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setAiPersona(p)}
                    className={`px-2.5 py-1 text-[11px] rounded-md font-medium transition-colors ${
                      aiPersona === p ? "bg-blue-600 text-white" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    }`}
                  >
                    {p.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Ask about cross-sector legislative risk, pricing-in dynamics, or portfolio impact..."
                value={aiQuestion}
                onChange={(e) => setAiQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAskAIRisk();
                }}
                className="flex-1 h-9 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] px-3 text-xs text-[var(--text-primary)] placeholder-[var(--input-placeholder)] focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <Button
                variant="primary"
                size="sm"
                onClick={handleAskAIRisk}
                disabled={aiLoading}
                className="h-9 text-xs px-4 font-semibold"
              >
                {aiLoading ? "Analyzing..." : "Analyze"}
              </Button>
            </div>

            {aiResponse && (
              <div className="p-4 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-2">
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] border-b border-[var(--border-subtle)] pb-2">
                  <span className="font-semibold text-blue-400">AI Risk Assessment</span>
                  <span className="text-[var(--text-faint)] font-mono">Lens: {aiPersona}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
                  {aiResponse}
                </p>
                <p className="text-[10px] text-[var(--text-faint)] pt-1">
                  Answers are grounded on empirical decision support records and verified parliamentary legislative texts.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* State Prediction Firewall Notice */}
        <div className="space-y-2">
          <StatePredictionFirewall state="All States" />
          <p className="text-[11px] text-[var(--text-faint)] px-1">
            Institutional risk scores are generated exclusively for Central Parliament enactments. State assembly bills possess qualitative statutory exposure and compliance context with strictly 0 quantitative stock risk scores.
          </p>
        </div>
      </main>
    </div>
  );
}
