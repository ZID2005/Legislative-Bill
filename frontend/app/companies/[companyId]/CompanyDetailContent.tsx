/**
 * app/companies/[companyId]/CompanyDetailContent.tsx
 * ===================================================
 * Complete production-grade Corporate Intelligence Profile orchestrator.
 *
 * Distinct Universes:
 * MODE A: Quantitative / prediction-eligible listed companies (47 Central companies)
 * MODE B: Intelligence-only / qualitative companies and entities (20 intelligence + 3 reference entities)
 *
 * Features:
 * - Factual identity & business scope
 * - Documented legislative footprint & filterable exposure matrix
 * - Economic transmission mechanism architecture
 * - State geographic presence & operational footprint
 * - Central quantitative predictions & decision support (MODE A)
 * - Intelligence company firewall (MODE B)
 * - Pre-event information diffusion diagnostics (MODE A)
 * - Multi-persona stakeholder analysis
 * - Grounded Groq AI Analyst copilot
 * - Traceable source provenance & related peer entities
 * - Watchlist integration modal
 */

"use client";

import React, { useEffect, useState } from "react";
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

export default function CompanyDetailContent({ companyId }: { companyId: string }) {
  // Primary State
  const [detail, setDetail] = useState<CompanyDetailResponse | null>(null);
  const [predStatus, setPredStatus] = useState<CompanyPredictionStatusResponse | null>(null);
  const [anticipation, setAnticipation] = useState<CompanyAnticipationResponse | null>(null);
  const [exposures, setExposures] = useState<BillCompanyExposure[]>([]);
  const [peers, setPeers] = useState<CompanySummaryItem[]>([]);

  // Navigation & Modal State
  const [activeTab, setActiveTab] = useState<CompanyTabId>("overview");
  const [isWatchlistOpen, setIsWatchlistOpen] = useState(false);

  // Status State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadCompanyDossier() {
      setLoading(true);
      setError(null);
      try {
        // Parallel fetch for core intelligence
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

  // Loading State
  if (loading) {
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto" aria-label="Loading company profile">
        <div className="h-4 w-48 bg-slate-800 rounded animate-pulse" />
        <div className="h-32 w-full bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-20 bg-slate-800/60 rounded-lg animate-pulse" />
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

  const isQuant = detail.is_quant_eligible;

  // Tabs configuration
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
        onSelectTab={(tab) => setActiveTab(tab as CompanyTabId)}
      />

      {/* ------------------------------------------------------------------ */}
      {/* 2. Primary Tab Navigation Ribbon                                   */}
      {/* ------------------------------------------------------------------ */}
      <nav
        className="flex items-center gap-1 border-b border-slate-800 overflow-x-auto no-scrollbar pb-1 text-xs"
        aria-label="Corporate Intelligence Dossier Tabs"
      >
        {tabs.map((t) => {
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-1.5 px-3.5 py-2.5 rounded-t-lg font-semibold transition-all whitespace-nowrap border-b-2 ${
                isActive
                  ? "border-blue-500 text-blue-400 bg-slate-800/40"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20"
              }`}
              aria-selected={isActive}
              role="tab"
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
              {typeof t.count === "number" && t.count > 0 && (
                <span
                  className={`ml-1 text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? "bg-blue-900/60 text-blue-300"
                      : "bg-slate-800 text-slate-400"
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
      {/* 3. Tab Contents                                                    */}
      {/* ------------------------------------------------------------------ */}
      <main className="space-y-6">
        {/* Tab 1: Executive Profile & Summary */}
        {activeTab === "overview" && (
          <div className="space-y-6">
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
          <CompanyExposureMatrix exposures={exposures} />
        )}

        {/* Tab 3: Transmission Mechanism */}
        {activeTab === "transmission" && (
          <EconomicTransmissionSection company={detail} exposures={exposures} />
        )}

        {/* Tab 4: State & Regional Presence */}
        {activeTab === "geography" && (
          <StateGeographicSection company={detail} exposures={exposures} />
        )}

        {/* Tab 5: Market Predictions / Firewall */}
        {activeTab === "predictions" && (
          <CompanyPredictionsSection
            company={detail}
            predictionStatus={predStatus}
          />
        )}

        {/* Tab 6: Pre-Event Anticipation */}
        {activeTab === "anticipation" && (
          <CompanyAnticipationSection
            anticipation={anticipation}
            isQuant={isQuant}
          />
        )}

        {/* Tab 7: Stakeholder Perspectives */}
        {activeTab === "stakeholders" && (
          <CompanyStakeholderIntelligence company={detail} exposures={exposures} />
        )}

        {/* Tab 8: AI Copilot */}
        {activeTab === "ai" && (
          <CompanyAIPanel company={detail} />
        )}

        {/* Tab 9: Provenance & Audit */}
        {activeTab === "provenance" && (
          <div className="space-y-6">
            <CompanyProvenanceSection company={detail} exposures={exposures} />
            <RelatedCompaniesCard company={detail} peers={peers} />
          </div>
        )}
      </main>

      {/* ------------------------------------------------------------------ */}
      {/* 4. Watchlist Integration Modal                                     */}
      {/* ------------------------------------------------------------------ */}
      <CompanyWatchlistModal
        isOpen={isWatchlistOpen}
        onClose={() => setIsWatchlistOpen(false)}
        company={detail}
      />
    </div>
  );
}
