/**
 * app/bills/[billId]/BillDetailContent.tsx
 * ==========================================
 * Editorial-Finance Bill Detail Dossier (Task 1.9A Redesign).
 *
 * Consolidates the 12 legacy tabs into 4 primary editorial sections:
 * 1. Executive Summary & Journey:
 *    - Prominent plain-language brief
 *    - Factual executive summary
 *    - Procedural milestones & legislative journey
 *    - Legislative timeline & amendment deltas ("What Changed")
 *    - Policy & economic vectors
 * 2. Statutory Mechanics:
 *    - Key provisions & statutory clauses
 *    - Regulatory oversight authority & interactions
 *    - Financial terms, statutory powers, and penalties
 * 3. Corporate & Market Impact:
 *    - Corporate exposure matrix (direct vs indirect)
 *    - Central quantitative market predictions (with StatePredictionFirewall)
 *    - Pre-event anticipation & information diffusion diagnostics
 *    - Affected sectors & industries taxonomy
 *    - Multi-stakeholder intelligence (Investor, Business, Citizen, Regulator)
 * 4. Provenance & Evidence:
 *    - Official gazette records & verifiable source links
 *    - Grounded Groq AI Research Copilot
 *    - Immutable audit trail & data provenance
 *
 * Summary Rail:
 * - Responsive, non-obscuring right-hand rail containing only grounded facts
 * - Jurisdiction, status, official dates, analytical scope, exposure count
 * - Grounded actions: Watchlist, Grounded AI prompt, Related Bills
 *
 * Backward-Compatibility:
 * - Maps all legacy ?tab= query parameters to the appropriate section and sub-view
 * - Supports browser back/forward history navigation via popstate
 * - Keeps all 12 legacy tabs accessible for deep links, bookmarks, and tests
 */

"use client";

import React, { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { billsApi } from "@/lib/api/bills";
import { isApiError } from "@/lib/errors";
import { formatDate } from "@/lib/utils";
import type {
  BillDetailResponse,
  BillPredictionStatusResponse,
  BillCompanyExposure,
  EnrichedBillDossier,
} from "@/types/api";

import { BillHeader } from "@/components/bills/BillHeader";
import { ExecutiveSummary } from "@/components/bills/ExecutiveSummary";
import { ProceduralJourney } from "@/components/bills/ProceduralJourney";
import { KeyProvisions } from "@/components/bills/KeyProvisions";
import { PolicyEconomicIntelligence } from "@/components/bills/PolicyEconomicIntelligence";
import { CorporateExposureTable } from "@/components/bills/CorporateExposureTable";
import { CentralPredictionSection } from "@/components/bills/CentralPredictionSection";
import { AnticipationSection } from "@/components/bills/AnticipationSection";
import { StakeholderIntelligence } from "@/components/bills/StakeholderIntelligence";
import { ProvenancePanel } from "@/components/bills/ProvenancePanel";
import { AIAssistantPanel } from "@/components/bills/AIAssistantPanel";
import { WatchlistModal } from "@/components/bills/WatchlistModal";
import { RelatedBillsCard } from "@/components/bills/RelatedBillsCard";
import { LegislativeTimeline } from "@/components/bills/LegislativeTimeline";
import { WhatChangedView } from "@/components/bills/WhatChangedView";
import { PlainLanguageSection } from "@/components/bills/PlainLanguageSection";
import { SectorIndustrySection } from "@/components/bills/SectorIndustrySection";
import { DocumentSourcesSection } from "@/components/bills/DocumentSourcesSection";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, ModelStatusBadge } from "@/components/ui/Badge";
import { MarketRelevanceBadge } from "@/components/coverage/CapabilityBadge";
import { ErrorState, SkeletonCard } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";

// ============================================================================
// Canonical 4 Editorial Sections & Sub-navigation Hierarchy
// ============================================================================

export type BillSectionId = "executive" | "mechanics" | "impact" | "provenance";

export interface BillSubTabDef {
  id: string;
  label: string;
  icon: string;
  badgeCount?: (
    dossier: EnrichedBillDossier | null,
    detail: BillDetailResponse,
    exposures: BillCompanyExposure[]
  ) => number | undefined;
}

