/**
 * app/bills/BillsContent.tsx
 * ==========================
 * Task 8.31C — Institutional Parliamentary & Assembly Bills Directory.
 *
 * Implements:
 * - Structured canonical index: All (66), Central (20), States (44)
 * - Dual-view mode: High-density Institutional Table (default) vs Card Grid
 * - StatePredictionFirewall banner on sub-national assembly tabs
 * - Search debouncing and sorting
 * - Pagination controls
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { billsApi } from "@/lib/api/bills";
import type { BillSummaryItem, PaginatedResponse } from "@/types/api";
import { JurisdictionBadge, StatusBadge } from "@/components/ui/Badge";
import { CapabilityBadge } from "@/components/coverage/CapabilityBadge";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { SearchInput } from "@/components/ui/SearchInput";
import { Pagination } from "@/components/ui/Pagination";
import { InstitutionalTable, type TableColumn } from "@/components/ui/InstitutionalTable";
import { ErrorState, SkeletonCard, EmptyState } from "@/components/ui/Skeleton";
import { getCapabilityLevel } from "@/lib/utils";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { cn } from "@/lib/utils";

const LIMIT = 25;

export default function BillsContent() {
  const [data, setData] = useState<PaginatedResponse<BillSummaryItem> | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [jurisdiction, setJurisdiction] = useState<string>("");
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    billsApi
      .listBills({ page, limit: LIMIT, search: search || undefined, jurisdiction: jurisdiction || undefined })
      .then((res) => { if (!cancelled) setData(res); })
      .catch((err) => { if (!cancelled) setError(err?.userMessage ?? "Failed to load bills directory."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [page, search, jurisdiction]);

  const tableColumns: TableColumn<BillSummaryItem>[] = [
    {
      key: "title",
      header: "Act / Enactment Title",
      sortable: true,
      render: (bill) => (
        <div className="min-w-[240px] max-w-md">
          <Link
            href={`/bills/${bill.bill_id}`}
            className="font-medium text-slate-100 hover:text-indigo-300 transition-colors line-clamp-1"
          >
            {bill.title}
          </Link>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[10px] font-mono text-slate-500">{bill.bill_number || bill.bill_id}</span>
            {bill.year && <span className="text-[10px] text-slate-600">· {bill.year}</span>}
          </div>
        </div>
      ),
    },
    {
      key: "jurisdiction",
      header: "Jurisdiction",
      sortable: true,
      width: "120px",
      render: (bill) => (
        <div className="flex items-center gap-1">
          <JurisdictionBadge jurisdiction={bill.jurisdiction} />
          {bill.state && (
            <span className="text-[10px] font-mono text-slate-400">({bill.state})</span>
          )}
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      width: "110px",
      render: (bill) => <StatusBadge status={bill.status} />,
    },
    {
      key: "company_exposure_count",
      header: "Exposures",
      align: "right",
      isNumeric: true,
      sortable: true,
      width: "100px",
      render: (bill) => (
        <span className="font-mono text-slate-200">
          {bill.company_exposure_count ?? 0}
        </span>
      ),
    },
    {
      key: "capability",
      header: "Modeling Tier",
      width: "120px",
      render: (bill) => {
        const level = getCapabilityLevel(bill.jurisdiction, bill.modeling_eligibility);
        return <CapabilityBadge level={level} />;
      },
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      width: "110px",
      render: (bill) => (
        <Link
          href={`/bills/${bill.bill_id}`}
          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-indigo-400 text-[11px] font-medium transition-colors"
        >
          Dossier ↗
        </Link>
      ),
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100">Bills Directory</h1>
            <EpistemicBadge type="FACT" size="xs" />
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Canonical statutory index of Central Parliament and State Assembly enactments
          </p>
        </div>
        {data && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">
              {new Intl.NumberFormat("en-IN").format(data.total)} Enactments Indexed
            </span>
          </div>
        )}
      </div>

      {/* Jurisdiction Hub Tabs */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <div className="flex items-center gap-1">
          {[
            { id: "", label: "All Legislation" },
            { id: "central", label: "Central Parliament" },
            { id: "state", label: "State Assemblies" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setJurisdiction(tab.id); setPage(1); }}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                jurisdiction === tab.id
                  ? "bg-indigo-600 text-white font-semibold"
                  : "text-slate-400 hover:text-white hover:bg-white/5"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* View mode toggle */}
        <div className="flex items-center gap-1 bg-white/5 p-0.5 rounded-md border border-white/10">
          <button
            onClick={() => setViewMode("table")}
            className={cn(
              "px-2 py-1 rounded text-xs transition-colors",
              viewMode === "table" ? "bg-white/15 text-white font-medium" : "text-slate-400 hover:text-slate-200"
            )}
            title="Dense Table View"
          >
            ☰ Table
          </button>
          <button
            onClick={() => setViewMode("grid")}
            className={cn(
              "px-2 py-1 rounded text-xs transition-colors",
              viewMode === "grid" ? "bg-white/15 text-white font-medium" : "text-slate-400 hover:text-slate-200"
            )}
            title="Card Grid View"
          >
            ⊞ Cards
          </button>
        </div>
      </div>

      {/* Sub-national State Firewall Banner if viewing State bills */}
      {jurisdiction === "state" && (
        <div className="animate-fade-in">
          <StatePredictionFirewall />
        </div>
      )}

      {/* Search Input Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput
          id="bills-search"
          value={search}
          onChange={(v) => { setSearch(v); setPage(1); }}
          placeholder="Search by title, bill number, or ministry..."
          className="w-full sm:w-80"
        />
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {error && <ErrorState error={error} onRetry={() => setPage(1)} />}

      {!loading && !error && data?.items.length === 0 && (
        <EmptyState
          title="No legislation found"
          description="Try adjusting your keyword query or jurisdiction selection."
          icon="📜"
        />
      )}

      {/* Results Rendering */}
      {!loading && !error && data && data.items.length > 0 && (
        <>
          {viewMode === "table" ? (
            <InstitutionalTable
              columns={tableColumns}
              data={data.items}
              keyExtractor={(b) => b.bill_id}
              compact={true}
              striped={true}
              stickyHeader={true}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {data.items.map((bill) => (
                <BillCard key={bill.bill_id} bill={bill} />
              ))}
            </div>
          )}

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
      className="group block rounded-lg border border-white/10 bg-[#0c1322] p-4 hover:border-indigo-500/40 hover:bg-[#121b2f] transition-all duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <JurisdictionBadge jurisdiction={bill.jurisdiction} />
        <StatusBadge status={bill.status} />
      </div>

      <h2 className="text-sm font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-2 mb-1.5">
        {bill.title}
      </h2>

      {bill.summary && (
        <p className="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">
          {bill.summary}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/5">
        <CapabilityBadge level={capLevel} />
        <span className="font-mono text-slate-300 font-medium">
          {bill.company_exposure_count ?? 0} exposures
        </span>
      </div>
    </Link>
  );
}
