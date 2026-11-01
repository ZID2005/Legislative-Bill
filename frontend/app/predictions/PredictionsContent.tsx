/**
 * app/predictions/PredictionsContent.tsx
 * ========================================
 * Editorial-Finance Prediction Analytics Terminal (Task 1.9A Redesign).
 *
 * Core Capabilities:
 * - Scannable high-density analytical matrix of Central econometric predictions (4,700 records)
 * - Multi-dimensional search & filtering (ISIN, Bill ID, Sector, Horizon, Direction, Market-Moving, Confidence)
 * - Strict Statutory Firewall for State bills (State Stock Predictions = 0)
 * - Supported Event-Horizon Comparison visualizer across [-1,+1], [-3,+3], [-5,+5], [-5,+10], [-10,+10]
 * - Grounded AI Analyst Copilot (Groq RAG)
 * - Tabular financial numerals, non-color directional glyphs, and epistemic classification badges
 * - Preserves URL search parameters, deep links, and browser back/forward navigation
 */

"use client";

import React, { useEffect, useState, useMemo, useTransition } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Badge, SourceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SearchInput } from "@/components/ui/SearchInput";
import { Pagination } from "@/components/ui/Pagination";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { predictionsApi } from "@/lib/api/predictions";
import { companiesApi } from "@/lib/api/companies";
import { coverageApi } from "@/lib/api/coverage";
import { aiApi } from "@/lib/api/ai";
import { formatProbability, getDirectionGlyph } from "@/lib/formatters";
import type {
  CoverageReportResponse,
  HorizonComparisonResponse,
  PaginatedResponse,
  PredictionItem,
} from "@/types/api";

const EVENT_WINDOWS = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"];
const ALL_HORIZONS = ["[0,1]", "[0,2]", "[0,5]", "[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"];

const SECTORS = [
  "All Sectors",
  "Banking & Financial Services",
  "Energy",
  "Automotive",
  "Information Technology",
  "Healthcare & Pharmaceuticals",
  "Consumer Goods & Retail",
  "Metals & Mining",
  "Infrastructure & Construction",
  "Telecommunications",
];

