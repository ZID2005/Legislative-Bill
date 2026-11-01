/**
 * components/monitoring/SchedulerPanel.tsx
 * ==========================================
 * Redesigned Scheduler Observability Panel (Task 1.11A).
 *
 * Implements:
 * - Read-only scheduler observability metrics
 * - Configuration parameters inspection
 * - Safe manual poll trigger invoking POST /api/v1/monitoring/check
 * - Strictly does NOT expose any execution of arbitrary shell commands.
 */

"use client";

import React, { useState } from "react";
import type { SchedulerStatus } from "@/types/api";
import { Skeleton } from "@/components/ui/Skeleton";
import { monitoringApi } from "@/lib/api/monitoring";
import { cn } from "@/lib/utils";

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
  const [polling, setPolling] = useState(false);
  const [pollResult, setPollResult] = useState<string | null>(null);

  const handlePoll = async () => {
    if (polling) return;
    setPolling(true);
    setPollResult(null);
    try {
      const res = await monitoringApi.triggerCheck();
      setPollResult(`Poll complete: ${res.status} (${res.sources_succeeded ?? 0} succeeded)`);
    } catch (e: unknown) {
      setPollResult(`Poll error: ${(e as Error).message ?? "Failed"}`);
    } finally {
      setPolling(false);
    }
  };

  if (error) {
    return (
      <div className="rounded-xl border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load scheduler status:</span> {error}
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div aria-busy="true" aria-label="Loading scheduler status">
        <Skeleton className="h-44 rounded-xl" />
      </div>
    );
  }

  const config = (data.config ?? {}) as Record<string, unknown>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div
        className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] overflow-hidden"
        role="region"
        aria-label="Scheduler observability"
      >
        <div className="px-5 py-4 border-b border-[var(--border-hairline)] flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2.5">
            <span className="text-base text-[var(--text-muted)]" aria-hidden="true">⏱</span>
            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                Legislative Surveillance Scheduler
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Automated background polling thread for Central Parliament and State Gazette registries.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={cn(
                "text-xs px-2.5 py-0.5 rounded border font-mono font-bold",
                data.enabled
                  ? "bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success-border)]"
                  : "bg-[var(--bg-elevated)] text-[var(--text-faint)] border-[var(--border-strong)]"
              )}
              aria-label={`Scheduler is ${data.enabled ? "enabled" : "disabled"}`}
            >
              {data.enabled ? "Active" : "Disabled"}
            </span>

            <button
              onClick={handlePoll}
              disabled={polling}
              className="px-3 py-1 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)] hover:bg-[var(--bg-card-hover)] text-xs font-mono font-medium text-[var(--text-primary)] transition-colors disabled:opacity-50 flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              aria-label="Execute safe manual monitoring check"
            >
              <span>{polling ? "⟳" : "▶"}</span>
              <span>{polling ? "Executing Poll..." : "Safe Trigger Poll"}</span>
            </button>
          </div>
        </div>

        {pollResult && (
          <div className="px-5 py-2.5 bg-[var(--bg-surface)] border-b border-[var(--border-hairline)] text-xs font-mono text-[var(--text-secondary)]">
            {pollResult}
          </div>
        )}

        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] p-3.5 space-y-1">
            <div className="text-[11px] font-mono text-[var(--text-faint)] uppercase tracking-wider">
              Background Thread
            </div>
            <div className={cn("text-sm font-mono font-bold", data.scheduled_running ? "text-emerald-400" : "text-[var(--text-faint)]")}>
              {data.scheduled_running ? "RUNNING (ACTIVE)" : "STOPPED"}
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] p-3.5 space-y-1">
            <div className="text-[11px] font-mono text-[var(--text-faint)] uppercase tracking-wider">
              Poll State
            </div>
            <div className={cn("text-sm font-mono font-bold", data.run_in_progress ? "text-amber-400" : "text-[var(--text-muted)]")}>
              {data.run_in_progress ? "IN PROGRESS" : "IDLE (AWAITING SCHEDULE)"}
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] p-3.5 space-y-1">
            <div className="text-[11px] font-mono text-[var(--text-faint)] uppercase tracking-wider">
              Last Poll Outcome
            </div>
            <div className={cn("text-sm font-mono font-bold",
              data.last_result_status === "SUCCESS" ? "text-emerald-400" :
              data.last_result_status === "FAILED" ? "text-rose-400" :
              data.last_result_status === "PARTIAL_SUCCESS" ? "text-amber-400" :
              "text-[var(--text-faint)]"
            )}>
              {data.last_result_status ?? "No runs recorded"}
            </div>
          </div>

          <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] p-3.5 space-y-1">
            <div className="text-[11px] font-mono text-[var(--text-faint)] uppercase tracking-wider">
              Next Scheduled Poll
            </div>
            <div className="text-xs font-mono font-medium text-[var(--text-primary)] mt-0.5 truncate" title={formatTime(data.next_run_at)}>
              {formatTime(data.next_run_at)}
            </div>
          </div>
        </div>

        <div className="px-5 pb-5 pt-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="text-xs font-mono text-[var(--text-muted)]">
            Last Successful Cycle: <strong className="text-[var(--text-primary)]">{formatTime(data.last_run_at)}</strong>
          </div>
          <div className="text-xs font-mono text-[var(--text-faint)] sm:text-right">
            Safety Guardrail: Safe idempotent poll only · Zero state stock predictions
          </div>
        </div>
      </div>

      {/* Level 3: Configuration Diagnostics */}
      <details className="group rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 sm:p-5">
        <summary className="text-xs font-semibold font-mono uppercase tracking-wider text-[var(--text-faint)] cursor-pointer list-none flex items-center justify-between select-none">
          <span>Scheduler Runtime Configuration Parameters</span>
          <span className="text-[var(--text-muted)] group-open:rotate-180 transition-transform">▼</span>
        </summary>

        <div className="mt-4 pt-3 border-t border-[var(--border-hairline)]">
          <pre className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-hairline)] text-xs font-mono text-[var(--text-secondary)] overflow-x-auto">
            {JSON.stringify(config, null, 2)}
          </pre>
        </div>
      </details>
    </div>
  );
}
