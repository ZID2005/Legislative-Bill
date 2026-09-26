/**
 * components/monitoring/CheckHistoryTable.tsx
 * ============================================
 * Paginated monitoring run history table.
 */

"use client";

import React from "react";
import type { MonitoringRunDetail, PaginatedResponse } from "@/types/api";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";

interface CheckHistoryTableProps {
  data: PaginatedResponse<MonitoringRunDetail> | null;
  loading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
}

const STATUS_COLORS: Record<string, string> = {
  SUCCESS: "text-emerald-400",
  PARTIAL_SUCCESS: "text-amber-400",
  FAILED: "text-rose-400",
  RUNNING: "text-blue-400",
};

function formatTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function formatDuration(secs: number | null | undefined): string {
  if (secs == null) return "—";
  if (secs < 60) return `${secs.toFixed(1)}s`;
  return `${(secs / 60).toFixed(1)}m`;
}

export function CheckHistoryTable({ data, loading, error, onPageChange }: CheckHistoryTableProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load run history:</span> {error}
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div aria-busy="true" aria-label="Loading run history">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 rounded-lg mb-2" />
        ))}
      </div>
    );
  }

  if (data.items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
        <p className="text-slate-500 text-sm">No monitoring runs have been recorded yet.</p>
        <p className="text-slate-600 text-xs mt-2">
          Runs are created when the scheduler executes or a manual check is triggered.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-xs text-slate-500">
        Showing {data.items.length} of {data.total} run{data.total !== 1 ? "s" : ""}
      </div>

      <div className="rounded-xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table" aria-label="Monitoring run history">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80">
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Run ID</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Started</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Duration</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Status</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Trigger</th>
                <th scope="col" className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">Sources</th>
                <th scope="col" className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">New Bills</th>
                <th scope="col" className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">Changes</th>
                <th scope="col" className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">Errors</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {data.items.map((run) => (
                <tr key={run.run_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {run.run_id.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">{formatTime(run.started_at)}</td>
                  <td className="px-4 py-3 text-xs text-slate-400">{formatDuration(run.duration_seconds)}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-semibold ${STATUS_COLORS[run.status] ?? "text-slate-400"}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400 capitalize">{run.trigger}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs text-slate-300">{run.sources_checked}</span>
                    <span className="text-xs text-slate-600"> ({run.sources_succeeded}✓ {run.sources_failed}✕)</span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs font-semibold text-emerald-400">
                    {run.new_bills}
                  </td>
                  <td className="px-4 py-3 text-center text-xs font-semibold text-amber-400">
                    {run.changed_bills + run.document_changes}
                  </td>
                  <td className="px-4 py-3 text-center text-xs font-semibold">
                    <span className={run.errors > 0 ? "text-rose-400" : "text-slate-600"}>
                      {run.errors}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.pages > 1 && (
        <Pagination
          page={data.page}
          pages={data.pages}
          total={data.total}
          limit={20}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}
