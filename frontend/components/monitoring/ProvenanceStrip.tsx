/**
 * components/monitoring/ProvenanceStrip.tsx
 * ==========================================
 * Displays provenance information: source, timestamp, document identity,
 * verification status.
 *
 * Never fabricates provenance. If a field is unavailable, shows "Unavailable."
 */

import React from "react";

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
      <div className={`flex items-center gap-3 text-xs text-slate-500 ${className}`} role="note" aria-label="Provenance information">
        <span title="Source">🔗 {sourceId ?? "Unknown source"}</span>
        <span>·</span>
        <span title="Detected at">🕐 {formatTime(detectedAt)}</span>
        {verificationStatus && (
          <>
            <span>·</span>
            <span className={verColor} title="Verification status">{verificationStatus}</span>
          </>
        )}
      </div>
    );
  }

  return (
    <div
      className={`rounded-lg border border-slate-800 bg-slate-900/50 p-3 ${className}`}
      role="note"
      aria-label="Provenance information"
    >
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
        Provenance
      </div>
      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="flex items-start gap-1">
          <dt className="text-slate-500 shrink-0">Source:</dt>
          <dd className="text-slate-300 break-all">{sourceId ?? "Unavailable"}</dd>
        </div>
        {sourceReference && (
          <div className="flex items-start gap-1">
            <dt className="text-slate-500 shrink-0">Reference:</dt>
            <dd className="text-slate-300 break-all truncate max-w-[200px]" title={sourceReference}>
              {sourceReference}
            </dd>
          </div>
        )}
        <div className="flex items-start gap-1">
          <dt className="text-slate-500 shrink-0">Detected:</dt>
          <dd className="text-slate-300">{formatTime(detectedAt)}</dd>
        </div>
        {documentId && (
          <div className="flex items-start gap-1">
            <dt className="text-slate-500 shrink-0">Document:</dt>
            <dd className="text-slate-300 font-mono">{documentId}</dd>
          </div>
        )}
        {jurisdiction && (
          <div className="flex items-start gap-1">
            <dt className="text-slate-500 shrink-0">Jurisdiction:</dt>
            <dd className="text-slate-300 capitalize">{jurisdiction}</dd>
          </div>
        )}
        <div className="flex items-start gap-1">
          <dt className="text-slate-500 shrink-0">Verification:</dt>
          <dd className={`${verColor} font-medium`}>{verificationStatus}</dd>
        </div>
      </dl>
    </div>
  );
}
