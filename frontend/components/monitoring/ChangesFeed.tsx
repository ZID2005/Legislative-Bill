/**
 * components/monitoring/ChangesFeed.tsx
 * =======================================
 * Server-filtered, paginated feed of detected legislative changes.
 * Each item is labelled [OBSERVED] or [DERIVED].
 */

"use client";

import React, { useState, useCallback } from "react";
import type { ChangeEventDetail, PaginatedResponse } from "@/types/api";
import { EpistemicLabel } from "./EpistemicLabel";
import { ProvenanceStrip } from "./ProvenanceStrip";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";

const CHANGE_TYPE_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  NEW_BILL: { label: "New Bill", icon: "📋", color: "text-emerald-400" },
  STATUS_CHANGED: { label: "Status Changed", icon: "🔄", color: "text-amber-400" },
  METADATA_CHANGED: { label: "Metadata Changed", icon: "✏", color: "text-blue-400" },
  DATE_CHANGED: { label: "Date Changed", icon: "📅", color: "text-blue-400" },
  DOCUMENT_CHANGED: { label: "Document Changed", icon: "📄", color: "text-purple-400" },
  SOURCE_CHANGED: { label: "Source Changed", icon: "🔗", color: "text-slate-400" },
  ERROR: { label: "Error", icon: "⚠", color: "text-rose-400" },
  NO_CHANGE: { label: "No Change", icon: "—", color: "text-slate-600" },
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

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
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
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load changes:</span> {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div
        className="flex items-center gap-3 flex-wrap bg-slate-900/50 rounded-xl border border-slate-800 p-3"
        role="search"
        aria-label="Change event filters"
      >
        <label htmlFor="change-jurisdiction" className="text-xs text-slate-500 shrink-0">Jurisdiction:</label>
        <select
          id="change-jurisdiction"
          value={filters.jurisdiction}
          onChange={(e) => onFilterChange({ jurisdiction: e.target.value })}
          className="rounded border border-slate-700 bg-slate-800 text-slate-200 text-xs px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All</option>
          <option value="central">Central</option>
          <option value="state">State</option>
        </select>

        <label htmlFor="change-type" className="text-xs text-slate-500 shrink-0">Change Type:</label>
        <select
          id="change-type"
          value={filters.event_type}
          onChange={(e) => onFilterChange({ event_type: e.target.value })}
          className="rounded border border-slate-700 bg-slate-800 text-slate-200 text-xs px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Types</option>
          <option value="NEW_BILL">New Bill</option>
          <option value="STATUS_CHANGED">Status Changed</option>
          <option value="METADATA_CHANGED">Metadata Changed</option>
          <option value="DATE_CHANGED">Date Changed</option>
          <option value="DOCUMENT_CHANGED">Document Changed</option>
          <option value="SOURCE_CHANGED">Source Changed</option>
        </select>

        {data && (
          <span className="text-xs text-slate-600 ml-auto">
            {data.total} event{data.total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Feed */}
      {loading || !data ? (
        <div aria-busy="true" aria-label="Loading change events">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl mb-2" />
          ))}
        </div>
      ) : data.items.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
          <p className="text-slate-500 text-sm">No change events match the current filters.</p>
          <p className="text-slate-600 text-xs mt-2">
            Events are detected when monitoring runs identify new or changed legislative records.
          </p>
        </div>
      ) : (
        <div className="space-y-2" role="list" aria-label="Detected change events">
          {data.items.map((event) => {
            const typeCfg = CHANGE_TYPE_CONFIG[event.event_type] ?? {
              label: event.event_type,
              icon: "?",
              color: "text-slate-400",
            };

            return (
              <div
                key={event.event_id}
                className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 hover:border-slate-700 hover:bg-slate-800/50 transition-all cursor-pointer group"
                onClick={() => onEventClick(event)}
                role="listitem"
                aria-label={`${typeCfg.label}: ${event.bill_title}`}
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && onEventClick(event)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className={`text-sm font-semibold ${typeCfg.color}`} aria-hidden="true">
                        {typeCfg.icon}
                      </span>
                      <span className={`text-sm font-semibold ${typeCfg.color}`}>{typeCfg.label}</span>
                      <EpistemicLabel status={event.epistemic_status as "OBSERVED" | "DERIVED"} />
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded border ${
                          event.jurisdiction === "central"
                            ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                            : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                        }`}
                      >
                        {event.jurisdiction === "central" ? "Central" : `State${event.state ? ` · ${event.state}` : ""}`}
                      </span>
                    </div>

                    <div className="text-sm text-slate-200 font-medium truncate">{event.bill_title || event.bill_id}</div>

                    {event.field_name && (
                      <div className="text-xs text-slate-500 mt-0.5">
                        Field: <span className="font-mono text-slate-400">{event.field_name}</span>
                      </div>
                    )}

                    <ProvenanceStrip
                      sourceId={event.source_id}
                      detectedAt={event.detected_at}
                      compact
                      className="mt-2"
                    />
                  </div>

                  <div className="text-xs text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    Detail →
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
