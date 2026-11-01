/**
 * components/companies/CompanyPredictionsSection.tsx
 * ===================================================
 * Quantitative Market Predictions & Institutional Decision Support.
 *
 * Strict Compliance:
 * 1. Mode B Firewall: For intelligence-only entities, immediately renders IntelligenceCompanyFirewall.
 * 2. Prediction Availability: Handles missing/empty predictions cleanly.
 * 3. Neutral institutional wording:
 *    - "Modelled direction"
 *    - "Market-moving classification"
 *    - "Model confidence"
 *    - "Decision-support assessment"
 *    - Strictly NO Buy/Sell/Hold, NO target prices, NO investment recommendations.
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import type {
  CompanyDetailResponse,
  CompanyPredictionStatusResponse,
  DecisionRecordResponse,
} from "@/types/api";
import { IntelligenceCompanyFirewall } from "@/components/firewalls/IntelligenceCompanyFirewall";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, PredictionBadge, SourceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { predictionsApi } from "@/lib/api/predictions";

export interface CompanyPredictionsSectionProps {
  company: CompanyDetailResponse;
  predictionStatus: CompanyPredictionStatusResponse | null;
  className?: string;
}

export function CompanyPredictionsSection({
  company,
  predictionStatus,
  className = "",
}: CompanyPredictionsSectionProps) {
  // Event window filter state
  const [selectedWindow, setSelectedWindow] = useState<string>("ALL");

  // Decision drawer state
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecordResponse | null>(null);
  const [loadingDecisionId, setLoadingDecisionId] = useState<string | null>(null);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  // 1. INTELLIGENCE COMPANY FIREWALL CHECK
  const isQuant = company.is_quant_eligible;
  const isIntel =
    company.universe_type.toLowerCase() === "intelligence" ||
    predictionStatus?.firewall_status === "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS" ||
    !isQuant;

  if (isIntel) {
    return (
      <div className={className} aria-label="Intelligence Company Firewall">
        <IntelligenceCompanyFirewall
          company={company}
          predictionStatus={predictionStatus}
        />
      </div>
    );
  }

  // 2. CHECK ACTUAL PREDICTION AVAILABILITY
  const rawPredictions = (predictionStatus?.predictions || predictionStatus?.items || []) as any[];
  const hasPredictions = Boolean(
    predictionStatus?.has_predictions && rawPredictions.length > 0
  );

  if (!hasPredictions) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Market Impact Predictions</CardTitle>
            <SourceBadge type="PREDICTION" size="xs" showTooltip />
          </div>
        </CardHeader>
        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-elevated)] p-6 text-center space-y-3">
          <span className="text-2xl" aria-hidden="true">📊</span>
          <h4 className="text-sm font-semibold text-[var(--text-primary)]">
            Prediction data is not currently available for this company/bill combination.
          </h4>
          <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed">
            Econometric market projections are calculated exclusively for Central Parliamentary enactments within the frozen backtested production dataset.
          </p>
        </div>
      </Card>
    );
  }

  // Filter by event window
  const eventWindows = ["ALL", "[-30,-1]", "[-5,-1]", "[0,1]", "[0,5]", "[0,20]"];
  const filteredPredictions = rawPredictions.filter((p) => {
    if (selectedWindow === "ALL") return true;
    return p.event_window === selectedWindow;
  });

  // Drill down to decision support
  const handleOpenDecision = async (predId: string) => {
    setLoadingDecisionId(predId);
    setDecisionError(null);
    try {
      const dec = await predictionsApi.getPredictionDecision(predId);
      setSelectedDecision(dec);
    } catch {
      setDecisionError("Failed to retrieve decision record for this prediction.");
    } finally {
      setLoadingDecisionId(null);
    }
  };

  return (
    <div className={`space-y-6 ${className}`} aria-label="Central Quantitative Predictions">
      {/* Disclaimer Banner */}
      <div className="rounded-lg border border-blue-900/50 bg-blue-950/20 p-3.5 text-xs text-[var(--text-secondary)] space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-blue-400 font-semibold">Institutional Methodology Disclosure</span>
          <SourceBadge type="PREDICTION" size="xs" />
        </div>
        <p className="text-[var(--text-secondary)] leading-relaxed text-[11px]">
          Quantitative price projections reflect multi-horizon econometric event study models calibrated on historical market behavior.
          All projections represent neutral statistical estimates. This platform does not provide investment advice, price targets, or trading recommendations.
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 w-full">
            <div className="flex items-center gap-2">
              <CardTitle>Central Market Impact Projections</CardTitle>
              <SourceBadge type="PREDICTION" size="xs" showTooltip />
            </div>
            <span className="text-xs font-mono font-tabular text-[var(--text-secondary)]">
              {filteredPredictions.length} modelled event windows
            </span>
          </div>
        </CardHeader>

        {/* Event Window Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 pb-3 border-b border-[var(--border-default)] text-xs">
          <span className="text-[var(--text-secondary)] mr-1 font-medium">Event Window:</span>
          {eventWindows.map((win) => (
            <button
              key={win}
              onClick={() => setSelectedWindow(win)}
              className={`px-2.5 py-1 rounded text-xs font-medium font-mono font-tabular transition-colors ${
                selectedWindow === win
                  ? "bg-[var(--action-primary)] text-[var(--text-primary)] shadow-xs"
                  : "bg-[var(--bg-surface-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-default)]"
              }`}
            >
              {win === "ALL" ? "All Windows" : win}
            </button>
          ))}
        </div>

        {/* Prediction Table */}
        <div className="overflow-x-auto -mx-6">
          <table className="financial-table w-full text-left text-xs border-collapse min-w-[700px]">
            <thead>
              <tr className="border-b border-[var(--border-default)] bg-[var(--bg-surface-elevated)] text-[var(--text-secondary)] font-semibold">
                <th scope="col" className="py-2.5 px-4 w-4/12">Legislative Measure</th>
                <th scope="col" className="py-2.5 px-3 w-2/12 font-tabular">Event Window</th>
                <th scope="col" className="py-2.5 px-3 w-2/12">Modelled Direction</th>
                <th scope="col" className="py-2.5 px-3 w-2/12">Market Classification</th>
                <th scope="col" className="py-2.5 px-3 w-2/12 text-center">Decision Support</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-default)]">
              {filteredPredictions.map((pred) => {
                const billId = pred.bill_id;
                const billTitle =
                  pred.bill_title ||
                  billId
                    ?.replace(/-/g, " ")
                    ?.replace(/\b\w/g, (c: string) => c.toUpperCase()) ||
                  "Legislative Bill";

                return (
                  <tr
                    key={pred.prediction_id}
                    className="hover:bg-[var(--bg-surface-elevated)]/60 transition-colors"
                  >
                    {/* Bill Title */}
                    <td className="py-3 px-4">
                      <Link
                        href={`/bills/${encodeURIComponent(billId)}`}
                        className="font-semibold text-[var(--text-primary)] hover:text-[var(--action-primary)] transition-colors block text-sm"
                      >
                        {billTitle}
                      </Link>
                      <Link
                        href={`/predictions/${encodeURIComponent(pred.prediction_id)}`}
                        className="text-[10px] text-[var(--action-primary)] hover:underline block mt-0.5 font-mono font-tabular"
                        title="View full prediction dossier"
                      >
                        Dossier ID: {pred.prediction_id} ↗
                      </Link>
                    </td>

                    {/* Window */}
                    <td className="py-3 px-3">
                      <span className="font-mono font-tabular text-xs font-semibold text-[var(--text-primary)] bg-[var(--bg-surface-elevated)] px-2 py-0.5 rounded border border-[var(--border-default)]">
                        {pred.event_window}
                      </span>
                    </td>

                    {/* Modelled Direction */}
                    <td className="py-3 px-3">
                      <PredictionBadge
                        direction={pred.predicted_direction}
                        confidence={pred.predicted_confidence}
                        size="xs"
                      />
                      <span className="text-[10px] text-[var(--text-muted)] block mt-0.5 font-tabular">
                        Strength: {pred.predicted_impact_strength || "LOW"}
                      </span>
                    </td>

                    {/* Market-Moving Classification */}
                    <td className="py-3 px-3">
                      <div className="space-y-0.5">
                        <span
                          className={`inline-block font-semibold text-[11px] ${
                            pred.predicted_market_moving
                              ? "text-amber-400"
                              : "text-[var(--text-secondary)]"
                          }`}
                        >
                          {pred.predicted_market_moving
                            ? "⚡ Market-Moving"
                            : "Standard Volatility"}
                        </span>
                        {typeof pred.market_moving_probability === "number" && (
                          <span className="text-[10px] text-[var(--text-muted)] block font-mono font-tabular">
                            Prob: {(pred.market_moving_probability * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Decision Support Trigger */}
                    <td className="py-3 px-3 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <Link href={`/predictions/${encodeURIComponent(pred.prediction_id)}`}>
                          <Button
                            variant="ghost"
                            size="xs"
                            className="text-xs text-[var(--action-primary)] hover:bg-[var(--bg-surface-elevated)]"
                            aria-label={`View full prediction dossier for ${billTitle}`}
                          >
                            Dossier ↗
                          </Button>
                        </Link>
                        <Button
                          variant="outline"
                          size="xs"
                          onClick={() => handleOpenDecision(pred.prediction_id)}
                          disabled={loadingDecisionId === pred.prediction_id}
                          className="text-xs border-[var(--border-default)] hover:border-[var(--border-strong)]"
                          aria-label={`View decision assessment for ${billTitle}`}
                        >
                          {loadingDecisionId === pred.prediction_id
                            ? "Loading..."
                            : "⚖ Assessment"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Decision Support Drawer / Modal */}
      {selectedDecision && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-fade-in"
          role="dialog"
          aria-modal="true"
          aria-labelledby="decision-modal-title"
        >
          <div className="w-full max-w-2xl rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-start justify-between gap-3 border-b border-[var(--border-default)] pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 id="decision-modal-title" className="text-sm font-semibold text-[var(--text-primary)]">
                    Decision-Support Assessment
                  </h3>
                  <SourceBadge type="DERIVED" size="xs" />
                </div>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  Window: <span className="font-mono font-tabular text-[var(--text-primary)]">{selectedDecision.event_window}</span> · ID: <span className="font-mono font-tabular">{selectedDecision.decision_id}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedDecision(null)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-base p-1"
                aria-label="Close decision modal"
              >
                ✕
              </button>
            </div>

            {/* Metric Chips */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="rounded bg-[var(--bg-surface-elevated)] p-2.5 border border-[var(--border-default)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase">Impact Category</span>
                <span className="font-bold text-[var(--text-primary)]">{selectedDecision.impact_category}</span>
              </div>
              <div className="rounded bg-[var(--bg-surface-elevated)] p-2.5 border border-[var(--border-default)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase">Risk Category</span>
                <span className="font-bold text-[var(--text-primary)]">{selectedDecision.risk_category}</span>
              </div>
              <div className="rounded bg-[var(--bg-surface-elevated)] p-2.5 border border-[var(--border-default)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase">Pricing-In Risk</span>
                <span className="font-bold text-amber-400">{selectedDecision.pricing_in_risk}</span>
              </div>
              <div className="rounded bg-[var(--bg-surface-elevated)] p-2.5 border border-[var(--border-default)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase">Impact Score</span>
                <span className="font-bold font-mono font-tabular text-blue-400">
                  {typeof selectedDecision.impact_score === "number"
                    ? selectedDecision.impact_score.toFixed(2)
                    : selectedDecision.impact_score}
                </span>
              </div>
            </div>

            {/* Decision Reason */}
            {selectedDecision.decision_reason && (
              <div className="space-y-1 text-xs">
                <span className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider block">
                  Model Rationale &amp; Transmission Rationale
                </span>
                <p className="text-[var(--text-secondary)] bg-[var(--bg-surface-elevated)] p-3 rounded border border-[var(--border-default)] leading-relaxed">
                  {selectedDecision.decision_reason}
                </p>
              </div>
            )}

            {/* Stakeholder Summaries */}
            <div className="space-y-2 pt-2 border-t border-[var(--border-default)] text-xs">
              <h4 className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                Persona Perspective Summaries
              </h4>

              {selectedDecision.investor_summary && (
                <div className="rounded bg-[var(--bg-surface-elevated)] p-3 border border-[var(--border-default)] space-y-1">
                  <span className="font-semibold text-blue-400 block text-[11px]">
                    💼 Investor Summary
                  </span>
                  <p className="text-[var(--text-secondary)] leading-relaxed">
                    {selectedDecision.investor_summary}
                  </p>
                </div>
              )}

              {selectedDecision.business_summary && (
                <div className="rounded bg-[var(--bg-surface-elevated)] p-3 border border-[var(--border-default)] space-y-1">
                  <span className="font-semibold text-emerald-400 block text-[11px]">
                    🏢 Corporate / Enterprise Summary
                  </span>
                  <p className="text-[var(--text-secondary)] leading-relaxed">
                    {selectedDecision.business_summary}
                  </p>
                </div>
              )}

              {selectedDecision.public_summary && (
                <div className="rounded bg-[var(--bg-surface-elevated)] p-3 border border-[var(--border-default)] space-y-1">
                  <span className="font-semibold text-purple-400 block text-[11px]">
                    👥 Industry &amp; Public Summary
                  </span>
                  <p className="text-[var(--text-secondary)] leading-relaxed">
                    {selectedDecision.public_summary}
                  </p>
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-[var(--border-default)]">
              <Link
                href={`/predictions/${encodeURIComponent(selectedDecision.prediction_id || `${selectedDecision.bill_id}_${selectedDecision.company_isin}_${selectedDecision.event_window}`)}`}
                className="text-xs text-[var(--action-primary)] hover:underline font-semibold inline-flex items-center gap-1"
              >
                <span>Open Full Prediction Dossier →</span>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedDecision(null)}
                className="text-xs"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {decisionError && (
        <p className="text-xs text-rose-400 font-medium">{decisionError}</p>
      )}
    </div>
  );
}

export default CompanyPredictionsSection;
