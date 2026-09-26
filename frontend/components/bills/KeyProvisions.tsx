/**
 * components/bills/KeyProvisions.tsx
 * ===================================
 * Renders structured provisions, amended statutes, regulatory authority,
 * financial terms, and enforcement mechanisms.
 * Distinguishes statutory wording from analytical explanations.
 */

"use client";

import React from "react";
import type { BillKnowledge } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, Badge } from "@/components/ui/Badge";

export interface KeyProvisionsProps {
  provisions: string[];
  knowledge?: BillKnowledge | null;
  jurisdiction: string;
  state?: string | null;
  className?: string;
}

export function KeyProvisions({
  provisions,
  knowledge,
  jurisdiction,
  state,
  className = "",
}: KeyProvisionsProps) {
  const isState = jurisdiction?.toLowerCase() === "state";
  const amendedActs = knowledge?.amended_acts || [];
  const authority = knowledge?.regulatory_authority;
  const financialTerms = knowledge?.financial_terms;
  const penalties = knowledge?.penalties_or_enforcement;
  const objective = knowledge?.objective;

  const displayProvisions =
    provisions.length > 0
      ? provisions
      : knowledge?.key_provisions && knowledge.key_provisions.length > 0
      ? knowledge.key_provisions
      : [];

  return (
    <div className={`space-y-4 ${className}`}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div>
              <CardTitle>Key Statutory Provisions &amp; Legal Framework</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                {isState
                  ? `Extracted from ${state || "State"} legislative knowledge records and official assembly texts.`
                  : "Extracted from Central Parliamentary knowledge records and official gazette notifications."}
              </p>
            </div>
            <SourceBadge type="FACT" size="xs" showTooltip />
          </div>
        </CardHeader>

        <div className="space-y-5">
          {/* Statutory Objective / Statement of Objects and Reasons */}
          {objective && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Statutory Objective / Preamble
                </span>
                <Badge variant="primary" size="xs">
                  Statutory Statement
                </Badge>
              </div>
              <blockquote className="text-xs text-slate-300 border-l-2 border-blue-500/60 pl-3.5 py-1 italic leading-relaxed font-sans bg-slate-950/40 rounded-r">
                &ldquo;{objective}&rdquo;
              </blockquote>
            </div>
          )}

          {/* Core Provisions List */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center justify-between">
              <span>Identified Key Provisions</span>
              <span className="text-[11px] font-normal text-slate-500">
                {displayProvisions.length} recorded
              </span>
            </h4>

            {displayProvisions.length > 0 ? (
              <ul className="space-y-2.5" role="list">
                {displayProvisions.map((provision, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-3 rounded-lg border border-slate-800/80 bg-slate-900/40 p-3"
                  >
                    <span
                      className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-900/50 border border-blue-700/60 text-[10px] font-semibold text-blue-300 mt-0.5"
                      aria-hidden="true"
                    >
                      §{idx + 1}
                    </span>
                    <div className="flex-1 space-y-1">
                      <p className="text-xs font-mono text-slate-200 leading-relaxed">
                        {provision}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500 italic">
                Specific clause-level provisions are summarized in the Statement of Objects and Reasons above.
              </p>
            )}
          </div>

          {/* Legal Authority & Amended Acts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80">
            {/* Regulatory Authority */}
            <div className="rounded-lg border border-slate-800/80 bg-slate-900/50 p-3.5 space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-sm" aria-hidden="true">🏛</span>
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Regulatory / Administrative Authority
                </span>
              </div>
              <p className="text-xs font-medium text-slate-200">
                {authority || (isState ? `${state || "State"} Competent Administrative Department` : "Central Sponsoring Ministry")}
              </p>
            </div>

            {/* Amended Laws / Related Acts */}
            <div className="rounded-lg border border-slate-800/80 bg-slate-900/50 p-3.5 space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-sm" aria-hidden="true">⚖</span>
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Amended Statutes / Intersecting Acts
                </span>
              </div>
              {amendedActs.length > 0 ? (
                <div className="flex flex-wrap gap-1.5 pt-0.5">
                  {amendedActs.slice(0, 5).map((act, i) => (
                    <span
                      key={i}
                      className="text-[11px] font-mono bg-slate-800/80 border border-slate-700/60 text-slate-300 rounded px-2 py-0.5"
                    >
                      {act}
                    </span>
                  ))}
                  {amendedActs.length > 5 && (
                    <span className="text-[10px] text-slate-500 self-center">
                      +{amendedActs.length - 5} more
                    </span>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-400">Principal enactment (No statutory amendment)</p>
              )}
            </div>
          </div>

          {/* Financial & Penal Provisions (if documented) */}
          {(financialTerms || penalties) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {financialTerms && (
                <div className="rounded-lg border border-amber-900/40 bg-amber-950/20 p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-amber-400">
                    <span className="text-xs" aria-hidden="true">💰</span>
                    <span className="text-xs font-semibold uppercase tracking-wider">
                      Financial &amp; Tax Terms
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono">
                    {financialTerms}
                  </p>
                </div>
              )}

              {penalties && (
                <div className="rounded-lg border border-rose-900/40 bg-rose-950/20 p-3 space-y-1">
                  <div className="flex items-center gap-1.5 text-rose-400">
                    <span className="text-xs" aria-hidden="true">⚠️</span>
                    <span className="text-xs font-semibold uppercase tracking-wider">
                      Compliance Penalties &amp; Enforcement
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono">
                    {penalties}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

export default KeyProvisions;