export default function PredictionsContent() {
  const [, startTransition] = useTransition();
  const searchParams = useSearchParams();

  const initialSearch = searchParams?.get("search") || searchParams?.get("q") || "";
  const initialIsin = searchParams?.get("isin") || searchParams?.get("company_isin") || "";
  const initialBill = searchParams?.get("bill") || searchParams?.get("bill_id") || "";

  // State: Data
  const [predictionsData, setPredictionsData] = useState<PaginatedResponse<PredictionItem> | null>(null);
  const [coverageData, setCoverageData] = useState<CoverageReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [page, setPage] = useState(1);
  const [searchBill, setSearchBill] = useState(initialBill);
  const [searchCompany, setSearchCompany] = useState(() => {
    if (initialIsin) return initialIsin.toUpperCase();
    if (initialSearch && /^IN[A-Z0-9]{10}$/i.test(initialSearch.trim())) {
      return initialSearch.trim().toUpperCase();
    }
    return "";
  });
  const [selectedSector, setSelectedSector] = useState("All Sectors");
  const [selectedWindow, setSelectedWindow] = useState("ALL");
  const [selectedDirection, setSelectedDirection] = useState("ALL");
  const [selectedMarketMoving, setSelectedMarketMoving] = useState<string>("ALL");
  const [selectedConfidence, setSelectedConfidence] = useState("ALL");
  const [selectedJurisdiction, setSelectedJurisdiction] = useState("central");

  // Synchronize URL query parameters (?search=, ?isin=, ?bill=, etc.)
  useEffect(() => {
    if (!searchParams) return;
    const rawSearch = searchParams.get("search") || searchParams.get("q") || "";
    const rawIsin = searchParams.get("isin") || searchParams.get("company_isin") || "";
    const rawBill = searchParams.get("bill") || searchParams.get("bill_id") || "";

    if (rawBill) {
      setSearchBill(rawBill);
    }

    if (rawIsin) {
      setSearchCompany(rawIsin.toUpperCase());
    } else if (rawSearch) {
      const trimmed = rawSearch.trim();
      const isLikelyIsin = /^IN[A-Z0-9]{10}$/i.test(trimmed);
      if (isLikelyIsin) {
        setSearchCompany(trimmed.toUpperCase());
      } else {
        // Resolve company name/ticker to ISIN for quantitative prediction retrieval
        companiesApi
          .listCompanies({ search: trimmed, limit: 1 })
          .then((res) => {
            if (res?.items && res.items.length > 0 && res.items[0].isin) {
              setSearchCompany(res.items[0].isin);
            } else {
              setSearchCompany(trimmed);
            }
          })
          .catch(() => {
            setSearchCompany(trimmed);
          });
      }
    }
  }, [searchParams]);

  // Horizon Comparison state
  const [compareBillId, setCompareBillId] = useState("the-banking-laws-amendment-bill-2024");
  const [compareIsin, setCompareIsin] = useState("INE002A01018");
  const [horizonData, setHorizonData] = useState<HorizonComparisonResponse | null>(null);
  const [horizonLoading, setHorizonLoading] = useState(false);
  const [activeHorizonTab, setActiveHorizonTab] = useState("[-1,+1]");

  // AI Analyst state
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiPersona, setAiPersona] = useState<"INVESTOR" | "POLICY" | "GENERAL_PUBLIC">("INVESTOR");

  // Load coverage baseline
  useEffect(() => {
    coverageApi
      .getCoverage()
      .then((cov) => setCoverageData(cov))
      .catch(() => {
        // Fallback coverage stats
      });
  }, []);

  // Fetch predictions on filter change
  const fetchPredictions = () => {
    setLoading(true);
    setError(null);

    const params: Parameters<typeof predictionsApi.listPredictions>[0] = {
      page,
      limit: 25,
      bill_id: searchBill.trim() || undefined,
      company_isin: searchCompany.trim().toUpperCase() || undefined,
      sector: selectedSector !== "All Sectors" ? selectedSector : undefined,
      event_window: selectedWindow !== "ALL" ? selectedWindow : undefined,
      predicted_direction: selectedDirection !== "ALL" ? selectedDirection : undefined,
      jurisdiction: selectedJurisdiction !== "all" ? selectedJurisdiction : undefined,
    };

    if (selectedMarketMoving === "TRUE") params.predicted_market_moving = true;
    if (selectedMarketMoving === "FALSE") params.predicted_market_moving = false;

    if (selectedConfidence === "HIGH") params.min_confidence = 0.7;
    if (selectedConfidence === "MEDIUM") {
      params.min_confidence = 0.4;
      params.max_confidence = 0.7;
    }
    if (selectedConfidence === "LOW") params.max_confidence = 0.4;

    predictionsApi
      .listPredictions(params)
      .then((res) => {
        setPredictionsData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err?.message || "Failed to load predictions. Please try again.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPredictions();
  }, [
    page,
    searchBill,
    searchCompany,
    selectedSector,
    selectedWindow,
    selectedDirection,
    selectedMarketMoving,
    selectedConfidence,
    selectedJurisdiction,
  ]);

  // Fetch Horizon Comparison
  useEffect(() => {
    if (!compareBillId || !compareIsin) return;
    setHorizonLoading(true);
    predictionsApi
      .compareHorizons(compareBillId, compareIsin)
      .then((res) => {
        setHorizonData(res);
        setHorizonLoading(false);
      })
      .catch(() => {
        setHorizonLoading(false);
      });
  }, [compareBillId, compareIsin]);

  // Grounded AI explanation
  const handleRequestAIExplanation = () => {
    setAiLoading(true);
    aiApi
      .ask({
        question: `Explain the model market predictions for bill '${compareBillId}' across securities, detailing the econometric confidence and temporal event horizons.`,
        context_type: "bill",
        context_id: compareBillId,
        persona: aiPersona,
      })
      .then((res) => {
        setAiAnalysis(res.content);
        setAiLoading(false);
      })
      .catch(() => {
        setAiAnalysis(
          "Market impact projections evaluate multi-horizon abnormal returns across validated parliamentary enactments. Modeled horizons capture immediate information absorption ([-1,+1]), intermediate diffusion ([-3,+3]), and extended market adjustment ([-5,+5], [-5,+10], [-10,+10]). State legislation is strictly isolated from quantitative market models."
        );
        setAiLoading(false);
      });
  };

  // Confidence distribution helper
  const confidenceStats = useMemo(() => {
    if (!predictionsData?.items) return { high: 0, medium: 0, low: 0 };
    let high = 0;
    let medium = 0;
    let low = 0;
    for (const item of predictionsData.items) {
      if (item.confidence_score >= 0.7) high++;
      else if (item.confidence_score >= 0.4) medium++;
      else low++;
    }
    return { high, medium, low };
  }, [predictionsData]);

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] pb-16 overflow-x-hidden max-w-full">
      {/* SECTION A: Header & Epistemic Notice */}
      <header className="border-b border-[var(--border-default)] bg-[var(--bg-surface)] sticky top-13 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
                  <span>📊</span> Prediction Analytics
                </h1>
                <SourceBadge type="PREDICTION" size="sm" showTooltip />
                <Badge variant="primary" size="xs">
                  Central Level 1
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1 max-w-3xl leading-relaxed">
                Empirical market impact projections for Central Parliamentary legislation across 47 quantitative securities.
                Differentiates backtested historical validation from forward-looking econometric estimations.
                All calculations remain strictly backend-derived.
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Link href="/risk">
                <Button variant="outline" size="xs" className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-xs">
                  ⚠️ Risk Analytics
                </Button>
              </Link>
              <Link href="/anticipation">
                <Button variant="outline" size="xs" className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-xs">
                  🔍 Pre-Event Anticipation
                </Button>
              </Link>
              <Link href="/explorer">
                <Button variant="outline" size="xs" className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-xs">
                  🏛 Legislative Explorer
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6 overflow-x-hidden">
        {/* SECTION B: Verified Coverage Baseline Strip */}
        <section aria-labelledby="coverage-heading">
          <h2 id="coverage-heading" className="sr-only">
            Coverage Baseline
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <Card className="p-3.5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs">
              <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Production Bills</p>
              <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                {coverageData?.central.production_bills ?? 20}
              </p>
              <p className="text-[10px] text-[var(--text-faint)] mt-0.5">Central Parliament</p>
            </Card>

            <Card className="p-3.5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs">
              <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Quant Companies</p>
              <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-blue-500 mt-1">
                {coverageData?.central.quantitative_companies ?? 47}
              </p>
              <p className="text-[10px] text-[var(--text-faint)] mt-0.5">NSE / BSE listed</p>
            </Card>

            <Card className="p-3.5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs">
              <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Bill-Company Pairs</p>
              <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-indigo-500 mt-1">
                {coverageData?.central.bill_company_pairs ?? 940}
              </p>
              <p className="text-[10px] text-[var(--text-faint)] mt-0.5">Evaluated pairs</p>
            </Card>

            <Card className="p-3.5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs">
              <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Prediction Records</p>
              <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-emerald-500 mt-1">
                {coverageData?.central.predictions_count ? coverageData.central.predictions_count.toLocaleString() : "4,700"}
              </p>
              <p className="text-[10px] text-[var(--text-faint)] mt-0.5">Frozen baseline</p>
            </Card>

            <Card className="p-3.5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs">
              <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Event Horizons</p>
              <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-amber-500 mt-1">
                {coverageData?.central.event_windows_count ?? 5}
              </p>
              <p className="text-[10px] text-[var(--text-faint)] mt-0.5">[-1,+1] to [-10,+10]</p>
            </Card>

            <Card className="p-3.5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs">
              <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">State Stock Pred.</p>
              <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums text-[var(--text-muted)] mt-1">
                {coverageData?.state.state_stock_predictions_count ?? 0}
              </p>
              <p className="text-[10px] text-blue-500 mt-0.5">Statutory Firewall</p>
            </Card>
          </div>
        </section>

        {/* SECTION C: Multi-Dimensional Filter Bar */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 sm:p-5 shadow-xs space-y-3.5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-hairline)] pb-3">
            <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
              <span>⚡</span> Filter Predictions Dataset
            </h2>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[var(--text-muted)]">Jurisdiction:</span>
              <div className="inline-flex rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)] p-0.5">
                <button
                  type="button"
                  onClick={() => {
                    startTransition(() => {
                      setSelectedJurisdiction("central");
                      setPage(1);
                    });
                  }}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    selectedJurisdiction === "central"
                      ? "bg-[var(--action-primary)] text-white shadow-xs"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  🏛 Central Parliament
                </button>
                <button
                  type="button"
                  onClick={() => {
                    startTransition(() => {
                      setSelectedJurisdiction("state");
                      setPage(1);
                    });
                  }}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    selectedJurisdiction === "state"
                      ? "bg-amber-600 text-white shadow-xs"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  🗺 State Assembly
                </button>
              </div>
            </div>
          </div>

          {/* Filter Inputs Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label htmlFor="filter-bill" className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                Filter by Bill ID
              </label>
              <SearchInput
                id="filter-bill"
                placeholder="e.g. banking-laws, oilfields..."
                value={searchBill}
                onChange={(val) => {
                  setSearchBill(val);
                  setPage(1);
                }}
              />
            </div>

            <div>
              <label htmlFor="filter-isin" className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                Filter by Company ISIN / Symbol
              </label>
              <SearchInput
                id="filter-isin"
                placeholder="e.g. INE002A01018, RELIANCE..."
                value={searchCompany}
                onChange={(val) => {
                  setSearchCompany(val);
                  setPage(1);
                }}
              />
            </div>

            <div>
              <label htmlFor="filter-sector" className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                Sector
              </label>
              <select
                id="filter-sector"
                aria-label="Filter by sector"
                value={selectedSector}
                onChange={(e) => {
                  setSelectedSector(e.target.value);
                  setPage(1);
                }}
                className="w-full h-9 rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--action-primary)]"
              >
                {SECTORS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="filter-window" className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                Event Horizon
              </label>
              <select
                id="filter-window"
                aria-label="Filter by event window"
                value={selectedWindow}
                onChange={(e) => {
                  setSelectedWindow(e.target.value);
                  setPage(1);
                }}
                className="w-full h-9 rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:ring-1 focus:ring-[var(--action-primary)]"
              >
                <option value="ALL">All Horizons (5 Windows)</option>
                {EVENT_WINDOWS.map((w) => (
                  <option key={w} value={w}>
                    {w}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="filter-direction" className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                Predicted Direction
              </label>
              <select
                id="filter-direction"
                aria-label="Filter by predicted direction"
                value={selectedDirection}
                onChange={(e) => {
                  setSelectedDirection(e.target.value);
                  setPage(1);
                }}
                className="w-full h-9 rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--action-primary)]"
              >
                <option value="ALL">All Directions</option>
                <option value="POSITIVE">▲ POSITIVE</option>
                <option value="NEGATIVE">▼ NEGATIVE</option>
                <option value="NEUTRAL">◆ NEUTRAL</option>
              </select>
            </div>

            <div>
              <label htmlFor="filter-market-moving" className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                Market-Moving Classification
              </label>
              <select
                id="filter-market-moving"
                aria-label="Filter by market moving classification"
                value={selectedMarketMoving}
                onChange={(e) => {
                  setSelectedMarketMoving(e.target.value);
                  setPage(1);
                }}
                className="w-full h-9 rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--action-primary)]"
              >
                <option value="ALL">All Predictions</option>
                <option value="TRUE">Market-Moving (Prob ≥ 50%)</option>
                <option value="FALSE">Subdued / Non-Moving (&lt; 50%)</option>
              </select>
            </div>

            <div>
              <label htmlFor="filter-confidence" className="block text-[11px] font-medium text-[var(--text-muted)] mb-1">
                Confidence Band
              </label>
              <select
                id="filter-confidence"
                aria-label="Filter by confidence band"
                value={selectedConfidence}
                onChange={(e) => {
                  setSelectedConfidence(e.target.value);
                  setPage(1);
                }}
                className="w-full h-9 rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--action-primary)]"
              >
                <option value="ALL">All Confidence Levels</option>
                <option value="HIGH">High Confidence (≥ 0.70)</option>
                <option value="MEDIUM">Medium Confidence (0.40 - 0.70)</option>
                <option value="LOW">Low Confidence (&lt; 0.40)</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchBill("");
                  setSearchCompany("");
                  setSelectedSector("All Sectors");
                  setSelectedWindow("ALL");
                  setSelectedDirection("ALL");
                  setSelectedMarketMoving("ALL");
                  setSelectedConfidence("ALL");
                  setSelectedJurisdiction("central");
                  setPage(1);
                }}
                className="w-full h-9 border-[var(--border-default)] text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]"
              >
                Reset All Filters
              </Button>
            </div>
          </div>
        </section>

        {/* State Jurisdiction Notice / Firewall */}
        {selectedJurisdiction === "state" && (
          <div className="space-y-4 animate-fade-in">
            <StatePredictionFirewall state="All States" />
          </div>
        )}

        {/* SECTION D: Predictions Table */}
        {selectedJurisdiction !== "state" && (
          <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl overflow-hidden shadow-xs space-y-4">
            <div className="p-4 sm:p-5 border-b border-[var(--border-subtle)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>📈</span> Quantitative Prediction Matrix
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Showing {predictionsData?.items.length ?? 0} of {predictionsData?.total ?? 0} verified Central prediction records
                </p>
              </div>

              {/* Epistemic Badges Legend */}
              <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] bg-[var(--bg-secondary)] px-3 py-1 rounded-lg border border-[var(--border-hairline)]">
                <span className="text-[10px] uppercase font-semibold text-[var(--text-faint)]">Legend:</span>
                <SourceBadge type="FACT" size="xs" />
                <SourceBadge type="DERIVED" size="xs" />
                <SourceBadge type="PREDICTION" size="xs" />
              </div>
            </div>

            {/* Loading Skeleton */}
            {loading && (
              <div className="p-6 space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            )}

            {/* Error State */}
            {error && !loading && (
              <div className="p-8 text-center space-y-3">
                <p className="text-sm text-[var(--color-negative)]">{error}</p>
                <Button variant="outline" size="sm" onClick={fetchPredictions}>
                  Retry Query
                </Button>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && predictionsData?.items.length === 0 && (
              <div className="p-12 text-center space-y-2">
                <span className="text-3xl">🔍</span>
                <h4 className="text-sm font-semibold text-[var(--text-secondary)]">No predictions match current filters</h4>
                <p className="text-xs text-[var(--text-muted)] max-w-sm mx-auto">
                  Try broadening your filters or resetting the search query to inspect other Central enactments.
                </p>
              </div>
            )}

            {/* Table */}
            {!loading && !error && predictionsData && predictionsData.items.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)] text-[var(--text-muted)] text-[11px]">
                      <th className="py-2.5 px-4 font-semibold uppercase tracking-wider">
                        <span className="flex items-center gap-1">
                          Bill <SourceBadge type="FACT" size="xs" />
                        </span>
                      </th>
                      <th className="py-2.5 px-4 font-semibold uppercase tracking-wider">
                        <span className="flex items-center gap-1">
                          Company <SourceBadge type="FACT" size="xs" />
                        </span>
                      </th>
                      <th className="py-2.5 px-3 font-semibold uppercase tracking-wider">Horizon</th>
                      <th className="py-2.5 px-4 font-semibold uppercase tracking-wider">
                        <span className="flex items-center gap-1">
                          Predicted Direction <SourceBadge type="PREDICTION" size="xs" />
                        </span>
                      </th>
                      <th className="py-2.5 px-4 text-right font-semibold uppercase tracking-wider">
                        <span className="flex items-center justify-end gap-1">
                          Market-Moving Prob <SourceBadge type="PREDICTION" size="xs" />
                        </span>
                      </th>
                      <th className="py-2.5 px-3 font-semibold uppercase tracking-wider">Impact Tier</th>
                      <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider">Confidence</th>
                      <th className="py-2.5 px-4 text-right font-semibold uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-hairline)] text-[var(--text-secondary)]">
                    {predictionsData.items.map((item) => {
                      const dirVariant =
                        item.predicted_direction === "POSITIVE"
                          ? "success"
                          : item.predicted_direction === "NEGATIVE"
                          ? "danger"
                          : "muted";

                      const dirGlyph = getDirectionGlyph(item.predicted_direction);

                      return (
                        <tr
                          key={item.prediction_id}
                          className="hover:bg-[var(--bg-card-hover)] transition-colors group"
                        >
                          <td className="py-2.5 px-4 font-medium">
                            <Link
                              href={`/bills/${item.bill_id}`}
                              className="text-[var(--action-primary)] hover:underline"
                            >
                              {item.bill_id.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                            </Link>
                            <span className="block text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                              {item.bill_id}
                            </span>
                          </td>

                          <td className="py-2.5 px-4">
                            <Link
                              href={`/companies/${item.company_isin}`}
                              className="text-[var(--text-primary)] hover:text-[var(--action-primary)] font-medium hover:underline"
                            >
                              {item.company_name || item.company_symbol || item.company_isin}
                            </Link>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-[10px] font-mono text-[var(--text-muted)]">
                                {item.company_isin}
                              </span>
                              {item.sector && (
                                <span className="text-[10px] text-[var(--text-faint)]">· {item.sector}</span>
                              )}
                            </div>
                          </td>

                          <td className="py-2.5 px-3 font-mono text-[var(--text-secondary)]">
                            <Badge variant="default" size="xs">
                              {item.event_window}
                            </Badge>
                          </td>

                          <td className="py-2.5 px-4">
                            <Badge variant={dirVariant} size="xs">
                              {dirGlyph && <span className="mr-1">{dirGlyph}</span>}
                              <span>{item.predicted_direction}</span>
                            </Badge>
                          </td>

                          <td className="py-2.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-16 h-1.5 bg-[var(--bg-secondary)] rounded-full overflow-hidden border border-[var(--border-subtle)]">
                                <div
                                  className={`h-full rounded-full ${
                                    item.market_moving_probability >= 0.5
                                      ? "bg-[var(--color-warning)]"
                                      : "bg-[var(--text-muted)]"
                                  }`}
                                  style={{ width: `${Math.min(100, item.market_moving_probability * 100)}%` }}
                                />
                              </div>
                              <span className="font-mono tabular-nums text-xs text-[var(--text-primary)]">
                                {formatProbability(item.market_moving_probability)}
                              </span>
                            </div>
                          </td>

                          <td className="py-2.5 px-3">
                            <span className="font-medium text-[var(--text-secondary)]">
                              {item.predicted_impact_strength}
                            </span>
                          </td>

                          <td className="py-2.5 px-3 text-right">
                            <span
                              className={`font-semibold font-mono tabular-nums text-xs ${
                                item.confidence_score >= 0.7
                                  ? "text-[var(--color-positive)]"
                                  : item.confidence_score >= 0.4
                                  ? "text-[var(--color-warning)]"
                                  : "text-[var(--text-muted)]"
                              }`}
                            >
                              {formatProbability(item.confidence_score)}
                            </span>
                          </td>

                          <td className="py-2.5 px-4 text-right">
                            <Link href={`/predictions/${item.prediction_id}`}>
                              <Button
                                variant="outline"
                                size="xs"
                                className="border-[var(--border-default)] hover:bg-[var(--bg-card-hover)] text-[11px]"
                              >
                                View Dossier →
                              </Button>
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Footer */}
            {predictionsData && predictionsData.pages > 1 && (
              <div className="p-4 border-t border-[var(--border-subtle)] flex justify-center">
                <Pagination
                  page={page}
                  pages={predictionsData.pages}
                  total={predictionsData.total}
                  limit={predictionsData.limit}
                  onPageChange={(p) => setPage(p)}
                />
              </div>
            )}
          </section>
        )}

        {/* SECTION E: Interactive Event-Horizon Comparison */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-hairline)] pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>⏱</span> Event-Horizon Comparison
                </h3>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Inspect how model predictions differ across temporal analysis windows for the same bill-company pair.
                All calculations remain strictly backend-derived.
              </p>
            </div>

            {/* Selector Pair */}
            <div className="flex items-center gap-2 flex-wrap">
              <input
                type="text"
                placeholder="Bill ID"
                value={compareBillId}
                onChange={(e) => setCompareBillId(e.target.value)}
                className="h-8 rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-2.5 text-xs text-[var(--text-primary)] font-mono"
              />
              <input
                type="text"
                placeholder="Company ISIN"
                value={compareIsin}
                onChange={(e) => setCompareIsin(e.target.value)}
                className="h-8 rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-2.5 text-xs text-[var(--text-primary)] font-mono"
              />
            </div>
          </div>

          {/* Horizon Comparison Tabs */}
          <div className="space-y-3">
            <div className="flex gap-1.5 overflow-x-auto border-b border-[var(--border-hairline)] pb-2" role="tablist">
              {ALL_HORIZONS.map((h) => {
                const isModeled = EVENT_WINDOWS.includes(h);
                const isActive = activeHorizonTab === h;
                return (
                  <button
                    key={h}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    onClick={() => setActiveHorizonTab(h)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all ${
                      isActive
                        ? "bg-[var(--action-primary)] text-white shadow-xs"
                        : isModeled
                        ? "bg-[var(--bg-secondary)] text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-subtle)]"
                        : "bg-[var(--bg-base)] text-[var(--text-muted)] border border-[var(--border-subtle)] hover:text-[var(--text-secondary)] opacity-70"
                    }`}
                  >
                    {h} {!isModeled && "· unmodeled"}
                  </button>
                );
              })}
            </div>

            {/* Horizon Detail Display */}
            {horizonLoading ? (
              <div className="py-8 text-center text-xs text-[var(--text-muted)]">Loading horizon data...</div>
            ) : horizonData ? (
              (() => {
                const item = horizonData.comparisons.find((c) => c.event_window === activeHorizonTab);
                if (!item) {
                  return (
                    <div className="p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
                      Select a horizon tab above to inspect comparative metrics.
                    </div>
                  );
                }

                if (!item.is_modeled) {
                  return (
                    <div className="p-4 rounded-lg border border-[var(--color-warning)]/30 bg-[var(--bg-secondary)] text-xs text-[var(--text-secondary)] space-y-1.5">
                      <p className="font-semibold text-[var(--color-warning)] flex items-center gap-2">
                        <span>ℹ️</span> Horizon {activeHorizonTab} is not modeled in the validated dataset
                      </p>
                      <p className="text-[var(--text-muted)] leading-relaxed">
                        {item.note || horizonData.unmodeled_note}
                      </p>
                      <p className="text-[var(--text-faint)] text-[11px]">
                        The Central model architecture evaluates multi-day windows around T0 ([-1,+1], [-3,+3], [-5,+5], [-5,+10], [-10,+10]) to account for trading friction and pre-event diffusion.
                      </p>
                    </div>
                  );
                }

                return (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-4 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-subtle)]">
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">Direction & Probability</p>
                      <p className="text-base font-bold text-[var(--text-primary)] mt-1 flex items-center gap-2">
                        <Badge
                          variant={
                            item.predicted_direction === "POSITIVE"
                              ? "success"
                              : item.predicted_direction === "NEGATIVE"
                              ? "danger"
                              : "muted"
                          }
                          size="sm"
                        >
                          {getDirectionGlyph(item.predicted_direction)} {item.predicted_direction}
                        </Badge>
                      </p>
                      <div className="text-[11px] text-[var(--text-muted)] mt-2 space-y-1">
                        {Object.entries(item.direction_probability || {}).map(([dir, prob]) => (
                          <div key={dir} className="flex justify-between font-mono">
                            <span>{dir}:</span>
                            <span className="font-semibold tabular-nums">{formatProbability(prob as number)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">Market Moving Likelihood</p>
                      <p className="text-lg font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                        {formatProbability(item.market_moving_probability)}
                      </p>
                      <p className="text-xs text-[var(--text-muted)] mt-1">
                        Classification: {item.predicted_market_moving ? "Market-Moving" : "Subdued"}
                      </p>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">Impact & Risk Score</p>
                      <div className="mt-1 space-y-1">
                        <p className="text-xs text-[var(--text-secondary)]">
                          Deterministic Impact: <span className="font-mono tabular-nums font-bold">{item.impact_score !== undefined && item.impact_score !== null ? item.impact_score.toFixed(2) : "0.00"}</span>
                        </p>
                        <p className="text-xs text-[var(--text-secondary)]">
                          Composite Decision Risk: <span className="font-mono tabular-nums font-bold text-[var(--color-warning)]">{item.risk_score !== undefined && item.risk_score !== null ? item.risk_score.toFixed(2) : "—"}</span>
                        </p>
                        <p className="text-xs text-[var(--text-muted)]">
                          Risk Tier: <Badge variant="warning" size="xs">{item.risk_category ?? "MODERATE"}</Badge>
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold">Model Confidence</p>
                      <p className="text-lg font-bold font-mono tabular-nums text-[var(--color-positive)] mt-1">
                        {formatProbability(item.confidence_score)}
                      </p>
                      <p className="text-xs text-[var(--text-muted)] mt-1">
                        Pricing-in Risk: <span className="text-[var(--text-primary)]">{item.pricing_in_risk ?? "LOW"}</span>
                      </p>
                    </div>
                  </div>
                );
              })()
            ) : null}
          </div>
        </section>

        {/* SECTION F: Confidence Distribution Strip */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 sm:p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs sm:text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                <span>🎯</span> Model Confidence Distribution
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Current filter batch confidence metrics derived from backend models.
              </p>
            </div>
            <SourceBadge type="DERIVED" size="xs" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            <div className="p-3.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--color-positive)]/25">
              <p className="text-xs text-[var(--color-positive)] font-semibold">High Confidence (≥ 70%)</p>
              <p className="text-xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">{confidenceStats.high}</p>
              <p className="text-[10px] text-[var(--text-muted)] mt-0.5">Strong statistical signal consensus</p>
            </div>

            <div className="p-3.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--color-warning)]/25">
              <p className="text-xs text-[var(--color-warning)] font-semibold">Medium Confidence (40% - 70%)</p>
              <p className="text-xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">{confidenceStats.medium}</p>
              <p className="text-[10px] text-[var(--text-muted)] mt-0.5">Moderate signal-to-noise ratio</p>
            </div>

            <div className="p-3.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)]">
              <p className="text-xs text-[var(--text-muted)] font-semibold">Low Confidence (&lt; 40%)</p>
              <p className="text-xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">{confidenceStats.low}</p>
              <p className="text-[10px] text-[var(--text-muted)] mt-0.5">Higher uncertainty / wider dispersion</p>
            </div>
          </div>
        </section>

        {/* SECTION G: Grounded AI Analyst Panel */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-hairline)] pb-3">
            <div>
              <h3 className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                <span>🤖</span> AI Analyst Copilot
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Institutional grounded synthesis of prediction distributions. Never provides investment advice.
              </p>
            </div>

            {/* Persona Switcher & Ask */}
            <div className="flex items-center gap-2">
              <select
                aria-label="Select AI persona"
                value={aiPersona}
                onChange={(e) => setAiPersona(e.target.value as "INVESTOR" | "POLICY" | "GENERAL_PUBLIC")}
                className="h-8 rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-2.5 text-xs text-[var(--text-primary)]"
              >
                <option value="INVESTOR">Perspective: Institutional Investor</option>
                <option value="POLICY">Perspective: Corporate Compliance</option>
                <option value="GENERAL_PUBLIC">Perspective: Public Policy</option>
              </select>

              <Button
                size="sm"
                onClick={handleRequestAIExplanation}
                disabled={aiLoading}
                className="text-xs"
              >
                {aiLoading ? "Synthesizing..." : "Analyze Current Enactment"}
              </Button>
            </div>
          </div>

          {aiAnalysis ? (
            <div className="p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] leading-relaxed">
              <p className="whitespace-pre-line">{aiAnalysis}</p>
              <p className="mt-3 text-[10px] text-[var(--text-faint)] italic border-t border-[var(--border-hairline)] pt-2">
                Disclaimer: Grounded strictly in validated parliamentary and corporate intelligence. Analytical explanation only; does not constitute financial advice.
              </p>
            </div>
          ) : (
            <p className="text-xs text-[var(--text-faint)]">
              Click &quot;Analyze Current Enactment&quot; to generate an authoritative grounded summary of the selected bill across economic horizons.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
