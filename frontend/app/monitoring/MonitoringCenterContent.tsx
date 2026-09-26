/**
 * app/monitoring/MonitoringCenterContent.tsx
 * ===========================================
 * Full client component for the Legislative Monitoring & Discovery Center.
 *
 * Tabs:
 *   Overview | Sources | Check History | Detected Changes | Discovery Feed | AI Analyst
 *
 * All data flows from existing /api/v1/monitoring/* endpoints.
 * No automatic stock prediction. State predictions remain strictly 0.
 *
 * Task 8.14.9 — Legislative Monitoring & Discovery Center.
 */

"use client";

import React, { useState, useEffect, useCallback } from "react";
import type {
  ChangeEventDetail,
  MonitoringOverview,
  MonitoringRunDetail,
  MonitoringSourceDetail,
  MonitoringSourceItem,
  PaginatedResponse,
} from "@/types/api";
import { monitoringApi } from "@/lib/api/monitoring";
import { JurisdictionBanner } from "@/components/monitoring/JurisdictionBanner";
import { MonitoringOverviewPanel } from "@/components/monitoring/MonitoringOverviewPanel";
import { SourceRegistryTable } from "@/components/monitoring/SourceRegistryTable";
import { SourceDetailDrawer } from "@/components/monitoring/SourceDetailDrawer";
import { CheckHistoryTable } from "@/components/monitoring/CheckHistoryTable";
import { ChangesFeed } from "@/components/monitoring/ChangesFeed";
import { DiscoveryFeed } from "@/components/monitoring/DiscoveryFeed";
import { SchedulerPanel } from "@/components/monitoring/SchedulerPanel";
import { ChangeDetailDrawer } from "@/components/monitoring/ChangeDetailDrawer";
import { MonitoringAIAnalyst } from "@/components/monitoring/MonitoringAIAnalyst";

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

