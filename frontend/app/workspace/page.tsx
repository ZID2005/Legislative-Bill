/**
 * app/workspace/page.tsx
 * =======================
 * Task 1.7A — Personalized Legislative Intelligence Workspace & Decision Workbench.
 *
 * Implements the approved premium editorial-finance design:
 * - Clear persona workbench purpose: monitored bills, watchlist entities, alerts, and decision telemetry
 * - High-density Attention Strip with tabular figures (notifications, alerts, bills, companies, industries, changes)
 * - Personalized Relevance Layer & Change Feed with epistemic tags
 * - Master-Detail Two-Column Layout (Monitored Entities + Chronological Activity Feed)
 * - Risk & Pre-Event Anticipation Analytics Snapshot with State & Intelligence Firewalls
 * - Integrated Grounded AI Workspace Assistant (Groq LLaMA 3.3 70B RAG)
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { workspaceApi } from "@/lib/api/workspace";
import type {
  PersonalizedChangeFeedItem,
  PersonalizedDashboardResponse,
  WorkspaceActivityItem,
  WorkspaceAnalyticsItem,
  WorkspaceGroupedActivityResponse,
  WorkspaceSummaryResponse,
} from "@/types/api";
import { AIWorkspaceAssistant } from "@/components/workspace/AIWorkspaceAssistant";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { EmptyState, ErrorState, SkeletonCard } from "@/components/ui/Skeleton";
import { PersonalizedPersonaHero } from "@/components/workspace/PersonalizedPersonaHero";
import { FirstRunGuidance } from "@/components/workspace/FirstRunGuidance";
import {
  OnboardingHandoffData,
  DEFAULT_HANDOFF_DATA,
  getOnboardingHandoff,
  isGuidanceDismissed,
} from "@/lib/onboarding/handoff";

export function WorkspacePage() {
  const [summary, setSummary] = useState<WorkspaceSummaryResponse | null>(null);
  const [activity, setActivity] = useState<WorkspaceActivityItem[]>([]);
  const [grouped, setGrouped] = useState<WorkspaceGroupedActivityResponse | null>(null);
  const [analytics, setAnalytics] = useState<WorkspaceAnalyticsItem[]>([]);
  const [decisionIntel, setDecisionIntel] = useState<PersonalizedDashboardResponse | null>(null);
  const [changeFeed, setChangeFeed] = useState<PersonalizedChangeFeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Personalized Handoff & First-Run Guidance State
  const [handoff, setHandoff] = useState<OnboardingHandoffData>(DEFAULT_HANDOFF_DATA);
  const [showGuidance, setShowGuidance] = useState(false);

  // Tabs & filters
  const [activityFilter, setActivityFilter] = useState<string>("ALL");
  const [entityTab, setEntityTab] = useState<"bills" | "companies" | "industries" | "jurisdictions">("bills");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Re-hydrate handoff state
      const handoffData = getOnboardingHandoff();
      setHandoff(handoffData);

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

      // Non-blocking fetch of decision intelligence & change feed
      if (typeof (workspaceApi as any).getDecisionIntelligence === "function") {
        (workspaceApi as any).getDecisionIntelligence().then((res: any) => setDecisionIntel(res)).catch(() => {});
      }
      if (typeof (workspaceApi as any).getChangeFeed === "function") {
        (workspaceApi as any).getChangeFeed(20).then((res: any) => setChangeFeed(res || [])).catch(() => {});
      }
    } catch (err: unknown) {
      console.error("Failed to load workspace data:", err);
      setError("Failed to load workspace data. Please verify backend service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setHandoff(getOnboardingHandoff());
    setShowGuidance(!isGuidanceDismissed());
    loadData();
  }, []);

  const filteredActivity = activity.filter((item) => {
    if (activityFilter === "ALL") return true;
    if (activityFilter === "ALERTS") return item.activity_id.startsWith("alert_");
    if (activityFilter === "MONITORING") return item.activity_id.startsWith("mon_");
    return true;
  });

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] p-6 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* -------------------------------------------------------------------- */}
      {/* 1. EXECUTIVE WORKBENCH HEADER & ACTIONS                              */}
      {/* -------------------------------------------------------------------- */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[var(--border-default)] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-base">⚖</span>
            <span className="text-xs uppercase tracking-widest font-bold text-blue-600 dark:text-blue-400 font-mono">
              Personalized Decision Center
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            Your Legislative Workspace
          </h1>
          <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1 max-w-3xl leading-relaxed">
            Your monitored bills, corporate exposures, custom watchlists, triggered alerts, and verified anticipation telemetry.
          </p>
        </div>

        {/* Action controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Link
            href="/portfolio"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm flex items-center gap-1.5"
          >
            <span>💼</span>
            <span>Portfolio Exposure</span>
          </Link>
          <Link
            href="/watchlists"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm flex items-center gap-1.5"
          >
            <span>⭐</span>
            <span>Manage Watchlists</span>
          </Link>
          <Link
            href="/alerts"
            className="px-4 py-2 bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] text-xs font-semibold rounded-lg border border-[var(--border-strong)] transition-colors flex items-center gap-1.5 shadow-xs"
          >
            <span>🔔</span>
            <span>Alerts Center</span>
          </Link>
          <Link
            href="/overview"
            className="px-3.5 py-2 bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-semibold rounded-lg border border-[var(--border-strong)] transition-colors shadow-xs"
          >
            Overview
          </Link>
          <button
            type="button"
            onClick={() => setShowGuidance((prev) => !prev)}
            title="Toggle first-run platform guidance"
            aria-label="Toggle first-run platform guidance"
            data-testid="toggle-guidance-btn"
            className="px-3 py-2 bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-semibold rounded-lg border border-[var(--border-strong)] transition-colors shadow-xs flex items-center gap-1.5"
          >
            <span>🧭</span>
            <span className="hidden sm:inline">Guidance</span>
          </button>
          <button
            onClick={loadData}
            title="Refresh workspace"
            aria-label="Refresh workspace"
            className="p-2 bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-lg border border-[var(--border-strong)] transition-colors"
          >
            ↻
          </button>
        </div>
      </div>

      {error && (
        <ErrorState error={error} onRetry={loadData} />
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 1A. FIRST-RUN GUIDANCE (PROGRESSIVE DISCLOSURE TOUR)                  */}
      {/* -------------------------------------------------------------------- */}
      {showGuidance && (
        <FirstRunGuidance
          onDismiss={() => setShowGuidance(false)}
        />
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 1B. PERSONALIZED COMMAND DESK HERO (PERSONA ORIENTATION)              */}
      {/* -------------------------------------------------------------------- */}
      <PersonalizedPersonaHero
        handoff={handoff}
        onReopenGuidance={() => setShowGuidance(true)}
      />

      {/* -------------------------------------------------------------------- */}
      {/* 2. HIGH-DENSITY ATTENTION SUMMARY (TABULAR NUMERALS)                 */}
      {/* -------------------------------------------------------------------- */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border-default)] border border-[var(--border-default)] rounded-xl bg-[var(--bg-surface)] overflow-hidden">
        {/* Unread Notifications */}
        <Link
          href="/notifications"
          className="p-4 text-center hover:bg-[var(--bg-card-hover)] transition-colors group block"
        >
          <div className="flex items-center justify-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <span>Notifications</span>
            <span className="text-[var(--text-faint)] group-hover:text-blue-500">📬</span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">
            {loading ? "..." : summary?.unread_notifications ?? 0}
          </div>
          <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">Require review</span>
        </Link>

        {/* Active Alerts */}
        <Link
          href="/alerts"
          className="p-4 text-center hover:bg-[var(--bg-card-hover)] transition-colors group block"
        >
          <div className="flex items-center justify-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <span>Active Alerts</span>
            <span className="text-[var(--text-faint)] group-hover:text-rose-500">🔔</span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">
            {loading ? "..." : summary?.active_alerts ?? 0}
          </div>
          <span className="text-[10px] text-rose-600 dark:text-rose-400 font-medium">Unread triggers</span>
        </Link>

        {/* Watched Bills */}
        <button
          onClick={() => setEntityTab("bills")}
          className="p-4 text-center hover:bg-[var(--bg-card-hover)] transition-colors group block w-full"
        >
          <div className="flex items-center justify-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <span>Watched Bills</span>
            <span className="text-[var(--text-faint)] group-hover:text-blue-500">📜</span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">
            {loading ? "..." : summary?.watched_bills ?? 0}
          </div>
          <span className="text-[10px] text-[var(--text-muted)]">Central &amp; State</span>
        </button>

        {/* Watched Companies */}
        <button
          onClick={() => setEntityTab("companies")}
          className="p-4 text-center hover:bg-[var(--bg-card-hover)] transition-colors group block w-full"
        >
          <div className="flex items-center justify-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <span>Watched Companies</span>
            <span className="text-[var(--text-faint)] group-hover:text-blue-500">🏢</span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">
            {loading ? "..." : summary?.watched_companies ?? 0}
          </div>
          <span className="text-[10px] text-[var(--text-muted)]">Corporate exposure</span>
        </button>

        {/* Watched Industries */}
        <button
          onClick={() => setEntityTab("industries")}
          className="p-4 text-center hover:bg-[var(--bg-card-hover)] transition-colors group block w-full"
        >
          <div className="flex items-center justify-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <span>Industries</span>
            <span className="text-[var(--text-faint)] group-hover:text-blue-500">🏭</span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">
            {loading ? "..." : summary?.watched_industries ?? 0}
          </div>
          <span className="text-[10px] text-[var(--text-muted)]">Monitored sectors</span>
        </button>

        {/* Recent Changes Count */}
        <div className="p-4 text-center">
          <div className="flex items-center justify-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <span>Recent Changes</span>
            <span className="text-[var(--text-faint)]">📡</span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-tabular text-blue-600 dark:text-blue-400">
            {loading ? "..." : summary?.recent_changes_count ?? 0}
          </div>
          <span className="text-[10px] text-[var(--text-muted)]">Last 7 days</span>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 3. YOUR LEGISLATIVE INTELLIGENCE & CHANGE FEED                       */}
      {/* -------------------------------------------------------------------- */}
      <div className="space-y-4 p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-default)] shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--border-subtle)] pb-3">
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-amber-500 font-bold text-xs">✦</span>
              <span className="text-[10px] font-bold uppercase tracking-widest text-amber-600 dark:text-amber-400 font-mono">
                Personalized Relevance Layer
              </span>
            </div>
            <h2 className="text-base font-bold text-[var(--text-primary)]">Your Legislative Intelligence</h2>
          </div>
          <div className="flex items-center gap-2 flex-wrap text-[10px] font-mono">
            <span className="px-2 py-0.5 rounded bg-[var(--color-success-bg)] text-[var(--color-success)] border border-[var(--color-success-border)]">MODELLED</span>
            <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20">KNOWLEDGE ONLY</span>
            <span className="px-2 py-0.5 rounded bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)]">LIVE</span>
            <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">VERIFIED</span>
            <Link
              href="/portfolio"
              className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold font-sans text-xs transition-colors ml-1 shadow-xs"
            >
              Open Portfolio Exposure →
            </Link>
          </div>
        </div>

        {/* Highlights Grid */}
        {decisionIntel && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
            {decisionIntel.relevant_new_bills.slice(0, 3).map((b) => (
              <div key={b.bill_id} className="p-3.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] space-y-2 hover:border-[var(--border-strong)] transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    {b.relevance_tier}
                  </span>
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">
                    {b.model_status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-[var(--text-primary)] line-clamp-1">
                  <Link href={`/bills/${b.bill_id}`} className="hover:text-blue-600 dark:hover:text-blue-400">
                    {b.bill_title}
                  </Link>
                </h4>
                <p className="text-[11px] text-[var(--text-muted)] line-clamp-2 leading-relaxed">
                  {b.primary_linkage_reason}
                </p>
                {(b as any).pre_event_public_information && (
                  <div className="p-1.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] text-[10px] text-[var(--text-secondary)]">
                    <span className="font-semibold mr-1">Pre-Event Info:</span>
                    {(b as any).pre_event_public_information.classification?.replace(/_/g, " ")} ({(b as any).pre_event_public_information.public_information_evidence})
                  </div>
                )}
                <div className="flex items-center justify-between text-[10px] text-[var(--text-faint)] pt-1 border-t border-[var(--border-subtle)]">
                  <span className="capitalize">{b.jurisdiction} {b.state ? `• ${b.state}` : ""}</span>
                  <span className="capitalize text-[var(--text-muted)] font-medium">{b.status}</span>
                </div>
              </div>
            ))}
            {decisionIntel.relevant_new_bills.length === 0 && (
              <div className="col-span-full p-4 text-center text-xs text-[var(--text-faint)] border border-dashed border-[var(--border-default)] rounded-xl">
                No new legislative measures currently match your tracked holdings.
              </div>
            )}
          </div>
        )}

        {/* Personalized Change Feed */}
        {changeFeed.length > 0 && (
          <div className="pt-3 border-t border-[var(--border-subtle)] space-y-2">
            <h3 className="text-xs font-bold text-[var(--text-secondary)] flex items-center gap-1.5">
              <span>📡</span>
              <span>Personalized Change Feed (No Polling Noise)</span>
            </h3>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {changeFeed.slice(0, 4).map((ch) => (
                <div key={ch.event_id} className="p-2.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 flex-shrink-0">
                      {ch.event_type}
                    </span>
                    <span className="font-semibold text-[var(--text-primary)] truncate">{ch.bill_title}</span>
                    <span className="text-[var(--text-muted)] text-[11px] truncate hidden sm:inline">• {ch.relevance_reason}</span>
                  </div>
                  <Link href={ch.deep_link} className="text-[11px] text-blue-600 dark:text-blue-400 hover:underline flex-shrink-0 ml-2">
                    Review →
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 4. MASTER-DETAIL DUAL COLUMNS                                        */}
      {/* -------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Monitored Entities (Grouped Activity) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--border-default)] pb-3">
            <div>
              <h2 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                Monitored Entities
                <span className="text-xs font-normal text-[var(--text-muted)] font-mono">
                  ({grouped?.total_watched ?? 0} total items)
                </span>
              </h2>
            </div>

            {/* Entity Filter Tabs */}
            <div className="flex flex-wrap items-center gap-1 bg-[var(--bg-surface)] p-1 rounded-lg border border-[var(--border-default)]">
              <button
                onClick={() => setEntityTab("bills")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "bills" ? "bg-blue-600 text-white font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Bills ({grouped?.bills.length ?? 0})
              </button>
              <button
                onClick={() => setEntityTab("companies")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "companies" ? "bg-blue-600 text-white font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Companies ({grouped?.companies.length ?? 0})
              </button>
              <button
                onClick={() => setEntityTab("industries")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "industries" ? "bg-blue-600 text-white font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Industries ({grouped?.industries.length ?? 0})
              </button>
              <button
                onClick={() => setEntityTab("jurisdictions")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  entityTab === "jurisdictions" ? "bg-blue-600 text-white font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                States ({grouped?.jurisdictions.length ?? 0})
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="space-y-3">
            {loading && (
              <div className="space-y-3">
                <SkeletonCard />
                <SkeletonCard />
              </div>
            )}

            {!loading && grouped && (
              <>
                {/* Bills Tab */}
                {entityTab === "bills" && (
                  grouped.bills.length === 0 ? (
                    <EmptyState
                      title="No Monitored Bills"
                      description="Monitors active parliamentary and state legislative developments. Track bills to receive automated stage progression alerts, clause amendment diffs, and procedural intelligence."
                      action={
                        <div className="flex flex-wrap items-center justify-center gap-2">
                          <Link
                            href="/bills"
                            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold inline-block transition-colors"
                          >
                            Explore Legislative Bills →
                          </Link>
                          <Link
                            href="/watchlists"
                            className="px-3.5 py-1.5 rounded-lg bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-default)] text-xs font-semibold inline-block transition-colors"
                          >
                            Manage Watchlists
                          </Link>
                        </div>
                      }
                    />
                  ) : (
                    grouped.bills.map((b) => (
                      <div
                        key={b.entity_id}
                        className="p-4 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl hover:border-[var(--border-strong)] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-default)] uppercase">
                              {b.jurisdiction}
                            </span>
                            {b.state && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)]">
                                {b.state}
                              </span>
                            )}
                            <span className="text-xs text-[var(--text-muted)]">In watchlist:</span>
                            <span className="text-xs font-medium text-[var(--text-secondary)]">
                              {b.watchlist_name}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-[var(--text-primary)] hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                            <Link href={b.deep_link}>{b.entity_name || b.entity_id}</Link>
                          </h4>
                          <p className="text-xs text-[var(--text-muted)]">
                            {b.latest_activity}
                          </p>
                        </div>

                        <div className="flex items-center gap-3 flex-shrink-0">
                          {b.alert_count > 0 && (
                            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[var(--color-danger-bg)] text-[var(--color-danger)] border border-[var(--color-danger-border)]">
                              {b.alert_count} Alerts
                            </span>
                          )}
                          <Link
                            href={b.deep_link}
                            className="px-3 py-1.5 text-xs font-medium bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] rounded-lg transition-colors border border-[var(--border-default)]"
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
                    <EmptyState
                      title="No Monitored Companies"
                      description="Tracks corporate entities exposed to regulatory, statutory, or tax changes. Evaluates quantitative sensitivity and isolates qualitative intelligence entities."
                      action={
                        <div className="flex flex-wrap items-center justify-center gap-2">
                          <Link
                            href="/companies"
                            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold inline-block transition-colors"
                          >
                            Explore Corporate Universe →
                          </Link>
                          <Link
                            href="/portfolio"
                            className="px-3.5 py-1.5 rounded-lg bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-default)] text-xs font-semibold inline-block transition-colors"
                          >
                            Set Up Portfolio Exposure
                          </Link>
                        </div>
                      }
                    />
                  ) : (
                    grouped.companies.map((c) => (
                      <div
                        key={c.entity_id}
                        className="p-4 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl hover:border-[var(--border-strong)] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-default)]">
                              {c.entity_id}
                            </span>
                            {c.extra_metadata?.sector && (
                              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)]">
                                {c.extra_metadata.sector}
                              </span>
                            )}
                            <span className="text-xs text-[var(--text-muted)]">Watchlist:</span>
                            <span className="text-xs font-medium text-[var(--text-secondary)]">
                              {c.watchlist_name}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-[var(--text-primary)] hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                            <Link href={c.deep_link}>{c.entity_name || c.entity_id}</Link>
                          </h4>
                          <p className="text-xs text-[var(--text-muted)]">{c.latest_activity}</p>
                        </div>

                        <div className="flex items-center gap-3 flex-shrink-0">
                          {c.extra_metadata?.is_quant_eligible ? (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--color-success-bg)] text-[var(--color-success)] border border-[var(--color-success-border)]">
                              Quant Modeled
                            </span>
                          ) : (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-muted)] border border-[var(--border-default)]">
                              Qualitative Intel
                            </span>
                          )}
                          <Link
                            href={c.deep_link}
                            className="px-3 py-1.5 text-xs font-medium bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] rounded-lg transition-colors border border-[var(--border-default)]"
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
                    <EmptyState
                      title="No Monitored Industries"
                      description="Tracks sectoral regulatory developments across Banking, Telecom, Energy, Pharmaceuticals, and Manufacturing to anticipate policy shifts and compliance standards."
                      action={
                        <Link
                          href="/industries"
                          className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold inline-block transition-colors"
                        >
                          Explore Industry Taxonomy →
                        </Link>
                      }
                    />
                  ) : (
                    grouped.industries.map((ind) => (
                      <div
                        key={ind.entity_id}
                        className="p-4 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl hover:border-[var(--border-strong)] transition-colors flex items-center justify-between shadow-xs"
                      >
                        <div>
                          <h4 className="text-sm font-semibold text-[var(--text-primary)]">
                            <Link href={ind.deep_link} className="hover:text-blue-600 dark:hover:text-blue-400">
                              {ind.entity_name || ind.entity_id}
                            </Link>
                          </h4>
                          <p className="text-xs text-[var(--text-muted)]">{ind.latest_activity}</p>
                        </div>
                        <Link
                          href={ind.deep_link}
                          className="px-3 py-1.5 text-xs font-medium bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] rounded-lg transition-colors border border-[var(--border-default)]"
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
                    <EmptyState
                      title="No Monitored Jurisdictions"
                      description="Monitors state legislative assemblies (Andhra Pradesh, Karnataka, Kerala, Telangana) and local gazettes for sub-national compliance and statutory orders."
                      action={
                        <Link
                          href="/states"
                          className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold inline-block transition-colors"
                        >
                          Explore State Assemblies →
                        </Link>
                      }
                    />
                  ) : (
                    grouped.jurisdictions.map((j) => (
                      <div
                        key={j.entity_id}
                        className="p-4 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl hover:border-[var(--border-strong)] transition-colors flex items-center justify-between shadow-xs"
                      >
                        <div>
                          <h4 className="text-sm font-semibold text-[var(--text-primary)] capitalize">
                            {j.entity_name || j.entity_id}
                          </h4>
                          <p className="text-xs text-[var(--text-muted)]">{j.latest_activity}</p>
                        </div>
                        <Link
                          href={j.deep_link}
                          className="px-3 py-1.5 text-xs font-medium bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] rounded-lg transition-colors border border-[var(--border-default)]"
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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--border-default)] pb-3">
            <h2 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
              <span>Recent Activity Feed</span>
            </h2>

            {/* Filter buttons */}
            <div className="flex flex-wrap items-center gap-1 bg-[var(--bg-surface)] p-1 rounded-lg border border-[var(--border-default)]">
              <button
                onClick={() => setActivityFilter("ALL")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  activityFilter === "ALL" ? "bg-blue-600 text-white font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setActivityFilter("ALERTS")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  activityFilter === "ALERTS" ? "bg-blue-600 text-white font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Alerts
              </button>
              <button
                onClick={() => setActivityFilter("MONITORING")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  activityFilter === "MONITORING" ? "bg-blue-600 text-white font-semibold" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}
              >
                Monitoring
              </button>
            </div>
          </div>

          {/* Activity Items */}
          <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
            {loading && (
              <div className="space-y-3">
                <SkeletonCard />
                <SkeletonCard />
              </div>
            )}

            {!loading && filteredActivity.length === 0 && (
              <EmptyState
                title="No Recent Activity"
                description="Chronological stream of legislative status changes, risk adjustments, and monitoring alerts for items in your watchlists with zero polling noise."
                action={
                  <Link
                    href="/live-discovery"
                    className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors inline-block"
                  >
                    View Live Intake Feed →
                  </Link>
                }
              />
            )}

            {!loading &&
              filteredActivity.map((item) => (
                <div
                  key={item.activity_id}
                  className="p-3.5 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl space-y-2 hover:border-[var(--border-strong)] transition-colors shadow-xs"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <EpistemicBadge type={item.epistemic_status} size="xs" showBracket />
                      <span className="text-xs font-medium text-[var(--text-secondary)]">
                        {item.entity_name}
                      </span>
                    </div>
                    <span className="text-[11px] text-[var(--text-faint)] font-mono">
                      {item.timestamp ? new Date(item.timestamp).toLocaleDateString() : ""}
                    </span>
                  </div>

                  <p className="text-xs font-medium text-[var(--text-primary)]">{item.title}</p>
                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">{item.summary}</p>

                  <div className="flex items-center justify-between pt-1 border-t border-[var(--border-subtle)]">
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">
                      Type: {item.activity_type}
                    </span>
                    <Link
                      href={item.deep_link}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-semibold"
                    >
                      View Details →
                    </Link>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 5. RISK & PRE-EVENT ANTICIPATION ANALYTICS SNAPSHOT                  */}
      {/* -------------------------------------------------------------------- */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-6 space-y-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--border-default)] pb-4">
          <div>
            <h2 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
              <span>Risk &amp; Anticipation Analytics Snapshot</span>
              <span className="text-xs px-2 py-0.5 rounded bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)] font-semibold font-mono">
                Verified Diagnostics
              </span>
            </h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Strictly consumes frozen models and risk ratings with full State &amp; Intelligence Firewall compliance.
            </p>
          </div>

          <div className="text-[11px] text-[var(--text-muted)] font-mono bg-[var(--bg-base)] px-3 py-1.5 rounded border border-[var(--border-default)]">
            Institutional Epistemic Rule: [OBSERVED] ⟂ [DERIVED] ⟂ [PREDICTION]
          </div>
        </div>

        {/* Snapshot Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {loading && (
            <div className="col-span-full grid grid-cols-1 md:grid-cols-3 gap-4">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          )}

          {!loading && analytics.length === 0 && (
            <EmptyState
              className="col-span-full"
              title="No Risk & Anticipation Analytics"
              description="Add securities or legislative measures to your watchlists to view risk classification and anticipation diagnostics."
            />
          )}

          {!loading &&
            analytics.map((it, idx) => (
              <div
                key={idx}
                className="bg-[var(--bg-base)] border border-[var(--border-default)] rounded-xl p-4 space-y-3"
              >
                {/* Card Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-default)]">
                      {it.entity_type}
                    </span>
                    <EpistemicBadge type={it.epistemic_label} size="xs" showBracket />
                  </div>
                  <span className="text-[10px] text-[var(--text-faint)] font-mono">
                    {it.entity_id}
                  </span>
                </div>

                <h4 className="text-sm font-semibold text-[var(--text-primary)] truncate">
                  {it.entity_name}
                </h4>

                {/* Firewall alerts */}
                {it.is_state_firewall_active && (
                  <div className="p-2.5 rounded bg-[var(--color-warning-bg)] border border-[var(--color-warning-border)] text-xs text-[var(--color-warning)]">
                    🛡 <strong>State Prediction Firewall Active</strong>: {it.firewall_note || "State stock predictions remain strictly 0."}
                  </div>
                )}

                {it.is_intelligence_firewall_active && (
                  <div className="p-2.5 rounded bg-[var(--bg-card)] border border-[var(--border-strong)] text-xs text-[var(--text-secondary)]">
                    🛡 <strong>Intelligence Company Firewall Active</strong>: {it.firewall_note}
                  </div>
                )}

                {/* Quantitative Metrics for Central Quant Securities */}
                {!it.is_state_firewall_active && !it.is_intelligence_firewall_active && (
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[var(--border-subtle)] text-xs">
                    <div>
                      <span className="text-[var(--text-faint)] text-[11px]">Risk Category</span>
                      <p className="font-semibold text-[var(--text-primary)]">
                        {it.risk_level || "MODERATE"}
                        {it.risk_score !== null && it.risk_score !== undefined && (
                          <span className="text-[var(--text-muted)] font-normal font-tabular"> ({it.risk_score.toFixed(2)})</span>
                        )}
                      </p>
                    </div>

                    <div>
                      <span className="text-[var(--text-faint)] text-[11px]">Anticipation Bias</span>
                      <p className="font-semibold text-[var(--text-primary)]">
                        {it.anticipation_tier || "NOT_FLAGGED"}
                        {it.anticipation_score !== null && it.anticipation_score !== undefined && (
                          <span className="text-[var(--text-muted)] font-normal font-tabular"> ({it.anticipation_score.toFixed(2)})</span>
                        )}
                      </p>
                    </div>

                    {it.prediction_record && (
                      <div className="col-span-2 mt-1 p-2 bg-[var(--bg-card)] rounded border border-[var(--border-default)]">
                        <span className="text-[var(--text-faint)] text-[10px] block">Model Prediction</span>
                        <div className="flex items-center justify-between text-xs font-medium text-[var(--text-primary)]">
                          <span>Direction: <strong className="text-emerald-500 dark:text-emerald-400 font-bold">{it.prediction_record.direction}</strong></span>
                          <span>Confidence: <strong className="text-blue-600 dark:text-blue-400 font-bold">{it.prediction_record.confidence}</strong></span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 6. GROUNDED AI ASSISTANT                                             */}
      {/* -------------------------------------------------------------------- */}
      <AIWorkspaceAssistant />
    </div>
  );
}

export default WorkspacePage;
