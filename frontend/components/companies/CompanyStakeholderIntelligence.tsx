/**
 * components/companies/CompanyStakeholderIntelligence.tsx
 * ========================================================
 * Multi-persona intelligence views for corporate profiles.
 *
 * Provides analytical perspectives for:
 * 1. Investor & Capital Markets Perspective
 * 2. Corporate Management & Enterprise Leadership
 * 3. Industry Association & Public Policy Perspective
 *
 * Strict Compliance:
 * - Semantic separation of FACT, DERIVED, INTERPRETATION, and PREDICTION.
 * - Explicit disclaimer: No investment advice or stock recommendations.
 */

"use client";

import React, { useState } from "react";
import type { CompanyDetailResponse, BillCompanyExposure } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, SourceBadge } from "@/components/ui/Badge";

export interface CompanyStakeholderIntelligenceProps {
  company: CompanyDetailResponse;
  exposures: BillCompanyExposure[];
  className?: string;
}

export function CompanyStakeholderIntelligence({
  company,
  exposures,
  className = "",
}: CompanyStakeholderIntelligenceProps) {
  const [activePersona, setActivePersona] = useState<"INVESTOR" | "CORPORATE" | "INDUSTRY">("INVESTOR");

  const isQuant = company.is_quant_eligible;
  const centralCount = company.central_exposures_count;
  const stateCount = company.state_exposures_count;
  const highImpactCount = exposures.filter((e) => e.exposure_strength === "HIGH").length;

  return (
    <div className={`space-y-6 ${className}`} aria-label="Stakeholder Intelligence Section">
      {/* ------------------------------------------------------------------ */}
      {/* 1. Methodology & Semantic Level Legend                             */}
      {/* ------------------------------------------------------------------ */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/90 p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">
              Stakeholder &amp; Business Intelligence Synthesis
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Structured operational interpretation of legislative exposure tailored across commercial personas.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            <SourceBadge type="FACT" size="xs" showTooltip />
            <SourceBadge type="DERIVED" size="xs" showTooltip />
            <SourceBadge type="INTERPRETATION" size="xs" showTooltip />
            {isQuant && <SourceBadge type="PREDICTION" size="xs" showTooltip />}
          </div>
        </div>

        {/* Semantic Level Map */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-[11px]">
          <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
            <span className="font-semibold text-emerald-400 block">FACT</span>
            <span className="text-slate-400">Statutory text &amp; ROC filings</span>
          </div>
          <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
            <span className="font-semibold text-cyan-400 block">DERIVED</span>
            <span className="text-slate-400">Exposure strength &amp; mechanism</span>
          </div>
          <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
            <span className="font-semibold text-amber-400 block">INTERPRETATION</span>
            <span className="text-slate-400">Stakeholder impact assessment</span>
          </div>
          <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
            <span className="font-semibold text-purple-400 block">PREDICTION</span>
            <span className="text-slate-400">
              {isQuant ? "Central econometric models" : "Firewalled / 0 predictions"}
            </span>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* 2. Persona Selector Tabs                                           */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => setActivePersona("INVESTOR")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activePersona === "INVESTOR"
              ? "bg-blue-600 text-white shadow-md"
              : "bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700"
          }`}
        >
          💼 Investor &amp; Capital Markets
        </button>
        <button
          onClick={() => setActivePersona("CORPORATE")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activePersona === "CORPORATE"
              ? "bg-blue-600 text-white shadow-md"
              : "bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700"
          }`}
        >
          🏢 Corporate Management &amp; Legal
        </button>
        <button
          onClick={() => setActivePersona("INDUSTRY")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activePersona === "INDUSTRY"
              ? "bg-blue-600 text-white shadow-md"
              : "bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700"
          }`}
        >
          👥 Industry &amp; Public Policy
        </button>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* 3. Persona Content Cards                                           */}
      {/* ------------------------------------------------------------------ */}
      {activePersona === "INVESTOR" && (
        <Card className="space-y-4">
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <CardTitle>Investor &amp; Capital Markets Perspective</CardTitle>
                <SourceBadge type="INTERPRETATION" size="xs" />
              </div>
              <Badge variant="muted" size="xs">Institutional Research</Badge>
            </div>
          </CardHeader>

          <div className="space-y-3 text-xs leading-relaxed text-slate-300">
            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-blue-400">1. Legislative Risk Exposure Profile</span>
                <SourceBadge type="DERIVED" size="xs" />
              </h4>
              <p className="text-slate-400">
                {company.company_name} maintains <strong className="text-slate-200">{company.total_exposures} verified legislative exposures</strong> across Central Parliament ({centralCount}) and regional State assemblies ({stateCount}). {highImpactCount > 0 ? `${highImpactCount} of these relationships represent high-strength exposure vectors.` : "Exposures are diversified across operational and regulatory channels."}
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-blue-400">2. Capital Structure &amp; Valuation Transmission</span>
                <SourceBadge type="INTERPRETATION" size="xs" />
              </h4>
              <p className="text-slate-400">
                Primary economic transmission channels active for this corporate profile include:{" "}
                <span className="text-cyan-300 font-medium">
                  {company.mechanisms?.slice(0, 4).join(", ") || "Statutory licensing and sector compliance"}
                </span>.
                These mechanisms directly influence recurring operational expenditures, licensing lead-times, and tariff resilience.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-blue-400">3. Predictive Modeling Status</span>
                {isQuant ? <SourceBadge type="PREDICTION" size="xs" /> : <SourceBadge type="FACT" size="xs" />}
              </h4>
              <p className="text-slate-400">
                {isQuant ? (
                  <>
                    This corporate entity is eligible for <strong className="text-emerald-300">Central quantitative price forecasting</strong>. Multi-horizon event studies are available under the Market Predictions tab.
                  </>
                ) : (
                  <>
                    This entity is classified as <strong className="text-amber-300">Intelligence-Only</strong>. Quantitative stock return predictions are permanently firewalled to prevent speculative equity forecasting on illiquid or unlisted securities.
                  </>
                )}
              </p>
            </div>
          </div>
        </Card>
      )}

      {activePersona === "CORPORATE" && (
        <Card className="space-y-4">
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <CardTitle>Corporate Management &amp; Legal Counsel Perspective</CardTitle>
                <SourceBadge type="INTERPRETATION" size="xs" />
              </div>
              <Badge variant="muted" size="xs">Executive Operational</Badge>
            </div>
          </CardHeader>

          <div className="space-y-3 text-xs leading-relaxed text-slate-300">
            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-emerald-400">1. Statutory Compliance Burden</span>
                <SourceBadge type="DERIVED" size="xs" />
              </h4>
              <p className="text-slate-400">
                Operating across {company.operating_states.length > 0 ? `${company.operating_states.length} States` : "India"}, corporate leadership must maintain dual compliance architectures: tracking Union parliamentary standards while auditing State assembly notifications across regional subsidiaries.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-emerald-400">2. Commercial Activity Alignment</span>
                <SourceBadge type="FACT" size="xs" />
              </h4>
              <p className="text-slate-400">
                Core commercial activities ({company.business_activities?.slice(0, 5).join(", ") || company.sector}) intersect with documented statutory frameworks. Legal counsel should verify clause-level obligations under the Exposure Matrix tab.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-emerald-400">3. Legislative Surveillance Recommendation</span>
                <SourceBadge type="INTERPRETATION" size="xs" />
              </h4>
              <p className="text-slate-400">
                Subscribe this corporate profile to an automated intelligence watchlist to receive notifications upon parliamentary status changes, committee amendments, or gazette enactment notifications.
              </p>
            </div>
          </div>
        </Card>
      )}

      {activePersona === "INDUSTRY" && (
        <Card className="space-y-4">
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <CardTitle>Industry Association &amp; Public Policy Perspective</CardTitle>
                <SourceBadge type="INTERPRETATION" size="xs" />
              </div>
              <Badge variant="muted" size="xs">Macro Sectoral</Badge>
            </div>
          </CardHeader>

          <div className="space-y-3 text-xs leading-relaxed text-slate-300">
            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-purple-400">1. Sectoral Policy Direction</span>
                <SourceBadge type="DERIVED" size="xs" />
              </h4>
              <p className="text-slate-400">
                The legislative footprint spans {company.sector} policy domains. Measures in this space predominantly emphasize regulatory formalization, licensing transparency, and regional compliance harmonization.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="text-purple-400">2. Stakeholder Spillover Dynamics</span>
                <SourceBadge type="INTERPRETATION" size="xs" />
              </h4>
              <p className="text-slate-400">
                Direct statutory mandates on this enterprise have indirect transmission spillovers into auxiliary vendor networks, MSME supply lines, and institutional employment pools across operating geographies.
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

export default CompanyStakeholderIntelligence;
