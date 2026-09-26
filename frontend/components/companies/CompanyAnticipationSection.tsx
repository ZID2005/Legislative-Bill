/**
 * components/companies/CompanyAnticipationSection.tsx
 * ====================================================
 * Pre-Event Anticipation & Information Diffusion analysis for corporate profiles.
 *
 * Strict Compliance:
 * 1. Neutral Institutional Wording: Evaluates public pre-event information diffusion.
 * 2. Explicit Disclaimer: Disclaims insider trading allegations.
 * 3. Intelligence Firewall: Renders non-applicable state for non-quantitative entities.
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import type { CompanyAnticipationResponse, CompanyAnticipationScoreItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, SourceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export interface CompanyAnticipationSectionProps {
  anticipation: CompanyAnticipationResponse | null;
  isQuant: boolean;
  className?: string;
}

export function CompanyAnticipationSection({
  anticipation,
  isQuant,
  className = "",
}: CompanyAnticipationSectionProps) {
  const [selectedScore, setSelectedScore] = useState<CompanyAnticipationScoreItem | null>(null);

  // 1. NON-QUANTITATIVE / INTELLIGENCE ENTITY CHECK
  if (!isQuant || anticipation?.reason === "INTELLIGENCE_ONLY_ENTITY") {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Pre-Event Information Diffusion Diagnostics</CardTitle>
            <SourceBadge type="DERIVED" size="xs" showTooltip />
          </div>
        </CardHeader>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 text-center space-y-2">
          <span className="text-2xl" aria-hidden="true">📡</span>
          <h4 className="text-sm font-semibold text-slate-300">
            Anticipation Diagnostics Not Applicable for this Entity
          </h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Pre-event econometric anticipation and information diffusion modeling operates strictly on liquid Central quantitative securities.
            Intelligence-only entities, unlisted companies, and public utilities are firewalled from econometric pre-event diagnostics.
          </p>
        </div>
      </Card>
    );
  }

  // 2. CHECK AVAILABILITY
  const scores = anticipation?.scores || [];
  const hasScores = anticipation?.available && scores.length > 0;

  if (!hasScores) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Pre-Event Information Diffusion Diagnostics</CardTitle>
            <SourceBadge type="DERIVED" size="xs" showTooltip />
          </div>
        </CardHeader>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 text-center space-y-2">
          <span className="text-xl" aria-hidden="true">📊</span>
          <h4 className="text-xs font-semibold text-slate-300">
            Anticipation Diagnostics Unavailable
          </h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            No pre-event information diffusion records are currently cataloged for this company.
          </p>
        </div>
      </Card>
    );
  }

  // Format classification badges
  const getClassificationBadge = (cls: string) => {
    switch (cls?.toUpperCase()) {
      case "STRONG_EVIDENCE":
        return <Badge variant="warning" size="xs">⚡ Strong Diffusion</Badge>;
      case "MODERATE_EVIDENCE":
        return <Badge variant="primary" size="xs">Moderate Diffusion</Badge>;
      case "WEAK_EVIDENCE":
        return <Badge variant="slate" size="xs">Weak Diffusion</Badge>;
      default:
        return <Badge variant="muted" size="xs">No Diffusion Evidence</Badge>;
    }
  };

  return (
    <div className={`space-y-6 ${className}`} aria-label="Anticipation Analysis Section">
      {/* Neutral Methodology & Non-Allegation Disclaimer */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/90 p-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-blue-400 font-semibold text-xs">
              Pre-Event Market Information Diffusion Analysis
            </span>
            <SourceBadge type="DERIVED" size="xs" />
          </div>
          <span className="text-[11px] text-slate-500">Methodology Benchmark</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Econometric pre-event diagnostic models evaluate whether parliamentary news, public consultations, or market volume anomalies were observed prior to official introduction date ($T_0$).
        </p>
        <div className="rounded bg-slate-800/60 p-2.5 border border-slate-700/60 text-[11px] text-amber-200/90 font-medium">
          🛡️ Institutional Disclaimer: Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law.
        </div>
      </div>

      {/* Anticipation Scores Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Company Anticipation Records ({scores.length})</CardTitle>
            <span className="text-xs text-slate-400">
              Evaluated against Central enactments
            </span>
          </div>
        </CardHeader>

        <div className="overflow-x-auto -mx-6">
          <table className="w-full text-left text-xs border-collapse min-w-[700px]">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/50 text-slate-400 font-semibold">
                <th scope="col" className="py-2.5 px-4 w-4/12">Central Legislation</th>
                <th scope="col" className="py-2.5 px-3 w-2/12">Introduction Date</th>
                <th scope="col" className="py-2.5 px-3 w-2/12">Diffusion Evidence</th>
                <th scope="col" className="py-2.5 px-3 w-2/12">Composite Score</th>
                <th scope="col" className="py-2.5 px-3 w-2/12 text-center">Diagnostic</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {scores.map((score) => {
                const billTitle =
                  score.bill_id
                    ?.replace(/-/g, " ")
                    ?.replace(/\b\w/g, (c) => c.toUpperCase()) || "Central Bill";

                return (
                  <tr
                    key={score.bill_id}
                    className="hover:bg-slate-800/40 transition-colors"
                  >
                    {/* Bill Title */}
                    <td className="py-3 px-4">
                      <Link
                        href={`/bills/${encodeURIComponent(score.bill_id)}`}
                        className="font-semibold text-slate-200 hover:text-blue-400 transition-colors block text-sm"
                      >
                        {billTitle}
                      </Link>
                      <span className="text-[10px] text-slate-500 font-mono block mt-0.5">
                        {score.company_symbol} · {score.confidence || "MODERATE"} Confidence
                      </span>
                    </td>

                    {/* T0 Date */}
                    <td className="py-3 px-3">
                      <span className="text-slate-300 font-mono text-xs">
                        {score.official_introduction_date || "Date not recorded"}
                      </span>
                    </td>

                    {/* Classification */}
                    <td className="py-3 px-3">
                      {getClassificationBadge(score.classification)}
                    </td>

                    {/* Score */}
                    <td className="py-3 px-3">
                      <div className="space-y-0.5">
                        <span className="font-mono font-bold text-slate-200 text-xs">
                          {typeof score.anticipation_score === "number"
                            ? score.anticipation_score.toFixed(3)
                            : "—"}
                        </span>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500">
                          <span>Mkt: {score.market_signal_score?.toFixed(2) ?? "—"}</span>
                          <span>Info: {score.information_signal_score?.toFixed(2) ?? "—"}</span>
                        </div>
                      </div>
                    </td>

                    {/* Diagnostic Trigger */}
                    <td className="py-3 px-3 text-center">
                      <Button
                        variant="outline"
                        size="xs"
                        onClick={() => setSelectedScore(score)}
                        className="text-xs border-slate-700 hover:border-slate-500"
                        aria-label={`View diagnostic detail for ${billTitle}`}
                      >
                        🔍 Diagnostic
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Anticipation Diagnostic Modal */}
      {selectedScore && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-fade-in"
          role="dialog"
          aria-modal="true"
          aria-labelledby="anticipation-modal-title"
        >
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 id="anticipation-modal-title" className="text-sm font-semibold text-slate-100">
                    Pre-Event Diffusion Diagnostic
                  </h3>
                  <SourceBadge type="DERIVED" size="xs" />
                </div>
                <p className="text-xs text-slate-400 mt-0.5 font-medium">
                  {selectedScore.bill_id}
                </p>
              </div>
              <button
                onClick={() => setSelectedScore(null)}
                className="text-slate-400 hover:text-white text-base p-1"
                aria-label="Close diagnostic modal"
              >
                ✕
              </button>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded bg-slate-800/60 p-2.5 border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Classification</span>
                <span className="font-bold text-slate-200">{selectedScore.classification}</span>
              </div>
              <div className="rounded bg-slate-800/60 p-2.5 border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Composite Score</span>
                <span className="font-bold text-blue-400">
                  {selectedScore.anticipation_score?.toFixed(3) ?? "—"}
                </span>
              </div>
              <div className="rounded bg-slate-800/60 p-2.5 border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Market Signal</span>
                <span className="font-bold text-slate-200">
                  {selectedScore.market_signal_score?.toFixed(3) ?? "—"}
                </span>
              </div>
              <div className="rounded bg-slate-800/60 p-2.5 border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Information Signal</span>
                <span className="font-bold text-slate-200">
                  {selectedScore.information_signal_score?.toFixed(3) ?? "—"}
                </span>
              </div>
            </div>

            {/* Diagnostic Reason */}
            {selectedScore.decision_reason && (
              <div className="space-y-1 text-xs">
                <span className="font-semibold text-slate-400 uppercase tracking-wider block">
                  Diagnostic Rationale
                </span>
                <p className="text-slate-300 bg-slate-800/40 p-3 rounded border border-slate-800 leading-relaxed">
                  {selectedScore.decision_reason}
                </p>
              </div>
            )}

            {/* Detected Signals */}
            {selectedScore.detected_signals && selectedScore.detected_signals.length > 0 && (
              <div className="space-y-1.5 text-xs pt-2 border-t border-slate-800">
                <span className="font-semibold text-slate-400 uppercase tracking-wider block">
                  Detected Pre-Event Signals
                </span>
                <ul className="space-y-1 text-slate-300">
                  {selectedScore.detected_signals.map((sig, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-blue-400" aria-hidden="true">•</span>
                      <span>{sig}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <Link
                href={`/bills/${encodeURIComponent(selectedScore.bill_id)}`}
                className="text-xs text-blue-400 hover:underline"
              >
                Inspect Bill Dossier ↗
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedScore(null)}
                className="text-xs"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CompanyAnticipationSection;
