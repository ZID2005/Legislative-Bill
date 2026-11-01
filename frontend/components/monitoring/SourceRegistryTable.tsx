/**
 * components/monitoring/SourceRegistryTable.tsx
 * ================================================
 * Redesigned Monitoring Source Registry Table (Task 1.11A).
 *
 * Implements:
 * - High-density institutional layout with hairline dividers
 * - Search by source name or identifier
 * - Jurisdiction filter (All, Central, State)
 * - Status filter (All, Healthy, Degraded, Planned, Error)
 * - Pagination controls and row inspection trigger
 */

"use client";

import React, { useState, useMemo } from "react";
import type { MonitoringSourceItem, PaginatedResponse } from "@/types/api";
import { SourceHealthBadge } from "./SourceHealthBadge";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";
import { cn } from "@/lib/utils";

interface SourceRegistryTableProps {
  data: PaginatedResponse<MonitoringSourceItem> | null;
  loading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
  onSourceClick: (source: MonitoringSourceItem) => void;
  jurisdictionFilter: string;
  onJurisdictionChange: (v: string) => void;
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function SourceRegistryTable({
  data,
  loading,
  error,
  onPageChange,
  onSourceClick,
  jurisdictionFilter,
  onJurisdictionChange,
}: SourceRegistryTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const filteredItems = useMemo(() => {
    if (!data?.items) return [];
    return data.items.filter((src) => {
      if (searchTerm) {
        const q = searchTerm.toLowerCase();
        const matchesName = src.source_name?.toLowerCase().includes(q);
        const matchesId = src.source_id?.toLowerCase().includes(q);
        const matchesState = src.state?.toLowerCase().includes(q);
        if (!matchesName && !matchesId && !matchesState) return false;
      }
      if (statusFilter) {
        const s = String(src.status).toUpperCase();
        if (statusFilter === "HEALTHY" && s !== "HEALTHY" && s !== "IMPLEMENTED") return false;
        if (statusFilter === "DEGRADED" && s !== "DEGRADED") return false;
        if (statusFilter === "ERROR" && s !== "ERROR") return false;
        if (statusFilter === "PLANNED" && s !== "PLANNED") return false;
      }
      return true;
    });
  }, [data?.items, searchTerm, statusFilter]);

  if (error) {
    return (
      <div className="rounded-xl border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load sources:</span> {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Control Bar: Search & Filters */}
      <div
        className="flex items-center gap-3 flex-wrap bg-[var(--bg-card)] p-3 rounded-xl border border-[var(--border-hairline)]"
        role="search"
        aria-label="Source registry filters"
      >
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search sources by name, ID, or state..."
            className="w-full rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] text-xs text-[var(--text-primary)] px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder:text-[var(--text-faint)]"
            aria-label="Filter sources by keyword"
          />
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="jurisdiction-filter" className="text-xs text-[var(--text-faint)] font-mono">
            Jurisdiction:
          </label>
          <select
            id="jurisdiction-filter"
            value={jurisdictionFilter}
            onChange={(e) => onJurisdictionChange(e.target.value)}
            className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] text-[var(--text-primary)] text-xs px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
          >
            <option value="">All</option>
            <option value="central">Central Parliament</option>
            <option value="state">State Legislatures</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="status-filter" className="text-xs text-[var(--text-faint)] font-mono">
            Status:
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] text-[var(--text-primary)] text-xs px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
          >
            <option value="">All Statuses</option>
            <option value="HEALTHY">Healthy / Implemented</option>
            <option value="DEGRADED">Degraded</option>
            <option value="ERROR">Errors</option>
            <option value="PLANNED">Planned</option>
          </select>
        </div>

        {data && (
          <span className="text-xs text-[var(--text-faint)] font-mono ml-auto">
            {filteredItems.length} of {data.total} source{data.total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Table */}
      {loading || !data ? (
        <div aria-busy="true" aria-label="Loading sources" className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-lg" />
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-8 text-center">
          <p className="text-[var(--text-faint)] text-xs font-mono">No sources match the current filters.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] overflow-hidden">
          <div className="overflow-x-auto">
            <table
              className="w-full text-left text-xs"
              role="table"
              aria-label="Monitoring source registry"
            >
              <thead className="bg-[var(--bg-surface)] text-[var(--text-faint)] font-mono uppercase tracking-wider border-b border-[var(--border-hairline)]">
                <tr>
                  <th scope="col" className="px-4 py-3">Source Name & ID</th>
                  <th scope="col" className="px-4 py-3">Jurisdiction</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3 text-center">Active</th>
                  <th scope="col" className="px-4 py-3">Last Checked</th>
                  <th scope="col" className="px-4 py-3">Last Success</th>
                  <th scope="col" className="px-4 py-3 text-right">Cadence</th>
                  <th scope="col" className="px-4 py-3 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-hairline)]">
                {filteredItems.map((source) => (
                  <tr
                    key={source.source_id}
                    className="hover:bg-[var(--bg-card-hover)] transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-semibold text-[var(--text-primary)]">{source.source_name}</div>
                      {source.state && (
                        <div className="text-[11px] text-[var(--text-muted)] mt-0.5">{source.state} Assembly</div>
                      )}
                      <div className="text-[10px] text-[var(--text-faint)] font-mono mt-0.5">{source.source_id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium border",
                          source.jurisdiction === "central"
                            ? "bg-blue-500/10 text-blue-400 border-blue-500/25"
                            : "bg-purple-500/10 text-purple-400 border-purple-500/25"
                        )}
                      >
                        {source.jurisdiction === "central" ? "Central" : "State"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <SourceHealthBadge status={source.status} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={cn("text-xs font-mono font-semibold", source.enabled ? "text-emerald-400" : "text-[var(--text-faint)]")}
                        aria-label={source.enabled ? "Enabled" : "Disabled"}
                      >
                        {source.enabled ? "Yes" : "No"}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[var(--text-muted)]">
                      {formatTime(source.last_checked_at)}
                    </td>
                    <td className="px-4 py-3 font-mono text-[var(--text-muted)]">
                      {formatTime(source.last_success_at)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-[var(--text-muted)]">
                      {source.polling_interval_hours}h
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onSourceClick(source)}
                        className="text-xs font-mono font-medium text-blue-400 hover:text-blue-300 transition-colors focus:outline-none focus-visible:underline"
                        aria-label={`View details for ${source.source_name}`}
                      >
                        Details →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
