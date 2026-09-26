/**
 * app/workspace/page.tsx
 * =======================
 * Personalized Legislative Intelligence Workspace & Decision Center (Task 8.15).
 *
 * Core User Inquiries Answered:
 * - What am I watching?
 * - What changed since I last looked?
 * - Which bills affect my watched companies?
 * - Which industries are seeing new legislative activity?
 * - Which watched items have new risk/anticipation information?
 * - What notifications require attention?
 * - What is confirmed versus derived versus predicted?
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { workspaceApi } from "@/lib/api/workspace";
import type {
  WorkspaceActivityItem,
  WorkspaceAnalyticsItem,
  WorkspaceEntityCard,
  WorkspaceGroupedActivityResponse,
  WorkspaceSummaryResponse,
} from "@/types/api";
import { AIWorkspaceAssistant } from "@/components/workspace/AIWorkspaceAssistant";

export function WorkspacePage() {
  const [summary, setSummary] = useState<WorkspaceSummaryResponse | null>(null);
  const [activity, setActivity] = useState<WorkspaceActivityItem[]>([]);
  const [grouped, setGrouped] = useState<WorkspaceGroupedActivityResponse | null>(null);
  const [analytics, setAnalytics] = useState<WorkspaceAnalyticsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tabs
  const [activityFilter, setActivityFilter] = useState<string>("ALL");
  const [entityTab, setEntityTab] = useState<"bills" | "companies" | "industries" | "jurisdictions">("bills");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, actRes, grpRes, anaRes] = await Promise.all([
        workspaceApi.getSummary(),
        workspaceApi.getActivity({ limit: 25 }),
        workspaceApi.getWatchlistActivity(),
        workspaceApi.getAnalyticsSnapshot(),
      ]);
      setSummary(sumRes);
      setActivity(actRes.items || []);
      setGrouped(grpRes);
      setAnalytics(anaRes.items || []);
    } catch (err: unknown) {
      console.error("Failed to load workspace data:", err);
      setError("Failed to load workspace data. Please verify backend service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredActivity = activity.filter((item) => {
    if (activityFilter === "ALL") return true;
    if (activityFilter === "ALERTS") return item.activity_id.startsWith("alert_");
    if (activityFilter === "MONITORING") return item.activity_id.startsWith("mon_");
    return true;
  });

  const getEpistemicBadge = (status: string) => {
    switch (status) {
      case "OBSERVED":
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
            [OBSERVED]
          </span>
        );
      case "DERIVED":
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
            [DERIVED]
          </span>
        );
      case "PREDICTION":
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
            [PREDICTION]
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            [{status}]
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⚖</span>
            <span className="text-xs uppercase tracking-widest font-bold text-blue-400">
              Personalized Decision Center
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
            Your Legislative Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Your monitored bills, corporate exposures, custom watchlists, triggered alerts, and verified anticipation telemetry.
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/watchlists"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm flex items-center gap-1.5"
          >
            <span>⭐</span>
            <span>Manage Watchlists</span>
          </Link>
          <Link
            href="/alerts"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <span>🔔</span>
            <span>Alerts Center</span>
          </Link>
          <button
            onClick={loadData}
            title="Refresh workspace"
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
          >
            ↻
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Section A: Attention Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Unread Notifications */}
        <Link
          href="/notifications"
          className="bg-slate-900 border border-slate-800 hover:border-blue-500/50 p-4 rounded-xl transition-all group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Notifications</span>
            <span className="text-slate-500 group-hover:text-blue-400">📬</span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {loading ? "..." : summary?.unread_notifications ?? 0}
          </div>
          <span className="text-[11px] text-amber-400 font-medium">Require review</span>
        </Link>

        {/* Active Alerts */}
        <Link
          href="/alerts"
          className="bg-slate-900 border border-slate-800 hover:border-blue-500/50 p-4 rounded-xl transition-all group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Active Alerts</span>
            <span className="text-slate-500 group-hover:text-blue-400">🔔</span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {loading ? "..." : summary?.active_alerts ?? 0}
          </div>
          <span className="text-[11px] text-red-400 font-medium">Unread triggers</span>
        </Link>

        {/* Watched Bills */}
        <button
          onClick={() => setEntityTab("bills")}
          className="bg-slate-900 border border-slate-800 hover:border-blue-500/50 p-4 rounded-xl transition-all text-left group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Watched Bills</span>
            <span className="text-slate-500 group-hover:text-blue-400">📜</span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {loading ? "..." : summary?.watched_bills ?? 0}
          </div>
          <span className="text-[11px] text-slate-400">Central & State</span>
        </button>

        {/* Watched Companies */}
        <button
          onClick={() => setEntityTab("companies")}
          className="bg-slate-900 border border-slate-800 hover:border-blue-500/50 p-4 rounded-xl transition-all text-left group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Watched Companies</span>
            <span className="text-slate-500 group-hover:text-blue-400">🏢</span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {loading ? "..." : summary?.watched_companies ?? 0}
          </div>
          <span className="text-[11px] text-slate-400">Corporate exposure</span>
        </button>

        {/* Watched Industries */}
        <button
          onClick={() => setEntityTab("industries")}
          className="bg-slate-900 border border-slate-800 hover:border-blue-500/50 p-4 rounded-xl transition-all text-left group"
        >
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Industries</span>
            <span className="text-slate-500 group-hover:text-blue-400">🏭</span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {loading ? "..." : summary?.watched_industries ?? 0}
          </div>
          <span className="text-[11px] text-slate-400">Monitored sectors</span>
        </button>

        {/* Recent Changes Count */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Recent Changes</span>
            <span className="text-slate-500">📡</span>
          </div>
          <div className="text-2xl font-bold text-blue-400">
            {loading ? "..." : summary?.recent_changes_count ?? 0}
          </div>
          <span className="text-[11px] text-slate-400">Last 7 days</span>
        </div>
      </div>

      {/* Section B & Section C: Dual Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Monitored Entities (Grouped Activity) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                Monitored Entities
                <span className="text-xs font-normal text-slate-400">
                  ({grouped?.total_watched ?? 0} total items)
                </span>
              </h2>
            </div>

            {/* Entity Filter Tabs */}
            <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setEntityTab("bills")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "bills" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Bills ({grouped?.bills.length ?? 0})
              </button>
              <button
                onClick={() => setEntityTab("companies")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "companies" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Companies ({grouped?.companies.length ?? 0})
              </button>
              <button
                onClick={() => setEntityTab("industries")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "industries" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Industries ({grouped?.industries.length ?? 0})
              </button>
              <button
                onClick={() => setEntityTab("jurisdictions")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "jurisdictions" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                States ({grouped?.jurisdictions.length ?? 0})
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="space-y-3">
            {loading && (
              <div className="p-8 text-center text-slate-500">Loading watched entities...</div>
            )}

            {!loading && grouped && (
              <>
                {/* Bills Tab */}
                {entityTab === "bills" && (
                  grouped.bills.length === 0 ? (
                    <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800/80">
                      <p className="text-sm text-slate-400">No bills monitored in your active watchlists.</p>
                      <Link
                        href="/bills"
                        className="mt-3 inline-block text-xs font-semibold text-blue-400 hover:text-blue-300"
                      >
                        Explore Legislative Bills →
                      </Link>
                    </div>
                  ) : (
                    grouped.bills.map((b) => (
                      <div
                        key={b.entity_id}
                        className="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                              {b.jurisdiction}
                            </span>
                            {b.state && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                                {b.state}
                              </span>
                            )}
                            <span className="text-xs text-slate-400">In watchlist:</span>
                            <span className="text-xs font-medium text-slate-300">
                              {b.watchlist_name}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-slate-100 hover:text-blue-400 transition-colors">
                            <Link href={b.deep_link}>{b.entity_name || b.entity_id}</Link>
                          </h4>
                          <p className="text-xs text-slate-400">
                            {b.latest_activity}
                          </p>
                        </div>

                        <div className="flex items-center gap-3 flex-shrink-0">
                          {b.alert_count > 0 && (
                            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-red-950 text-red-300 border border-red-800">
                              {b.alert_count} Alerts
                            </span>
                          )}
                          <Link
                            href={b.deep_link}
                            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                          >
                            View Dossier →
                          </Link>
                        </div>
                      </div>
                    ))
                  )
                )}

                {/* Companies Tab */}
                {entityTab === "companies" && (
                  grouped.companies.length === 0 ? (
                    <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800/80">
                      <p className="text-sm text-slate-400">No corporate entities monitored in your watchlists.</p>
                      <Link
                        href="/companies"
                        className="mt-3 inline-block text-xs font-semibold text-blue-400 hover:text-blue-300"
                      >
                        Explore Corporate Universe →
                      </Link>
                    </div>
                  ) : (
                    grouped.companies.map((c) => (
                      <div
                        key={c.entity_id}
                        className="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                              {c.entity_id}
                            </span>
                            {c.extra_metadata?.sector && (
                              <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                                {c.extra_metadata.sector}
                              </span>
                            )}
                            <span className="text-xs text-slate-400">Watchlist:</span>
                            <span className="text-xs font-medium text-slate-300">
                              {c.watchlist_name}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-slate-100 hover:text-blue-400 transition-colors">
                            <Link href={c.deep_link}>{c.entity_name || c.entity_id}</Link>
                          </h4>
                          <p className="text-xs text-slate-400">{c.latest_activity}</p>
                        </div>

                        <div className="flex items-center gap-3 flex-shrink-0">
                          {c.extra_metadata?.is_quant_eligible ? (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                              Quant Modeled
                            </span>
                          ) : (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              Qualitative Intel
                            </span>
                          )}
                          <Link
                            href={c.deep_link}
                            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                          >
                            View Company →
                          </Link>
                        </div>
                      </div>
                    ))
                  )
                )}

                {/* Industries Tab */}
                {entityTab === "industries" && (
                  grouped.industries.length === 0 ? (
                    <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800/80">
                      <p className="text-sm text-slate-400">No industries monitored yet.</p>
                      <Link
                        href="/industries"
                        className="mt-3 inline-block text-xs font-semibold text-blue-400 hover:text-blue-300"
                      >
                        Explore Industry Taxonomy →
                      </Link>
                    </div>
                  ) : (
                    grouped.industries.map((ind) => (
                      <div
                        key={ind.entity_id}
                        className="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors flex items-center justify-between"
                      >
                        <div>
                          <h4 className="text-sm font-semibold text-slate-100">
                            <Link href={ind.deep_link} className="hover:text-blue-400">
                              {ind.entity_name || ind.entity_id}
                            </Link>
                          </h4>
                          <p className="text-xs text-slate-400">{ind.latest_activity}</p>
                        </div>
                        <Link
                          href={ind.deep_link}
                          className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                        >
                          View Industry →
                        </Link>
                      </div>
                    ))
                  )
                )}

                {/* Jurisdictions Tab */}
                {entityTab === "jurisdictions" && (
                  grouped.jurisdictions.length === 0 ? (
                    <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800/80">
                      <p className="text-sm text-slate-400">No jurisdictions monitored yet.</p>
                      <Link
                        href="/states"
                        className="mt-3 inline-block text-xs font-semibold text-blue-400 hover:text-blue-300"
                      >
                        Explore State Assemblies →
                      </Link>
                    </div>
                  ) : (
                    grouped.jurisdictions.map((j) => (
                      <div
                        key={j.entity_id}
                        className="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors flex items-center justify-between"
                      >
                        <div>
                          <h4 className="text-sm font-semibold text-slate-100 capitalize">
                            {j.entity_name || j.entity_id}
                          </h4>
                          <p className="text-xs text-slate-400">{j.latest_activity}</p>
                        </div>
                        <Link
                          href={j.deep_link}
                          className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                        >
                          View Assembly →
                        </Link>
                      </div>
                    ))
                  )
                )}
              </>
            )}
          </div>
        </div>

        {/* Right Column: Recent Activity Feed */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <span>Recent Activity Feed</span>
            </h2>

            {/* Filter */}
            <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setActivityFilter("ALL")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  activityFilter === "ALL" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setActivityFilter("ALERTS")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  activityFilter === "ALERTS" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Alerts
              </button>
              <button
                onClick={() => setActivityFilter("MONITORING")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  activityFilter === "MONITORING" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Monitoring
              </button>
            </div>
          </div>

          {/* Activity Items */}
          <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
            {loading && <div className="p-8 text-center text-slate-500">Loading feed...</div>}

            {!loading && filteredActivity.length === 0 && (
              <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800">
                <p className="text-sm text-slate-400">No recent activity detected for your watchlists.</p>
              </div>
            )}

            {!loading &&
              filteredActivity.map((item) => (
                <div
                  key={item.activity_id}
                  className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {getEpistemicBadge(item.epistemic_status)}
                      <span className="text-xs font-medium text-slate-300">
                        {item.entity_name}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500">
                      {item.timestamp ? new Date(item.timestamp).toLocaleDateString() : ""}
                    </span>
                  </div>

                  <p className="text-xs font-medium text-slate-200">{item.title}</p>
                  <p className="text-xs text-slate-400 leading-relaxed">{item.summary}</p>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/60">
                    <span className="text-[10px] text-slate-400 font-mono">
                      Type: {item.activity_type}
                    </span>
                    <Link
                      href={item.deep_link}
                      className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
                    >
                      View Details →
                    </Link>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Section D: Risk & Pre-Event Anticipation Analytics Snapshot */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <span>Risk & Anticipation Analytics Snapshot</span>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                Verified Diagnostics
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly consumes frozen models and risk ratings with full State & Intelligence Firewall compliance.
            </p>
          </div>

          <div className="text-[11px] text-slate-400 italic bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
            Institutional Epistemic Rule: [OBSERVED] ⟂ [DERIVED] ⟂ [PREDICTION]
          </div>
        </div>

        {/* Snapshot Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {loading && <div className="p-6 text-slate-500">Loading analytics snapshot...</div>}

          {!loading && analytics.length === 0 && (
            <div className="col-span-full p-8 text-center text-slate-400 bg-slate-950/50 rounded-xl border border-slate-800">
              Add companies or bills to your watchlists to view risk classification and anticipation diagnostics.
            </div>
          )}

          {!loading &&
            analytics.map((it, idx) => (
              <div
                key={idx}
                className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3"
              >
                {/* Card Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {it.entity_type}
                    </span>
                    {getEpistemicBadge(it.epistemic_label.replace("[", "").replace("]", ""))}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {it.entity_id}
                  </span>
                </div>

                <h4 className="text-sm font-semibold text-slate-100 truncate">
                  {it.entity_name}
                </h4>

                {/* Firewall alerts */}
                {it.is_state_firewall_active && (
                  <div className="p-2.5 rounded bg-amber-950/40 border border-amber-800 text-xs text-amber-300">
                    🛡 <strong>State Prediction Firewall Active</strong>: {it.firewall_note}
                  </div>
                )}

                {it.is_intelligence_firewall_active && (
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-700 text-xs text-slate-300">
                    🛡 <strong>Intelligence Company Firewall Active</strong>: {it.firewall_note}
                  </div>
                )}

                {/* Quantitative Metrics for Central Quant Securities */}
                {!it.is_state_firewall_active && !it.is_intelligence_firewall_active && (
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-xs">
                    <div>
                      <span className="text-slate-500 text-[11px]">Risk Category</span>
                      <p className="font-semibold text-slate-200">
                        {it.risk_level || "MODERATE"}
                        {it.risk_score !== null && it.risk_score !== undefined && (
                          <span className="text-slate-400 font-normal"> ({it.risk_score.toFixed(2)})</span>
                        )}
                      </p>
                    </div>

                    <div>
                      <span className="text-slate-500 text-[11px]">Anticipation Bias</span>
                      <p className="font-semibold text-slate-200">
                        {it.anticipation_tier || "NOT_FLAGGED"}
                        {it.anticipation_score !== null && it.anticipation_score !== undefined && (
                          <span className="text-slate-400 font-normal"> ({it.anticipation_score.toFixed(2)})</span>
                        )}
                      </p>
                    </div>

                    {it.prediction_record && (
                      <div className="col-span-2 mt-1 p-2 bg-slate-900 rounded border border-slate-800">
                        <span className="text-slate-500 text-[10px] block">Model Prediction</span>
                        <div className="flex items-center justify-between text-xs font-medium text-slate-200">
                          <span>Direction: <strong className="text-emerald-400">{it.prediction_record.direction}</strong></span>
                          <span>Confidence: <strong className="text-blue-400">{it.prediction_record.confidence}</strong></span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
        </div>
      </div>

      {/* Section E: Grounded AI Assistant */}
      <AIWorkspaceAssistant />
    </div>
  );
}

export default WorkspacePage;
