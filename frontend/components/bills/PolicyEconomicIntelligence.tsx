/**
 * components/bills/PolicyEconomicIntelligence.tsx
 * ===============================================
 * Policy and Economic Intelligence section of the Bill Detail Dossier.
 * Displays sectors, stakeholders, economic mechanism classifications, and market relevance.
 * Guarantees: Qualitative domain classifications only; no synthetic financial returns.
 */

"use client";

import React from "react";
import type { BillSummaryItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, Badge } from "@/components/ui/Badge";
import { MarketRelevanceBadge } from "@/components/coverage/CapabilityBadge";

export interface PolicyEconomicIntelligenceProps {
  bill: BillSummaryItem;
  className?: string;
}

export function PolicyEconomicIntelligence({
  bill,
  className = "",
}: PolicyEconomicIntelligenceProps) {
  const isState = bill.jurisdiction?.toLowerCase() === "state";
  const geoScope = isState ? `${bill.state || "State"} Territory` : "National (All India)";

  return (
    <div className={`space-y-4 ${className}`}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div>
              <CardTitle>Policy &amp; Economic Impact Intelligence</CardTitle>
              <p className="text-xs text-[var(--text-faint)] mt-0.5">
                Qualitative economic vectors, sector classifications, and transmission mechanism taxonomy.
              </p>
            </div>
            <SourceBadge type="DERIVED" size="xs" showTooltip />
          </div>
        </CardHeader>

        <div className="space-y-5">
          {/* Classification Overview Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60 p-3">
              <p className="text-[10px] font-semibold text-[var(--text-faint)] uppercase tracking-wider mb-1">
                Policy Domain
              </p>
              <p className="text-xs font-semibold text-[var(--text-primary)]">
                {bill.policy_domain || "General Legal Framework"}
              </p>
            </div>

            <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60 p-3">
              <p className="text-[10px] font-semibold text-[var(--text-faint)] uppercase tracking-wider mb-1">
                Geographic Scope
              </p>
              <p className="text-xs font-semibold text-[var(--text-primary)]">
                {geoScope}
              </p>
            </div>

            <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60 p-3">
              <p className="text-[10px] font-semibold text-[var(--text-faint)] uppercase tracking-wider mb-1">
                Market Relevance
              </p>
              <div className="pt-0.5">
                <MarketRelevanceBadge relevance={bill.market_relevance} size="xs" />
              </div>
            </div>

            <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60 p-3">
              <p className="text-[10px] font-semibold text-[var(--text-faint)] uppercase tracking-wider mb-1">
                Data Sufficiency
              </p>
              <span
                className={`inline-block text-[11px] font-medium px-2 py-0.5 rounded border ${
                  bill.data_sufficiency === "COMPLETE"
                    ? "bg-emerald-950/60 text-emerald-300 border-emerald-800/40"
                    : "bg-[var(--bg-elevated)] text-[var(--text-muted)] border-[var(--border-strong)]"
                }`}
              >
                {bill.data_sufficiency}
              </span>
            </div>
          </div>

          {/* Economic Sectors */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                Impacted Economic Sectors
              </h4>
              <span className="text-[11px] text-[var(--text-faint)]">
                {bill.economic_sectors.length} sectors identified
              </span>
            </div>

            {bill.economic_sectors.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {bill.economic_sectors.map((sector, i) => (
                  <span
                    key={sector}
                    className={`text-xs px-2.5 py-1 rounded-md border font-medium ${
                      i === 0
                        ? "bg-blue-900/30 text-blue-200 border-blue-700/50"
                        : "bg-[var(--bg-elevated)]/70 text-[var(--text-secondary)] border-[var(--border-strong)]/60"
                    }`}
                  >
                    {i === 0 && <span className="text-blue-400 mr-1.5 font-bold">★</span>}
                    {sector}
                    {i === 0 && (
                      <span className="ml-1.5 text-[10px] text-blue-400 uppercase font-semibold">
                        Primary
                      </span>
                    )}
                  </span>
                ))}
                {bill.secondary_sectors &&
                  bill.secondary_sectors
                    .filter((s) => !bill.economic_sectors.includes(s))
                    .map((sec) => (
                      <span
                        key={sec}
                        className="text-xs px-2.5 py-1 rounded-md bg-[var(--bg-elevated)]/40 text-[var(--text-muted)] border border-[var(--border-strong)]/40"
                      >
                        {sec}
                      </span>
                    ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--text-faint)] italic">No specific economic sectors classified.</p>
            )}
          </div>

          {/* Affected Stakeholder Communities */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                Affected Stakeholders &amp; Constituents
              </h4>
              <span className="text-[11px] text-[var(--text-faint)]">
                {bill.stakeholders.length} constituent groups
              </span>
            </div>

            {bill.stakeholders.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {bill.stakeholders.map((sh) => (
                  <span
                    key={sh}
                    className="inline-flex items-center gap-1.5 text-xs bg-[var(--bg-elevated)] border border-[var(--border-strong)] rounded-md px-2.5 py-1 text-[var(--text-primary)]"
                  >
                    <span className="text-[var(--text-muted)] text-xs" aria-hidden="true">👥</span>
                    {sh}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--text-faint)] italic">No stakeholder categories documented.</p>
            )}
          </div>

          {/* Transmission Mechanism & Boundaries Note */}
          <div className="rounded-md border border-[var(--border-default)] bg-[var(--bg-card)]/40 p-3 text-[11px] text-[var(--text-muted)] leading-relaxed space-y-1">
            <p className="font-semibold text-[var(--text-secondary)]">Methodological Standard</p>
            <p>
              Economic and policy intelligence relies on deterministic text-extraction and ontological mapping.
              Categorization does not imply immediate capital market repricing or equity risk adjustments.
              Corporate exposure records in subsequent sections reflect documented legal and operational touchpoints.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default PolicyEconomicIntelligence;
