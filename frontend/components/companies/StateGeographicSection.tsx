/**
 * components/companies/StateGeographicSection.tsx
 * ===============================================
 * Visualizes geographic operational presence and State-level legislative exposures.
 *
 * Displays:
 * - State presence map/list (HQ, facilities, operating states)
 * - State bill exposures grouped by State jurisdiction
 * - Clear invariant disclaimer:
 *   "State legislative exposure" is strictly distinguished from "State stock prediction".
 *   State stock predictions remain strictly 0 under project invariants.
 */

"use client";

import React from "react";
import Link from "next/link";
import type { CompanyDetailResponse, BillCompanyExposure } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, ExposureBadge, SourceBadge } from "@/components/ui/Badge";

export interface StateGeographicSectionProps {
  company: CompanyDetailResponse;
  exposures: BillCompanyExposure[];
  className?: string;
}

export function StateGeographicSection({
  company,
  exposures,
  className = "",
}: StateGeographicSectionProps) {
  // Filter for State-level exposures only
  const stateExposures = React.useMemo(() => {
    return exposures.filter(
      (exp) => exp.jurisdiction?.toLowerCase() === "state" || Boolean(exp.state)
    );
  }, [exposures]);

  // Group exposures by State
  const exposuresByState = React.useMemo(() => {
    const map = new Map<string, BillCompanyExposure[]>();
    for (const exp of stateExposures) {
      const st = exp.state || "State Assembly";
      if (!map.has(st)) {
        map.set(st, []);
      }
      map.get(st)!.push(exp);
    }
    return map;
  }, [stateExposures]);

  return (
    <div className={`space-y-6 ${className}`} aria-label="Geographic and State Exposure">
      {/* ------------------------------------------------------------------ */}
      {/* 1. Mandatory Invariant Banner: State Exposure vs Prediction        */}
      {/* ------------------------------------------------------------------ */}
      <div className="rounded-lg border border-amber-800/40 bg-amber-950/20 p-4 text-xs space-y-1.5 text-amber-200">
        <div className="flex items-center gap-2">
          <span className="text-base" aria-hidden="true">🛡️</span>
          <h4 className="font-semibold text-amber-300">
            Statutory Isolation: State Legislative Exposure vs Equity Predictions
          </h4>
        </div>
        <p className="text-slate-400 leading-relaxed">
          State assembly exposures identify legitimate regional legal and regulatory vectors based on operational presence in that State.
          Under project architecture invariants, <strong className="text-slate-200">State stock predictions remain strictly 0</strong>.
          State measures are purely qualitative intelligence assets and do not generate market forecasts.
        </p>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* 2. Operational Footprint & Facilities Presence                     */}
      {/* ------------------------------------------------------------------ */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <CardTitle>Geographic Operational Footprint</CardTitle>
              <SourceBadge type="FACT" size="xs" />
            </div>
            <span className="text-xs text-slate-500">
              HQ: {[company.hq_city, company.hq_state].filter(Boolean).join(", ") || "India"}
            </span>
          </div>
        </CardHeader>

        {/* Operating States Pills */}
        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Operating States ({company.operating_states.length})
            </p>
            {company.operating_states.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {company.operating_states.map((st) => (
                  <Link
                    key={st}
                    href={`/states/${encodeURIComponent(st)}`}
                    className="text-xs bg-slate-800 border border-slate-700/80 rounded-md px-2.5 py-1 text-slate-300 hover:text-white hover:border-slate-500 transition-colors inline-flex items-center gap-1.5"
                  >
                    <span>🗺</span>
                    <span>{st}</span>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">
                National operational footprint registered.
              </p>
            )}
          </div>

          {/* Operational Facilities if recorded */}
          {company.facilities && company.facilities.length > 0 && (
            <div className="pt-3 border-t border-slate-800">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Verified Facilities ({company.facilities.length})
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {company.facilities.map((fac, idx) => (
                  <div
                    key={idx}
                    className="rounded bg-slate-800/50 border border-slate-700/40 p-2.5 text-xs"
                  >
                    <span className="font-semibold text-slate-200 block">
                      {String(fac.name || fac.facility_name || `Facility #${idx + 1}`)}
                    </span>
                    <span className="text-slate-400 text-[11px] block mt-0.5">
                      {String(fac.state || fac.city || "Verified Facility")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* ------------------------------------------------------------------ */}
      {/* 3. Documented State Assembly Legislative Exposures                  */}
      {/* ------------------------------------------------------------------ */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <CardTitle>State Assembly Exposures ({stateExposures.length})</CardTitle>
              <SourceBadge type="DERIVED" size="xs" />
            </div>
            <span className="text-xs text-slate-500">
              {exposuresByState.size} {exposuresByState.size === 1 ? "State" : "States"} impacted
            </span>
          </div>
        </CardHeader>

        {stateExposures.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            No State-level assembly exposures currently recorded for this corporate entity.
          </div>
        ) : (
          <div className="space-y-6">
            {Array.from(exposuresByState.entries()).map(([stateName, bills]) => (
              <div
                key={stateName}
                className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-3"
              >
                {/* State Section Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-base" aria-hidden="true">🗺</span>
                    <h4 className="text-sm font-bold text-slate-100">{stateName}</h4>
                    <Badge variant="warning" size="xs" className="border-amber-800/60 text-amber-400">
                      {bills.length} {bills.length === 1 ? "Bill Exposure" : "Bill Exposures"}
                    </Badge>
                  </div>
                  <Link
                    href={`/states/${encodeURIComponent(stateName)}`}
                    className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                  >
                    View State Dossier ↗
                  </Link>
                </div>

                {/* State Bills Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {bills.map((exp) => (
                    <div
                      key={exp.bill_id}
                      className="rounded-lg border border-slate-800 bg-slate-800/40 p-3.5 space-y-2 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <Link
                            href={`/bills/${encodeURIComponent(exp.bill_id)}`}
                            className="text-xs font-semibold text-slate-200 hover:text-blue-400 transition-colors line-clamp-2"
                          >
                            {exp.bill_title}
                          </Link>
                          <ExposureBadge
                            type={exp.exposure_type}
                            strength={exp.exposure_strength}
                            directIndirect={exp.direct_indirect}
                            size="xs"
                          />
                        </div>

                        <p className="text-[11px] text-slate-400 mt-1.5">
                          <span className="text-slate-500">Mechanism:</span> {exp.mechanism}
                        </p>
                      </div>

                      {/* Evidence citation snippet */}
                      {exp.evidence && exp.evidence.length > 0 && (
                        <div className="pt-2 border-t border-slate-700/40 text-[11px] text-slate-400">
                          <span className="font-medium text-slate-300 block truncate">
                            Claim: "{exp.evidence[0].claim}"
                          </span>
                          {exp.evidence[0].reference && (
                            <span className="text-[10px] text-slate-500 block">
                              Ref: {exp.evidence[0].reference}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default StateGeographicSection;
