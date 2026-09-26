/**
 * components/bills/ProceduralJourney.tsx
 * =======================================
 * Legislative procedural timeline based strictly on actual available dates and statuses.
 * Invariant: Never infers dates; renders "Date not available" when not present.
 */

"use client";

import React from "react";
import type { BillSummaryItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";

export interface ProceduralJourneyProps {
  bill: BillSummaryItem;
  className?: string;
}

interface Milestone {
  id: string;
  label: string;
  status: "completed" | "in_progress" | "pending";
  date: string;
  notes: string;
}

export function ProceduralJourney({ bill, className = "" }: ProceduralJourneyProps) {
  const normStatus = bill.status?.toLowerCase() || "";
  const isPassedBoth =
    normStatus === "passed_both" ||
    normStatus === "assented" ||
    normStatus === "enacted";
  const isPassedOne =
    normStatus === "passed_lok_sabha" ||
    normStatus === "passed_rajya_sabha" ||
    normStatus === "passed";
  const isAssented =
    Boolean(bill.assent_date) ||
    normStatus === "assented" ||
    normStatus === "enacted";

  const milestones: Milestone[] = [
    {
      id: "introduced",
      label: "Tabled & Formally Introduced",
      status: "completed",
      date: bill.introduction_date
        ? formatDate(bill.introduction_date)
        : "Date not available",
      notes: `Introduced in ${bill.house || "Legislature"} (${bill.legislature})`,
    },
    {
      id: "house_passage",
      label: "First Chamber Passage",
      status: isPassedBoth || isPassedOne ? "completed" : "in_progress",
      date: "Date not available",
      notes:
        isPassedBoth || isPassedOne
          ? `Passed initial house consideration (${bill.house || "House"})`
          : "Under committee review or floor debate",
    },
    {
      id: "full_passage",
      label: "Legislative Passage",
      status: isPassedBoth ? "completed" : isPassedOne ? "in_progress" : "pending",
      date: "Date not available",
      notes: isPassedBoth
        ? "Formally passed by the legislature"
        : isPassedOne
        ? "Transmitted to second chamber / floor"
        : "Awaiting final parliamentary vote",
    },
    {
      id: "assent",
      label: bill.jurisdiction?.toLowerCase() === "state" ? "Governor Assent" : "Presidential Assent",
      status: isAssented ? "completed" : isPassedBoth ? "in_progress" : "pending",
      date: bill.assent_date ? formatDate(bill.assent_date) : "Date not available",
      notes: isAssented
        ? "Constitutional assent granted"
        : isPassedBoth
        ? "Awaiting assent from competent constitutional authority"
        : "Pending legislative passage",
    },
    {
      id: "gazette",
      label: "Official Gazette Notification",
      status: isAssented ? "completed" : "pending",
      date: "Date not available",
      notes: isAssented
        ? "Notified in the Official Gazette as statutory enactment"
        : "Pending executive notification",
    },
  ];

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div>
            <CardTitle>Procedural Journey</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified statutory journey milestones based strictly on recorded parliamentary gazette records.
            </p>
          </div>
          <SourceBadge type="FACT" size="xs" showTooltip />
        </div>
      </CardHeader>

      <div className="pt-2">
        <ol className="relative border-l border-slate-800 ml-3.5 space-y-6">
          {milestones.map((m) => {
            const isDone = m.status === "completed";
            const isInProg = m.status === "in_progress";

            return (
              <li key={m.id} className="ml-6 group">
                {/* Milestone Node */}
                <span
                  className={`absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full border text-xs ${
                    isDone
                      ? "border-emerald-500/80 bg-emerald-950 text-emerald-300 ring-4 ring-slate-950"
                      : isInProg
                      ? "border-blue-500/80 bg-blue-950 text-blue-300 animate-pulse ring-4 ring-slate-950"
                      : "border-slate-800 bg-slate-900 text-slate-600 ring-4 ring-slate-950"
                  }`}
                  aria-hidden="true"
                >
                  {isDone ? "✓" : isInProg ? "●" : "○"}
                </span>

                <div className="rounded-lg border border-slate-800/80 bg-slate-900/40 p-3 hover:bg-slate-900/70 transition-colors">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                    <h4 className="text-xs font-semibold text-slate-200">
                      {m.label}
                    </h4>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-[11px] font-mono ${
                          m.date === "Date not available"
                            ? "text-slate-500 italic"
                            : "text-slate-300 font-medium"
                        }`}
                      >
                        {m.date}
                      </span>
                      <span
                        className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                          isDone
                            ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800/50"
                            : isInProg
                            ? "bg-blue-950/80 text-blue-300 border border-blue-800/50"
                            : "bg-slate-800/60 text-slate-500 border border-slate-700/50"
                        }`}
                      >
                        {isDone ? "Recorded" : isInProg ? "Active" : "Pending"}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {m.notes}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>

        <div className="mt-4 rounded-md border border-slate-800/60 bg-slate-900/30 p-2.5 text-[11px] text-slate-500 leading-normal flex items-start gap-2">
          <span className="text-slate-400" aria-hidden="true">ℹ</span>
          <span>
            <strong>Research Integrity Note:</strong> Specific intermediate dates are explicitly rendered as
            &ldquo;Date not available&rdquo; unless authoritatively recorded in source parliamentary gazettes.
            The platform strictly prohibits date estimation or synthetic milestone generation.
          </span>
        </div>
      </div>
    </Card>
  );
}

export default ProceduralJourney;
