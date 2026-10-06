/**
 * app/live-discovery/page.tsx
 * ============================
 * Task 8.25 — Live Legislative Discovery.
 *
 * Separate from the frozen analytical dataset.
 * Shows recently discovered, active, and upcoming bills from authoritative sources.
 *
 * CRITICAL: Live discovery bills are NOT in the analytical prediction model.
 * A newly discovered bill MUST NOT appear to have market predictions.
 */

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DataStatusBadge, DataLayerBanner } from "@/components/ui/DataStatusBadge";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types — Live legislative record (NOT the frozen modelled dataset)
// ---------------------------------------------------------------------------

interface LiveBillRecord {
  id: string;
  title: string;
  jurisdiction: "central" | "state";
  state?: string;
  house?: string;
  billNumber?: string;
  status: "NEW" | "RECENT" | "ACTIVE" | "AMENDED" | "PASSED" | "ASSENT_PENDING" | "NOTIFIED" | "ARCHIVED" | "UPCOMING" | "SOURCE_UNVERIFIED";
  discoveredAt: string;
  lastUpdated: string;
  introducedDate?: string;
  subject?: string;
  source: string;
  sourceUrl?: string;
  sourceOrganization?: string;
  isInAnalyticalModel: boolean; // MUST be false for new live discoveries
  provenance: "AUTHORITATIVE" | "SECONDARY" | "UNVERIFIED";
}

// ---------------------------------------------------------------------------
// Mock live data — clearly labelled as LIVE DISCOVERY, not modelled
// ---------------------------------------------------------------------------

const LIVE_DISCOVERY_RECORDS: LiveBillRecord[] = [
  {
    id: "live_central_2025_001",
    title: "Digital Competition Bill, 2025",
    jurisdiction: "central",
    house: "Lok Sabha",
    billNumber: "Bill No. 47/2025",
    status: "ACTIVE",
    discoveredAt: "2026-09-25T08:30:00Z",
    lastUpdated: "2026-09-27T14:20:00Z",
    introducedDate: "2026-09-10T00:00:00Z",
    subject: "Digital markets, competition regulation, platform accountability",
    source: "Lok Sabha Official Website",
    sourceUrl: "https://loksabha.nic.in",
    sourceOrganization: "Parliament of India",
    isInAnalyticalModel: false,
    provenance: "AUTHORITATIVE",
  },
  {
    id: "live_central_2025_002",
    title: "Telecommunications (Amendment) Bill, 2025",
    jurisdiction: "central",
    house: "Rajya Sabha",
    billNumber: "Bill No. 31/2025",
    status: "ASSENT_PENDING",
    discoveredAt: "2026-09-20T10:15:00Z",
    lastUpdated: "2026-09-28T09:00:00Z",
    introducedDate: "2026-08-28T00:00:00Z",
    subject: "Spectrum allocation, telecom licensing, satellite communications",
    source: "Rajya Sabha Official Website",
    sourceUrl: "https://rajyasabha.nic.in",
    sourceOrganization: "Parliament of India",
    isInAnalyticalModel: false,
    provenance: "AUTHORITATIVE",
  },
  {
    id: "live_central_2025_003",
    title: "Data Protection (Amendment) Bill, 2026",
    jurisdiction: "central",
    house: "Lok Sabha",
    billNumber: "Bill No. 12/2026",
    status: "NEW",
    discoveredAt: "2026-09-28T06:00:00Z",
    lastUpdated: "2026-09-28T06:00:00Z",
    introducedDate: "2026-09-28T00:00:00Z",
    subject: "Personal data protection, consent framework, data fiduciaries",
    source: "Ministry of Electronics & IT",
    sourceUrl: "https://meity.gov.in",
    sourceOrganization: "MeitY",
    isInAnalyticalModel: false,
    provenance: "AUTHORITATIVE",
  },
  {
    id: "live_state_ka_2025_001",
    title: "Karnataka IT & ITES Employment (Amendment) Bill, 2026",
    jurisdiction: "state",
    state: "Karnataka",
    house: "Legislative Assembly",
    billNumber: "KA Bill 08/2026",
    status: "ACTIVE",
    discoveredAt: "2026-09-15T09:00:00Z",
    lastUpdated: "2026-09-26T11:30:00Z",
    introducedDate: "2026-09-10T00:00:00Z",
    subject: "IT sector employment conditions, working hours, remote work policy",
    source: "Karnataka Legislative Assembly",
    sourceUrl: "https://kla.kar.nic.in",
    sourceOrganization: "Karnataka Legislature",
    isInAnalyticalModel: false,
    provenance: "AUTHORITATIVE",
  },
  {
    id: "live_state_ts_2025_001",
    title: "Telangana Real Estate Regulatory (Amendment) Act, 2026",
    jurisdiction: "state",
    state: "Telangana",
    house: "Legislative Assembly",
    billNumber: "TS Bill 15/2026",
    status: "NOTIFIED",
    discoveredAt: "2026-09-01T00:00:00Z",
    lastUpdated: "2026-09-22T10:00:00Z",
    introducedDate: "2026-08-15T00:00:00Z",
    subject: "Real estate project registration, buyer protection, RERA compliance",
    source: "Telangana Government Gazette",
    sourceUrl: "https://gazette.telangana.gov.in",
    sourceOrganization: "Telangana Government",
    isInAnalyticalModel: false,
    provenance: "AUTHORITATIVE",
  },
  {
    id: "live_state_kl_2025_001",
    title: "Kerala Agricultural (Amendment) Bill, 2026",
    jurisdiction: "state",
    state: "Kerala",
    house: "Legislative Assembly",
    billNumber: "KL Bill 22/2026",
    status: "UPCOMING",
    discoveredAt: "2026-09-20T12:00:00Z",
    lastUpdated: "2026-09-28T08:00:00Z",
    subject: "Agricultural land use, crop insurance, farmer welfare",
    source: "Kerala Legislature Bulletin",
    sourceUrl: "https://niyamasabha.org",
    sourceOrganization: "Kerala Legislature",
    isInAnalyticalModel: false,
    provenance: "SECONDARY",
  },
];

