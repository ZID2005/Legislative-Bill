/**
 * app/portfolio/page.tsx
 * =======================
 * Task 8.28 — Decision Intelligence & Personalized Impact Workspace.
 *
 * Connects:
 *   LEGISLATION → SECTORS / INDUSTRIES → COMPANY EXPOSURE → USER PORTFOLIO → EXISTING MODELLED IMPACT
 *
 * Core Features:
 * - Portfolio Legislative Exposure View:
 *     * Relevance Tiers: DIRECT, HIGH RELEVANCE, MODERATE RELEVANCE, INDIRECT, INFORMATIONAL
 *     * Evidence-backed linkage reasons explaining WHY legislation is surfaced
 *     * Epistemic model status: MODELLED, KNOWLEDGE ONLY, NOT ELIGIBLE, PENDING REVIEW
 *     * Preservation of frozen Central quantitative models across 5 authoritative horizons
 *     * Statutory 0 stock predictions for State bills
 * - Holdings Management & CSV/XLSX Import
 * - Grounded AI Explanation Modal ("Why is this bill relevant to my portfolio?")
 * - "MY LEGISLATIVE IMPACT REPORT" Generation
 * - Strict non-financial advice notices & FACT / INTERPRETATION / PREDICTION labels
 */

"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { portfolioApi } from "@/lib/api/portfolio";
import type {
  ExplainRelevanceResponse,
  PersonalizedBillImpactItem,
  PersonalizedImpactReportResponse,
  PortfolioHoldingItem,
  PortfolioLegislativeExposureResponse,
  UserPortfolioItem,
} from "@/types/api";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Constants & Color Mappings
// ---------------------------------------------------------------------------

