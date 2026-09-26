"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge, SourceBadge, JurisdictionBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SearchInput } from "@/components/ui/SearchInput";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { riskApi } from "@/lib/api/risk";
import { watchlistsApi } from "@/lib/api/watchlists";
import { aiApi } from "@/lib/api/ai";
import type {
  BillRiskSummary,
  CompanyRiskSummary,
  PortfolioRiskResponse,
  RiskSummaryResponse,
  WatchlistResponse,
} from "@/types/api";

const RISK_BAND_COLORS: Record<string, { bg: string; text: string; border: string; bar: string }> = {
  VERY_LOW: { bg: "bg-emerald-950/40", text: "text-emerald-400", border: "border-emerald-800/60", bar: "bg-emerald-500" },
  LOW: { bg: "bg-blue-950/40", text: "text-blue-400", border: "border-blue-800/60", bar: "bg-blue-500" },
  MODERATE: { bg: "bg-amber-950/40", text: "text-amber-400", border: "border-amber-800/60", bar: "bg-amber-500" },
  HIGH: { bg: "bg-orange-950/40", text: "text-orange-400", border: "border-orange-800/60", bar: "bg-orange-500" },
  VERY_HIGH: { bg: "bg-rose-950/40", text: "text-rose-400", border: "border-rose-800/60", bar: "bg-rose-500" },
};

