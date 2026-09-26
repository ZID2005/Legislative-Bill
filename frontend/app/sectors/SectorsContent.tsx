/**
 * app/sectors/SectorsContent.tsx
 * ===============================
 * Macro Economic Sector Directory for India Legislative Intelligence.
 * Displays macroeconomic sectors with aggregated legislative footprints,
 * corporate exposures, and navigation to underlying industries.
 */

"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { industriesApi } from "@/lib/api/industries";
import { CapabilityBadge } from "@/components/coverage/CapabilityBadge";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import type { IndustrySummaryItem } from "@/types/api";

interface SectorMeta {
  name: string;
  icon: string;
  description: string;
  aliases: string[];
}

const MACRO_SECTORS: SectorMeta[] = [
  {
    name: "Banking & Financial Services",
    icon: "🏦",
    description: "Scheduled commercial banks, NBFCs, payment systems, digital lenders, and insurance underwriters.",
    aliases: ["banking & financial services", "bfsi", "banking", "financial services", "finance"],
  },
  {
    name: "Technology & IT",
    icon: "💻",
    description: "IT services exporters, SaaS platforms, digital public infrastructure, and AI engineering.",
    aliases: ["technology", "it", "information technology", "technology & it"],
  },
  {
    name: "Healthcare & Pharmaceuticals",
    icon: "💊",
    description: "Formulation manufacturers, API exporters, hospitals, diagnostic chains, and medical technology.",
    aliases: ["healthcare & pharmaceuticals", "healthcare", "pharmaceuticals", "pharma"],
  },
  {
    name: "Energy & Power",
    icon: "⚡",
    description: "Renewable energy generators, transmission utilities, oil & gas refining, and green hydrogen initiatives.",
    aliases: ["energy", "power", "energy & power", "utilities"],
  },
  {
    name: "Infrastructure & Real Estate",
    icon: "🏗️",
    description: "Highways, ports, airports, commercial REITs, urban development, and construction contractors.",
    aliases: ["infrastructure", "real estate", "infrastructure & real estate", "construction"],
  },
  {
    name: "Consumer Goods & FMCG",
    icon: "🛒",
    description: "Fast-moving consumer goods, packaged foods, personal care, and retail distribution networks.",
    aliases: ["consumer goods & fmcg", "consumer goods", "fmcg", "retail"],
  },
  {
    name: "Consumer / Digital",
    icon: "📱",
    description: "Consumer internet platforms, quick commerce, gig delivery networks, and e-commerce ecosystems.",
    aliases: ["consumer / digital", "consumer digital", "digital platforms", "e-commerce"],
  },
  {
    name: "Manufacturing & Industrials",
    icon: "🏭",
    description: "Automotive OEMs, capital equipment, industrial machinery, specialty chemicals, and heavy engineering.",
    aliases: ["manufacturing", "manufacturing & industrials", "industrials", "automotive"],
  },
  {
    name: "Telecommunications",
    icon: "📡",
    description: "Mobile network operators, passive tower infrastructure, fiber networks, and satellite communications.",
    aliases: ["telecommunications", "telecom"],
  },
  {
    name: "Metals & Mining",
    icon: "⛏️",
    description: "Integrated steel producers, non-ferrous smelters, mineral extraction, and critical mineral processing.",
    aliases: ["metals & mining", "mining", "metals", "mining & metals"],
  },
  {
    name: "Logistics & Transportation",
    icon: "🚢",
    description: "Multimodal logistics providers, freight rail, container terminals, aviation, and warehousing.",
    aliases: ["logistics & transportation", "logistics", "transportation"],
  },
  {
    name: "Agriculture",
    icon: "🌾",
    description: "Agrochemicals, fertilizers, farm mechanization, commodity procurement, and rural agribusiness.",
    aliases: ["agriculture", "agribusiness", "farming"],
  },
];

