/**
 * components/firewalls/IntelligenceCompanyFirewall.tsx
 * =====================================================
 * Renders when a non-quantitative (intelligence-only) company's
 * predictions are requested.
 *
 * CRITICAL: Must NEVER show prediction widgets for intelligence entities.
 * Shows: company profile, legislative exposure, economic mechanisms,
 * relevant states, and documented evidence.
 */

import React from "react";
import { cn } from "@/lib/utils";
import type { CompanyDetailResponse, CompanyPredictionStatusResponse } from "@/types/api";

export interface IntelligenceCompanyFirewallProps {
  company?: CompanyDetailResponse | null;
  predictionStatus?: CompanyPredictionStatusResponse | null;
  className?: string;
}

export function IntelligenceCompanyFirewall({
  company,
  predictionStatus,
  className,
}: IntelligenceCompanyFirewallProps) {
  const entityName = company?.company_name ?? "This entity";
  const entityType = company?.entity_type ?? "intelligence entity";
  const universeType = company?.universe_type ?? "intelligence";

  return (
    <section
      className={cn(
        "rounded-lg border border-slate-700 bg-slate-900 p-6",
        className
      )}
      aria-label="Prediction availability status"
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-5">
        <div
          className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-amber-900/40 border border-amber-700/40"
          aria-hidden="true"
        >
          <span className="text-base">🏢</span>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Market prediction unavailable for this entity
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {entityName} — {entityType} · {universeType}
          </p>
        </div>
      </div>

      {/* Explanation */}
      <p className="text-sm text-slate-400 mb-5 leading-relaxed">
        This entity is classified as a <span className="text-slate-300 font-medium">qualitative intelligence entity</span>,
        not a quantitative prediction-eligible listed security.
        It may be an unlisted company, a state entity, a cooperative, or an entity
        without sufficient market data for the backtested quantitative model.
        The quantitative firewall is permanently active for this entity.
      </p>

      {/* Available intelligence */}
      <div className="rounded-md border border-slate-800 bg-slate-800/40 p-4 mb-4">
        <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Available intelligence for this entity
        </p>
        <ul className="space-y-2" role="list">
          {[
            {
              icon: "📋",
              label: "Company / Entity Profile",
              desc: "Business description, activities, sector classification, and HQ location",
              available: !!company,
            },
            {
              icon: "🔗",
              label: "Documented Legislative Exposure",
              desc: `${company?.total_exposures ?? 0} evidence-backed exposure records across Central and State bills`,
              available: (company?.total_exposures ?? 0) > 0,
            },
            {
              icon: "⚙️",
              label: "Economic Mechanisms",
              desc: "Identified economic transmission channels linking legislation to this entity",
              available: (company?.mechanisms?.length ?? 0) > 0,
            },
            {
              icon: "🗺",
              label: "Relevant States",
              desc: `Operating in: ${company?.operating_states?.slice(0, 4).join(", ") ?? "—"}`,
              available: (company?.operating_states?.length ?? 0) > 0,
            },
            {
              icon: "📎",
              label: "Evidence & Sources",
              desc: "Official source documents, statutory sections, and citation references",
              available: true,
            },
          ].map(({ icon, label, desc, available }) => (
            <li key={label} className={cn("flex items-start gap-2", !available && "opacity-40")}>
              <span className="text-sm mt-0.5 flex-shrink-0" aria-hidden="true">
                {icon}
              </span>
              <div>
                <span className="text-xs font-medium text-slate-300">{label}</span>
                <p className="text-xs text-slate-500">{desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Explicitly not available */}
      <div className="rounded-md border border-slate-800 bg-slate-800/20 p-3">
        <p className="text-xs font-medium text-slate-500 mb-1.5">
          Quantitative prediction unavailable (firewall active)
        </p>
        <ul className="space-y-1 text-xs text-slate-600">
          {[
            "Stock return prediction",
            "Market direction (Bullish/Bearish)",
            "Decision support records",
            "Anticipation bias scores",
            "Stakeholder reports",
          ].map((item) => (
            <li key={item} className="flex items-center gap-1.5">
              <span aria-hidden="true">✕</span>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {predictionStatus?.message && (
        <p className="mt-3 text-xs text-slate-600 italic">
          System note: {predictionStatus.message}
        </p>
      )}
    </section>
  );
}

export default IntelligenceCompanyFirewall;
