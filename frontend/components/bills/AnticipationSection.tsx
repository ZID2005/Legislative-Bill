/**
 * components/bills/AnticipationSection.tsx
 * ========================================
 * Pre-Event Anticipation & Information Diffusion section.
 * Displays econometric pre-event signals, diffusion metrics, and neutral diagnostics.
 *
 * Strict Compliance:
 * - Neutral terminology only.
 * - Explicitly disclaims insider trading allegations.
 * - Invariant: State legislation strictly indicates non-applicability.
 */

"use client";

import React from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, Badge } from "@/components/ui/Badge";

export interface AnticipationSectionProps {
  anticipationData: Record<string, unknown> | null;
  isState: boolean;
  className?: string;
}

export function AnticipationSection({
  anticipationData,
  isState,
  className = "",
}: AnticipationSectionProps) {
  // 1. STATE BILL FIREWALL
  if (isState) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Pre-Event Anticipation Diagnostics</CardTitle>
            <SourceBadge type="DERIVED" size="xs" showTooltip />
          </div>
        </CardHeader>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 text-center space-y-2">
          <span className="text-2xl" aria-hidden="true">📡</span>
          <h4 className="text-sm font-semibold text-slate-300">
            Anticipation Analysis Not Applicable to State Legislation
          </h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Pre-event econometric anticipation and information diffusion modeling operates strictly on Central Parliamentary enactments.
            State assembly proceedings are not subjected to pre-event market leakage diagnostics.
          </p>
        </div>
      </Card>
    );
  }

  // 2. CHECK CENTRAL AVAILABILITY
  const isAvailable = Boolean(anticipationData?.available);
  const billRecord = (anticipationData?.bill_record || {}) as Record<string, any>;
  const scores = ((anticipationData?.scores as any[]) || billRecord.company_scores || []) as any[];

  if (!isAvailable || (!billRecord.overall_anticipation_score && scores.length === 0)) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Pre-Event Anticipation Diagnostics</CardTitle>
            <SourceBadge type="DERIVED" size="xs" showTooltip />
          </div>
        </CardHeader>
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 text-center space-y-2">
          <span className="text-xl" aria-hidden="true">📊</span>
          <h4 className="text-xs font-semibold text-slate-300">
            Anticipation Diagnostics Not Available
          </h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Pre-event information diffusion modeling is not recorded for this legislative measure.
          </p>
        </div>
      </Card>
    );
  }

  const overallScore = typeof billRecord.overall_anticipation_score === "number"
    ? billRecord.overall_anticipation_score.toFixed(3)
    : "—";
  const classification = billRecord.overall_classification || "RECORDED";
  const flag = Boolean(billRecord.overall_anticipation_flag);
  const confidence = billRecord.overall_confidence || "MODERATE";
  const totalAnalyzed = billRecord.total_companies_analyzed || scores.length;

  return (
    <div className={`space-y-4 ${className}`} aria-label="Anticipation diagnostics section">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2 w-full">
            <div>
              <CardTitle>Pre-Event Legislative Anticipation &amp; Diffusion Analysis</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Econometric diagnostics evaluating whether legislative signals were reflected in market volumes prior to formal introduction.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="amber" size="xs">
                {classification}
              </Badge>
              <SourceBadge type="DERIVED" size="xs" showTooltip />
            </div>
          </div>
        </CardHeader>

        {/* Mandatory Neutral Institutional Framing Notice */}
        <div className="rounded-md border border-amber-900/40 bg-amber-950/20 p-3.5 text-xs text-amber-200 leading-relaxed space-y-1 mb-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold" aria-hidden="true">⚖</span>
            <span className="font-semibold text-amber-100">Methodology &amp; Terminology Disclosure</span>
          </div>
          <p className="text-amber-300/90 text-xs font-sans">
            Pre-event information evidence suggests that some legislative or policy information may have been diffused or anticipated by market participants before the formal legislative tabling.
            These diagnostics reflect quantitative statistical volume/volatility patterns; they do <strong>not</strong> prove or allege non-public information leakage or insider trading.
          </p>
        </div>

        {/* Aggregate Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
              Anticipation Score
            </p>
            <p className="text-base font-mono font-bold text-amber-400">
              {overallScore}
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
              Diagnostic Tier
            </p>
            <p className="text-xs font-bold text-slate-200 mt-1">
              {classification}
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
              Pre-Event Signal
            </p>
            <span
              className={`inline-block text-xs font-semibold px-2 py-0.5 rounded mt-0.5 ${
                flag
                  ? "bg-amber-950 text-amber-300 border border-amber-800"
                  : "bg-slate-800 text-slate-400 border border-slate-700"
              }`}
            >
              {flag ? "Flagged (Diffusion Detected)" : "Unflagged (Normal)"}
            </span>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
              Confidence &amp; Universe
            </p>
            <p className="text-xs font-medium text-slate-300 mt-1">
              {confidence} · {totalAnalyzed} Companies
            </p>
          </div>
        </div>

        {/* Company Pre-Event Breakdown Table */}
        {scores.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5">
              Company Diagnostic Breakdown (Top Samples)
            </h4>
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs text-slate-300" aria-label="Company anticipation breakdown">
                <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th scope="col" className="py-2.5 px-3">Company</th>
                    <th scope="col" className="py-2.5 px-3">Anticipation Score</th>
                    <th scope="col" className="py-2.5 px-3">Classification</th>
                    <th scope="col" className="py-2.5 px-3">Pre-Event Flag</th>
                    <th scope="col" className="py-2.5 px-3">Diagnostic Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono text-[11px]">
                  {scores.slice(0, 8).map((sc: any, idx: number) => {
                    const scVal = typeof sc.anticipation_score === "number"
                      ? sc.anticipation_score.toFixed(3)
                      : "—";
                    const scFlag = Boolean(sc.anticipation_flag);

                    return (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        <td className="py-2.5 px-3 font-sans">
                          <span className="font-semibold text-slate-200 block">
                            {sc.company_symbol || sc.company_name || sc.company_isin}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {sc.company_isin}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-bold text-amber-400">
                          {scVal}
                        </td>
                        <td className="py-2.5 px-3 font-sans">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                            {sc.classification || "RECORDED"}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-sans">
                          <span
                            className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                              scFlag
                                ? "bg-amber-950/80 text-amber-300"
                                : "text-slate-500"
                            }`}
                          >
                            {scFlag ? "Flagged" : "Normal"}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-sans text-slate-400 text-[11px] max-w-sm truncate leading-snug">
                          {sc.decision_reason || "Pre-event market diagnostics evaluated."}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

export default AnticipationSection;
