/**
 * components/industries/IndustryCorporateExposure.tsx
 * ===================================================
 * Corporate exposure network for an industry, grouping quantitative and intelligence-only entities.
 */

import React, { useState } from "react";
import Link from "next/link";
import { Badge, ExposureBadge } from "@/components/ui/Badge";
import type { IndustryCompanyItem } from "@/types/api";

export interface IndustryCorporateExposureProps {
  quantitativeCompanies: IndustryCompanyItem[];
  intelligenceCompanies: IndustryCompanyItem[];
  referenceCompanies: IndustryCompanyItem[];
}

export function IndustryCorporateExposure({
  quantitativeCompanies,
  intelligenceCompanies,
  referenceCompanies,
}: IndustryCorporateExposureProps) {
  const [filter, setFilter] = useState<"ALL" | "QUANT" | "INTEL">("ALL");

  const totalCount = quantitativeCompanies.length + intelligenceCompanies.length + referenceCompanies.length;
  const displayedCompanies =
    filter === "QUANT"
      ? quantitativeCompanies
      : filter === "INTEL"
      ? [...intelligenceCompanies, ...referenceCompanies]
      : [...quantitativeCompanies, ...intelligenceCompanies, ...referenceCompanies];

  return (
    <section aria-labelledby="corporate-exposure-heading" className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 id="corporate-exposure-heading" className="text-lg font-semibold text-[var(--text-primary)]">
            Corporate Exposure Network
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Member corporations and state utilities subject to industry statutory mechanisms
          </p>
        </div>

        {/* Filter Strip */}
        <div className="inline-flex rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] p-1 text-xs">
          <button
            type="button"
            onClick={() => setFilter("ALL")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              filter === "ALL" ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            All Entities ({totalCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter("QUANT")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              filter === "QUANT"
                ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/40"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Quantitative Securities ({quantitativeCompanies.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter("INTEL")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              filter === "INTEL"
                ? "bg-blue-950/60 text-blue-300 border border-blue-800/40"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Corporate Intelligence ({intelligenceCompanies.length + referenceCompanies.length})
          </button>
        </div>
      </div>

      {/* Table / List */}
      <div className="overflow-x-auto rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60">
        <table className="w-full text-left text-xs text-[var(--text-secondary)]">
          <thead className="bg-[var(--bg-elevated)]/80 text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider border-b border-[var(--border-default)]">
            <tr>
              <th scope="col" className="px-4 py-3">Company / Entity</th>
              <th scope="col" className="px-4 py-3">Universe Status</th>
              <th scope="col" className="px-4 py-3">Exposure Profile</th>
              <th scope="col" className="px-4 py-3">Mechanism</th>
              <th scope="col" className="px-4 py-3">Market Relevance</th>
              <th scope="col" className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-default)]/60">
            {displayedCompanies.map((c) => {
              const isQuant = c.is_quant_eligible;
              return (
                <tr key={c.company_id} className="hover:bg-[var(--bg-elevated)]/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-[var(--text-primary)]">
                      <Link
                        href={`/companies/${encodeURIComponent(c.company_id)}`}
                        className="hover:text-blue-400 transition-colors"
                      >
                        {c.company_name}
                      </Link>
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5 text-[11px] text-[var(--text-muted)]">
                      <span>{c.company_id}</span>
                      {c.ticker_nse && (
                        <>
                          <span>·</span>
                          <span className="text-[var(--text-secondary)] font-mono">NSE: {c.ticker_nse}</span>
                        </>
                      )}
                      <span>·</span>
                      <span className="capitalize">{c.listing_status}</span>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    {isQuant ? (
                      <span className="inline-flex items-center gap-1 rounded bg-emerald-950/40 border border-emerald-700/40 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        QUANTITATIVE
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded bg-blue-950/40 border border-blue-700/40 px-2 py-0.5 text-[11px] font-medium text-blue-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                        INTELLIGENCE ONLY
                      </span>
                    )}
                  </td>

                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <ExposureBadge directIndirect={c.direct_indirect} strength={c.exposure_strength} size="xs" />
                      <span className="text-[11px] text-[var(--text-muted)]">({c.exposure_count} bills)</span>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <span className="rounded bg-[var(--bg-elevated)] px-2 py-0.5 text-[11px] text-[var(--text-secondary)] capitalize">
                      {c.primary_mechanism}
                    </span>
                  </td>

                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                      c.market_relevance === "HIGH"
                        ? "bg-rose-950/40 text-rose-300 border border-rose-800/40"
                        : c.market_relevance === "MEDIUM"
                        ? "bg-amber-950/40 text-amber-300 border border-amber-800/40"
                        : "bg-[var(--bg-elevated)] text-[var(--text-muted)] border border-[var(--border-strong)]"
                    }`}>
                      {c.market_relevance}
                    </span>
                  </td>

                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/companies/${encodeURIComponent(c.company_id)}`}
                      className="rounded bg-[var(--bg-elevated)] px-2.5 py-1 text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-white transition-colors"
                    >
                      Dossier →
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default IndustryCorporateExposure;
