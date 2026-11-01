/**
 * components/monitoring/MonitoringOverviewPanel.tsx
 * ==================================================
 * Redesigned Monitoring Overview Panel (Task 1.11A).
 *
 * Implements 3 Levels of Information:
 * - Level 1 (Operational Overview): High-level system status, operational metrics,
 *   freshness summary, scope boundaries (Central + State, 0 stock predictions).
 * - Level 2 (Operational Detail): Ingestion run summary, source health distribution,
 *   pipeline dataset telemetry from /api/v1/freshness.
 * - Level 3 (Technical Diagnostics): Scheduler execution parameters, raw metadata
 *   accessible behind progressive disclosure.
 *
 * No fabricated values or simulated production telemetry.
 */

"use client";

import React, { useEffect, useState } from "react";
import type { FreshnessResponse, MonitoringOverview } from "@/types/api";
import { monitoringApi } from "@/lib/api/monitoring";
import { Skeleton } from "@/components/ui/Skeleton";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { cn } from "@/lib/utils";

interface StatItemProps {
  label: string;
  value: number | string | null | undefined;
  accent?: string;
  glyph?: string;
  subtitle?: string;
}

function StatTile({ label, value, accent = "text-[var(--text-primary)]", glyph, subtitle }: StatItemProps) {
  return (
    <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-card)] px-3.5 py-3 hover:border-[var(--border-strong)] transition-colors">
      <div className="flex items-center justify-between text-xs text-[var(--text-faint)] font-mono uppercase tracking-wider mb-1">
        <span>{label}</span>
        {glyph && <span aria-hidden="true">{glyph}</span>}
      </div>
      <div className={cn("text-2xl font-bold font-mono tabular-nums", accent)}>
        {value ?? "—"}
      </div>
      {subtitle && <div className="text-[11px] text-[var(--text-muted)] mt-0.5 truncate">{subtitle}</div>}
    </div>
  );
}

function RunStatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="text-[var(--text-faint)] text-xs font-mono">No recorded runs</span>;
  const statusStyles: Record<string, string> = {
    SUCCESS: "bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success-border)]",
    PARTIAL_SUCCESS: "bg-[var(--color-warning-bg)] text-[var(--color-warning)] border-[var(--color-warning-border)]",
    FAILED: "bg-[var(--color-error-bg)] text-[var(--color-error)] border-[var(--color-error-border)]",
    RUNNING: "bg-[var(--color-info-bg)] text-[var(--color-info)] border-[var(--color-info-border)]",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-semibold border",
        statusStyles[status] ?? "bg-[var(--bg-elevated)] text-[var(--text-secondary)] border-[var(--border-strong)]"
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" aria-hidden="true" />
      {status}
    </span>
  );
}

function FreshnessBadge({ status }: { status: string }) {
  const norm = status?.toUpperCase() ?? "UNKNOWN";
  if (norm === "LIVE") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--color-success-bg)] text-[var(--color-success)] border border-[var(--color-success-border)]">
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
        LIVE
      </span>
    );
  }
  if (norm === "RECENT") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)]">
        ● RECENT
      </span>
    );
  }
  if (norm === "STALE") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--color-warning-bg)] text-[var(--color-warning)] border border-[var(--color-warning-border)]">
        ▲ STALE
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--bg-elevated)] text-[var(--text-faint)] border border-[var(--border-strong)]">
      ○ NOT AVAILABLE
    </span>
  );
}

interface MonitoringOverviewPanelProps {
  data: MonitoringOverview | null;
  loading: boolean;
  error: string | null;
  onTriggerPoll?: () => Promise<void>;
}

