/**
 * components/bills/CorporateExposureTable.tsx
 * ============================================
 * Institutional Corporate Exposure Table for the Bill Detail Dossier.
 * Displays verified bill-company exposure records with interactive filtering,
 * statutory evidence drawers, and direct/indirect classifications.
 */

"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import type { BillCompanyExposure } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, ExposureBadge, Badge } from "@/components/ui/Badge";

export interface CorporateExposureTableProps {
  exposures: BillCompanyExposure[];
  className?: string;
}

export function CorporateExposureTable({
  exposures,
  className = "",
}: CorporateExposureTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [directFilter, setDirectFilter] = useState<"ALL" | "DIRECT" | "INDIRECT">("ALL");
  const [strengthFilter, setStrengthFilter] = useState<"ALL" | "HIGH" | "MEDIUM" | "LOW">("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return exposures.filter((exp) => {
      if (searchTerm.trim()) {
        const q = searchTerm.toLowerCase();
        const matchesName = exp.company_name?.toLowerCase().includes(q);
        const matchesActivity = exp.business_activity?.toLowerCase().includes(q);
        const matchesSector = exp.sector?.toLowerCase().includes(q);
        if (!matchesName && !matchesActivity && !matchesSector) return false;
      }

      if (directFilter !== "ALL") {
        if (exp.direct_indirect?.toUpperCase() !== directFilter) return false;
      }

      if (strengthFilter !== "ALL") {
        if (exp.exposure_strength?.toUpperCase() !== strengthFilter) return false;
      }

      return true;
    });
  }, [exposures, searchTerm, directFilter, strengthFilter]);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className={`space-y-4 ${className}`} aria-label="Corporate exposure section">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2 w-full">
            <div>
              <CardTitle>Documented Corporate Exposures</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Evidence-grounded corporate touchpoints and statutory transmission mechanisms.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="slate" size="xs">
                {exposures.length} Documented
              </Badge>
              <SourceBadge type="FACT" size="xs" showTooltip />
            </div>
          </div>
        </CardHeader>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg border border-slate-800 bg-slate-900/60 mb-4">
          {/* Search Box */}
          <div className="flex-1 min-w-[200px] max-w-sm">
            <input
              type="text"
              placeholder="Search by company or activity..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              aria-label="Search exposures"
            />
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Direct/Indirect */}
            <div className="flex items-center rounded border border-slate-700 overflow-hidden">
              {(["ALL", "DIRECT", "INDIRECT"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setDirectFilter(mode)}
                  className={`px-2.5 py-1 text-[11px] font-medium transition-colors ${
                    directFilter === mode
                      ? "bg-blue-600 text-white"
                      : "bg-slate-800/80 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {mode === "ALL" ? "All Types" : mode}
                </button>
              ))}
            </div>

            {/* Strength */}
            <div className="flex items-center rounded border border-slate-700 overflow-hidden">
              {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setStrengthFilter(lvl)}
                  className={`px-2 py-1 text-[11px] font-medium transition-colors ${
                    strengthFilter === lvl
                      ? "bg-slate-700 text-white font-semibold"
                      : "bg-slate-800/80 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {lvl === "ALL" ? "All Levels" : lvl}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Exposures Table */}
        {filtered.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs text-slate-300" aria-label="Corporate exposures table">
              <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th scope="col" className="py-3 px-3.5">Company &amp; Sector</th>
                  <th scope="col" className="py-3 px-3">Exposure Vector</th>
                  <th scope="col" className="py-3 px-3">Strength &amp; Mechanism</th>
                  <th scope="col" className="py-3 px-3">Jurisdiction / State</th>
                  <th scope="col" className="py-3 px-3 text-right">Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                {filtered.map((exp) => {
                  const isExpanded = expandedId === exp.company_id;
                  return (
                    <React.Fragment key={exp.company_id}>
                      <tr className="hover:bg-slate-900/50 transition-colors">
                        {/* Company Name & Sector */}
                        <td className="py-3 px-3.5 align-top">
                          <Link
                            href={`/companies/${encodeURIComponent(exp.company_id)}`}
                            className="font-semibold text-slate-100 hover:text-blue-400 transition-colors block text-xs"
                          >
                            {exp.company_name}
                          </Link>
                          <span className="text-[11px] text-slate-500 block mt-0.5">
                            {exp.sector || "Unclassified"} {exp.sub_sector ? `· ${exp.sub_sector}` : ""}
                          </span>
                        </td>

                        {/* Exposure Type & Direct/Indirect */}
                        <td className="py-3 px-3 align-top space-y-1">
                          <ExposureBadge
                            type={exp.exposure_type}
                            directIndirect={exp.direct_indirect}
                            size="xs"
                          />
                          {exp.business_activity && (
                            <p className="text-[11px] text-slate-400 line-clamp-1">
                              {exp.business_activity}
                            </p>
                          )}
                        </td>

                        {/* Strength & Mechanism */}
                        <td className="py-3 px-3 align-top max-w-xs">
                          <div className="flex items-center gap-1.5 mb-1">
                            <ExposureBadge strength={exp.exposure_strength} size="xs" />
                            <span className="text-[10px] text-slate-500 font-mono">
                              Relevance: {exp.market_relevance}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-300 line-clamp-2 leading-relaxed font-sans">
                            {exp.mechanism || "Direct statutory compliance impact"}
                          </p>
                        </td>

                        {/* Jurisdiction / State */}
                        <td className="py-3 px-3 align-top whitespace-nowrap">
                          {exp.state ? (
                            <span className="text-xs text-sky-400 font-medium">
                              🗺 {exp.state}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400">
                              🏛 National
                            </span>
                          )}
                        </td>

                        {/* Evidence Expander */}
                        <td className="py-3 px-3 align-top text-right whitespace-nowrap">
                          <button
                            type="button"
                            onClick={() => toggleExpand(exp.company_id)}
                            className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors inline-flex items-center gap-1"
                            aria-expanded={isExpanded}
                            aria-label={`Toggle evidence for ${exp.company_name}`}
                          >
                            <span>{exp.evidence && exp.evidence.length > 0 ? `${exp.evidence.length} claims` : "Details"}</span>
                            <span>{isExpanded ? "▲" : "▼"}</span>
                          </button>
                        </td>
                      </tr>

                      {/* Evidence Expanded Drawer */}
                      {isExpanded && (
                        <tr className="bg-slate-900/70 border-b border-slate-800">
                          <td colSpan={5} className="p-4 space-y-3">
                            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                              <h5 className="text-xs font-semibold text-slate-200">
                                Documented Statutory Evidence — {exp.company_name}
                              </h5>
                              <SourceBadge type="FACT" size="xs" />
                            </div>

                            {exp.evidence && exp.evidence.length > 0 ? (
                              <ul className="space-y-2 text-xs" role="list">
                                {exp.evidence.map((ev, i) => (
                                  <li
                                    key={i}
                                    className="rounded-md border border-slate-800 bg-slate-950/60 p-2.5 space-y-1"
                                  >
                                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                                      <span className="font-semibold text-slate-300">
                                        Claim #{i + 1}
                                      </span>
                                      {ev.statutory_section && (
                                        <span className="font-mono text-blue-300">
                                          § Section: {ev.statutory_section}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-slate-300 text-xs leading-relaxed font-sans">
                                      {ev.claim}
                                    </p>
                                    {ev.reference && (
                                      <p className="text-[10px] text-slate-500 font-mono">
                                        Source: {ev.reference}
                                      </p>
                                    )}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-xs text-slate-400 italic">
                                Documented legal exposure mapped from verified corporate filings and statutory jurisdiction.
                              </p>
                            )}

                            {exp.source_urls && exp.source_urls.length > 0 && (
                              <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
                                <span className="text-slate-500">Source References:</span>
                                {exp.source_urls.map((url, idx) => (
                                  <a
                                    key={idx}
                                    href={url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-400 hover:text-blue-300 underline truncate max-w-xs"
                                  >
                                    {url}
                                  </a>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          /* Empty State */
          <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-8 text-center space-y-2">
            <span className="text-2xl" aria-hidden="true">🏢</span>
            <h4 className="text-sm font-semibold text-slate-300">
              No Documented Corporate Exposures
            </h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              {searchTerm || directFilter !== "ALL" || strengthFilter !== "ALL"
                ? "No corporate records match your active search filters. Try resetting the filters."
                : "This legislative bill does not currently have documented direct corporate exposure vectors in the institutional repository."}
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}

export default CorporateExposureTable;
