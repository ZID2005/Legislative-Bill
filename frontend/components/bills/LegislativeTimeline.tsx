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
        <p className="text-xs text-slate-400 p-4">
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
            <p className="text-[11px] text-slate-500 mt-0.5">
              Chronological milestones verified from official gazette, parliamentary, and assembly records.
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <Badge variant="slate" size="xs">
              {timeline.length} VERIFIED STAGES
            </Badge>
            <span className="text-[10px] text-slate-500 font-mono">
              ZERO INFERRED DATES
            </span>
          </div>
        </div>
      </CardHeader>

      <div className="p-4 sm:p-5">
        <ol className="relative border-l border-slate-800 ml-3 space-y-6">
          {timeline.map((event, idx) => {
            const variant = getStageBadgeVariant(event.stage);
            const icon = getStageIcon(event.stage);

            return (
              <li key={event.event_id || idx} className="mb-6 ml-6 last:mb-0">
                {/* Node icon circle */}
                <span className="absolute -left-3.5 flex items-center justify-center w-7 h-7 rounded-full bg-slate-900 border border-slate-700 text-xs shadow-md">
                  {icon}
                </span>

                <div className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/40 hover:bg-slate-900/70 transition-colors space-y-2">
                  {/* Top row: Stage label + Date + Evidence Badge */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-100">
                        {event.stage_label || event.stage}
                      </span>
                      <Badge variant={variant} size="xs">
                        {event.stage}
                      </Badge>
                    </div>
                    <span className="text-xs font-mono font-medium text-slate-400">
                      {event.date ? formatDate(event.date) : "Official date unnotified"}
                    </span>
                  </div>

                  {/* Description */}
                  {event.description && (
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {event.description}
                    </p>
                  )}

                  {/* Metadata footer: source authority, chamber, document reference */}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500 pt-1 border-t border-slate-800/60">
                    <div>
                      <span className="text-slate-600">Authority:</span>{" "}
                      <span className="text-slate-400">{event.source_authority}</span>
                    </div>
                    {event.chamber && (
                      <div>
                        <span className="text-slate-600">Chamber:</span>{" "}
                        <span className="text-slate-400">{event.chamber}</span>
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
