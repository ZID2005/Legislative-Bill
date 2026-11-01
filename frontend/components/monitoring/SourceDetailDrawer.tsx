/**
 * components/monitoring/SourceDetailDrawer.tsx
 * =============================================
 * Redesigned Source Detail Drawer (Task 1.11A).
 *
 * Implements:
 * - Level 2 Operational Detail: Source identity, verified URLs (no credentials),
 *   jurisdiction, polling cadence, and last check/success timestamps.
 * - Level 3 Technical Diagnostics: Recent runs, failure stack traces, and
 *   raw provenance metadata placed behind progressive disclosure.
 * - Safe manual poll action trigger.
 * - Accessible keyboard (Escape) and focus trap handling.
 */

"use client";

import React, { useEffect, useRef, useState } from "react";
import type { MonitoringSourceDetail } from "@/types/api";
import { SourceHealthBadge } from "./SourceHealthBadge";
import { ProvenanceStrip } from "./ProvenanceStrip";
import { Skeleton } from "@/components/ui/Skeleton";
import { monitoringApi } from "@/lib/api/monitoring";
import { cn } from "@/lib/utils";

interface SourceDetailDrawerProps {
  sourceId: string | null;
  data: MonitoringSourceDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return "Never recorded";
  try {
    return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function SourceDetailDrawer({ sourceId, data, loading, error, onClose }: SourceDetailDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const [polling, setPolling] = useState(false);
  const [pollResult, setPollResult] = useState<string | null>(null);

  // Close on Escape key
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  // Focus trap
  useEffect(() => {
    if (sourceId) drawerRef.current?.focus();
  }, [sourceId]);

  const handleTriggerPoll = async () => {
    if (polling) return;
    setPolling(true);
    setPollResult(null);
    try {
      const res = await monitoringApi.triggerCheck(sourceId ?? undefined);
      setPollResult(`Poll executed: ${res.status}`);
    } catch (e: unknown) {
      setPollResult(`Error: ${(e as Error).message ?? "Poll failed"}`);
    } finally {
      setPolling(false);
    }
  };

  if (!sourceId) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className="fixed right-0 top-0 h-full w-full max-w-lg bg-[var(--bg-card)] border-l border-[var(--border-strong)] z-50 overflow-y-auto shadow-2xl transition-colors"
        role="dialog"
        aria-modal="true"
        aria-label={`Source detail: ${data?.source_name ?? sourceId}`}
        tabIndex={-1}
      >
        {/* Header */}
        <div className="sticky top-0 bg-[var(--bg-card)]/95 backdrop-blur border-b border-[var(--border-hairline)] px-5 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">
              {loading ? "Loading source..." : (data?.source_name ?? sourceId)}
            </h2>
            {data && (
              <p className="text-xs text-[var(--text-faint)] font-mono mt-0.5">{data.source_id}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors p-1.5 rounded-lg hover:bg-[var(--bg-elevated)] focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Close source detail"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-5">
          {error ? (
            <div className="rounded-lg border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-xs font-mono" role="alert">
              <span className="font-semibold">⚠ Error loading source:</span> {error}
            </div>
          ) : loading || !data ? (
            <div aria-busy="true" className="space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12 rounded-lg" />
              ))}
            </div>
          ) : (
            <>
              {/* Level 1: Status & Jurisdiction Badges */}
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2 flex-wrap">
                  <SourceHealthBadge status={data.status} size="md" />
                  <span
                    className={cn(
                      "text-xs font-mono px-2 py-0.5 rounded border font-medium",
                      data.jurisdiction === "central"
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/25"
                        : "bg-purple-500/10 text-purple-400 border-purple-500/25"
                    )}
                  >
                    {data.jurisdiction === "central" ? "Central Parliament" : `State · ${data.state ?? ""}`}
                  </span>
                  <span className={cn("text-xs font-mono px-2 py-0.5 rounded border", data.enabled ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25" : "bg-slate-700/40 text-[var(--text-faint)] border-[var(--border-strong)]")}>
                    {data.enabled ? "Active" : "Disabled"}
                  </span>
                </div>

                <button
                  onClick={handleTriggerPoll}
                  disabled={polling}
                  className="px-2.5 py-1 text-xs font-mono bg-[var(--bg-elevated)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] rounded text-[var(--text-primary)] transition-colors disabled:opacity-50"
                  aria-label="Trigger safe poll for source"
                >
                  {polling ? "Polling..." : "▶ Safe Poll"}
                </button>
              </div>

              {pollResult && (
                <div className="p-2 rounded bg-[var(--bg-surface)] border border-[var(--border-hairline)] text-xs font-mono text-[var(--text-muted)]">
                  {pollResult}
                </div>
              )}

              {/* Level 2: Operational Identity & Schedule */}
              <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 space-y-2">
                <h3 className="text-xs font-semibold text-[var(--text-faint)] font-mono uppercase tracking-wider mb-2">
                  Source Configuration
                </h3>
                <dl className="space-y-2 text-xs">
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1.5">
                    <dt className="text-[var(--text-faint)] font-mono">Source ID</dt>
                    <dd className="text-[var(--text-primary)] font-mono font-medium">{data.source_id}</dd>
                  </div>
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1.5">
                    <dt className="text-[var(--text-faint)] font-mono">Parser / Ingestion Type</dt>
                    <dd className="text-[var(--text-secondary)] font-mono">{data.source_type}</dd>
                  </div>
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1.5">
                    <dt className="text-[var(--text-faint)] font-mono">Verified Portal URL</dt>
                    <dd className="text-blue-400 font-mono truncate max-w-[240px]">
                      {data.source_url ? (
                        <a href={data.source_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                          {data.source_url}
                        </a>
                      ) : (
                        <span className="text-[var(--text-faint)]">Unavailable</span>
                      )}
                    </dd>
                  </div>
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1.5">
                    <dt className="text-[var(--text-faint)] font-mono">Polling Cadence</dt>
                    <dd className="text-[var(--text-primary)] font-mono font-bold">{data.polling_interval_hours} hours</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-[var(--text-faint)] font-mono">Priority Weight</dt>
                    <dd className="text-[var(--text-primary)] font-mono">{data.priority}</dd>
                  </div>
                </dl>
              </div>

              {/* Level 2: Surveillance Timestamps */}
              <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 space-y-2">
                <h3 className="text-xs font-semibold text-[var(--text-faint)] font-mono uppercase tracking-wider mb-2">
                  Surveillance Timestamps
                </h3>
                <dl className="space-y-2 text-xs">
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1.5">
                    <dt className="text-[var(--text-faint)] font-mono">Last Checked</dt>
                    <dd className="text-[var(--text-primary)] font-mono">{formatTime(data.last_checked_at)}</dd>
                  </div>
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1.5">
                    <dt className="text-[var(--text-faint)] font-mono">Last Successful Parse</dt>
                    <dd className="text-emerald-400 font-mono font-medium">{formatTime(data.last_success_at)}</dd>
                  </div>
                  {data.last_error && (
                    <div className="space-y-1 pt-1">
                      <div className="flex justify-between text-rose-400 font-mono">
                        <dt>Last Error Timestamp</dt>
                        <dd>{formatTime(data.last_error_at)}</dd>
                      </div>
                      <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono text-[11px] break-words">
                        {data.last_error}
                      </div>
                    </div>
                  )}
                </dl>
              </div>

              {/* Notes */}
              {data.notes && (
                <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] p-3 text-xs text-[var(--text-muted)]">
                  <span className="font-semibold text-[var(--text-secondary)] font-mono">Operational Note: </span>
                  {data.notes}
                </div>
              )}

              {/* Level 3: Technical Diagnostics & Raw Traces */}
              <details className="group rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 text-xs font-mono">
                <summary className="font-semibold uppercase tracking-wider text-[var(--text-faint)] cursor-pointer list-none flex items-center justify-between select-none">
                  <span>Technical Diagnostics & Recent Runs</span>
                  <span className="text-[var(--text-muted)] group-open:rotate-180 transition-transform">▼</span>
                </summary>

                <div className="mt-4 pt-3 border-t border-[var(--border-hairline)] space-y-3">
                  {data.recent_run_results && data.recent_run_results.length > 0 ? (
                    <div className="space-y-1.5">
                      <div className="text-[11px] text-[var(--text-faint)] uppercase">Recent Run History</div>
                      {data.recent_run_results.slice(0, 5).map((r: Record<string, unknown>, i) => (
                        <div key={i} className="p-2 rounded bg-[var(--bg-surface)] border border-[var(--border-hairline)] flex items-center justify-between text-[11px]">
                          <span className="text-[var(--text-muted)]">{formatTime(r.started_at as string)}</span>
                          <span className={cn("font-bold", r.status === "SUCCESS" ? "text-emerald-400" : "text-rose-400")}>
                            {String(r.status)}
                          </span>
                          <span className="text-[var(--text-faint)]">
                            +{Number(r.new_bills ?? 0)} new · {Number(r.changed_bills ?? 0)} diff
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-[var(--text-faint)] text-[11px]">No recent runs recorded for this source.</div>
                  )}

                  {data.provenance && (
                    <div className="space-y-1 pt-2 border-t border-[var(--border-hairline)]">
                      <div className="text-[11px] text-[var(--text-faint)] uppercase">Raw Provenance Payload</div>
                      <pre className="p-2.5 rounded bg-[var(--bg-surface)] border border-[var(--border-hairline)] text-[10px] text-[var(--text-muted)] overflow-x-auto">
                        {JSON.stringify(data.provenance, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </details>

              {/* Provenance Strip */}
              <ProvenanceStrip
                sourceId={data.source_id}
                verificationStatus={(data.provenance?.monitoring_system as string) ?? "SYSTEM_DETECTED"}
                documentId={data.source_id}
                jurisdiction={data.jurisdiction}
              />
            </>
          )}
        </div>
      </div>
    </>
  );
}
