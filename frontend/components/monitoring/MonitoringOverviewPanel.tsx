/**
 * components/monitoring/MonitoringOverviewPanel.tsx
 * ==================================================
 * Displays actual monitoring telemetry from the backend.
 * No hardcoded values — all data from /api/v1/monitoring/overview.
 *
 * Shows:
 * - Source counts (total, enabled, central, state, implemented, planned)
 * - Source health (healthy, errors, never checked)
 * - Last run summary (status, new bills, changed bills, errors)
 * - Scheduler status
 * - Total change events
 */

"use client";

import React from "react";
import type { MonitoringOverview } from "@/types/api";
import { Skeleton } from "@/components/ui/Skeleton";

interface OverviewStatProps {
  label: string;
  value: number | string | null | undefined;
  icon?: string;
  accent?: string;
  subtitle?: string;
}

function OverviewStat({ label, value, icon, accent = "text-slate-200", subtitle }: OverviewStatProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 hover:border-slate-700 transition-colors">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</span>
        {icon && <span className="text-base" aria-hidden="true">{icon}</span>}
      </div>
      <div className={`text-2xl font-bold tabular-nums ${accent}`}>
        {value ?? "—"}
      </div>
      {subtitle && <div className="text-xs text-slate-600 mt-0.5">{subtitle}</div>}
    </div>
  );
}

function RunStatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="text-slate-500 text-sm">No runs yet</span>;
  const colors: Record<string, string> = {
    SUCCESS: "text-emerald-400",
    PARTIAL_SUCCESS: "text-amber-400",
    FAILED: "text-rose-400",
    RUNNING: "text-blue-400",
  };
  return (
    <span className={`text-sm font-semibold ${colors[status] ?? "text-slate-400"}`}>
      {status}
    </span>
  );
}

interface MonitoringOverviewPanelProps {
  data: MonitoringOverview | null;
  loading: boolean;
  error: string | null;
}

export function MonitoringOverviewPanel({ data, loading, error }: MonitoringOverviewPanelProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load monitoring overview:</span> {error}
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Loading monitoring overview">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-lg" />
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  const formatTime = (iso: string | null | undefined) => {
    if (!iso) return "Never";
    try {
      return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
    } catch {
      return iso;
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Source Counts */}
      <section aria-labelledby="sources-heading">
        <h3 id="sources-heading" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Source Registry
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <OverviewStat label="Total Sources" value={data.total_sources} icon="🗃" />
          <OverviewStat label="Enabled" value={data.enabled_sources} icon="✓" accent="text-emerald-400" />
          <OverviewStat label="Central" value={data.central_sources} icon="🏛" accent="text-blue-400" />
          <OverviewStat label="State" value={data.state_sources} icon="🗳" accent="text-purple-400" />
          <OverviewStat label="Implemented" value={data.implemented_sources} icon="⚡" accent="text-emerald-400" />
          <OverviewStat label="Planned" value={data.planned_sources} icon="◦" accent="text-slate-400" />
        </div>
      </section>

      {/* Source Health */}
      <section aria-labelledby="health-heading">
        <h3 id="health-heading" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Source Health
        </h3>
        <div className="grid grid-cols-3 gap-3">
          <OverviewStat label="Healthy" value={data.sources_healthy} icon="✓" accent="text-emerald-400" />
          <OverviewStat
            label="With Errors"
            value={data.sources_with_errors}
            icon="✕"
            accent={data.sources_with_errors > 0 ? "text-rose-400" : "text-slate-400"}
          />
          <OverviewStat
            label="Never Checked"
            value={data.sources_never_checked}
            icon="?"
            accent={data.sources_never_checked > 0 ? "text-amber-400" : "text-slate-400"}
          />
        </div>
      </section>

      {/* Last Run Summary */}
      <section aria-labelledby="lastrun-heading">
        <h3 id="lastrun-heading" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Last Run Summary
        </h3>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          {data.last_run_id ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Status</div>
                <RunStatusBadge status={data.last_run_status} />
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Run at</div>
                <div className="text-sm text-slate-300">{formatTime(data.last_run_at)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">New Bills</div>
                <div className="text-sm font-semibold text-emerald-400">{data.last_run_new_bills}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Changed Bills</div>
                <div className="text-sm font-semibold text-amber-400">{data.last_run_changed_bills}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Errors</div>
                <div className={`text-sm font-semibold ${data.last_run_errors > 0 ? "text-rose-400" : "text-slate-400"}`}>
                  {data.last_run_errors}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No monitoring runs have been recorded yet.</p>
          )}
        </div>
      </section>

      {/* Scheduler + Change Events Row */}
      <section aria-labelledby="sched-heading">
        <h3 id="sched-heading" className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Scheduler & Events
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
            <div className="text-xs text-slate-500 mb-1">Scheduler</div>
            <div className={`text-sm font-semibold ${data.scheduler.enabled ? "text-emerald-400" : "text-slate-500"}`}>
              {data.scheduler.enabled ? "Enabled" : "Disabled"}
            </div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
            <div className="text-xs text-slate-500 mb-1">Last Scheduled Run</div>
            <div className="text-sm text-slate-300">{formatTime(data.scheduler.last_run_at)}</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
            <div className="text-xs text-slate-500 mb-1">Total Runs</div>
            <div className="text-2xl font-bold tabular-nums text-slate-200">{data.total_runs}</div>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
            <div className="text-xs text-slate-500 mb-1">Total Change Events</div>
            <div className="text-2xl font-bold tabular-nums text-blue-400">{data.total_change_events}</div>
          </div>
        </div>
      </section>
    </div>
  );
}