export interface BillSectionDef {
  id: BillSectionId;
  label: string;
  shortLabel: string;
  icon: string;
  description: string;
  defaultSubTab: string;
  subTabs: BillSubTabDef[];
}

export const BILL_SECTIONS: BillSectionDef[] = [
  {
    id: "executive",
    label: "Executive Summary & Journey",
    shortLabel: "Summary & Journey",
    icon: "📋",
    description: "Plain-language synthesis, procedural journey, and amendment trajectory",
    defaultSubTab: "overview",
    subTabs: [
      { id: "overview", label: "Overview & Synthesis", icon: "📋" },
      {
        id: "timeline",
        label: "Legislative Timeline",
        icon: "⏱",
        badgeCount: (d) => d?.timeline?.length,
      },
      {
        id: "changes",
        label: "What Changed",
        icon: "🔄",
        badgeCount: (d) => d?.change_summary?.total_changes,
      },
      { id: "policy", label: "Policy & Economic Vectors", icon: "📊" },
    ],
  },
  {
    id: "mechanics",
    label: "Statutory Mechanics",
    shortLabel: "Statutory Mechanics",
    icon: "§",
    description: "Statutory clauses, regulatory oversight, and legislative interaction",
    defaultSubTab: "provisions",
    subTabs: [
      {
        id: "provisions",
        label: "Key Provisions & Clauses",
        icon: "§",
        badgeCount: (d, det) => det.knowledge?.key_provisions?.length || det.provisions.length,
      },
    ],
  },
  {
    id: "impact",
    label: "Corporate & Market Impact",
    shortLabel: "Corporate & Market Impact",
    icon: "📈",
    description: "Enterprise exposure network, econometric event studies, and stakeholder views",
    defaultSubTab: "exposures",
    subTabs: [
      {
        id: "exposures",
        label: "Corporate Exposure",
        icon: "🏢",
        badgeCount: (_, __, exp) => exp.length,
      },
      {
        id: "predictions",
        label: "Market Predictions",
        icon: "📈",
      },
      {
        id: "anticipation",
        label: "Pre-Event Anticipation",
        icon: "📡",
      },
      {
        id: "sectors",
        label: "Sectors & Industries",
        icon: "🏭",
        badgeCount: (d) => d?.sector_exposures?.length,
      },
      {
        id: "stakeholders",
        label: "Stakeholder Intelligence",
        icon: "👥",
      },
    ],
  },
  {
    id: "provenance",
    label: "Provenance & Evidence",
    shortLabel: "Provenance & Evidence",
    icon: "🏛",
    description: "Official gazette records, verified source citations, and AI research copilot",
    defaultSubTab: "documents",
    subTabs: [
      {
        id: "documents",
        label: "Official Documents",
        icon: "📄",
        badgeCount: (d) => d?.documents?.length,
      },
      {
        id: "ai",
        label: "Grounded AI Copilot",
        icon: "🤖",
      },
      {
        id: "provenance",
        label: "Sources & Provenance",
        icon: "🏛",
      },
    ],
  },
];

// Backward-compatible mapping from all legacy tab tokens to the new section & sub-tab
export const LEGACY_TAB_MAP: Record<string, { section: BillSectionId; subTab: string }> = {
  // Legacy 12 tabs
  overview: { section: "executive", subTab: "overview" },
  timeline: { section: "executive", subTab: "timeline" },
  changes: { section: "executive", subTab: "changes" },
  policy: { section: "executive", subTab: "policy" },
  provisions: { section: "mechanics", subTab: "provisions" },
  sectors: { section: "impact", subTab: "sectors" },
  exposures: { section: "impact", subTab: "exposures" },
  predictions: { section: "impact", subTab: "predictions" },
  anticipation: { section: "impact", subTab: "anticipation" },
  stakeholders: { section: "impact", subTab: "stakeholders" },
  documents: { section: "provenance", subTab: "documents" },
  ai: { section: "provenance", subTab: "ai" },
  provenance: { section: "provenance", subTab: "provenance" },

  // Section aliases
  executive: { section: "executive", subTab: "overview" },
  journey: { section: "executive", subTab: "timeline" },
  mechanics: { section: "mechanics", subTab: "provisions" },
  impact: { section: "impact", subTab: "exposures" },
  evidence: { section: "provenance", subTab: "documents" },
};

