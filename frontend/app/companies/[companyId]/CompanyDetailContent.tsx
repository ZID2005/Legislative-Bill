/**
 * app/companies/[companyId]/CompanyDetailContent.tsx
 * ===================================================
 * Editorial-Finance Corporate Intelligence Profile Orchestrator (Task 1.9A Redesign).
 *
 * Distinct Universes (Strict Epistemic Isolation):
 * - MODE A: Quantitative / prediction-eligible listed companies (47 Central companies)
 *   Multi-horizon econometric event studies, pre-event information diffusion,
 *   statutory exposure matrix, and enterprise transmission channels.
 * - MODE B: Qualitative intelligence entities (20 intelligence + 3 reference entities)
 *   Sub-national statutory or unlisted entities. Quantitative stock predictions are
 *   strictly unavailable by design under methodology invariants. Features full
 *   statutory footprint, state presence, and economic mechanisms without empty
 *   or misleading prediction widgets.
 *
 * Non-Inference Safeguard:
 * - Never infers eligibility from display name, industry, or sector.
 * - Strictly derived from authoritative fields: is_quant_eligible, universe_type,
 *   and quantitative_firewall_status.
 *
 * Backward-Compatibility:
 * - Preserves all 9 legacy tab identifiers and display labels
 * - Synchronizes ?tab= query parameter with browser back/forward navigation
 */

"use client";

