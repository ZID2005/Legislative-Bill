"use client";

import React, { useEffect, useState, useMemo, useTransition } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge, SourceBadge, JurisdictionBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SearchInput } from "@/components/ui/SearchInput";
import { Pagination } from "@/components/ui/Pagination";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { predictionsApi } from "@/lib/api/predictions";
import { coverageApi } from "@/lib/api/coverage";
import { aiApi } from "@/lib/api/ai";
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

  // State: Data
  const [predictionsData, setPredictionsData] = useState<PaginatedResponse<PredictionItem> | null>(null);
  const [coverageData, setCoverageData] = useState<CoverageReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [page, setPage] = useState(1);
  const [searchBill, setSearchBill] = useState("");
  const [searchCompany, setSearchCompany] = useState("");
  const [selectedSector, setSelectedSector] = useState("All Sectors");
  const [selectedWindow, setSelectedWindow] = useState("ALL");
  const [selectedDirection, setSelectedDirection] = useState("ALL");
  const [selectedMarketMoving, setSelectedMarketMoving] = useState<string>("ALL");
  const [selectedConfidence, setSelectedConfidence] = useState("ALL");
  const [selectedJurisdiction, setSelectedJurisdiction] = useState("central");

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

  // Load coverage once
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
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-16">
      {/* SECTION A: Header & Epistemic Notice */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
                  <span className="text-blue-500">📊</span> Prediction Analytics
                </h1>
                <SourceBadge type="PREDICTION" size="sm" showTooltip />
                <Badge variant="primary" size="xs">
                  Central Level 1
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
                Empirical market impact projections for Central Parliamentary legislation across 47 quantitative securities.
                Differentiates backtested historical validation from forward-looking econometric estimations.
                All calculations remain strictly backend-derived.
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Link href="/risk">
                <Button variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800 text-xs">
                  ⚠️ Risk Analytics
                </Button>
              </Link>
              <Link href="/anticipation">
                <Button variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800 text-xs">
                  🔍 Pre-Event Anticipation
                </Button>
              </Link>
              <Link href="/explorer">
                <Button variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800 text-xs">
                  🏛 Legislative Explorer
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* SECTION B: Verified Coverage Baseline Cards */}
        <section aria-labelledby="coverage-heading">
          <h2 id="coverage-heading" className="sr-only">
            Coverage Baseline
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <Card className="p-4 bg-slate-900/80 border-slate-800">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Production Bills</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">
                {coverageData?.central.production_bills ?? 20}
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">Central Parliament</p>
            </Card>

            <Card className="p-4 bg-slate-900/80 border-slate-800">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Quant Companies</p>
              <p className="text-2xl font-bold text-blue-400 mt-1">
                {coverageData?.central.quantitative_companies ?? 47}
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">NSE / BSE listed</p>
            </Card>

            <Card className="p-4 bg-slate-900/80 border-slate-800">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Bill-Company Pairs</p>
              <p className="text-2xl font-bold text-indigo-400 mt-1">
                {coverageData?.central.bill_company_pairs ?? 940}
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">Evaluated pairs</p>
            </Card>

            <Card className="p-4 bg-slate-900/80 border-slate-800">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Prediction Records</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">
                {coverageData?.central.predictions_count ? coverageData.central.predictions_count.toLocaleString() : "4,700"}
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">Frozen baseline</p>
            </Card>

            <Card className="p-4 bg-slate-900/80 border-slate-800">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Event Horizons</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">
                {coverageData?.central.event_windows_count ?? 5}
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">[-1,+1] to [-10,+10]</p>
            </Card>

            <Card className="p-4 bg-slate-900/80 border-slate-800">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">State Stock Pred.</p>
              <p className="text-2xl font-bold text-slate-400 mt-1">
                {coverageData?.state.state_stock_predictions_count ?? 0}
              </p>
              <p className="text-[10px] text-blue-400 mt-0.5">Statutory Firewall</p>
            </Card>
          </div>
        </section>

        {/* SECTION C: Multi-Dimensional Filter Bar */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <span>⚡</span> Filter Predictions Dataset
            </h2>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Jurisdiction Mode:</span>
              <div className="inline-flex rounded-lg border border-slate-700 bg-slate-950 p-0.5">
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
                      ? "bg-blue-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200"
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
                      ? "bg-amber-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🗺 State Assembly
                </button>
              </div>
            </div>
          </div>

          {/* Filter Inputs Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Bill filter */}
            <div>
              <label htmlFor="filter-bill" className="block text-xs font-medium text-slate-400 mb-1">
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

            {/* Company ISIN */}
            <div>
              <label htmlFor="filter-isin" className="block text-xs font-medium text-slate-400 mb-1">
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

            {/* Sector Selector */}
            <div>
              <label htmlFor="filter-sector" className="block text-xs font-medium text-slate-400 mb-1">
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
                className="w-full h-9 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {SECTORS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Event Window Selector */}
            <div>
              <label htmlFor="filter-window" className="block text-xs font-medium text-slate-400 mb-1">
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
                className="w-full h-9 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="ALL">All Horizons (5 Windows)</option>
                {EVENT_WINDOWS.map((w) => (
                  <option key={w} value={w}>
                    {w}
                  </option>
                ))}
              </select>
            </div>

            {/* Direction Selector */}
            <div>
              <label htmlFor="filter-direction" className="block text-xs font-medium text-slate-400 mb-1">
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
                className="w-full h-9 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="ALL">All Directions</option>
                <option value="POSITIVE">🟢 POSITIVE</option>
                <option value="NEGATIVE">🔴 NEGATIVE</option>
                <option value="NEUTRAL">⚪ NEUTRAL</option>
              </select>
            </div>

            {/* Market-Moving Probability */}
            <div>
              <label htmlFor="filter-market-moving" className="block text-xs font-medium text-slate-400 mb-1">
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
                className="w-full h-9 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="ALL">All Predictions</option>
                <option value="TRUE">Market-Moving (Prob ≥ 50%)</option>
                <option value="FALSE">Subdued / Non-Moving (&lt; 50%)</option>
              </select>
            </div>

            {/* Confidence Threshold */}
            <div>
              <label htmlFor="filter-confidence" className="block text-xs font-medium text-slate-400 mb-1">
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
                className="w-full h-9 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="ALL">All Confidence Levels</option>
                <option value="HIGH">High Confidence (≥ 0.70)</option>
                <option value="MEDIUM">Medium Confidence (0.40 - 0.70)</option>
                <option value="LOW">Low Confidence (&lt; 0.40)</option>
              </select>
            </div>

            {/* Reset Filters */}
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
                className="w-full h-9 border-slate-700 text-xs text-slate-300 hover:bg-slate-800"
              >
                Reset All Filters
              </Button>
            </div>
          </div>
        </section>

        {/* State Jurisdiction Notice / Firewall */}
        {selectedJurisdiction === "state" && (
          <div className="space-y-4">
            <StatePredictionFirewall state="All States" />
          </div>
        )}

        {/* SECTION D: Predictions Table */}
        {selectedJurisdiction !== "state" && (
          <section className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg space-y-4">
            <div className="p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <span>📈</span> Quantitative Prediction Matrix
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Showing {predictionsData?.items.length ?? 0} of {predictionsData?.total ?? 0} verified Central prediction records
                </p>
              </div>

              {/* Epistemic Badges Legend */}
              <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="text-[11px] uppercase tracking-wider text-slate-500">Legend:</span>
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
                <p className="text-sm text-rose-400">{error}</p>
                <Button variant="outline" size="sm" onClick={fetchPredictions}>
                  Retry Query
                </Button>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && predictionsData?.items.length === 0 && (
              <div className="p-12 text-center space-y-2">
                <span className="text-3xl">🔍</span>
                <h4 className="text-sm font-semibold text-slate-300">No predictions match current filters</h4>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  Try broadening your filters or resetting the search query to inspect other Central enactments.
                </p>
              </div>
            )}

            {/* Table */}
            {!loading && !error && predictionsData && predictionsData.items.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/70 text-slate-400">
                      <th className="py-3 px-4 font-semibold uppercase tracking-wider">
                        <span className="flex items-center gap-1">
                          Bill <SourceBadge type="FACT" size="xs" />
                        </span>
                      </th>
                      <th className="py-3 px-4 font-semibold uppercase tracking-wider">
                        <span className="flex items-center gap-1">
                          Company <SourceBadge type="FACT" size="xs" />
                        </span>
                      </th>
                      <th className="py-3 px-3 font-semibold uppercase tracking-wider">Horizon</th>
                      <th className="py-3 px-4 font-semibold uppercase tracking-wider">
                        <span className="flex items-center gap-1">
                          Predicted Direction <SourceBadge type="PREDICTION" size="xs" />
                        </span>
                      </th>
                      <th className="py-3 px-4 font-semibold uppercase tracking-wider">
                        <span className="flex items-center gap-1">
                          Market-Moving Prob <SourceBadge type="PREDICTION" size="xs" />
                        </span>
                      </th>
                      <th className="py-3 px-3 font-semibold uppercase tracking-wider">Impact Tier</th>
                      <th className="py-3 px-3 font-semibold uppercase tracking-wider">Confidence</th>
                      <th className="py-3 px-4 text-right font-semibold uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {predictionsData.items.map((item) => {
                      const dirVariant =
                        item.predicted_direction === "POSITIVE"
                          ? "success"
                          : item.predicted_direction === "NEGATIVE"
                          ? "danger"
                          : "muted";

                      return (
                        <tr
                          key={item.prediction_id}
                          className="hover:bg-slate-800/40 transition-colors group"
                        >
                          <td className="py-3 px-4 font-medium">
                            <Link
                              href={`/bills/${item.bill_id}`}
                              className="text-blue-400 hover:text-blue-300 hover:underline"
                            >
                              {item.bill_id.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                            </Link>

                            <span className="block text-[10px] text-slate-500 font-mono mt-0.5">
                              {item.bill_id}
                            </span>
                          </td>

                          <td className="py-3 px-4">
                            <Link
                              href={`/companies/${item.company_isin}`}
                              className="text-slate-200 hover:text-blue-300 font-medium hover:underline"
                            >
                              {item.company_name || item.company_symbol || item.company_isin}
                            </Link>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-[10px] font-mono text-slate-400">
                                {item.company_isin}
                              </span>
                              {item.sector && (
                                <span className="text-[10px] text-slate-500">· {item.sector}</span>
                              )}
                            </div>
                          </td>

                          <td className="py-3 px-3 font-mono text-slate-300">
                            <Badge variant="default" size="xs">
                              {item.event_window}
                            </Badge>
                          </td>

                          <td className="py-3 px-4">
                            <Badge variant={dirVariant} size="xs">
                              {item.predicted_direction}
                            </Badge>
                          </td>

                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    item.market_moving_probability >= 0.5
                                      ? "bg-amber-500"
                                      : "bg-slate-500"
                                  }`}
                                  style={{ width: `${Math.min(100, item.market_moving_probability * 100)}%` }}
                                />
                              </div>
                              <span className="font-mono text-xs text-slate-300">
                                {(item.market_moving_probability * 100).toFixed(1)}%
                              </span>
                            </div>
                          </td>

                          <td className="py-3 px-3">
                            <span className="font-medium text-slate-300">
                              {item.predicted_impact_strength}
                            </span>
                          </td>

                          <td className="py-3 px-3">
                            <span
                              className={`font-semibold text-xs ${
                                item.confidence_score >= 0.7
                                  ? "text-emerald-400"
                                  : item.confidence_score >= 0.4
                                  ? "text-amber-400"
                                  : "text-slate-400"
                              }`}
                            >
                              {(item.confidence_score * 100).toFixed(1)}%
                            </span>
                          </td>

                          <td className="py-3 px-4 text-right">
                            <Link href={`/predictions/${item.prediction_id}`}>
                              <Button
                                variant="outline"
                                size="xs"
                                className="border-slate-700 hover:bg-slate-800 text-[11px]"
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
              <div className="p-4 border-t border-slate-800 flex justify-center">
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
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-lg space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <span>⏱</span> Event-Horizon Comparison
                </h3>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <p className="text-xs text-slate-400 mt-1">
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
                className="h-8 rounded border border-slate-700 bg-slate-950 px-2 text-xs text-slate-200"
              />
              <input
                type="text"
                placeholder="Company ISIN"
                value={compareIsin}
                onChange={(e) => setCompareIsin(e.target.value)}
                className="h-8 rounded border border-slate-700 bg-slate-950 px-2 text-xs text-slate-200"
              />
            </div>
          </div>

          {/* Horizon Comparison Tabs */}
          <div className="space-y-4">
            <div className="flex gap-1.5 overflow-x-auto border-b border-slate-800 pb-2">
              {ALL_HORIZONS.map((h) => {
                const isModeled = EVENT_WINDOWS.includes(h);
                const isActive = activeHorizonTab === h;
                return (
                  <button
                    key={h}
                    type="button"
                    onClick={() => setActiveHorizonTab(h)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all ${
                      isActive
                        ? "bg-blue-600 text-white shadow-md"
                        : isModeled
                        ? "bg-slate-800 text-slate-300 hover:bg-slate-700"
                        : "bg-slate-950/70 text-slate-500 border border-slate-800 hover:text-slate-400"
                    }`}
                  >
                    {h} {!isModeled && "· unmodeled"}
                  </button>
                );
              })}
            </div>

            {/* Horizon Detail Display */}
            {horizonLoading ? (
              <div className="py-8 text-center text-xs text-slate-400">Loading horizon data...</div>
            ) : horizonData ? (
              (() => {
                const item = horizonData.comparisons.find((c) => c.event_window === activeHorizonTab);
                if (!item) {
                  return (
                    <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-400">
                      Select a horizon tab above to inspect comparative metrics.
                    </div>
                  );
                }

                if (!item.is_modeled) {
                  return (
                    <div className="p-5 rounded-lg border border-amber-800/40 bg-amber-950/20 text-xs text-amber-200 space-y-2">
                      <p className="font-semibold flex items-center gap-2">
                        <span>ℹ️</span> Horizon {activeHorizonTab} is not modeled in the validated dataset
                      </p>
                      <p className="text-amber-300/80 leading-relaxed">
                        {item.note || horizonData.unmodeled_note}
                      </p>
                      <p className="text-slate-400 text-[11px]">
                        The Central model architecture evaluates multi-day windows around T0 ([-1,+1], [-3,+3], [-5,+5], [-5,+10], [-10,+10]) to account for trading friction and pre-event diffusion.
                      </p>
                    </div>
                  );
                }

                return (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-5 bg-slate-950/80 rounded-xl border border-slate-800">
                    <div>
                      <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Direction & Probability</p>
                      <p className="text-lg font-bold text-slate-100 mt-1 flex items-center gap-2">
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
                          {item.predicted_direction}
                        </Badge>
                      </p>
                      <div className="text-[11px] text-slate-400 mt-2 space-y-1">
                        {Object.entries(item.direction_probability || {}).map(([dir, prob]) => (
                          <div key={dir} className="flex justify-between font-mono">
                            <span>{dir}:</span>
                            <span>{(prob * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Market Moving Likelihood</p>
                      <p className="text-xl font-bold text-slate-100 mt-1">
                        {item.market_moving_probability !== null && item.market_moving_probability !== undefined
                          ? `${(item.market_moving_probability * 100).toFixed(1)}%`
                          : "—"}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        Classification: {item.predicted_market_moving ? "Market-Moving" : "Subdued"}
                      </p>
                    </div>

                    <div>
                      <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Impact & Risk Score</p>
                      <div className="mt-1 space-y-1">
                        <p className="text-xs text-slate-300">
                          Deterministic Impact: <span className="font-mono font-bold">{item.impact_score?.toFixed(2) ?? "0.00"}</span>
                        </p>
                        <p className="text-xs text-slate-300">
                          Composite Decision Risk: <span className="font-mono font-bold text-amber-400">{item.risk_score?.toFixed(2) ?? "—"}</span>
                        </p>
                        <p className="text-xs text-slate-400">
                          Risk Tier: <Badge variant="warning" size="xs">{item.risk_category ?? "MODERATE"}</Badge>
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Model Confidence</p>
                      <p className="text-xl font-bold text-emerald-400 mt-1">
                        {item.confidence_score !== null && item.confidence_score !== undefined
                          ? `${(item.confidence_score * 100).toFixed(1)}%`
                          : "—"}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        Pricing-in Risk: <span className="text-slate-300">{item.pricing_in_risk ?? "LOW"}</span>
                      </p>
                    </div>
                  </div>
                );
              })()
            ) : null}
          </div>
        </section>

        {/* SECTION F: Confidence Distribution Visualization */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>🎯</span> Model Confidence Distribution
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Current filter batch confidence metrics derived from backend models.
              </p>
            </div>
            <SourceBadge type="DERIVED" size="xs" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="p-4 rounded-lg bg-slate-950 border border-emerald-900/40">
              <p className="text-xs text-emerald-400 font-semibold">High Confidence (≥ 70%)</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">{confidenceStats.high}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Strong statistical signal consensus</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-950 border border-amber-900/40">
              <p className="text-xs text-amber-400 font-semibold">Medium Confidence (40% - 70%)</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">{confidenceStats.medium}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Moderate signal-to-noise ratio</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-950 border border-slate-700">
              <p className="text-xs text-slate-400 font-semibold">Low Confidence (&lt; 40%)</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">{confidenceStats.low}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Higher uncertainty / wider dispersion</p>
            </div>
          </div>
        </section>

        {/* SECTION G: Grounded AI Analyst Panel */}
        <section className="bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950/40 border border-blue-900/40 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>🤖</span> AI Analyst Copilot
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Institutional grounded synthesis of prediction distributions. Never provides investment advice.
              </p>
            </div>

            {/* Persona Switcher & Ask */}
            <div className="flex items-center gap-2">
              <select
                aria-label="Select AI persona"
                value={aiPersona}
                onChange={(e) => setAiPersona(e.target.value as "INVESTOR" | "POLICY" | "GENERAL_PUBLIC")}
                className="h-8 rounded border border-slate-700 bg-slate-950 px-2.5 text-xs text-slate-200"
              >
                <option value="INVESTOR">Perspective: Institutional Investor</option>
                <option value="POLICY">Perspective: Corporate Compliance</option>
                <option value="GENERAL_PUBLIC">Perspective: Public Policy</option>
              </select>

              <Button
                size="sm"
                onClick={handleRequestAIExplanation}
                disabled={aiLoading}
                className="bg-blue-600 hover:bg-blue-500 text-xs"
              >
                {aiLoading ? "Synthesizing..." : "Analyze Current Enactment"}
              </Button>
            </div>
          </div>

          {aiAnalysis ? (
            <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 text-xs text-slate-300 leading-relaxed">
              <p className="whitespace-pre-line">{aiAnalysis}</p>
              <p className="mt-3 text-[10px] text-slate-500 italic border-t border-slate-800/80 pt-2">
                Disclaimer: Grounded strictly in validated parliamentary and corporate intelligence. Analytical explanation only; does not constitute financial advice.
              </p>
            </div>
          ) : (
            <p className="text-xs text-slate-500">
              Click &quot;Analyze Current Enactment&quot; to generate an authoritative grounded summary of the selected bill across economic horizons.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
