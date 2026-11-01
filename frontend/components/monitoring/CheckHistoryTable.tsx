/**
 * components/monitoring/CheckHistoryTable.tsx
 * ============================================
 * Redesigned Monitoring Run History Table (Task 1.11A).
 *
 * Implements:
 * - Scannable tabular history of pipeline ingestion runs
 * - Accurate durations and timestamps
 * - Clear success/partial/failure status badges
 * - Pagination controls
 */

"use client";

import React from "react";
import type { MonitoringRunDetail, PaginatedResponse } from "@/types/api";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";
import { cn } from "@/lib/utils";

interface CheckHistoryTableProps {
  data: PaginatedResponse<MonitoringRunDetail> | null;
  loading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
}

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

function RunStatusBadge({ status }: { status: string }) {
  const norm = status?.toUpperCase() ?? "UNKNOWN";
  if (norm === "SUCCESS") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[var(--color-success-bg)] text-[var(--color-success)] border border-[var(--color-success-border)]">
        ✓ SUCCESS
      </span>
    );
  }
  if (norm === "PARTIAL_SUCCESS") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[var(--color-warning-bg)] text-[var(--color-warning)] border border-[var(--color-warning-border)]">
        ▲ PARTIAL
      </span>
    );
  }
  if (norm === "FAILED") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[var(--color-error-bg)] text-[var(--color-error)] border border-[var(--color-error-border)]">
        ✕ FAILED
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)]">
      ● RUNNING
    </span>
  );
}

export function CheckHistoryTable({ data, loading, error, onPageChange }: CheckHistoryTableProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load run history:</span> {error}
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div aria-busy="true" aria-label="Loading run history" className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 rounded-lg" />
        ))}
      </div>
    );
  }

  if (data.items.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-8 text-center space-y-1">
        <p className="text-[var(--text-faint)] text-xs font-mono">No monitoring runs have been recorded yet.</p>
        <p className="text-[var(--text-muted)] text-[11px]">
          Runs are recorded automatically when the scheduler executes or when an authorized operator triggers a safe poll.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-xs text-[var(--text-faint)] font-mono flex items-center justify-between">
        <span>Showing {data.items.length} of {data.total} run{data.total !== 1 ? "s" : ""}</span>
        <span>Audit Trail Active</span>
      </div>

      <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs" role="table" aria-label="Monitoring run history">
            <thead className="bg-[var(--bg-surface)] text-[var(--text-faint)] font-mono uppercase tracking-wider border-b border-[var(--border-hairline)]">
              <tr>
                <th scope="col" className="px-4 py-3">Run ID</th>
                <th scope="col" className="px-4 py-3">Started Timestamp</th>
                <th scope="col" className="px-4 py-3">Duration</th>
                <th scope="col" className="px-4 py-3">Execution Status</th>
                <th scope="col" className="px-4 py-3">Trigger Channel</th>
                <th scope="col" className="px-4 py-3 text-center">Sources (OK/Total)</th>
                <th scope="col" className="px-4 py-3 text-right">New Bills</th>
                <th scope="col" className="px-4 py-3 text-right">Changes</th>
                <th scope="col" className="px-4 py-3 text-right">Errors</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-hairline)] font-mono">
              {data.items.map((run) => (
                <tr key={run.run_id} className="hover:bg-[var(--bg-card-hover)] transition-colors">
                  <td className="px-4 py-3 text-[var(--text-secondary)] font-semibold" title={run.run_id}>
                    {run.run_id.slice(0, 12)}…
                  </td>
                  <td className="px-4 py-3 text-[var(--text-muted)]">
                    {formatTime(run.started_at)}
                  </td>
                  <td className="px-4 py-3 text-[var(--text-muted)]">
                    {formatDuration(run.duration_seconds)}
                  </td>
                  <td className="px-4 py-3">
                    <RunStatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3 text-[var(--text-muted)] capitalize">
                    {run.trigger.replace(/_/g, " ")}
                  </td>
                  <td className="px-4 py-3 text-center text-[var(--text-secondary)]">
                    {run.sources_succeeded} / {run.sources_checked}
                  </td>
                  <td className="px-4 py-3 text-right font-bold text-emerald-400 tabular-nums">
                    +{run.new_bills}
                  </td>
                  <td className="px-4 py-3 text-right font-bold text-amber-400 tabular-nums">
                    {run.changed_bills}
                  </td>
                  <td className={cn("px-4 py-3 text-right font-bold tabular-nums", run.errors > 0 ? "text-rose-400" : "text-[var(--text-muted)]")}>
                    {run.errors}
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
