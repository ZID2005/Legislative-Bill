/**
 * app/explorer/ExplorerContent.tsx
 * ================================
 * India Legislative Explorer — Unified Discovery for Central & State Legislation.
 *
 * Implements:
 * - Full-text global search & token search
 * - Dual discovery: Structured Legislative Bills filtering + Unified Cross-Entity Search
 * - Multi-attribute filter sidebar (jurisdiction, state, status, year, sector, policy domain,
 *   stakeholder, market relevance, prediction availability, corporate exposure)
 * - Capability-aware result cards with strict Central vs State firewall behavior
 * - Planned state roadmap notices
 * - Server-side pagination with URL query synchronization
 * - Responsive layout (collapsible mobile filter drawer)
 * - Accessibility (semantic HTML, keyboard search, aria labels)
 */

"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { billsApi, ListBillsParams } from "@/lib/api/bills";
import { searchApi } from "@/lib/api/search";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import {
  CapabilityBadge,
  JurisdictionBadge,
  MarketRelevanceBadge,
  CorporateExposureBadge,
  PredictionAvailability,
} from "@/components/coverage/CapabilityBadge";
import { SkeletonCard, ErrorState } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";
import { formatDate } from "@/lib/utils";
import type {
  BillSummaryItem,
  PaginatedResponse,
  SearchResponse,
  SearchResultItem,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Constants & Taxonomy Options
// ---------------------------------------------------------------------------

const IMPLEMENTED_STATES = ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"];

const PLANNED_STATES = [
  "Maharashtra",
  "Tamil Nadu",
  "Gujarat",
  "Uttar Pradesh",
  "West Bengal",
  "Rajasthan",
  "Madhya Pradesh",
  "Punjab",
  "Haryana",
  "Bihar",
  "Odisha",
  "Assam",
  "Jharkhand",
  "Chhattisgarh",
  "Himachal Pradesh",
  "Uttarakhand",
  "Goa",
  "Tripura",
  "Meghalaya",
  "Manipur",
  "Nagaland",
  "Arunachal Pradesh",
  "Mizoram",
  "Sikkim",
];

const ECONOMIC_SECTORS = [
  "Banking & Financial Services",
  "Energy & Power",
  "Information Technology",
  "Infrastructure & Logistics",
  "Healthcare & Pharmaceuticals",
  "Agriculture & Commodities",
  "Automotive & Mobility",
  "Consumer Goods & Retail",
  "Telecommunications & Media",
  "Mining & Metals",
  "Heavy Industries & Manufacturing",
  "Chemicals & Fertilizers",
  "Textiles & Apparel",
  "Real Estate & Urban Development",
];

const POLICY_DOMAINS = [
  "Financial Regulation",
  "Commerce & Industry",
  "Digital Governance",
  "Environmental & Energy Policy",
  "Labour & Employment",
  "Health & Welfare",
  "Taxation & Fiscal Policy",
  "Infrastructure Development",
];

const STAKEHOLDERS = [
  "Listed Corporates",
  "Financial Institutions",
  "Retail Investors",
  "MSMEs & Startups",
  "Consumers",
  "Industrial Producers",
];

const YEARS = [2024, 2023, 2022, 2021, 2020, 2019];

// ---------------------------------------------------------------------------
// Explorer Content Component
// ---------------------------------------------------------------------------

export default function ExplorerContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Read URL query parameters
  const qParam = searchParams.get("q") ?? searchParams.get("search") ?? "";
  const jurisdictionParam = searchParams.get("jurisdiction") ?? "all";
  const stateParam = searchParams.get("state") ?? "all";
  const statusParam = searchParams.get("status") ?? "all";
  const yearParam = searchParams.get("year") ?? "all";
  const sectorParam = searchParams.get("sector") ?? "all";
  const domainParam = searchParams.get("policy_domain") ?? "all";
  const stakeholderParam = searchParams.get("stakeholder") ?? "all";
  const relevanceParam = searchParams.get("market_relevance") ?? "all";
  const eligibilityParam = searchParams.get("modeling_eligibility") ?? "all";
  const exposureParam = searchParams.get("has_company_exposure") ?? "all";
  const pageParam = parseInt(searchParams.get("page") ?? "1", 10);
  const modeParam = (searchParams.get("mode") as "bills" | "unified") ?? "bills";

  // Local state
  const [searchInput, setSearchInput] = useState(qParam);
  const [activeMode, setActiveMode] = useState<"bills" | "unified">(modeParam);
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);

  // Data fetching states
  const [billsData, setBillsData] = useState<PaginatedResponse<BillSummaryItem> | null>(null);
  const [unifiedData, setUnifiedData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sync input when URL param changes
  useEffect(() => {
    setSearchInput(qParam);
  }, [qParam]);

  // Push state to URL query params
  const updateUrlParams = useCallback(
    (updates: Record<string, string | number | null>) => {
      const current = new URLSearchParams(searchParams.toString());

      Object.entries(updates).forEach(([key, val]) => {
        if (
          val === null ||
          val === "" ||
          val === "all" ||
          (key === "page" && (val === 1 || val === "1"))
        ) {
          current.delete(key);
        } else {
          current.set(key, String(val));
        }
      });

      // Reset page if not explicitly provided in updates
      if (!("page" in updates)) {
        current.delete("page");
      }

      const queryString = current.toString();
      router.push(queryString ? `${pathname}?${queryString}` : pathname);
    },
    [pathname, router, searchParams]
  );

  // Is the currently selected state a planned state?
  const isPlannedState = useMemo(() => {
    if (stateParam === "all") return false;
    return PLANNED_STATES.some((s) => s.toLowerCase() === stateParam.toLowerCase());
  }, [stateParam]);

  // Fetch Bills or Unified Search
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (activeMode === "unified" && qParam.trim()) {
        // Unified cross-entity search
        const res = await searchApi.globalSearch(qParam.trim(), 20);
        setUnifiedData(res);
      } else {
        // Structured Bills search & filtering
        const params: ListBillsParams = {
          page: pageParam,
          limit: 10,
          search: qParam.trim() || undefined,
          jurisdiction: jurisdictionParam !== "all" ? jurisdictionParam : undefined,
          state: stateParam !== "all" ? stateParam : undefined,
          status: statusParam !== "all" ? statusParam : undefined,
          year: yearParam !== "all" ? parseInt(yearParam, 10) : undefined,
          sector: sectorParam !== "all" ? sectorParam : undefined,
          policy_domain: domainParam !== "all" ? domainParam : undefined,
          stakeholder: stakeholderParam !== "all" ? stakeholderParam : undefined,
          market_relevance: relevanceParam !== "all" ? relevanceParam : undefined,
          modeling_eligibility: eligibilityParam !== "all" ? eligibilityParam : undefined,
          has_company_exposure:
            exposureParam === "true" ? true : exposureParam === "false" ? false : undefined,
          sort_by: "introduction_date",
          sort_order: "desc",
        };

        const res = await billsApi.listBills(params);
        setBillsData(res);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load legislative records.");
    } finally {
      setLoading(false);
    }
  }, [
    activeMode,
    qParam,
    pageParam,
    jurisdictionParam,
    stateParam,
    statusParam,
    yearParam,
    sectorParam,
    domainParam,
    stakeholderParam,
    relevanceParam,
    eligibilityParam,
    exposureParam,
  ]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle search submission
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateUrlParams({ q: searchInput.trim() || null, page: 1 });
  };

  const handleClearSearch = () => {
    setSearchInput("");
    updateUrlParams({ q: null, page: 1 });
  };

  // Clear all filters
  const handleResetFilters = () => {
    setSearchInput("");
    router.push(pathname);
  };

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (jurisdictionParam !== "all") count++;
    if (stateParam !== "all") count++;
    if (statusParam !== "all") count++;
    if (yearParam !== "all") count++;
    if (sectorParam !== "all") count++;
    if (domainParam !== "all") count++;
    if (stakeholderParam !== "all") count++;
    if (relevanceParam !== "all") count++;
    if (eligibilityParam !== "all") count++;
    if (exposureParam !== "all") count++;
    return count;
  }, [
    jurisdictionParam,
    stateParam,
    statusParam,
    yearParam,
    sectorParam,
    domainParam,
    stakeholderParam,
    relevanceParam,
    eligibilityParam,
    exposureParam,
  ]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in text-slate-200">
      {/* ==================================================================== */}
      {/* 10. EXPLORER HEADER */}
      {/* ==================================================================== */}
      <header className="border-b border-slate-800 pb-5 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl" aria-hidden="true">
                🏛
              </span>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
                India Legislative Explorer
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl">
              Search and explore Central and State legislation, economic intelligence, corporate
              exposure, and market-model availability across the Indian Union.
            </p>
          </div>

          {/* Discovery Mode Switch */}
          <div className="inline-flex rounded-lg border border-slate-800 bg-slate-900 p-1 text-xs">
            <button
              type="button"
              onClick={() => {
                setActiveMode("bills");
                updateUrlParams({ mode: null });
              }}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeMode === "bills"
                  ? "bg-blue-900/60 text-blue-200 border border-blue-700/50"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              📜 Legislative Bills
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveMode("unified");
                updateUrlParams({ mode: "unified" });
              }}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeMode === "unified"
                  ? "bg-blue-900/60 text-blue-200 border border-blue-700/50"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              🌐 Unified Cross-Entity
            </button>
          </div>
        </div>
      </header>

      {/* ==================================================================== */}
      {/* 11. GLOBAL SEARCH BAR */}
      {/* ==================================================================== */}
      <section aria-label="Search controls" className="space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <span
              className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500 pointer-events-none"
              aria-hidden="true"
            >
              🔍
            </span>
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={
                activeMode === "unified"
                  ? "Search across bills, companies (Reliance, Tata...), sectors, or states..."
                  : "Search bill titles, bill numbers (e.g. 33 of 2024), sectors, keywords..."
              }
              aria-label="Legislative Search Query"
              className="w-full pl-9 pr-10 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
            {searchInput && (
              <button
                type="button"
                onClick={handleClearSearch}
                aria-label="Clear search"
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            )}
          </div>

          <Button type="submit" variant="primary" size="md">
            Search
          </Button>

          {/* Mobile Filter Toggle Button */}
          <Button
            type="button"
            variant="secondary"
            size="md"
            className="lg:hidden flex items-center gap-1.5"
            onClick={() => setMobileFilterOpen(!mobileFilterOpen)}
            aria-expanded={mobileFilterOpen}
          >
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <span className="bg-blue-600 text-white rounded-full px-1.5 text-[10px] font-bold">
                {activeFilterCount}
              </span>
            )}
          </Button>
        </form>

        {/* Active Filter Badges & Reset Button */}
        {activeFilterCount > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="text-slate-400 font-medium">Active Filters ({activeFilterCount}):</span>
            {jurisdictionParam !== "all" && (
              <Badge variant="primary" size="xs">
                Jurisdiction: {jurisdictionParam}
              </Badge>
            )}
            {stateParam !== "all" && (
              <Badge variant="info" size="xs">
                State: {stateParam}
              </Badge>
            )}
            {sectorParam !== "all" && (
              <Badge variant="muted" size="xs">
                Sector: {sectorParam}
              </Badge>
            )}
            {domainParam !== "all" && (
              <Badge variant="muted" size="xs">
                Domain: {domainParam}
              </Badge>
            )}
            {relevanceParam !== "all" && (
              <Badge variant="amber" size="xs">
                Relevance: {relevanceParam}
              </Badge>
            )}
            {eligibilityParam !== "all" && (
              <Badge variant="emerald" size="xs">
                Model: {eligibilityParam}
              </Badge>
            )}
            {exposureParam !== "all" && (
              <Badge variant="slate" size="xs">
                Exposures: {exposureParam === "true" ? "Verified" : "None"}
              </Badge>
            )}
            <button
              type="button"
              onClick={handleResetFilters}
              className="text-xs text-blue-400 hover:text-blue-300 underline ml-1"
            >
              Reset all
            </button>
          </div>
        )}
      </section>

      {/* Planned State Roadmap Notice */}
      {isPlannedState && (
        <div
          role="status"
          className="rounded-lg border border-amber-800/40 bg-amber-950/20 p-4 text-xs text-amber-200 space-y-1"
        >
          <div className="flex items-center gap-2 font-semibold">
            <span>📍</span>
            <span>Planned State Coverage: {stateParam} (Roadmap Expansion)</span>
          </div>
          <p className="text-amber-300/80 leading-relaxed">
            {stateParam} is scheduled in the Level 3 Union expansion pipeline. 0 legislative bills
            have been ingested to date. Official state assembly gazette scrapers and statutory
            dossiers will be integrated in subsequent phases.
          </p>
        </div>
      )}

      {/* Main Grid: Sidebar Filters + Results Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* ================================================================== */}
        {/* 12. FILTER SIDEBAR */}
        {/* ================================================================== */}
        <aside
          aria-label="Legislative Filters"
          className={`lg:block ${
            mobileFilterOpen ? "block" : "hidden"
          } space-y-5 bg-slate-900 border border-slate-800 p-4 rounded-xl text-xs`}
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="font-semibold text-slate-200 uppercase tracking-wider text-[11px]">
              Filter Criteria
            </span>
            {activeFilterCount > 0 && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="text-blue-400 hover:text-blue-300 text-[11px]"
              >
                Reset
              </button>
            )}
          </div>

          {/* Jurisdiction Filter */}
          <div className="space-y-1.5">
            <label htmlFor="jurisdiction-select" className="block text-slate-400 font-medium">Jurisdiction</label>
            <select
              id="jurisdiction-select"
              value={jurisdictionParam}
              onChange={(e) => updateUrlParams({ jurisdiction: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Jurisdictions (Unified)</option>
              <option value="central">Central Parliament</option>
              <option value="state">State Assembly</option>
            </select>
          </div>

          {/* State Filter */}
          <div className="space-y-1.5">
            <label htmlFor="state-select" className="block text-slate-400 font-medium">Indian State / Assembly</label>
            <select
              id="state-select"
              value={stateParam}
              onChange={(e) => updateUrlParams({ state: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All States</option>
              <optgroup label="Active Pilot Assemblies (L2)">
                {IMPLEMENTED_STATES.map((s) => (
                  <option key={s} value={s}>
                    {s} (Active Pilot)
                  </option>
                ))}
              </optgroup>
              <optgroup label="Roadmap Pipeline (L3)">
                {PLANNED_STATES.map((s) => (
                  <option key={s} value={s}>
                    {s} (Planned · 0 bills)
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* Economic Sector Filter */}
          <div className="space-y-1.5">
            <label htmlFor="sector-select" className="block text-slate-400 font-medium">Economic Sector</label>
            <select
              id="sector-select"
              value={sectorParam}
              onChange={(e) => updateUrlParams({ sector: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Sectors (14 Sectors)</option>
              {ECONOMIC_SECTORS.map((sec) => (
                <option key={sec} value={sec}>
                  {sec}
                </option>
              ))}
            </select>
          </div>

          {/* Policy Domain Filter */}
          <div className="space-y-1.5">
            <label htmlFor="domain-select" className="block text-slate-400 font-medium">Policy Domain</label>
            <select
              id="domain-select"
              value={domainParam}
              onChange={(e) => updateUrlParams({ policy_domain: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Policy Domains</option>
              {POLICY_DOMAINS.map((dom) => (
                <option key={dom} value={dom}>
                  {dom}
                </option>
              ))}
            </select>
          </div>

          {/* Affected Stakeholder */}
          <div className="space-y-1.5">
            <label htmlFor="stakeholder-select" className="block text-slate-400 font-medium">Affected Stakeholder</label>
            <select
              id="stakeholder-select"
              value={stakeholderParam}
              onChange={(e) => updateUrlParams({ stakeholder: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Stakeholders</option>
              {STAKEHOLDERS.map((stk) => (
                <option key={stk} value={stk}>
                  {stk}
                </option>
              ))}
            </select>
          </div>

          {/* Market Relevance Filter */}
          <div className="space-y-1.5">
            <label htmlFor="relevance-select" className="block text-slate-400 font-medium">Market Relevance</label>
            <select
              id="relevance-select"
              value={relevanceParam}
              onChange={(e) => updateUrlParams({ market_relevance: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Relevance Levels</option>
              <option value="HIGH">High Relevance</option>
              <option value="MEDIUM">Medium Relevance</option>
              <option value="LOW">Low Relevance</option>
              <option value="NONE">None / Neutral</option>
            </select>
          </div>

          {/* Modeling Eligibility (Prediction Availability) */}
          <div className="space-y-1.5">
            <label htmlFor="eligibility-select" className="block text-slate-400 font-medium">Prediction Availability</label>
            <select
              id="eligibility-select"
              value={eligibilityParam}
              onChange={(e) => updateUrlParams({ modeling_eligibility: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Eligibility</option>
              <option value="ELIGIBLE">Market Modelled (Central Production)</option>
              <option value="NOT_ELIGIBLE">Not Modelled (State / Non-Modelled)</option>
            </select>
          </div>

          {/* Corporate Exposure Filter */}
          <div className="space-y-1.5">
            <label htmlFor="exposure-select" className="block text-slate-400 font-medium">Corporate Exposure</label>
            <select
              id="exposure-select"
              value={exposureParam}
              onChange={(e) => updateUrlParams({ has_company_exposure: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Legislation</option>
              <option value="true">Documented Exposures Only</option>
              <option value="false">No Documented Exposures</option>
            </select>
          </div>

          {/* Year Filter */}
          <div className="space-y-1.5">
            <label htmlFor="year-select" className="block text-slate-400 font-medium">Year</label>
            <select
              id="year-select"
              value={yearParam}
              onChange={(e) => updateUrlParams({ year: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Years</option>
              {YEARS.map((y) => (
                <option key={y} value={String(y)}>
                  {y}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="space-y-1.5">
            <label htmlFor="status-select" className="block text-slate-400 font-medium">Bill Status</label>
            <select
              id="status-select"
              value={statusParam}
              onChange={(e) => updateUrlParams({ status: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="passed">Passed / Enacted</option>
              <option value="introduced">Introduced / Tabled</option>
              <option value="pending">Pending</option>
            </select>
          </div>
        </aside>

        {/* ================================================================== */}
        {/* 13. RESULTS FEED */}
        {/* ================================================================== */}
        <main className="lg:col-span-3 space-y-4">
          {/* Results Header with Counts & Sort */}
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2 text-xs text-slate-400 border-b border-slate-800/80">
            <div>
              {loading ? (
                <span>Loading records...</span>
              ) : activeMode === "unified" && unifiedData ? (
                <span>
                  Found <strong className="text-slate-200">{unifiedData.total_matches}</strong>{" "}
                  cross-entity matches for &ldquo;{unifiedData.query}&rdquo;
                </span>
              ) : billsData ? (
                <span>
                  Showing{" "}
                  <strong className="text-slate-200">
                    {billsData.items.length > 0
                      ? (billsData.page - 1) * billsData.limit + 1
                      : 0}
                    –{(billsData.page - 1) * billsData.limit + billsData.items.length}
                  </strong>{" "}
                  of <strong className="text-slate-200">{billsData.total}</strong> legislative records
                </span>
              ) : null}
            </div>

            {activeMode === "bills" && (
              <div className="flex items-center gap-1.5">
                <span className="text-slate-500">Sort:</span>
                <span className="text-slate-300 font-medium">Latest Introduction</span>
              </div>
            )}
          </div>

          {/* Error State */}
          {error && <ErrorState error={new Error(error)} onRetry={fetchData} />}

          {/* Loading Skeletons */}
          {loading && (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          )}

          {/* UNIFIED SEARCH MODE RESULTS */}
          {!loading && !error && activeMode === "unified" && unifiedData && (
            <div className="space-y-3">
              {unifiedData.items.length === 0 ? (
                <Card className="p-8 text-center space-y-3">
                  <div className="text-2xl">🔍</div>
                  <h3 className="text-sm font-semibold text-slate-200">No matching entities found</h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    Try searching for a different keyword, company name, sector, or switch to the
                    Bills tab.
                  </p>
                </Card>
              ) : (
                unifiedData.items.map((it: SearchResultItem) => (
                  <Card key={`${it.category}-${it.id}`} className="hover:border-slate-700 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            {it.category === "bills_central"
                              ? "BILL · CENTRAL"
                              : it.category === "bills_state"
                              ? "BILL · STATE"
                              : it.category === "companies_quant"
                              ? "COMPANY · QUANT"
                              : it.category === "companies_intel"
                              ? "COMPANY · INTEL"
                              : it.category === "industries"
                              ? "INDUSTRY"
                              : it.category === "sectors"
                              ? "SECTOR"
                              : it.category === "states"
                              ? "STATE"
                              : it.category === "monitoring"
                              ? "MONITORING"
                              : String(it.category).replace("_", " ")}
                          </span>
                          {it.jurisdiction && (
                            <JurisdictionBadge jurisdiction={it.jurisdiction} state={it.state} size="xs" />
                          )}
                        </div>

                        <h3 className="text-sm font-semibold text-slate-100">
                          {it.title}
                        </h3>

                        {it.subtitle && (
                          <p className="text-xs text-slate-400">{it.subtitle}</p>
                        )}
                      </div>

                      <Link href={it.url}>
                        <Button variant="secondary" size="xs">
                          Explore →
                        </Button>
                      </Link>
                    </div>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* BILLS MODE RESULTS */}
          {!loading && !error && activeMode === "bills" && billsData && (
            <div className="space-y-4">
              {billsData.items.length === 0 ? (
                <Card className="p-8 text-center space-y-3">
                  <div className="text-2xl">📋</div>
                  <h3 className="text-sm font-semibold text-slate-200">No legislation found</h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    No legislative bills matched your active search query or filter combination.
                  </p>
                  <Button variant="outline" size="sm" onClick={handleResetFilters}>
                    Reset All Filters
                  </Button>
                </Card>
              ) : (
                billsData.items.map((b) => {
                  const isState = b.jurisdiction?.toLowerCase() === "state";
                  const isModelEligible = b.modeling_eligibility === "ELIGIBLE";

                  return (
                    <Card
                      key={b.bill_id}
                      className="p-5 hover:border-slate-700 transition-colors space-y-3.5"
                    >
                      {/* Top Badges Row */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <JurisdictionBadge jurisdiction={b.jurisdiction} state={b.state} size="xs" />
                          <StatusBadge status={b.status} size="xs" />
                          <MarketRelevanceBadge relevance={b.market_relevance} size="xs" />
                          {b.company_exposure_count > 0 && (
                            <CorporateExposureBadge count={b.company_exposure_count} size="xs" />
                          )}
                        </div>

                        {/* Capability Level Badge */}
                        <CapabilityBadge
                          level={isState ? 2 : isModelEligible ? 1 : 2}
                          size="xs"
                        />
                      </div>

                      {/* Bill Title & Identifiers */}
                      <div>
                        <h2 className="text-base font-semibold text-slate-100 hover:text-blue-300 transition-colors">
                          <Link href={`/bills/${b.bill_id}`}>
                            {b.short_title || b.title}
                          </Link>
                        </h2>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 font-mono mt-1">
                          {b.bill_number && <span>No: {b.bill_number}</span>}
                          <span>·</span>
                          <span>Chamber: {b.house}</span>
                          <span>·</span>
                          <span>
                            Introduced:{" "}
                            {b.introduction_date ? formatDate(b.introduction_date) : b.year ?? "N/A"}
                          </span>
                        </div>
                      </div>

                      {/* Summary */}
                      <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">
                        {b.summary}
                      </p>

                      {/* Sectors and Domain Tags */}
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        {b.policy_domain && (
                          <Badge variant="muted" size="xs">
                            Domain: {b.policy_domain}
                          </Badge>
                        )}
                        {b.economic_sectors.slice(0, 3).map((sec) => (
                          <span
                            key={sec}
                            className="text-[10px] font-medium bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700/60"
                          >
                            {sec}
                          </span>
                        ))}
                      </div>

                      {/* 15 & 16: State vs Central Prediction Behavior */}
                      <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          {isState ? (
                            <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                              <span className="text-blue-400">ℹ</span>
                              <span>
                                Economic intelligence only ·{" "}
                                <strong className="text-slate-300">
                                  Market prediction not currently available for State legislation.
                                </strong>
                              </span>
                            </div>
                          ) : isModelEligible ? (
                            <div className="flex items-center gap-2">
                              <PredictionAvailability
                                available={true}
                                jurisdiction="central"
                              />
                              <Link
                                href={`/predictions?bill_id=${b.bill_id}`}
                                className="text-emerald-400 hover:text-emerald-300 font-medium text-[11px] underline"
                              >
                                View Predictions
                              </Link>
                            </div>
                          ) : (
                            <PredictionAvailability
                              available={false}
                              jurisdiction="central"
                              firewallStatus="Outside production modelling scope"
                            />
                          )}
                        </div>

                        {/* Navigation Action */}
                        <div className="flex-shrink-0">
                          <Link href={`/bills/${b.bill_id}`}>
                            <Button variant="outline" size="xs">
                              View Dossier →
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </Card>
                  );
                })
              )}

              {/* 18. Server-Side Pagination */}
              {billsData.pages > 1 && (
                <div className="pt-4">
                  <Pagination
                    page={billsData.page}
                    pages={billsData.pages}
                    total={billsData.total}
                    limit={billsData.limit}
                    onPageChange={(p) => updateUrlParams({ page: p })}
                  />
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