// ---------------------------------------------------------------------------
// Filter & Status config
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<string, string> = {
  NEW: "bg-blue-500/12 border-blue-500/25 text-blue-400",
  RECENT: "bg-teal-500/12 border-teal-500/25 text-teal-400",
  ACTIVE: "bg-emerald-500/12 border-emerald-500/25 text-emerald-400",
  AMENDED: "bg-orange-500/12 border-orange-500/25 text-orange-400",
  PASSED: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300",
  ASSENT_PENDING: "bg-amber-500/12 border-amber-500/25 text-amber-400",
  NOTIFIED: "bg-blue-500/12 border-blue-500/25 text-blue-400",
  ARCHIVED: "bg-slate-700/30 border-slate-600/30 text-slate-500",
  UPCOMING: "bg-violet-500/12 border-violet-500/25 text-violet-400",
  SOURCE_UNVERIFIED: "bg-rose-500/12 border-rose-500/25 text-rose-400",
};

const JURISDICTION_FILTERS = ["All", "Central", "State"];
const STATUS_FILTERS = ["All", "NEW", "ACTIVE", "UPCOMING", "PASSED", "ASSENT_PENDING", "NOTIFIED"];

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(iso);
}

// ---------------------------------------------------------------------------
// Bill card component
// ---------------------------------------------------------------------------

