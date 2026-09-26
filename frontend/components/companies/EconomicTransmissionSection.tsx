/**
 * components/companies/EconomicTransmissionSection.tsx
 * =====================================================
 * Visual and structured explanation of how legislation transmits into corporate impact.
 *
 * Sequence:
 * Legislation → Policy / Provision → Business Activity → Company Presence →
 * Corporate Exposure → Economic Mechanism → Market Relevance
 *
 * Strict Compliance:
 * - Only displays mechanisms documented in actual company exposures.
 * - Does NOT invent causal links or speculative financial consequences.
 */

"use client";

import React from "react";
import type { CompanyDetailResponse, BillCompanyExposure } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, SourceBadge } from "@/components/ui/Badge";

export interface EconomicTransmissionSectionProps {
  company: CompanyDetailResponse;
  exposures: BillCompanyExposure[];
  className?: string;
}

interface MechanismSummary {
  name: string;
  count: number;
  bills: { id: string; title: string; strength: string; directness: string }[];
  description: string;
}

const MECHANISM_DESCRIPTIONS: Record<string, string> = {
  taxation: "Alters statutory tax rates, customs duties, excise regimes, or cess liabilities directly affecting corporate net revenues.",
  compliance_cost: "Imposes statutory reporting, recordkeeping, auditing, or operational procedural mandates incurring incremental compliance overhead.",
  licensing: "Requires regulatory permits, formal operating registrations, or statutory licensing authorizations to conduct commercial business.",
  regulation: "Imposes direct supervisory restrictions, standard operating limits, or administrative oversight on corporate products and services.",
  procurement: "Governs public tender mandates, local sourcing stipulations, or government vendor eligibility criteria.",
  land: "Impacts real estate, industrial zoning, leasing rights, or environmental acquisition guidelines.",
  infrastructure: "Mandates physical equipment specifications, grid connections, logistical corridors, or safety standards.",
  labour: "Dictates statutory working conditions, union recognition, severance obligations, or wage classifications.",
  supply_chain: "Affects input sourcing regulations, cross-border or interstate freight movement, and vendor compliance certification.",
  tariffs: "Imposes import/export duty structures altering domestic manufacturing competitiveness.",
  environmental_compliance: "Imposes statutory emissions limits, waste processing protocols, or environmental clearances.",
};

export function EconomicTransmissionSection({
  company,
  exposures,
  className = "",
}: EconomicTransmissionSectionProps) {
  // Aggregate documented mechanisms from actual exposures
  const mechanisms = React.useMemo<MechanismSummary[]>(() => {
    const map = new Map<string, MechanismSummary>();

    for (const exp of exposures) {
      if (!exp.mechanism) continue;
      const raw = exp.mechanism.trim();
      const normKey = raw.toLowerCase().replace(/\s+/g, "_");

      if (!map.has(normKey)) {
        map.set(normKey, {
          name: raw,
          count: 0,
          bills: [],
          description:
            MECHANISM_DESCRIPTIONS[normKey] ||
            "Governs statutory operational transmission channel connecting legislative provisions to corporate activities.",
        });
      }

      const item = map.get(normKey)!;
      item.count++;
      if (item.bills.length < 4) {
        item.bills.push({
          id: exp.bill_id,
          title: exp.bill_title,
          strength: exp.exposure_strength,
          directness: exp.direct_indirect,
        });
      }
    }

    return Array.from(map.values()).sort((a, b) => b.count - a.count);
  }, [exposures]);

  return (
    <div className={`space-y-6 ${className}`} aria-label="Economic Transmission Mechanisms">
      {/* ------------------------------------------------------------------ */}
      {/* 1. Visual Transmission Pipeline Flow                               */}
      {/* ------------------------------------------------------------------ */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <CardTitle>Economic Transmission Architecture</CardTitle>
              <SourceBadge type="DERIVED" size="xs" showTooltip />
            </div>
            <span className="text-xs text-slate-500 font-mono">Structural Framework</span>
          </div>
        </CardHeader>

        <p className="text-xs text-slate-400 mb-6 leading-relaxed">
          The framework illustrates the deterministic chain linking statutory enactment to corporate operational exposure.
          Only mechanisms supported by verified parliamentary evidence are classified.
        </p>

        {/* Transmission Chain Steps */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2 relative">
          {[
            { step: "01", title: "Legislation", desc: "Parliamentary or Assembly Bill enacted or tabled" },
            { step: "02", title: "Statutory Clause", desc: "Specific legal provision, rule, or penalty" },
            { step: "03", title: "Commercial Activity", desc: "Corporate business lines & active operations" },
            { step: "04", title: "Jurisdictional Presence", desc: "Headquarters or state facility footprints" },
            { step: "05", title: "Corporate Exposure", desc: "Direct legal exposure or supply-chain vector" },
            { step: "06", title: "Economic Mechanism", desc: "Tax, compliance, licensing, or regulatory channel" },
            { step: "07", title: "Market Relevance", desc: "Qualitative institutional market classification" },
          ].map((node, i) => (
            <div
              key={node.step}
              className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 flex flex-col justify-between relative group hover:border-slate-700 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono font-bold text-slate-500">
                    {node.step}
                  </span>
                  {i < 6 && (
                    <span className="hidden lg:inline text-slate-600 text-xs font-mono">→</span>
                  )}
                </div>
                <h4 className="text-xs font-semibold text-slate-200 mb-1">{node.title}</h4>
                <p className="text-[11px] text-slate-400 leading-snug">{node.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* ------------------------------------------------------------------ */}
      {/* 2. Active Documented Mechanisms for this Company                   */}
      {/* ------------------------------------------------------------------ */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <CardTitle>
                Documented Transmission Channels ({mechanisms.length})
              </CardTitle>
              <SourceBadge type="DERIVED" size="xs" />
            </div>
            <span className="text-xs text-slate-400">
              Evidence-backed transmission mechanisms
            </span>
          </div>
        </CardHeader>

        {mechanisms.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            No specific transmission mechanisms are recorded in current exposure evidence.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mechanisms.map((mech) => (
              <div
                key={mech.name}
                className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-base" aria-hidden="true">⚙</span>
                      <h4 className="text-sm font-semibold text-slate-100 capitalize">
                        {mech.name}
                      </h4>
                    </div>
                    <Badge variant="info" size="xs" className="border-cyan-800 text-cyan-400">
                      {mech.count} {mech.count === 1 ? "Bill" : "Bills"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                    {mech.description}
                  </p>
                </div>

                {/* Connected Bills */}
                <div className="pt-3 border-t border-slate-800/80 space-y-1.5">
                  <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                    Intersecting Legislation:
                  </span>
                  <div className="space-y-1">
                    {mech.bills.map((b) => (
                      <div
                        key={b.id}
                        className="flex items-center justify-between gap-2 text-[11px]"
                      >
                        <span className="text-slate-300 truncate max-w-[260px] font-medium">
                          {b.title}
                        </span>
                        <span className="text-slate-500 text-[10px] shrink-0">
                          {b.strength} · {b.directness}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default EconomicTransmissionSection;
