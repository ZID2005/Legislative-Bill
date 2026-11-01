/**
 * components/portfolio/PortfolioHeader.tsx
 * ========================================
 * Executive Portfolio Exposure Header Strip.
 *
 * Implements:
 * - Portfolio switcher dropdown for multi-tenant portfolios
 * - High-density tabular metric strip (replacing 6 bulky KPI cards)
 * - Restrained editorial-finance typography and hairline borders
 * - Global action buttons (+ Add Holding, Import CSV/JSON, Generate Report)
 * - Authoritative Decision-Support Governance disclaimer banner
 */

"use client";

import React from "react";
import type { PortfolioLegislativeExposureResponse, UserPortfolioItem } from "@/types/api";

export interface PortfolioHeaderProps {
  portfolios: UserPortfolioItem[];
  activePortfolio: UserPortfolioItem | null;
  onSelectPortfolio: (portfolio: UserPortfolioItem) => void;
  exposure: PortfolioLegislativeExposureResponse | null;
  onAddHolding: () => void;
  onImportHoldings: () => void;
  onGenerateReport: () => void;
  reportLoading: boolean;
  activeView: "workspace" | "report";
  onToggleView: (view: "workspace" | "report") => void;
  hasReportData: boolean;
}

export function PortfolioHeader({
  portfolios,
  activePortfolio,
  onSelectPortfolio,
  exposure,
  onAddHolding,
  onImportHoldings,
  onGenerateReport,
  reportLoading,
  activeView,
  onToggleView,
  hasReportData,
}: PortfolioHeaderProps) {
  return (
    <header className="space-y-4">
      {/* Top Bar: Title & Primary Actions */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-[var(--border-default)]">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-base" aria-hidden="true">💼</span>
            <span className="text-[10px] uppercase tracking-widest font-bold text-blue-500 dark:text-blue-400 font-mono">
              Decision Intelligence Workspace
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25">
              Task 1.8A Grounded
            </span>
            {portfolios.length > 1 && (
              <label className="inline-flex items-center gap-1.5 ml-2 text-xs text-[var(--text-muted)]">
                <span>Portfolio:</span>
                <select
                  value={activePortfolio?.portfolio_id || ""}
                  onChange={(e) => {
                    const found = portfolios.find((p) => p.portfolio_id === e.target.value);
                    if (found) onSelectPortfolio(found);
                  }}
                  className="bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] rounded-md px-2 py-0.5 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
                  aria-label="Select active portfolio"
                >
                  {portfolios.map((p) => (
                    <option key={p.portfolio_id} value={p.portfolio_id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)] font-headline">
            Portfolio Legislative Exposure Workspace
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 max-w-3xl">
            Evidence-backed legislative intelligence matching your holdings to Central acts, State legislation, and validated econometric horizons.
          </p>
        </div>

        {/* Global Action Toolbar */}
        <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
          <div className="inline-flex rounded-lg border border-[var(--border-default)] p-0.5 bg-[var(--bg-secondary)]">
            <button
              type="button"
              onClick={() => onToggleView("workspace")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeView === "workspace"
                  ? "bg-[var(--bg-card)] text-[var(--text-primary)] shadow-xs"
                  : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              Workspace
            </button>
            {hasReportData && (
              <button
                type="button"
                onClick={() => onToggleView("report")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  activeView === "report"
                    ? "bg-[var(--bg-card)] text-[var(--text-primary)] shadow-xs"
                    : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Impact Report
              </button>
            )}
          </div>

          <button
            type="button"
            onClick={onAddHolding}
            className="px-3 py-1.5 rounded-md bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] text-xs font-semibold border border-[var(--border-strong)] transition-colors flex items-center gap-1.5 shadow-xs"
          >
            <span aria-hidden="true">+</span> Add Holding
          </button>
          <button
            type="button"
            onClick={onImportHoldings}
            className="px-3 py-1.5 rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-semibold border border-[var(--border-default)] transition-colors flex items-center gap-1.5"
          >
            <span aria-hidden="true">📂</span> Import CSV / JSON
          </button>
          <button
            type="button"
            onClick={onGenerateReport}
            disabled={reportLoading}
            className="px-3.5 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <span aria-hidden="true">📄</span>
            <span>{reportLoading ? "Generating…" : "Generate Report"}</span>
          </button>
        </div>
      </div>

      {/* Decision-Support Governance Alert Banner */}
      <div className="p-3 sm:p-3.5 rounded-lg bg-[var(--color-info-bg)] border border-[var(--color-info-border)] flex items-start gap-2.5">
        <span className="text-sm text-[var(--color-info)] mt-0.5 select-none" aria-hidden="true">ℹ</span>
        <div className="text-xs text-[var(--text-secondary)] leading-relaxed">
          <strong className="text-[var(--text-primary)] font-semibold">Decision-Support Governance:</strong>{" "}
          This workspace correlates documented statutory enactments, company exposure networks, and verified Central event-study forecasts. It does{" "}
          <strong className="text-rose-600 dark:text-rose-400 font-semibold">NOT</strong> provide automated trading signals, Buy/Sell/Hold ratings, or target prices. Sub-national state legislation strictly carries{" "}
          <span className="font-mono font-semibold text-[var(--text-primary)]">0 stock market predictions</span> under immutable methodology invariants.
        </div>
      </div>

      {/* High-Density Tabular Exposure Strip */}
      {exposure && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3 py-2 border-y border-[var(--border-hairline)] bg-[var(--bg-surface)] px-3 rounded-lg">
          <div className="p-2 sm:p-2.5">
            <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold block">Tracked Holdings</span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-lg font-bold font-tabular text-[var(--text-primary)]">{exposure.total_holdings}</span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">companies</span>
            </div>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium font-tabular block mt-0.5">
              {exposure.exposed_holdings_count} Exposed
            </span>
          </div>

          <div className="p-2 sm:p-2.5 border-l border-[var(--border-hairline)]">
            <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-semibold block">Relevant Bills</span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-lg font-bold font-tabular text-blue-600 dark:text-blue-400">{exposure.total_relevant_bills}</span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">measures</span>
            </div>
            <span className="text-[10px] text-[var(--text-muted)] font-mono block mt-0.5">
              Matched by rules
            </span>
          </div>

          <div className="p-2 sm:p-2.5 border-l border-[var(--border-hairline)]">
            <span className="text-[10px] uppercase tracking-wider text-rose-600 dark:text-rose-400 font-semibold block">Direct Exposures</span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-lg font-bold font-tabular text-rose-600 dark:text-rose-400">{exposure.direct_bills_count}</span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">acts</span>
            </div>
            <span className="text-[10px] text-rose-600/80 dark:text-rose-400/80 font-mono block mt-0.5">
              Chartered links
            </span>
          </div>

          <div className="p-2 sm:p-2.5 border-l border-[var(--border-hairline)]">
            <span className="text-[10px] uppercase tracking-wider text-amber-600 dark:text-amber-400 font-semibold block">High Relevance</span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-lg font-bold font-tabular text-amber-600 dark:text-amber-400">{exposure.high_relevance_bills_count}</span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">shifts</span>
            </div>
            <span className="text-[10px] text-amber-600/80 dark:text-amber-400/80 font-mono block mt-0.5">
              Sector mandates
            </span>
          </div>

          <div className="p-2 sm:p-2.5 border-l border-[var(--border-hairline)]">
            <span className="text-[10px] uppercase tracking-wider text-emerald-600 dark:text-emerald-400 font-semibold block">Modelled Central</span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-lg font-bold font-tabular text-emerald-600 dark:text-emerald-400">{exposure.modelled_central_bills_count}</span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">forecasts</span>
            </div>
            <span className="text-[10px] text-emerald-600/80 dark:text-emerald-400/80 font-mono block mt-0.5">
              47 Quant universe
            </span>
          </div>

          <div className="p-2 sm:p-2.5 border-l border-[var(--border-hairline)]">
            <span className="text-[10px] uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-semibold block">State / Intelligence</span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-lg font-bold font-tabular text-cyan-600 dark:text-cyan-400">
                {exposure.state_bills_count + exposure.knowledge_only_bills_count}
              </span>
              <span className="text-[11px] text-[var(--text-muted)] font-mono">records</span>
            </div>
            <span className="text-[10px] text-[var(--text-muted)] font-mono block mt-0.5">
              0 Stock predictions
            </span>
          </div>
        </div>
      )}
    </header>
  );
}

export default PortfolioHeader;

