/**
 * components/monitoring/ProvenanceStrip.tsx
 * ==========================================
 * Displays provenance information: source, timestamp, document identity,
 * verification status.
 *
 * Never fabricates provenance. If a field is unavailable, shows "Unavailable."
 */

import React from "react";
import { cn } from "@/lib/utils";

interface ProvenanceStripProps {
  sourceId?: string | null;
  sourceReference?: string | null;
  detectedAt?: string | null;
  verificationStatus?: string;
  documentId?: string | null;
  jurisdiction?: string | null;
  className?: string;
  compact?: boolean;
}

function formatTime(iso?: string | null): string {
  if (!iso) return "Unavailable";
  try {
    return new Date(iso).toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function ProvenanceStrip({
  sourceId,
  sourceReference,
  detectedAt,
  verificationStatus = "SYSTEM_DETECTED",
  documentId,
  jurisdiction,
  className = "",
  compact = false,
}: ProvenanceStripProps) {
  const verColor =
    verificationStatus === "VERIFIED"
      ? "text-emerald-400"
      : verificationStatus === "SYSTEM_DETECTED"
      ? "text-blue-400"
      : "text-amber-400";

  if (compact) {
    return (
      <div
        className={cn("flex items-center gap-2.5 text-xs text-[var(--text-faint)] font-mono flex-wrap", className)}
        role="note"
        aria-label="Provenance information"
      >
        <span title="Source identity" className="text-[var(--text-secondary)]">
          Source: {sourceId ?? "Unavailable"}
        </span>
        <span>·</span>
        <span title="Detection timestamp">Detected: {formatTime(detectedAt)}</span>
        {verificationStatus && (
          <>
            <span>·</span>
            <span className={cn("font-semibold", verColor)} title="Verification status">
              {verificationStatus}
            </span>
          </>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn("rounded-lg border border-[var(--border-hairline)] bg-[var(--bg-card)] p-3", className)}
      role="note"
      aria-label="Provenance information"
    >
      <div className="text-[11px] font-semibold font-mono text-[var(--text-faint)] uppercase tracking-wider mb-2">
        Provenance & Audit Trail
      </div>
      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 text-xs font-mono">
        <div className="flex items-start gap-1.5">
          <dt className="text-[var(--text-faint)] shrink-0">Source:</dt>
          <dd className="text-[var(--text-primary)] break-all font-medium">{sourceId ?? "Unavailable"}</dd>
        </div>
        {sourceReference && (
          <div className="flex items-start gap-1.5">
            <dt className="text-[var(--text-faint)] shrink-0">Reference:</dt>
            <dd className="text-[var(--text-secondary)] break-all truncate max-w-[200px]" title={sourceReference}>
              {sourceReference}
            </dd>
          </div>
        )}
        <div className="flex items-start gap-1.5">
          <dt className="text-[var(--text-faint)] shrink-0">Detected:</dt>
          <dd className="text-[var(--text-secondary)]">{formatTime(detectedAt)}</dd>
        </div>
        {documentId && (
          <div className="flex items-start gap-1.5">
            <dt className="text-[var(--text-faint)] shrink-0">Document:</dt>
            <dd className="text-[var(--text-secondary)]">{documentId}</dd>
          </div>
        )}
        {jurisdiction && (
          <div className="flex items-start gap-1.5">
            <dt className="text-[var(--text-faint)] shrink-0">Jurisdiction:</dt>
            <dd className="text-[var(--text-secondary)] capitalize">{jurisdiction}</dd>
          </div>
        )}
        <div className="flex items-start gap-1.5">
          <dt className="text-[var(--text-faint)] shrink-0">Verification:</dt>
          <dd className={cn("font-medium", verColor)}>{verificationStatus}</dd>
        </div>
      </dl>
    </div>
  );
}