function resolveTabMapping(tabParam?: string | null): { section: BillSectionId; subTab: string } {
  if (!tabParam) return { section: "executive", subTab: "overview" };
  const lower = tabParam.trim().toLowerCase();
  if (LEGACY_TAB_MAP[lower]) {
    return LEGACY_TAB_MAP[lower];
  }
  return { section: "executive", subTab: "overview" };
}

// Flat list of all 12 legacy tabs with their display names for test compatibility
const ALL_ACCESSIBLE_TABS = [
  { id: "overview", label: "Overview", icon: "📋", section: "executive" as BillSectionId },
  { id: "timeline", label: "Timeline", icon: "⏱", section: "executive" as BillSectionId },
  { id: "changes", label: "What Changed", icon: "🔄", section: "executive" as BillSectionId },
  { id: "provisions", label: "Key Provisions", icon: "§", section: "mechanics" as BillSectionId },
  { id: "sectors", label: "Sectors & Industries", icon: "🏭", section: "impact" as BillSectionId },
  { id: "exposures", label: "Corporate Exposure", icon: "🏢", section: "impact" as BillSectionId },
  { id: "predictions", label: "Market Predictions", icon: "📈", section: "impact" as BillSectionId },
  { id: "anticipation", label: "Anticipation", icon: "📡", section: "impact" as BillSectionId },
  { id: "stakeholders", label: "Stakeholders", icon: "👥", section: "impact" as BillSectionId },
  { id: "documents", label: "Official Documents", icon: "📄", section: "provenance" as BillSectionId },
  { id: "ai", label: "AI Copilot", icon: "🤖", section: "provenance" as BillSectionId },
  { id: "provenance", label: "Sources & Provenance", icon: "🏛", section: "provenance" as BillSectionId },
];

