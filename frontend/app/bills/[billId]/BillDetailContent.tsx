/**
 * app/bills/[billId]/BillDetailContent.tsx
 * ==========================================
 * Production-Quality Bill Detail Dossier.
 *
 * Core intelligence hub unifying:
 * - Bill Identity & Procedural Journey
 * - Statutory Provisions & Regulatory Authority
 * - Policy & Economic Vectors
 * - Evidence-backed Corporate Exposures
 * - Central Market Predictions (with StatePredictionFirewall & Central Non-Modelled Handling)
 * - Pre-Event Legislative Anticipation & Diffusion Diagnostics
 * - Stakeholder Impact Intelligence (FACT | DERIVED | INTERPRETATION | PREDICTION)
 * - Grounded Groq AI Explanations Copilot
 * - Authoritative Provenance & Official Source Links
 * - Watchlist Integration
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { billsApi } from "@/lib/api/bills";
import { isApiError } from "@/lib/errors";
import type {
  BillDetailResponse,
  BillPredictionStatusResponse,
  BillCompanyExposure,
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

import { Tabs, type Tab } from "@/components/ui/Tabs";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ErrorState, SkeletonCard } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";

export default function BillDetailContent({ billId }: { billId: string }) {
  const [detail, setDetail] = useState<BillDetailResponse | null>(null);
  const [predStatus, setPredStatus] = useState<BillPredictionStatusResponse | null>(null);
  const [exposures, setExposures] = useState<BillCompanyExposure[]>([]);
  const [anticipationData, setAnticipationData] = useState<Record<string, unknown> | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  // Active section tab
  const [activeTab, setActiveTab] = useState("overview");

  // Watchlist Modal
  const [isWatchlistOpen, setIsWatchlistOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadDossier() {
      setLoading(true);
      setError(null);
      setNotFound(false);

      try {
        const [d, ps, exp, ant] = await Promise.all([
          billsApi.getBill(billId),
          Promise.resolve(billsApi.getBillPredictions(billId)).catch(() => null),
          Promise.resolve(billsApi.getBillCompanies(billId)).catch(() => []),
          Promise.resolve(billsApi.getBillAnticipation(billId)).catch(() => null),
        ]);

        if (!cancelled) {
          setDetail(d);
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
        {/* Header Skeleton */}
        <div className="space-y-3">
          <div className="h-4 w-48 bg-slate-800 rounded animate-pulse" />
          <div className="flex gap-2">
            <div className="h-6 w-24 bg-slate-800 rounded animate-pulse" />
            <div className="h-6 w-20 bg-slate-800 rounded animate-pulse" />
            <div className="h-6 w-32 bg-slate-800 rounded animate-pulse" />
          </div>
          <div className="h-8 w-3/4 bg-slate-800 rounded animate-pulse" />
          <div className="h-4 w-1/2 bg-slate-800 rounded animate-pulse" />
        </div>

        {/* Content Skeleton Grid */}
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
        <div className="flex h-16 w-16 mx-auto items-center justify-center rounded-2xl bg-slate-800 border border-slate-700 text-3xl">
          📜
        </div>
        <h2 className="text-xl font-bold text-slate-100">
          Legislative Bill Not Found
        </h2>
        <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
          No legislative measure matching the identifier &ldquo;<span className="font-mono text-slate-200">{billId}</span>&rdquo; could be found in the Central Parliament or State Assembly repositories.
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

  // Dossier Tabs Configuration
  const tabs: Tab[] = [
    { id: "overview", label: "Overview & Journey", icon: "📋" },
    { id: "provisions", label: "Key Provisions", count: (knowledge?.key_provisions?.length || provisions.length) || undefined, icon: "§" },
    { id: "exposures", label: "Corporate Exposure", count: exposures.length || undefined, icon: "🏢" },
    { id: "predictions", label: "Market Predictions", icon: isState ? "🛡" : "📈" },
    { id: "anticipation", label: "Anticipation", icon: "📡" },
    { id: "stakeholders", label: "Stakeholders", icon: "👥" },
    { id: "ai", label: "AI Copilot", icon: "🤖" },
    { id: "provenance", label: "Sources & Provenance", icon: "🏛" },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Dossier Header */}
      <BillHeader
        bill={bill}
        onOpenWatchlist={() => setIsWatchlistOpen(true)}
        onAskAIClick={() => setActiveTab("ai")}
      />

      {/* Main Dossier Grid: 2/3 Content + 1/3 Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left 2 Columns: Main Tabs & Tab Panels */}
        <div className="lg:col-span-2 space-y-6">
          {/* Dossier Navigation Tabs */}
          <div className="overflow-x-auto pb-1">
            <Tabs
              tabs={tabs}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              size="md"
            />
          </div>

          {/* TAB 1: OVERVIEW & PROCEDURAL JOURNEY */}
          {activeTab === "overview" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-overview">
              <ExecutiveSummary bill={bill} />
              <ProceduralJourney bill={bill} />
              <PolicyEconomicIntelligence bill={bill} />
            </div>
          )}

          {/* TAB 2: KEY PROVISIONS & STATUTORY TEXT */}
          {activeTab === "provisions" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-provisions">
              <KeyProvisions
                provisions={provisions}
                knowledge={knowledge}
                jurisdiction={bill.jurisdiction}
                state={bill.state}
              />
            </div>
          )}

          {/* TAB 3: CORPORATE EXPOSURES */}
          {activeTab === "exposures" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-exposures">
              <CorporateExposureTable exposures={exposures} />
            </div>
          )}

          {/* TAB 4: MARKET PREDICTIONS (FIREWALLED FOR STATE BILLS) */}
          {activeTab === "predictions" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-predictions">
              <CentralPredictionSection
                bill={bill}
                predictionStatus={predStatus}
              />
            </div>
          )}

          {/* TAB 5: PRE-EVENT ANTICIPATION */}
          {activeTab === "anticipation" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-anticipation">
              <AnticipationSection
                anticipationData={anticipationData}
                isState={isState}
              />
            </div>
          )}

          {/* TAB 6: STAKEHOLDER INTELLIGENCE */}
          {activeTab === "stakeholders" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-stakeholders">
              <StakeholderIntelligence bill={bill} />
            </div>
          )}

          {/* TAB 7: GROUNDED AI COPILOT */}
          {activeTab === "ai" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-ai">
              <AIAssistantPanel
                billId={bill.bill_id}
                billTitle={bill.title}
                isState={isState}
              />
            </div>
          )}

          {/* TAB 8: SOURCES & PROVENANCE */}
          {activeTab === "provenance" && (
            <div className="space-y-6 animate-fade-in" role="tabpanel" id="tabpanel-provenance">
              <ProvenancePanel
                bill={bill}
                provenance={provenance}
              />
            </div>
          )}
        </div>

        {/* Right 1 Column: Contextual Intelligence Sidebar */}
        <aside className="space-y-5 lg:sticky lg:top-6" aria-label="Contextual intelligence sidebar">
          {/* Executive Factsheet Card */}
          <Card>
            <CardHeader>
              <CardTitle>Legislative Factsheet</CardTitle>
            </CardHeader>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Jurisdiction</span>
                <span className="font-semibold text-slate-200">
                  {bill.jurisdiction === "central" ? "Central Parliament" : `${bill.state} Assembly`}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Chamber</span>
                <span className="font-semibold text-slate-200">{bill.house || "—"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Status</span>
                <span className="font-semibold text-slate-200">{bill.status}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Modeling Tier</span>
                <span className="font-semibold text-slate-200 font-mono">
                  {bill.modeling_eligibility}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Market Relevance</span>
                <span className="font-semibold text-slate-200">
                  {bill.market_relevance}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Exposures Documented</span>
                <span className="font-semibold text-slate-200 font-mono">
                  {bill.company_exposure_count} ({bill.listed_company_exposure_count} listed)
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Data Quality</span>
                <span className="font-semibold text-emerald-400">
                  ✓ {bill.data_quality}
                </span>
              </div>
            </div>
          </Card>

          {/* Quick AI Prompt Card */}
          <div className="rounded-xl border border-blue-900/40 bg-blue-950/20 p-4 space-y-2.5">
            <div className="flex items-center gap-2 text-blue-300 font-semibold text-xs">
              <span>🤖</span>
              <span>Grounded Copilot Available</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Have questions regarding statutory provisions, corporate exposure, or economic impact?
            </p>
            <Button
              variant="outline"
              size="xs"
              onClick={() => setActiveTab("ai")}
              className="w-full text-xs"
              id="sidebar-ask-ai"
            >
              Launch AI Analyst ↗
            </Button>
          </div>

          {/* Related Legislation Card */}
          <RelatedBillsCard relatedBills={related_bills} />

          {/* Watchlist Quick Action Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-2.5">
            <h5 className="text-xs font-semibold text-slate-200">
              Track in Custom Watchlist
            </h5>
            <p className="text-[11px] text-slate-500 leading-relaxed">
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
