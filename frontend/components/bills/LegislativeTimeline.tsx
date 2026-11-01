/**
 * components/bills/LegislativeTimeline.tsx
 * =========================================
 * Task 8.27 Phase 3 — Chronological Legislative Event Timeline.
 *
 * Renders meaningful, evidence-backed procedural stages:
 * DISCOVERED, INTRODUCED, REFERRED, COMMITTEE_REVIEW, PASSED, ASSENT, NOTIFIED, UPDATED, SUPERSEDED, WITHDRAWN.
 *
 * Invariant: Only displays stages supported by official evidence.
 * Never infers or speculates about future/unverified stages.
 */

"use client";

import React from "react";
import type { TimelineEventItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";

export interface LegislativeTimelineProps {
  timeline: TimelineEventItem[];
  className?: string;
}

export function LegislativeTimeline({
  timeline,
  className = "",
}: LegislativeTimelineProps) {
  if (!timeline || timeline.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Legislative Timeline</CardTitle>
            <Badge variant="slate" size="xs">
              EVIDENCE-GROUNDED
            </Badge>
          </div>
        </CardHeader>
        <p className="text-xs text-[var(--text-muted)] p-4">
          No authoritative procedural milestones recorded yet for this legislative measure.
        </p>
      </Card>
    );
  }

  const getStageBadgeVariant = (stage: string) => {
    switch (stage) {
      case "ASSENT":
      case "NOTIFIED":
        return "emerald";
      case "PASSED":
        return "blue";
      case "INTRODUCED":
      case "REFERRED":
      case "COMMITTEE_REVIEW":
        return "amber";
      case "WITHDRAWN":
      case "SUPERSEDED":
        return "rose";
      default:
        return "slate";
    }
  };

  const getStageIcon = (stage: string) => {
    switch (stage) {
      case "DISCOVERED":
        return "🔍";
      case "INTRODUCED":
        return "📥";
      case "REFERRED":
      case "COMMITTEE_REVIEW":
        return "⚖️";
      case "PASSED":
        return "🏛️";
      case "ASSENT":
        return "🖋️";
      case "NOTIFIED":
        return "📜";
      case "UPDATED":
        return "🔄";
      case "WITHDRAWN":
        return "🚫";
      case "SUPERSEDED":
        return "⏭️";
      default:
        return "📌";
    }
  };

  return (
    <Card className={className} id="legislative-timeline-section">
      <CardHeader>
        <div className="flex items-center justify-between w-full flex-wrap gap-2">
          <div>
            <CardTitle>Legislative Timeline</CardTitle>
            <p className="text-[11px] text-[var(--text-faint)] mt-0.5">
              Chronological milestones verified from official gazette, parliamentary, and assembly records.
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <Badge variant="slate" size="xs">
              {timeline.length} VERIFIED STAGES
            </Badge>
            <span className="text-[10px] text-[var(--text-faint)] font-mono">
              ZERO INFERRED DATES
            </span>
          </div>
        </div>
      </CardHeader>

      <div className="p-4 sm:p-5">
        <ol className="relative border-l border-[var(--border-default)] ml-3 space-y-6">
          {timeline.map((event, idx) => {
            const variant = getStageBadgeVariant(event.stage);
            const icon = getStageIcon(event.stage);

            return (
              <li key={event.event_id || idx} className="mb-6 ml-6 last:mb-0">
                {/* Node icon circle */}
                <span className="absolute -left-3.5 flex items-center justify-center w-7 h-7 rounded-full bg-[var(--bg-card)] border border-[var(--border-strong)] text-xs shadow-md">
                  {icon}
                </span>

                <div className="p-3.5 rounded-lg border border-[var(--border-default)]/80 bg-[var(--bg-card)]/40 hover:bg-[var(--bg-card)]/70 transition-colors space-y-2">
                  {/* Top row: Stage label + Date + Evidence Badge */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-[var(--text-primary)]">
                        {event.stage_label || event.stage}
                      </span>
                      <Badge variant={variant} size="xs">
                        {event.stage}
                      </Badge>
                    </div>
                    <span className="text-xs font-mono font-medium text-[var(--text-muted)]">
                      {event.date ? formatDate(event.date) : "Official date unnotified"}
                    </span>
                  </div>

                  {/* Description */}
                  {event.description && (
                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                      {event.description}
                    </p>
                  )}

                  {/* Metadata footer: source authority, chamber, document reference */}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-[var(--text-faint)] pt-1 border-t border-[var(--border-default)]/60">
                    <div>
                      <span className="text-slate-600">Authority:</span>{" "}
                      <span className="text-[var(--text-muted)]">{event.source_authority}</span>
                    </div>
                    {event.chamber && (
                      <div>
                        <span className="text-slate-600">Chamber:</span>{" "}
                        <span className="text-[var(--text-muted)]">{event.chamber}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-600">Evidence:</span>{" "}
                      <span className="text-emerald-400 font-mono text-[10px]">
                        ✓ {event.evidence_type}
                      </span>
                    </div>
                    {event.document_url && (
                      <a
                        href={event.document_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline inline-flex items-center gap-1 text-[10px]"
                      >
                        Official Document ↗
                      </a>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </Card>
  );
}
