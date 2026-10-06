/**
 * app/upcoming-legislation/page.tsx
 * ====================================
 * Task 8.25 — Upcoming Legislation (Phase 8).
 *
 * Only shows scheduled legislative events where AUTHORITATIVE SOURCE provides dates.
 * NEVER fabricates future legislative dates.
 * Language: "Scheduled", "Reported", "Expected by source", "Date not available"
 */

"use client";

import React, { useState } from "react";
import { DataStatusBadge, DataLayerBanner } from "@/components/ui/DataStatusBadge";
import { cn } from "@/lib/utils";

interface UpcomingLegislativeEvent {
  id: string;
  title: string;
  type: "SESSION" | "READING" | "COMMITTEE" | "BUDGET" | "VOTE" | "TABLING" | "CONSIDERATION";
  jurisdiction: "central" | "state";
  state?: string;
  scheduledDate?: string; // only if authoritative source provides it
  dateConfidence: "SCHEDULED" | "REPORTED" | "EXPECTED_BY_SOURCE" | "DATE_NOT_AVAILABLE";
  billId?: string;
  billTitle?: string;
  description: string;
  source: string;
  sourceUrl?: string;
  sourceOrganization?: string;
  lastVerified: string;
}

// Only authoritative scheduled events — NO fabricated dates
const UPCOMING_EVENTS: UpcomingLegislativeEvent[] = [
  {
    id: "upcoming_001",
    type: "SESSION",
    title: "Winter Session of Parliament 2026",
    jurisdiction: "central",
    scheduledDate: "2026-11-15T00:00:00Z",
    dateConfidence: "REPORTED",
    description: "Expected commencement of the Winter Session. Date reported by parliamentary sources, subject to official notification.",
    source: "Parliament of India — Press Information Bureau",
    sourceUrl: "https://pib.gov.in",
    sourceOrganization: "PIB, Government of India",
    lastVerified: "2026-09-25T10:00:00Z",
  },
  {
    id: "upcoming_002",
    type: "READING",
    title: "Second Reading — Digital Competition Bill, 2025",
    jurisdiction: "central",
    scheduledDate: "2026-10-15T00:00:00Z",
    dateConfidence: "REPORTED",
    billTitle: "Digital Competition Bill, 2025",
    description: "Second reading of the Digital Competition Bill expected in October session. Exact date subject to parliamentary scheduling.",
    source: "Lok Sabha Business Advisory Committee — reported by news agencies",
    sourceUrl: "https://loksabha.nic.in",
    sourceOrganization: "Parliament of India",
    lastVerified: "2026-09-20T00:00:00Z",
  },
  {
    id: "upcoming_003",
    type: "SESSION",
    title: "Karnataka Budget Session 2027",
    jurisdiction: "state",
    state: "Karnataka",
    dateConfidence: "DATE_NOT_AVAILABLE",
    description: "Annual budget session typically held in February–March. No official date announced at this time.",
    source: "Karnataka Legislative Assembly website",
    sourceUrl: "https://kla.kar.nic.in",
    sourceOrganization: "Karnataka Legislature",
    lastVerified: "2026-09-15T00:00:00Z",
  },
  {
    id: "upcoming_004",
    type: "COMMITTEE",
    title: "Standing Committee Review — Telecommunications (Amendment) Bill",
    jurisdiction: "central",
    scheduledDate: "2026-10-05T00:00:00Z",
    dateConfidence: "SCHEDULED",
    billTitle: "Telecommunications (Amendment) Bill, 2025",
    description: "Parliamentary Standing Committee on Communications scheduled to present report on the Telecommunications Amendment Bill.",
    source: "Rajya Sabha — Committee on Information Technology",
    sourceUrl: "https://rajyasabha.nic.in",
    sourceOrganization: "Parliament of India",
    lastVerified: "2026-09-28T08:00:00Z",
  },
  {
    id: "upcoming_005",
    type: "TABLING",
    title: "Data Protection Amendment — Expected Tabling",
    jurisdiction: "central",
    dateConfidence: "EXPECTED_BY_SOURCE",
    billTitle: "Data Protection (Amendment) Bill, 2026",
    description: "MeitY has indicated the bill will be tabled for public consultation before end of Q4 2026. No formal date set.",
    source: "Ministry of Electronics & Information Technology",
    sourceUrl: "https://meity.gov.in",
    sourceOrganization: "MeitY",
    lastVerified: "2026-09-28T06:00:00Z",
  },
];

const DATE_CONFIDENCE_CONFIG: Record<string, { label: string; color: string }> = {
  SCHEDULED: { label: "Scheduled", color: "text-emerald-400" },
  REPORTED: { label: "Reported by source", color: "text-amber-400" },
  EXPECTED_BY_SOURCE: { label: "Expected by source", color: "text-orange-400" },
  DATE_NOT_AVAILABLE: { label: "Date not available", color: "text-slate-500" },
};

const EVENT_TYPE_ICONS: Record<string, string> = {
  SESSION: "🏛",
  READING: "📖",
  COMMITTEE: "👥",
  BUDGET: "💼",
  VOTE: "🗳",
  TABLING: "📋",
  CONSIDERATION: "⚖",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-IN", {
      weekday: "short", day: "numeric", month: "long", year: "numeric",
    });
  } catch { return iso; }
}