type TabId =
  | "overview"
  | "sources"
  | "history"
  | "changes"
  | "discovery"
  | "scheduler"
  | "ai";

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "sources", label: "Sources", icon: "🔌" },
  { id: "history", label: "Check History", icon: "🕐" },
  { id: "changes", label: "Detected Changes", icon: "🔄" },
  { id: "discovery", label: "Discovery Feed", icon: "📡" },
  { id: "scheduler", label: "Scheduler", icon: "⏱" },
  { id: "ai", label: "AI Analyst", icon: "🤖" },
];

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function MonitoringCenterContent() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  // Overview
  const [overview, setOverview] = useState<MonitoringOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState<string | null>(null);

  // Sources
  const [sources, setSources] = useState<PaginatedResponse<MonitoringSourceItem> | null>(null);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [sourcesError, setSourcesError] = useState<string | null>(null);
  const [sourcePage, setSourcePage] = useState(1);
  const [sourceJurisdiction, setSourceJurisdiction] = useState("");

  // Source detail drawer
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [sourceDetail, setSourceDetail] = useState<MonitoringSourceDetail | null>(null);
  const [sourceDetailLoading, setSourceDetailLoading] = useState(false);
  const [sourceDetailError, setSourceDetailError] = useState<string | null>(null);

  // Check history
  const [runs, setRuns] = useState<PaginatedResponse<MonitoringRunDetail> | null>(null);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);
  const [runsPage, setRunsPage] = useState(1);

  // Changes feed
  const [changes, setChanges] = useState<PaginatedResponse<ChangeEventDetail> | null>(null);
  const [changesLoading, setChangesLoading] = useState(false);
  const [changesError, setChangesError] = useState<string | null>(null);
  const [changesPage, setChangesPage] = useState(1);
  const [changesFilters, setChangesFilters] = useState({
    jurisdiction: "",
    event_type: "",
    source_id: "",
  });

  // Change detail drawer
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [eventDetail, setEventDetail] = useState<ChangeEventDetail | null>(null);
  const [eventDetailLoading, setEventDetailLoading] = useState(false);
  const [eventDetailError, setEventDetailError] = useState<string | null>(null);

  // Discovery feed (same data, no filters pre-applied)
  const [discovery, setDiscovery] = useState<PaginatedResponse<ChangeEventDetail> | null>(null);
  const [discoveryLoading, setDiscoveryLoading] = useState(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);
  const [discoveryPage, setDiscoveryPage] = useState(1);

  // ---------------------------------------------------------------------------
  // Data fetching — Tab-gated for performance
  // ---------------------------------------------------------------------------

  const fetchOverview = useCallback(async () => {
    setOverviewLoading(true);
    setOverviewError(null);
    try {
      const data = await monitoringApi.getOverview();
      setOverview(data);
    } catch (e: unknown) {
      setOverviewError((e as Error).message ?? "Failed to load overview");
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  const fetchSources = useCallback(async () => {
    setSourcesLoading(true);
    setSourcesError(null);
    try {
      const data = await monitoringApi.getSources({
        page: sourcePage,
        limit: 25,
        jurisdiction: sourceJurisdiction || undefined,
      });
      setSources(data);
    } catch (e: unknown) {
      setSourcesError((e as Error).message ?? "Failed to load sources");
    } finally {
      setSourcesLoading(false);
    }
  }, [sourcePage, sourceJurisdiction]);

  const fetchRuns = useCallback(async () => {
    setRunsLoading(true);
    setRunsError(null);
    try {
      const data = await monitoringApi.getRuns({ page: runsPage, limit: 20 });
      setRuns(data);
    } catch (e: unknown) {
      setRunsError((e as Error).message ?? "Failed to load run history");
    } finally {
      setRunsLoading(false);
    }
  }, [runsPage]);

  const fetchChanges = useCallback(async () => {
    setChangesLoading(true);
    setChangesError(null);
    try {
      const data = await monitoringApi.getChanges({
        page: changesPage,
        limit: 25,
        jurisdiction: changesFilters.jurisdiction || undefined,
        event_type: changesFilters.event_type || undefined,
        source_id: changesFilters.source_id || undefined,
      });
      setChanges(data);
    } catch (e: unknown) {
      setChangesError((e as Error).message ?? "Failed to load change events");
    } finally {
      setChangesLoading(false);
    }
  }, [changesPage, changesFilters]);

  const fetchDiscovery = useCallback(async () => {
    setDiscoveryLoading(true);
    setDiscoveryError(null);
    try {
      const data = await monitoringApi.getChanges({
        page: discoveryPage,
        limit: 25,
      });
      setDiscovery(data);
    } catch (e: unknown) {
      setDiscoveryError((e as Error).message ?? "Failed to load discovery feed");
    } finally {
      setDiscoveryLoading(false);
    }
  }, [discoveryPage]);

  // Tab-gated fetching
  useEffect(() => {
    if (activeTab === "overview") fetchOverview();
  }, [activeTab, fetchOverview]);

  useEffect(() => {
    if (activeTab === "sources") fetchSources();
  }, [activeTab, fetchSources]);

  useEffect(() => {
    if (activeTab === "history") fetchRuns();
  }, [activeTab, fetchRuns]);

  useEffect(() => {
    if (activeTab === "changes") fetchChanges();
  }, [activeTab, fetchChanges]);

  useEffect(() => {
    if (activeTab === "discovery") fetchDiscovery();
  }, [activeTab, fetchDiscovery]);

  // ---------------------------------------------------------------------------
  // Source detail fetch
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!selectedSourceId) return;
    setSourceDetailLoading(true);
    setSourceDetailError(null);
    monitoringApi.getSource(selectedSourceId).then((d) => {
      setSourceDetail(d);
    }).catch((e: unknown) => {
      setSourceDetailError((e as Error).message ?? "Failed to load source detail");
    }).finally(() => setSourceDetailLoading(false));
  }, [selectedSourceId]);

  // ---------------------------------------------------------------------------
  // Change event detail fetch
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!selectedEventId) return;
    setEventDetailLoading(true);
    setEventDetailError(null);
    monitoringApi.getChangeDetail(selectedEventId).then((d) => {
      setEventDetail(d);
    }).catch((e: unknown) => {
      setEventDetailError((e as Error).message ?? "Failed to load change detail");
    }).finally(() => setEventDetailLoading(false));
  }, [selectedEventId]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleSourceClick = (source: MonitoringSourceItem) => {
    setSelectedSourceId(source.source_id);
    setSourceDetail(null);
  };

  const handleEventClick = (event: ChangeEventDetail) => {
    setSelectedEventId(event.event_id);
    setEventDetail(null);
  };

  const handleChangeFilterChange = (f: Partial<typeof changesFilters>) => {
    setChangesFilters((prev) => ({ ...prev, ...f }));
    setChangesPage(1);
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="p-4 md:p-6 space-y-5 max-w-[1400px] mx-auto">
      {/* Page header */}
      <header>
        <div className="flex items-start justify-between gap-4 flex-wrap mb-1">
          <div>
            <h1 className="text-xl font-bold text-slate-100">
              Legislative Monitoring & Discovery Center
            </h1>
            <p className="text-sm text-slate-400 mt-0.5">
              Real-time legislative change detection · Central Parliament + State Assemblies
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true" />
            System operational · Additive monitoring only
          </div>
        </div>
      </header>

      {/* Jurisdiction Banner */}
      <JurisdictionBanner variant="compact" />

      {/* Tab Navigation */}
      <nav role="tablist" aria-label="Monitoring center sections" className="flex items-center gap-1 border-b border-slate-800 overflow-x-auto pb-0">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 ${
              activeTab === tab.id
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-500 hover:text-slate-300 hover:border-slate-600"
            }`}
          >
            <span aria-hidden="true">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Tab Panels */}
      <main>
        {/* Overview */}
        <section
          id="panel-overview"
          role="tabpanel"
          aria-labelledby="tab-overview"
          hidden={activeTab !== "overview"}
          className="animate-fade-in"
        >
          <MonitoringOverviewPanel
            data={overview}
            loading={overviewLoading}
            error={overviewError}
          />
        </section>

        {/* Sources */}
        <section
          id="panel-sources"
          role="tabpanel"
          aria-labelledby="tab-sources"
          hidden={activeTab !== "sources"}
          className="animate-fade-in"
        >
          <SourceRegistryTable
            data={sources}
            loading={sourcesLoading}
            error={sourcesError}
            onPageChange={setSourcePage}
            onSourceClick={handleSourceClick}
            jurisdictionFilter={sourceJurisdiction}
            onJurisdictionChange={(v) => { setSourceJurisdiction(v); setSourcePage(1); }}
          />
        </section>

        {/* Check History */}
        <section
          id="panel-history"
          role="tabpanel"
          aria-labelledby="tab-history"
          hidden={activeTab !== "history"}
          className="animate-fade-in"
        >
          <CheckHistoryTable
            data={runs}
            loading={runsLoading}
            error={runsError}
            onPageChange={setRunsPage}
          />
        </section>

        {/* Detected Changes */}
        <section
          id="panel-changes"
          role="tabpanel"
          aria-labelledby="tab-changes"
          hidden={activeTab !== "changes"}
          className="animate-fade-in"
        >
          <ChangesFeed
            data={changes}
            loading={changesLoading}
            error={changesError}
            filters={changesFilters}
            onFilterChange={handleChangeFilterChange}
            onPageChange={setChangesPage}
            onEventClick={handleEventClick}
          />
        </section>

        {/* Discovery Feed */}
        <section
          id="panel-discovery"
          role="tabpanel"
          aria-labelledby="tab-discovery"
          hidden={activeTab !== "discovery"}
          className="animate-fade-in"
        >
          <div className="mb-4">
            <JurisdictionBanner variant="full" />
          </div>
          <DiscoveryFeed
            data={discovery}
            loading={discoveryLoading}
            error={discoveryError}
            onPageChange={setDiscoveryPage}
            onEventClick={handleEventClick}
          />
        </section>

        {/* Scheduler */}
        <section
          id="panel-scheduler"
          role="tabpanel"
          aria-labelledby="tab-scheduler"
          hidden={activeTab !== "scheduler"}
          className="animate-fade-in"
        >
          <SchedulerPanel
            data={overview?.scheduler ?? null}
            loading={overviewLoading}
            error={overviewError}
          />
        </section>

        {/* AI Analyst */}
        <section
          id="panel-ai"
          role="tabpanel"
          aria-labelledby="tab-ai"
          hidden={activeTab !== "ai"}
          className="animate-fade-in"
        >
          <MonitoringAIAnalyst className="min-h-[500px]" />
        </section>
      </main>

      {/* Source Detail Drawer */}
      <SourceDetailDrawer
        sourceId={selectedSourceId}
        data={sourceDetail}
        loading={sourceDetailLoading}
        error={sourceDetailError}
        onClose={() => setSelectedSourceId(null)}
      />

      {/* Change Detail Drawer */}
      <ChangeDetailDrawer
        eventId={selectedEventId}
        data={eventDetail}
        loading={eventDetailLoading}
        error={eventDetailError}
        onClose={() => setSelectedEventId(null)}
      />
    </div>
  );
}
