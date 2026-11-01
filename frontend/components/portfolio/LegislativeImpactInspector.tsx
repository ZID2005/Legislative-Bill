/**
 * components/portfolio/LegislativeImpactInspector.tsx
 * ===================================================
 * Contextual Legislative-Impact Inspector (Right Column).
 *
 * Implements:
 * - Grouped bill exposures by supported relevance categories:
 *     1. Direct Statutory Exposures (DIRECT)
 *     2. High Relevance Regulatory Shifts (HIGH RELEVANCE)
 *     3. Moderate & Indirect Exposures (MODERATE RELEVANCE, INDIRECT, INFORMATIONAL)
 * - Progressive disclosure: concise summary with expandable evidence & model forecasts
 * - Authoritative Central model predictions with tabular figures across event windows
 * - Sub-national state legislation firewall indicator (0 stock predictions)
 * - Contextual drill-downs to Bill Dossier, Company Profile, Predictions, and Watchlists
 * - Grounded AI "Explain Relevance" action
 */

"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import type { PersonalizedBillImpactItem, PortfolioHoldingItem } from "@/types/api";

const TIER_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  DIRECT: {
    bg: "bg-rose-500/10",
    text: "text-rose-600 dark:text-rose-400",
    border: "border-rose-500/25",
  },
  "HIGH RELEVANCE": {
    bg: "bg-amber-500/10",
    text: "text-amber-600 dark:text-amber-400",
    border: "border-amber-500/25",
  },
  "MODERATE RELEVANCE": {
    bg: "bg-blue-500/10",
    text: "text-blue-600 dark:text-blue-400",
    border: "border-blue-500/25",
  },
  INDIRECT: {
    bg: "bg-purple-500/10",
    text: "text-purple-600 dark:text-purple-400",
    border: "border-purple-500/25",
  },
  INFORMATIONAL: {
    bg: "bg-[var(--bg-secondary)]",
    text: "text-[var(--text-muted)]",
    border: "border-[var(--border-default)]",
  },
};

const MODEL_STATUS_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  MODELLED: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-500/25",
  },
  "KNOWLEDGE ONLY": {
    bg: "bg-cyan-500/10",
    text: "text-cyan-700 dark:text-cyan-400",
    border: "border-cyan-500/25",
  },
  "NOT ELIGIBLE": {
    bg: "bg-[var(--bg-secondary)]",
    text: "text-[var(--text-muted)]",
    border: "border-[var(--border-hairline)]",
  },
  "PENDING REVIEW": {
    bg: "bg-amber-500/10",
    text: "text-amber-600 dark:text-amber-400",
    border: "border-amber-500/25",
  },
};

export interface LegislativeImpactInspectorProps {
  bills: PersonalizedBillImpactItem[];
  selectedHolding: PortfolioHoldingItem | null;
  onClearSelectedHolding: () => void;
  onExplainRelevance: (billId: string) => void;
  loading?: boolean;
}

