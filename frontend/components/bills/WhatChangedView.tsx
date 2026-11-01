/**
 * components/bills/WhatChangedView.tsx
 * =====================================
 * Task 8.27 Phase 4 — "What Changed?" Structured Change Summary.
 *
 * Clearly distinguishes:
 * - DOCUMENT CHANGE (e.g. PDF hash update, file re-download, document link update)
 * - LEGISLATIVE STATUS CHANGE (e.g. statutory status transition, title amendment, procedural reading)
 *
 * Strict Guardrail:
 * Does not claim a substantive legislative change merely because PDF metadata or file size changed.
 */

"use client";

import React, { useState } from "react";
import type { BillChangeSummary } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";

export interface WhatChangedViewProps {
  changeSummary?: BillChangeSummary | null;
  changes?: BillChangeSummary | null;
  className?: string;
}

export function WhatChangedView({
  changeSummary,
  changes,
  className = "",
}: WhatChangedViewProps) {
  const activeSummary = changes || changeSummary;
  const [filterType, setFilterType] = useState<"all" | "legislative" | "document">("all");

  const {
    has_changes,
    total_changes,
    last_change_detected_at,
    document_changes = [],
    legislative_changes = [],
    summary_text,
    separation_notice,
  } = activeSummary || {};

  const filteredDocChanges = filterType === "legislative" ? [] : document_changes;
  const filteredLegChanges = filterType === "document" ? [] : legislative_changes;

  return (
    <Card className={className} id="what-changed-section">
      <CardHeader>
        <div className="flex items-center justify-between w-full flex-wrap gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>What Changed?</CardTitle>
              {has_changes ? (
                <Badge variant="amber" size="xs">
                  {total_changes} REVISIONS DETECTED
                </Badge>
              ) : (
                <Badge variant="emerald" size="xs">
                  BASELINE UNMODIFIED
                </Badge>
              )}
            </div>
            <p className="text-[11px] text-[var(--text-faint)] mt-0.5">
              Structured audit trail distinguishing document-level revisions from legislative status changes.
            </p>
          </div>

          {/* Filter Pills */}
          {has_changes && (
            <div className="flex items-center gap-1 bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-0.5 text-xs">
              <button
                onClick={() => setFilterType("all")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  filterType === "all"
                    ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                All ({total_changes})
              </button>
              <button
                onClick={() => setFilterType("legislative")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  filterType === "legislative"
                    ? "bg-blue-900/60 text-blue-200 shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Legislative ({legislative_changes.length})
              </button>
              <button
                onClick={() => setFilterType("document")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  filterType === "document"
                    ? "bg-amber-900/60 text-amber-200 shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Documents ({document_changes.length})
              </button>
            </div>
          )}
        </div>
      </CardHeader>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Summary Banner */}
        <div className="p-3 rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/50 flex items-start gap-3">
          <span className="text-lg">ℹ️</span>
          <div className="space-y-1 text-xs">
            <p className="text-[var(--text-primary)] leading-relaxed font-medium">
              {summary_text || "No modifications recorded since baseline catalog ingestion."}
            </p>
            {last_change_detected_at && (
              <p className="text-[11px] text-[var(--text-faint)] font-mono">
                Latest verified change detected: {formatDate(last_change_detected_at)}
              </p>
            )}
          </div>
        </div>

        {/* Epistemic Architecture Separation Banner */}
        <div className="p-3 rounded-lg border border-blue-950/60 bg-blue-950/20 text-xs text-blue-300 leading-relaxed">
          <strong className="text-blue-200 uppercase tracking-wide text-[10px] block mb-0.5">
            Strict Epistemic Separation Rule
          </strong>
          {separation_notice ||
            "DOCUMENT CHANGE vs LEGISLATIVE STATUS CHANGE: Document-level modifications (such as PDF re-indexing, hash updates, or URL formatting) are tracked separately from formal legislative status transitions. A document metadata change is never presented as a substantive statutory enactment."}
        </div>

        {/* Changes Lists */}
        {has_changes ? (
          <div className="space-y-4">
            {/* Legislative Changes Section */}
            {filteredLegChanges.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
                  Legislative Status & Procedural Changes ({filteredLegChanges.length})
                </h4>
                <div className="space-y-2">
                  {filteredLegChanges.map((lc, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-blue-900/40 bg-[var(--bg-card)]/40 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-[var(--text-primary)]">
                            Field: <span className="font-mono text-blue-300">{lc.field_name}</span>
                          </span>
                          <Badge variant="blue" size="xs">
                            {lc.change_type}
                          </Badge>
                        </div>
                        <span className="text-[11px] text-[var(--text-muted)] font-mono">
                          {formatDate(lc.detected_at)}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1 border-t border-[var(--border-default)]">
                        <div>
                          <span className="text-[var(--text-faint)]">Previous Value:</span>{" "}
                          <span className="text-[var(--text-muted)] font-mono">{lc.old_value || "—"}</span>
                        </div>
                        <div>
                          <span className="text-[var(--text-faint)]">Updated Value:</span>{" "}
                          <span className="text-emerald-400 font-mono font-medium">{lc.new_value || "—"}</span>
                        </div>
                      </div>
                      <p className="text-[11px] text-[var(--text-muted)]">
                        Authority: <span className="text-[var(--text-secondary)]">{lc.source_authority}</span>
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Document Changes Section */}
            {filteredDocChanges.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  Official Document & Hash Changes ({filteredDocChanges.length})
                </h4>
                <div className="space-y-2">
                  {filteredDocChanges.map((dc, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-amber-900/40 bg-[var(--bg-card)]/40 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-[var(--text-primary)]">
                            Document Binary Modified
                          </span>
                          <Badge variant="amber" size="xs">
                            {dc.change_type}
                          </Badge>
                        </div>
                        <span className="text-[11px] text-[var(--text-muted)] font-mono">
                          {formatDate(dc.detected_at)}
                        </span>
                      </div>
                      <div className="text-[11px] space-y-1 pt-1 border-t border-[var(--border-default)]">
                        {dc.previous_hash && (
                          <div className="font-mono text-[var(--text-muted)] truncate">
                            <span className="text-[var(--text-faint)]">Previous SHA-256:</span> {dc.previous_hash}
                          </div>
                        )}
                        {dc.new_hash && (
                          <div className="font-mono text-emerald-400 truncate">
                            <span className="text-[var(--text-faint)]">Verified New SHA-256:</span> {dc.new_hash}
                          </div>
                        )}
                      </div>
                      <p className="text-[11px] text-[var(--text-muted)] italic">
                        {dc.notes}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-6 border border-dashed border-[var(--border-default)] rounded-lg text-[var(--text-muted)] text-xs">
            No document or procedural alterations detected. The legislative record remains at its authoritative initial baseline.
          </div>
        )}
      </div>
    </Card>
  );
}
