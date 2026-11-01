"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Badge, SourceBadge, JurisdictionBadge } from "@/components/ui/Badge";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { Button } from "@/components/ui/Button";
import { SearchInput } from "@/components/ui/SearchInput";
import { Pagination } from "@/components/ui/Pagination";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { anticipationApi } from "@/lib/api/anticipation";
import { aiApi } from "@/lib/api/ai";
import { AnticipationEvidenceSection } from "@/components/anticipation/AnticipationEvidenceSection";
import type {
  AnticipationItem,
  AnticipationSummaryResponse,
  PaginatedResponse,
} from "@/types/api";

const MANDATORY_LEGAL_DISCLAIMER =
  "Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law.";

const TIER_COLORS: Record<string, { bg: string; text: string; border: string; bar: string; glyph: string }> = {
  NO_EVIDENCE: { bg: "bg-[var(--bg-card)]", text: "text-[var(--text-muted)]", border: "border-[var(--border-subtle)]", bar: "bg-slate-500", glyph: "○" },
  WEAK_EVIDENCE: { bg: "bg-blue-950/20", text: "text-blue-400", border: "border-blue-800/40", bar: "bg-blue-500", glyph: "◔" },
  MODERATE_EVIDENCE: { bg: "bg-amber-950/20", text: "text-amber-400", border: "border-amber-800/40", bar: "bg-amber-500", glyph: "◑" },
  STRONG_EVIDENCE: { bg: "bg-indigo-950/20", text: "text-indigo-400", border: "border-indigo-800/40", bar: "bg-indigo-500", glyph: "●" },
};

