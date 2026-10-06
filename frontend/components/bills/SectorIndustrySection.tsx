/**
 * components/bills/SectorIndustrySection.tsx
 * ===========================================
 * Task 8.27 Phase 7 — Sector & Industry Exposure.
 *
 * Integrates:
 * - Macro Sector Directory
 * - Canonical Industry Classifications
 * - Regulated Business Activities
 * - Categorical Exposure Tiers (DIRECT, INDIRECT, POTENTIAL, UNKNOWN)
 *
 * Invariant: Does not infer exposure solely from company name similarity.
 */

"use client";

import React from "react";
import type { SectorExposureItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export interface SectorIndustrySectionProps {
  sectorExposures?: SectorExposureItem[];
  sectors?: SectorExposureItem[];
  className?: string;
}

export function SectorIndustrySection({
  sectorExposures,
  sectors,
  className = "",
}: SectorIndustrySectionProps) {
  const activeSectors = sectors || sectorExposures || [];

  if (activeSectors.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Sector & Industry Footprint</CardTitle>
        </CardHeader>
        <p className="text-xs text-slate-400 p-4">
          No economic sector exposures mapped for this legislative measure.
        </p>
      </Card>
    );
  }

  const getExposureBadgeVariant = (type: string) => {
    switch (type) {
      case "DIRECT":
        return "blue";
      case "INDIRECT":
        return "amber";
      case "POTENTIAL":
        return "slate";
      default:
        return "slate";
    }
  };

  return (
    <Card className={className} id="sector-industry-section">
      <CardHeader>
        <div className="flex items-center justify-between w-full flex-wrap gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>Sector & Industry Footprint</CardTitle>
              <Badge variant="blue" size="xs">
                MACRO SECTOR DIRECTORY
              </Badge>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Verified mapping of affected economic sectors, industries, and regulated business activities.
            </p>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
            <span>EVIDENCE-GROUNDED LINKAGE</span>
          </div>
        </div>
      </CardHeader>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Exposure Classification Key */}
        <div className="flex flex-wrap items-center gap-3 p-2.5 rounded-lg border border-slate-800 bg-slate-900/40 text-[11px] text-slate-400">
          <span className="font-semibold text-slate-300">Exposure Classification:</span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-blue-400" />
            <strong className="text-slate-200">DIRECT</strong> — Primary statutory mandate
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            <strong className="text-slate-200">INDIRECT</strong> — Supply chain / downstream
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-slate-400" />
            <strong className="text-slate-200">POTENTIAL</strong> — Thematic overlap
          </span>
        </div>

        {/* Sectors Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {activeSectors.map((item, idx) => {
            const variant = getExposureBadgeVariant(item.exposure_type);

            return (
              <div
                key={idx}
                className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/30 hover:bg-slate-900/50 transition-colors space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">
                      Macro Sector
                    </span>
                    <h4 className="text-sm font-semibold text-slate-100 mt-0.5">
                      {item.sector}
                    </h4>
                  </div>
                  <Badge variant={variant} size="xs">
                    {item.exposure_type} EXPOSURE
                  </Badge>
                </div>

                {/* Industries */}
                {item.industries && item.industries.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[11px] font-medium text-slate-400 block">
                      Affected Industries:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {item.industries.map((ind, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700/60 text-slate-300 text-[11px]"
                        >
                          {ind}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Regulated Business Activities */}
                {item.business_activities && item.business_activities.length > 0 && (
                  <div className="space-y-1 pt-2 border-t border-slate-800/60">
                    <span className="text-[11px] font-medium text-slate-400 block">
                      Potentially Regulated Activities:
                    </span>
                    <ul className="text-xs text-slate-300 space-y-0.5">
                      {item.business_activities.map((act, aIdx) => (
                        <li key={aIdx} className="flex items-center gap-1.5 text-[11px]">
                          <span className="text-blue-400">•</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Transmission Channel */}
                {item.transmission_channel && (
                  <p className="text-[11px] text-slate-400 italic pt-1 border-t border-slate-800/40">
                    Channel: {item.transmission_channel}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