export function LegislativeImpactInspector({
  bills,
  selectedHolding,
  onClearSelectedHolding,
  onExplainRelevance,
  loading = false,
}: LegislativeImpactInspectorProps) {
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [jurisdictionFilter, setJurisdictionFilter] = useState<string>("ALL");
  const [expandedBillIds, setExpandedBillIds] = useState<Record<string, boolean>>({});

  const toggleExpand = (billId: string) => {
    setExpandedBillIds((prev) => ({
      ...prev,
      [billId]: !prev[billId],
    }));
  };

  // Filter bills
  const filteredBills = useMemo(() => {
    return bills.filter((b) => {
      // Holding filter
      if (selectedHolding) {
        const matchesHolding = b.affected_companies.some(
          (c) => c.toLowerCase() === selectedHolding.company_name.toLowerCase()
        );
        if (!matchesHolding) return false;
      }

      // Tier filter
      if (tierFilter !== "ALL" && b.relevance_tier !== tierFilter) return false;

      // Jurisdiction filter
      if (jurisdictionFilter === "CENTRAL" && b.jurisdiction !== "central") return false;
      if (jurisdictionFilter === "STATE" && b.jurisdiction !== "state") return false;

      return true;
    });
  }, [bills, selectedHolding, tierFilter, jurisdictionFilter]);

  // Grouped by documented categories
  const groupedSections = useMemo(() => {
    const direct = filteredBills.filter((b) => b.relevance_tier === "DIRECT");
    const high = filteredBills.filter((b) => b.relevance_tier === "HIGH RELEVANCE");
    const moderateAndOthers = filteredBills.filter(
      (b) => b.relevance_tier !== "DIRECT" && b.relevance_tier !== "HIGH RELEVANCE"
    );

    return [
      {
        id: "direct",
        title: "Direct Statutory Exposures",
        badge: `${direct.length} Acts`,
        badgeColor: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/25",
        description: "Enactments directly naming your holdings or governing chartered core operations.",
        bills: direct,
      },
      {
        id: "high",
        title: "High Relevance Regulatory Shifts",
        badge: `${high.length} Measures`,
        badgeColor: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25",
        description: "Sector-level legislation and compliance mandates with direct economic transmission.",
        bills: high,
      },
      {
        id: "moderate",
        title: "Moderate & Indirect Exposures",
        badge: `${moderateAndOthers.length} Measures`,
        badgeColor: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/25",
        description: "Downstream supply-chain, tax, or cross-sectoral regulatory adjustments.",
        bills: moderateAndOthers,
      },
    ];
  }, [filteredBills]);

  return (
    <section
      className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl overflow-hidden flex flex-col h-full"
      aria-label="Legislative Impact Inspector"
    >
      {/* Inspector Header */}
      <div className="p-3.5 border-b border-[var(--border-default)] bg-[var(--bg-base)] space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
                Legislative Impact Inspector
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-muted)] font-tabular">
                {filteredBills.length} {filteredBills.length === 1 ? "Measure" : "Measures"}
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
              {selectedHolding ? (
                <span>
                  Contextual exposure for:{" "}
                  <strong className="text-[var(--text-primary)]">{selectedHolding.company_name}</strong>{" "}
                  <button
                    type="button"
                    onClick={onClearSelectedHolding}
                    className="text-blue-600 dark:text-blue-400 hover:underline ml-1 font-semibold"
                  >
                    (Show all holdings)
                  </button>
                </span>
              ) : (
                "Correlating portfolio holdings across active Central and State legislative frameworks."
              )}
            </p>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[var(--border-hairline)] text-xs">
          {/* Tier Filters */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)]">Relevance:</span>
            {["ALL", "DIRECT", "HIGH RELEVANCE", "MODERATE RELEVANCE", "INDIRECT"].map((tier) => (
              <button
                key={tier}
                type="button"
                onClick={() => setTierFilter(tier)}
                className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                  tierFilter === tier
                    ? "bg-blue-600 text-white"
                    : "bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border-hairline)]"
                }`}
              >
                {tier === "HIGH RELEVANCE" ? "HIGH" : tier === "MODERATE RELEVANCE" ? "MODERATE" : tier}
              </button>
            ))}
          </div>

          {/* Jurisdiction Filters */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)]">Jurisdiction:</span>
            {["ALL", "CENTRAL", "STATE"].map((jx) => (
              <button
                key={jx}
                type="button"
                onClick={() => setJurisdictionFilter(jx)}
                className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                  jurisdictionFilter === jx
                    ? "bg-blue-600 text-white"
                    : "bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border-hairline)]"
                }`}
              >
                {jx}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Inspector Body */}
      <div className="flex-1 overflow-y-auto max-h-[640px] p-3 sm:p-4 space-y-6">
        {loading ? (
          <div className="p-8 text-center text-xs text-[var(--text-muted)] font-mono">
            Loading correlated legislative impacts…
          </div>
        ) : filteredBills.length === 0 ? (
          <div className="p-10 text-center text-xs text-[var(--text-muted)] space-y-3 bg-[var(--bg-base)]/50 rounded-xl border border-[var(--border-hairline)]">
            <p className="font-semibold text-sm text-[var(--text-primary)]">No Legislative Impacts Found</p>
            <p className="max-w-md mx-auto text-[var(--text-secondary)]">
              {selectedHolding
                ? `No legislative measures matched ${selectedHolding.company_name} with current tier and jurisdiction filters.`
                : "No legislative measures match your current filter selections."}
            </p>
            <button
              type="button"
              onClick={() => {
                setTierFilter("ALL");
                setJurisdictionFilter("ALL");
                onClearSelectedHolding();
              }}
              className="px-3 py-1.5 rounded-md bg-[var(--bg-surface)] border border-[var(--border-default)] text-xs font-semibold text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
            >
              Reset All Filters
            </button>
          </div>
        ) : (
          groupedSections.map((sec) => {
            if (sec.bills.length === 0) return null;

            return (
              <div key={sec.id} className="space-y-3">
                {/* Section Header */}
                <div className="flex items-center justify-between pb-1.5 border-b border-[var(--border-hairline)]">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
                        {sec.title}
                      </h3>
                      <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-bold border ${sec.badgeColor}`}>
                        {sec.badge}
                      </span>
                    </div>
                    <p className="text-[10px] text-[var(--text-muted)] mt-0.5">{sec.description}</p>
                  </div>
                </div>

                {/* Bill Cards in Section */}
                <div className="space-y-3">
                  {sec.bills.map((b) => {
                    const isExpanded = expandedBillIds[b.bill_id] ?? true; // Default expanded for analytical clarity
                    const tierStyle = TIER_STYLES[b.relevance_tier] || TIER_STYLES.INFORMATIONAL;
                    const modelStyle = MODEL_STATUS_STYLES[b.model_status] || MODEL_STATUS_STYLES["KNOWLEDGE ONLY"];
                    const isCentral = b.jurisdiction === "central";

                    return (
                      <article
                        key={b.bill_id}
                        className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] hover:border-[var(--border-strong)] transition-all overflow-hidden"
                      >
                        {/* Bill Card Header */}
                        <div className="p-3 sm:p-3.5 space-y-2">
                          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <Link
                                  href={`/bills/${encodeURIComponent(b.bill_id)}`}
                                  className="text-xs sm:text-sm font-bold text-[var(--text-primary)] hover:text-blue-600 dark:hover:text-blue-400 transition-colors leading-tight"
                                >
                                  {b.bill_title}
                                </Link>
                                {b.bill_number && (
                                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] border border-[var(--border-hairline)] text-[var(--text-muted)] font-tabular">
                                    {b.bill_number}
                                  </span>
                                )}
                              </div>

                              <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)] flex-wrap">
                                <span className="font-semibold text-[var(--text-secondary)]">
                                  {isCentral ? "Central Parliament" : `${b.state} Assembly`}
                                </span>
                                <span>•</span>
                                <span>
                                  Status:{" "}
                                  <strong className="text-[var(--text-primary)] capitalize">{b.status}</strong>
                                </span>
                                {b.latest_verified_update && (
                                  <>
                                    <span>•</span>
                                    <span>
                                      Updated:{" "}
                                      <strong className="text-[var(--text-secondary)]">
                                        {b.latest_verified_update}
                                      </strong>
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>

                            {/* Badges */}
                            <div className="flex items-center gap-1.5 flex-shrink-0 flex-wrap">
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded-sm border ${tierStyle.bg} ${tierStyle.text} ${tierStyle.border}`}
                              >
                                {b.relevance_tier}
                              </span>
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded-sm border ${modelStyle.bg} ${modelStyle.text} ${modelStyle.border}`}
                              >
                                {b.model_status}
                              </span>
                              <button
                                type="button"
                                onClick={() => toggleExpand(b.bill_id)}
                                className="text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] px-1 py-0.5 rounded"
                                aria-label={isExpanded ? "Collapse details" : "Expand details"}
                              >
                                {isExpanded ? "▲" : "▼"}
                              </button>
                            </div>
                          </div>

                          {/* Primary Linkage Reason */}
                          <div className="p-2.5 rounded-md bg-[var(--bg-base)] border border-[var(--border-hairline)] space-y-1">
                            <div className="flex items-start gap-1.5 text-xs text-[var(--text-primary)] leading-relaxed">
                              <span className="text-amber-500 font-bold mt-0.5" aria-hidden="true">
                                ✦
                              </span>
                              <div>
                                <strong className="text-amber-600 dark:text-amber-400 font-semibold mr-1">
                                  Linkage Reason:
                                </strong>
                                <span className="text-[var(--text-secondary)]">{b.primary_linkage_reason}</span>
                              </div>
                            </div>

                            {/* Affected Holdings & Sectors inline */}
                            <div className="flex items-center gap-3 text-[10px] text-[var(--text-muted)] pt-1 flex-wrap">
                              {b.affected_companies.length > 0 && (
                                <span className="inline-flex items-center gap-1 flex-wrap">
                                  <span>Exposed Holding:</span>
                                  {b.affected_companies.map((comp, idx) => (
                                    <Link
                                      key={comp}
                                      href={`/companies/${encodeURIComponent(comp)}`}
                                      className="font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                                    >
                                      {comp}
                                      {idx < b.affected_companies.length - 1 ? "," : ""}
                                    </Link>
                                  ))}
                                </span>
                              )}
                              {b.affected_sectors.length > 0 && (
                                <span>
                                  Sector:{" "}
                                  <strong className="text-[var(--text-primary)]">
                                    {b.affected_sectors.join(", ")}
                                  </strong>
                                </span>
                              )}
                              {b.affected_industries.length > 0 && (
                                <span>
                                  Industry:{" "}
                                  <strong className="text-[var(--text-secondary)]">
                                    {b.affected_industries.join(", ")}
                                  </strong>
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Expandable Evidence & Analytical Detail */}
                          {isExpanded && (
                            <div className="space-y-2.5 pt-1">
                              {/* Modelled Central Prediction Section */}
                              {b.model_status === "MODELLED" && b.authoritative_prediction && (
                                <div className="p-2.5 rounded-md bg-emerald-500/5 border border-emerald-500/20 text-xs space-y-1.5">
                                  <div className="flex items-center justify-between flex-wrap gap-2">
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-xs" aria-hidden="true">📊</span>
                                      <span className="font-semibold text-emerald-700 dark:text-emerald-400 text-[11px]">
                                        Authoritative Central Model Output (Frozen Baseline)
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-tabular">
                                        ISIN: {b.authoritative_prediction.isin}
                                      </span>
                                      <Link
                                        href={`/predictions?search=${encodeURIComponent(
                                          b.authoritative_prediction.isin
                                        )}`}
                                        className="text-[10px] text-emerald-600 dark:text-emerald-300 hover:underline font-semibold"
                                      >
                                        View Prediction Horizon ↗
                                      </Link>
                                    </div>
                                  </div>

                                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1 border-t border-emerald-500/15">
                                    <div>
                                      <span className="text-[var(--text-muted)] text-[10px] block">Direction</span>
                                      <strong
                                        className={`font-semibold ${
                                          b.authoritative_prediction.predicted_direction === "POSITIVE"
                                            ? "text-emerald-600 dark:text-emerald-400"
                                            : b.authoritative_prediction.predicted_direction === "NEGATIVE"
                                            ? "text-rose-600 dark:text-rose-400"
                                            : "text-[var(--text-secondary)]"
                                        }`}
                                      >
                                        {b.authoritative_prediction.predicted_direction === "POSITIVE" && "▲ "}
                                        {b.authoritative_prediction.predicted_direction === "NEGATIVE" && "▼ "}
                                        {b.authoritative_prediction.predicted_direction === "NEUTRAL" && "◆ "}
                                        {b.authoritative_prediction.predicted_direction}
                                      </strong>
                                    </div>
                                    <div>
                                      <span className="text-[var(--text-muted)] text-[10px] block">Confidence</span>
                                      <strong className="text-[var(--text-primary)]">
                                        {b.authoritative_prediction.predicted_confidence}
                                      </strong>
                                    </div>
                                    <div>
                                      <span className="text-[var(--text-muted)] text-[10px] block">Event Horizon</span>
                                      <strong className="text-[var(--text-primary)] font-mono font-tabular">
                                        {b.authoritative_prediction.event_window}
                                      </strong>
                                    </div>
                                    <div>
                                      <span className="text-[var(--text-muted)] text-[10px] block">Risk Band</span>
                                      <strong className="text-amber-600 dark:text-amber-400">
                                        {b.authoritative_prediction.risk_category || "MODERATE"}
                                      </strong>
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* State Bill Statutory Firewall Notice */}
                              {!isCentral && (
                                <div className="text-[11px] text-[var(--text-muted)] font-mono flex items-center gap-1.5 p-2 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-hairline)]">
                                  <span aria-hidden="true">🛡</span>
                                  <span>
                                    State Stock Predictions = 0 (Statutory Methodology Invariant). Business intelligence &amp; compliance only.
                                  </span>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Footer Controls */}
                          <div className="flex items-center justify-between pt-2 border-t border-[var(--border-hairline)] text-xs">
                            <div>
                              {b.source_provenance[0] && (
                                <a
                                  href={b.source_provenance[0]}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[10px] text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                                >
                                  <span>Source Provenance ↗</span>
                                </a>
                              )}
                            </div>

                            <div className="flex items-center gap-2">
                              <Link
                                href="/watchlists"
                                className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-[11px] font-medium border border-[var(--border-default)] transition-colors"
                              >
                                ⭐ Watchlists
                              </Link>
                              <button
                                type="button"
                                onClick={() => onExplainRelevance(b.bill_id)}
                                className="px-2.5 py-1 rounded bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-[11px] font-medium border border-[var(--border-default)] transition-colors"
                              >
                                ✦ Explain Relevance
                              </button>
                              <Link
                                href={`/bills/${encodeURIComponent(b.bill_id)}`}
                                className="px-2.5 py-1 rounded bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 text-[11px] font-semibold border border-blue-500/25 transition-colors"
                              >
                                View Dossier →
                              </Link>
                            </div>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

export default LegislativeImpactInspector;