function LiveBillCard({ record }: { record: LiveBillRecord }) {
  return (
    <div
      className={cn(
        "card-base card-hover card-live p-5 space-y-3 animate-fade-in",
        record.status === "NEW" && "ring-1 ring-blue-500/20"
      )}
    >
      {/* Header row */}
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
            <DataStatusBadge status={record.status} showDot />
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/8 text-slate-500 font-medium">
              {record.jurisdiction === "central" ? "Central" : record.state}
            </span>
            {record.house && (
              <span className="text-[10px] text-slate-600">
                {record.house}
              </span>
            )}
            {!record.isInAnalyticalModel && (
              <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-slate-800/60 border border-white/5 text-slate-600 font-mono">
                NOT IN PREDICTION MODEL
              </span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-slate-100 leading-snug line-clamp-2">
            {record.title}
          </h3>
          {record.billNumber && (
            <p className="text-xs text-slate-600 font-mono mt-0.5">{record.billNumber}</p>
          )}
        </div>
      </div>

      {/* Subject */}
      {record.subject && (
        <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">{record.subject}</p>
      )}

      {/* Metadata grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs border-t border-white/5 pt-3">
        <div>
          <span className="text-slate-600">Discovered</span>
          <p className="text-slate-300 font-medium">{timeAgo(record.discoveredAt)}</p>
        </div>
        <div>
          <span className="text-slate-600">Last Updated</span>
          <p className="text-slate-300 font-medium">{timeAgo(record.lastUpdated)}</p>
        </div>
        {record.introducedDate && (
          <div>
            <span className="text-slate-600">Introduced</span>
            <p className="text-slate-300 font-medium">{formatDate(record.introducedDate)}</p>
          </div>
        )}
        <div>
          <span className="text-slate-600">Provenance</span>
          <p
            className={cn(
              "font-medium",
              record.provenance === "AUTHORITATIVE" ? "text-emerald-400" :
              record.provenance === "SECONDARY" ? "text-amber-400" : "text-rose-400"
            )}
          >
            {record.provenance}
          </p>
        </div>
      </div>

      {/* Source */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <div className="min-w-0">
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">SOURCE</span>
          <p className="text-xs text-slate-400 truncate">{record.source}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {record.sourceUrl && (
            <a
              href={record.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 rounded"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Official Source
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function LiveDiscoveryPage() {
  const [jurisdictionFilter, setJurisdictionFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"discovered" | "updated" | "status">("discovered");

  const filtered = LIVE_DISCOVERY_RECORDS
    .filter((r) => {
      if (jurisdictionFilter === "Central" && r.jurisdiction !== "central") return false;
      if (jurisdictionFilter === "State" && r.jurisdiction !== "state") return false;
      if (statusFilter !== "All" && r.status !== statusFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return (
          r.title.toLowerCase().includes(q) ||
          r.subject?.toLowerCase().includes(q) ||
          r.state?.toLowerCase().includes(q) ||
          r.billNumber?.toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "discovered") return new Date(b.discoveredAt).getTime() - new Date(a.discoveredAt).getTime();
      if (sortBy === "updated") return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
      return a.status.localeCompare(b.status);
    });

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 max-w-7xl mx-auto animate-fade-in">
      {/* Page header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-section-label">Legislative Discovery</span>
          <span className="text-slate-700">/</span>
          <span className="badge-live">
            <span className="live-pulse" />
            LIVE
          </span>
        </div>
        <h1 className="text-headline text-white mb-3">Live Legislative Discovery</h1>
        <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
          Newly discovered bills and legislative measures from authoritative sources.
          These records are tracked in real-time and are <strong className="text-slate-300">separate from the frozen quantitative analytical model</strong>.
        </p>
      </div>

      {/* Data layer banner */}
      <DataLayerBanner type="live" className="mb-6" />

      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[
          { label: "Total Discovered", value: LIVE_DISCOVERY_RECORDS.length, color: "text-white" },
          { label: "Active Bills", value: LIVE_DISCOVERY_RECORDS.filter(r => r.status === "ACTIVE").length, color: "text-emerald-400" },
          { label: "New (48h)", value: LIVE_DISCOVERY_RECORDS.filter(r => r.status === "NEW").length, color: "text-blue-400" },
          { label: "Upcoming", value: LIVE_DISCOVERY_RECORDS.filter(r => r.status === "UPCOMING").length, color: "text-violet-400" },
        ].map((stat) => (
          <div key={stat.label} className="card-base p-4">
            <p className="text-section-label mb-1">{stat.label}</p>
            <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <circle cx={11} cy={11} r={8} />
            <path strokeLinecap="round" d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search bills…"
            className="w-full pl-9 pr-4 py-2 bg-slate-900/60 border border-white/8 rounded-lg text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
          />
        </div>

        {/* Jurisdiction filter */}
        <div className="flex items-center gap-1 bg-slate-900/60 border border-white/8 rounded-lg p-1">
          {JURISDICTION_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setJurisdictionFilter(f)}
              className={cn(
                "px-3 py-1 rounded-md text-xs font-medium transition-all",
                jurisdictionFilter === f
                  ? "bg-white/10 text-white"
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Status filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 bg-slate-900/60 border border-white/8 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-blue-500/50 transition-colors"
        >
          {STATUS_FILTERS.map((f) => (
            <option key={f} value={f}>{f === "All" ? "All Statuses" : f}</option>
          ))}
        </select>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
          className="px-3 py-2 bg-slate-900/60 border border-white/8 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-blue-500/50 transition-colors"
        >
          <option value="discovered">Sort: Discovered</option>
          <option value="updated">Sort: Last Updated</option>
          <option value="status">Sort: Status</option>
        </select>

        <span className="text-xs text-slate-600 ml-auto">
          {filtered.length} record{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="card-base p-12 text-center">
          <p className="text-slate-500 text-sm">No records match your current filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map((record) => (
            <LiveBillCard key={record.id} record={record} />
          ))}
        </div>
      )}

      {/* Footer disclaimer */}
      <div className="mt-10 pt-6 border-t border-white/5">
        <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
          <strong className="text-slate-500">Live Discovery Disclaimer:</strong> Records in this section are sourced
          from authoritative legislative bodies but have not been processed through the quantitative analytical
          pipeline. No stock price predictions, market impact scores, or anticipation signals are available
          for these records unless they independently pass the analytical eligibility criteria in a future
          explicitly versioned task. Source provenance is tracked and displayed for each record.
        </p>
      </div>
    </div>
  );
}
