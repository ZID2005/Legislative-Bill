/**
 * app/industries/IndustriesContent.tsx
 * ====================================
 * Interactive Industry Intelligence Discovery Dashboard.
 * Connects Indian legislation with affected sectors, companies, economic mechanisms, and available market analytics.
 */

"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { industriesApi } from "@/lib/api/industries";
import { CapabilityBadge, type CapabilityLevel } from "@/components/coverage/CapabilityBadge";
import { Badge } from "@/components/ui/Badge";
import type { IndustrySummaryItem } from "@/types/api";

const ALL_SECTORS = [
  "All Sectors",
  "Banking & Financial Services",
  "Consumer / Digital",
  "Consumer Goods & FMCG",
  "Energy",
  "Healthcare & Pharmaceuticals",
  "Infrastructure",
  "Logistics & Transportation",
  "Manufacturing",
  "Metals & Mining",
  "Technology",
  "Telecommunications",
];

export default function IndustriesContent() {
  const [industries, setIndustries] = useState<IndustrySummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedSector, setSelectedSector] = useState("All Sectors");
  const [jurisdiction, setJurisdiction] = useState<"ALL" | "CENTRAL" | "STATE">("ALL");
  const [universeFilter, setUniverseFilter] = useState<"ALL" | "QUANTITATIVE" | "INTELLIGENCE">("ALL");
  const [sortBy, setSortBy] = useState<"bills_desc" | "companies_desc" | "name_asc" | "level_asc">("bills_desc");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await industriesApi.listIndustries({
        limit: 100,
        sort_by: sortBy,
      });
      setIndustries(res.items || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load industry intelligence data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [sortBy]);

  // Client-side filtering across fields for instant interactive search
  const filteredIndustries = useMemo(() => {
    return industries.filter((ind) => {
      // Sector filter
      if (selectedSector !== "All Sectors" && ind.sector.toLowerCase() !== selectedSector.toLowerCase()) {
        return false;
      }

      // Jurisdiction filter
      if (jurisdiction === "CENTRAL" && ind.central_exposures_count === 0 && ind.quantitative_companies_count === 0) {
        return false;
      }
      if (jurisdiction === "STATE" && ind.state_exposures_count === 0) {
        return false;
      }

      // Universe filter
      if (universeFilter === "QUANTITATIVE" && ind.quantitative_companies_count === 0) {
        return false;
      }
      if (universeFilter === "INTELLIGENCE" && ind.intelligence_companies_count === 0) {
        return false;
      }

      // Search query
      if (search.trim()) {
        const q = search.trim().toLowerCase();
        const nameMatch = ind.name.toLowerCase().includes(q);
        const sectorMatch = ind.sector.toLowerCase().includes(q);
        const mechMatch = ind.economic_mechanisms.some((m) => m.toLowerCase().includes(q));
        const subMatch = ind.sub_industries.some((s) => s.toLowerCase().includes(q));
        if (!nameMatch && !sectorMatch && !mechMatch && !subMatch) {
          return false;
        }
      }

      return true;
    });
  }, [industries, selectedSector, jurisdiction, universeFilter, search]);

  // Dynamic KPI aggregation from actual loaded items
  const stats = useMemo(() => {
    const totalInds = industries.length;
    const quantInds = industries.filter((i) => i.coverage_level === 1).length;
    const intelInds = industries.filter((i) => i.coverage_level === 2).length;
    const totalBills = industries.reduce((acc, i) => acc + i.related_bills_count, 0);
    const totalComps = industries.reduce((acc, i) => acc + i.exposed_companies_count, 0);

    return { totalInds, quantInds, intelInds, totalBills, totalComps };
  }, [industries]);

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <header className="rounded-xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xl">🏭</span>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                Industry Intelligence
              </h1>
              <Badge variant="primary" size="xs">Platform Discovery</Badge>
            </div>
            <p className="text-sm text-slate-400 max-w-3xl leading-relaxed">
              Connect Indian Parliamentary and State legislation with affected economic sectors, corporations,
              transmission mechanisms, and available econometric market analytics.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <Link
              href="/sectors"
              className="rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-800 hover:border-slate-600 transition-colors"
            >
              Macro Sector Directory →
            </Link>
          </div>
        </div>

        {/* Dynamic Baseline KPI Banner */}
        <div className="mt-6 grid grid-cols-2 sm:grid-cols-5 gap-3 pt-5 border-t border-slate-800/80">
          <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Total Industries</span>
            <p className="mt-1 text-xl font-bold text-white">{stats.totalInds}</p>
            <span className="text-[10px] text-slate-500">Across 11 broad sectors</span>
          </div>

          <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Level 1 Modelled</span>
            <p className="mt-1 text-xl font-bold text-emerald-400">{stats.quantInds}</p>
            <span className="text-[10px] text-slate-500">Quantitative securities active</span>
          </div>

          <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Level 2 Intelligence</span>
            <p className="mt-1 text-xl font-bold text-blue-400">{stats.intelInds}</p>
            <span className="text-[10px] text-slate-500">Qualitative / State exposures</span>
          </div>

          <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Corporate Entities</span>
            <p className="mt-1 text-xl font-bold text-slate-200">{stats.totalComps}</p>
            <span className="text-[10px] text-slate-500">Listed, unlisted & utilities</span>
          </div>

          <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">State Stock Predictions</span>
            <p className="mt-1 text-xl font-bold text-slate-400">0</p>
            <span className="text-[10px] text-slate-500">Statutory firewall invariant</span>
          </div>
        </div>
      </header>

      {/* Filter Toolbar */}
      <section aria-label="Filters and Search" className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search Box */}
          <div>
            <label htmlFor="search-input" className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">
              Search Industry / Mechanism
            </label>
            <input
              id="search-input"
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search e.g. Automobiles, compliance, power..."
              className="w-full rounded-lg border border-slate-700 bg-slate-800/90 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Sector Dropdown */}
          <div>
            <label htmlFor="sector-select" className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">
              Sector Classification
            </label>
            <select
              id="sector-select"
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800/90 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
            >
              {ALL_SECTORS.map((sec) => (
                <option key={sec} value={sec}>
                  {sec}
                </option>
              ))}
            </select>
          </div>

          {/* Jurisdiction Toggle */}
          <div>
            <span className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">
              Jurisdiction Scope
            </span>
            <div className="grid grid-cols-3 gap-1 rounded-lg border border-slate-700 bg-slate-800/90 p-1 text-xs">
              {(["ALL", "CENTRAL", "STATE"] as const).map((j) => (
                <button
                  key={j}
                  type="button"
                  onClick={() => setJurisdiction(j)}
                  className={`rounded py-1 font-medium transition-colors text-center ${
                    jurisdiction === j
                      ? j === "CENTRAL"
                        ? "bg-amber-950/70 text-amber-300 border border-amber-700/50"
                        : j === "STATE"
                        ? "bg-blue-950/70 text-blue-300 border border-blue-700/50"
                        : "bg-slate-700 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {j === "ALL" ? "All" : j === "CENTRAL" ? "Central" : "State"}
                </button>
              ))}
            </div>
          </div>

          {/* Universe Filter */}
          <div>
            <span className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">
              Universe Type
            </span>
            <div className="grid grid-cols-3 gap-1 rounded-lg border border-slate-700 bg-slate-800/90 p-1 text-xs">
              {(["ALL", "QUANTITATIVE", "INTELLIGENCE"] as const).map((u) => (
                <button
                  key={u}
                  type="button"
                  onClick={() => setUniverseFilter(u)}
                  className={`rounded py-1 font-medium transition-colors text-center text-[11px] ${
                    universeFilter === u
                      ? u === "QUANTITATIVE"
                        ? "bg-emerald-950/70 text-emerald-300 border border-emerald-700/50"
                        : u === "INTELLIGENCE"
                        ? "bg-blue-950/70 text-blue-300 border border-blue-700/50"
                        : "bg-slate-700 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {u === "ALL" ? "All" : u === "QUANTITATIVE" ? "Quant" : "Intel"}
                </button>
              ))}
            </div>
          </div>

          {/* Sort By */}
          <div>
            <label htmlFor="sort-select" className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1">
              Sort Order
            </label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800/90 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="bills_desc">Most Related Bills</option>
              <option value="companies_desc">Most Exposed Companies</option>
              <option value="name_asc">Alphabetical (A-Z)</option>
              <option value="level_asc">Coverage Level (L1 first)</option>
            </select>
          </div>
        </div>

        {/* State Jurisdiction Statutory Notice */}
        {jurisdiction === "STATE" && (
          <div className="rounded-lg border border-blue-900/50 bg-blue-950/20 p-3.5 text-xs text-blue-200 flex items-start gap-2.5">
            <span className="text-base mt-0.5">🗺</span>
            <div>
              <p className="font-semibold text-blue-300">
                Statutory Distinction: Legislative & Economic Intelligence vs. Stock-Market Prediction
              </p>
              <p className="mt-0.5 text-slate-400 leading-relaxed">
                State assembly acts provide qualitative legislative intelligence and verified corporate operational exposures only.
                Under the platform's research integrity firewall, <span className="text-slate-200 font-medium">State stock predictions remain strictly 0</span>.
                State economic impact does not produce automated equity forecasts.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((idx) => (
            <div key={idx} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 animate-pulse">
              <div className="h-5 w-2/3 bg-slate-800 rounded" />
              <div className="h-4 w-1/3 bg-slate-800 rounded" />
              <div className="h-16 bg-slate-800/50 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Error State with Retry */}
      {!loading && error && (
        <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-8 text-center space-y-3">
          <p className="text-rose-300 font-semibold text-sm">{error}</p>
          <button
            type="button"
            onClick={loadData}
            className="rounded-lg bg-rose-900/60 border border-rose-700/50 px-4 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-800 transition-colors"
          >
            Retry Loading
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredIndustries.length === 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center space-y-3">
          <span className="text-3xl block">🔍</span>
          <h3 className="text-base font-semibold text-white">No Matching Industries Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            No industries matched your search and filter criteria. Try resetting filters or searching a broader term.
          </p>
          <button
            type="button"
            onClick={() => {
              setSearch("");
              setSelectedSector("All Sectors");
              setJurisdiction("ALL");
              setUniverseFilter("ALL");
            }}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-1.5 text-xs text-slate-300 hover:text-white transition-colors"
          >
            Reset Filters
          </button>
        </div>
      )}

      {/* Industry Cards Grid */}
      {!loading && !error && filteredIndustries.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredIndustries.map((ind) => {
            return (
              <div
                key={ind.industry_id}
                className="group rounded-xl border border-slate-800 bg-slate-900/70 hover:bg-slate-900 hover:border-slate-700 p-5 transition-all duration-200 flex flex-col justify-between shadow-sm"
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <span className="rounded bg-slate-800 border border-slate-700 px-2 py-0.5 text-[10px] font-medium text-slate-300">
                      {ind.sector}
                    </span>
                    <CapabilityBadge level={ind.coverage_level as CapabilityLevel} size="xs" />
                  </div>

                  {/* Industry Title */}
                  <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition-colors">
                    <Link href={`/industry/${encodeURIComponent(ind.industry_id)}`}>
                      {ind.name}
                    </Link>
                  </h3>

                  {/* Quantitative Status Pill */}
                  <div className="mt-2">
                    {ind.market_analysis_available ? (
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        Market Analysis Active ({ind.quantitative_companies_count} quant)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                        Corporate Intelligence ({ind.intelligence_companies_count} entities)
                      </span>
                    )}
                  </div>

                  {/* Stat Chips */}
                  <div className="mt-4 grid grid-cols-3 gap-2 text-center py-2.5 px-3 rounded-lg bg-slate-800/40 border border-slate-800">
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Bills</span>
                      <span className="text-sm font-bold text-white">{ind.related_bills_count}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Companies</span>
                      <span className="text-sm font-bold text-white">{ind.exposed_companies_count}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Exposures</span>
                      <span className="text-sm font-bold text-amber-300">
                        {ind.central_exposures_count + ind.state_exposures_count}
                      </span>
                    </div>
                  </div>

                  {/* Mechanisms Tags */}
                  {ind.economic_mechanisms.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {ind.economic_mechanisms.slice(0, 3).map((m) => (
                        <span
                          key={m}
                          className="rounded bg-slate-800/90 border border-slate-700/60 px-1.5 py-0.5 text-[10px] text-slate-400 capitalize"
                        >
                          {m.replace("_", " ")}
                        </span>
                      ))}
                      {ind.economic_mechanisms.length > 3 && (
                        <span className="text-[10px] text-slate-500 self-center">
                          +{ind.economic_mechanisms.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer Action */}
                <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-500">
                    {ind.central_exposures_count} Central · {ind.state_exposures_count} State
                  </span>
                  <Link
                    href={`/industry/${encodeURIComponent(ind.industry_id)}`}
                    className="font-medium text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                  >
                    <span>Dossier</span>
                    <span>→</span>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