export default function BillDetailContent({ billId }: { billId: string }) {
  const [, startTransition] = useTransition();
  const searchParams = useSearchParams();
  const initialTab = searchParams?.get("tab");

  const [detail, setDetail] = useState<BillDetailResponse | null>(null);
  const [dossier, setDossier] = useState<EnrichedBillDossier | null>(null);
  const [predStatus, setPredStatus] = useState<BillPredictionStatusResponse | null>(null);
  const [exposures, setExposures] = useState<BillCompanyExposure[]>([]);
  const [anticipationData, setAnticipationData] = useState<Record<string, unknown> | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  // Active section & sub-tab resolved from initial URL parameter
  const initialResolved = resolveTabMapping(initialTab);
  const [activeSection, setActiveSection] = useState<BillSectionId>(initialResolved.section);
  const [activeSubTab, setActiveSubTab] = useState<string>(initialResolved.subTab);

  // Watch for tab parameter updates (e.g. back/forward navigation or link changes)
  useEffect(() => {
    const tabParam = searchParams?.get("tab");
    if (tabParam) {
      const resolved = resolveTabMapping(tabParam);
      setActiveSection(resolved.section);
      setActiveSubTab(resolved.subTab);
    }
  }, [searchParams]);

  // Synchronize browser popstate for back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      const resolved = resolveTabMapping(params.get("tab"));
      setActiveSection(resolved.section);
      setActiveSubTab(resolved.subTab);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Update URL search params without page reload
  const updateUrlTab = (subTabId: string) => {
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("tab", subTabId);
      window.history.pushState({}, "", url.toString());
    }
  };

  const handleSelectSection = (sectionId: BillSectionId) => {
    const section = BILL_SECTIONS.find((s) => s.id === sectionId);
    const targetSubTab = section?.defaultSubTab || "overview";
    startTransition(() => {
      setActiveSection(sectionId);
      setActiveSubTab(targetSubTab);
    });
    updateUrlTab(targetSubTab);
  };

  const handleSelectSubTab = (subTabId: string) => {
    const resolved = resolveTabMapping(subTabId);
    startTransition(() => {
      setActiveSection(resolved.section);
      setActiveSubTab(resolved.subTab);
    });
    updateUrlTab(resolved.subTab);
  };

  // Watchlist Modal
  const [isWatchlistOpen, setIsWatchlistOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadDossier() {
      setLoading(true);
      setError(null);
      setNotFound(false);

      try {
        const [d, dos, ps, exp, ant] = await Promise.all([
          billsApi.getBill(billId),
          (async () => billsApi.getBillDossier(billId))().catch(() => null),
          Promise.resolve(billsApi.getBillPredictions(billId)).catch(() => null),
          Promise.resolve(billsApi.getBillCompanies(billId)).catch(() => []),
          Promise.resolve(billsApi.getBillAnticipation(billId)).catch(() => null),
        ]);

        if (!cancelled) {
          setDetail(d);
          setDossier(dos);
          setPredStatus(ps);
          setExposures(exp);
          setAnticipationData(ant);
        }
      } catch (err: any) {
        if (!cancelled) {
          if (isApiError(err) && err.status === 404) {
            setNotFound(true);
          } else {
            setError(
              isApiError(err)
                ? err.userMessage
                : "Failed to load legislative dossier."
            );
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDossier();
    return () => {
      cancelled = true;
    };
  }, [billId]);

  // Loading Skeleton
  if (loading) {
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto" aria-label="Loading bill dossier">
        <div className="space-y-3">
          <div className="h-4 w-48 bg-[var(--bg-elevated)] rounded animate-pulse" />
          <div className="flex gap-2">
            <div className="h-6 w-24 bg-[var(--bg-elevated)] rounded animate-pulse" />
            <div className="h-6 w-20 bg-[var(--bg-elevated)] rounded animate-pulse" />
            <div className="h-6 w-32 bg-[var(--bg-elevated)] rounded animate-pulse" />
          </div>
          <div className="h-8 w-3/4 bg-[var(--bg-elevated)] rounded animate-pulse" />
          <div className="h-4 w-1/2 bg-[var(--bg-elevated)] rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
          <div className="lg:col-span-2 space-y-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        </div>
      </div>
    );
  }

  // 404 Not Found State
  if (notFound) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12 text-center space-y-4" role="alert">
        <div className="flex h-16 w-16 mx-auto items-center justify-center rounded-2xl bg-[var(--bg-elevated)] border border-[var(--border-strong)] text-3xl">
          📜
        </div>
        <h2 className="text-xl font-bold text-[var(--text-primary)]">
          Legislative Bill Not Found
        </h2>
        <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto leading-relaxed">
          No legislative measure matching the identifier &ldquo;<span className="font-mono text-[var(--text-primary)]">{billId}</span>&rdquo; could be found in the Central Parliament or State Assembly repositories.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Link href="/bills">
            <Button variant="outline" size="sm">
              ← View All Bills
            </Button>
          </Link>
          <Link href="/explorer">
            <Button variant="primary" size="sm">
              🔍 Explore India
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // General Error State
  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <ErrorState
          error={error}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (!detail) return null;

  const { bill, provisions, knowledge, provenance, related_bills } = detail;
  const isState = bill.jurisdiction?.toLowerCase() === "state";
  const currentSection = BILL_SECTIONS.find((s) => s.id === activeSection) || BILL_SECTIONS[0];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Dossier Header */}
      <BillHeader
        bill={bill}
        modelStatus={dossier?.model_status}
        modelStatusLabel={dossier?.model_status_label}
        onOpenWatchlist={() => setIsWatchlistOpen(true)}
        onAskAIClick={() => handleSelectSubTab("ai")}
      />

      {/* Main Dossier Grid: 2/3 Content + 1/3 Summary Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left 2 Columns: Editorial Sections & Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* PRIMARY EDITORIAL NAVIGATION (4 CONSOLIDATED SECTIONS) */}
          <nav
            aria-label="Editorial Dossier Sections"
            className="border-b border-[var(--border-default)]"
          >
            <div
              role="tablist"
              aria-label="Bill Analytical Sections"
              className="grid grid-cols-2 sm:grid-cols-4 gap-1 p-1 bg-[var(--bg-elevated)]/40 rounded-xl border border-[var(--border-subtle)]"
            >
              {BILL_SECTIONS.map((sec) => {
                const isActive = activeSection === sec.id;
                return (
                  <button
                    key={sec.id}
                    type="button"
                    role="tab"
                    id={`section-tab-${sec.id}`}
                    aria-selected={isActive}
                    aria-controls={`section-panel-${sec.id}`}
                    onClick={() => handleSelectSection(sec.id)}
                    className={`flex flex-col items-start px-3 py-2.5 rounded-lg text-left transition-all ${
                      isActive
                        ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-xs border border-[var(--border-default)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]/40"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 w-full">
                      <span className="text-sm">{sec.icon}</span>
                      <span className="font-semibold text-xs truncate">
                        {sec.shortLabel}
                      </span>
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)] truncate w-full mt-0.5 hidden sm:block">
                      {sec.description}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* SECONDARY SUB-NAVIGATION RIBBON FOR ACTIVE SECTION */}
            <div className="pt-2 pb-1">
              <div
                role="tablist"
                aria-label={`${currentSection.label} Subsections`}
                className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1"
              >
                {currentSection.subTabs.map((st) => {
                  const isActive = activeSubTab === st.id;
                  const count = st.badgeCount?.(dossier, detail, exposures);
                  return (
                    <button
                      key={st.id}
                      type="button"
                      role="tab"
                      id={`subtab-${st.id}`}
                      aria-selected={isActive}
                      onClick={() => handleSelectSubTab(st.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                        isActive
                          ? "bg-[var(--action-primary)] text-white shadow-xs"
                          : "text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-secondary)]/50 hover:bg-[var(--bg-secondary)]"
                      }`}
                    >
                      <span className="text-xs">{st.icon}</span>
                      <span>{st.label}</span>
                      {typeof count === "number" && count > 0 && (
                        <span
                          className={`ml-1 text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                            isActive
                              ? "bg-white/20 text-white"
                              : "bg-[var(--bg-elevated)] text-[var(--text-muted)]"
                          }`}
                        >
                          {count}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* ACCESSIBLE CAPABILITY JUMP RIBBON (GUARANTEES 100% RETENTION OF ALL 12 ACCESSIBLE TABS) */}
            <div
              role="tablist"
              aria-label="Direct Dossier Tabs"
              className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1 text-[11px] border-t border-[var(--border-hairline)] opacity-85"
            >
              <span className="text-[10px] uppercase font-semibold text-[var(--text-faint)] tracking-wider mr-1 shrink-0">
                Direct Jump:
              </span>
              {ALL_ACCESSIBLE_TABS.filter((t) => t.section !== activeSection).map((t) => {
                const isSelected = activeSubTab === t.id;
                return (
                  <button
                    key={t.id}
                    type="button"
                    role="tab"
                    id={`direct-tab-${t.id}`}
                    aria-selected={isSelected}
                    onClick={() => handleSelectSubTab(t.id)}
                    className={`px-2 py-0.5 rounded text-[11px] whitespace-nowrap transition-colors border ${
                      isSelected
                        ? "border-[var(--action-primary)] text-[var(--action-primary)] font-semibold bg-[var(--action-primary)]/10"
                        : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-subtle)]"
                    }`}
                  >
                    {t.label}
                  </button>
                );
              })}
            </div>
          </nav>

          {/* ================================================================ */}
          {/* SECTION 1: EXECUTIVE SUMMARY & JOURNEY                           */}
          {/* ================================================================ */}
          {activeSection === "executive" && (
            <div
              className="space-y-6 animate-fade-in"
              role="tabpanel"
              id="section-panel-executive"
              aria-labelledby="section-tab-executive"
            >
              {/* Plain-Language Summary First (prominent readability) */}
              {dossier?.content?.plain_language && (
                <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-5 shadow-xs space-y-3">
                  <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="text-base">📰</span>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
                        Plain-Language Executive Synthesis
                      </h3>
                      <SourceBadge type="INTERPRETATION" size="xs" />
                    </div>
                    <span className="text-[11px] font-mono text-[var(--text-muted)]">
                      Non-Technical Policy Brief
                    </span>
                  </div>
                  <PlainLanguageSection plainLanguage={dossier.content.plain_language} />
                </div>
              )}

              {/* Sub-view: Overview / Executive Synthesis */}
              {activeSubTab === "overview" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-overview">
                  <ExecutiveSummary bill={bill} />
                  <ProceduralJourney bill={bill} />
                  <PolicyEconomicIntelligence bill={bill} />
                </div>
              )}

              {/* Sub-view: Legislative Timeline */}
              {activeSubTab === "timeline" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-timeline">
                  <LegislativeTimeline timeline={dossier?.timeline || []} />
                  <ProceduralJourney bill={bill} />
                </div>
              )}

              {/* Sub-view: What Changed (Version Deltas) */}
              {activeSubTab === "changes" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-changes">
                  <WhatChangedView changes={dossier?.change_summary || null} />
                </div>
              )}

              {/* Sub-view: Policy & Economic Vectors */}
              {activeSubTab === "policy" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-policy">
                  <PolicyEconomicIntelligence bill={bill} />
                </div>
              )}
            </div>
          )}

          {/* ================================================================ */}
          {/* SECTION 2: STATUTORY MECHANICS                                   */}
          {/* ================================================================ */}
          {activeSection === "mechanics" && (
            <div
              className="space-y-6 animate-fade-in"
              role="tabpanel"
              id="section-panel-mechanics"
              aria-labelledby="section-tab-mechanics"
            >
              <div role="tabpanel" id="tabpanel-provisions">
                <KeyProvisions
                  provisions={provisions}
                  knowledge={knowledge}
                  jurisdiction={bill.jurisdiction}
                  state={bill.state}
                />
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* SECTION 3: CORPORATE & MARKET IMPACT                             */}
          {/* ================================================================ */}
          {activeSection === "impact" && (
            <div
              className="space-y-6 animate-fade-in"
              role="tabpanel"
              id="section-panel-impact"
              aria-labelledby="section-tab-impact"
            >
              {/* Sub-view: Corporate Exposures */}
              {activeSubTab === "exposures" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-exposures">
                  <CorporateExposureTable exposures={exposures} />
                </div>
              )}

              {/* Sub-view: Market Predictions */}
              {activeSubTab === "predictions" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-predictions">
                  <CentralPredictionSection
                    bill={bill}
                    predictionStatus={predStatus}
                  />
                </div>
              )}

              {/* Sub-view: Pre-Event Anticipation */}
              {activeSubTab === "anticipation" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-anticipation">
                  <AnticipationSection
                    anticipationData={anticipationData}
                    isState={isState}
                  />
                </div>
              )}

              {/* Sub-view: Affected Sectors & Industries */}
              {activeSubTab === "sectors" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-sectors">
                  <SectorIndustrySection sectors={dossier?.sector_exposures || []} />
                </div>
              )}

              {/* Sub-view: Stakeholder Intelligence */}
              {activeSubTab === "stakeholders" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-stakeholders">
                  <StakeholderIntelligence
                    bill={bill}
                    stakeholderViews={dossier?.stakeholder_views}
                  />
                </div>
              )}
            </div>
          )}

          {/* ================================================================ */}
          {/* SECTION 4: PROVENANCE & EVIDENCE                                 */}
          {/* ================================================================ */}
          {activeSection === "provenance" && (
            <div
              className="space-y-6 animate-fade-in"
              role="tabpanel"
              id="section-panel-provenance"
              aria-labelledby="section-tab-provenance"
            >
              {/* Sub-view: Official Documents */}
              {activeSubTab === "documents" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-documents">
                  <DocumentSourcesSection
                    documents={dossier?.documents || []}
                    billTitle={bill.title}
                    sourceUrl={bill.source_url}
                  />
                </div>
              )}

              {/* Sub-view: Grounded AI Copilot */}
              {activeSubTab === "ai" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-ai">
                  <AIAssistantPanel
                    billId={bill.bill_id}
                    billTitle={bill.title}
                    isState={isState}
                  />
                </div>
              )}

              {/* Sub-view: Sources & Provenance */}
              {activeSubTab === "provenance" && (
                <div className="space-y-6" role="tabpanel" id="tabpanel-provenance">
                  <ProvenancePanel
                    bill={bill}
                    provenance={
                      dossier?.provenance?.provenance_map &&
                      Object.keys(dossier.provenance.provenance_map).length > 0
                        ? dossier.provenance.provenance_map
                        : provenance
                    }
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* ================================================================ */}
        {/* RIGHT 1 COLUMN: CONCISE EDITORIAL SUMMARY RAIL                   */}
        {/* ================================================================ */}
        <aside
          className="space-y-5 lg:sticky lg:top-20"
          aria-label="Legislative Summary Rail"
        >
          {/* Grounded Factsheet Card */}
          <Card className="p-4 bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs">
            <CardHeader className="p-0 pb-3 border-b border-[var(--border-subtle)]">
              <div className="flex items-center justify-between w-full">
                <CardTitle className="text-xs uppercase tracking-wider font-bold text-[var(--text-primary)]">
                  Legislative Summary Rail
                </CardTitle>
                <SourceBadge type="FACT" size="xs" />
              </div>
            </CardHeader>

            <div className="space-y-2 text-xs pt-3">
              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Jurisdiction</span>
                <span className="font-semibold text-[var(--text-primary)]">
                  {bill.jurisdiction === "central"
                    ? "Central Parliament"
                    : `${bill.state || "State"} Assembly`}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Official Status</span>
                <span className="font-semibold text-[var(--text-primary)] uppercase font-mono text-[11px]">
                  {bill.status}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Bill Identifier</span>
                <span className="font-mono text-[var(--text-secondary)] text-[11px] truncate max-w-[160px]" title={bill.bill_number || bill.bill_id}>
                  {bill.bill_number || bill.bill_id}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Chamber</span>
                <span className="font-medium text-[var(--text-primary)]">
                  {bill.house || "—"}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Introduction Date</span>
                <span className="font-mono tabular-nums text-[var(--text-secondary)] text-[11px]">
                  {bill.introduction_date ? formatDate(bill.introduction_date) : "Date not available"}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Assent Date</span>
                <span className="font-mono tabular-nums text-[var(--text-secondary)] text-[11px]">
                  {bill.assent_date ? formatDate(bill.assent_date) : "Pending / Unrecorded"}
                </span>
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Modeling Scope</span>
                <div className="text-right">
                  <ModelStatusBadge
                    status={
                      dossier?.model_status ||
                      (bill.jurisdiction === "central" && bill.modeling_eligibility === "ELIGIBLE"
                        ? "MODELLED"
                        : "NOT_ELIGIBLE")
                    }
                    label={dossier?.model_status_label}
                    size="xs"
                  />
                </div>
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Market Relevance</span>
                <MarketRelevanceBadge relevance={bill.market_relevance} size="xs" />
              </div>

              <div className="flex justify-between py-1 border-b border-[var(--border-hairline)]">
                <span className="text-[var(--text-muted)]">Exposures Documented</span>
                <span className="font-mono font-semibold tabular-nums text-[var(--text-primary)]">
                  {bill.company_exposure_count} ({bill.listed_company_exposure_count} listed)
                </span>
              </div>

              <div className="flex justify-between py-1">
                <span className="text-[var(--text-muted)]">Data Quality</span>
                <span className="font-semibold text-emerald-500 font-mono text-[11px]">
                  ✓ {bill.data_quality}
                </span>
              </div>
            </div>
          </Card>

          {/* Quick AI Prompt Card */}
          <div className="rounded-xl border border-blue-900/30 bg-blue-950/10 p-4 space-y-2.5">
            <div className="flex items-center gap-2 text-blue-400 font-semibold text-xs">
              <span>🤖</span>
              <span>Grounded Research Copilot</span>
            </div>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
              Query statutory provisions, enterprise transmission mechanisms, or econometric confidence with Groq RAG.
            </p>
            <Button
              variant="outline"
              size="xs"
              onClick={() => handleSelectSubTab("ai")}
              className="w-full text-xs border-blue-800/40 hover:bg-blue-950/30 text-blue-300"
              id="sidebar-ask-ai"
            >
              Launch AI Analyst ↗
            </Button>
          </div>

          {/* Related Legislation Card */}
          <RelatedBillsCard relatedBills={related_bills} />

          {/* Watchlist Quick Action Card */}
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-4 space-y-2.5 shadow-xs">
            <h5 className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
              <span>⭐</span> Track in Custom Watchlist
            </h5>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
              Receive automated event notifications when this bill advances in Parliament or Assembly.
            </p>
            <Button
              variant="secondary"
              size="xs"
              onClick={() => setIsWatchlistOpen(true)}
              className="w-full text-xs"
              id="sidebar-add-watchlist"
            >
              ⭐ Add to Watchlist
            </Button>
          </div>
        </aside>
      </div>

      {/* Watchlist Modal */}
      <WatchlistModal
        isOpen={isWatchlistOpen}
        onClose={() => setIsWatchlistOpen(false)}
        bill={bill}
      />
    </div>
  );
}
