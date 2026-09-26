/**
 * components/industries/IndustryExecutiveOverview.tsx
 * ====================================================
 * 4-Zone Epistemic Overview: [FACT], [DERIVED], [INTERPRETATION], [PREDICTION].
 */

import React from "react";
import { SourceBadge } from "@/components/ui/Badge";
import type { IndustryDossierResponse } from "@/types/api";

export interface IndustryExecutiveOverviewProps {
  dossier: IndustryDossierResponse;
}

export function IndustryExecutiveOverview({ dossier }: IndustryExecutiveOverviewProps) {
  return (
    <section aria-labelledby="executive-overview-heading" className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 id="executive-overview-heading" className="text-lg font-semibold text-white">
          Executive Industry Overview
        </h2>
        <span className="text-xs text-slate-400">
          Epistemic Categorization · Verified Methodology
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Zone 1: FACTS */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-2 mb-3">
            <SourceBadge type="FACT" size="sm" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Verified Legal & Entity Facts
            </h3>
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            {dossier.facts.map((fact, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-emerald-400 mt-0.5">•</span>
                <span>{fact}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Zone 2: DERIVED */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-2 mb-3">
            <SourceBadge type="DERIVED" size="sm" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Derived Aggregations & Transmissions
            </h3>
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            {dossier.derived.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-blue-400 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Zone 3: INTERPRETATION */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-2 mb-3">
            <SourceBadge type="INTERPRETATION" size="sm" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Economic & Regulatory Interpretation
            </h3>
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            {dossier.interpretations.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Zone 4: PREDICTION */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center gap-2 mb-3">
            <SourceBadge type="PREDICTION" size="sm" />
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Econometric Model Projections
            </h3>
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            {dossier.predictions.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-purple-400 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

export default IndustryExecutiveOverview;
