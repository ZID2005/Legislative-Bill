/**
 * app/bills/BillsContent.tsx
 * ==========================
 * Paginated bill listing with jurisdiction and status filters.
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { billsApi } from "@/lib/api/bills";
import type { BillSummaryItem, PaginatedResponse } from "@/types/api";
import { JurisdictionBadge, StatusBadge } from "@/components/ui/Badge";
import { CapabilityBadge } from "@/components/coverage/CapabilityBadge";
import { SearchInput } from "@/components/ui/SearchInput";
import { Pagination } from "@/components/ui/Pagination";
import { ErrorState, SkeletonCard, EmptyState } from "@/components/ui/Skeleton";
import { getCapabilityLevel } from "@/lib/utils";

const LIMIT = 20;

export default function BillsContent() {
  const [data, setData] = useState<PaginatedResponse<BillSummaryItem> | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    billsApi
      .listBills({ page, limit: LIMIT, search: search || undefined, jurisdiction: jurisdiction || undefined })
      .then((res) => { if (!cancelled) setData(res); })
      .catch((err) => { if (!cancelled) setError(err?.userMessage ?? "Failed to load bills."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [page, search, jurisdiction]);

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Bills</h1>
          <p className="text-xs text-slate-500 mt-0.5">Central Parliament & State Assembly legislation</p>
        </div>
        {data && (
          <p className="text-xs text-slate-500">
            {new Intl.NumberFormat("en-IN").format(data.total)} bills
          </p>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput
          id="bills-search"
          value={search}
          onChange={(v) => { setSearch(v); setPage(1); }}
          placeholder="Search bills…"
          className="w-full sm:w-72"
        />
        <select
          value={jurisdiction}
          onChange={(e) => { setJurisdiction(e.target.value); setPage(1); }}
          className="bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-300 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
          aria-label="Filter by jurisdiction"
        >
          <option value="">All Jurisdictions</option>
          <option value="central">Central Parliament</option>
          <option value="state">State Assembly</option>
        </select>
      </div>

      {/* Results */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {error && <ErrorState error={error} onRetry={() => setPage(1)} />}

      {!loading && !error && data?.items.length === 0 && (
        <EmptyState
          title="No bills found"
          description="Try adjusting your search or jurisdiction filter."
          icon="📜"
        />
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.items.map((bill) => (
              <BillCard key={bill.bill_id} bill={bill} />
            ))}
          </div>
          <Pagination
            page={data.page}
            pages={data.pages}
            total={data.total}
            limit={data.limit}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}

function BillCard({ bill }: { bill: BillSummaryItem }) {
  const capLevel = getCapabilityLevel(bill.jurisdiction, bill.modeling_eligibility);

  return (
    <Link
      href={`/bills/${bill.bill_id}`}
      className="group block rounded-lg border border-slate-800 bg-slate-900 p-4 hover:border-slate-700 hover:bg-slate-800/60 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex flex-wrap gap-1.5">
          <JurisdictionBadge jurisdiction={bill.jurisdiction} state={bill.state} size="xs" />
          <CapabilityBadge level={capLevel} size="xs" />
        </div>
        <StatusBadge status={bill.status} size="xs" />
      </div>
      <h3 className="text-sm font-semibold text-slate-200 line-clamp-2 group-hover:text-white transition-colors mt-2 mb-1.5">
        {bill.short_title}
      </h3>
      <p className="text-xs text-slate-500 line-clamp-2 mb-3">{bill.summary}</p>
      <div className="flex items-center justify-between text-xs text-slate-600">
        <span>{bill.year ?? "—"} · {bill.house}</span>
        {bill.company_exposure_count > 0 && (
          <span className="text-blue-500">{bill.company_exposure_count} exposures</span>
        )}
      </div>
    </Link>
  );
}