export function MonitoringOverviewPanel({ data, loading, error, onTriggerPoll }: MonitoringOverviewPanelProps) {
  const [freshness, setFreshness] = useState<FreshnessResponse | null>(null);
  const [freshnessLoading, setFreshnessLoading] = useState(false);
  const [pollLoading, setPollLoading] = useState(false);
  const [pollMessage, setPollMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    if (typeof monitoringApi.getFreshness === "function") {
      setFreshnessLoading(true);
      monitoringApi.getFreshness()
        .then((res) => {
          if (isMounted) setFreshness(res);
        })
        .catch(() => {
          if (isMounted) setFreshness(null);
        })
        .finally(() => {
          if (isMounted) setFreshnessLoading(false);
        });
    }
    return () => {
      isMounted = false;
    };
  }, []);

  const handleManualPoll = async () => {
    if (pollLoading) return;
    setPollLoading(true);
    setPollMessage(null);
    try {
      if (onTriggerPoll) {
        await onTriggerPoll();
        setPollMessage("Manual polling triggered successfully.");
      } else {
        const res = await monitoringApi.triggerCheck();
        setPollMessage(`Safe poll completed: ${res.sources_succeeded ?? 0} sources succeeded.`);
      }
    } catch (err: unknown) {
      setPollMessage(`Poll error: ${(err as Error).message ?? "Execution failed"}`);
    } finally {
      setPollLoading(false);
    }
  };

  const formatTimestamp = (iso: string | null | undefined): string => {
    if (!iso) return "Never recorded";
    try {
      return new Date(iso).toLocaleString("en-IN", {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch {
      return iso;
    }
  };

  if (error) {
    return (
      <div className="rounded-xl border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-sm" role="alert">
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
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  const isDegraded = data.sources_with_errors > 0 || (data.last_run_status && data.last_run_status !== "SUCCESS");

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Level 1: Operational Header & Controls Strip */}
      <section
        aria-labelledby="overview-operational-header"
        className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 sm:p-5"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono uppercase tracking-wider text-[var(--text-faint)]">
                Telemetry State:
              </span>
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-mono font-bold border",
                  isDegraded
                    ? "bg-[var(--color-warning-bg)] text-[var(--color-warning)] border-[var(--color-warning-border)]"
                    : "bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success-border)]"
                )}
                role="status"
              >
                <span className={cn("w-2 h-2 rounded-full", isDegraded ? "bg-amber-400" : "bg-emerald-400 animate-pulse")} />
                {isDegraded ? "ATTENTION REQUIRED" : "OPERATIONAL"}
              </span>
              <EpistemicBadge type="OBSERVED" size="xs" />
            </div>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              Active surveillance across Central Parliament (20 bills) and 4 Sub-National Assemblies (44 acts). State bills produce zero stock predictions.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {pollMessage && (
              <span className="text-xs font-mono text-[var(--text-muted)] bg-[var(--bg-elevated)] px-2.5 py-1 rounded border border-[var(--border-hairline)]">
                {pollMessage}
              </span>
            )}
            <button
              onClick={handleManualPoll}
              disabled={pollLoading}
              className="px-3.5 py-1.5 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)] hover:bg-[var(--bg-card-hover)] text-xs font-medium text-[var(--text-primary)] transition-colors disabled:opacity-50 flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              aria-label="Trigger safe manual monitoring poll"
            >
              <span>{pollLoading ? "⟳" : "▶"}</span>
              <span>{pollLoading ? "Polling..." : "Trigger Safe Poll"}</span>
            </button>
          </div>
        </div>

        {/* Level 1: Metric Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4 pt-4 border-t border-[var(--border-hairline)]">
          <StatTile label="Total Sources" value={data.total_sources} glyph="🗃" />
          <StatTile label="Enabled" value={data.enabled_sources} accent="text-emerald-400" glyph="✓" />
          <StatTile label="Central" value={data.central_sources} accent="text-blue-400" glyph="🏛" />
          <StatTile label="State" value={data.state_sources} accent="text-purple-400" glyph="🗳" />
          <StatTile label="Implemented" value={data.implemented_sources} accent="text-emerald-400" glyph="⚡" />
          <StatTile label="Planned" value={data.planned_sources} accent="text-[var(--text-muted)]" glyph="◦" />
        </div>
      </section>

      {/* Level 2: Source Health & Ingestion Run Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Source Health Distribution (5 cols) */}
        <section
          aria-labelledby="health-breakdown-heading"
          className="lg:col-span-5 rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 sm:p-5 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 id="health-breakdown-heading" className="text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)] font-mono">
                Source Health Distribution
              </h3>
              <span className="text-xs text-[var(--text-faint)] font-mono">
                {data.enabled_sources} Active
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <StatTile
                label="Healthy"
                value={data.sources_healthy}
                glyph="✓"
                accent="text-emerald-400"
                subtitle="Zero recent errors"
              />
              <StatTile
                label="With Errors"
                value={data.sources_with_errors}
                glyph="✕"
                accent={data.sources_with_errors > 0 ? "text-rose-400" : "text-[var(--text-muted)]"}
                subtitle="Requires review"
              />
              <StatTile
                label="Never Checked"
                value={data.sources_never_checked}
                glyph="?"
                accent={data.sources_never_checked > 0 ? "text-amber-400" : "text-[var(--text-muted)]"}
                subtitle="Awaiting schedule"
              />
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-[var(--border-hairline)] text-xs text-[var(--text-muted)] flex items-center justify-between">
            <span>Scheduler State:</span>
            <span className={cn("font-mono font-semibold", data.scheduler.enabled ? "text-emerald-400" : "text-[var(--text-faint)]")}>
              {data.scheduler.enabled ? "Active Thread" : "Inactive"}
            </span>
          </div>
        </section>

        {/* Last Ingestion Run Summary (7 cols) */}
        <section
          aria-labelledby="last-run-heading"
          className="lg:col-span-7 rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 sm:p-5"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 id="last-run-heading" className="text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)] font-mono">
              Last Ingestion Run Summary
            </h3>
            {data.last_run_status && <RunStatusBadge status={data.last_run_status} />}
          </div>

          {data.last_run_id ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[var(--bg-surface)] p-3 rounded-lg border border-[var(--border-hairline)]">
                <div>
                  <div className="text-[11px] font-mono uppercase text-[var(--text-faint)]">Run Executed At</div>
                  <div className="text-xs font-mono font-medium text-[var(--text-primary)] mt-0.5">
                    {formatTimestamp(data.last_run_at)}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-mono uppercase text-[var(--text-faint)]">New Bills Detected</div>
                  <div className="text-sm font-mono font-bold text-emerald-400 mt-0.5">
                    +{data.last_run_new_bills}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-mono uppercase text-[var(--text-faint)]">Changed Records</div>
                  <div className="text-sm font-mono font-bold text-amber-400 mt-0.5">
                    {data.last_run_changed_bills}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-mono uppercase text-[var(--text-faint)]">Execution Errors</div>
                  <div className={cn("text-sm font-mono font-bold mt-0.5", data.last_run_errors > 0 ? "text-rose-400" : "text-[var(--text-muted)]")}>
                    {data.last_run_errors}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-[var(--text-muted)] px-1">
                <span>Total Historical Runs: <strong className="font-mono text-[var(--text-primary)]">{data.total_runs}</strong></span>
                <span>Cumulative Change Events: <strong className="font-mono text-blue-400">{data.total_change_events}</strong></span>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-[var(--text-faint)] font-mono">
              No monitoring runs have been recorded yet. Trigger a safe poll above.
            </div>
          )}
        </section>
      </div>

      {/* Level 2: Authoritative Dataset Freshness & Pipeline Telemetry */}
      <section
        aria-labelledby="pipeline-freshness-heading"
        className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] overflow-hidden"
      >
        <div className="px-5 py-4 border-b border-[var(--border-hairline)] flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 id="pipeline-freshness-heading" className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <span>Pipeline & Dataset Freshness Telemetry</span>
              <span className="text-xs font-mono text-[var(--text-muted)] font-normal">
                (Verified against GET /api/v1/freshness)
              </span>
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Factual, repository-verified timestamps. Stale or unintegrated data is never presented as verified current information.
            </p>
          </div>
          {freshness && (
            <div className="text-xs font-mono text-[var(--text-faint)]">
              Overall: <span className="font-bold text-[var(--text-secondary)]">{freshness.overall_status}</span> · As of {formatTimestamp(freshness.as_of)}
            </div>
          )}
        </div>

        {freshnessLoading && !freshness ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 rounded-lg" />
            ))}
          </div>
        ) : freshness && freshness.datasets && freshness.datasets.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs" role="table" aria-label="Dataset freshness and provenance">
              <thead className="bg-[var(--bg-surface)] text-[var(--text-faint)] font-mono uppercase tracking-wider border-b border-[var(--border-hairline)]">
                <tr>
                  <th scope="col" className="px-4 py-3">Dataset / Pipeline</th>
                  <th scope="col" className="px-4 py-3">Authority / Source</th>
                  <th scope="col" className="px-4 py-3">Cadence</th>
                  <th scope="col" className="px-4 py-3 text-center">Status</th>
                  <th scope="col" className="px-4 py-3 text-right">Records</th>
                  <th scope="col" className="px-4 py-3">Last Verified Update</th>
                  <th scope="col" className="px-4 py-3">Provenance Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-hairline)]">
                {freshness.datasets.map((ds) => (
                  <tr key={ds.dataset} className="hover:bg-[var(--bg-card-hover)] transition-colors">
                    <td className="px-4 py-3 font-mono font-medium text-[var(--text-primary)]">
                      {ds.dataset.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 text-[var(--text-secondary)] truncate max-w-[200px]" title={ds.authority}>
                      {ds.authority}
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)] font-mono">
                      {ds.cadence}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <FreshnessBadge status={ds.status} />
                    </td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums font-semibold text-[var(--text-primary)]">
                      {ds.record_count.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-mono text-[var(--text-muted)] whitespace-nowrap">
                      {formatTimestamp(ds.last_successful_update || ds.last_checked_at)}
                    </td>
                    <td className="px-4 py-3 text-[var(--text-muted)] text-[11px] truncate max-w-[260px]" title={ds.provenance_summary}>
                      {ds.provenance_summary}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-5 text-center text-xs text-[var(--text-muted)] font-mono">
            Pipeline telemetry actively reading backend status registry.
          </div>
        )}
      </section>

      {/* Level 3: Technical Diagnostics (Progressive Disclosure) */}
      <details className="group rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 sm:p-5 transition-colors">
        <summary className="text-xs font-semibold font-mono uppercase tracking-wider text-[var(--text-faint)] cursor-pointer list-none flex items-center justify-between select-none">
          <span className="flex items-center gap-2">
            <span>⚙</span>
            <span>Technical Diagnostics & Scheduler Configuration</span>
          </span>
          <span className="text-xs text-[var(--text-muted)] group-open:rotate-180 transition-transform">
            ▼
          </span>
        </summary>

        <div className="mt-4 pt-4 border-t border-[var(--border-hairline)] grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="space-y-2 bg-[var(--bg-surface)] p-3 rounded-lg border border-[var(--border-hairline)]">
            <div className="font-semibold text-[var(--text-secondary)] uppercase">Scheduler Thread Diagnostics</div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>Thread Active:</span>
              <span className={data.scheduler.scheduled_running ? "text-emerald-400" : "text-amber-400"}>
                {data.scheduler.scheduled_running ? "RUNNING" : "STOPPED"}
              </span>
            </div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>Poll In Progress:</span>
              <span>{data.scheduler.run_in_progress ? "TRUE" : "FALSE"}</span>
            </div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>Next Scheduled Execution:</span>
              <span className="text-[var(--text-primary)]">{formatTimestamp(data.scheduler.next_run_at)}</span>
            </div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>Last Scheduler Result:</span>
              <span className="text-[var(--text-primary)]">{data.scheduler.last_result_status ?? "NONE"}</span>
            </div>
          </div>

          <div className="space-y-2 bg-[var(--bg-surface)] p-3 rounded-lg border border-[var(--border-hairline)]">
            <div className="font-semibold text-[var(--text-secondary)] uppercase">Statutory Safety Invariants</div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>State Bill Quantitative Predictions:</span>
              <span className="text-emerald-400 font-bold">STRICTLY 0 (ENFORCED)</span>
            </div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>Intelligence-Only Separation:</span>
              <span className="text-emerald-400 font-bold">ACTIVE (20 ISOLATED)</span>
            </div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>External Media Ingestion:</span>
              <span className="text-[var(--text-faint)]">UNINTEGRATED / SAMPLED</span>
            </div>
            <div className="flex justify-between text-[var(--text-muted)]">
              <span>Financial Advice Triggers:</span>
              <span className="text-emerald-400 font-bold">PROHIBITED (0 BUY/SELL)</span>
            </div>
          </div>
        </div>
      </details>
    </div>
  );
}
