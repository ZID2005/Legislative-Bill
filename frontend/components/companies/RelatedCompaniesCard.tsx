/**
 * components/companies/RelatedCompaniesCard.tsx
 * ==============================================
 * Displays legitimate corporate relationships sourced directly from the backend.
 *
 * Relationships:
 * 1. Conglomerate / Group Companies (matching `group_name`)
 * 2. Sector & Industry Peers (queried via `companiesApi.listCompanies({ sector })`)
 *
 * Strict Compliance:
 * - Only uses actual backend data. Zero synthetic corporate affiliations.
 */

"use client";

import React from "react";
import Link from "next/link";
import type { CompanyDetailResponse, CompanySummaryItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge, SourceBadge } from "@/components/ui/Badge";

export interface RelatedCompaniesCardProps {
  company: CompanyDetailResponse;
  peers: CompanySummaryItem[];
  className?: string;
}

export function RelatedCompaniesCard({
  company,
  peers,
  className = "",
}: RelatedCompaniesCardProps) {
  // Exclude current company
  const otherPeers = peers.filter(
    (p) => p.company_id !== company.company_id && p.isin !== company.isin
  );

  return (
    <Card className={className} aria-label="Related Entities Section">
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <CardTitle>Related Entities &amp; Sector Peers</CardTitle>
            <SourceBadge type="FACT" size="xs" showTooltip />
          </div>
          <span className="text-xs text-slate-500">
            {company.sector} Sector
          </span>
        </div>
      </CardHeader>

      <div className="space-y-4 text-xs">
        {/* Group Affiliation if available */}
        {company.group_name && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 space-y-1">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
              Corporate Conglomerate Affiliation
            </span>
            <p className="text-xs font-semibold text-slate-200">
              {company.group_name}
            </p>
            <p className="text-[11px] text-slate-400">
              Member enterprise sharing common group sponsorship and consolidated strategic positioning.
            </p>
          </div>
        )}

        {/* Sector Peers List */}
        <div>
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
            Sector Peers in {company.sector}:
          </span>

          {otherPeers.length === 0 ? (
            <p className="text-slate-500 italic py-2">
              No peer entities recorded within this exact sector classification.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {otherPeers.slice(0, 6).map((peer) => (
                <Link
                  key={peer.company_id}
                  href={`/companies/${encodeURIComponent(peer.company_id)}`}
                  className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 hover:bg-slate-800/60 hover:border-slate-700 transition-colors flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-1.5">
                      <span className="font-semibold text-slate-200 hover:text-blue-400 transition-colors line-clamp-1">
                        {peer.company_name}
                      </span>
                      <Badge
                        variant={peer.is_quant_eligible ? "success" : "info"}
                        size="xs"
                      >
                        {peer.is_quant_eligible ? "Quant" : "Intel"}
                      </Badge>
                    </div>
                    <span className="text-[11px] text-slate-400 block mt-0.5">
                      {peer.industry || peer.sector}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 pt-2 mt-2 border-t border-slate-800/80">
                    <span>{peer.ticker_nse ? `NSE: ${peer.ticker_nse}` : peer.listing_status}</span>
                    <span>{peer.documented_exposure_count || 0} Bills</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

export default RelatedCompaniesCard;
