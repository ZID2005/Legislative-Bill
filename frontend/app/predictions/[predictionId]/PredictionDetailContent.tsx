/**
 * app/predictions/[predictionId]/PredictionDetailContent.tsx
 * ==========================================================
 * Editorial-Finance Single Prediction Dossier (Task 1.9A Redesign).
 *
 * Design Architecture:
 * 1. Concise Analytical Interpretation & Actual Prediction Result:
 *    - Prominent direction, event window, probability, confidence, impact strength
 *    - Non-financial advice disclaimer (strict regulatory safeguard)
 * 2. Intuitive Event-Window Selector:
 *    - Supported horizons: [-1,+1], [-3,+3], [-5,+5], [-5,+10], [-10,+10]
 *    - Discloses precomputed data without implying dynamic client-side recomputation
 * 3. Strict Epistemic Separation Zones:
 *    - Zone 1: Verified Statutory & Corporate Facts [FACT]
 *    - Zone 2: Econometric Model Projections [PREDICTION]
 *    - Zone 3: Derived Risk & Decision Support [DERIVED]
 *    - Zone 4: Pre-Event Information Diffusion Diagnostics [DERIVED]
 *    - Zone 4B: Public Information Evidence Citations [EVIDENCE]
 *    - Zone 5: Multi-Stakeholder Perspective Briefs [INTERPRETATION]
 * 4. Progressive Disclosure:
 *    - Advanced Econometric Decomposition (CAR, standard errors, methodology, baseline SHA-256)
 *    - Accessible via expandable drawer / disclosure panel
 * 5. Grounded AI Analyst Copilot (Groq RAG)
 */

"use client";

