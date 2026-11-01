/**
 * components/bills/CentralPredictionSection.tsx
 * ==============================================
 * Central Market Predictions section with:
 * - StatePredictionFirewall for all State bills (strictly 0 state predictions)
 * - Central Non-Modelled disclosure for non-modeled Central bills
 * - Quantitative predictions across 5 event windows for eligible Central bills
 * - Institutional Decision Support drill-down drawer/modal
 *
 * Strict Compliance: Neutral institutional language.
 * No Buy/Sell/Hold, price targets, or financial recommendations.
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import type {
  BillSummaryItem,
  BillPredictionStatusResponse,
  DecisionRecordResponse,
} from "@/types/api";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, PredictionBadge, Badge } from "@/components/ui/Badge";
import { PredictionAvailability } from "@/components/coverage/CapabilityBadge";
import { Button } from "@/components/ui/Button";
import { predictionsApi } from "@/lib/api/predictions";

import { formatProbability, formatRiskScore, getDirectionGlyph } from "@/lib/formatters";

export interface CentralPredictionSectionProps {
  bill: BillSummaryItem;
  predictionStatus: BillPredictionStatusResponse | null;
  className?: string;
}

export function CentralPredictionSection({
  bill,
  predictionStatus,
  className = "",
}: CentralPredictionSectionProps) {
  const isState = bill.jurisdiction?.toLowerCase() === "state";
  const [selectedDecision, setSelectedDecision] = useState<DecisionRecordResponse | null>(null);
  const [loadingDecisionId, setLoadingDecisionId] = useState<string | null>(null);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  // 1. STATE LEGISLATION FIREWALL
  if (isState) {
    return (
      <div className={className}>
        <StatePredictionFirewall
          state={bill.state}
          bill={bill}
          predictionStatus={predictionStatus}
        />
      </div>
    );
  }

  // 2. CENTRAL NON-MODELLED BILLS
  const hasPredictions = Boolean(
    predictionStatus?.has_predictions &&
    predictionStatus?.predictions &&
    predictionStatus.predictions.length > 0
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
        <div className="space-y-4">
          <PredictionAvailability
            available={false}
            jurisdiction={bill.jurisdiction}
            firewallStatus={predictionStatus?.firewall_status || "CENTRAL_NON_MODELLED_BILL"}
            message={
              predictionStatus?.message ||
              "Market modelling is not currently available for this bill. Bill is outside the frozen 20 quantitative production set."
            }
          />
          <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)] p-4 text-xs text-[var(--text-muted)] leading-relaxed space-y-2">
            <h5 className="font-semibold text-[var(--text-primary)]">
              Coverage Scope &amp; Non-Modelled Disclosure
            </h5>
            <p className="text-[var(--color-warning)] font-medium">
              {predictionStatus?.message || "Market modelling is not currently available for this bill. Bill is not part of the frozen 20 quantitative production set."}
            </p>
            <p>
              Under research and methodology governance, econometric price prediction models were trained and frozen exclusively on the 20 primary Central Parliamentary enactments.
            </p>
            <p>
              This measure retains comprehensive factual intelligence, provisions, and corporate exposure classifications, but quantitative equity price forecasting is barred.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // 3. CENTRAL MODELLED BILLS
  const predictions = predictionStatus?.predictions || [];

  const handleOpenDecision = async (predId: string) => {
    setLoadingDecisionId(predId);
    setDecisionError(null);
    try {
      const decision = await predictionsApi.getPredictionDecision(predId);
      setSelectedDecision(decision);
    } catch (err) {
      setDecisionError("Institutional decision support record could not be loaded.");
    } finally {
      setLoadingDecisionId(null);
    }
  };

  return (
    <div className={`space-y-4 ${className}`} aria-label="Central market predictions section">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2 w-full">
            <div>
              <CardTitle>Central Market Predictions &amp; Impact Modeling</CardTitle>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Econometric projections across 5 event windows. Neutral institutional analytics only.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="purple" size="xs">
                {predictions.length} Model Projections
              </Badge>
              <SourceBadge type="PREDICTION" size="xs" showTooltip />
            </div>
          </div>
        </CardHeader>

        {/* Mandatory Regulatory Warning */}
        <div className="rounded-md border border-[var(--color-model)]/30 bg-[var(--color-model)]/10 p-3 text-xs text-[var(--text-secondary)] leading-relaxed flex items-start gap-2 mb-4">
          <span className="text-sm mt-0.5" aria-hidden="true">🛡</span>
          <div>
            <span className="font-semibold text-[var(--text-primary)]">Institutional Notice:</span>{" "}
            Projections reflect quantitative econometric models trained on historical parliamentary events.
            Outputs indicate statistical sensitivity and market-moving probability. They do not constitute investment, trading, or portfolio recommendations.
          </div>
        </div>

        {/* Predictions Table */}
        <div className="overflow-x-auto rounded-lg border border-[var(--border-default)]">
          <table className="w-full text-left text-xs text-[var(--text-secondary)]" aria-label="Central predictions table">
            <thead className="bg-[var(--bg-base)] text-[var(--text-muted)] uppercase text-[10px] tracking-wider border-b border-[var(--border-default)]">
              <tr>
                <th scope="col" className="py-3 px-3.5">Company / Entity</th>
                <th scope="col" className="py-3 px-3">Event Window</th>
                <th scope="col" className="py-3 px-3">Projected Direction</th>
                <th scope="col" className="py-3 px-3">Market Moving</th>
                <th scope="col" className="py-3 px-3">Impact Strength</th>
                <th scope="col" className="py-3 px-3 text-right">Confidence</th>
                <th scope="col" className="py-3 px-3 text-right">Decision Support</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)] bg-[var(--bg-surface)]">
              {predictions.map((p: any, idx: number) => {
                const predId = p.prediction_id || `pred-${idx}`;
                const dir = String(p.predicted_direction || "NEUTRAL");
                const isMm = Boolean(p.predicted_market_moving);
                const mmProb = typeof p.market_moving_probability === "number"
                  ? formatProbability(p.market_moving_probability)
                  : "—";
                const confScore = typeof p.model_confidence === "number"
                  ? formatProbability(p.model_confidence)
                  : typeof p.confidence_score === "number"
                  ? formatProbability(p.confidence_score)
                  : "—";

                return (
                  <tr key={predId} className="hover:bg-[var(--table-row-hover)] transition-colors">
                    <td className="py-3 px-3.5 font-sans">
                      <Link
                        href={`/companies/${encodeURIComponent(p.company_isin || p.company_symbol || p.company_name)}`}
                        className="font-semibold text-[var(--text-primary)] hover:text-[var(--action-primary)] transition-colors block text-xs"
                      >
                        {p.company_name || p.company_isin}
                      </Link>
                      <span className="text-[10px] text-[var(--text-muted)] font-mono">
                        {p.company_symbol ? `${p.company_symbol} · ` : ""}
                        {p.company_isin}
                      </span>
                    </td>

                    <td className="py-3 px-3">
                      <span className="text-xs bg-[var(--bg-secondary)] px-2 py-0.5 rounded border border-[var(--border-default)] font-mono font-medium text-[var(--text-secondary)]">
                        {p.event_window}
                      </span>
                    </td>

                    <td className="py-3 px-3 font-sans">
                      <PredictionBadge direction={dir} size="xs" />
                    </td>

                    <td className="py-3 px-3 font-sans">
                      <span
                        className={`text-[11px] font-semibold font-mono tabular-nums ${
                          isMm ? "text-[var(--color-warning)]" : "text-[var(--text-muted)]"
                        }`}
                      >
                        {isMm ? `Yes (${mmProb})` : `No (${mmProb})`}
                      </span>
                    </td>

                    <td className="py-3 px-3 font-sans">
                      <span
                        className={`text-xs uppercase font-medium ${
                          p.predicted_impact_strength === "HIGH"
                            ? "text-[var(--color-negative)]"
                            : p.predicted_impact_strength === "MEDIUM"
                            ? "text-[var(--color-warning)]"
                            : "text-[var(--text-muted)]"
                        }`}
                      >
                        {p.predicted_impact_strength || "LOW"}
                      </span>
                    </td>

                    <td className="py-3 px-3 text-right">
                      <span className="text-xs text-[var(--text-primary)] font-mono tabular-nums">
                        {confScore}{" "}
                        <span className="text-[10px] text-[var(--text-muted)] font-sans">
                          ({p.predicted_confidence || "MOD"})
                        </span>
                      </span>
                    </td>

                    <td className="py-3 px-3 text-right font-sans">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link href={`/predictions/${encodeURIComponent(predId)}`}>
                          <Button
                            variant="ghost"
                            size="xs"
                            className="text-xs text-[var(--action-primary)] hover:bg-[var(--bg-secondary)]"
                            aria-label={`View full prediction dossier for ${predId}`}
                          >
                            Dossier ↗
                          </Button>
                        </Link>
                        <Button
                          variant="outline"
                          size="xs"
                          onClick={() => handleOpenDecision(predId)}
                          disabled={loadingDecisionId === predId}
                          id={`btn-decision-${predId}`}
                          aria-label={`View decision support for ${p.company_name || p.company_isin}`}
                        >
                          {loadingDecisionId === predId ? "Loading..." : "Decision ↗"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Decision Support Drawer / Modal */}
        {selectedDecision && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--overlay-backdrop)] backdrop-blur-xs p-4 animate-fade-in"
            role="dialog"
            aria-modal="true"
            aria-labelledby="decision-modal-title"
          >
            <div className="w-full max-w-2xl rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
                <div>
                  <h3 id="decision-modal-title" className="text-base font-bold text-[var(--text-primary)]">
                    Institutional Decision Support Record
                  </h3>
                  <p className="text-xs text-[var(--text-muted)] font-mono">
                    ISIN: {selectedDecision.company_isin} · Window: {selectedDecision.event_window}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedDecision(null)}
                  className="rounded-lg p-1.5 text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] transition-colors"
                  aria-label="Close modal"
                >
                  ✕
                </button>
              </div>

              {/* Tiers Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-2.5">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">Risk Category</p>
                  <p className="text-xs font-bold text-[var(--color-warning)] mt-0.5">{selectedDecision.risk_category}</p>
                </div>
                <div className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-2.5">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">Pricing-in Risk</p>
                  <p className="text-xs font-bold text-[var(--text-secondary)] mt-0.5">{selectedDecision.pricing_in_risk}</p>
                </div>
                <div className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-2.5">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">Impact Category</p>
                  <p className="text-xs font-bold text-[var(--action-primary)] mt-0.5">{selectedDecision.impact_category}</p>
                </div>
                <div className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-2.5">
                  <p className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">Risk Score</p>
                  <p className="text-xs font-mono tabular-nums font-bold text-[var(--text-primary)] mt-0.5">
                    {formatRiskScore(selectedDecision.risk_score, 3)}
                  </p>
                </div>
              </div>

              {/* Reasoning */}
              <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-3.5 space-y-1.5">
                <h5 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
                  Analytical Decision Rationale
                </h5>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-sans">
                  {selectedDecision.decision_reason}
                </p>
              </div>

              {/* Stakeholder Summaries */}
              <div className="space-y-2 text-xs">
                {selectedDecision.investor_summary && (
                  <div className="p-3 rounded-md bg-[var(--bg-secondary)]/60 border border-[var(--border-subtle)]">
                    <span className="font-semibold text-[var(--color-positive)] block mb-1">Investor Perspective</span>
                    <p className="text-[var(--text-secondary)] leading-relaxed">{selectedDecision.investor_summary}</p>
                  </div>
                )}
                {selectedDecision.business_summary && (
                  <div className="p-3 rounded-md bg-[var(--bg-secondary)]/60 border border-[var(--border-subtle)]">
                    <span className="font-semibold text-[var(--action-primary)] block mb-1">Corporate &amp; Enterprise Impact</span>
                    <p className="text-[var(--text-secondary)] leading-relaxed">{selectedDecision.business_summary}</p>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[var(--border-subtle)]">
                <Link
                  href={`/predictions/${encodeURIComponent(selectedDecision.prediction_id || `${bill.bill_id}_${selectedDecision.company_isin}_${selectedDecision.event_window}`)}`}
                  className="text-xs text-[var(--action-primary)] hover:underline font-semibold inline-flex items-center gap-1"
                >
                  <span>Open Full Prediction Dossier →</span>
                </Link>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedDecision(null)}
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        )}

        {decisionError && (
          <p className="text-xs text-[var(--color-danger)] mt-2">{decisionError}</p>
        )}
      </Card>
    </div>
  );
}

export default CentralPredictionSection;
