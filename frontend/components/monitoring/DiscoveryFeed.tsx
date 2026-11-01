/**
 * components/monitoring/DiscoveryFeed.tsx
 * =========================================
 * Redesigned Legislative Discovery Feed (Task 1.11A).
 *
 * Implements:
 * - Scannable cards with hairline dividers
 * - Strict Central vs State statutory firewall reminders
 * - Epistemic status labels ([OBSERVED] or [DERIVED])
 * - Direct deep links to canonical Bill Dossiers
 */

"use client";

import React from "react";
import Link from "next/link";
import type { ChangeEventDetail, PaginatedResponse } from "@/types/api";
import { EpistemicLabel } from "./EpistemicLabel";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";
import { cn } from "@/lib/utils";

interface DiscoveryFeedProps {
  data: PaginatedResponse<ChangeEventDetail> | null;
  loading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
  onEventClick: (event: ChangeEventDetail) => void;
}

function formatRelativeTime(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return iso;
  }
}

const EVENT_GLYPHS: Record<string, string> = {
  NEW_BILL: "📋",
  STATUS_CHANGED: "🔄",
  METADATA_CHANGED: "✏",
  DATE_CHANGED: "📅",
  DOCUMENT_CHANGED: "📄",
  SOURCE_CHANGED: "🔗",
};

export function DiscoveryFeed({ data, loading, error, onPageChange, onEventClick }: DiscoveryFeedProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-[var(--color-error-border)] bg-[var(--color-error-bg)] p-4 text-[var(--color-error)] text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load discovery feed:</span> {error}
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div aria-busy="true" aria-label="Loading discovery feed" className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    );
  }

  if (data.items.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-10 text-center space-y-2">
        <p className="text-[var(--text-faint)] text-xs font-mono">No legislative discoveries yet.</p>
        <p className="text-[var(--text-muted)] text-[11px]">
          The discovery feed automatically populates when continuous surveillance detects newly gazetted enactments.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-xs text-[var(--text-faint)] font-mono flex items-center justify-between">
        <span>{data.total} discover{data.total !== 1 ? "ies" : "y"} · Page {data.page} of {data.pages}</span>
        <span>Real-time Ingestion Stream</span>
      </div>

      <div role="feed" aria-label="Legislative discovery feed" className="space-y-2.5">
        {data.items.map((event) => (
          <article
            key={event.event_id}
            className="rounded-xl border border-[var(--border-hairline)] bg-[var(--bg-card)] p-4 hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-all group select-none"
            aria-label={`${event.event_type}: ${event.bill_title || event.bill_id}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-base shrink-0 mt-0.5 text-[var(--text-muted)]" aria-hidden="true">
                {EVENT_GLYPHS[event.event_type] ?? "📋"}
              </span>

              <div className="flex-1 min-w-0 space-y-1">
                {/* Bill title — clickable to inspect */}
                <button
                  onClick={() => onEventClick(event)}
                  className="text-sm font-semibold text-[var(--text-primary)] hover:text-blue-400 transition-colors text-left truncate w-full"
                >
                  {event.bill_title || event.bill_id}
                </button>

                <div className="flex items-center gap-2 flex-wrap text-xs">
                  <EpistemicLabel status={event.epistemic_status as "OBSERVED" | "DERIVED"} showIcon={false} />

                  <span className={cn(
                    "font-mono font-medium",
                    event.jurisdiction === "central" ? "text-blue-400" : "text-purple-400"
                  )}>
                    {event.jurisdiction === "central"
                      ? "Central Parliament"
                      : `State${event.state ? ` · ${event.state}` : ""}`}
                  </span>

                  <span className="text-[var(--text-faint)]">·</span>
                  <span className="text-[var(--text-faint)] font-mono">{formatRelativeTime(event.detected_at)}</span>
                </div>

                {/* Deep Navigation Links & Firewall Notice */}
                <div className="flex items-center gap-3 pt-1 flex-wrap">
                  <Link
                    href={`/bills/${encodeURIComponent(event.bill_id)}`}
                    className="text-xs font-mono font-medium text-blue-400 hover:text-blue-300 transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Bill Dossier →
                  </Link>

                  {event.jurisdiction === "state" && (
                    <span className="text-xs font-mono text-amber-400/90 italic">
                      Economic intelligence only · No stock prediction
                    </span>
                  )}
                </div>
              </div>

              <div className="shrink-0 text-xs font-mono text-[var(--text-muted)] group-hover:text-blue-400 transition-colors">
                {event.event_type.replace(/_/g, " ")}
              </div>
            </div>
          </article>
        ))}
      </div>

      {data.pages > 1 && (
        <Pagination
          page={data.page}
          pages={data.pages}
          total={data.total}
          limit={25}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}
