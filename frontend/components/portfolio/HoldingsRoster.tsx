/**
 * components/portfolio/HoldingsRoster.tsx
 * =======================================
 * Searchable, compact institutional holdings roster (Left Column).
 *
 * Implements:
 * - Search filter across company name, ISIN, ticker, sector, industry
 * - Real-time inline exposure indicators (e.g. "4 bills [●]")
 * - Holding selection to focus the Legislative Impact Inspector
 * - Position information (shares, avg price in tabular numerals)
 * - Safe holding deletion with confirmation dialog
 * - High-contrast active row state and keyboard accessibility
 */

"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import type { PortfolioHoldingItem } from "@/types/api";
import { SearchInput } from "@/components/ui/SearchInput";

export interface HoldingsRosterProps {
  holdings: PortfolioHoldingItem[];
  selectedHolding: PortfolioHoldingItem | null;
  onSelectHolding: (holding: PortfolioHoldingItem | null) => void;
  onRemoveHolding: (holding: PortfolioHoldingItem) => void;
  onAddHolding: () => void;
  holdingsExposureMap?: Record<string, string[]>;
}

export function HoldingsRoster({
  holdings,
  selectedHolding,
  onSelectHolding,
  onRemoveHolding,
  onAddHolding,
  holdingsExposureMap = {},
}: HoldingsRosterProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredHoldings = useMemo(() => {
    if (!searchQuery.trim()) return holdings;
    const q = searchQuery.toLowerCase().trim();
    return holdings.filter(
      (h) =>
        h.company_name.toLowerCase().includes(q) ||
        (h.isin && h.isin.toLowerCase().includes(q)) ||
        (h.ticker && h.ticker.toLowerCase().includes(q)) ||
        (h.sector && h.sector.toLowerCase().includes(q)) ||
        (h.industry && h.industry.toLowerCase().includes(q))
    );
  }, [holdings, searchQuery]);

  return (
    <section
      className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl overflow-hidden flex flex-col h-full"
      aria-label="Tracked Holdings Roster"
    >
      {/* Roster Header */}
      <div className="p-3.5 border-b border-[var(--border-default)] bg-[var(--bg-base)] space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
              Tracked Holdings Roster
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-muted)] font-tabular">
              {holdings.length}
            </span>
          </div>
          <button
            type="button"
            onClick={onAddHolding}
            className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-500 flex items-center gap-1 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)] rounded"
          >
            <span aria-hidden="true">+</span> Add Company
          </button>
        </div>

        {/* Search Input */}
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          onClear={() => setSearchQuery("")}
          placeholder="Filter by company, ISIN, sector…"
          className="text-xs"
        />

        {/* Selected Holding Indicator & Clear Button */}
        {selectedHolding && (
          <div className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-blue-500/10 border border-blue-500/25 text-xs">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="text-[10px] uppercase font-bold text-blue-600 dark:text-blue-400">Filtering:</span>
              <span className="font-semibold text-[var(--text-primary)] truncate">{selectedHolding.company_name}</span>
            </div>
            <button
              type="button"
              onClick={() => onSelectHolding(null)}
              className="text-[10px] font-semibold text-blue-600 dark:text-blue-400 hover:underline ml-2 whitespace-nowrap focus-visible:outline-none"
            >
              Show All
            </button>
          </div>
        )}
      </div>

      {/* Holdings List / Table */}
      <div className="flex-1 overflow-y-auto max-h-[640px] divide-y divide-[var(--border-hairline)]">
        {filteredHoldings.length === 0 ? (
          <div className="p-6 text-center text-xs text-[var(--text-muted)] space-y-3" data-testid="empty-holdings-state">
            {searchQuery ? (
              <>
                <p className="font-medium text-[var(--text-secondary)]">No matching holdings found for &ldquo;{searchQuery}&rdquo;.</p>
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                >
                  Clear search filter
                </button>
              </>
            ) : (
              <div className="space-y-3 py-2">
                <div className="w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-500 flex items-center justify-center mx-auto text-lg" aria-hidden="true">
                  💼
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-[var(--text-primary)]">
                    No Holdings in This Portfolio
                  </h4>
                  <p className="text-[11px] text-[var(--text-muted)] max-w-xs mx-auto mt-1 leading-relaxed">
                    Portfolio exposure analyzes your equity holdings against active Central Acts and State gazettes to identify regulatory risk, anticipation horizons, and sector sensitivities.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={onAddHolding}
                    data-testid="add-first-holding-btn"
                    className="w-full sm:w-auto px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors shadow-xs"
                  >
                    + Add First Holding
                  </button>
                  <Link
                    href="/companies"
                    className="w-full sm:w-auto px-3.5 py-1.5 rounded-lg bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-default)] text-xs font-semibold transition-colors"
                  >
                    Browse Companies →
                  </Link>
                </div>
              </div>
            )}
          </div>
        ) : (
          filteredHoldings.map((h) => {
            const isSelected = selectedHolding?.holding_id === h.holding_id;
            const exposedBills = holdingsExposureMap[h.company_name] || [];
            const exposedCount = exposedBills.length;

            return (
              <div
                key={h.holding_id}
                role="button"
                tabIndex={0}
                onClick={() => onSelectHolding(isSelected ? null : h)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelectHolding(isSelected ? null : h);
                  }
                }}
                className={`p-3 text-left transition-colors flex items-start justify-between gap-3 cursor-pointer group focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)] ${
                  isSelected
                    ? "bg-[var(--bg-secondary)] border-l-2 border-l-blue-500 dark:border-l-blue-400 pl-2.5"
                    : "hover:bg-[var(--bg-card-hover)]"
                }`}
                aria-pressed={isSelected}
                aria-label={`Select ${h.company_name}`}
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {h.company_name}
                    </span>
                    {(h.isin || h.ticker) && (
                      <span className="text-[10px] font-mono text-[var(--text-muted)] font-tabular">
                        {h.ticker || h.isin}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)] flex-wrap">
                    {h.sector && <span>{h.sector}</span>}
                    {h.sector && h.industry && <span>•</span>}
                    {h.industry && <span className="text-[var(--text-secondary)]">{h.industry}</span>}
                  </div>

                  {h.quantity != null && (
                    <div className="text-[10px] font-tabular text-[var(--text-muted)]">
                      <span>{h.quantity.toLocaleString()} shares</span>
                      {h.avg_purchase_price != null && (
                        <span> @ ₹{h.avg_purchase_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Right side: Exposure Badge & Delete */}
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  <span
                    className={`px-2 py-0.5 rounded-sm text-[10px] font-mono font-bold font-tabular border ${
                      exposedCount > 0
                        ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25"
                        : "bg-[var(--bg-secondary)] text-[var(--text-muted)] border-[var(--border-hairline)]"
                    }`}
                    title={exposedCount > 0 ? `${exposedCount} bills correlate to this holding` : "No statutory exposures found"}
                  >
                    {exposedCount} {exposedCount === 1 ? "bill" : "bills"}
                  </span>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveHolding(h);
                    }}
                    className="text-[10px] text-[var(--text-muted)] hover:text-rose-600 dark:hover:text-rose-400 opacity-60 hover:opacity-100 transition-opacity focus-visible:outline-none"
                    aria-label={`Remove ${h.company_name} from portfolio`}
                  >
                    Remove
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

export default HoldingsRoster;
