/**
 * components/bills/ExecutiveSummary.tsx
 * =====================================
 * Executive Summary component for the Bill Detail Dossier.
 * Displays plain-language factual summary and core legislative dimensions.
 */

"use client";

import React from "react";
import type { BillSummaryItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge } from "@/components/ui/Badge";

export interface ExecutiveSummaryProps {
  bill: BillSummaryItem;
  className?: string;
}

export function ExecutiveSummary({ bill, className = "" }: ExecutiveSummaryProps) {
  const summaryText =
    bill.summary && bill.summary.trim().length > 0
      ? bill.summary
      : "Official legislative summary is not provided in source parliamentary records. Refer to statutory text and extracted provisions.";

  return (
    <div className={`space-y-4 ${className}`}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Executive Summary</CardTitle>
            <SourceBadge type="FACT" size="xs" showTooltip />
          </div>
        </CardHeader>
        <div className="space-y-4">
          <p className="text-sm text-slate-300 leading-relaxed font-normal">
            {summaryText}
          </p>

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5 pt-2 border-t border-slate-800/80">
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-2.5">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
                Policy Domain
              </p>
              <p className="text-xs font-medium text-slate-200 truncate">
                {bill.policy_domain || "General Legislation"}
              </p>
            </div>

            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-2.5">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
                Primary Sector
              </p>
              <p className="text-xs font-medium text-slate-200 truncate">
                {bill.economic_sectors && bill.economic_sectors.length > 0
                  ? bill.economic_sectors[0]
                  : "Multi-sectoral"}
              </p>
            </div>

            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-2.5">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
                Corporate Exposures
              </p>
              <p className="text-xs font-medium text-slate-200">
                {bill.company_exposure_count} verified{" "}
                <span className="text-[11px] text-slate-400">
                  ({bill.listed_company_exposure_count} listed)
                </span>
              </p>
            </div>

            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-2.5">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-0.5">
                Market Relevance
              </p>
              <p className="text-xs font-medium text-slate-200">
                {bill.market_relevance}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default ExecutiveSummary;
