/**
 * components/monitoring/SourceDetailDrawer.tsx
 * =============================================
 * Slide-in drawer showing full source detail including:
 * - Source identity and URL (no credentials exposed)
 * - Monitoring status and schedule
 * - Last check, last success, last error
 * - Recent run results
 * - Provenance
 */

"use client";

import React, { useEffect, useRef } from "react";
import type { MonitoringSourceDetail } from "@/types/api";
import { SourceHealthBadge } from "./SourceHealthBadge";
import { ProvenanceStrip } from "./ProvenanceStrip";
import { Skeleton } from "@/components/ui/Skeleton";

interface SourceDetailDrawerProps {
  sourceId: string | null;
  data: MonitoringSourceDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return "Never";
  try {
    return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function SourceDetailDrawer({ sourceId, data, loading, error, onClose }: SourceDetailDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

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
        className="fixed right-0 top-0 h-full w-full max-w-lg bg-slate-900 border-l border-slate-700 z-50 overflow-y-auto shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-label={`Source detail: ${data?.source_name ?? sourceId}`}
        tabIndex={-1}
      >
        {/* Header */}
        <div className="sticky top-0 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-5 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              {loading ? "Loading source..." : (data?.source_name ?? sourceId)}
            </h2>
            {data && (
              <p className="text-xs text-slate-500 font-mono mt-0.5">{data.source_id}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1.5 rounded-lg hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Close source detail"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-5">
          {error ? (
            <div className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
              <span className="font-semibold">⚠ Error:</span> {error}
            </div>
          ) : loading || !data ? (
            <div aria-busy="true">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 rounded-lg mb-2" />
              ))}
            </div>
          ) : (
            <>
              {/* Status row */}
              <div className="flex items-center gap-3 flex-wrap">
                <SourceHealthBadge status={data.status} size="md" />
                <span
                  className={`text-xs px-2 py-1 rounded border ${
                    data.jurisdiction === "central"
                      ? "bg-blue-500/10 text-blue-400 border-blue-500/25"
                      : "bg-purple-500/10 text-purple-400 border-purple-500/25"
                  }`}
                >
                  {data.jurisdiction === "central" ? "🏛 Central" : "🗳 State"}{data.state ? ` · ${data.state}` : ""}
                </span>
                <span className={`text-xs px-2 py-1 rounded border ${data.enabled ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25" : "bg-slate-700/40 text-slate-500 border-slate-700"}`}>
                  {data.enabled ? "Enabled" : "Disabled"}
                </span>
              </div>

              {/* Identity */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-2">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Source Identity</h3>
                <dl className="space-y-1.5 text-sm">
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-32 shrink-0">Source ID</dt>
                    <dd className="text-slate-300 font-mono text-xs">{data.source_id}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-32 shrink-0">Source Type</dt>
                    <dd className="text-slate-300">{data.source_type}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-32 shrink-0">URL / Domain</dt>
                    <dd className="text-blue-400 text-xs break-all">
                      {data.source_url
                        ? <a href={data.source_url} target="_blank" rel="noopener noreferrer" className="hover:underline">{data.source_url}</a>
                        : "Unavailable"}
                    </dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-32 shrink-0">Polling Interval</dt>
                    <dd className="text-slate-300">{data.polling_interval_hours}h</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-32 shrink-0">Priority</dt>
                    <dd className="text-slate-300">{data.priority}</dd>
                  </div>
                </dl>
              </div>

              {/* Check history */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-2">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Check History</h3>
                <dl className="space-y-1.5 text-sm">
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-32 shrink-0">Last Checked</dt>
                    <dd className="text-slate-300">{formatTime(data.last_checked_at)}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-32 shrink-0">Last Success</dt>
                    <dd className="text-slate-300">{formatTime(data.last_success_at)}</dd>
                  </div>
                  {data.last_error && (
                    <>
                      <div className="flex gap-2">
                        <dt className="text-slate-500 w-32 shrink-0">Last Error</dt>
                        <dd className="text-rose-400">{formatTime(data.last_error_at)}</dd>
                      </div>
                      <div className="flex gap-2">
                        <dt className="text-slate-500 w-32 shrink-0">Error Detail</dt>
                        <dd className="text-rose-400 text-xs">{data.last_error}</dd>
                      </div>
                    </>
                  )}
                </dl>
              </div>

              {/* Recent run results */}
              {data.recent_run_results.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Recent Runs</h3>
                  <div className="space-y-2">
                    {data.recent_run_results.slice(0, 5).map((r: Record<string, unknown>, i) => (
                      <div key={i} className="rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2 flex items-center justify-between text-xs">
                        <div className="text-slate-400">{formatTime(r.started_at as string)}</div>
                        <span className={`font-semibold ${r.status === "SUCCESS" ? "text-emerald-400" : "text-rose-400"}`}>
                          {r.status as string}
                        </span>
                        <div className="text-slate-500">
                          {Number(r.new_bills ?? 0)} new · {Number(r.changed_bills ?? 0)} changed
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              {data.notes && (
                <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">Notes: </span>{data.notes}
                </div>
              )}

              {/* Provenance */}
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
