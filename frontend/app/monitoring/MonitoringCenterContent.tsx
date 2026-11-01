/**
 * app/monitoring/MonitoringCenterContent.tsx
 * ===========================================
 * Legislative Monitoring & Observability Center (Task 1.11A Redesign).
 *
 * Implements:
 * - 3-Level Information Architecture (Overview, Detail, Diagnostics)
 * - Restrained editorial-finance aesthetic adhering to SEANCE_DESIGN_SYSTEM.md
 * - Factual telemetry from /api/v1/monitoring/* and /api/v1/freshness
 * - Strict Central vs State statutory firewall (State stock predictions permanently 0)
 * - Full URL search parameter synchronization for tab and drawer state
 */

"use client";

import React, { useState, useEffect, useCallback, useRef, useTransition } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
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
import { cn } from "@/lib/utils";

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

interface TabItem {
  id: TabId;
  label: string;
  glyph: string;
  description: string;
}

const TABS: TabItem[] = [
  { id: "overview", label: "Overview", glyph: "◉", description: "Operational telemetry & pipeline freshness" },
  { id: "sources", label: "Sources", glyph: "🔌", description: "Configured central & state portals" },
  { id: "history", label: "Check History", glyph: "⏱", description: "Audit trail of surveillance runs" },
  { id: "changes", label: "Detected Changes", glyph: "🔄", description: "Verified legislative deltas & diffs" },
  { id: "discovery", label: "Discovery Feed", glyph: "📡", description: "Intake stream of gazetted enactments" },
  { id: "scheduler", label: "Scheduler", glyph: "⚙", description: "Surveillance thread & run controls" },
  { id: "ai", label: "AI Analyst", glyph: "✦", description: "Grounded surveillance inquiry assistant" },
];

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function MonitoringCenterContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  // Read initial tab from URL search parameters
  const initialTabParam = searchParams.get("tab") as TabId | null;
  const initialSourceParam = searchParams.get("source");
  const initialEventParam = searchParams.get("event");

  const [activeTab, setActiveTab] = useState<TabId>(
    initialTabParam && TABS.some((t) => t.id === initialTabParam) ? initialTabParam : "overview"
  );

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
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(initialSourceParam ?? null);
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
  const [selectedEventId, setSelectedEventId] = useState<string | null>(initialEventParam ?? null);
  const [eventDetail, setEventDetail] = useState<ChangeEventDetail | null>(null);
  const [eventDetailLoading, setEventDetailLoading] = useState(false);
  const [eventDetailError, setEventDetailError] = useState<string | null>(null);

  // Discovery feed
  const [discovery, setDiscovery] = useState<PaginatedResponse<ChangeEventDetail> | null>(null);
  const [discoveryLoading, setDiscoveryLoading] = useState(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);
  const [discoveryPage, setDiscoveryPage] = useState(1);

  // Synchronize tab and drawer state from URL strictly on actual searchParams changes (e.g. browser back/forward)
  const prevSearchParamsRef = useRef<string>(searchParams ? searchParams.toString() : "");
  useEffect(() => {
    const currentQs = searchParams ? searchParams.toString() : "";
    if (currentQs === prevSearchParamsRef.current) return;
    prevSearchParamsRef.current = currentQs;

    const urlTab = searchParams.get("tab") as TabId | null;
    if (urlTab && TABS.some((t) => t.id === urlTab)) {
      setActiveTab(urlTab);
    }
    const urlSource = searchParams.get("source");
    setSelectedSourceId(urlSource);
    const urlEvent = searchParams.get("event");
    setSelectedEventId(urlEvent);
  }, [searchParams]);

  // ---------------------------------------------------------------------------
  // Data fetching
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

  // Source detail fetch
  useEffect(() => {
    if (!selectedSourceId) {
      setSourceDetail(null);
      return;
    }
    setSourceDetailLoading(true);
    setSourceDetailError(null);
    monitoringApi.getSource(selectedSourceId)
      .then((d) => setSourceDetail(d))
      .catch((e: unknown) => setSourceDetailError((e as Error).message ?? "Failed to load source detail"))
      .finally(() => setSourceDetailLoading(false));
  }, [selectedSourceId]);

  // Change event detail fetch
  useEffect(() => {
    if (!selectedEventId) {
      setEventDetail(null);
      return;
    }
    setEventDetailLoading(true);
    setEventDetailError(null);
    monitoringApi.getChangeDetail(selectedEventId)
      .then((d) => setEventDetail(d))
      .catch((e: unknown) => setEventDetailError((e as Error).message ?? "Failed to load change detail"))
      .finally(() => setEventDetailLoading(false));
  }, [selectedEventId]);

  // ---------------------------------------------------------------------------
  // URL Parameter Synchronization Handlers
  // ---------------------------------------------------------------------------

  const updateUrlParams = useCallback((updater: (params: URLSearchParams) => void) => {
    try {
      const params = new URLSearchParams(searchParams ? searchParams.toString() : "");
      updater(params);
      const qs = params.toString();
      const target = qs ? `${pathname}?${qs}` : pathname;
      if (router && typeof router.replace === "function") {
        router.replace(target, { scroll: false });
      } else if (router && typeof router.push === "function") {
        router.push(target);
      }
    } catch {
      // Ignore navigation update errors in test or SSR environments
    }
  }, [router, pathname, searchParams]);

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    startTransition(() => {
      updateUrlParams((params) => {
        params.set("tab", tab);
      });
    });
  };

  const handleSourceClick = (source: MonitoringSourceItem) => {
    setSelectedSourceId(source.source_id);
    setSourceDetail(null);
    startTransition(() => {
      updateUrlParams((params) => {
        params.set("source", source.source_id);
      });
    });
  };

  const handleCloseSourceDrawer = () => {
    setSelectedSourceId(null);
    startTransition(() => {
      updateUrlParams((params) => {
        params.delete("source");
      });
    });
  };

  const handleEventClick = (event: ChangeEventDetail) => {
    setSelectedEventId(event.event_id);
    setEventDetail(null);
    startTransition(() => {
      updateUrlParams((params) => {
        params.set("event", event.event_id);
      });
    });
  };

  const handleCloseEventDrawer = () => {
    setSelectedEventId(null);
    startTransition(() => {
      updateUrlParams((params) => {
        params.delete("event");
      });
    });
  };

  const handleChangeFilterChange = (f: Partial<typeof changesFilters>) => {
    setChangesFilters((prev) => ({ ...prev, ...f }));
    setChangesPage(1);
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1400px] mx-auto min-h-screen">
      {/* Editorial Page Header */}
      <header className="border-b border-[var(--border-hairline)] pb-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-blue-400">
                Observability Center
              </span>
              <span className="text-[var(--text-faint)]">/</span>
              <span className="text-xs font-mono text-[var(--text-faint)] uppercase">
                Continuous Ingestion
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              Legislative Monitoring & Discovery Center
            </h1>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] max-w-3xl leading-relaxed">
              Real-time legislative change detection across Central Parliament and 4 Sub-National State Assemblies (AP, KA, KL, TS). State legislative monitoring produces zero quantitative stock predictions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)] bg-[var(--bg-card)] border border-[var(--border-hairline)] rounded-lg px-3 py-2 shadow-xs">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true" />
              <span>Surveillance active</span>
            </div>
          </div>
        </div>
      </header>

      {/* Mandatory Jurisdiction & Firewall Banner */}
      <JurisdictionBanner variant="compact" />

      {/* Tab Navigation Segmented Bar */}
      <nav
        role="tablist"
        aria-label="Monitoring center sections"
        className="flex items-center gap-1 border-b border-[var(--border-hairline)] overflow-x-auto pb-0 -mb-2"
      >
        {TABS.map((tab) => {
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              role="tab"
              aria-selected={isSelected}
              aria-controls={`panel-${tab.id}`}
              onClick={() => handleTabChange(tab.id)}
              className={cn(
                "flex items-center gap-2 px-3.5 py-2.5 text-xs font-mono font-semibold border-b-2 transition-all whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 select-none",
                isSelected
                  ? "border-blue-500 text-blue-400 bg-[var(--bg-surface)]/60 rounded-t-md"
                  : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]"
              )}
            >
              <span aria-hidden="true" className="text-xs">{tab.glyph}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Tab Panels */}
      <main>
        {/* Overview Tab Panel */}
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
            onTriggerPoll={fetchOverview}
          />
        </section>

        {/* Sources Registry Tab Panel */}
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

        {/* Check History Tab Panel */}
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

        {/* Detected Changes Tab Panel */}
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

        {/* Discovery Feed Tab Panel */}
        <section
          id="panel-discovery"
          role="tabpanel"
          aria-labelledby="tab-discovery"
          hidden={activeTab !== "discovery"}
          className="animate-fade-in space-y-4"
        >
          <JurisdictionBanner variant="full" />
          <DiscoveryFeed
            data={discovery}
            loading={discoveryLoading}
            error={discoveryError}
            onPageChange={setDiscoveryPage}
            onEventClick={handleEventClick}
          />
        </section>

        {/* Scheduler Tab Panel */}
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

        {/* AI Analyst Tab Panel */}
        <section
          id="panel-ai"
          role="tabpanel"
          aria-labelledby="tab-ai"
          hidden={activeTab !== "ai"}
          className="animate-fade-in"
        >
          <MonitoringAIAnalyst className="min-h-[520px]" />
        </section>
      </main>

      {/* Source Detail Drawer */}
      <SourceDetailDrawer
        sourceId={selectedSourceId}
        data={sourceDetail}
        loading={sourceDetailLoading}
        error={sourceDetailError}
        onClose={handleCloseSourceDrawer}
      />

      {/* Change Detail Drawer */}
      <ChangeDetailDrawer
        eventId={selectedEventId}
        data={eventDetail}
        loading={eventDetailLoading}
        error={eventDetailError}
        onClose={handleCloseEventDrawer}
      />
    </div>
  );
}