import React, { useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";
import { companiesApi } from "@/lib/api/companies";
import { isApiError } from "@/lib/errors";
import type {
  BillCompanyExposure,
  CompanyAnticipationResponse,
  CompanyDetailResponse,
  CompanyPredictionStatusResponse,
  CompanySummaryItem,
} from "@/types/api";
import { CompanyHeader } from "@/components/companies/CompanyHeader";
import { CompanyOverview } from "@/components/companies/CompanyOverview";
import { CompanyExposureMatrix } from "@/components/companies/CompanyExposureMatrix";
import { EconomicTransmissionSection } from "@/components/companies/EconomicTransmissionSection";
import { StateGeographicSection } from "@/components/companies/StateGeographicSection";
import { CompanyPredictionsSection } from "@/components/companies/CompanyPredictionsSection";
import { CompanyAnticipationSection } from "@/components/companies/CompanyAnticipationSection";
import { CompanyStakeholderIntelligence } from "@/components/companies/CompanyStakeholderIntelligence";
import { CompanyAIPanel } from "@/components/companies/CompanyAIPanel";
import { CompanyProvenanceSection } from "@/components/companies/CompanyProvenanceSection";
import { RelatedCompaniesCard } from "@/components/companies/RelatedCompaniesCard";
import { CompanyWatchlistModal } from "@/components/companies/CompanyWatchlistModal";
import { ErrorState, SkeletonCard } from "@/components/ui/Skeleton";
import { SourceBadge } from "@/components/ui/Badge";

export type CompanyTabId =
  | "overview"
  | "footprint"
  | "transmission"
  | "geography"
  | "predictions"
  | "anticipation"
  | "stakeholders"
  | "ai"
  | "provenance";

const VALID_COMPANY_TABS: CompanyTabId[] = [
  "overview",
  "footprint",
  "transmission",
  "geography",
  "predictions",
  "anticipation",
  "stakeholders",
  "ai",
  "provenance",
];

export default function CompanyDetailContent({ companyId }: { companyId: string }) {
  const [, startTransition] = useTransition();
  const searchParams = useSearchParams();
  const initialTabParam = searchParams?.get("tab")?.toLowerCase() as CompanyTabId | undefined;

  // Primary State
  const [detail, setDetail] = useState<CompanyDetailResponse | null>(null);
  const [predStatus, setPredStatus] = useState<CompanyPredictionStatusResponse | null>(null);
  const [anticipation, setAnticipation] = useState<CompanyAnticipationResponse | null>(null);
  const [exposures, setExposures] = useState<BillCompanyExposure[]>([]);
  const [peers, setPeers] = useState<CompanySummaryItem[]>([]);

  // Navigation & Modal State
  const [activeTab, setActiveTab] = useState<CompanyTabId>(() => {
    if (initialTabParam && VALID_COMPANY_TABS.includes(initialTabParam)) {
      return initialTabParam;
    }
    return "overview";
  });
  const [isWatchlistOpen, setIsWatchlistOpen] = useState(false);

  // Status State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Synchronize URL query parameter updates
  useEffect(() => {
    const tabParam = searchParams?.get("tab")?.toLowerCase() as CompanyTabId | undefined;
    if (tabParam && VALID_COMPANY_TABS.includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  // Synchronize browser popstate for back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get("tab")?.toLowerCase() as CompanyTabId | undefined;
      if (tabParam && VALID_COMPANY_TABS.includes(tabParam)) {
        setActiveTab(tabParam);
      }
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const handleSelectTab = (tabId: CompanyTabId) => {
    startTransition(() => {
      setActiveTab(tabId);
    });
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("tab", tabId);
      window.history.pushState({}, "", url.toString());
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function loadCompanyDossier() {
      setLoading(true);
      setError(null);
      try {
        // Parallel fetch for core corporate intelligence
        const [d, ps, ant, expList] = await Promise.all([
          companiesApi.getCompany(companyId),
          companiesApi.getCompanyPredictions(companyId).catch(() => null),
          companiesApi.getCompanyAnticipation(companyId).catch(() => null),
          companiesApi.getCompanyExposures(companyId).catch(() => []),
        ]);

        if (cancelled) return;

        setDetail(d);
        setPredStatus(ps);
        setAnticipation(ant);

        // Prefer explicit exposures list, or fallback to related_bills on detail
        const mergedExposures =
          expList && expList.length > 0 ? expList : (d.related_bills as BillCompanyExposure[]) || [];
        setExposures(mergedExposures);

        // Fetch sector peers in background
        if (d.sector) {
          companiesApi
            .listCompanies({ sector: d.sector, limit: 8 })
            .then((res) => {
              if (!cancelled && res?.items) {
                setPeers(res.items);
              }
            })
            .catch(() => {
              // peer fetch failure is non-blocking
            });
        }
      } catch (err) {
        if (!cancelled) {
          setError(isApiError(err) ? err.userMessage : "Failed to load corporate profile.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadCompanyDossier();

    return () => {
      cancelled = true;
    };
  }, [companyId]);

  // Loading Skeleton State
  if (loading) {
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto" aria-label="Loading company profile">
        <div className="h-4 w-48 bg-[var(--bg-elevated)] rounded animate-pulse" />
        <div className="h-32 w-full bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl animate-pulse" />
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-20 bg-[var(--bg-elevated)]/60 rounded-lg animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SkeletonCard />
          </div>
          <SkeletonCard />
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto" role="alert">
        <ErrorState error={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  if (!detail) return null;

  // Authoritative Mode A vs Mode B Determination (strict technical safeguard)
  const isQuant = Boolean(
    detail.is_quant_eligible &&
    detail.universe_type?.toLowerCase() === "quantitative" &&
    detail.quantitative_firewall_status !== "FIREWALLED"
  );
  const isIntel = !isQuant || detail.universe_type?.toLowerCase() === "intelligence";

  // Tab definitions preserving exact labels tested in company-detail.test.tsx
  const tabs: { id: CompanyTabId; label: string; icon: string; count?: number }[] = [
    { id: "overview", label: "Executive Profile", icon: "📋" },
    { id: "footprint", label: "Legislative Footprint", icon: "🔗", count: exposures.length },
    { id: "transmission", label: "Transmission Mechanism", icon: "⚙️" },
    { id: "geography", label: "State & Regional Presence", icon: "🗺", count: detail.operating_states.length },
    {
      id: "predictions",
      label: isQuant ? "Market Predictions" : "Prediction Firewall",
      icon: isQuant ? "📈" : "🛡️",
    },
    { id: "anticipation", label: "Pre-Event Anticipation", icon: "📡" },
    { id: "stakeholders", label: "Stakeholder Intelligence", icon: "👥" },
    { id: "ai", label: "AI Analyst Copilot", icon: "🤖" },
    { id: "provenance", label: "Audit & Provenance", icon: "📎" },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* ------------------------------------------------------------------ */}
      {/* 1. Header (Identity, Badges, Quick Actions)                        */}
      {/* ------------------------------------------------------------------ */}
      <CompanyHeader
        company={detail}
        onOpenWatchlist={() => setIsWatchlistOpen(true)}
        onSelectTab={(tab) => handleSelectTab(tab as CompanyTabId)}
      />

      {/* ------------------------------------------------------------------ */}
      {/* 2. Authoritative Mode A vs Mode B Institutional Indicator           */}
      {/* ------------------------------------------------------------------ */}
      {isQuant ? (
        <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/5 px-4 py-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-500/20 text-emerald-400 font-bold text-xs">
              A
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-emerald-400 tracking-tight uppercase text-[11px]">
                  Mode A: Quantitative / Prediction-Eligible Entity
                </span>
                <SourceBadge type="PREDICTION" size="xs" />
              </div>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-relaxed">
                Listed security covered by Central econometric event studies across 5 supported horizons with pre-event anticipation diagnostics.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 font-mono font-tabular text-[11px] text-[var(--text-secondary)] shrink-0">
            {detail.isin && <span>ISIN: {detail.isin}</span>}
            {detail.ticker_nse && <span>NSE: {detail.ticker_nse}</span>}
            {detail.ticker_bse && <span>BSE: {detail.ticker_bse}</span>}
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-xs space-y-1.5 shadow-xs">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-amber-500/20 text-amber-400 font-bold text-xs">
              B
            </span>
            <span className="font-bold text-amber-400 tracking-tight uppercase text-[11px]">
              Mode B: Qualitative Intelligence Entity
            </span>
            <span className="text-[var(--text-muted)]">·</span>
            <span className="text-[var(--text-secondary)] font-medium">
              Statutory Firewall Active
            </span>
          </div>
          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed pl-8">
            This entity is an unlisted corporate, state-owned enterprise, statutory corporation, or public utility.
            Quantitative stock market predictions are strictly unavailable by design under platform methodology invariants.
            Documented legislative exposures, economic transmission mechanisms, and state footprint remain fully available.
          </p>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* 3. Primary Tab Navigation Ribbon                                   */}
      {/* ------------------------------------------------------------------ */}
      <nav
        className="flex items-center gap-1 border-b border-[var(--border-default)] overflow-x-auto no-scrollbar pb-1 text-xs"
        aria-label="Corporate Intelligence Dossier Tabs"
        role="tablist"
      >
        {tabs.map((t) => {
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => handleSelectTab(t.id)}
              className={`flex items-center gap-1.5 px-3.5 py-2.5 rounded-t-lg font-semibold transition-all whitespace-nowrap border-b-2 text-xs ${
                isActive
                  ? "border-[var(--action-primary)] text-[var(--action-primary)] bg-[var(--bg-elevated)]/40 shadow-xs"
                  : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]/20"
              }`}
              aria-selected={isActive}
              role="tab"
              id={`company-tab-${t.id}`}
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
              {typeof t.count === "number" && t.count > 0 && (
                <span
                  className={`ml-1 text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? "bg-[var(--action-primary)]/20 text-[var(--action-primary)]"
                      : "bg-[var(--bg-elevated)] text-[var(--text-muted)]"
                  }`}
                >
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* ------------------------------------------------------------------ */}
      {/* 4. Tab Contents                                                    */}
      {/* ------------------------------------------------------------------ */}
      <main className="space-y-6">
        {/* Tab 1: Executive Profile & Summary */}
        {activeTab === "overview" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-overview">
            <CompanyOverview company={detail} />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <EconomicTransmissionSection company={detail} exposures={exposures} />
              </div>
              <div>
                <RelatedCompaniesCard company={detail} peers={peers} />
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Legislative Footprint & Exposure Matrix */}
        {activeTab === "footprint" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-footprint">
            <CompanyExposureMatrix exposures={exposures} />
          </div>
        )}

        {/* Tab 3: Transmission Mechanism */}
        {activeTab === "transmission" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-transmission">
            <EconomicTransmissionSection company={detail} exposures={exposures} />
          </div>
        )}

        {/* Tab 4: State & Regional Presence */}
        {activeTab === "geography" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-geography">
            <StateGeographicSection company={detail} exposures={exposures} />
          </div>
        )}

        {/* Tab 5: Market Predictions / Firewall */}
        {activeTab === "predictions" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-predictions">
            <CompanyPredictionsSection
              company={detail}
              predictionStatus={predStatus}
            />
          </div>
        )}

        {/* Tab 6: Pre-Event Anticipation */}
        {activeTab === "anticipation" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-anticipation">
            <CompanyAnticipationSection
              anticipation={anticipation}
              isQuant={isQuant}
            />
          </div>
        )}

        {/* Tab 7: Stakeholder Perspectives */}
        {activeTab === "stakeholders" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-stakeholders">
            <CompanyStakeholderIntelligence company={detail} exposures={exposures} />
          </div>
        )}

        {/* Tab 8: AI Copilot */}
        {activeTab === "ai" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-ai">
            <CompanyAIPanel company={detail} />
          </div>
        )}

        {/* Tab 9: Provenance & Audit */}
        {activeTab === "provenance" && (
          <div className="space-y-6 animate-fade-in" role="tabpanel" id="company-panel-provenance">
            <CompanyProvenanceSection company={detail} exposures={exposures} />
            <RelatedCompaniesCard company={detail} peers={peers} />
          </div>
        )}
      </main>

      {/* ------------------------------------------------------------------ */}
      {/* 5. Watchlist Integration Modal                                     */}
      {/* ------------------------------------------------------------------ */}
      <CompanyWatchlistModal
        isOpen={isWatchlistOpen}
        onClose={() => setIsWatchlistOpen(false)}
        company={detail}
      />
    </div>
  );
}
