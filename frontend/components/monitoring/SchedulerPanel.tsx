/**
 * components/monitoring/SchedulerPanel.tsx
 * ==========================================
 * Read-only scheduler observability display.
 * Shows scheduler config, status, last/next run.
 * Does NOT expose any trigger that could run arbitrary shell commands.
 */

"use client";

import React from "react";
import type { SchedulerStatus } from "@/types/api";
import { Skeleton } from "@/components/ui/Skeleton";

interface SchedulerPanelProps {
  data: SchedulerStatus | null;
  loading: boolean;
  error: string | null;
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return "Not scheduled";
  try {
    return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function SchedulerPanel({ data, loading, error }: SchedulerPanelProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load scheduler status:</span> {error}
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div aria-busy="true" aria-label="Loading scheduler status">
        <Skeleton className="h-40 rounded-xl" />
      </div>
    );
  }

  const config = data.config as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <div
        className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden"
        role="region"
        aria-label="Scheduler observability"
      >
        <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-3">
          <span className="text-lg" aria-hidden="true">⏱</span>
          <h3 className="text-sm font-semibold text-slate-200">Monitoring Scheduler</h3>
          <span
            className={`ml-auto text-xs px-2 py-0.5 rounded border font-semibold ${
              data.enabled
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
                : "bg-slate-700/30 text-slate-500 border-slate-700"
            }`}
            aria-label={`Scheduler is ${data.enabled ? "enabled" : "disabled"}`}
          >
            {data.enabled ? "Enabled" : "Disabled"}
          </span>
        </div>

        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Thread Running</div>
            <div className={`text-sm font-semibold ${data.scheduled_running ? "text-emerald-400" : "text-slate-500"}`}>
              {data.scheduled_running ? "Yes" : "No"}
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Run In Progress</div>
            <div className={`text-sm font-semibold ${data.run_in_progress ? "text-amber-400" : "text-slate-500"}`}>
              {data.run_in_progress ? "Yes — running" : "No"}
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Last Result</div>
            <div className={`text-sm font-semibold ${
              data.last_result_status === "SUCCESS" ? "text-emerald-400" :
              data.last_result_status === "FAILED" ? "text-rose-400" :
              data.last_result_status === "PARTIAL_SUCCESS" ? "text-amber-400" :
              "text-slate-500"
            }`}>
              {data.last_result_status ?? "No runs yet"}
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Last Run</div>
            <div className="text-sm text-slate-300">{formatTime(data.last_run_at)}</div>
          </div>

          <div className="space-y-1">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Next Scheduled Run</div>
            <div className="text-sm text-slate-300">{formatTime(data.next_run_at)}</div>
          </div>
        </div>

        {/* Config */}
        {config && Object.keys(config).length > 0 && (
          <div className="border-t border-slate-800 px-5 py-4">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Configuration</div>
            <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {Object.entries(config).map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs text-slate-500 capitalize">{k.replace(/_/g, " ")}</dt>
                  <dd className="text-sm text-slate-300 font-mono">{String(v)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        <div className="border-t border-slate-800 px-5 py-3 bg-slate-950/30">
          <p className="text-xs text-slate-600">
            <span className="font-semibold text-slate-500">Observability only.</span>{" "}
            The scheduler does not automatically retrain models, modify frozen Central predictions,
            or create State stock predictions.
          </p>
        </div>
      </div>
    </div>
  );
}
