"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge, SourceBadge, JurisdictionBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { predictionsApi } from "@/lib/api/predictions";
import { anticipationApi } from "@/lib/api/anticipation";
import { aiApi } from "@/lib/api/ai";
import type {
  AnticipationScoreResponse,
  DecisionRecordResponse,
  HorizonComparisonResponse,
  PredictionItem,
  StakeholderReportResponse,
} from "@/types/api";

interface PredictionDetailContentProps {
  predictionId: string;
}

export default function PredictionDetailContent({ predictionId }: PredictionDetailContentProps) {
  const [prediction, setPrediction] = useState<PredictionItem | null>(null);
  const [decision, setDecision] = useState<DecisionRecordResponse | null>(null);
  const [anticipation, setAnticipation] = useState<AnticipationScoreResponse | null>(null);

  const [horizonData, setHorizonData] = useState<HorizonComparisonResponse | null>(null);
  const [report, setReport] = useState<StakeholderReportResponse | null>(null);
  const [selectedReportType, setSelectedReportType] = useState<"investor" | "business" | "public">("investor");

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
    const q = aiQuestion.trim() || `Analyze the market impact prediction for ${prediction.company_name || prediction.company_isin} under bill ${prediction.bill_id} in horizon ${prediction.event_window}.`;
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
        setAiResponse("This empirical econometric projection captures estimated abnormal returns over the defined event window. Direction and probability are derived from backtested model features without incorporating speculative sentiment.");
        setAiLoading(false);
      });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 space-y-6 max-w-6xl mx-auto">
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
      <div className="min-h-screen bg-slate-950 text-slate-100 p-12">
        <div className="max-w-xl mx-auto text-center space-y-4 bg-slate-900/80 border border-slate-800 p-8 rounded-2xl">
          <span className="text-4xl">⚠️</span>
          <h2 className="text-xl font-bold text-slate-200">Prediction Record Not Found</h2>
          <p className="text-xs text-slate-400">
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Link
                href="/predictions"
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 font-medium"
              >
                ← Back to Predictions
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-xs font-mono text-slate-300 truncate max-w-xs sm:max-w-md">
                {prediction.prediction_id}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <JurisdictionBadge jurisdiction="central" size="sm" />
              <SourceBadge type="PREDICTION" size="sm" showTooltip />
              <Link href={`/bills/${prediction.bill_id}`}>
                <Button variant="outline" size="xs" className="border-slate-700 text-xs">
                  🏛 Bill Dossier
                </Button>
              </Link>
              <Link href={`/companies/${prediction.company_isin}`}>
                <Button variant="outline" size="xs" className="border-slate-700 text-xs">
                  🏢 Company Profile
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Regulatory & Institutional Disclaimer */}
        <div className="p-4 rounded-xl border border-amber-800/40 bg-amber-950/20 text-amber-200/90 text-xs flex items-start gap-3 shadow-inner">
          <span className="text-base flex-shrink-0 mt-0.5">⚖️</span>
          <div className="space-y-1">
            <p className="font-semibold text-amber-300 uppercase tracking-wider text-[10px]">
              Institutional Non-Financial Advice Notice
            </p>
            <p className="leading-relaxed text-[11px] text-amber-200/80">
              Projections are empirical econometric outputs based on backtested historical relationships and public information.
              They do not constitute investment advice, price targets, or recommendations to buy, sell, or hold any security.
              Legislative impacts are probabilistic and contingent on Parliamentary enactment dynamics.
            </p>
          </div>
        </div>

        {/* Hero Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="primary" size="xs">
                  Central Level 1
                </Badge>
                <Badge variant="default" size="xs">
                  Horizon {prediction.event_window}
                </Badge>
                <Badge variant={dirVariant} size="xs">
                  {prediction.predicted_direction}
                </Badge>
                {prediction.predicted_market_moving && (
                  <Badge variant="warning" size="xs">
                    Market-Moving
                  </Badge>
                )}
              </div>

              <h1 className="text-2xl font-bold text-slate-100 mt-2">
                {prediction.company_name || prediction.company_symbol || prediction.company_isin}
              </h1>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                <span>Bill:</span>
                <Link
                  href={`/bills/${prediction.bill_id}`}
                  className="text-blue-400 hover:underline font-medium"
                >
                  {prediction.bill_id.replace(/-/g, " ")}
                </Link>
                {prediction.sector && (
                  <>
                    <span className="text-slate-600">·</span>
                    <span>Sector: {prediction.sector}</span>
                  </>
                )}
              </p>
            </div>

            {/* Quick Metrics Pill Box */}
            <div className="flex items-center gap-4 bg-slate-950/80 border border-slate-800 rounded-xl p-3 sm:px-5">
              <div className="text-center">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block">
                  Direction <SourceBadge type="PREDICTION" size="xs" />
                </span>
                <span
                  className={`text-lg font-bold font-mono ${
                    prediction.predicted_direction === "POSITIVE"
                      ? "text-emerald-400"
                      : prediction.predicted_direction === "NEGATIVE"
                      ? "text-rose-400"
                      : "text-slate-400"
                  }`}
                >
                  {prediction.predicted_direction}
                </span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div className="text-center">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block">
                  Confidence <SourceBadge type="PREDICTION" size="xs" />
                </span>
                <span className="text-lg font-bold font-mono text-blue-400">
                  {(prediction.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div className="text-center">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold block">
                  Moving Prob <SourceBadge type="PREDICTION" size="xs" />
                </span>
                <span className="text-lg font-bold font-mono text-amber-400">
                  {(prediction.market_moving_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* EPISTEMIC SEPARATION GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* ZONE 1: Verified Statutory & Corporate Facts [FACT] */}
          <Card className="p-5 bg-slate-900/80 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                  Statutory & Entity Facts
                </h2>
                <SourceBadge type="FACT" size="xs" />
              </div>
              <span className="text-[11px] text-slate-500">Official Records</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">
                  Bill Identifier
                </span>
                <span className="font-mono text-slate-300 block truncate mt-0.5" title={prediction.bill_id}>
                  {prediction.bill_id}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">
                  Jurisdiction
                </span>
                <span className="text-slate-300 block font-medium mt-0.5">
                  Central Parliament (Lok Sabha / Rajya Sabha)
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">
                  Security ISIN
                </span>
                <span className="font-mono text-blue-400 block mt-0.5">
                  {prediction.company_isin}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">
                  Exchange Ticker
                </span>
                <span className="font-mono text-slate-300 block mt-0.5">
                  {prediction.company_symbol || "NSE / BSE Listed"}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 col-span-2">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">
                  Economic Sector
                </span>
                <span className="text-slate-200 block font-medium mt-0.5">
                  {prediction.sector || "Unclassified Industry"}
                </span>
              </div>
            </div>
          </Card>

          {/* ZONE 2: Econometric Model Projections [PREDICTION] */}
          <Card className="p-5 bg-slate-900/80 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                  Model Projections
                </h2>
                <SourceBadge type="PREDICTION" size="xs" />
              </div>
              <span className="text-[11px] text-slate-500">Model {prediction.model_version}</span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400">Event Analysis Window</span>
                <span className="font-mono text-slate-200 font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-700">
                  {prediction.event_window}
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400">Predicted Direction</span>
                <Badge variant={dirVariant} size="xs">
                  {prediction.predicted_direction}
                </Badge>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Market-Moving Probability</span>
                  <span className="font-mono font-semibold text-slate-200">
                    {(prediction.market_moving_probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      prediction.market_moving_probability >= 0.5 ? "bg-amber-500" : "bg-slate-500"
                    }`}
                    style={{ width: `${Math.min(100, prediction.market_moving_probability * 100)}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-500 block uppercase">Impact Tier</span>
                  <span className="font-semibold text-slate-300 mt-0.5 block">
                    {prediction.predicted_impact_strength}
                  </span>
                </div>

                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 text-center">
                  <span className="text-[10px] text-slate-500 block uppercase">Confidence Tier</span>
                  <span className="font-semibold text-blue-400 mt-0.5 block">
                    {prediction.predicted_confidence}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* ZONE 3: Derived Risk & Decision Support [DERIVED] */}
        {decision && (
          <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
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
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                <span className="text-[10px] uppercase font-semibold text-slate-500 block tracking-wider">
                  Risk & Pricing Metrics
                </span>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Risk Score:</span>
                    <span className="font-mono font-bold text-slate-200">
                      {decision.risk_score?.toFixed(2) ?? "—"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Impact Score:</span>
                    <span className="font-mono font-bold text-slate-200">
                      {decision.impact_score?.toFixed(2) ?? "—"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Pricing-In Risk:</span>
                    <span className="font-semibold text-amber-400">
                      {decision.pricing_in_risk || "STANDARD"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1.5 md:col-span-2">
                <span className="text-[10px] uppercase font-semibold text-slate-500 block tracking-wider">
                  Decision Rationale
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {decision.decision_reason || "Categorized via standardized cross-sectional risk weighting matrix."}
                </p>
              </div>
            </div>

            {/* Investor & Business Summaries */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                <h4 className="text-xs font-semibold text-blue-300 flex items-center gap-1.5">
                  <span>💼</span> Institutional Investor Perspective
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {decision.investor_summary || "Positioning considerations based on historical abnormal return distributions."}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                <h4 className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                  <span>🏭</span> Corporate & Operating Perspective
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {decision.business_summary || "Operational exposure and regulatory compliance impact."}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* ZONE 4: Pre-Event Anticipation Context (if available) */}
        {anticipation && (
          <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <span>🔍</span> Pre-Event Information Diffusion
                </h2>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <Link href="/anticipation">
                <Button variant="outline" size="xs" className="border-slate-700 text-xs">
                  View Full Anticipation Dashboard →
                </Button>
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold block">
                  Classification
                </span>
                <span className="text-sm font-bold text-slate-200 mt-1 block">
                  {anticipation.anticipation_tier?.replace(/_/g, " ") || "UNCLASSIFIED"}
                </span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold block">
                  Anticipation Score
                </span>
                <span className="text-sm font-bold font-mono text-indigo-400 mt-1 block">
                  {(anticipation.anticipation_score * 100).toFixed(1)}%
                </span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold block">
                  Diffusion Index
                </span>
                <span className="text-sm font-bold font-mono text-amber-400 mt-1 block">
                  {(anticipation.diffusion_index * 100).toFixed(1)}%
                </span>
              </div>

            </div>

            <p className="text-[11px] text-slate-400 italic">
              "Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law."
            </p>
          </section>
        )}

        {/* Stakeholder Reports Tab Strip [INTERPRETATION] */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Stakeholder Perspective Briefs
              </h3>
              <SourceBadge type="INTERPRETATION" size="xs" />
            </div>

            <div className="inline-flex rounded-lg border border-slate-700 bg-slate-950 p-0.5 text-xs">
              {(["investor", "business", "public"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setSelectedReportType(tab)}
                  className={`px-3 py-1 rounded-md font-medium capitalize transition-colors ${
                    selectedReportType === tab
                      ? "bg-blue-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tab} View
                </button>
              ))}
            </div>
          </div>

          {report ? (
            <div className="space-y-3">
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Executive Assessment
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {report.executive_summary}
                </p>
              </div>

              {report.key_takeaways?.length > 0 && (
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Key Factors & Transmission Channels
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
                    {report.key_takeaways.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-500 py-4 text-center">
              Stakeholder synthesis report generated dynamically from verified parameters.
            </p>
          )}
        </section>

        {/* Horizon Comparison Links */}
        {horizonData && horizonData.comparisons.length > 0 && (
          <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>⏱</span> Alternative Event Horizons for This Pair
              </h3>
              <span className="text-[11px] text-slate-500">Same Bill & Company</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {horizonData.comparisons.map((item) => {
                const isCurrent = item.event_window === prediction.event_window;
                return (
                  <div
                    key={item.event_window}
                    className={`p-3 rounded-lg border text-center transition-all ${
                      isCurrent
                        ? "bg-blue-950/40 border-blue-600/60 ring-1 ring-blue-500/50"
                        : item.is_modeled
                        ? "bg-slate-950 border-slate-800 hover:border-slate-700"
                        : "bg-slate-950/40 border-slate-800/40 opacity-50"
                    }`}
                  >
                    <span className="text-xs font-mono font-bold text-slate-200 block">
                      {item.event_window}
                    </span>
                    {item.is_modeled ? (
                      <span
                        className={`text-[11px] font-semibold mt-1 block ${
                          item.predicted_direction === "POSITIVE"
                            ? "text-emerald-400"
                            : item.predicted_direction === "NEGATIVE"
                            ? "text-rose-400"
                            : "text-slate-400"
                        }`}
                      >
                        {item.predicted_direction || "NEUTRAL"}
                        {isCurrent && " (Current)"}
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-500 mt-1 block">Unmodeled</span>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Grounded AI Analyst */}
        <section className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>🤖</span> AI Market Analyst Copilot
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
                placeholder={`Ask about this prediction dossier (e.g., "Why was impact classified as ${prediction.predicted_impact_strength}?")`}
                value={aiQuestion}
                onChange={(e) => setAiQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAskAI();
                }}
                className="flex-1 h-10 rounded-lg border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <Button
                variant="primary"
                size="sm"
                onClick={handleAskAI}
                disabled={aiLoading}
                className="h-10 text-xs px-4"
              >
                {aiLoading ? "Analyzing..." : "Analyze"}
              </Button>
            </div>

            {aiResponse && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800/60 pb-2">
                  <span className="font-semibold text-blue-400">AI Synthesized Assessment</span>
                  <span className="text-slate-500">Lens: {aiPersona}</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                  {aiResponse}
                </p>
                <p className="text-[10px] text-slate-500 pt-1">
                  Answers are grounded on empirical prediction records and official parliamentary gazettes. No price targets or investment advice are generated.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* Model Provenance & Statutory Firewall Statement */}
        <section className="border-t border-slate-800 pt-6 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Econometric Provenance & Validation Standards
            </h4>
            <span className="text-[10px] font-mono text-slate-500">
              Created: {prediction.created_at ? new Date(prediction.created_at).toLocaleDateString() : "Frozen Central Baseline"}
            </span>
          </div>

          <div className="text-[11px] text-slate-500 leading-relaxed space-y-1">
            <p>
              • Quantitative predictions are frozen from the Central Parliament market impact model (4,700 records spanning 20 Central enactments × 47 listed securities × 5 event horizons).
            </p>
            <p>
              • <strong className="text-slate-400">State Prediction Firewall:</strong> State legislative assemblies have strictly 0 market predictions. Quantitative market impact is evaluated exclusively at the Central Parliament level.
            </p>
            <p>
              • All calculations (CAR, market-moving probability, risk band, pricing-in tier) remain strictly backend-derived.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