export default function SectorsContent() {
  const [industries, setIndustries] = useState<IndustrySummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await industriesApi.listIndustries({ limit: 100 });
      setIndustries(res.items || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load sector data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Group industries into macro sectors
  const sectorData = useMemo(() => {
    const map = new Map<
      string,
      {
        meta: SectorMeta;
        industries: IndustrySummaryItem[];
        totalBills: number;
        centralBills: number;
        stateBills: number;
        totalCompanies: number;
        quantCompanies: number;
        intelCompanies: number;
      }
    >();

    // Initialize all predefined sectors
    for (const meta of MACRO_SECTORS) {
      map.set(meta.name, {
        meta,
        industries: [],
        totalBills: 0,
        centralBills: 0,
        stateBills: 0,
        totalCompanies: 0,
        quantCompanies: 0,
        intelCompanies: 0,
      });
    }

    // Assign industries to sectors
    for (const ind of industries) {
      const lowerSec = ind.sector.toLowerCase();
      let matchedMeta = MACRO_SECTORS.find((m) =>
        m.aliases.some((alias) => lowerSec.includes(alias) || alias.includes(lowerSec))
      );

      if (!matchedMeta) {
        // Fallback catch-all
        matchedMeta = {
          name: ind.sector,
          icon: "⬡",
          description: `Sector coverage for ${ind.sector} legislative and economic activities.`,
          aliases: [lowerSec],
        };
      }

      if (!map.has(matchedMeta.name)) {
        map.set(matchedMeta.name, {
          meta: matchedMeta,
          industries: [],
          totalBills: 0,
          centralBills: 0,
          stateBills: 0,
          totalCompanies: 0,
          quantCompanies: 0,
          intelCompanies: 0,
        });
      }

      const entry = map.get(matchedMeta.name)!;
      entry.industries.push(ind);
      entry.totalBills += ind.related_bills_count;
      entry.centralBills += ind.central_exposures_count;
      entry.stateBills += ind.state_exposures_count;
      entry.totalCompanies += ind.exposed_companies_count;
      entry.quantCompanies += ind.quantitative_companies_count;
      entry.intelCompanies += ind.intelligence_companies_count;
    }

    // Filter by search
    return Array.from(map.values()).filter((item) => {
      if (!search.trim()) return true;
      const q = search.trim().toLowerCase();
      return (
        item.meta.name.toLowerCase().includes(q) ||
        item.meta.description.toLowerCase().includes(q) ||
        item.industries.some((i) => i.name.toLowerCase().includes(q))
      );
    });
  }, [industries, search]);

  const aggregateMetrics = useMemo(() => {
    let sectorsCount = sectorData.length;
    let industriesCount = industries.length;
    let totalBills = 0;
    let totalExposures = 0;

    for (const ind of industries) {
      totalBills += ind.related_bills_count;
      totalExposures += ind.exposed_companies_count;
    }

    return { sectorsCount, industriesCount, totalBills, totalExposures };
  }, [sectorData, industries]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
      {/* Header Banner */}
      <div className="mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                MACRO TAXONOMY
              </span>
              <span className="text-xs font-mono text-slate-500">
                11 High-Impact Economic Domains
              </span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <span>Macro Sector Directory</span>
            </h1>
            <p className="text-slate-400 mt-2 max-w-3xl text-sm leading-relaxed">
              Explore India’s high-level economic sectors mapped against Central and State legislative
              interventions, corporate exposures, and quantified economic transmission paths.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/industries"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors flex items-center gap-2 shadow-lg shadow-indigo-500/10"
            >
              <span>View All Industries</span>
              <span>→</span>
            </Link>
          </div>
        </div>

        {/* Global Macro KPI Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Macro Sectors</p>
            <p className="text-2xl font-bold text-white mt-1">11</p>
            <p className="text-xs text-slate-500 mt-0.5">NIC-mapped clusters</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Underlying Industries</p>
            <p className="text-2xl font-bold text-indigo-400 mt-1">{aggregateMetrics.industriesCount}</p>
            <p className="text-xs text-slate-500 mt-0.5">Granular segments</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Active Bills Mapped</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{aggregateMetrics.totalBills}</p>
            <p className="text-xs text-slate-500 mt-0.5">Central & State enactments</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Corporate Links</p>
            <p className="text-2xl font-bold text-sky-400 mt-1">{aggregateMetrics.totalExposures}</p>
            <p className="text-xs text-slate-500 mt-0.5">Quant + Intelligence firms</p>
          </div>
        </div>

        {/* State Prediction Firewall Reminder */}
        <div className="mt-6">
          <StatePredictionFirewall />
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-8 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search sectors or industries..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <span className="absolute left-3 top-2.5 text-slate-500 text-sm">🔍</span>
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-3 top-2.5 text-xs text-slate-500 hover:text-slate-300"
            >
              ✕
            </button>
          )}
        </div>
        <span className="text-xs text-slate-500 font-mono">
          Showing {sectorData.length} Macro Sectors
        </span>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800">
          <div className="inline-block animate-spin text-2xl mb-2">⏳</div>
          <p className="text-sm">Synthesizing macro sector taxonomy and legislative linkages...</p>
        </div>
      )}

      {error && (
        <div className="p-6 bg-red-950/40 border border-red-800/60 rounded-xl text-red-300 text-sm mb-6">
          <p className="font-semibold mb-1">Failed to load sector directory</p>
          <p className="text-xs text-red-400">{error}</p>
          <button
            onClick={loadData}
            className="mt-3 px-3 py-1.5 bg-red-800 hover:bg-red-700 text-white rounded text-xs transition-colors"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Macro Sectors Grid */}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sectorData.map((item) => {
            const hasQuant = item.quantCompanies > 0;
            const sectorSlug = encodeURIComponent(item.meta.name);

            return (
              <div
                key={item.meta.name}
                className="bg-slate-900/70 border border-slate-800/90 hover:border-slate-700 rounded-xl p-5 flex flex-col justify-between transition-all duration-200 shadow-sm hover:shadow-indigo-950/20"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-xl">
                        {item.meta.icon}
                      </div>
                      <div>
                        <h2 className="text-lg font-bold text-white hover:text-indigo-400 transition-colors">
                          <Link href={`/industries?sector=${sectorSlug}`}>
                            {item.meta.name}
                          </Link>
                        </h2>
                        <span className="text-xs text-slate-500 font-mono">
                          {item.industries.length} {item.industries.length === 1 ? "Industry" : "Industries"}
                        </span>
                      </div>
                    </div>
                    <div>
                      {hasQuant ? (
                        <CapabilityBadge level={1} size="xs" />
                      ) : (
                        <CapabilityBadge level={2} size="xs" />
                      )}
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-400 leading-relaxed mb-4 line-clamp-2">
                    {item.meta.description}
                  </p>

                  {/* Metrics Row */}
                  <div className="grid grid-cols-3 gap-2 bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5 mb-4 text-center">
                    <div>
                      <span className="text-[10px] font-mono text-slate-500 block uppercase">Bills</span>
                      <span className="text-sm font-semibold text-slate-200">{item.totalBills}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-500 block uppercase">Central</span>
                      <span className="text-sm font-semibold text-emerald-400">{item.centralBills}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-500 block uppercase">State</span>
                      <span className="text-sm font-semibold text-amber-400">{item.stateBills}</span>
                    </div>
                  </div>

                  {/* Child Industries Pills */}
                  <div className="mb-4">
                    <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider block mb-1.5">
                      Sub-Industries:
                    </span>
                    <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
                      {item.industries.length > 0 ? (
                        item.industries.map((ind) => (
                          <Link
                            key={ind.industry_id}
                            href={`/industry/${ind.industry_id}`}
                            className="text-xs px-2 py-0.5 rounded bg-slate-800/80 hover:bg-indigo-900/40 hover:text-indigo-300 text-slate-300 border border-slate-700/50 transition-colors"
                          >
                            {ind.name}
                          </Link>
                        ))
                      ) : (
                        <span className="text-xs text-slate-600 italic">No discrete sub-industries mapped</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Footer Action */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between mt-auto">
                  <span className="text-xs text-slate-500">
                    {item.quantCompanies > 0 && (
                      <span className="text-indigo-400 font-mono text-[11px]">
                        {item.quantCompanies} Quant Stocks
                      </span>
                    )}
                    {item.quantCompanies > 0 && item.intelCompanies > 0 && (
                      <span className="mx-1.5 text-slate-700">•</span>
                    )}
                    {item.intelCompanies > 0 && (
                      <span className="text-slate-400 font-mono text-[11px]">
                        {item.intelCompanies} Intel Firms
                      </span>
                    )}
                  </span>
                  <Link
                    href={`/industries?sector=${sectorSlug}`}
                    className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
                  >
                    <span>Explore</span>
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