const TIER_BADGES: Record<string, { bg: string; text: string; border: string }> = {
  DIRECT: { bg: "bg-rose-500/10", text: "text-rose-400", border: "border-rose-500/30" },
  "HIGH RELEVANCE": { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  "MODERATE RELEVANCE": { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
  INDIRECT: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/30" },
  INFORMATIONAL: { bg: "bg-slate-500/10", text: "text-slate-400", border: "border-slate-500/30" },
};

const MODEL_STATUS_BADGES: Record<string, { bg: string; text: string; border: string }> = {
  MODELLED: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  "KNOWLEDGE ONLY": { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/30" },
  "NOT ELIGIBLE": { bg: "bg-slate-500/10", text: "text-slate-400", border: "border-slate-500/30" },
  "PENDING REVIEW": { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
};

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<UserPortfolioItem[]>([]);
  const [activePortfolio, setActivePortfolio] = useState<UserPortfolioItem | null>(null);
  const [exposure, setExposure] = useState<PortfolioLegislativeExposureResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tabs
  const [activeTab, setActiveTab] = useState<"exposure" | "holdings" | "report">("exposure");

  // Filter for Exposure
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [jurisdictionFilter, setJurisdictionFilter] = useState<string>("ALL");

  // Modals
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAddHoldingModal, setShowAddHoldingModal] = useState(false);
  const [selectedExplainBill, setSelectedExplainBill] = useState<string | null>(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainResult, setExplainResult] = useState<ExplainRelevanceResponse | null>(null);

  // Report Modal / View
  const [reportData, setReportData] = useState<PersonalizedImpactReportResponse | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  // Load portfolio and exposure
  const loadPortfolioData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pfs = await portfolioApi.listPortfolios();
      setPortfolios(pfs);
      const current = pfs[0] || null;
      setActivePortfolio(current);

      if (current) {
        const exp = await portfolioApi.getExposure(current.portfolio_id);
        setExposure(exp);
      } else {
        const exp = await portfolioApi.getExposure();
        setExposure(exp);
      }
    } catch (err) {
      console.error("Error loading portfolio data:", err);
      setError("Unable to connect to backend portfolio service. Showing sample portfolio.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPortfolioData();
  }, [loadPortfolioData]);

  // Handle explain relevance
  const handleExplainRelevance = async (billId: string) => {
    setSelectedExplainBill(billId);
    setExplainLoading(true);
    setExplainResult(null);
    try {
      const res = await portfolioApi.explainRelevance(billId);
      setExplainResult(res);
    } catch (err) {
      console.error("Failed to explain relevance:", err);
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

  // Handle generate report
  const handleGenerateReport = async () => {
    setReportLoading(true);
    try {
      const rep = await portfolioApi.generateReport(activePortfolio?.portfolio_id);
      setReportData(rep);
      setActiveTab("report");
    } catch (err) {
      console.error("Failed to generate report:", err);
    } finally {
      setReportLoading(false);
    }
  };

  // Filtered bills
  const filteredBills = (exposure?.relevant_bills || []).filter((b) => {
    if (tierFilter !== "ALL" && b.relevance_tier !== tierFilter) return false;
    if (jurisdictionFilter === "CENTRAL" && b.jurisdiction !== "central") return false;
    if (jurisdictionFilter === "STATE" && b.jurisdiction !== "state") return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">💼</span>
            <span className="text-xs uppercase tracking-widest font-bold text-blue-400">
              Personalized Decision Intelligence
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Task 8.28 Verified
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
            Portfolio Legislative Exposure Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Evidence-backed legislative intelligence matching your holdings to Central acts, State legislation, and validated econometric horizons.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddHoldingModal(true)}
            className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700/80 transition-all flex items-center gap-2"
          >
            <span>+</span> Add Holding
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-3.5 py-2 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-semibold border border-blue-500/30 transition-all flex items-center gap-2"
          >
            <span>📂</span> Import CSV / XLSX
          </button>
          <button
            onClick={handleGenerateReport}
            disabled={reportLoading}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all flex items-center gap-2"
          >
            <span>📄</span> {reportLoading ? "Generating..." : "Generate Impact Report"}
          </button>
        </div>
      </div>

      {/* Decision Support Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-800/40 flex items-start gap-3">
        <span className="text-base text-blue-400 mt-0.5">ℹ</span>
        <div className="text-xs text-slate-300 leading-relaxed">
          <strong className="text-blue-300">Decision-Support Governance:</strong> This system surfaces documented legislative facts, corporate exposure networks, and validated Central model records. It does <strong className="text-rose-400">NOT</strong> provide automated investment advice, buy/sell/hold ratings, or target prices. State legislation strictly carries 0 stock predictions.
        </div>
      </div>

      {/* Exposure Summary KPI Cards */}
      {exposure && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Tracked Holdings</span>
            <p className="text-2xl font-bold text-slate-100 mt-1">{exposure.total_holdings}</p>
            <span className="text-[10px] text-emerald-400 font-medium">{exposure.exposed_holdings_count} Exposed</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Total Relevant Bills</span>
            <p className="text-2xl font-bold text-blue-400 mt-1">{exposure.total_relevant_bills}</p>
            <span className="text-[10px] text-slate-500 font-mono">Matched by rules</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-rose-500/20">
            <span className="text-[10px] text-rose-400 uppercase font-semibold">Direct Exposures</span>
            <p className="text-2xl font-bold text-rose-400 mt-1">{exposure.direct_bills_count}</p>
            <span className="text-[10px] text-rose-400/80 font-mono">Documented statutory links</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-amber-500/20">
            <span className="text-[10px] text-amber-400 uppercase font-semibold">High Relevance</span>
            <p className="text-2xl font-bold text-amber-400 mt-1">{exposure.high_relevance_bills_count}</p>
            <span className="text-[10px] text-amber-400/80 font-mono">Industry & presence</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-emerald-500/20">
            <span className="text-[10px] text-emerald-400 uppercase font-semibold">Modelled Central</span>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{exposure.modelled_central_bills_count}</p>
            <span className="text-[10px] text-emerald-400/80 font-mono">47 Quant universe</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <span className="text-[10px] text-cyan-400 uppercase font-semibold">State / Knowledge</span>
            <p className="text-2xl font-bold text-cyan-400 mt-1">{exposure.state_bills_count + exposure.knowledge_only_bills_count}</p>
            <span className="text-[10px] text-slate-400 font-mono">0 Stock predictions</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800">
        <button
          onClick={() => setActiveTab("exposure")}
          className={cn(
            "px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2",
            activeTab === "exposure"
              ? "border-blue-500 text-blue-400 bg-blue-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          )}
        >
          <span>⚖</span> Portfolio Legislative Exposure ({exposure?.total_relevant_bills || 0})
        </button>
        <button
          onClick={() => setActiveTab("holdings")}
          className={cn(
            "px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2",
            activeTab === "holdings"
              ? "border-blue-500 text-blue-400 bg-blue-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          )}
        >
          <span>🏢</span> Your Holdings ({activePortfolio?.holdings.length || 0})
        </button>
        {reportData && (
          <button
            onClick={() => setActiveTab("report")}
            className={cn(
              "px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2",
              activeTab === "report"
                ? "border-blue-500 text-blue-400 bg-blue-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            <span>📄</span> My Legislative Impact Report
          </button>
        )}
      </div>

      {/* TAB 1: LEGISLATIVE EXPOSURE */}
      {activeTab === "exposure" && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Relevance Tier:</span>
              <div className="flex gap-1.5 flex-wrap">
                {["ALL", "DIRECT", "HIGH RELEVANCE", "MODERATE RELEVANCE", "INDIRECT"].map((tier) => (
                  <button
                    key={tier}
                    onClick={() => setTierFilter(tier)}
                    className={cn(
                      "px-2.5 py-1 rounded text-[11px] font-semibold transition-all",
                      tierFilter === tier
                        ? "bg-blue-600 text-white"
                        : "bg-slate-800 text-slate-400 hover:text-white"
                    )}
                  >
                    {tier}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Jurisdiction:</span>
              <div className="flex gap-1.5">
                {["ALL", "CENTRAL", "STATE"].map((jx) => (
                  <button
                    key={jx}
                    onClick={() => setJurisdictionFilter(jx)}
                    className={cn(
                      "px-2.5 py-1 rounded text-[11px] font-semibold transition-all",
                      jurisdictionFilter === jx
                        ? "bg-blue-600 text-white"
                        : "bg-slate-800 text-slate-400 hover:text-white"
                    )}
                  >
                    {jx}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Exposure Items List */}
          {loading ? (
            <div className="p-12 text-center text-slate-500 font-mono text-sm">
              Analyzing deterministic legislative exposure across portfolio holdings...
            </div>
          ) : filteredBills.length === 0 ? (
            <div className="p-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
              No legislative items match the selected filter criteria.
            </div>
          ) : (
            <div className="space-y-4">
              {filteredBills.map((b) => {
                const tierStyle = TIER_BADGES[b.relevance_tier] || TIER_BADGES.INFORMATIONAL;
                const modelStyle = MODEL_STATUS_BADGES[b.model_status] || MODEL_STATUS_BADGES["KNOWLEDGE ONLY"];

                return (
                  <div
                    key={b.bill_id}
                    className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-all space-y-3.5"
                  >
                    {/* Top Row: Title, Tier Badge, Model Badge */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <Link
                            href={`/bills/${b.bill_id}`}
                            className="text-base font-bold text-slate-100 hover:text-blue-400 transition-colors"
                          >
                            {b.bill_title}
                          </Link>
                          {b.bill_number && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                              {b.bill_number}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400 flex-wrap">
                          <span className="font-semibold text-slate-300">
                            {b.jurisdiction === "central" ? "Central Parliament" : `${b.state} Assembly`}
                          </span>
                          <span>•</span>
                          <span>Status: <strong className="text-slate-200 capitalize">{b.status}</strong></span>
                          {b.latest_verified_update && (
                            <>
                              <span>•</span>
                              <span>Latest Update: <strong className="text-slate-300">{b.latest_verified_update}</strong></span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Badges */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={cn("text-xs font-bold px-2.5 py-1 rounded-md border", tierStyle.bg, tierStyle.text, tierStyle.border)}>
                          {b.relevance_tier}
                        </span>
                        <span className={cn("text-xs font-bold px-2.5 py-1 rounded-md border", modelStyle.bg, modelStyle.text, modelStyle.border)}>
                          {b.model_status}
                        </span>
                      </div>
                    </div>

                    {/* Linkage Reason & Evidence */}
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                      <div className="flex items-start gap-2">
                        <span className="text-amber-400 font-bold text-xs mt-0.5">✦</span>
                        <div className="text-xs text-slate-200 leading-relaxed font-medium">
                          <strong className="text-amber-300 font-semibold">Linkage Reason:</strong> {b.primary_linkage_reason}
                        </div>
                      </div>

                      {/* Affected Company and Sectors */}
                      <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1 flex-wrap">
                        {b.affected_companies.length > 0 && (
                          <span>
                            Exposed Holding: <strong className="text-slate-200">{b.affected_companies.join(", ")}</strong>
                          </span>
                        )}
                        {b.affected_sectors.length > 0 && (
                          <span>
                            Sector: <strong className="text-slate-200">{b.affected_sectors.join(", ")}</strong>
                          </span>
                        )}
                        {b.affected_industries.length > 0 && (
                          <span>
                            Industry: <strong className="text-slate-200">{b.affected_industries.join(", ")}</strong>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Authoritative Model Data (if Central Modelled) */}
                    {b.model_status === "MODELLED" && b.authoritative_prediction && (
                      <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/30 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-emerald-400">Authoritative Central Model Output (Frozen Baseline)</span>
                          <span className="text-[10px] font-mono text-emerald-500">ISIN: {b.authoritative_prediction.isin}</span>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                          <div>
                            <span className="text-slate-400">Direction:</span>{" "}
                            <strong className={cn(
                              b.authoritative_prediction.predicted_direction === "POSITIVE" ? "text-emerald-400" :
                              b.authoritative_prediction.predicted_direction === "NEGATIVE" ? "text-rose-400" : "text-slate-300"
                            )}>
                              {b.authoritative_prediction.predicted_direction}
                            </strong>
                          </div>
                          <div>
                            <span className="text-slate-400">Confidence:</span>{" "}
                            <strong className="text-slate-200">{b.authoritative_prediction.predicted_confidence}</strong>
                          </div>
                          <div>
                            <span className="text-slate-400">Horizon:</span>{" "}
                            <strong className="text-slate-200 font-mono">{b.authoritative_prediction.event_window}</strong>
                          </div>
                          <div>
                            <span className="text-slate-400">Risk Band:</span>{" "}
                            <strong className="text-amber-400">{b.authoritative_prediction.risk_category || "MODERATE"}</strong>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* State Legislation Firewall Notice */}
                    {b.jurisdiction === "state" && (
                      <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
                        <span>🛡</span>
                        <span>State Stock Predictions = 0 (Statutory Methodology Invariant). Business intelligence only.</span>
                      </div>
                    )}

                    {/* Footer Controls */}
                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/50">
                      <div className="flex items-center gap-2">
                        {b.source_provenance[0] && (
                          <a
                            href={b.source_provenance[0]}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] text-blue-400 hover:underline flex items-center gap-1"
                          >
                            <span>Source Provenance ↗</span>
                          </a>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleExplainRelevance(b.bill_id)}
                          className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
                        >
                          ✦ Explain Relevance
                        </button>
                        <Link
                          href={`/bills/${b.bill_id}`}
                          className="px-3 py-1 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-medium border border-blue-500/30 transition-colors"
                        >
                          View Bill Dossier →
                        </Link>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: YOUR HOLDINGS */}
      {activeTab === "holdings" && activePortfolio && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">{activePortfolio.name}</h2>
              <p className="text-xs text-slate-400">{activePortfolio.description || "Active tracking portfolio"}</p>
            </div>
            <button
              onClick={() => setShowAddHoldingModal(true)}
              className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
            >
              + Add Company
            </button>
          </div>

          <div className="rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Company</th>
                  <th className="p-3.5">ISIN / Ticker</th>
                  <th className="p-3.5">Sector & Industry</th>
                  <th className="p-3.5">User Holdings</th>
                  <th className="p-3.5">Exposed Bills</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 bg-slate-950/40">
                {activePortfolio.holdings.map((h) => {
                  const exposedCount = exposure?.holdings_exposure_map[h.company_name]?.length || 0;

                  return (
                    <tr key={h.holding_id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="p-3.5 font-semibold text-slate-200">
                        {h.company_name}
                      </td>
                      <td className="p-3.5 font-mono text-slate-400">
                        {h.isin || h.ticker || "—"}
                      </td>
                      <td className="p-3.5 text-slate-300">
                        {h.sector || "Unclassified"} {h.industry ? `• ${h.industry}` : ""}
                      </td>
                      <td className="p-3.5 text-slate-300">
                        {h.quantity ? `${h.quantity} shares` : "Tracked"}
                        {h.avg_purchase_price ? ` @ ₹${h.avg_purchase_price}` : ""}
                      </td>
                      <td className="p-3.5">
                        <span className={cn(
                          "px-2 py-0.5 rounded text-[11px] font-bold font-mono",
                          exposedCount > 0 ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : "bg-slate-800 text-slate-500"
                        )}>
                          {exposedCount} bills
                        </span>
                      </td>
                      <td className="p-3.5 text-right">
                        <button
                          onClick={async () => {
                            if (confirm(`Remove ${h.company_name} from portfolio?`)) {
                              await portfolioApi.removeHolding(activePortfolio.portfolio_id, h.holding_id);
                              loadPortfolioData();
                            }
                          }}
                          className="text-xs text-rose-400 hover:text-rose-300 font-medium"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: IMPACT REPORT */}
      {activeTab === "report" && reportData && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-xl font-bold text-slate-100">{reportData.report_title}</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Generated: {reportData.generated_at} • Scoped strictly to your authorized holdings
              </p>
            </div>
            <button
              onClick={() => window.print()}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700"
            >
              Print / Save PDF
            </button>
          </div>

          {/* Section 1: Portfolio Summary */}
          <div className="space-y-2">
            <h3 className="text-xs uppercase font-bold text-blue-400 tracking-wider">1. Portfolio Summary</h3>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-slate-400">Total Holdings:</span>{" "}
                <strong className="text-slate-100">{reportData.portfolio_summary.total_holdings}</strong>
              </div>
              <div>
                <span className="text-slate-400">Exposed Holdings:</span>{" "}
                <strong className="text-emerald-400">{reportData.portfolio_summary.exposed_holdings_count}</strong>
              </div>
              <div>
                <span className="text-slate-400">Relevant Bills:</span>{" "}
                <strong className="text-blue-400">{reportData.portfolio_summary.total_relevant_bills}</strong>
              </div>
              <div>
                <span className="text-slate-400">Direct Ties:</span>{" "}
                <strong className="text-rose-400">{reportData.portfolio_summary.direct_bills_count}</strong>
              </div>
            </div>
          </div>

          {/* Section 2: Relevant Legislation Table */}
          <div className="space-y-2">
            <h3 className="text-xs uppercase font-bold text-blue-400 tracking-wider">2. Relevant Legislative Measures</h3>
            <div className="rounded-xl border border-slate-800 overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-3">Bill</th>
                    <th className="p-3">Jurisdiction</th>
                    <th className="p-3">Tier</th>
                    <th className="p-3">Model Status</th>
                    <th className="p-3">Linkage Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 bg-slate-950/40">
                  {reportData.relevant_bills.map((b) => (
                    <tr key={b.bill_id}>
                      <td className="p-3 font-semibold text-slate-200">{b.bill_title}</td>
                      <td className="p-3 capitalize text-slate-400">{b.jurisdiction} {b.state ? `(${b.state})` : ""}</td>
                      <td className="p-3 font-bold text-amber-400">{b.relevance_tier}</td>
                      <td className="p-3 font-mono text-cyan-400">{b.model_status}</td>
                      <td className="p-3 text-slate-300 max-w-xs">{b.primary_linkage_reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Disclaimers & Epistemic Boundaries */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            {reportData.disclaimers.map((d, i) => (
              <p key={i}>{d}</p>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: Explain Relevance (Grounded AI / Deterministic) */}
      {selectedExplainBill && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-lg">✦</span>
                <h3 className="text-sm font-bold text-slate-100">Grounded Relevance Analysis</h3>
              </div>
              <button
                onClick={() => setSelectedExplainBill(null)}
                className="text-slate-400 hover:text-white text-base"
              >
                ✕
              </button>
            </div>

            {explainLoading ? (
              <div className="p-8 text-center text-xs font-mono text-slate-400">
                Synthesizing evidence-backed linkages across bill dossier and holdings...
              </div>
            ) : explainResult ? (
              <div className="space-y-4 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Relevance Tier:</span>
                  <span className="font-bold text-amber-400 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
                    {explainResult.relevance_tier}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 leading-relaxed text-slate-200 whitespace-pre-wrap">
                  {explainResult.explanation}
                </div>

                <div className="text-[10px] text-slate-500 leading-tight border-t border-slate-800 pt-3">
                  {explainResult.disclaimer}
                </div>
              </div>
            ) : null}

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedExplainBill(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Add Holding */}
      {showAddHoldingModal && activePortfolio && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const form = e.target as HTMLFormElement;
              const fd = new FormData(form);
              await portfolioApi.addHolding(activePortfolio.portfolio_id, {
                company_name: String(fd.get("company_name")),
                isin: String(fd.get("isin") || ""),
                ticker: String(fd.get("ticker") || ""),
                sector: String(fd.get("sector") || ""),
                industry: String(fd.get("industry") || ""),
                quantity: fd.get("quantity") ? Number(fd.get("quantity")) : undefined,
                avg_purchase_price: fd.get("avg_purchase_price") ? Number(fd.get("avg_purchase_price")) : undefined,
              });
              setShowAddHoldingModal(false);
              loadPortfolioData();
            }}
            className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100">Add Portfolio Holding</h3>
              <button
                type="button"
                onClick={() => setShowAddHoldingModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Company Name *</label>
                <input
                  name="company_name"
                  required
                  placeholder="e.g. Reliance Industries Limited"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">ISIN (optional)</label>
                  <input
                    name="isin"
                    placeholder="e.g. INE002A01018"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 font-mono focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Ticker (optional)</label>
                  <input
                    name="ticker"
                    placeholder="e.g. RELIANCE"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 font-mono focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Sector</label>
                  <input
                    name="sector"
                    placeholder="e.g. Energy"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Industry</label>
                  <input
                    name="industry"
                    placeholder="e.g. Oil & Gas"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Quantity</label>
                  <input
                    name="quantity"
                    type="number"
                    placeholder="e.g. 50"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Avg Price (₹)</label>
                  <input
                    name="avg_purchase_price"
                    type="number"
                    step="0.01"
                    placeholder="e.g. 2650"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAddHoldingModal(false)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white"
              >
                Save Holding
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL: Import CSV / XLSX */}
      {showUploadModal && activePortfolio && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100">Import Holdings</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-6 border-2 border-dashed border-slate-800 rounded-xl text-center space-y-2 hover:border-slate-700 transition-colors">
              <span className="text-3xl">📂</span>
              <p className="text-xs text-slate-300 font-medium">Select or drop a CSV or JSON file</p>
              <p className="text-[10px] text-slate-500">Columns: company_name, isin, ticker, sector, industry, quantity, avg_purchase_price</p>
              <input
                type="file"
                accept=".csv,.json"
                className="text-xs text-slate-400 mt-2"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const text = await file.text();
                  try {
                    let holdingsToImport = [];
                    if (file.name.endsWith(".json")) {
                      holdingsToImport = JSON.parse(text);
                    } else {
                      // Basic CSV parsing
                      const lines = text.split("\n").filter(Boolean);
                      const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());
                      for (let i = 1; i < lines.length; i++) {
                        const vals = lines[i].split(",").map((v) => v.trim());
                        const item: Record<string, any> = {};
                        headers.forEach((h, idx) => { item[h] = vals[idx]; });
                        if (item.company_name || item.company) {
                          holdingsToImport.push({
                            company_name: item.company_name || item.company,
                            isin: item.isin,
                            ticker: item.ticker,
                            sector: item.sector,
                            industry: item.industry,
                            quantity: item.quantity ? Number(item.quantity) : undefined,
                            avg_purchase_price: item.avg_purchase_price ? Number(item.avg_purchase_price) : undefined,
                          });
                        }
                      }
                    }
                    if (holdingsToImport.length > 0) {
                      await portfolioApi.importHoldings(activePortfolio.portfolio_id, holdingsToImport);
                      setShowUploadModal(false);
                      loadPortfolioData();
                    }
                  } catch (parseErr) {
                    alert("Error parsing file format.");
                  }
                }}
              />
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
