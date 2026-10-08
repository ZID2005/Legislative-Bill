/**
 * app/companies/CompaniesContent.tsx
 * ===================================
 * Task 8.31C — Modern Institutional Corporate Intelligence Directory.
 *
 * Implements:
 * - 70 Master Companies: 47 Quantitative + 20 Intelligence + 3 Reference
 * - Universe filter tabs with strict firewall distinction
 * - Sector dropdown and full-text search
 * - InstitutionalTable with dense monospace numbers
 * - Quick ContextDrawer inspection
 * - Pagination controls
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { companiesApi } from "@/lib/api/companies";
import type { CompanySummaryItem, PaginatedResponse } from "@/types/api";
import { SearchInput } from "@/components/ui/SearchInput";
import { Pagination } from "@/components/ui/Pagination";
import { InstitutionalTable, type TableColumn } from "@/components/ui/InstitutionalTable";
import { ContextDrawer } from "@/components/ui/ContextDrawer";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { ErrorState, SkeletonCard, EmptyState } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

const LIMIT = 25;

const UNIVERSE_TABS = [
  { id: "", label: "All Universe", count: 70 },
  { id: "quantitative", label: "Quantitative Securities", count: 47 },
  { id: "intelligence", label: "Intelligence Entities", count: 20 },
  { id: "reference", label: "Reference Benchmarks", count: 3 },
];

const SECTOR_OPTIONS = [
  "All Sectors",
  "Financial Services",
  "Energy & Utilities",
  "Information Technology",
  "Healthcare & Pharma",
  "Consumer Goods",
  "Industrials & Manufacturing",
  "Materials & Mining",
  "Telecommunications",
];

export default function CompaniesContent() {
  const [data, setData] = useState<PaginatedResponse<CompanySummaryItem> | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [universeType, setUniverseType] = useState<string>("");
  const [sector, setSector] = useState<string>("");
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Drawer inspection state
  const [inspectCompany, setInspectCompany] = useState<CompanySummaryItem | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params: Record<string, any> = {
      page,
      limit: LIMIT,
      search: search || undefined,
      universe_type: universeType || undefined,
      sector: sector && sector !== "All Sectors" ? sector : undefined,
    };

    companiesApi
      .listCompanies(params)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.userMessage ?? "Failed to load corporate directory.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, search, universeType, sector]);

  const tableColumns: TableColumn<CompanySummaryItem>[] = [
    {
      key: "company_name",
      header: "Entity / Corporate Name",
      sortable: true,
      render: (company) => (
        <div className="min-w-[220px] max-w-sm">
          <Link
            href={`/companies/${company.company_id || company.isin}`}
            className="font-medium text-slate-100 hover:text-indigo-300 transition-colors line-clamp-1"
          >
            {company.company_name}
          </Link>
          <div className="flex items-center gap-1.5 mt-0.5">
            {company.ticker_nse && (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {company.ticker_nse}
              </span>
            )}
            {company.ticker_bse && !company.ticker_nse && (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700">
                BSE: {company.ticker_bse}
              </span>
            )}
            <span className="text-[10px] font-mono text-slate-500">{company.isin}</span>
          </div>
        </div>
      ),
    },
    {
      key: "sector",
      header: "Sector / Industry",
      sortable: true,
      render: (company) => (
        <div className="max-w-[200px]">
          <span className="text-xs text-slate-200 block truncate">{company.sector || "Unclassified"}</span>
          <span className="text-[10px] text-slate-500 block truncate">{company.industry || "—"}</span>
        </div>
      ),
    },
    {
      key: "universe_type",
      header: "Universe Tier",
      sortable: true,
      width: "140px",
      render: (company) => {
        const isQuant =
          company.is_quant_eligible ||
          company.universe_type === "quantitative" ||
          company.universe_type === "both";
        return isQuant ? (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-700/50">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            QUANTITATIVE
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950/60 text-amber-300 border border-amber-700/50">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            INTELLIGENCE
          </span>
        );
      },
    },
    {
      key: "documented_exposure_count",
      header: "Exposures",
      align: "right",
      isNumeric: true,
      sortable: true,
      width: "100px",
      render: (company) => (
        <span className="font-mono-num font-semibold text-slate-200">
          {company.documented_exposure_count ?? 0}
        </span>
      ),
    },
    {
      key: "market_prediction_available",
      header: "Market Predictions",
      sortable: true,
      width: "160px",
      render: (company) => {
        const isQuant =
          company.is_quant_eligible ||
          company.universe_type === "quantitative" ||
          company.universe_type === "both";
        return isQuant ? (
          <div className="flex items-center gap-1">
            <EpistemicBadge type="PREDICTION" size="sm" />
            <span className="text-[11px] text-emerald-400 font-medium">5 Horizons</span>
          </div>
        ) : (
          <span className="text-[10px] font-mono text-amber-400/90 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-800/40">
            FIREWALLED (KNOWLEDGE ONLY)
          </span>
        );
      },
    },
    {
      key: "actions",
      header: "",
      align: "right",
      width: "130px",
      render: (company) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => setInspectCompany(company)}
            className="px-2 py-1 text-[11px] font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 rounded border border-slate-700/60 transition-colors"
            title="Inspect entity details"
          >
            Inspect
          </button>
          <Link
            href={`/companies/${company.company_id || company.isin}`}
            className="px-2 py-1 text-[11px] font-medium text-indigo-300 hover:text-indigo-200 bg-indigo-950/40 hover:bg-indigo-900/50 rounded border border-indigo-700/40 transition-colors"
          >
            Dossier →
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Metric Strip */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xl">🏢</span>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
                Corporate Intelligence Universe
              </h1>
              <EpistemicBadge type="FACT" size="sm" />
            </div>
            <p className="text-sm text-slate-400">
              70 Master Corporate Entities indexed across Central and State legislative exposure networks.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/industries"
              className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded border border-slate-700 transition-colors"
            >
              Industry Breakdown →
            </Link>
            <Link
              href="/sectors"
              className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded border border-slate-700 transition-colors"
            >
              Macro Sectors →
            </Link>
          </div>
        </div>

        {/* 4 Stat Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 shadow-sm">
            <div className="text-xs text-slate-400">Total Universe</div>
            <div className="text-2xl font-bold font-mono-num text-slate-100 mt-1">70</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Master Legal Entities</div>
          </div>
          <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-800/30 shadow-sm">
            <div className="text-xs text-emerald-400">Quantitative Securities</div>
            <div className="text-2xl font-bold font-mono-num text-emerald-300 mt-1">47</div>
            <div className="text-[11px] text-emerald-500/80 mt-0.5">NSE/BSE Listed (Event Study)</div>
          </div>
          <div className="p-3.5 rounded-lg bg-amber-950/20 border border-amber-800/30 shadow-sm">
            <div className="text-xs text-amber-400">Intelligence Entities</div>
            <div className="text-2xl font-bold font-mono-num text-amber-300 mt-1">20</div>
            <div className="text-[11px] text-amber-500/80 mt-0.5">Unlisted / State (Firewalled)</div>
          </div>
          <div className="p-3.5 rounded-lg bg-indigo-950/20 border border-indigo-800/30 shadow-sm">
            <div className="text-xs text-indigo-400">Documented Exposures</div>
            <div className="text-2xl font-bold font-mono-num text-indigo-300 mt-1">104</div>
            <div className="text-[11px] text-indigo-400/70 mt-0.5">Evidence-backed Links</div>
          </div>
        </div>
      </div>

      {/* Universe Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
          {UNIVERSE_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setUniverseType(tab.id);
                setPage(1);
              }}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5",
                universeType === tab.id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              )}
            >
              <span>{tab.label}</span>
              <span
                className={cn(
                  "text-[10px] font-mono px-1 rounded",
                  universeType === tab.id ? "bg-indigo-700/60 text-white" : "bg-slate-800 text-slate-400"
                )}
              >
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-1 bg-slate-900 p-0.5 rounded border border-slate-800 text-xs">
          <button
            onClick={() => setViewMode("table")}
            className={cn(
              "px-2.5 py-1 rounded font-medium transition-colors",
              viewMode === "table" ? "bg-slate-800 text-slate-100" : "text-slate-400 hover:text-slate-200"
            )}
            title="Institutional Table View"
          >
            Dense Table
          </button>
          <button
            onClick={() => setViewMode("grid")}
            className={cn(
              "px-2.5 py-1 rounded font-medium transition-colors",
              viewMode === "grid" ? "bg-slate-800 text-slate-100" : "text-slate-400 hover:text-slate-200"
            )}
            title="Card Grid View"
          >
            Cards
          </button>
        </div>
      </div>

      {/* Search & Sector Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="flex-1">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Search by company name, ticker (e.g., RELIANCE, TCS), or ISIN..."
          />
        </div>
        <div className="w-full sm:w-64">
          <select
            value={sector}
            onChange={(e) => {
              setSector(e.target.value);
              setPage(1);
            }}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-lg focus:outline-none focus:border-indigo-500"
          >
            {SECTOR_OPTIONS.map((sec) => (
              <option key={sec} value={sec}>
                {sec}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filter Notice if Intelligence Selected */}
      {universeType === "intelligence" && (
        <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded-lg flex items-start gap-3">
          <span className="text-amber-400 mt-0.5 text-base">🛡️</span>
          <div>
            <h4 className="text-xs font-semibold text-amber-200">
              Intelligence Universe Firewall Active (KNOWLEDGE ONLY)
            </h4>
            <p className="text-[11px] text-amber-300/80 mt-0.5 leading-relaxed">
              These 20 entities represent unlisted, public sector, and regional operational entities. Per institutional invariants,
              market impact and event-study stock predictions are strictly firewalled (0 stock predictions).
            </p>
          </div>
        </div>
      )}

      {/* Content Rendering */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <SkeletonCard key={i} className="h-14 bg-slate-900/60" />
          ))}
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={() => setPage(1)} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No Corporate Entities Found"
          description="No corporate entities matched your search and filter criteria."
          action={
            <button
              onClick={() => {
                setSearch("");
                setUniverseType("");
                setSector("");
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
            >
              Reset filters
            </button>
          }
        />
      ) : viewMode === "table" ? (
        <div className="space-y-4">
          <InstitutionalTable
            columns={tableColumns}
            data={data.items}
            keyExtractor={(item) => item.company_id || item.isin}
            compact
            striped
          />
          <Pagination
            page={data.page}
            pages={data.pages}
            total={data.total}
            limit={LIMIT}
            onPageChange={setPage}
          />
        </div>
      ) : (
        /* Grid Card Mode */
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.items.map((company) => {
              const isQuant =
                company.is_quant_eligible ||
                company.universe_type === "quantitative" ||
                company.universe_type === "both";
              return (
                <div
                  key={company.company_id || company.isin}
                  className="p-4 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-mono text-slate-500">{company.isin}</span>
                      {isQuant ? (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-950/70 text-emerald-300 border border-emerald-800/40">
                          QUANT
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-800/40">
                          INTELLIGENCE
                        </span>
                      )}
                    </div>
                    <Link
                      href={`/companies/${company.company_id || company.isin}`}
                      className="font-medium text-slate-100 hover:text-indigo-300 transition-colors line-clamp-1 block text-sm"
                    >
                      {company.company_name}
                    </Link>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                      {company.sector} · {company.industry}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-slate-500">Exposures: </span>
                      <span className="font-mono-num font-semibold text-slate-200">
                        {company.documented_exposure_count ?? 0}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setInspectCompany(company)}
                        className="text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800"
                      >
                        Inspect
                      </button>
                      <Link
                        href={`/companies/${company.company_id || company.isin}`}
                        className="text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        Dossier →
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <Pagination
            page={data.page}
            pages={data.pages}
            total={data.total}
            limit={LIMIT}
            onPageChange={setPage}
          />
        </div>
      )}

      {/* Quick Tear-Sheet Inspection Drawer */}
      <ContextDrawer
        open={Boolean(inspectCompany)}
        onClose={() => setInspectCompany(null)}
        title={inspectCompany?.company_name || "Company Overview"}
        subtitle={`ISIN: ${inspectCompany?.isin || "—"}`}
      >
        {inspectCompany && (
          <div className="space-y-5 text-sm">
            {/* Header badges */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                {inspectCompany.ticker_nse ? `NSE: ${inspectCompany.ticker_nse}` : inspectCompany.isin}
              </span>
              {inspectCompany.is_quant_eligible || inspectCompany.universe_type === "quantitative" ? (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-700/50">
                  Quantitative Security
                </span>
              ) : (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-700/50">
                  Intelligence Entity (Knowledge Only)
                </span>
              )}
            </div>

            {/* Core attributes */}
            <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-2.5">
              <div className="flex justify-between">
                <span className="text-xs text-slate-400">Sector</span>
                <span className="text-xs font-medium text-slate-200">{inspectCompany.sector || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-slate-400">Industry</span>
                <span className="text-xs font-medium text-slate-200">{inspectCompany.industry || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-slate-400">Headquarters</span>
                <span className="text-xs font-medium text-slate-200">{inspectCompany.hq_state || "India"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-slate-400">Listing Status</span>
                <span className="text-xs font-medium text-slate-200">{inspectCompany.listing_status || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-slate-400">Documented Exposures</span>
                <span className="text-xs font-mono-num font-semibold text-indigo-300">
                  {inspectCompany.documented_exposure_count ?? 0}
                </span>
              </div>
            </div>

            {/* Firewall Notice if not quant */}
            {!(inspectCompany.is_quant_eligible || inspectCompany.universe_type === "quantitative") && (
              <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/40 text-xs text-amber-300 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <span>🛡️</span> Market Prediction Firewall
                </div>
                <p className="text-amber-300/80 text-[11px] leading-relaxed">
                  This entity is maintained for legislative intelligence and corporate network analysis only. No market price impact predictions are generated.
                </p>
              </div>
            )}

            {/* CTA */}
            <div className="pt-2">
              <Link
                href={`/companies/${inspectCompany.company_id || inspectCompany.isin}`}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors"
              >
                <span>Open Full Company Dossier</span>
                <span>→</span>
              </Link>
            </div>
          </div>
        )}
      </ContextDrawer>
    </div>
  );
}
