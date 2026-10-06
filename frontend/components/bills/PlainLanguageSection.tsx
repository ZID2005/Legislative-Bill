/**
 * components/bills/PlainLanguageSection.tsx
 * ==========================================
 * Task 8.27 Phase 5 — Plain-Language Non-Expert Explanation.
 *
 * Grounded in authoritative statutory records.
 * Structured into 5 standard questions:
 * 1. WHAT IS THIS BILL?
 * 2. WHAT DOES IT CHANGE?
 * 3. WHO COULD BE AFFECTED?
 * 4. WHY COULD IT MATTER ECONOMICALLY? (Mechanisms without stock predictions)
 * 5. WHAT IS STILL UNKNOWN? (Explicitly identifying missing information)
 */

"use client";

import React from "react";
import type { PlainLanguageExplanation } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export interface PlainLanguageSectionProps {
  plainLanguage: PlainLanguageExplanation;
  className?: string;
}

export function PlainLanguageSection({
  plainLanguage,
  className = "",
}: PlainLanguageSectionProps) {
  if (!plainLanguage) return null;

  const {
    what_is_this_bill,
    what_does_it_change,
    who_could_be_affected,
    why_could_it_matter_economically,
    what_is_still_unknown,
    grounded_sources = [],
    epistemic_level = "INTERPRETATION",
    epistemic_notice,
  } = plainLanguage;

  return (
    <Card className={className} id="plain-language-section">
      <CardHeader>
        <div className="flex items-center justify-between w-full flex-wrap gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>Plain-Language Legislative Brief</CardTitle>
              <Badge variant="blue" size="xs">
                {epistemic_level}
              </Badge>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Clear, non-technical explanation grounded strictly in the underlying legislative record.
            </p>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            NON-TECHNICAL BRIEFING
          </span>
        </div>
      </CardHeader>

      <div className="p-4 sm:p-5 space-y-5">
        {/* Notice on Epistemic Level */}
        <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs text-slate-400 leading-relaxed">
          <strong className="text-slate-200 uppercase tracking-wider text-[10px] block mb-0.5">
            Epistemic Distinction: Interpretation
          </strong>
          {epistemic_notice ||
            "INTERPRETATION: Derived explanation based on documented facts. Never presents interpretations or projections as authoritative legislative text."}
        </div>

        {/* 5 Standard Sections Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 1. What is this bill? */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 space-y-2">
            <div className="flex items-center gap-2 text-slate-200 font-semibold text-xs uppercase tracking-wider">
              <span>📖</span>
              <h4>What is this bill?</h4>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {what_is_this_bill || "Official legislative summary unavailable in source repository."}
            </p>
          </div>

          {/* 2. What does it change? */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 space-y-2">
            <div className="flex items-center gap-2 text-slate-200 font-semibold text-xs uppercase tracking-wider">
              <span>⚡</span>
              <h4>What does it change?</h4>
            </div>
            <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
              {what_does_it_change || "Statutory modifications pending detailed procedural notification."}
            </div>
          </div>

          {/* 3. Who could be affected? */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 space-y-2">
            <div className="flex items-center gap-2 text-slate-200 font-semibold text-xs uppercase tracking-wider">
              <span>👥</span>
              <h4>Who could be affected?</h4>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {who_could_be_affected || "Stakeholder mapping documented in relevant sector directories."}
            </p>
          </div>

          {/* 4. Why could it matter economically? */}
          <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 space-y-2">
            <div className="flex items-center gap-2 text-slate-200 font-semibold text-xs uppercase tracking-wider">
              <span>📈</span>
              <h4>Why could it matter economically?</h4>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {why_could_it_matter_economically || "Economic mechanisms outlined without quantitative market predictions."}
            </p>
          </div>
        </div>

        {/* 5. What is still unknown? Full-width highlight box */}
        <div className="p-4 rounded-xl border border-amber-900/40 bg-amber-950/15 space-y-2">
          <div className="flex items-center gap-2 text-amber-300 font-semibold text-xs uppercase tracking-wider">
            <span>❓</span>
            <h4>What is still unknown?</h4>
          </div>
          <p className="text-xs text-amber-200/90 leading-relaxed">
            {what_is_still_unknown || "Future readings, committee reports, or gazette enforcement notifications pending."}
          </p>
        </div>

        {/* Grounded Sources Footer */}
        {grounded_sources && grounded_sources.length > 0 && (
          <div className="pt-2 border-t border-slate-800/60 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
            <span className="text-slate-400 font-medium">Grounded Sources:</span>
            {grounded_sources.map((src, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-slate-300 font-mono text-[10px] truncate max-w-xs"
                title={src}
              >
                {src}
              </span>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