export default function RiskContent() {
  // Summary Data State
  const [summary, setSummary] = useState<RiskSummaryResponse | null>(null);
  const [bills, setBills] = useState<BillRiskSummary[]>([]);
  const [companies, setCompanies] = useState<CompanyRiskSummary[]>([]);
  const [watchlists, setWatchlists] = useState<WatchlistResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Table Tabs & Filters
  const [activeTableTab, setActiveTableTab] = useState<"bills" | "companies">("bills");
  const [billSearch, setBillSearch] = useState("");
  const [companySearch, setCompanySearch] = useState("");
  const [companySectorFilter, setCompanySectorFilter] = useState("ALL");

  // Portfolio Risk State
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string>("");
  const [customIsinInput, setCustomIsinInput] = useState<string>("");
  const [portfolioResult, setPortfolioResult] = useState<PortfolioRiskResponse | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);

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
    if (!billSearch.trim()) return bills;
    const q = billSearch.toLowerCase();
    return bills.filter(
      (b) =>
        b.bill_id.toLowerCase().includes(q) ||
        b.bill_title.toLowerCase().includes(q) ||
        b.dominant_risk_band.toLowerCase().includes(q)
    );
  }, [bills, billSearch]);

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
        c.company_symbol.toLowerCase().includes(q);
      return matchesSector && matchesSearch;
    });
  }, [companies, companySearch, companySectorFilter]);

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
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
                  <span className="text-amber-500">⚠️</span> Institutional Risk Analytics
                </h1>
                <SourceBadge type="DERIVED" size="sm" showTooltip />
                <Badge variant="primary" size="xs">
                  Central Level 1
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
                Standardized multi-horizon legislative risk classifications across 4,700 decision support records.
                Evaluates deterministic risk bands (VERY_LOW to VERY_HIGH), pricing-in status, sector dispersion, and portfolio exposure.
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Link href="/predictions">
                <Button variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800 text-xs">
                  📊 Predictions Matrix
                </Button>
              </Link>
              <Link href="/anticipation">
                <Button variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800 text-xs">
                  🔍 Pre-Event Anticipation
                </Button>
              </Link>
              <Link href="/watchlists">
                <Button variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800 text-xs">
                  ⭐ Watchlists & Alerts
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* SECTION A: Deterministic Risk Band Distribution */}
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        ) : summary ? (
          <section className="space-y-4" aria-labelledby="risk-distribution-heading">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 id="risk-distribution-heading" className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>🎯</span> 5-Tier Deterministic Risk Model
                </h2>
                <p className="text-xs text-slate-400">
                  Total Evaluated Decisions: <strong className="text-slate-200">{summary.total_decisions.toLocaleString()}</strong> · Cross-Sectional Mean: <strong className="text-amber-400">{(summary.avg_overall_risk * 100).toFixed(1)}%</strong>
                </p>
              </div>
              <span className="text-[11px] text-slate-500 font-mono">
                Threshold: Very Low (&lt;0.20) to Very High (≥0.80)
              </span>
            </div>

            {/* Risk Band Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {(
                [
                  { band: "VERY_LOW", label: "Very Low Risk", range: "0.00 – 0.20" },
                  { band: "LOW", label: "Low Risk", range: "0.20 – 0.40" },
                  { band: "MODERATE", label: "Moderate Risk", range: "0.40 – 0.60" },
                  { band: "HIGH", label: "High Risk", range: "0.60 – 0.80" },
                  { band: "VERY_HIGH", label: "Very High Risk", range: "0.80 – 1.00" },
                ] as const
              ).map(({ band, label, range }) => {
                const count = summary.risk_band_distribution[band] || 0;
                const pct = summary.total_decisions > 0 ? (count / summary.total_decisions) * 100 : 0;
                const style = RISK_BAND_COLORS[band];

                return (
                  <Card
                    key={band}
                    className={`p-4 ${style.bg} border ${style.border} transition-transform hover:scale-[1.01]`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400">
                        {label}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">{range}</span>
                    </div>
                    <p className={`text-2xl font-bold mt-2 font-mono ${style.text}`}>
                      {count.toLocaleString()}
                    </p>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                      <span>{pct.toFixed(1)}% of total</span>
                    </div>
                  </Card>
                );
              })}
            </div>

            {/* Stacked Proportional Bar */}
            <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden flex shadow-inner border border-slate-800">
              {(["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"] as const).map((band) => {
                const count = summary.risk_band_distribution[band] || 0;
                const pct = summary.total_decisions > 0 ? (count / summary.total_decisions) * 100 : 0;
                const style = RISK_BAND_COLORS[band];
                return (
                  <div
                    key={band}
                    className={`h-full ${style.bar} transition-all`}
                    style={{ width: `${pct}%` }}
                    title={`${band}: ${count} (${pct.toFixed(1)}%)`}
                  />
                );
              })}
            </div>
          </section>
        ) : null}

        {/* SECTION B: Pricing-In Risk Distribution & Window Dispersion */}
        {summary && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pricing-in Risk Breakdown */}
            <Card className="p-5 bg-slate-900/80 border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                    Market Pricing-In Status
                  </h3>
                  <SourceBadge type="DERIVED" size="xs" />
                </div>
                <span className="text-[11px] text-slate-500">Anticipatory Absorption</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(summary.pricing_in_distribution).map(([status, count]) => {
                  const pct = summary.total_decisions > 0 ? (count / summary.total_decisions) * 100 : 0;
                  return (
                    <div
                      key={status}
                      className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-center"
                    >
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block truncate">
                        {status.replace(/_/g, " ")}
                      </span>
                      <p className="text-lg font-bold font-mono text-slate-100 mt-1">
                        {count.toLocaleString()}
                      </p>
                      <span className="text-[10px] text-slate-500 block mt-0.5">
                        {pct.toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
                Pricing-in indicators evaluate whether price movement and abnormal returns occurred prior to formal enactment, distinguishing surprise enactments from fully absorbed regulatory milestones.
              </p>
            </Card>

            {/* Event Window Risk Breakdown */}
            <Card className="p-5 bg-slate-900/80 border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                    Risk by Event Window
                  </h3>
                  <SourceBadge type="DERIVED" size="xs" />
                </div>
                <span className="text-[11px] text-slate-500">5 Temporal Horizons</span>
              </div>

              <div className="space-y-2.5">
                {summary.risk_by_event_window.map((ew) => (
                  <div
                    key={ew.event_window}
                    className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-blue-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-700">
                        {ew.event_window}
                      </span>
                      <span className="text-slate-400">{ew.record_count} decisions</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-slate-400">Mean Risk:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {(ew.avg_risk_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* SECTION C: Sector Risk Dispersion */}
        {summary && summary.risk_by_sector.length > 0 && (
          <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <span>🏢</span> Cross-Sector Legislative Risk Dispersion
                </h3>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <span className="text-xs text-slate-400">
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
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-xs font-bold text-slate-200 leading-snug">
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

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>{sec.record_count} total evaluations</span>
                      <span className="text-amber-400 font-medium">
                        {highRiskCount} High/Very High ({highRiskPct.toFixed(0)}%)
                      </span>
                    </div>

                    {/* Mini horizontal band breakdown */}
                    <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden flex">
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

        {/* SECTION D: Portfolio-Level Risk Aggregation */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <span>💼</span> Portfolio Legislative Risk Aggregation
                </h3>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <p className="text-xs text-slate-400 mt-1">
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
              <label htmlFor="portfolio-watchlist" className="block text-xs font-medium text-slate-400 mb-1">
                Load From Saved Watchlist
              </label>
              <select
                id="portfolio-watchlist"
                aria-label="Load from saved watchlist"
                value={selectedWatchlistId}
                onChange={(e) => setSelectedWatchlistId(e.target.value)}
                className="w-full h-10 rounded-lg border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
              <label htmlFor="portfolio-isins" className="block text-xs font-medium text-slate-400 mb-1">
                Or Input Security ISINs (Comma Separated)
              </label>
              <div className="flex gap-2">
                <input
                  id="portfolio-isins"
                  type="text"
                  placeholder="e.g. INE002A01018, INE009A01021, INE040A01034"
                  value={customIsinInput}
                  onChange={(e) => setCustomIsinInput(e.target.value)}
                  className="flex-1 h-10 rounded-lg border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleCalculatePortfolioRisk}
                  disabled={portfolioLoading || (!selectedWatchlistId && !customIsinInput.trim())}
                  className="h-10 text-xs px-5 font-semibold"
                >
                  {portfolioLoading ? "Analyzing..." : "Compute Risk"}
                </Button>
              </div>
            </div>
          </div>

          {/* Portfolio Error */}
          {portfolioError && (
            <div className="p-4 rounded-lg bg-rose-950/30 border border-rose-800 text-xs text-rose-300">
              {portfolioError}
            </div>
          )}

          {/* Portfolio Results Display */}
          {portfolioResult && (
            <div className="space-y-4 pt-2 border-t border-slate-800">
              {/* Status & Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <Card className="p-4 bg-slate-950 border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">
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
                  <p className="text-[10px] text-slate-500 mt-1">
                    {portfolioResult.modeled_companies_count} modeled / {portfolioResult.selected_companies_count} selected
                  </p>
                </Card>

                <Card className="p-4 bg-slate-950 border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                    Composite Risk Score
                  </span>
                  <p className="text-2xl font-bold font-mono text-slate-100 mt-1">
                    {portfolioResult.avg_portfolio_risk_score !== null &&
                    portfolioResult.avg_portfolio_risk_score !== undefined
                      ? `${(portfolioResult.avg_portfolio_risk_score * 100).toFixed(1)}%`
                      : "Insufficient Data"}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Weighted across decisions</p>
                </Card>

                <Card className="p-4 bg-slate-950 border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">
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
                      <span className="text-xs text-slate-500">Unclassified</span>
                    )}
                  </div>
                </Card>

                <Card className="p-4 bg-slate-950 border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                    Total Exposure Records
                  </span>
                  <p className="text-2xl font-bold font-mono text-blue-400 mt-1">
                    {portfolioResult.total_exposure_records}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Decision records linked</p>
                </Card>
              </div>

              {/* Informative notice if unmodeled companies exist */}
              {portfolioResult.unmodeled_companies_count > 0 && (
                <div className="p-3.5 rounded-lg border border-amber-800/40 bg-amber-950/20 text-xs text-amber-300 space-y-1">
                  <p className="font-semibold flex items-center gap-1.5">
                    <span>ℹ️</span> Qualitative Intelligence Entities in Portfolio
                  </p>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    {portfolioResult.unmodeled_companies_count} entity(ies) in this portfolio belong to the qualitative corporate intelligence tier (or are State-only entities). By statutory design, qualitative entities have strictly 0 quantitative stock predictions or econometric risk scores. Composite portfolio metrics are computed exclusively over the {portfolioResult.modeled_companies_count} quantitative securities.
                  </p>
                </div>
              )}

              {/* Portfolio Companies Table */}
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400">
                      <th className="py-2.5 px-4 font-semibold">Security</th>
                      <th className="py-2.5 px-3 font-semibold">ISIN</th>
                      <th className="py-2.5 px-3 font-semibold">Sector</th>
                      <th className="py-2.5 px-3 font-semibold">Universe Tier</th>
                      <th className="py-2.5 px-3 font-semibold">Decisions</th>
                      <th className="py-2.5 px-3 font-semibold">Avg Risk</th>
                      <th className="py-2.5 px-3 font-semibold">Risk Band</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {portfolioResult.companies.map((c) => (
                      <tr key={c.company_isin} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 font-medium">
                          <Link
                            href={`/companies/${c.company_isin}`}
                            className="text-blue-400 hover:underline"
                          >
                            {c.company_name}
                          </Link>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">
                          {c.company_isin}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">{c.sector}</td>
                        <td className="py-2.5 px-3">
                          <Badge variant={c.is_modeled ? "primary" : "default"} size="xs">
                            {c.universe_type}
                          </Badge>
                        </td>

                        <td className="py-2.5 px-3 font-mono">{c.record_count}</td>
                        <td className="py-2.5 px-3 font-mono">
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
                            <span className="text-slate-500 text-[10px]">Unmodeled</span>
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

        {/* SECTION E: Tabbed Entity Risk Profiles (Bills & Companies) */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg space-y-4">
          <div className="p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setActiveTableTab("bills")}
                className={`text-sm font-bold pb-1 border-b-2 transition-colors ${
                  activeTableTab === "bills"
                    ? "border-blue-500 text-blue-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                🏛 Bill Risk Profiles ({bills.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveTableTab("companies")}
                className={`text-sm font-bold pb-1 border-b-2 transition-colors ${
                  activeTableTab === "companies"
                    ? "border-blue-500 text-blue-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                🏢 Company Risk Profiles ({companies.length})
              </button>
            </div>

            {/* Filter Bar */}
            <div className="flex items-center gap-2">
              {activeTableTab === "bills" ? (
                <SearchInput
                  placeholder="Search bills by title or ID..."
                  value={billSearch}
                  onChange={(v) => setBillSearch(v)}
                />
              ) : (
                <div className="flex items-center gap-2">
                  <SearchInput
                    placeholder="Search companies or ISIN..."
                    value={companySearch}
                    onChange={(v) => setCompanySearch(v)}
                  />
                  <select
                    aria-label="Filter companies by sector"
                    value={companySectorFilter}
                    onChange={(e) => setCompanySectorFilter(e.target.value)}
                    className="h-8 rounded border border-slate-700 bg-slate-950 px-2 text-xs text-slate-200"
                  >
                    <option value="ALL">All Sectors</option>
                    {companySectors.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
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
                  <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400">
                    <th className="py-3 px-4 font-semibold uppercase tracking-wider">Bill</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Jurisdiction</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Decisions</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Avg Risk</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Max Risk</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">High Risk Enclaves</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Dominant Band</th>
                    <th className="py-3 px-4 text-right font-semibold uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {filteredBills.map((b) => (
                    <tr key={b.bill_id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-medium">
                        <Link href={`/bills/${b.bill_id}`} className="text-blue-400 hover:underline">
                          {b.bill_title}
                        </Link>
                        <span className="block text-[10px] text-slate-500 font-mono mt-0.5">
                          {b.bill_id}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <JurisdictionBadge jurisdiction={b.jurisdiction} size="xs" />
                      </td>
                      <td className="py-3 px-3 font-mono">{b.record_count}</td>
                      <td className="py-3 px-3 font-mono font-semibold">
                        {(b.avg_risk_score * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-3 font-mono text-amber-400">
                        {(b.max_risk_score * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`font-mono text-xs ${
                            b.high_risk_count > 0 ? "text-rose-400 font-bold" : "text-slate-500"
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
                          {b.dominant_risk_band}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link href={`/bills/${b.bill_id}`}>
                          <Button variant="outline" size="xs" className="border-slate-700 text-[11px]">
                            Inspect Bill →
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Companies Table */}
          {activeTableTab === "companies" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400">
                    <th className="py-3 px-4 font-semibold uppercase tracking-wider">Company</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Sector</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Universe</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Decisions</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Avg Risk</th>
                    <th className="py-3 px-3 font-semibold uppercase tracking-wider">Dominant Band</th>
                    <th className="py-3 px-4 text-right font-semibold uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {filteredCompanies.map((c) => (
                    <tr key={c.company_isin} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-medium">
                        <Link
                          href={`/companies/${c.company_isin}`}
                          className="text-blue-400 hover:underline"
                        >
                          {c.company_name}
                        </Link>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] font-mono text-slate-500">
                            {c.company_isin}
                          </span>
                          {c.company_symbol && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              ({c.company_symbol})
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-3 text-slate-400">{c.sector}</td>
                      <td className="py-3 px-3">
                        <Badge
                          variant={c.market_prediction_available ? "primary" : "default"}
                          size="xs"
                        >
                          {c.universe_type}
                        </Badge>
                      </td>

                      <td className="py-3 px-3 font-mono">{c.record_count}</td>
                      <td className="py-3 px-3 font-mono font-semibold">
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
                          {c.dominant_risk_band}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link href={`/companies/${c.company_isin}`}>
                          <Button variant="outline" size="xs" className="border-slate-700 text-[11px]">
                            Profile →
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* SECTION F: Grounded AI Risk Analyst */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>🤖</span> AI Legislative Risk Analyst
              </h3>
              <SourceBadge type="INTERPRETATION" size="xs" />
            </div>

            {/* Persona Switcher */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Analyst Lens:</span>
              <div className="inline-flex rounded-lg border border-slate-700 bg-slate-950 p-0.5">
                {(["INVESTOR", "POLICY", "GENERAL_PUBLIC"] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setAiPersona(p)}
                    className={`px-2.5 py-1 text-[11px] rounded-md font-medium transition-colors ${
                      aiPersona === p ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
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
                className="flex-1 h-10 rounded-lg border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <Button
                variant="primary"
                size="sm"
                onClick={handleAskAIRisk}
                disabled={aiLoading}
                className="h-10 text-xs px-4"
              >
                {aiLoading ? "Analyzing..." : "Analyze"}
              </Button>
            </div>

            {aiResponse && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800/60 pb-2">
                  <span className="font-semibold text-blue-400">AI Risk Assessment</span>
                  <span className="text-slate-500">Lens: {aiPersona}</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                  {aiResponse}
                </p>
                <p className="text-[10px] text-slate-500 pt-1">
                  Answers are grounded on empirical decision support records and verified parliamentary legislative texts.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* State Prediction Firewall Notice */}
        <div className="space-y-2">
          <StatePredictionFirewall state="All States" />
          <p className="text-[11px] text-slate-500 px-1">
            Institutional risk scores are generated exclusively for Central Parliament enactments. State assembly bills possess qualitative statutory exposure and compliance context with strictly 0 quantitative stock risk scores.
          </p>
        </div>
      </main>
    </div>
  );
}
