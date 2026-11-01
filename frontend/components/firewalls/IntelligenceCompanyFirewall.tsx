/**
 * components/firewalls/IntelligenceCompanyFirewall.tsx
 * =====================================================
 * Renders when a non-quantitative (intelligence-only) company's
 * predictions are requested.
 *
 * CRITICAL STATUTORY FIREWALL: Must NEVER show prediction widgets for intelligence entities.
 * Shows: company profile, legislative exposure, economic mechanisms,
 * relevant states, and documented evidence.
 * Dual-theme synchronized for Seance.
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
        "rounded-2xl border border-[var(--border-default)] bg-[var(--bg-card)] p-6 shadow-xs transition-colors",
        className
      )}
      role="region"
      aria-label="Prediction availability status"
    >
      {/* Header */}
      <div className="flex items-start gap-3.5 mb-5">
        <div
          className="mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-[var(--color-warning)]/12 border border-[var(--color-warning)]/30 text-[var(--color-warning)]"
          aria-hidden="true"
        >
          <span className="text-base">🏢</span>
        </div>
        <div>
          <h3 className="text-sm font-bold text-[var(--text-primary)] tracking-tight">
            Market prediction unavailable for this entity
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            {entityName} — {entityType} · {universeType}
          </p>
        </div>
      </div>

      {/* Explanation */}
      <p className="text-sm text-[var(--text-secondary)] mb-5 leading-relaxed">
        This entity is classified as a <span className="text-[var(--text-primary)] font-semibold">qualitative intelligence entity</span>,
        not a quantitative prediction-eligible listed security.
        It may be an unlisted company, a state entity, a cooperative, or an entity
        without sufficient market data for the backtested quantitative model.
        The quantitative firewall is permanently active for this entity.
      </p>

      {/* Available intelligence */}
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)]/50 p-4 mb-4">
        <p className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider mb-3">
          Available intelligence for this entity
        </p>
        <ul className="space-y-2.5" role="list">
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
            <li key={label} className={cn("flex items-start gap-2.5", !available && "opacity-40")}>
              <span className="text-sm mt-0.5 flex-shrink-0" aria-hidden="true">
                {icon}
              </span>
              <div>
                <span className="text-xs font-semibold text-[var(--text-primary)]">{label}</span>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">{desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Explicitly not available */}
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)]/40 p-4">
        <p className="text-xs font-semibold text-[var(--text-muted)] mb-2">
          Quantitative prediction unavailable (firewall active)
        </p>
        <ul className="space-y-1.5 text-xs text-[var(--text-muted)]">
          {[
            "Stock return prediction",
            "Market direction (Bullish/Bearish)",
            "Decision support records",
            "Anticipation bias scores",
            "Stakeholder reports",
          ].map((item) => (
            <li key={item} className="flex items-center gap-2">
              <span aria-hidden="true" className="font-bold">✕</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {predictionStatus?.message && (
        <p className="mt-3.5 text-xs text-[var(--text-muted)] italic">
          System note: {predictionStatus.message}
        </p>
      )}
    </section>
  );
}

export default IntelligenceCompanyFirewall;
