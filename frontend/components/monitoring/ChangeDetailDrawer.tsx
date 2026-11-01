/**
 * components/monitoring/ChangeDetailDrawer.tsx
 * =============================================
 * Redesigned Change Detail Drawer (Task 1.11A).
 *
 * Implements:
 * - Level 2 Operational Detail: Clear BEFORE / AFTER diff visualization
 * - Epistemic status label ([OBSERVED] or [DERIVED])
 * - Truthful handling of unavailable previous values (never fabricated)
 * - Level 3 Technical Diagnostics: Confidence score, detection metadata,
 *   raw payload diff behind progressive disclosure
 * - Deep link to canonical Bill Dossier (/bills/[billId])
 */

"use client";

import React, { useEffect, useRef } from "react";
import Link from "next/link";
import type { ChangeEventDetail } from "@/types/api";
import { EpistemicLabel } from "./EpistemicLabel";
import { ProvenanceStrip } from "./ProvenanceStrip";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

interface ChangeDetailDrawerProps {
  eventId: string | null;
  data: ChangeEventDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

const EVENT_TYPE_LABELS: Record<string, { label: string; colorClass: string }> = {
  NEW_BILL: { label: "New Bill Introduced", colorClass: "text-emerald-400" },
  STATUS_CHANGED: { label: "Status Changed", colorClass: "text-amber-400" },
  METADATA_CHANGED: { label: "Metadata Modified", colorClass: "text-blue-400" },
  DATE_CHANGED: { label: "Official Date Changed", colorClass: "text-blue-400" },
  DOCUMENT_CHANGED: { label: "Document Changed", colorClass: "text-purple-400" },
  SOURCE_CHANGED: { label: "Source Changed", colorClass: "text-[var(--text-muted)]" },
  NO_CHANGE: { label: "No Change", colorClass: "text-[var(--text-faint)]" },
  ERROR: { label: "Detection Error", colorClass: "text-rose-400" },
};

function ValueBlock({ label, value, isUnavailable }: { label: string; value: unknown; isUnavailable?: boolean }) {
  const display = isUnavailable || value == null ? (
    <span className="italic text-[var(--text-faint)] font-mono text-xs">
      Previous value unavailable (initial record introduction or snapshotting not applicable)
    </span>
  ) : typeof value === "object" ? (
    <pre className="text-xs font-mono text-[var(--text-secondary)] whitespace-pre-wrap overflow-x-auto p-2 rounded bg-[var(--bg-card)] border border-[var(--border-hairline)]">
      {JSON.stringify(value, null, 2)}
    </pre>
  ) : (
    <span className="text-[var(--text-primary)] font-mono text-xs font-medium">{String(value)}</span>
  );

  return (
    <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] p-3">
      <div className="text-[11px] font-mono font-semibold text-[var(--text-faint)] uppercase tracking-wider mb-1.5">
        {label}
      </div>
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
  const typeCfg = EVENT_TYPE_LABELS[eventType] ?? { label: eventType, colorClass: "text-[var(--text-muted)]" };

  return (
    <>
      <div className="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div
        ref={drawerRef}
        className="fixed right-0 top-0 h-full w-full max-w-lg bg-[var(--bg-card)] border-l border-[var(--border-strong)] z-50 overflow-y-auto shadow-2xl transition-colors"
        role="dialog"
        aria-modal="true"
        aria-label={`Change event detail: ${data?.bill_title ?? eventId}`}
        tabIndex={-1}
      >
        {/* Header */}
        <div className="sticky top-0 bg-[var(--bg-card)]/95 backdrop-blur border-b border-[var(--border-hairline)] px-5 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)] truncate max-w-[340px]">
              {loading ? "Loading change..." : (data?.bill_title || "Change Event")}
            </h2>
            {data && (
              <div className="flex items-center gap-2 mt-1">
                <span className={cn("text-xs font-mono font-bold", typeCfg.colorClass)}>{typeCfg.label}</span>
                {data.epistemic_status && (
                  <EpistemicLabel status={data.epistemic_status as "OBSERVED" | "DERIVED"} />
                )}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors p-1.5 rounded-lg hover:bg-[var(--bg-elevated)] focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Close change detail"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-5">
          {error ? (
            <div className="rounded-lg border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-xs font-mono" role="alert">
              <span className="font-semibold">⚠ Error:</span> {error}
            </div>
          ) : loading || !data ? (
            <div aria-busy="true" className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 rounded-lg" />
              ))}
            </div>
          ) : (
            <>
              {/* Level 2: Target Bill Identity */}
              <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-surface)] p-4 space-y-2">
                <h3 className="text-xs font-semibold text-[var(--text-faint)] font-mono uppercase tracking-wider mb-2">
                  Statutory Entity Identity
                </h3>
                <dl className="space-y-1.5 text-xs font-mono">
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1">
                    <dt className="text-[var(--text-faint)]">Bill ID</dt>
                    <dd className="text-[var(--text-primary)] font-semibold">{data.bill_id}</dd>
                  </div>
                  <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1">
                    <dt className="text-[var(--text-faint)]">Jurisdiction</dt>
                    <dd className="text-[var(--text-secondary)] capitalize">{data.jurisdiction}</dd>
                  </div>
                  {data.state && (
                    <div className="flex justify-between border-b border-[var(--border-hairline)] pb-1">
                      <dt className="text-[var(--text-faint)]">State Assembly</dt>
                      <dd className="text-[var(--text-secondary)]">{data.state}</dd>
                    </div>
                  )}
                  {data.field_name && (
                    <div className="flex justify-between">
                      <dt className="text-[var(--text-faint)]">Target Delta Field</dt>
                      <dd className="text-blue-400 font-bold">{data.field_name}</dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* Level 2: BEFORE vs. AFTER State Comparison */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-[var(--text-faint)] font-mono uppercase tracking-wider mb-2">
                  State Delta Transition
                </h3>
                <ValueBlock
                  label={data.previous_version_available ? "Before (Prior State)" : "Before (Unavailable)"}
                  value={data.old_value}
                  isUnavailable={!data.previous_version_available}
                />
                <div className="flex items-center justify-center text-[var(--text-faint)] text-xs font-mono">
                  ↓ DETECTED DELTA ↓
                </div>
                <ValueBlock
                  label={data.current_version_available ? "After (Current State)" : "After (Unavailable)"}
                  value={data.new_value}
                  isUnavailable={!data.current_version_available}
                />
                {!data.previous_version_available && (
                  <p className="text-[11px] text-[var(--text-muted)] italic font-mono px-1">
                    Previous value unavailable — this bill was newly ingested into the repository.
                  </p>
                )}
              </div>

              {/* Detection Confidence Strip */}
              <div className="rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-surface)] px-4 py-2.5 flex items-center justify-between text-xs font-mono">
                <span className="text-[var(--text-faint)]">Parser Confidence</span>
                <span className="font-bold text-emerald-400">{(data.confidence * 100).toFixed(0)}% Match</span>
              </div>

              {/* Canonical Bill Dossier Deep Link */}
              {data.bill_id && (
                <Link
                  href={`/bills/${encodeURIComponent(data.bill_id)}`}
                  className="block rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)] hover:bg-[var(--bg-card-hover)] px-4 py-2.5 text-xs font-mono font-medium text-blue-400 hover:text-blue-300 transition-colors text-center"
                >
                  View Canonical Bill Dossier →
                </Link>
              )}

              {/* Level 3: Technical Diagnostics & Raw Payload */}
              <details className="group rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 text-xs font-mono">
                <summary className="font-semibold uppercase tracking-wider text-[var(--text-faint)] cursor-pointer list-none flex items-center justify-between select-none">
                  <span>Technical Diagnostics & Raw Event Payload</span>
                  <span className="text-[var(--text-muted)] group-open:rotate-180 transition-transform">▼</span>
                </summary>

                <div className="mt-3 pt-3 border-t border-[var(--border-hairline)] space-y-2">
                  <div className="flex justify-between text-[11px] text-[var(--text-muted)]">
                    <span>Event ID:</span>
                    <span className="text-[var(--text-primary)]">{data.event_id}</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-[var(--text-muted)]">
                    <span>Source ID:</span>
                    <span className="text-[var(--text-primary)]">{data.source_id}</span>
                  </div>
                  {data.source_reference && (
                    <div className="flex justify-between text-[11px] text-[var(--text-muted)]">
                      <span>Source Ref:</span>
                      <span className="text-[var(--text-primary)]">{data.source_reference}</span>
                    </div>
                  )}
                  {data.provenance && (
                    <div className="space-y-1 pt-1">
                      <div className="text-[11px] text-[var(--text-faint)] uppercase">Provenance Metadata</div>
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
