/**
 * app/portfolio/page.tsx
 * =======================
 * TASK 1.8A — SEANCE PORTFOLIO WORKSPACE REDESIGN
 *
 * Implements the approved Premium Editorial-Finance Two-Column Decision Center:
 * - Left Column (~40%): Searchable Holdings & Company Roster with inline exposure indicators
 * - Right Column (~60%): Contextual Legislative-Impact Inspector grouped by supported relevance tiers
 * - Executive Header: High-density tabular exposure ticker, multi-tenant portfolio switcher, action toolbar
 * - Progressive Disclosure: Expandable evidence details, Central quantitative model forecasts, State firewalls
 * - Modal flows: Add Holding, Import CSV/JSON, Grounded AI Relevance Explanation, Printable Impact Report
 * - Full Light/Dark/System theme calibration and WCAG 2.2 AAA accessibility
 */

"use client";

import React, { useState, useEffect, useCallback, useTransition } from "react";
import { portfolioApi } from "@/lib/api/portfolio";
import type {
  ExplainRelevanceResponse,
  PersonalizedImpactReportResponse,
  PortfolioHoldingItem,
  PortfolioLegislativeExposureResponse,
  UserPortfolioItem,
} from "@/types/api";

import { PortfolioHeader } from "@/components/portfolio/PortfolioHeader";
import { HoldingsRoster } from "@/components/portfolio/HoldingsRoster";
import { LegislativeImpactInspector } from "@/components/portfolio/LegislativeImpactInspector";
import { ExplainRelevanceModal } from "@/components/portfolio/ExplainRelevanceModal";
import { AddHoldingModal } from "@/components/portfolio/AddHoldingModal";
import { ImportHoldingsModal } from "@/components/portfolio/ImportHoldingsModal";
import { PortfolioImpactReport } from "@/components/portfolio/PortfolioImpactReport";