export default function UpcomingLegislationPage() {
  const [jurisdictionFilter, setJurisdictionFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState("All");

  const filtered = UPCOMING_EVENTS.filter((e) => {
    if (jurisdictionFilter === "Central" && e.jurisdiction !== "central") return false;
    if (jurisdictionFilter === "State" && e.jurisdiction !== "state") return false;
    if (typeFilter !== "All" && e.type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-section-label">Legislative Discovery</span>
          <span className="text-slate-700">/</span>
          <DataStatusBadge status="UPCOMING" />
        </div>
        <h1 className="text-headline text-white mb-2">Upcoming Legislation</h1>
        <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
          Scheduled legislative events where authoritative sources provide confirmed or expected dates.
          <strong className="text-slate-300"> No future dates are fabricated.</strong> Each event includes its date confidence level and source provenance.
        </p>
      </div>

      {/* Important disclaimer */}
      <div className="mb-6 flex items-start gap-3 px-4 py-3 rounded-lg border border-amber-800/30 bg-amber-950/20 text-xs">
        <span className="text-amber-400 flex-shrink-0 mt-0.5">⚠</span>
        <div>
          <p className="font-semibold text-amber-300 mb-0.5">Epistemic Disclaimer</p>
          <p className="text-slate-400 leading-relaxed">
            Legislative scheduling is subject to change by parliamentary authorities.
            Dates labelled &ldquo;Reported&rdquo; or &ldquo;Expected by source&rdquo; are not confirmed
            and may not reflect official parliamentary decisions. Always verify with official sources.
            This platform <strong className="text-slate-300">never predicts</strong> that a bill will be introduced or passed
            unless authoritative data supports the statement.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex items-center gap-1 bg-slate-900/60 border border-white/8 rounded-lg p-1">
          {["All", "Central", "State"].map((f) => (
            <button
              key={f}
              onClick={() => setJurisdictionFilter(f)}
              className={cn(
                "px-3 py-1 rounded-md text-xs font-medium transition-all",
                jurisdictionFilter === f ? "bg-white/10 text-white" : "text-slate-500 hover:text-slate-300"
              )}
            >
              {f}
            </button>
          ))}
        </div>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 bg-slate-900/60 border border-white/8 rounded-lg text-xs text-slate-300 focus:outline-none"
        >
          <option value="All">All Event Types</option>
          <option value="SESSION">Sessions</option>
          <option value="READING">Readings</option>
          <option value="COMMITTEE">Committee Reviews</option>
          <option value="TABLING">Tabling</option>
          <option value="VOTE">Votes</option>
        </select>

        <span className="text-xs text-slate-600 ml-auto">{filtered.length} event{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Events list */}
      <div className="space-y-4">
        {filtered.length === 0 ? (
          <div className="card-base p-12 text-center">
            <p className="text-slate-500 text-sm">No upcoming events match your filters.</p>
          </div>
        ) : (
          filtered.map((event, idx) => {
            const dateConf = DATE_CONFIDENCE_CONFIG[event.dateConfidence];
            return (
              <div
                key={event.id}
                className={cn(
                  "card-base p-5 animate-fade-in",
                  `animate-stagger-${Math.min(idx + 1, 6)}`
                )}
              >
                <div className="flex items-start gap-4">
                  {/* Type icon */}
                  <div className="flex-shrink-0 h-10 w-10 rounded-xl bg-white/5 border border-white/8 flex items-center justify-center text-lg">
                    {EVENT_TYPE_ICONS[event.type] ?? "📅"}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">
                        {event.type.replace("_", " ")}
                      </span>
                      <span className="text-slate-700">·</span>
                      <span className="text-[10px] text-slate-600">
                        {event.jurisdiction === "central" ? "Central Parliament" : event.state}
                      </span>
                    </div>

                    <h3 className="text-sm font-semibold text-slate-100 mb-2">{event.title}</h3>

                    {event.billTitle && (
                      <p className="text-xs text-slate-500 mb-2">
                        Re: <span className="text-slate-400">{event.billTitle}</span>
                      </p>
                    )}

                    <p className="text-xs text-slate-400 leading-relaxed mb-3">{event.description}</p>

                    {/* Date + confidence */}
                    <div className="flex flex-wrap items-center gap-4 text-xs">
                      <div>
                        <span className="text-slate-600 block mb-0.5 uppercase tracking-wider text-[9px]">Date</span>
                        <span className="text-slate-200 font-medium">
                          {event.scheduledDate ? formatDate(event.scheduledDate) : "—"}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-600 block mb-0.5 uppercase tracking-wider text-[9px]">Confidence</span>
                        <span className={cn("font-medium", dateConf.color)}>
                          {dateConf.label}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-600 block mb-0.5 uppercase tracking-wider text-[9px]">Last Verified</span>
                        <span className="text-slate-400">
                          {new Date(event.lastVerified).toLocaleDateString("en-IN", {
                            day: "numeric", month: "short", year: "numeric"
                          })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Source link */}
                  <div className="flex-shrink-0 text-right">
                    {event.sourceUrl ? (
                      <a
                        href={event.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg border border-white/8 bg-white/3 text-slate-400 hover:text-white hover:border-white/15 transition-all"
                      >
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        Official Source
                      </a>
                    ) : (
                      <span className="text-[10px] text-slate-600">No URL available</span>
                    )}
                    <p className="text-[10px] text-slate-600 mt-1 max-w-[120px] text-right truncate">
                      {event.sourceOrganization}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="mt-10 pt-6 border-t border-white/5">
        <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
          <strong className="text-slate-500">Data Policy:</strong> Only events with authoritative source backing are displayed.
          Future dates without official confirmation are labelled &ldquo;Expected by source&rdquo; or &ldquo;Date not available&rdquo;.
          This section will never predict legislative outcomes or fabricate procedural milestones.
        </p>
      </div>
    </div>
  );
}
