/**
 * components/bills/RelatedBillsCard.tsx
 * =====================================
 * Displays related legislative bills linked through parliamentary or statutory networks.
 */

"use client";

import React from "react";
import Link from "next/link";
import type { BillSummaryItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { JurisdictionBadge, StatusBadge } from "@/components/ui/Badge";

export interface RelatedBillsCardProps {
  relatedBills: BillSummaryItem[];
  className?: string;
}

export function RelatedBillsCard({
  relatedBills,
  className = "",
}: RelatedBillsCardProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <CardTitle>Related Legislation</CardTitle>
          <span className="text-[11px] text-slate-500 font-mono">
            {relatedBills.length} linked
          </span>
        </div>
      </CardHeader>

      {relatedBills.length > 0 ? (
        <div className="space-y-2.5">
          {relatedBills.map((rb) => (
            <Link
              key={rb.bill_id}
              href={`/bills/${encodeURIComponent(rb.bill_id)}`}
              className="block rounded-lg border border-slate-800 bg-slate-900/40 p-3 hover:bg-slate-900/80 hover:border-slate-700 transition-all group"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1.5 flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition-colors line-clamp-2">
                    {rb.short_title || rb.title}
                  </p>
                  <div className="flex flex-wrap items-center gap-1.5">
                    <JurisdictionBadge
                      jurisdiction={rb.jurisdiction}
                      state={rb.state}
                      size="xs"
                    />
                    <StatusBadge status={rb.status} size="xs" />
                  </div>
                </div>
                <span
                  className="text-slate-600 group-hover:text-blue-400 transition-colors text-sm"
                  aria-hidden="true"
                >
                  →
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-500 italic py-2">
          No directly linked related enactments recorded in the parliamentary graph.
        </p>
      )}
    </Card>
  );
}

export default RelatedBillsCard;
