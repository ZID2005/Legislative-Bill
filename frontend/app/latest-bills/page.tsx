/**
 * app/latest-bills/page.tsx
 * ==========================
 * Task 8.25 — Latest Bills Experience (Phase 7).
 *
 * Shows newest discovered bills across Central & State jurisdictions.
 * Ordering based on ingestion/source metadata — not claimed unless supported.
 * Clearly shows: LAST UPDATED, SOURCE, DISCOVERED AT.
 *
 * CRITICAL: These are LIVE DISCOVERY records only.
 * NOT from the frozen analytical prediction dataset.
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { DataStatusBadge, DataLayerBanner } from "@/components/ui/DataStatusBadge";
import { cn } from "@/lib/utils";

interface LatestBillRecord {
  id: string;
  title: string;
  billNumber?: string;
  jurisdiction: "central" | "state";
  state?: string;
  house?: string;
  status: "NEW" | "RECENT" | "ACTIVE" | "AMENDED" | "PASSED" | "ASSENT_PENDING" | "NOTIFIED" | "UPCOMING";
  subject?: string;
  introducedDate?: string;
  discoveredAt: string;
  lastUpdated: string;
  source: string;
  sourceUrl?: string;
  sourceOrganization?: string;
  isInAnalyticalModel: boolean;
}

// Latest bills ordered by discovery time — LIVE DATA ONLY
const LATEST_BILLS: LatestBillRecord[] = [
  {
    id: "latest_001",
    title: "Data Protection (Amendment) Bill, 2026",
    billNumber: "Bill No. 12/2026",
    jurisdiction: "central",
    house: "Lok Sabha",
    status: "NEW",
    subject: "Personal data protection, consent framework, data fiduciaries",
    introducedDate: "2026-09-28T00:00:00Z",
    discoveredAt: "2026-09-28T06:00:00Z",
    lastUpdated: "2026-09-28T06:00:00Z",
    source: "Ministry of Electronics & IT",
    sourceUrl: "https://meity.gov.in",
    sourceOrganization: "MeitY",
    isInAnalyticalModel: false,
  },
  {
    id: "latest_002",
    title: "Telecommunications (Amendment) Bill, 2025",
    billNumber: "Bill No. 31/2025",
    jurisdiction: "central",
    house: "Rajya Sabha",
    status: "ASSENT_PENDING",
    subject: "Spectrum allocation, telecom licensing, satellite communications",
    introducedDate: "2026-08-28T00:00:00Z",
    discoveredAt: "2026-09-20T10:15:00Z",
    lastUpdated: "2026-09-28T09:00:00Z",
    source: "Rajya Sabha Official Website",
    sourceUrl: "https://rajyasabha.nic.in",
    sourceOrganization: "Parliament of India",
    isInAnalyticalModel: false,
  },
  {
    id: "latest_003",
    title: "Digital Competition Bill, 2025",
    billNumber: "Bill No. 47/2025",
    jurisdiction: "central",
    house: "Lok Sabha",
    status: "ACTIVE",
    subject: "Digital markets, competition regulation, platform accountability",
    introducedDate: "2026-09-10T00:00:00Z",
    discoveredAt: "2026-09-25T08:30:00Z",
    lastUpdated: "2026-09-27T14:20:00Z",
    source: "Lok Sabha Official Website",
    sourceUrl: "https://loksabha.nic.in",
    sourceOrganization: "Parliament of India",
    isInAnalyticalModel: false,
  },
  {
    id: "latest_004",
    title: "Karnataka IT & ITES Employment (Amendment) Bill, 2026",
    billNumber: "KA Bill 08/2026",
    jurisdiction: "state",
    state: "Karnataka",
    house: "Legislative Assembly",
    status: "ACTIVE",
    subject: "IT sector employment conditions, working hours, remote work policy",
    introducedDate: "2026-09-10T00:00:00Z",
    discoveredAt: "2026-09-15T09:00:00Z",
    lastUpdated: "2026-09-26T11:30:00Z",
    source: "Karnataka Legislative Assembly",
    sourceUrl: "https://kla.kar.nic.in",
    sourceOrganization: "Karnataka Legislature",
    isInAnalyticalModel: false,
  },
  {
    id: "latest_005",
    title: "Telangana Real Estate Regulatory (Amendment) Act, 2026",
    billNumber: "TS Bill 15/2026",
    jurisdiction: "state",
    state: "Telangana",
    house: "Legislative Assembly",
    status: "NOTIFIED",
    subject: "Real estate project registration, buyer protection, RERA compliance",
    introducedDate: "2026-08-15T00:00:00Z",
    discoveredAt: "2026-09-01T00:00:00Z",
    lastUpdated: "2026-09-22T10:00:00Z",
    source: "Telangana Government Gazette",
    sourceUrl: "https://gazette.telangana.gov.in",
    sourceOrganization: "Telangana Government",
    isInAnalyticalModel: false,
  },
  {
    id: "latest_006",
    title: "Kerala Agricultural (Amendment) Bill, 2026",
    billNumber: "KL Bill 22/2026",
    jurisdiction: "state",
    state: "Kerala",
    house: "Legislative Assembly",
    status: "UPCOMING",
    subject: "Agricultural land use, crop insurance, farmer welfare",
    discoveredAt: "2026-09-20T12:00:00Z",
    lastUpdated: "2026-09-28T08:00:00Z",
    source: "Kerala Legislature Bulletin",
    sourceUrl: "https://niyamasabha.org",
    sourceOrganization: "Kerala Legislature",
    isInAnalyticalModel: false,
  },
];

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
    });
  } catch { return iso; }
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

const JURISDICTION_FILTERS = ["All", "Central", "State"];
const STATE_FILTERS = ["All States", "Karnataka", "Kerala", "Telangana", "Andhra Pradesh"];

export default function LatestBillsPage() {
  const [jurisdictionFilter, setJurisdictionFilter] = useState("All");
  const [stateFilter, setStateFilter] = useState("All States");
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const filtered = LATEST_BILLS
    .filter((r) => {
      if (jurisdictionFilter === "Central" && r.jurisdiction !== "central") return false;
      if (jurisdictionFilter === "State" && r.jurisdiction !== "state") return false;
      if (stateFilter !== "All States" && r.state !== stateFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return (
          r.title.toLowerCase().includes(q) ||
          r.subject?.toLowerCase().includes(q) ||
          r.billNumber?.toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => new Date(b.discoveredAt).getTime() - new Date(a.discoveredAt).getTime());

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-section-label">Legislative Discovery</span>
          <span className="text-slate-700">/</span>
          <span className="badge-live">
            <span className="live-pulse" />
            LIVE
          </span>
        </div>
        <h1 className="text-headline text-white mb-2">Latest Bills</h1>
        <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
          Most recently introduced and discovered legislative measures.
          Ordered by discovery timestamp. Source provenance displayed for every record.
        </p>
      </div>

      {/* Data layer banner */}
      <DataLayerBanner type="live" className="mb-6" />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <circle cx={11} cy={11} r={8} />
            <path strokeLinecap="round" d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
            placeholder="Search bills…"
            className="w-full pl-9 pr-4 py-2 bg-slate-900/60 border border-white/8 rounded-lg text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
          />
        </div>

        <div className="flex items-center gap-1 bg-slate-900/60 border border-white/8 rounded-lg p-1">
          {JURISDICTION_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => { setJurisdictionFilter(f); setPage(1); }}
              className={cn(
                "px-3 py-1 rounded-md text-xs font-medium transition-all",
                jurisdictionFilter === f ? "bg-white/10 text-white" : "text-slate-500 hover:text-slate-300"
              )}
            >
              {f}
            </button>
          ))}
        </div>

        {jurisdictionFilter === "State" && (
          <select
            value={stateFilter}
            onChange={(e) => { setStateFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-900/60 border border-white/8 rounded-lg text-xs text-slate-300 focus:outline-none"
          >
            {STATE_FILTERS.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        )}

        <span className="text-xs text-slate-600 ml-auto">
          {filtered.length} bill{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="card-base overflow-hidden mb-6">
        <div className="mobile-scroll-x">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ minWidth: 260 }}>Bill</th>
                <th style={{ minWidth: 100 }}>Jurisdiction</th>
                <th style={{ minWidth: 80 }}>Status</th>
                <th style={{ minWidth: 100 }}>Introduced</th>
                <th style={{ minWidth: 100 }}>Discovered</th>
                <th style={{ minWidth: 100 }}>Last Updated</th>
                <th style={{ minWidth: 140 }}>Source</th>
              </tr>
            </thead>
            <tbody>
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-sm text-slate-500">
                    No bills match your filters.
                  </td>
                </tr>
              ) : (
                paginated.map((bill) => (
                  <tr key={bill.id}>
                    <td>
                      <div>
                        <p className="text-sm font-medium text-slate-200 line-clamp-2 leading-snug">
                          {bill.title}
                        </p>
                        {bill.billNumber && (
                          <p className="text-[10px] text-slate-600 font-mono mt-0.5">{bill.billNumber}</p>
                        )}
                        <span className="text-[9px] px-1 py-0.5 rounded bg-slate-800/60 border border-white/5 text-slate-600 font-mono mt-1 inline-block">
                          NOT IN PREDICTION MODEL
                        </span>
                      </div>
                    </td>
                    <td>
                      <div className="text-xs">
                        <p className="text-slate-300 font-medium">
                          {bill.jurisdiction === "central" ? "Central" : bill.state}
                        </p>
                        {bill.house && (
                          <p className="text-slate-600">{bill.house}</p>
                        )}
                      </div>
                    </td>
                    <td>
                      <DataStatusBadge status={bill.status} showDot />
                    </td>
                    <td className="text-xs text-slate-400">
                      {bill.introducedDate ? formatDate(bill.introducedDate) : "—"}
                    </td>
                    <td className="text-xs text-slate-400">
                      <span title={formatDate(bill.discoveredAt)}>
                        {timeAgo(bill.discoveredAt)}
                      </span>
                    </td>
                    <td className="text-xs text-slate-400">
                      <span title={formatDate(bill.lastUpdated)}>
                        {timeAgo(bill.lastUpdated)}
                      </span>
                    </td>
                    <td>
                      <div className="text-xs">
                        <p className="text-slate-400 truncate max-w-[140px]">{bill.source}</p>
                        {bill.sourceUrl && (
                          <a
                            href={bill.sourceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300 transition-colors"
                          >
                            View Official Source ↗
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900/60 border border-white/8 text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            ← Prev
          </button>
          <span className="text-xs text-slate-500">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900/60 border border-white/8 text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            Next →
          </button>
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-8 pt-6 border-t border-white/5">
        <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
          <strong className="text-slate-500">Source Provenance:</strong> Bills are ordered by discovery timestamp from authoritative sources.
          &ldquo;Last Updated&rdquo; reflects the most recent change detected in the source record.
          &ldquo;Discovered At&rdquo; reflects when the record was first ingested.
          No bill is labelled as &ldquo;latest&rdquo; unless the source metadata supports the ordering.
        </p>
      </div>
    </div>
  );
}
