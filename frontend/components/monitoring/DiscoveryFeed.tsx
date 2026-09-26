/**
 * components/monitoring/DiscoveryFeed.tsx
 * =========================================
 * Unified discovery feed combining newly discovered bills, changes,
 * and legislative updates. Links to /bills/[id], /companies/[id], /industry/[id].
 *
 * Uses the changes feed from monitoring as the discovery data source.
 * Filters: Central/State, source, change type, date range.
 */

"use client";

import React from "react";
import Link from "next/link";
import type { ChangeEventDetail, PaginatedResponse } from "@/types/api";
import { EpistemicLabel } from "./EpistemicLabel";
import { Skeleton } from "@/components/ui/Skeleton";
import { Pagination } from "@/components/ui/Pagination";

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

const EVENT_ICONS: Record<string, string> = {
  NEW_BILL: "🆕",
  STATUS_CHANGED: "🔄",
  METADATA_CHANGED: "✏",
  DATE_CHANGED: "📅",
  DOCUMENT_CHANGED: "📄",
  SOURCE_CHANGED: "🔗",
};

export function DiscoveryFeed({ data, loading, error, onPageChange, onEventClick }: DiscoveryFeedProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-rose-400 text-sm" role="alert">
        <span className="font-semibold">⚠ Failed to load discovery feed:</span> {error}
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div aria-busy="true" aria-label="Loading discovery feed">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl mb-2" />
        ))}
      </div>
    );
  }

  if (data.items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-10 text-center">
        <div className="text-3xl mb-3" aria-hidden="true">📡</div>
        <p className="text-slate-400 font-medium">No legislative discoveries yet.</p>
        <p className="text-slate-600 text-sm mt-2">
          The discovery feed populates as monitoring runs detect new or changed legislative records.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-xs text-slate-500">
        {data.total} discover{data.total !== 1 ? "ies" : "y"} · Page {data.page} of {data.pages}
      </div>

      <div role="feed" aria-label="Legislative discovery feed" className="space-y-2">
        {data.items.map((event) => (
          <article
            key={event.event_id}
            className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 hover:border-slate-700 hover:bg-slate-800/40 transition-all group"
            aria-label={`${event.event_type}: ${event.bill_title}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl shrink-0 mt-0.5" aria-hidden="true">
                {EVENT_ICONS[event.event_type] ?? "📋"}
              </span>

              <div className="flex-1 min-w-0">
                {/* Bill title — links to bill dossier */}
                <button
                  onClick={() => onEventClick(event)}
                  className="text-sm font-semibold text-slate-200 hover:text-blue-400 transition-colors text-left truncate w-full"
                >
                  {event.bill_title || event.bill_id}
                </button>

                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <EpistemicLabel status={event.epistemic_status as "OBSERVED" | "DERIVED"} showIcon={false} />

                  <span className={`text-xs font-medium ${
                    event.jurisdiction === "central" ? "text-blue-400" : "text-purple-400"
                  }`}>
                    {event.jurisdiction === "central"
                      ? "Central Parliament"
                      : `State${event.state ? ` · ${event.state}` : ""}`}
                  </span>

                  <span className="text-xs text-slate-600">·</span>
                  <span className="text-xs text-slate-500">{formatRelativeTime(event.detected_at)}</span>
                </div>

                {/* Navigation links */}
                <div className="flex items-center gap-3 mt-2 flex-wrap">
                  <Link
                    href={`/bills/${encodeURIComponent(event.bill_id)}`}
                    className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Bill Dossier →
                  </Link>

                  {/* State notice */}
                  {event.jurisdiction === "state" && (
                    <span className="text-xs text-amber-500/70 italic">
                      Economic intelligence only · No stock prediction
                    </span>
                  )}
                </div>
              </div>

              <div className="shrink-0 text-xs text-slate-600 group-hover:text-blue-400 transition-colors">
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