export default function AnticipationContent() {
  const searchParams = useSearchParams();

  // Data state
  const [summary, setSummary] = useState<AnticipationSummaryResponse | null>(null);
  const [tableData, setTableData] = useState<PaginatedResponse<AnticipationItem> | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [page, setPage] = useState(1);
  const [billQuery, setBillQuery] = useState(searchParams.get("bill_id") || "");
  const [companyQuery, setCompanyQuery] = useState(searchParams.get("company_isin") || "");
  const [selectedTier, setSelectedTier] = useState("ALL");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [selectedSector, setSelectedSector] = useState("ALL");

  // Selected pair for active evidence inspection
  const [activeEvidencePair, setActiveEvidencePair] = useState<{
    billId: string;
    companyIsin?: string;
    companyName?: string;
  }>({
    billId: "the-banking-laws-amendment-bill-2024",
    companyIsin: "INE002A01018",
    companyName: "State Bank of India",
  });

  // AI Analyst state
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiPersona, setAiPersona] = useState<"INVESTOR" | "POLICY" | "GENERAL_PUBLIC">("INVESTOR");

  // Fetch summary once
  useEffect(() => {
    setSummaryLoading(true);
    anticipationApi
      .getAnticipationSummary()
      .then((res) => {
        setSummary(res);
        setSummaryLoading(false);
      })
      .catch((err) => {
        setError(err?.message || "Failed to load anticipation summary.");
        setSummaryLoading(false);
      });
  }, []);

  // Fetch table data on filter change
  const fetchTableData = () => {
    setTableLoading(true);
    const params: Parameters<typeof anticipationApi.listAnticipation>[0] = {
      page,
      limit: 25,
      bill_id: billQuery.trim() || undefined,
      company_isin: companyQuery.trim().toUpperCase() || undefined,
      classification: selectedTier !== "ALL" ? selectedTier : undefined,
      flagged_only: flaggedOnly ? true : undefined,
      sector: selectedSector !== "ALL" ? selectedSector : undefined,
    };

    anticipationApi
      .listAnticipation(params)
      .then((res) => {
        setTableData(res);
        setTableLoading(false);
        // If results exist and active pair is default, pick the first row for inspection
        if (res && res.items && res.items.length > 0 && billQuery.trim()) {
          const first = res.items[0];
          setActiveEvidencePair({
            billId: first.bill_id,
            companyIsin: first.company_isin,
            companyName: first.company_name || undefined,
          });
        }
      })
      .catch((err) => {
        setError(err?.message || "Failed to query anticipation records.");
        setTableLoading(false);
      });
  };

  useEffect(() => {
    fetchTableData();
  }, [page, billQuery, companyQuery, selectedTier, flaggedOnly, selectedSector]);

  // Sector list from summary
  const sectorsList = useMemo(() => {
    if (!summary?.sector_distribution) return [];
    return summary.sector_distribution.map((s) => s.sector).sort();
  }, [summary]);

  // Grounded AI Q&A
  const handleAskAI = () => {
    setAiLoading(true);
    const q =
      aiQuestion.trim() ||
      "Explain the econometric concept of legislative information diffusion and the Anticipation Paradox across Indian equity markets.";
    aiApi
      .ask({
        question: q,
        context_type: "comparison",
        context_id: "anticipation_diffusion_summary",
        persona: aiPersona,
      })
      .then((res) => {
        setAiResponse(res.content);
        setAiLoading(false);
      })
      .catch(() => {
        setAiResponse(
          "Pre-event information diffusion assesses whether abnormal price or trading volume movements preceded formal parliamentary introduction. The Anticipation Paradox demonstrates that heavily anticipated legislative enactments often exhibit muted post-announcement abnormal returns, as regulatory implications were already absorbed through public consultations and committee hearings."
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
                <span className="text-[var(--color-model)] font-mono text-base" aria-hidden="true">🔍</span>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                  Pre-Event Information Diffusion
                </h1>
                <EpistemicBadge type="DERIVED" size="sm" />
                <Badge variant="primary" size="xs">
                  Central Level 1
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1 max-w-3xl leading-relaxed">
                Evaluates pre-introduction market diffusion across 940 bill-company pairs (20 Central Parliament bills × 47 listed securities).
                Measures pre-event abnormal returns and volume ratios across 5 temporal pre-event trading windows.
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Link href="/predictions">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  📊 Predictions
                </Button>
              </Link>
              <Link href="/risk">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  ⚠️ Risk Analytics
                </Button>
              </Link>
              <Link href="/explorer">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  🏛 Legislative Explorer
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-8">
        {/* MANDATORY VERBATIM STATUTORY LEGAL DISCLAIMER (TOP) */}
        <section aria-label="Statutory Research Notice" className="p-4 rounded-xl border border-indigo-900/40 bg-indigo-950/20 text-indigo-200 text-xs flex items-start gap-3 shadow-sm">
          <span className="text-base flex-shrink-0 mt-0.5" aria-hidden="true">⚖️</span>
          <div className="space-y-1">
            <p className="font-semibold text-indigo-300 uppercase tracking-wider text-[10px] flex items-center gap-2">
              <span>Statutory Research Notice & Regulatory Disclaimer</span>
              <span className="text-[9px] font-mono text-indigo-400/80">[RESEARCH_INVARIANT]</span>
            </p>
            <p className="leading-relaxed text-[11px] font-medium text-[var(--text-primary)]">
              &ldquo;{MANDATORY_LEGAL_DISCLAIMER}&rdquo;
            </p>
          </div>
        </section>

        {/* SECTION A: Verified Coverage Baseline & Key Metrics */}
        {summaryLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        ) : summary ? (
          <section aria-labelledby="anticipation-metrics">
            <h2 id="anticipation-metrics" className="sr-only">
              Coverage Baseline
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <Card className="p-4 bg-[var(--bg-card)] border-[var(--border-default)] shadow-sm">
                <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                  Evaluated Pairs
                </span>
                <p className="text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                  {summary.total_pairs}
                </p>
                <p className="text-[10px] text-[var(--text-faint)] mt-0.5">20 Bills × 47 Securities</p>
              </Card>

              <Card className="p-4 bg-[var(--bg-card)] border-[var(--border-default)] shadow-sm">
                <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                  Diffusion Flags
                </span>
                <p className="text-2xl font-bold font-mono tabular-nums text-indigo-400 mt-1">
                  {summary.flagged_pairs_count}
                </p>
                <p className="text-[10px] text-[var(--text-faint)] mt-0.5 font-mono tabular-nums">
                  {((summary.flagged_pairs_count / summary.total_pairs) * 100).toFixed(1)}% of evaluated pairs
                </p>
              </Card>

              <Card className="p-4 bg-[var(--bg-card)] border-[var(--border-default)] shadow-sm">
                <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                  Mean Anticipation Score
                </span>
                <p className="text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                  {(summary.avg_anticipation_score * 100).toFixed(1)}%
                </p>
                <p className="text-[10px] text-[var(--text-faint)] mt-0.5">Composite diffusion index</p>
              </Card>

              <Card className="p-4 bg-[var(--bg-card)] border-[var(--border-default)] shadow-sm">
                <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                  Mean Market Signal
                </span>
                <p className="text-2xl font-bold font-mono tabular-nums text-amber-400 mt-1">
                  {(summary.avg_market_signal * 100).toFixed(1)}%
                </p>
                <p className="text-[10px] text-[var(--text-faint)] mt-0.5">Pre-event volume ratio</p>
              </Card>

              <Card className="p-4 bg-[var(--bg-card)] border-[var(--border-default)] shadow-sm">
                <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
                  Mean Info Signal
                </span>
                <p className="text-2xl font-bold font-mono tabular-nums text-blue-400 mt-1">
                  {(summary.avg_information_signal * 100).toFixed(1)}%
                </p>
                <p className="text-[10px] text-[var(--text-faint)] mt-0.5">Public news diffusion</p>
              </Card>
            </div>
          </section>
        ) : null}

        {/* SECTION B: 4 Neutral Classification Tiers */}
        {summary && (
          <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 shadow-sm space-y-4" aria-labelledby="diffusion-spectrum-heading">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-3">
              <div>
                <h3 id="diffusion-spectrum-heading" className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                  <span>📊</span> 4-Tier Neutral Information Diffusion Spectrum
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Classifies pairs into neutral statistical bands based on composite pre-event indicators.
                </p>
              </div>
              <span className="text-[11px] text-[var(--text-faint)] font-mono">
                No Evidence (&lt;0.25) · Weak (0.25–0.50) · Moderate (0.50–0.75) · Strong (≥0.75)
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {(
                [
                  { tier: "NO_EVIDENCE", label: "No Evidence", range: "0.00 – 0.25", desc: "Minimal or zero pre-event deviation" },
                  { tier: "WEAK_EVIDENCE", label: "Weak Evidence", range: "0.25 – 0.50", desc: "Slight pre-announcement volume uptick" },
                  { tier: "MODERATE_EVIDENCE", label: "Moderate Evidence", range: "0.50 – 0.75", desc: "Observable pre-event abnormal returns" },
                  { tier: "STRONG_EVIDENCE", label: "Strong Evidence", range: "0.75 – 1.00", desc: "Significant pre-introduction diffusion" },
                ] as const
              ).map(({ tier, label, range, desc }) => {
                const count = summary.classification_distribution[tier] || 0;
                const pct = summary.total_pairs > 0 ? (count / summary.total_pairs) * 100 : 0;
                const style = TIER_COLORS[tier];

                return (
                  <Card
                    key={tier}
                    className={`p-4 ${style.bg} border ${style.border} transition-colors`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-[var(--text-muted)]">
                        {label}
                      </span>
                      <span className="text-[10px] font-mono text-[var(--text-faint)]">{range}</span>
                    </div>
                    <p className={`text-2xl font-bold mt-1.5 font-mono tabular-nums ${style.text}`}>
                      {count.toLocaleString()}
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)] mt-0.5 font-mono tabular-nums">{pct.toFixed(1)}% of total</p>
                    <p className="text-[10px] text-[var(--text-faint)] mt-1 leading-snug">{desc}</p>
                  </Card>
                );
              })}
            </div>

            {/* Stacked Proportional Bar */}
            <div className="w-full h-2.5 bg-[var(--bg-base)] rounded-full overflow-hidden flex shadow-inner border border-[var(--border-subtle)]">
              {(["NO_EVIDENCE", "WEAK_EVIDENCE", "MODERATE_EVIDENCE", "STRONG_EVIDENCE"] as const).map(
                (tier) => {
                  const count = summary.classification_distribution[tier] || 0;
                  const pct = summary.total_pairs > 0 ? (count / summary.total_pairs) * 100 : 0;
                  const style = TIER_COLORS[tier];
                  return (
                    <div
                      key={tier}
                      className={`h-full ${style.bar} transition-all`}
                      style={{ width: `${pct}%` }}
                      title={`${tier}: ${count} (${pct.toFixed(1)}%)`}
                    />
                  );
                }
              )}
            </div>
          </section>
        )}

        {/* SECTION C: Pre-Event Trading Windows CAR Statistics (Chronological Context) */}
        {summary && summary.window_stats_distribution.length > 0 && (
          <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 shadow-sm space-y-4" aria-labelledby="car-windows-heading">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-3">
              <div className="flex items-center gap-2">
                <h3 id="car-windows-heading" className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                  <span>⏱</span> Pre-Event Trading Windows CAR Statistics
                </h3>
                <EpistemicBadge type="DERIVED" size="sm" />
              </div>
              <span className="text-xs text-[var(--text-muted)] font-mono">
                Evaluating {summary.window_stats_distribution.length} pre-announcement horizons
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {summary.window_stats_distribution.map((ws) => (
                <div
                  key={ws.window}
                  className="p-3.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-2 hover:border-[var(--border-strong)] transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-[var(--color-model)] bg-[var(--color-model)]/10 px-2 py-0.5 rounded border border-[var(--color-model)]/30">
                      {ws.window}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono tabular-nums">{ws.observation_count} obs</span>
                  </div>

                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--text-muted)] text-[11px]">Mean CAR:</span>
                      <span
                        className={`font-mono tabular-nums font-bold text-xs ${
                          ws.mean_car > 0
                            ? "text-[var(--color-positive)]"
                            : ws.mean_car < 0
                            ? "text-[var(--color-negative)]"
                            : "text-[var(--text-secondary)]"
                        }`}
                      >
                        {(ws.mean_car * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--text-muted)] text-[11px]">Mean MAR:</span>
                      <span className="font-mono tabular-nums text-[var(--text-secondary)] text-xs">
                        {(ws.mean_mar * 100).toFixed(3)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--text-muted)] text-[11px]">Sig. Pairs:</span>
                      <span className="font-mono tabular-nums text-[var(--color-warning)] font-semibold text-xs">
                        {ws.significant_pairs_count}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* SECTION D: Top Flagged Diffusion Pairs */}
        {summary && summary.top_flagged_pairs.length > 0 && (
          <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 shadow-sm space-y-4" aria-labelledby="flagged-pairs-heading">
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
              <div className="flex items-center gap-2">
                <h3 id="flagged-pairs-heading" className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                  <span>🚩</span> Highest Diffusion Pairs
                </h3>
                <Badge variant="warning" size="xs">
                  Public Diffusion Focus
                </Badge>
              </div>
              <span className="text-xs text-[var(--text-muted)] font-mono">Top 10 Ranked by Score</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {summary.top_flagged_pairs.map((p) => (
                <div
                  key={`${p.bill_id}-${p.company_isin}`}
                  className="p-3.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-2 hover:border-[var(--border-strong)] transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <Link
                        href={`/companies/${p.company_isin}`}
                        className="text-xs font-bold text-[var(--text-primary)] hover:text-blue-400 hover:underline"
                      >
                        {p.company_name}
                      </Link>
                      <span className="block text-[10px] text-[var(--text-faint)] font-mono">
                        {p.company_isin} ({p.company_symbol})
                      </span>
                    </div>
                    <Badge variant="warning" size="xs">
                      {(p.anticipation_score * 100).toFixed(1)}%
                    </Badge>
                  </div>

                  <div className="text-xs text-[var(--text-muted)] truncate">
                    <span>Bill: </span>
                    <Link
                      href={`/bills/${p.bill_id}`}
                      className="text-blue-400 hover:underline font-medium"
                    >
                      {p.bill_title}
                    </Link>
                  </div>

                  {p.detected_signals.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {p.detected_signals.slice(0, 3).map((sig, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[var(--text-muted)] font-mono"
                        >
                          {sig}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs">
                    <button
                      type="button"
                      onClick={() => {
                        setActiveEvidencePair({
                          billId: p.bill_id,
                          companyIsin: p.company_isin,
                          companyName: p.company_name,
                        });
                        const el = document.getElementById("evidence-enrichment");
                        if (el) el.scrollIntoView({ behavior: "smooth" });
                      }}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      Inspect Evidence ↓
                    </button>
                    <Link
                      href={`/predictions?bill_id=${encodeURIComponent(p.bill_id)}&company_isin=${encodeURIComponent(p.company_isin)}`}
                      className="text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    >
                      View Model →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* SECTION E: Paginated Filterable Anticipation Matrix */}
        <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl overflow-hidden shadow-sm space-y-4" aria-labelledby="diffusion-matrix-heading">
          <div className="p-4 sm:p-5 border-b border-[var(--border-subtle)] space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 id="diffusion-matrix-heading" className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>📋</span> 940-Pair Information Diffusion Matrix
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Showing {tableData?.items.length ?? 0} of {tableData?.total ?? 0} evaluated Central bill-company pairs
                </p>
              </div>

              {/* Toggle: Flagged Only */}
              <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)] cursor-pointer bg-[var(--bg-base)] px-3 py-1.5 rounded-lg border border-[var(--border-default)]">
                <input
                  type="checkbox"
                  aria-label="Show Flagged Only (Scores ≥ 0.70)"
                  checked={flaggedOnly}
                  onChange={(e) => {
                    setFlaggedOnly(e.target.checked);
                    setPage(1);
                  }}
                  className="rounded border-[var(--border-strong)] bg-[var(--bg-card)] text-indigo-500 focus:ring-0"
                />
                <span className="font-medium">Show Flagged Only (Scores ≥ 0.70)</span>
              </label>
            </div>

            {/* Filter Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Filter by Bill ID
                </label>
                <SearchInput
                  placeholder="e.g. banking-laws..."
                  value={billQuery}
                  onChange={(v) => {
                    setBillQuery(v);
                    setPage(1);
                  }}
                  className="w-full h-8 text-xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Filter by ISIN / Symbol
                </label>
                <SearchInput
                  placeholder="e.g. INE002A01018..."
                  value={companyQuery}
                  onChange={(v) => {
                    setCompanyQuery(v);
                    setPage(1);
                  }}
                  className="w-full h-8 text-xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                  Classification Tier
                </label>
                <select
                  aria-label="Filter by classification tier"
                  value={selectedTier}
                  onChange={(e) => {
                    setSelectedTier(e.target.value);
                    setPage(1);
                  }}
                  className="w-full h-8 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] px-2.5 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="ALL">All Tiers (4 Tiers)</option>
                  <option value="NO_EVIDENCE">No Evidence (&lt; 0.25)</option>
                  <option value="WEAK_EVIDENCE">Weak Evidence (0.25 - 0.50)</option>
                  <option value="MODERATE_EVIDENCE">Moderate Evidence (0.50 - 0.75)</option>
                  <option value="STRONG_EVIDENCE">Strong Evidence (≥ 0.75)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">Sector</label>
                <select
                  aria-label="Filter by sector"
                  value={selectedSector}
                  onChange={(e) => {
                    setSelectedSector(e.target.value);
                    setPage(1);
                  }}
                  className="w-full h-8 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] px-2.5 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="ALL">All Sectors</option>
                  {sectorsList.map((sec) => (
                    <option key={sec} value={sec}>
                      {sec}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Loading Skeleton */}
          {tableLoading && (
            <div className="p-6 space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}

          {/* Table */}
          {!tableLoading && tableData && tableData.items.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]/60 text-[var(--text-muted)]">
                    <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Bill</th>
                    <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">Company</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Sector</th>
                    <th className="py-2.5 px-4 text-right font-semibold uppercase tracking-wider text-[11px]">
                      Anticipation Score
                    </th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Tier</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Market Sig</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Info Sig</th>
                    <th className="py-2.5 px-3 text-center font-semibold uppercase tracking-wider text-[11px]">Flag</th>
                    <th className="py-2.5 px-4 text-right font-semibold uppercase tracking-wider text-[11px]">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-secondary)]">
                  {tableData.items.map((item) => {
                    const style = TIER_COLORS[item.classification] || TIER_COLORS.NO_EVIDENCE;
                    const isSelected =
                      activeEvidencePair.billId === item.bill_id &&
                      activeEvidencePair.companyIsin === item.company_isin;

                    return (
                      <tr
                        key={`${item.bill_id}-${item.company_isin}`}
                        className={`hover:bg-[var(--bg-base)]/80 transition-colors ${
                          isSelected ? "bg-indigo-950/15" : ""
                        }`}
                      >
                        <td className="py-3 px-4 font-medium">
                          <Link
                            href={`/bills/${item.bill_id}`}
                            className="text-[var(--text-primary)] hover:text-[var(--action-primary)] font-semibold transition-colors"
                          >
                            {item.bill_title || item.bill_id.replace(/-/g, " ")}
                          </Link>
                          <span className="block text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                            {item.bill_id}
                          </span>
                        </td>

                        <td className="py-3 px-4">
                          <Link
                            href={`/companies/${item.company_isin}`}
                            className="text-[var(--text-primary)] hover:text-[var(--action-primary)] font-semibold transition-colors"
                          >
                            {item.company_name || item.company_symbol || item.company_isin}
                          </Link>
                          <span className="block text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                            {item.company_isin}
                          </span>
                        </td>

                        <td className="py-3 px-3 text-[var(--text-muted)]">{item.sector || "General"}</td>

                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-16 h-1.5 bg-[var(--bg-base)] rounded-full overflow-hidden border border-[var(--border-subtle)]">
                              <div
                                className={`h-full ${style.bar}`}
                                style={{ width: `${Math.min(100, item.anticipation_score * 100)}%` }}
                              />
                            </div>
                            <span className="font-mono tabular-nums text-xs font-semibold text-[var(--text-primary)]">
                              {(item.anticipation_score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>

                        <td className="py-3 px-3">
                          <Badge
                            variant={
                              item.classification === "STRONG_EVIDENCE"
                                ? "warning"
                                : item.classification === "MODERATE_EVIDENCE"
                                ? "primary"
                                : "default"
                            }
                            size="xs"
                          >
                            <span className="mr-1">{style.glyph}</span>
                            {item.classification.replace(/_/g, " ")}
                          </Badge>
                        </td>

                        <td className="py-3 px-3 text-right font-mono tabular-nums text-[var(--text-secondary)]">
                          {(item.market_signal_score * 100).toFixed(0)}%
                        </td>

                        <td className="py-3 px-3 text-right font-mono tabular-nums text-[var(--text-secondary)]">
                          {(item.information_signal_score * 100).toFixed(0)}%
                        </td>

                        <td className="py-3 px-3 text-center">
                          {item.anticipation_flag ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-[var(--color-warning)] border border-amber-500/30">
                              FLAG
                            </span>
                          ) : (
                            <span className="text-[10px] text-[var(--text-faint)]">—</span>
                          )}
                        </td>

                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Button
                              variant="outline"
                              size="xs"
                              onClick={() => {
                                setActiveEvidencePair({
                                  billId: item.bill_id,
                                  companyIsin: item.company_isin,
                                  companyName: item.company_name || undefined,
                                });
                                const el = document.getElementById("evidence-enrichment");
                                if (el) el.scrollIntoView({ behavior: "smooth" });
                              }}
                              className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-[10px] h-7 px-2"
                              title="Inspect chronological evidence & signals"
                            >
                              Evidence ↓
                            </Button>
                            <Link
                              href={`/predictions?bill_id=${encodeURIComponent(
                                item.bill_id
                              )}&company_isin=${encodeURIComponent(item.company_isin)}`}
                            >
                              <Button
                                variant="outline"
                                size="xs"
                                className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-[11px] h-7"
                              >
                                Predictions →
                              </Button>
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Empty State */}
          {!tableLoading && tableData && tableData.items.length === 0 && (
            <div className="p-12 text-center space-y-2">
              <span className="text-3xl" aria-hidden="true">🔍</span>
              <h4 className="text-sm font-semibold text-[var(--text-secondary)]">
                No anticipation records match filters
              </h4>
              <p className="text-xs text-[var(--text-faint)] max-w-sm mx-auto">
                Broaden your search terms or classification tier to view other evaluated pairs.
              </p>
            </div>
          )}

          {/* Pagination */}
          {tableData && tableData.pages > 1 && (
            <div className="p-4 border-t border-[var(--border-subtle)] flex justify-center">
              <Pagination
                page={page}
                pages={tableData.pages}
                total={tableData.total}
                limit={tableData.limit}
                onPageChange={(p) => setPage(p)}
              />
            </div>
          )}
        </section>

        {/* SECTION E2: Anticipation Evidence Enrichment & Chronology ("What was known, and when") */}
        <section id="evidence-enrichment" aria-labelledby="evidence-enrichment-title">
          <div className="p-4 bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl space-y-3 mb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-2.5">
              <div>
                <h3 id="evidence-enrichment-title" className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>⏳</span> Chronological Diffusion & Evidence Inspector
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Currently Grounded: <strong className="text-[var(--text-primary)] font-mono">{activeEvidencePair.billId}</strong> × <strong className="text-[var(--text-primary)] font-mono">{activeEvidencePair.companyIsin || "All Securities"}</strong>
                </p>
              </div>
              <span className="text-[11px] text-[var(--text-faint)] font-mono">
                Source Calibration: PRS Legislative, Gazette Notifications, GDELT & Google Trends
              </span>
            </div>

            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              <strong>Methodology & Limitations Note: </strong>
              Pre-event media indicators evaluate publicly published news articles, official parliamentary gazettes, and public consultation releases prior to the formal introduction milestone. GDELT and search trends do not represent total media consciousness, and absence of recorded signal does not confirm informational isolation.
            </p>
          </div>

          <AnticipationEvidenceSection
            billId={activeEvidencePair.billId}
            companyIsin={activeEvidencePair.companyIsin}
            companyName={activeEvidencePair.companyName}
          />
        </section>

        {/* SECTION F: Grounded AI Diffusion Analyst */}
        <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 shadow-sm space-y-4" aria-labelledby="ai-diffusion-heading">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-3">
            <div className="flex items-center gap-2">
              <h3 id="ai-diffusion-heading" className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                <span>🤖</span> AI Information Diffusion Analyst
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
                placeholder="Ask about pre-event information diffusion, market absorption dynamics, or the Anticipation Paradox..."
                value={aiQuestion}
                onChange={(e) => setAiQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAskAI();
                }}
                className="flex-1 h-9 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] px-3 text-xs text-[var(--text-primary)] placeholder-[var(--input-placeholder)] focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <Button
                variant="primary"
                size="sm"
                onClick={handleAskAI}
                disabled={aiLoading}
                className="h-9 text-xs px-4 font-semibold"
              >
                {aiLoading ? "Analyzing..." : "Analyze"}
              </Button>
            </div>

            {aiResponse && (
              <div className="p-4 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-2">
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] border-b border-[var(--border-subtle)] pb-2">
                  <span className="font-semibold text-blue-400">AI Diffusion Analysis</span>
                  <span className="text-[var(--text-faint)] font-mono">Lens: {aiPersona}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
                  {aiResponse}
                </p>
                <p className="text-[10px] text-[var(--text-faint)] pt-1">
                  Answers reflect empirical academic research methodology evaluating public information diffusion.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* State Prediction Firewall Notice */}
        <div className="space-y-2">
          <StatePredictionFirewall state="All States" />
          <p className="text-[11px] text-[var(--text-faint)] px-1">
            Pre-event anticipation scores are modeled strictly for Central Parliament legislation across 47 quantitative securities. State assemblies and qualitative corporate entities have strictly 0 quantitative anticipation scores.
          </p>
        </div>

        {/* MANDATORY VERBATIM STATUTORY LEGAL DISCLAIMER (BOTTOM) */}
        <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-card)] text-center shadow-sm">
          <p className="text-[11px] text-[var(--text-muted)] italic leading-relaxed">
            &ldquo;{MANDATORY_LEGAL_DISCLAIMER}&rdquo;
          </p>
        </div>
      </main>
    </div>
  );
}