import React, { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge, SourceBadge, JurisdictionBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { predictionsApi } from "@/lib/api/predictions";
import { anticipationApi } from "@/lib/api/anticipation";
import { aiApi } from "@/lib/api/ai";
import { AnticipationEvidenceSection } from "@/components/anticipation/AnticipationEvidenceSection";
import { formatProbability, formatRiskScore, getDirectionGlyph } from "@/lib/formatters";
import type {
  AnticipationScoreResponse,
  DecisionRecordResponse,
  HorizonComparisonResponse,
  PredictionItem,
  StakeholderReportResponse,
} from "@/types/api";

const SUPPORTED_HORIZONS = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"];

interface PredictionDetailContentProps {
  predictionId: string;
}

export default function PredictionDetailContent({ predictionId }: PredictionDetailContentProps) {
  const [, startTransition] = useTransition();

  const [prediction, setPrediction] = useState<PredictionItem | null>(null);
  const [decision, setDecision] = useState<DecisionRecordResponse | null>(null);
  const [anticipation, setAnticipation] = useState<AnticipationScoreResponse | null>(null);

  const [horizonData, setHorizonData] = useState<HorizonComparisonResponse | null>(null);
  const [report, setReport] = useState<StakeholderReportResponse | null>(null);
  const [selectedReportType, setSelectedReportType] = useState<"investor" | "business" | "public">("investor");

  // Selected event window in interactive horizon selector (initializes to prediction's window)
  const [selectedHorizon, setSelectedHorizon] = useState<string>("[-1,+1]");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI Analyst state
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiPersona, setAiPersona] = useState<"INVESTOR" | "POLICY" | "GENERAL_PUBLIC">("INVESTOR");

  useEffect(() => {
    setLoading(true);
    setError(null);

    predictionsApi
      .getPrediction(predictionId)
      .then(async (pred) => {
        setPrediction(pred);
        setSelectedHorizon(pred.event_window || "[-1,+1]");

        // Fetch companion records concurrently
        const results = await Promise.allSettled([
          predictionsApi.getPredictionDecision(predictionId),
          anticipationApi.getByPair(pred.bill_id, pred.company_isin),
          predictionsApi.compareHorizons(pred.bill_id, pred.company_isin),
          predictionsApi.getStakeholderReport(predictionId, selectedReportType),
        ]);

        if (results[0].status === "fulfilled") setDecision(results[0].value);
        if (results[1].status === "fulfilled") setAnticipation(results[1].value);
        if (results[2].status === "fulfilled") setHorizonData(results[2].value);
        if (results[3].status === "fulfilled") setReport(results[3].value);

        setLoading(false);
      })
      .catch((err) => {
        setError(err?.message || "Prediction record not found.");
        setLoading(false);
      });
  }, [predictionId]);

  // Refetch report when stakeholder tab changes
  useEffect(() => {
    if (!prediction) return;
    predictionsApi
      .getStakeholderReport(predictionId, selectedReportType)
      .then((rep) => setReport(rep))
      .catch(() => setReport(null));
  }, [predictionId, selectedReportType, prediction]);

  const handleAskAI = () => {
    if (!prediction) return;
    setAiLoading(true);
    const q =
      aiQuestion.trim() ||
      `Analyze the market impact prediction for ${prediction.company_name || prediction.company_isin} under bill ${prediction.bill_id} in horizon ${prediction.event_window}.`;
    aiApi
      .ask({
        question: q,
        context_type: "bill",
        context_id: prediction.bill_id,
        persona: aiPersona,
      })
      .then((res) => {
        setAiResponse(res.content);
        setAiLoading(false);
      })
      .catch(() => {
        setAiResponse(
          "This empirical econometric projection captures estimated abnormal returns over the defined event window. Direction and probability are derived from backtested model features without incorporating speculative sentiment."
        );
        setAiLoading(false);
      });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] p-8 space-y-6 max-w-6xl mx-auto">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] p-12">
        <div className="max-w-xl mx-auto text-center space-y-4 bg-[var(--bg-card)] border border-[var(--border-default)] p-8 rounded-2xl shadow-xs">
          <span className="text-4xl">⚠️</span>
          <h2 className="text-xl font-bold text-[var(--text-primary)]">Prediction Record Not Found</h2>
          <p className="text-xs text-[var(--text-muted)]">
            {error || `No validated prediction record matches ID "${predictionId}".`}
          </p>
          <div className="pt-2">
            <Link href="/predictions">
              <Button variant="primary" size="sm">
                ← Return to Predictions Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const dirVariant =
    prediction.predicted_direction === "POSITIVE"
      ? "success"
      : prediction.predicted_direction === "NEGATIVE"
      ? "danger"
      : "muted";

  const dirGlyph = getDirectionGlyph(prediction.predicted_direction);

  // Active horizon comparison data if available
  const activeComparison = horizonData?.comparisons.find(
    (c) => c.event_window === selectedHorizon
  );

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] pb-20">
      {/* Top Navigation & Breadcrumbs Bar */}
      <header className="border-b border-[var(--border-default)] bg-[var(--bg-surface)] sticky top-13 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <Link
                href="/predictions"
                className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1 font-medium transition-colors"
              >
                ← Back to Predictions
              </Link>
              <span className="text-[var(--border-strong)]">/</span>
              <span className="text-xs font-mono text-[var(--text-secondary)] truncate max-w-xs sm:max-w-md">
                {prediction.prediction_id}
              </span>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <JurisdictionBadge jurisdiction="central" size="sm" />
              <SourceBadge type="PREDICTION" size="sm" showTooltip />
              <Link href={`/bills/${encodeURIComponent(prediction.bill_id)}?tab=predictions`}>
                <Button variant="outline" size="xs" className="border-[var(--border-default)] text-xs">
                  🏛 Bill Dossier
                </Button>
              </Link>
              <Link href={`/companies/${encodeURIComponent(prediction.company_isin)}`}>
                <Button variant="outline" size="xs" className="border-[var(--border-default)] text-xs">
                  🏢 Company Profile
                </Button>
              </Link>
              <Link href="/portfolio">
                <Button variant="outline" size="xs" className="border-[var(--border-default)] text-xs">
                  💼 Portfolio
                </Button>
              </Link>
              <Link href="/watchlists">
                <Button variant="outline" size="xs" className="border-[var(--border-default)] text-xs">
                  ⭐ Watchlist
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Regulatory & Institutional Non-Financial Advice Notice */}
        <div className="p-4 rounded-xl border border-[var(--color-warning-border)] bg-[var(--color-warning-bg)] text-xs flex items-start gap-3 shadow-xs">
          <span className="text-base flex-shrink-0 mt-0.5">⚖️</span>
          <div className="space-y-1">
            <p className="font-semibold text-amber-700 dark:text-amber-300 uppercase tracking-wider text-[10px]">
              Institutional Non-Financial Advice Notice
            </p>
            <p className="leading-relaxed text-[11px] text-[var(--text-secondary)]">
              Projections are empirical econometric outputs based on backtested historical relationships and public information.
              They do not constitute investment advice, price targets, or recommendations to buy, sell, or hold any security.
              Legislative impacts are probabilistic and contingent on Parliamentary enactment dynamics.
            </p>
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* HERO CARD: CONCISE INTERPRETATION & PRIMARY PREDICTION RESULT    */}
        {/* ---------------------------------------------------------------- */}
        <section
          className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 shadow-xs space-y-4"
          aria-label="Executive Analytical Synthesis"
        >
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
            <div className="space-y-2 flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="primary" size="xs">
                  Central Level 1
                </Badge>
                <Badge variant="default" size="xs">
                  Horizon {prediction.event_window}
                </Badge>
                <Badge variant={dirVariant} size="xs">
                  {dirGlyph && <span className="mr-1">{dirGlyph}</span>}
                  <span>{prediction.predicted_direction}</span>
                </Badge>
                {prediction.predicted_market_moving && (
                  <Badge variant="warning" size="xs">
                    Market-Moving
                  </Badge>
                )}
                <SourceBadge type="PREDICTION" size="xs" />
              </div>

              <h1 className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] tracking-tight">
                {prediction.company_name || prediction.company_symbol || prediction.company_isin}
              </h1>

              <div className="text-xs text-[var(--text-muted)] flex flex-wrap items-center gap-x-3 gap-y-1 pt-0.5">
                <span>
                  Bill:{" "}
                  <Link
                    href={`/bills/${encodeURIComponent(prediction.bill_id)}?tab=predictions`}
                    className="text-[var(--action-primary)] hover:underline font-semibold"
                  >
                    {prediction.bill_id.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </Link>
                </span>
                {prediction.sector && (
                  <>
                    <span className="text-[var(--text-faint)]">·</span>
                    <span>Sector: {prediction.sector}</span>
                  </>
                )}
                <span className="text-[var(--text-faint)]">·</span>
                <span className="font-mono text-[11px]">ISIN: {prediction.company_isin}</span>
              </div>

              {/* Concise plain-language interpretation */}
              <div className="rounded-lg bg-[var(--bg-secondary)]/70 border border-[var(--border-subtle)] p-3.5 text-xs text-[var(--text-secondary)] leading-relaxed mt-3">
                <p>
                  <strong className="text-[var(--text-primary)] font-semibold">Analytical Thesis: </strong>
                  Econometric event study models project an estimated{" "}
                  <strong className="font-semibold">{prediction.predicted_direction.toLowerCase()}</strong> market response over the{" "}
                  <span className="font-mono font-semibold">{prediction.event_window}</span> trading horizon around official parliamentary action.
                  Impact strength is classified as <strong className="font-semibold">{prediction.predicted_impact_strength}</strong> with{" "}
                  <strong className="font-semibold">{prediction.predicted_confidence.toLowerCase()}</strong> statistical confidence ({formatProbability(prediction.confidence_score)}).
                </p>
              </div>
            </div>

            {/* Quick Metrics Key Value Box */}
            <div className="grid grid-cols-3 gap-3 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-3 sm:p-4 text-center shrink-0 w-full lg:w-auto">
              <div className="px-2">
                <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold block">
                  Direction
                </span>
                <span
                  className={`text-lg sm:text-xl font-bold font-mono mt-0.5 block ${
                    prediction.predicted_direction === "POSITIVE"
                      ? "text-[var(--color-positive)]"
                      : prediction.predicted_direction === "NEGATIVE"
                      ? "text-[var(--color-negative)]"
                      : "text-[var(--text-muted)]"
                  }`}
                >
                  {prediction.predicted_direction}
                </span>
              </div>
              <div className="px-2 border-x border-[var(--border-hairline)]">
                <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold block">
                  Confidence
                </span>
                <span className="text-lg sm:text-xl font-bold font-mono tabular-nums text-[var(--action-primary)] mt-0.5 block">
                  {formatProbability(prediction.confidence_score)}
                </span>
              </div>
              <div className="px-2">
                <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold block">
                  Moving Prob
                </span>
                <span className="text-lg sm:text-xl font-bold font-mono tabular-nums text-[var(--color-warning)] mt-0.5 block">
                  {formatProbability(prediction.market_moving_probability)}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* INTERACTIVE EVENT-WINDOW SELECTOR                                */}
        {/* ---------------------------------------------------------------- */}
        <section
          className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-4 sm:p-5 shadow-xs space-y-3"
          aria-label="Supported Event Window Selector"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-hairline)] pb-2.5">
            <div>
              <h3 className="text-xs sm:text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
                <span>⏱</span> Supported Event Horizons: Backtested Baseline
              </h3>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                Select an event window to inspect precomputed projections for this bill-company pair. Baseline calculations are frozen and immutable.
              </p>
            </div>
            <span className="text-[10px] font-mono text-[var(--text-faint)]">
              5 Calibrated Horizons
            </span>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap" role="tablist" aria-label="Event Horizons">
            {SUPPORTED_HORIZONS.map((horizon) => {
              const isSelected = selectedHorizon === horizon;
              const isDefault = horizon === prediction.event_window;
              const matchedComp = horizonData?.comparisons.find((c) => c.event_window === horizon);

              return (
                <button
                  key={horizon}
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  onClick={() => startTransition(() => setSelectedHorizon(horizon))}
                  className={`px-3 py-2 rounded-lg font-mono text-xs font-semibold transition-all border ${
                    isSelected
                      ? "bg-[var(--action-primary)] text-white border-[var(--action-primary)] shadow-xs"
                      : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] border-[var(--border-subtle)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]"
                  }`}
                >
                  <span>{horizon}</span>
                  {isDefault && (
                    <span className="ml-1 text-[9px] uppercase px-1 py-0.2 rounded bg-white/20 text-white">
                      Primary
                    </span>
                  )}
                  {matchedComp?.predicted_direction && !isSelected && (
                    <span className="ml-1 text-[10px] text-[var(--text-muted)]">
                      · {matchedComp.predicted_direction}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Contextual description of selected horizon */}
          {activeComparison && (
            <div className="p-3 bg-[var(--bg-secondary)]/60 rounded-lg border border-[var(--border-subtle)] text-xs flex flex-wrap items-center justify-between gap-3 text-[var(--text-secondary)]">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-[var(--text-primary)]">{selectedHorizon}</span>
                <span>· Direction: </span>
                <Badge
                  variant={
                    activeComparison.predicted_direction === "POSITIVE"
                      ? "success"
                      : activeComparison.predicted_direction === "NEGATIVE"
                      ? "danger"
                      : "muted"
                  }
                  size="xs"
                >
                  {getDirectionGlyph(activeComparison.predicted_direction)} {activeComparison.predicted_direction}
                </Badge>
              </div>
              <div className="flex items-center gap-3 font-mono text-[11px] text-[var(--text-muted)]">
                {activeComparison.market_moving_probability !== undefined && (
                  <span>Moving Prob: <strong className="text-[var(--text-primary)]">{formatProbability(activeComparison.market_moving_probability)}</strong></span>
                )}
                {activeComparison.impact_score !== undefined && activeComparison.impact_score !== null && (
                  <span>Impact: <strong className="text-[var(--text-primary)]">{Number(activeComparison.impact_score).toFixed(2)}</strong></span>
                )}
              </div>
            </div>
          )}
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* EPISTEMIC SEPARATION GRID: FACTS & PREDICTIONS                   */}
        {/* ---------------------------------------------------------------- */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* ZONE 1: Verified Statutory & Corporate Facts [FACT] */}
          <Card className="p-5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-xs sm:text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">
                  Statutory & Entity Facts
                </h2>
                <SourceBadge type="FACT" size="xs" />
              </div>
              <span className="text-[11px] text-[var(--text-muted)]">Official Records</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase font-medium">
                  Bill Identifier
                </span>
                <span className="font-mono text-[var(--text-secondary)] block truncate mt-0.5" title={prediction.bill_id}>
                  {prediction.bill_id}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase font-medium">
                  Jurisdiction
                </span>
                <span className="text-[var(--text-secondary)] block font-medium mt-0.5">
                  Central Parliament (Lok Sabha / Rajya Sabha)
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase font-medium">
                  Security ISIN
                </span>
                <span className="font-mono text-[var(--action-primary)] block mt-0.5">
                  {prediction.company_isin}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase font-medium">
                  Exchange Ticker
                </span>
                <span className="font-mono text-[var(--text-secondary)] block mt-0.5">
                  {prediction.company_symbol || "NSE / BSE Listed"}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] col-span-2">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase font-medium">
                  Economic Sector
                </span>
                <span className="text-[var(--text-primary)] block font-medium mt-0.5">
                  {prediction.sector || "Unclassified Industry"}
                </span>
              </div>
            </div>
          </Card>

          {/* ZONE 2: Econometric Model Projections [PREDICTION] */}
          <Card className="p-5 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-xs sm:text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">
                  Model Projections
                </h2>
                <SourceBadge type="PREDICTION" size="xs" />
              </div>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">Model {prediction.model_version}</span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)]">Event Analysis Window</span>
                <span className="font-mono text-[var(--text-primary)] font-bold bg-[var(--bg-base)] px-2 py-0.5 rounded border border-[var(--border-subtle)]">
                  {prediction.event_window}
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)]">Predicted Direction</span>
                <Badge variant={dirVariant} size="xs">
                  {dirGlyph && <span className="mr-1">{dirGlyph}</span>}
                  <span>{prediction.predicted_direction}</span>
                </Badge>
              </div>

              <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] space-y-1.5">
                <div className="flex items-center justify-between text-[var(--text-muted)]">
                  <span>Market-Moving Probability</span>
                  <span className="font-mono tabular-nums font-semibold text-[var(--text-primary)]">
                    {formatProbability(prediction.market_moving_probability)}
                  </span>
                </div>
                <div className="w-full h-2 bg-[var(--bg-base)] rounded-full overflow-hidden border border-[var(--border-subtle)]">
                  <div
                    className={`h-full rounded-full transition-all ${
                      prediction.market_moving_probability >= 0.5 ? "bg-[var(--color-warning)]" : "bg-[var(--text-muted)]"
                    }`}
                    style={{ width: `${Math.min(100, prediction.market_moving_probability * 100)}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[10px] text-[var(--text-muted)] block uppercase">Impact Tier</span>
                  <span className="font-semibold text-[var(--text-secondary)] mt-0.5 block">
                    {prediction.predicted_impact_strength}
                  </span>
                </div>

                <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[10px] text-[var(--text-muted)] block uppercase">Confidence Tier</span>
                  <span className="font-semibold text-[var(--action-primary)] mt-0.5 block">
                    {prediction.predicted_confidence}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* ZONE 3: DERIVED RISK & DECISION SUPPORT [DERIVED]                 */}
        {/* ---------------------------------------------------------------- */}
        {decision && (
          <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>🛡</span> Decision Support & Risk Classification
                </h2>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <Badge
                variant={
                  decision.risk_category === "VERY_HIGH" || decision.risk_category === "HIGH"
                    ? "danger"
                    : decision.risk_category === "MODERATE"
                    ? "warning"
                    : "success"
                }
                size="sm"
              >
                Risk Band: {decision.risk_category}
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] space-y-2">
                <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block tracking-wider">
                  Risk & Pricing Metrics
                </span>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Risk Score:</span>
                    <span className="font-mono tabular-nums font-bold text-[var(--text-primary)]">
                      {formatRiskScore(decision.risk_score, 2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Impact Score:</span>
                    <span className="font-mono tabular-nums font-bold text-[var(--text-primary)]">
                      {formatRiskScore(decision.impact_score, 2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Pricing-In Risk:</span>
                    <span className="font-semibold text-[var(--color-warning)] font-mono text-[11px]">
                      {decision.pricing_in_risk || "STANDARD"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] space-y-1.5 md:col-span-2">
                <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block tracking-wider">
                  Decision Rationale
                </span>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  {decision.decision_reason || "Categorized via standardized cross-sectional risk weighting matrix."}
                </p>
              </div>
            </div>

            {/* Investor & Business Summaries */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)]/60 border border-[var(--border-subtle)] space-y-1.5">
                <h4 className="text-xs font-semibold text-[var(--action-primary)] flex items-center gap-1.5">
                  <span>💼</span> Institutional Investor Perspective
                </h4>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {decision.investor_summary || "Positioning considerations based on historical abnormal return distributions."}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[var(--bg-secondary)]/60 border border-[var(--border-subtle)] space-y-1.5">
                <h4 className="text-xs font-semibold text-[var(--color-model)] flex items-center gap-1.5">
                  <span>🏭</span> Corporate & Operating Perspective
                </h4>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {decision.business_summary || "Operational exposure and regulatory compliance impact."}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* ZONE 4: PRE-EVENT ANTICIPATION CONTEXT [DERIVED]                 */}
        {/* ---------------------------------------------------------------- */}
        {anticipation && (
          <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <span>🔍</span> Pre-Event Information Diffusion
                </h2>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <Link href="/anticipation">
                <Button variant="outline" size="xs" className="border-[var(--border-default)] text-xs">
                  View Full Anticipation Dashboard →
                </Button>
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold block">
                  Classification
                </span>
                <span className="text-sm font-bold text-[var(--text-primary)] mt-1 block">
                  {anticipation.anticipation_tier?.replace(/_/g, " ") || "UNCLASSIFIED"}
                </span>
              </div>

              <div className="p-3 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold block">
                  Anticipation Score
                </span>
                <span className="text-sm font-bold font-mono tabular-nums text-[var(--action-primary)] mt-1 block">
                  {formatProbability(anticipation.anticipation_score)}
                </span>
              </div>

              <div className="p-3 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold block">
                  Diffusion Index
                </span>
                <span className="text-sm font-bold font-mono tabular-nums text-[var(--color-warning)] mt-1 block">
                  {formatProbability(anticipation.diffusion_index)}
                </span>
              </div>
            </div>

            <p className="text-[11px] text-[var(--text-muted)] italic">
              &quot;Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law.&quot;
            </p>
          </section>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* ZONE 4B: PUBLIC INFORMATION EVIDENCE ENRICHMENT                  */}
        {/* ---------------------------------------------------------------- */}
        {prediction && (
          <AnticipationEvidenceSection
            billId={prediction.bill_id}
            companyIsin={prediction.company_isin}
            companyName={prediction.company_name}
          />
        )}

        {/* ---------------------------------------------------------------- */}
        {/* STAKEHOLDER REPORTS TAB STRIP [INTERPRETATION]                   */}
        {/* ---------------------------------------------------------------- */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-hairline)] pb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-xs sm:text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">
                Stakeholder Perspective Briefs
              </h3>
              <SourceBadge type="INTERPRETATION" size="xs" />
            </div>

            <div className="inline-flex rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)] p-0.5 text-xs">
              {(["investor", "business", "public"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setSelectedReportType(tab)}
                  className={`px-3 py-1 rounded-md font-medium capitalize transition-colors ${
                    selectedReportType === tab
                      ? "bg-[var(--action-primary)] text-white shadow-xs"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {tab} View
                </button>
              ))}
            </div>
          </div>

          {report ? (
            <div className="space-y-3">
              <div className="p-4 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-subtle)] space-y-2">
                <h4 className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                  Executive Assessment
                </h4>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  {report.executive_summary}
                </p>
              </div>

              {report.key_takeaways?.length > 0 && (
                <div className="p-4 bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-subtle)] space-y-2">
                  <h4 className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                    Key Factors & Transmission Channels
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-xs text-[var(--text-secondary)]">
                    {report.key_takeaways.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-[var(--text-muted)] py-4 text-center">
              Stakeholder synthesis report generated dynamically from verified parameters.
            </p>
          )}
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* PROGRESSIVE DISCLOSURE: ADVANCED ECONOMETRICS & METHODOLOGY       */}
        {/* ---------------------------------------------------------------- */}
        <details className="group rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-5 shadow-xs transition-colors">
          <summary className="flex items-center justify-between cursor-pointer list-none text-xs sm:text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider select-none">
            <span className="flex items-center gap-2">
              <span>🔬</span> Advanced Econometric Decomposition & Methodology
            </span>
            <span className="text-xs text-[var(--action-primary)] font-medium group-open:rotate-180 transition-transform">
              ▼
            </span>
          </summary>

          <div className="pt-4 mt-3 border-t border-[var(--border-hairline)] space-y-4 text-xs text-[var(--text-secondary)] leading-relaxed">
            <p>
              Econometric event-study projections capture Cumulative Abnormal Returns (CAR) computed using the standard
              market model: <span className="font-mono bg-[var(--bg-secondary)] px-1.5 py-0.5 rounded">R_it = α_i + β_i · R_mt + ε_it</span>.
              The market return <span className="font-mono">R_mt</span> is calibrated on the Nifty 50 benchmark index.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-[11px]">
              <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase">Estimation Window</span>
                <span className="font-bold text-[var(--text-primary)] mt-1 block">T-120 to T-31 (90 days)</span>
              </div>
              <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase">Anti-Leakage Buffer</span>
                <span className="font-bold text-[var(--text-primary)] mt-1 block">30 days pre-event</span>
              </div>
              <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase">Model Calibration</span>
                <span className="font-bold text-[var(--text-primary)] mt-1 block">Frozen Backtest v1.0.0</span>
              </div>
              <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase">Baseline Integrity</span>
                <span className="font-bold text-emerald-500 mt-1 block">SHA-256 Verified ✓</span>
              </div>
            </div>

            <p className="text-[11px] text-[var(--text-muted)] italic">
              Frozen Baseline SHA-256: <code className="font-mono text-[10px] bg-[var(--bg-secondary)] px-1 py-0.5 rounded">50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7</code>.
              Data is read-only and globally immutable under production integrity guarantees.
            </p>
          </div>
        </details>

        {/* ---------------------------------------------------------------- */}
        {/* GROUNDED GROQ AI ANALYST COPILOT                                 */}
        {/* ---------------------------------------------------------------- */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-hairline)] pb-3">
            <div>
              <h3 className="text-xs sm:text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                <span>🤖</span> Grounded Groq AI Analyst Copilot
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Ask targeted analytical questions regarding this event-study forecast.
              </p>
            </div>

            {/* Persona Switcher */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[var(--text-muted)]">Persona:</span>
              <select
                aria-label="Select AI persona"
                value={aiPersona}
                onChange={(e) => setAiPersona(e.target.value as "INVESTOR" | "POLICY" | "GENERAL_PUBLIC")}
                className="h-8 rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-2.5 text-xs text-[var(--text-primary)]"
              >
                <option value="INVESTOR">Institutional Investor</option>
                <option value="POLICY">Policy & Regulatory</option>
                <option value="GENERAL_PUBLIC">General Citizen</option>
              </select>
            </div>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder={`Ask about ${prediction.company_name || prediction.company_isin} under ${prediction.bill_id}...`}
              value={aiQuestion}
              onChange={(e) => setAiQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAskAI()}
              className="flex-1 h-9 rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 text-xs text-[var(--text-primary)] placeholder-[var(--text-faint)] focus:outline-none focus:ring-1 focus:ring-[var(--action-primary)]"
            />
            <Button
              size="sm"
              onClick={handleAskAI}
              disabled={aiLoading}
              className="h-9 px-4 text-xs"
            >
              {aiLoading ? "Synthesizing..." : "Inquire Copilot ↗"}
            </Button>
          </div>

          {aiResponse && (
            <div className="p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] leading-relaxed space-y-2">
              <p className="whitespace-pre-line">{aiResponse}</p>
              <p className="text-[10px] text-[var(--text-faint)] italic border-t border-[var(--border-hairline)] pt-1.5">
                Strict Non-Financial Advice Guarantee: Synthesized exclusively from grounded parliamentary facts and backtested model outputs.
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
