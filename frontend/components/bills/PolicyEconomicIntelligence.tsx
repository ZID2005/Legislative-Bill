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
              <p className="text-xs text-slate-500 mt-0.5">
                Qualitative economic vectors, sector classifications, and transmission mechanism taxonomy.
              </p>
            </div>
            <SourceBadge type="DERIVED" size="xs" showTooltip />
          </div>
        </CardHeader>

        <div className="space-y-5">
          {/* Classification Overview Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                Policy Domain
              </p>
              <p className="text-xs font-semibold text-slate-200">
                {bill.policy_domain || "General Legal Framework"}
              </p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                Geographic Scope
              </p>
              <p className="text-xs font-semibold text-slate-200">
                {geoScope}
              </p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                Market Relevance
              </p>
              <div className="pt-0.5">
                <MarketRelevanceBadge relevance={bill.market_relevance} size="xs" />
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                Data Sufficiency
              </p>
              <span
                className={`inline-block text-[11px] font-medium px-2 py-0.5 rounded border ${
                  bill.data_sufficiency === "COMPLETE"
                    ? "bg-emerald-950/60 text-emerald-300 border-emerald-800/40"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}
              >
                {bill.data_sufficiency}
              </span>
            </div>
          </div>

          {/* Economic Sectors */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Impacted Economic Sectors
              </h4>
              <span className="text-[11px] text-slate-500">
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
                        : "bg-slate-800/70 text-slate-300 border-slate-700/60"
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
                        className="text-xs px-2.5 py-1 rounded-md bg-slate-800/40 text-slate-400 border border-slate-700/40"
                      >
                        {sec}
                      </span>
                    ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No specific economic sectors classified.</p>
            )}
          </div>

          {/* Affected Stakeholder Communities */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Affected Stakeholders &amp; Constituents
              </h4>
              <span className="text-[11px] text-slate-500">
                {bill.stakeholders.length} constituent groups
              </span>
            </div>

            {bill.stakeholders.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {bill.stakeholders.map((sh) => (
                  <span
                    key={sh}
                    className="inline-flex items-center gap-1.5 text-xs bg-slate-800 border border-slate-700 rounded-md px-2.5 py-1 text-slate-200"
                  >
                    <span className="text-slate-400 text-xs" aria-hidden="true">👥</span>
                    {sh}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No stakeholder categories documented.</p>
            )}
          </div>

          {/* Transmission Mechanism & Boundaries Note */}
          <div className="rounded-md border border-slate-800 bg-slate-900/40 p-3 text-[11px] text-slate-400 leading-relaxed space-y-1">
            <p className="font-semibold text-slate-300">Methodological Standard</p>
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
