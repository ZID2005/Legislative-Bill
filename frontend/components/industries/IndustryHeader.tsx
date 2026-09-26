"use client";

import React, { useState } from "react";
import Link from "next/link";
import { CapabilityBadge, type CapabilityLevel } from "@/components/coverage/CapabilityBadge";
import { Badge } from "@/components/ui/Badge";
import type { IndustryDossierResponse } from "@/types/api";
import { IndustryWatchlistModal } from "@/components/industries/IndustryWatchlistModal";

export interface IndustryHeaderProps {
  dossier: IndustryDossierResponse;
}

export function IndustryHeader({ dossier }: IndustryHeaderProps) {
  const [showWatchlistModal, setShowWatchlistModal] = useState(false);
  return (
    <header className="rounded-xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl backdrop-blur-sm">
      {/* Breadcrumb & Navigation */}
      <nav aria-label="Breadcrumb" className="mb-4 flex items-center gap-2 text-xs text-slate-400">
        <Link href="/industries" className="hover:text-slate-200 transition-colors">
          Industry Intelligence
        </Link>
        <span>/</span>
        <Link href={`/industries?sector=${encodeURIComponent(dossier.sector)}`} className="hover:text-slate-200 transition-colors">
          {dossier.sector}
        </Link>
        <span>/</span>
        <span className="text-slate-200 font-medium">{dossier.name}</span>
      </nav>

      {/* Main Title Row */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2.5 mb-2">
            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {dossier.name}
            </h1>
            <Badge variant="primary" size="sm">
              {dossier.sector}
            </Badge>
            <CapabilityBadge level={dossier.coverage_level as CapabilityLevel} size="sm" showTooltip />
            {dossier.market_analysis_available ? (
              <span className="inline-flex items-center gap-1 rounded bg-emerald-950/40 border border-emerald-700/50 px-2 py-0.5 text-xs text-emerald-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
                Market Analytics Available
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded bg-slate-800 border border-slate-700 px-2 py-0.5 text-xs text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-500" aria-hidden="true" />
                Corporate Intelligence Only
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 max-w-3xl leading-relaxed">
            {dossier.description}
          </p>
        </div>

        {/* Action Links */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => setShowWatchlistModal(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-semibold text-amber-300 hover:bg-amber-500/20 transition-colors shadow-sm"
          >
            <span>⭐</span>
            <span>Add to Watchlist</span>
          </button>
          <Link
            href={`/explorer?sector=${encodeURIComponent(dossier.sector)}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-800 hover:border-slate-600 transition-colors"
          >
            <span>Explore Bills in Explorer</span>
            <span>→</span>
          </Link>
        </div>
      </div>

      {/* Watchlist Modal */}
      <IndustryWatchlistModal
        isOpen={showWatchlistModal}
        onClose={() => setShowWatchlistModal(false)}
        industry={{
          industry_id: dossier.industry_id,
          name: dossier.name,
          sector: dossier.sector,
        }}
      />

      {/* KPI Stats Grid */}
      <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-5 border-t border-slate-800/80">
        <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Related Bills</span>
          <p className="mt-1 text-xl font-bold text-white">{dossier.total_bills_count}</p>
          <span className="text-[10px] text-slate-500">
            {dossier.central_bills_count} Central · {dossier.state_bills_count} State
          </span>
        </div>

        <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Tracked Companies</span>
          <p className="mt-1 text-xl font-bold text-white">{dossier.total_companies_count}</p>
          <span className="text-[10px] text-slate-500">
            {dossier.quantitative_companies_count} Quant · {dossier.intelligence_companies_count} Intel
          </span>
        </div>

        <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Central Exposures</span>
          <p className="mt-1 text-xl font-bold text-amber-300">{dossier.central_exposures_count}</p>
          <span className="text-[10px] text-slate-500">Parliamentary statutes</span>
        </div>

        <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">State Exposures</span>
          <p className="mt-1 text-xl font-bold text-blue-300">{dossier.state_exposures_count}</p>
          <span className="text-[10px] text-slate-500">Assembly legislation</span>
        </div>

        <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Active Mechanisms</span>
          <p className="mt-1 text-xl font-bold text-slate-200">{dossier.active_mechanisms.length}</p>
          <span className="text-[10px] text-slate-500 capitalize">{dossier.dominant_mechanism}</span>
        </div>

        <div className="rounded-lg bg-slate-800/50 border border-slate-800 p-3">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Coverage Level</span>
          <p className="mt-1 text-xl font-bold text-emerald-400">Level {dossier.coverage_level}</p>
          <span className="text-[10px] text-slate-500">
            {dossier.coverage_level === 1 ? "Quantitative Market" : "Corporate Intelligence"}
          </span>
        </div>
      </div>
    </header>
  );
}

export default IndustryHeader;