export default function PortfolioPage() {
  const [, startTransition] = useTransition();

  // Primary Data State
  const [portfolios, setPortfolios] = useState<UserPortfolioItem[]>([]);
  const [activePortfolio, setActivePortfolio] = useState<UserPortfolioItem | null>(null);
  const [exposure, setExposure] = useState<PortfolioLegislativeExposureResponse | null>(null);
  const [selectedHolding, setSelectedHolding] = useState<PortfolioHoldingItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // View state: workspace vs report
  const [activeView, setActiveView] = useState<"workspace" | "report">("workspace");

  // Report state
  const [reportData, setReportData] = useState<PersonalizedImpactReportResponse | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  // Modal dialog states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [explainBillId, setExplainBillId] = useState<string | null>(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainResult, setExplainResult] = useState<ExplainRelevanceResponse | null>(null);

  // Load portfolios and initial exposure
  const loadPortfolioData = useCallback(async (targetPortfolioId?: string) => {
    setLoading(true);
    setError(null);
    try {
      const pfs = await portfolioApi.listPortfolios();
      setPortfolios(pfs);

      const target =
        (targetPortfolioId ? pfs.find((p) => p.portfolio_id === targetPortfolioId) : null) ||
        pfs[0] ||
        null;
      setActivePortfolio(target);

      const exp = target
        ? await portfolioApi.getExposure(target.portfolio_id)
        : await portfolioApi.getExposure();
      setExposure(exp);
    } catch (err: any) {
      console.error("Error loading portfolio data:", err);
      setError("Unable to connect to backend portfolio service. Displaying offline baseline view.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPortfolioData();
  }, [loadPortfolioData]);

  // Handle portfolio switch
  const handleSelectPortfolio = async (portfolio: UserPortfolioItem) => {
    setActivePortfolio(portfolio);
    setSelectedHolding(null);
    setLoading(true);
    try {
      const exp = await portfolioApi.getExposure(portfolio.portfolio_id);
      setExposure(exp);
    } catch (err: any) {
      console.error("Error switching portfolio:", err);
    } finally {
      setLoading(false);
    }
  };

  // Add Holding
  const handleSaveHolding = async (holdingData: Partial<PortfolioHoldingItem>) => {
    if (!activePortfolio) return;
    await portfolioApi.addHolding(activePortfolio.portfolio_id, holdingData);
    await loadPortfolioData(activePortfolio.portfolio_id);
  };

  // Remove Holding
  const handleRemoveHolding = async (holding: PortfolioHoldingItem) => {
    if (!activePortfolio) return;
    if (confirm(`Remove ${holding.company_name} from ${activePortfolio.name}?`)) {
      try {
        await portfolioApi.removeHolding(activePortfolio.portfolio_id, holding.holding_id);
        if (selectedHolding?.holding_id === holding.holding_id) {
          setSelectedHolding(null);
        }
        await loadPortfolioData(activePortfolio.portfolio_id);
      } catch (err: any) {
        alert(`Failed to remove holding: ${err.message}`);
      }
    }
  };

  // Import Holdings
  const handleImportHoldings = async (holdingsToImport: any[]) => {
    if (!activePortfolio) return;
    await portfolioApi.importHoldings(activePortfolio.portfolio_id, holdingsToImport);
    await loadPortfolioData(activePortfolio.portfolio_id);
  };

  // Explain Relevance
  const handleExplainRelevance = async (billId: string) => {
    setExplainBillId(billId);
    setExplainLoading(true);
    setExplainResult(null);
    try {
      const res = await portfolioApi.explainRelevance(billId);
      setExplainResult(res);
    } catch (err) {
      setExplainResult({
        bill_id: billId,
        relevance_tier: "INFORMATIONAL",
        explanation: "INSUFFICIENT VERIFIED INFORMATION: Could not contact decision intelligence engine.",
        affected_holdings: [],
        model_status: "KNOWLEDGE ONLY",
        grounded: false,
        disclaimer: "Non-financial decision support only.",
      });
    } finally {
      setExplainLoading(false);
    }
  };

  // Generate Report
  const handleGenerateReport = async () => {
    setReportLoading(true);
    try {
      const rep = await portfolioApi.generateReport(activePortfolio?.portfolio_id);
      setReportData(rep);
      setActiveView("report");
    } catch (err: any) {
      alert(`Report generation failed: ${err.message}`);
    } finally {
      setReportLoading(false);
    }
  };

  // Selected bill details for explain modal title
  const explainBill = exposure?.relevant_bills.find((b) => b.bill_id === explainBillId);

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-[1440px] mx-auto">
      {/* Executive Portfolio Header */}
      <PortfolioHeader
        portfolios={portfolios}
        activePortfolio={activePortfolio}
        onSelectPortfolio={handleSelectPortfolio}
        exposure={exposure}
        onAddHolding={() => setShowAddModal(true)}
        onImportHoldings={() => setShowImportModal(true)}
        onGenerateReport={handleGenerateReport}
        reportLoading={reportLoading}
        activeView={activeView}
        onToggleView={setActiveView}
        hasReportData={reportData !== null}
      />

      {error && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/25 text-xs text-amber-600 dark:text-amber-400">
          {error}
        </div>
      )}

      {/* Primary Content Switcher */}
      {activeView === "report" && reportData ? (
        <PortfolioImpactReport
          reportData={reportData}
          onBackToWorkspace={() => setActiveView("workspace")}
        />
      ) : (
        /* Two-Column Decision Center Workspace */
        <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column (40% / 5 Cols): Holdings Roster */}
          <aside className="lg:col-span-5 w-full">
            <HoldingsRoster
              holdings={activePortfolio?.holdings || []}
              selectedHolding={selectedHolding}
              onSelectHolding={(h) => {
                startTransition(() => {
                  setSelectedHolding(h);
                });
              }}
              onRemoveHolding={handleRemoveHolding}
              onAddHolding={() => setShowAddModal(true)}
              holdingsExposureMap={exposure?.holdings_exposure_map || {}}
            />
          </aside>

          {/* Right Column (60% / 7 Cols): Legislative Impact Inspector */}
          <section className="lg:col-span-7 w-full">
            <LegislativeImpactInspector
              bills={exposure?.relevant_bills || []}
              selectedHolding={selectedHolding}
              onClearSelectedHolding={() => setSelectedHolding(null)}
              onExplainRelevance={handleExplainRelevance}
              loading={loading}
            />
          </section>
        </main>
      )}

      {/* Modal Dialogs */}
      <ExplainRelevanceModal
        isOpen={explainBillId !== null}
        onClose={() => setExplainBillId(null)}
        loading={explainLoading}
        result={explainResult}
        billTitle={explainBill?.bill_title}
      />

      <AddHoldingModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSave={handleSaveHolding}
      />

      <ImportHoldingsModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImport={handleImportHoldings}
      />
    </div>
  );
}
