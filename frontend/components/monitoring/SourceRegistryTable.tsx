/**
 * components/monitoring/SourceRegistryTable.tsx
 * ================================================
 * Accessible table/card view of all monitoring sources.
 * Supports pagination and filtering by jurisdiction/status.
 */

"use client";

import React, { useState, useCallback } from "react";
import type { MonitoringSourceItem, PaginatedResponse } from "@/types/api";
import { SourceHealthBadge } from "./SourceHealthBadge";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";

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
  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load sources:</span> {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <label htmlFor="jurisdiction-filter" className="text-xs text-slate-500">
          Jurisdiction:
        </label>
        <select
          id="jurisdiction-filter"
          value={jurisdictionFilter}
          onChange={(e) => onJurisdictionChange(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-800 text-slate-200 text-sm px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All</option>
          <option value="central">Central Parliament</option>
          <option value="state">State Legislatures</option>
        </select>

        {data && (
          <span className="text-xs text-slate-500 ml-auto">
            {data.total} source{data.total !== 1 ? "s" : ""} total
          </span>
        )}
      </div>

      {/* Table */}
      {loading || !data ? (
        <div aria-busy="true" aria-label="Loading sources">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-lg mb-2" />
          ))}
        </div>
      ) : data.items.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
          <p className="text-slate-500">No sources match the current filters.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table
              className="w-full text-sm"
              role="table"
              aria-label="Monitoring source registry"
            >
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/80">
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Source
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Jurisdiction
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Enabled
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Last Checked
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Last Success
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Interval
                  </th>
                  <th scope="col" className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Detail
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.items.map((source) => (
                  <tr
                    key={source.source_id}
                    className="hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-200">{source.source_name}</div>
                      {source.state && (
                        <div className="text-xs text-slate-500">{source.state}</div>
                      )}
                      <div className="text-xs text-slate-600 font-mono mt-0.5">{source.source_id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${
                          source.jurisdiction === "central"
                            ? "bg-blue-500/10 text-blue-400 border-blue-500/25"
                            : "bg-purple-500/10 text-purple-400 border-purple-500/25"
                        }`}
                      >
                        {source.jurisdiction === "central" ? "🏛" : "🗳"}{" "}
                        {source.jurisdiction === "central" ? "Central" : "State"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <SourceHealthBadge status={source.status} />
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs font-semibold ${source.enabled ? "text-emerald-400" : "text-slate-500"}`}
                        aria-label={source.enabled ? "Enabled" : "Disabled"}
                      >
                        {source.enabled ? "Yes" : "No"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {formatTime(source.last_checked_at)}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {formatTime(source.last_success_at)}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {source.polling_interval_hours}h
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onSourceClick(source)}
                        className="text-xs text-blue-400 hover:text-blue-300 transition-colors focus:outline-none focus-visible:underline"
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
