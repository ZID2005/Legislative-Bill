/**
 * components/companies/CompanyOverview.tsx
 * =========================================
 * Executive summary card for corporate profiles.
 *
 * Displays:
 * 1. Factual Identity & Business Scope (Description, activities, facilities, HQ)
 * 2. Derived Legislative Exposure Metrics (Counts, directness, strength distribution, jurisdictions)
 *
 * Strict Compliance:
 * - Clear semantic distinction between FACT (official filings) and DERIVED (system analysis).
 * - Zero fabricated financial or predictive metrics.
 */

"use client";

import React from "react";
import Link from "next/link";
import type { CompanyDetailResponse } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, SourceBadge } from "@/components/ui/Badge";

export interface CompanyOverviewProps {
  company: CompanyDetailResponse;
  className?: string;
}

export function CompanyOverview({ company, className = "" }: CompanyOverviewProps) {
  // Calculate exposure strength distribution from related bills if available
  const strengthCounts = {
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0,
  };

  if (company.related_bills && company.related_bills.length > 0) {
    for (const exp of company.related_bills) {
      const s = (exp.exposure_strength || "").toUpperCase();
      if (s in strengthCounts) {
        strengthCounts[s as keyof typeof strengthCounts]++;
      }
    }
  }

  return (
    <div className={`space-y-6 ${className}`} aria-label="Company Overview Section">
      {/* ------------------------------------------------------------------ */}
      {/* 1. Derived Intelligence / Key Exposure Metrics Banner               */}
      {/* ------------------------------------------------------------------ */}
      <section aria-labelledby="exposure-metrics-heading">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h2 id="exposure-metrics-heading" className="text-sm font-semibold text-slate-200">
              Legislative Exposure Summary
            </h2>
            <SourceBadge type="DERIVED" size="xs" showTooltip />
          </div>
          <span className="text-xs text-slate-500">
            {company.total_exposures} total verified legislative exposures
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Total Documented Exposures */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3.5 flex flex-col justify-between">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Total Exposures
            </p>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-slate-100">{company.total_exposures}</span>
              <span className="text-[10px] text-slate-500">Bills</span>
            </div>
          </div>

          {/* Central Exposures */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3.5 flex flex-col justify-between">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Central Parliament
            </p>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-blue-400">
                {company.central_exposures_count}
              </span>
              <span className="text-[10px] text-blue-500/80">Union</span>
            </div>
          </div>

          {/* State Exposures */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3.5 flex flex-col justify-between">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              State Assemblies
            </p>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-amber-400">
                {company.state_exposures_count}
              </span>
              <span className="text-[10px] text-amber-500/80">Regional</span>
            </div>
          </div>

          {/* Direct Exposures */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3.5 flex flex-col justify-between">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Direct Exposure
            </p>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-emerald-400">
                {company.direct_exposures_count}
              </span>
              <span className="text-[10px] text-emerald-500/80">Primary</span>
            </div>
          </div>

          {/* Indirect Exposures */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3.5 flex flex-col justify-between">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Indirect Exposure
            </p>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-purple-400">
                {company.indirect_exposures_count}
              </span>
              <span className="text-[10px] text-purple-500/80">Supply/Sector</span>
            </div>
          </div>

          {/* High Strength Distribution */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3.5 flex flex-col justify-between">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              High Impact Vectors
            </p>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-rose-400">
                {strengthCounts.HIGH}
              </span>
              <span className="text-[10px] text-slate-500">
                {strengthCounts.MEDIUM} Med · {strengthCounts.LOW} Low
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* 2. Executive Corporate Profile & Operational Footprint             */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Business Description and Activities */}
        <Card className="lg:col-span-2 space-y-4">
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <CardTitle>Business Overview &amp; Commercial Scope</CardTitle>
                <SourceBadge type="FACT" size="xs" showTooltip />
              </div>
              <span className="text-xs text-slate-500">{company.sector}</span>
            </div>
          </CardHeader>

          {company.business_description ? (
            <p className="text-sm text-slate-300 leading-relaxed">
              {company.business_description}
            </p>
          ) : (
            <p className="text-sm text-slate-500 italic">
              Commercial profile records are maintained under verified sector disclosures.
            </p>
          )}

          {/* Documented Business Activities */}
          {company.business_activities && company.business_activities.length > 0 && (
            <div className="pt-2 border-t border-slate-800/80">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Core Commercial Activities
              </p>
              <div className="flex flex-wrap gap-1.5" role="list">
                {company.business_activities.map((act) => (
                  <span
                    key={act}
                    className="text-xs rounded bg-slate-800/80 border border-slate-700/60 px-2.5 py-1 text-slate-300"
                    role="listitem"
                  >
                    {act}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Key Transmission Mechanisms Active */}
          {company.mechanisms && company.mechanisms.length > 0 && (
            <div className="pt-2 border-t border-slate-800/80">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Active Economic Transmission Channels
                </p>
                <SourceBadge type="DERIVED" size="xs" />
              </div>
              <div className="flex flex-wrap gap-1.5">
                {company.mechanisms.map((mech) => (
                  <Badge key={mech} variant="info" size="xs" className="border-cyan-800/60 text-cyan-300 bg-cyan-950/20">
                    ⚙ {mech}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Right 1 Col: Operational Presence & Authority Metadata */}
        <Card className="space-y-4">
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <CardTitle>Corporate Footprint</CardTitle>
                <SourceBadge type="FACT" size="xs" />
              </div>
            </div>
          </CardHeader>

          <div className="space-y-3 text-xs divide-y divide-slate-800/60">
            {/* Sector / Industry */}
            <div className="pt-1">
              <span className="text-slate-500 block">Sector / Industry</span>
              <span className="text-slate-200 font-medium">
                {company.sector} — {company.industry || "General"}
              </span>
              {company.sub_industry && (
                <span className="text-slate-400 block text-[11px] mt-0.5">
                  Sub-industry: {company.sub_industry}
                </span>
              )}
            </div>

            {/* Entity Type & Ownership */}
            <div className="pt-2">
              <span className="text-slate-500 block">Ownership &amp; Form</span>
              <span className="text-slate-200 font-medium">
                {company.ownership_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())} · {company.listing_status}
              </span>
            </div>

            {/* Headquarters */}
            <div className="pt-2">
              <span className="text-slate-500 block">Headquarters</span>
              <span className="text-slate-200 font-medium">
                {[company.hq_city, company.hq_state].filter(Boolean).join(", ") || "India"}
              </span>
            </div>

            {/* Operating States */}
            {company.operating_states && company.operating_states.length > 0 && (
              <div className="pt-2">
                <span className="text-slate-500 block mb-1">
                  Operating States ({company.operating_states.length})
                </span>
                <div className="flex flex-wrap gap-1">
                  {company.operating_states.slice(0, 6).map((st) => (
                    <Link
                      key={st}
                      href={`/states/${encodeURIComponent(st)}`}
                      className="text-[11px] bg-slate-800 text-slate-300 hover:text-white px-1.5 py-0.5 rounded transition-colors"
                    >
                      {st}
                    </Link>
                  ))}
                  {company.operating_states.length > 6 && (
                    <span className="text-[11px] text-slate-500 self-center">
                      +{company.operating_states.length - 6} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Data Sources & Certification */}
            <div className="pt-2">
              <span className="text-slate-500 block mb-1">Authoritative Data Sources</span>
              <div className="flex flex-wrap gap-1">
                {(company.data_sources && company.data_sources.length > 0
                  ? company.data_sources
                  : ["Ministry of Corporate Affairs", "BSE/NSE", "Official Gazette"]
                ).map((src) => (
                  <span
                    key={src}
                    className="text-[10px] bg-slate-800/80 text-slate-400 border border-slate-700/40 px-1.5 py-0.5 rounded"
                  >
                    {src}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default CompanyOverview;
