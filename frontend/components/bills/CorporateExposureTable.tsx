/**
 * components/bills/CorporateExposureTable.tsx
 * ============================================
 * Institutional Corporate Exposure Table for the Bill Detail Dossier.
 * Displays verified bill-company exposure records with interactive filtering,
 * statutory evidence drawers, and direct/indirect classifications.
 * Dual-theme synchronized for Seance.
 */

"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import type { BillCompanyExposure } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, ExposureBadge, Badge } from "@/components/ui/Badge";
import { ChevronDownIcon, ChevronUpIcon, SearchIcon, CompaniesIcon } from "@/components/ui/Icons";

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
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Evidence-grounded corporate touchpoints and statutory transmission mechanisms.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="default" size="xs">
                {exposures.length} Documented
              </Badge>
              <SourceBadge type="FACT" size="xs" showTooltip />
            </div>
          </div>
        </CardHeader>

        {/* Epistemic Guidance Banner */}
        <div className="mb-4 rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)]/50 p-3 text-xs flex items-start gap-2.5">
          <span className="text-sm text-blue-500 flex-shrink-0 mt-0.5" aria-hidden="true">ℹ</span>
          <div className="leading-relaxed text-[var(--text-muted)] text-[11px]">
            <strong className="text-[var(--text-primary)]">Epistemic Distinction:</strong> Corporate exposures document verified statutory touchpoints, compliance obligations, and transmission channels. Quantitative econometric market predictions are separate statistical models available for listed securities under Central legislation only (State legislation operates under a strict zero-prediction statutory firewall).
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)] mb-4">
          {/* Search Box */}
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none" aria-hidden="true">
              <SearchIcon size="xs" />
            </span>
            <input
              type="text"
              placeholder="Search by company or activity..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg border border-[var(--input-border)] bg-[var(--input-bg)] pl-8 pr-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--focus-ring)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)] transition-all"
              aria-label="Search exposures"
            />
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Direct/Indirect */}
            <div className="flex items-center rounded-lg border border-[var(--border-default)] overflow-hidden bg-[var(--bg-card)]">
              {(["ALL", "DIRECT", "INDIRECT"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setDirectFilter(mode)}
                  className={`px-2.5 py-1 text-[11px] font-medium transition-colors ${
                    directFilter === mode
                      ? "bg-[var(--action-primary)] text-white shadow-xs font-semibold"
                      : "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                  }`}
                >
                  {mode === "ALL" ? "All Types" : mode}
                </button>
              ))}
            </div>

            {/* Strength */}
            <div className="flex items-center rounded-lg border border-[var(--border-default)] overflow-hidden bg-[var(--bg-card)]">
              {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setStrengthFilter(lvl)}
                  className={`px-2 py-1 text-[11px] font-medium transition-colors ${
                    strengthFilter === lvl
                      ? "bg-[var(--action-primary)] text-white font-semibold"
                      : "bg-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
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
          <div className="overflow-x-auto rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)]">
            <table className="w-full text-left text-xs" aria-label="Corporate exposures table">
              <thead className="bg-[var(--bg-base)] text-[var(--text-muted)] uppercase text-[10px] tracking-wider border-b border-[var(--border-default)]">
                <tr>
                  <th scope="col" className="py-3 px-3.5">Company &amp; Sector</th>
                  <th scope="col" className="py-3 px-3">Exposure Vector</th>
                  <th scope="col" className="py-3 px-3">Strength &amp; Mechanism</th>
                  <th scope="col" className="py-3 px-3">Jurisdiction / State</th>
                  <th scope="col" className="py-3 px-3 text-right">Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] bg-[var(--bg-surface)]">
                {filtered.map((exp) => {
                  const isExpanded = expandedId === exp.company_id;
                  return (
                    <React.Fragment key={exp.company_id}>
                      <tr className="hover:bg-[var(--table-row-hover)] transition-colors">
                        {/* Company Name & Sector */}
                        <td className="py-3 px-3.5 align-top">
                          <Link
                            href={`/companies/${encodeURIComponent(exp.company_id)}`}
                            className="font-semibold text-[var(--text-primary)] hover:text-[var(--action-primary)] transition-colors block text-xs"
                          >
                            {exp.company_name}
                          </Link>
                          <span className="text-[11px] text-[var(--text-muted)] block mt-0.5">
                            {exp.sector || "Unclassified"} {exp.sub_sector ? `· ${exp.sub_sector}` : ""}
                          </span>
                          <div className="flex items-center gap-2 mt-1">
                            {exp.jurisdiction?.toLowerCase() === "state" || exp.state ? (
                              <span
                                className="text-[10px] text-amber-600 dark:text-amber-400 font-mono font-medium inline-flex items-center gap-1"
                                title="State legislation is firewalled from stock market predictions under project invariants"
                              >
                                🛡️ State Isolation (0 Predictions)
                              </span>
                            ) : (
                              <Link
                                href={`/predictions?search=${encodeURIComponent(exp.company_name)}`}
                                className="text-[10px] text-[var(--action-primary)] hover:underline font-medium inline-flex items-center gap-0.5"
                                title={`Search predictions for ${exp.company_name}`}
                              >
                                Predictions ↗
                              </Link>
                            )}
                          </div>
                        </td>

                        {/* Exposure Type & Direct/Indirect */}
                        <td className="py-3 px-3 align-top space-y-1">
                          <ExposureBadge
                            type={exp.exposure_type}
                            directIndirect={exp.direct_indirect}
                            size="xs"
                          />
                          {exp.business_activity && (
                            <p className="text-[11px] text-[var(--text-muted)] line-clamp-1">
                              {exp.business_activity}
                            </p>
                          )}
                        </td>

                        {/* Strength & Mechanism */}
                        <td className="py-3 px-3 align-top max-w-xs">
                          <div className="flex items-center gap-1.5 mb-1">
                            <ExposureBadge strength={exp.exposure_strength} size="xs" />
                            <span className="text-[10px] text-[var(--text-muted)] font-mono">
                              Relevance: {exp.market_relevance}
                            </span>
                          </div>
                          <p className="text-[11px] text-[var(--text-secondary)] line-clamp-2 leading-relaxed font-sans">
                            {exp.mechanism || "Direct statutory compliance impact"}
                          </p>
                        </td>

                        {/* Jurisdiction / State */}
                        <td className="py-3 px-3 align-top whitespace-nowrap">
                          {exp.state ? (
                            <span className="text-xs text-[var(--color-info)] font-medium inline-flex items-center gap-1">
                              <span>🗺</span>
                              <span>{exp.state}</span>
                            </span>
                          ) : (
                            <span className="text-xs text-[var(--text-muted)] inline-flex items-center gap-1">
                              <span>🏛</span>
                              <span>National</span>
                            </span>
                          )}
                        </td>

                        {/* Evidence Expander */}
                        <td className="py-3 px-3 align-top text-right whitespace-nowrap">
                          <button
                            type="button"
                            onClick={() => toggleExpand(exp.company_id)}
                            className="text-xs text-[var(--action-primary)] hover:underline font-medium transition-colors inline-flex items-center gap-1"
                            aria-expanded={isExpanded}
                            aria-label={`Toggle evidence for ${exp.company_name}`}
                          >
                            <span>{exp.evidence && exp.evidence.length > 0 ? `${exp.evidence.length} claims` : "Details"}</span>
                            {isExpanded ? <ChevronUpIcon size="xs" /> : <ChevronDownIcon size="xs" />}
                          </button>
                        </td>
                      </tr>

                      {/* Evidence Expanded Drawer */}
                      {isExpanded && (
                        <tr className="bg-[var(--bg-secondary)]/60 border-b border-[var(--border-default)]">
                          <td colSpan={5} className="p-4 space-y-3">
                            <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-2">
                              <h5 className="text-xs font-semibold text-[var(--text-primary)]">
                                Documented Statutory Evidence — {exp.company_name}
                              </h5>
                              <SourceBadge type="FACT" size="xs" />
                            </div>

                            {exp.evidence && exp.evidence.length > 0 ? (
                              <ul className="space-y-2 text-xs" role="list">
                                {exp.evidence.map((ev, i) => (
                                  <li
                                    key={i}
                                    className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] p-3 space-y-1 shadow-xs"
                                  >
                                    <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)]">
                                      <span className="font-semibold text-[var(--text-primary)]">
                                        Claim #{i + 1}
                                      </span>
                                      {ev.statutory_section && (
                                        <span className="font-mono text-[var(--action-primary)] font-medium">
                                          § Section: {ev.statutory_section}
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-[var(--text-secondary)] text-xs leading-relaxed font-sans">
                                      {ev.claim}
                                    </p>
                                    {ev.reference && (
                                      <p className="text-[10px] text-[var(--text-muted)] font-mono">
                                        Source: {ev.reference}
                                      </p>
                                    )}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-xs text-[var(--text-muted)] italic">
                                Documented legal exposure mapped from verified corporate filings and statutory jurisdiction.
                              </p>
                            )}

                            {exp.source_urls && exp.source_urls.length > 0 && (
                              <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
                                <span className="text-[var(--text-muted)]">Source References:</span>
                                {exp.source_urls.map((url, idx) => (
                                  <a
                                    key={idx}
                                    href={url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[var(--action-primary)] hover:underline truncate max-w-xs"
                                  >
                                    {url}
                                  </a>
                                ))}
                              </div>
                            )}

                            {/* Workflow Cross-Links */}
                            <div className="flex flex-wrap items-center gap-4 pt-3 border-t border-[var(--border-default)] text-xs">
                              <Link
                                href={`/companies/${encodeURIComponent(exp.company_id)}`}
                                className="inline-flex items-center gap-1 font-semibold text-[var(--action-primary)] hover:underline"
                              >
                                <span>🏢 View Company Profile →</span>
                              </Link>
                              {exp.jurisdiction?.toLowerCase() === "state" || exp.state ? (
                                <span className="inline-flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400 font-mono font-medium">
                                  <span>🛡️ State Legislation (Zero Stock Predictions Guaranteed)</span>
                                </span>
                              ) : (
                                <Link
                                  href={`/predictions?search=${encodeURIComponent(exp.company_name)}`}
                                  className="inline-flex items-center gap-1 font-semibold text-[var(--action-primary)] hover:underline"
                                >
                                  <span>📈 Check Market Predictions →</span>
                                </Link>
                              )}
                              <Link
                                href="/portfolio"
                                className="inline-flex items-center gap-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:underline"
                                title="Evaluate exposure of this measure across your tracked holdings in Portfolio Exposure"
                              >
                                <span>💼 Check Portfolio Exposure →</span>
                              </Link>
                            </div>
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
          <div className="rounded-xl border border-dashed border-[var(--border-default)] bg-[var(--bg-secondary)]/30 p-8 text-center space-y-2">
            <div className="text-[var(--text-muted)] inline-flex items-center justify-center mb-1" aria-hidden="true">
              <CompaniesIcon size="lg" />
            </div>
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">
              No Documented Corporate Exposures
            </h4>
            <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto leading-relaxed">
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
