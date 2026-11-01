/**
 * components/monitoring/ChangesFeed.tsx
 * =======================================
 * Redesigned Detected Changes Feed (Task 1.11A).
 *
 * Implements:
 * - Scannable institutional change cards with hairline borders
 * - Epistemic classification labels ([OBSERVED] / [DERIVED])
 * - Multi-attribute filters (jurisdiction, event type, source ID)
 * - Provenance strip per event item
 * - Pagination controls and click-to-inspect trigger
 */

"use client";

import React from "react";
import type { ChangeEventDetail, PaginatedResponse } from "@/types/api";
import { EpistemicLabel } from "./EpistemicLabel";
import { ProvenanceStrip } from "./ProvenanceStrip";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";
import { cn } from "@/lib/utils";

const CHANGE_TYPE_CONFIG: Record<string, { label: string; glyph: string; colorClass: string }> = {
  NEW_BILL: { label: "New Bill", glyph: "📋", colorClass: "text-emerald-400" },
  STATUS_CHANGED: { label: "Status Changed", glyph: "🔄", colorClass: "text-amber-400" },
  METADATA_CHANGED: { label: "Metadata Changed", glyph: "✏", colorClass: "text-blue-400" },
  DATE_CHANGED: { label: "Date Changed", glyph: "📅", colorClass: "text-blue-400" },
  DOCUMENT_CHANGED: { label: "Document Changed", glyph: "📄", colorClass: "text-purple-400" },
  SOURCE_CHANGED: { label: "Source Changed", glyph: "🔗", colorClass: "text-[var(--text-muted)]" },
  ERROR: { label: "Error", glyph: "⚠", colorClass: "text-rose-400" },
  NO_CHANGE: { label: "No Change", glyph: "—", colorClass: "text-[var(--text-faint)]" },
};

interface FilterState {
  jurisdiction: string;
  event_type: string;
  source_id: string;
}

interface ChangesFeedProps {
  data: PaginatedResponse<ChangeEventDetail> | null;
  loading: boolean;
  error: string | null;
  filters: FilterState;
  onFilterChange: (f: Partial<FilterState>) => void;
  onPageChange: (page: number) => void;
  onEventClick: (event: ChangeEventDetail) => void;
}

export function ChangesFeed({
  data,
  loading,
  error,
  filters,
  onFilterChange,
  onPageChange,
  onEventClick,
}: ChangesFeedProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load changes:</span> {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search & Filter Bar */}
      <div
        className="flex items-center gap-3 flex-wrap bg-[var(--bg-card)] rounded-xl border border-[var(--border-hairline)] p-3"
        role="search"
        aria-label="Change event filters"
      >
        <div className="flex items-center gap-2">
          <label htmlFor="change-jurisdiction" className="text-xs text-[var(--text-faint)] font-mono shrink-0">
            Jurisdiction:
          </label>
          <select
            id="change-jurisdiction"
            value={filters.jurisdiction}
            onChange={(e) => onFilterChange({ jurisdiction: e.target.value })}
            className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] text-[var(--text-primary)] text-xs px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
          >
            <option value="">All Jurisdictions</option>
            <option value="central">Central Parliament</option>
            <option value="state">State Legislatures</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="change-type" className="text-xs text-[var(--text-faint)] font-mono shrink-0">
            Change Type:
          </label>
          <select
            id="change-type"
            value={filters.event_type}
            onChange={(e) => onFilterChange({ event_type: e.target.value })}
            className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] text-[var(--text-primary)] text-xs px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
          >
            <option value="">All Event Types</option>
            <option value="NEW_BILL">New Bill Introduced</option>
            <option value="STATUS_CHANGED">Status Milestone Transition</option>
            <option value="METADATA_CHANGED">Metadata Field Modified</option>
            <option value="DATE_CHANGED">Official Date Amended</option>
            <option value="DOCUMENT_CHANGED">Gazette Document Updated</option>
            <option value="SOURCE_CHANGED">Intake Source Changed</option>
          </select>
        </div>

        {data && (
          <span className="text-xs text-[var(--text-faint)] font-mono ml-auto">
            {data.total} event{data.total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Feed List */}
      {loading || !data ? (
        <div aria-busy="true" aria-label="Loading change events" className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : data.items.length === 0 ? (
        <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-8 text-center space-y-1">
          <p className="text-[var(--text-faint)] text-xs font-mono">No change events match the current filters.</p>
          <p className="text-[var(--text-muted)] text-[11px]">
            Events are detected when scheduled runs identify legislative deltas against authoritative gazettes.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5" role="list" aria-label="Detected change events">
          {data.items.map((event) => {
            const typeCfg = CHANGE_TYPE_CONFIG[event.event_type] ?? {
              label: event.event_type,
              glyph: "?",
              colorClass: "text-[var(--text-muted)]",
            };

            return (
              <div
                key={event.event_id}
                className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-all cursor-pointer group select-none"
                onClick={() => onEventClick(event)}
                role="listitem"
                aria-label={`${typeCfg.label}: ${event.bill_title || event.bill_id}`}
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && onEventClick(event)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0 space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={cn("text-xs font-mono font-bold flex items-center gap-1", typeCfg.colorClass)}>
                        <span aria-hidden="true">{typeCfg.glyph}</span>
                        {typeCfg.label}
                      </span>
                      <EpistemicLabel status={event.epistemic_status as "OBSERVED" | "DERIVED"} />
                      <span
                        className={cn(
                          "text-[11px] font-mono px-2 py-0.5 rounded border",
                          event.jurisdiction === "central"
                            ? "bg-blue-500/10 text-blue-400 border-blue-500/25"
                            : "bg-purple-500/10 text-purple-400 border-purple-500/25"
                        )}
                      >
                        {event.jurisdiction === "central" ? "Central Parliament" : `State · ${event.state ?? "Assembly"}`}
                      </span>
                    </div>

                    <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-400 transition-colors truncate">
                      {event.bill_title || event.bill_id}
                    </div>

                    {event.field_name && (
                      <div className="text-xs text-[var(--text-faint)] font-mono">
                        Modified Field: <span className="text-[var(--text-secondary)] font-semibold">{event.field_name}</span>
                      </div>
                    )}

                    <ProvenanceStrip
                      sourceId={event.source_id}
                      detectedAt={event.detected_at}
                      compact
                      className="pt-0.5"
                    />
                  </div>

                  <div className="text-xs font-mono text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 pt-1">
                    Inspect Diff →
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {data && data.pages > 1 && (
        <Pagination
          page={data.page}
          pages={data.pages}
          total={data.total}
          limit={25}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}
