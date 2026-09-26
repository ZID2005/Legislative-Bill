/**
 * components/monitoring/ChangeDetailDrawer.tsx
 * =============================================
 * Slide-in drawer for a single change event showing:
 * - BEFORE / AFTER values
 * - Epistemic label [OBSERVED] or [DERIVED]
 * - Provenance strip
 *
 * If previous value is unavailable, shows "Previous value unavailable."
 * Does NOT fabricate before-state.
 */

"use client";

import React, { useEffect, useRef } from "react";
import type { ChangeEventDetail } from "@/types/api";
import { EpistemicLabel } from "./EpistemicLabel";
import { ProvenanceStrip } from "./ProvenanceStrip";
import { Skeleton } from "@/components/ui/Skeleton";

interface ChangeDetailDrawerProps {
  eventId: string | null;
  data: ChangeEventDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

const EVENT_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  NEW_BILL: { label: "New Bill", color: "text-emerald-400" },
  STATUS_CHANGED: { label: "Status Changed", color: "text-amber-400" },
  METADATA_CHANGED: { label: "Metadata Changed", color: "text-blue-400" },
  DATE_CHANGED: { label: "Date Changed", color: "text-blue-400" },
  DOCUMENT_CHANGED: { label: "Document Changed", color: "text-purple-400" },
  SOURCE_CHANGED: { label: "Source Changed", color: "text-slate-400" },
  NO_CHANGE: { label: "No Change", color: "text-slate-500" },
  ERROR: { label: "Error", color: "text-rose-400" },
};

function ValueBlock({ label, value }: { label: string; value: unknown }) {
  const display = value == null
    ? <span className="italic text-slate-600">Unavailable</span>
    : typeof value === "object"
    ? <pre className="text-xs text-slate-300 whitespace-pre-wrap">{JSON.stringify(value, null, 2)}</pre>
    : <span className="text-slate-200">{String(value)}</span>;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">{label}</div>
      <div className="text-sm">{display}</div>
    </div>
  );
}

export function ChangeDetailDrawer({ eventId, data, loading, error, onClose }: ChangeDetailDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    if (eventId) drawerRef.current?.focus();
  }, [eventId]);

  if (!eventId) return null;

  const eventType = data?.event_type ?? "";
  const typeCfg = EVENT_TYPE_LABELS[eventType] ?? { label: eventType, color: "text-slate-400" };

  return (
    <>
      <div className="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div
        ref={drawerRef}
        className="fixed right-0 top-0 h-full w-full max-w-lg bg-slate-900 border-l border-slate-700 z-50 overflow-y-auto shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-label={`Change event detail: ${data?.bill_title ?? eventId}`}
        tabIndex={-1}
      >
        {/* Header */}
        <div className="sticky top-0 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-5 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              {loading ? "Loading change..." : (data?.bill_title || "Change Event")}
            </h2>
            {data && (
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs font-semibold ${typeCfg.color}`}>{typeCfg.label}</span>
                {data.epistemic_status && (
                  <EpistemicLabel status={data.epistemic_status as "OBSERVED" | "DERIVED"} />
                )}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1.5 rounded-lg hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Close change detail"
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
              {/* Bill identity */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Bill Identity</h3>
                <dl className="space-y-1 text-sm">
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-28 shrink-0">Bill ID</dt>
                    <dd className="text-slate-300 font-mono text-xs">{data.bill_id}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-slate-500 w-28 shrink-0">Jurisdiction</dt>
                    <dd className="text-slate-300 capitalize">{data.jurisdiction}</dd>
                  </div>
                  {data.state && (
                    <div className="flex gap-2">
                      <dt className="text-slate-500 w-28 shrink-0">State</dt>
                      <dd className="text-slate-300">{data.state}</dd>
                    </div>
                  )}
                  {data.field_name && (
                    <div className="flex gap-2">
                      <dt className="text-slate-500 w-28 shrink-0">Changed Field</dt>
                      <dd className="text-slate-300 font-mono">{data.field_name}</dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* BEFORE / AFTER */}
              <div>
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
                  Change Detail
                </h3>
                <div className="space-y-2">
                  <ValueBlock
                    label={data.previous_version_available ? "Before" : "Before (Unavailable)"}
                    value={data.old_value}
                  />
                  <div className="flex items-center justify-center text-slate-600 text-sm">↓</div>
                  <ValueBlock
                    label={data.current_version_available ? "After" : "After (Unavailable)"}
                    value={data.new_value}
                  />
                </div>
                {!data.previous_version_available && (
                  <p className="text-xs text-amber-400/80 mt-2 italic">
                    Previous value unavailable — this bill may be newly discovered.
                  </p>
                )}
              </div>

              {/* Confidence */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-2 flex items-center justify-between text-sm">
                <span className="text-slate-500">Detection Confidence</span>
                <span className="font-semibold text-slate-200">{(data.confidence * 100).toFixed(0)}%</span>
              </div>

              {/* Bill link */}
              {data.bill_id && (
                <a
                  href={`/bills/${encodeURIComponent(data.bill_id)}`}
                  className="block rounded-lg border border-blue-500/20 bg-blue-500/5 px-4 py-2.5 text-sm text-blue-400 hover:bg-blue-500/10 transition-colors text-center"
                >
                  View Bill Dossier →
                </a>
              )}

              {/* Provenance */}
              <ProvenanceStrip
                sourceId={data.source_id}
                sourceReference={data.source_reference}
                detectedAt={data.detected_at}
                verificationStatus={(data.provenance?.verification_status as string) ?? "SYSTEM_DETECTED"}
                documentId={data.bill_id}
                jurisdiction={data.jurisdiction}
              />
            </>
          )}
        </div>
      </div>
    </>
  );
}
