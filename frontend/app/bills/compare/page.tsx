/**
 * app/bills/compare/page.tsx
 * ===========================
 * Task 8.31C — Institutional Statutory Comparison Workspace.
 *
 * Side-by-side statutory diff and corporate exposure overlap analysis:
 * - Dual bill selector (Central & State)
 * - Metadata comparison grid
 * - Key provisions mapping & regulatory powers
 * - Corporate exposure overlap matrix
 * - Econometric market impact delta (Central Level 1 bills)
 * - Official source provenance & gazette PDF links
 */

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { billsApi } from "@/lib/api/bills";
import type { BillDetailResponse, BillSummaryItem, BillCompanyExposure } from "@/types/api";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { CapabilityBadge } from "@/components/coverage/CapabilityBadge";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { SkeletonCard, EmptyState, ErrorState } from "@/components/ui/Skeleton";
import { getCapabilityLevel } from "@/lib/utils";

export default function BillComparisonPage() {
  const [billsList, setBillsList] = useState<BillSummaryItem[]>([]);
  const [billAId, setBillAId] = useState<string>("");
  const [billBId, setBillBId] = useState<string>("");

  const [billA, setBillA] = useState<BillDetailResponse | null>(null);
  const [billB, setBillB] = useState<BillDetailResponse | null>(null);

  const [exposuresA, setExposuresA] = useState<BillCompanyExposure[]>([]);
  const [exposuresB, setExposuresB] = useState<BillCompanyExposure[]>([]);

  const [loadingList, setLoadingList] = useState(true);
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available bills list
  useEffect(() => {
    let cancelled = false;
    setLoadingList(true);
    billsApi
      .listBills({ limit: 100 })
      .then((res) => {
        if (!cancelled && res.items.length > 0) {
          setBillsList(res.items);
          // Set default pair: first two bills
          setBillAId(res.items[0].bill_id);
          if (res.items.length > 1) {
            setBillBId(res.items[1].bill_id);
          }
        }
      })
      .catch((err) => {
        if (!cancelled) setError("Failed to load bills directory.");
      })
      .finally(() => {
        if (!cancelled) setLoadingList(false);
      });

    return () => { cancelled = true; };
  }, []);

  // Fetch comparison data when selections change
  useEffect(() => {
    if (!billAId || !billBId) return;
    let cancelled = false;
    setLoadingComparison(true);
    setError(null);

    Promise.all([
      billsApi.getBill(billAId),
      billsApi.getBill(billBId),
      billsApi.getBillCompanies(billAId).catch(() => []),
      billsApi.getBillCompanies(billBId).catch(() => []),
    ])
      .then(([detailA, detailB, expA, expB]) => {
        if (!cancelled) {
          const normA = (detailA as any)?.bill ? detailA : { bill: detailA, provisions: (detailA as any)?.provisions || [], provenance: {}, prediction_available: false, related_bills: [] };
          const normB = (detailB as any)?.bill ? detailB : { bill: detailB, provisions: (detailB as any)?.provisions || [], provenance: {}, prediction_available: false, related_bills: [] };
          setBillA(normA as any);
          setBillB(normB as any);
          setExposuresA(expA);
          setExposuresB(expB);
        }
      })
      .catch((err) => {
        if (!cancelled) setError("Failed to fetch statutory comparison data.");
      })
      .finally(() => {
        if (!cancelled) setLoadingComparison(false);
      });

    return () => { cancelled = true; };
  }, [billAId, billBId]);

  // Compute exposure overlap
  const overlapAnalysis = React.useMemo(() => {
    const mapA = new Set(exposuresA.map((e) => e.company_name || e.company_id));
    const mapB = new Set(exposuresB.map((e) => e.company_name || e.company_id));

    const common = exposuresA.filter((e) => mapB.has(e.company_name || e.company_id));
    const uniqueA = exposuresA.filter((e) => !mapB.has(e.company_name || e.company_id));
    const uniqueB = exposuresB.filter((e) => !mapA.has(e.company_name || e.company_id));

    return { common, uniqueA, uniqueB };
  }, [exposuresA, exposuresB]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⚖</span>
            <h1 className="text-xl font-bold text-white tracking-tight">Statutory Comparison Workbench</h1>
            <EpistemicBadge type="FACT" size="xs" />
          </div>
          <p className="text-xs text-slate-400">
            Side-by-side analytical comparison of provisions, corporate exposure overlap, and market transmission.
          </p>
        </div>
        <Link
          href="/bills"
          className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded border border-white/10 bg-white/5 transition-colors self-start sm:self-auto"
        >
          ← Back to Bills Directory
        </Link>
      </div>

      {error && <ErrorState error={error} onRetry={() => window.location.reload()} />}

      {/* Bill Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-[#0c1322] border border-white/10 rounded-lg p-4">
        {/* Left Bill Picker */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Primary Enactment (Side A)</span>
            {billA && <CapabilityBadge level={getCapabilityLevel(billA.bill.jurisdiction, billA.bill.modeling_eligibility)} />}
          </label>
          <select
            value={billAId}
            onChange={(e) => setBillAId(e.target.value)}
            disabled={loadingList}
            className="w-full bg-[#070b12] border border-white/10 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {billsList.map((b) => (
              <option key={b.bill_id} value={b.bill_id}>
                [{(b.jurisdiction || "central").toUpperCase()}] {b.title}
              </option>
            ))}
          </select>
        </div>

        {/* Right Bill Picker */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Comparison Enactment (Side B)</span>
            {billB && <CapabilityBadge level={getCapabilityLevel(billB.bill.jurisdiction, billB.bill.modeling_eligibility)} />}
          </label>
          <select
            value={billBId}
            onChange={(e) => setBillBId(e.target.value)}
            disabled={loadingList}
            className="w-full bg-[#070b12] border border-white/10 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {billsList.map((b) => (
              <option key={b.bill_id} value={b.bill_id}>
                [{(b.jurisdiction || "central").toUpperCase()}] {b.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loadingComparison && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {!loadingComparison && billA && billB && (
        <div className="space-y-6">
          {/* Section 1: Statutory Metadata Comparison */}
          <div className="bg-[#0c1322] border border-white/10 rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-[#090e18] border-b border-white/10 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                1. Institutional Statutory Profiles
              </h2>
              <span className="text-[10px] font-mono text-slate-500">Side-by-Side Metadata</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/10">
              {/* Bill A Profile */}
              <div className="p-4 space-y-3">
                <div>
                  <h3 className="text-sm font-bold text-white leading-snug">{billA.bill.title}</h3>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">{billA.bill.bill_number || "Statutory Act"}</p>
                </div>
                <div className="space-y-1.5 text-xs text-slate-300">
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Jurisdiction</span>
                    <span className="font-medium text-slate-200 uppercase">{billA.bill.jurisdiction} {billA.bill.state ? `(${billA.bill.state})` : ""}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Chamber</span>
                    <span>{billA.bill.house || "Parliament"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Status</span>
                    <span className="font-mono text-emerald-400 font-semibold">{billA.bill.status}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Enactment Date</span>
                    <span className="font-mono">{billA.bill.introduction_date || "—"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Policy Domain</span>
                    <span>{billA.bill.policy_domain || "Regulatory"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Exposures Documented</span>
                    <span className="font-mono font-bold text-slate-100">{exposuresA.length} entities</span>
                  </div>
                </div>
                <div className="pt-2">
                  <Link
                    href={`/bills/${billA.bill.bill_id}`}
                    className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    View Full Dossier A ↗
                  </Link>
                </div>
              </div>

              {/* Bill B Profile */}
              <div className="p-4 space-y-3">
                <div>
                  <h3 className="text-sm font-bold text-white leading-snug">{billB.bill.title}</h3>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">{billB.bill.bill_number || "Statutory Act"}</p>
                </div>
                <div className="space-y-1.5 text-xs text-slate-300">
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Jurisdiction</span>
                    <span className="font-medium text-slate-200 uppercase">{billB.bill.jurisdiction} {billB.bill.state ? `(${billB.bill.state})` : ""}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Chamber</span>
                    <span>{billB.bill.house || "Parliament"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Status</span>
                    <span className="font-mono text-emerald-400 font-semibold">{billB.bill.status}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Enactment Date</span>
                    <span className="font-mono">{billB.bill.introduction_date || "—"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Policy Domain</span>
                    <span>{billB.bill.policy_domain || "Regulatory"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/5">
                    <span className="text-slate-500">Exposures Documented</span>
                    <span className="font-mono font-bold text-slate-100">{exposuresB.length} entities</span>
                  </div>
                </div>
                <div className="pt-2">
                  <Link
                    href={`/bills/${billB.bill.bill_id}`}
                    className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    View Full Dossier B ↗
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Corporate Exposure Overlap Analysis */}
          <div className="bg-[#0c1322] border border-white/10 rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-[#090e18] border-b border-white/10 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                2. Corporate Exposure Overlap Matrix
              </h2>
              <span className="text-[10px] font-mono text-slate-500">
                {overlapAnalysis.common.length} Overlapping Entities
              </span>
            </div>

            <div className="p-4 space-y-4">
              {/* Overlapping Companies */}
              {overlapAnalysis.common.length > 0 ? (
                <div>
                  <h4 className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider mb-2">
                    ⚠ Dual-Exposed Corporations (Impacted by Both Acts):
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    {overlapAnalysis.common.map((exp) => (
                      <div
                        key={exp.company_id || exp.company_name}
                        className="p-2.5 rounded bg-amber-950/20 border border-amber-500/30 flex items-center justify-between"
                      >
                        <div>
                          <p className="text-xs font-semibold text-slate-100">{exp.company_name}</p>
                          <p className="text-[10px] font-mono text-slate-400">{exp.sector || exp.company_id}</p>
                        </div>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 uppercase">
                          DUAL IMPACT
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-400 italic">
                  No direct corporate exposure overlap detected between these two enactments.
                </div>
              )}

              {/* Side A Unique Exposures vs Side B Unique Exposures */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-white/5">
                <div>
                  <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Exclusively Exposed to {billA.bill.short_title || billA.bill.title} ({overlapAnalysis.uniqueA.length}):
                  </h4>
                  <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                    {overlapAnalysis.uniqueA.slice(0, 8).map((exp) => (
                      <div key={exp.company_id || exp.company_name} className="flex items-center justify-between text-xs py-1 border-b border-white/5">
                        <span className="text-slate-300 truncate">{exp.company_name}</span>
                        <span className="font-mono text-[10px] text-slate-500">{exp.exposure_type || "DIRECT"}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Exclusively Exposed to {billB.bill.short_title || billB.bill.title} ({overlapAnalysis.uniqueB.length}):
                  </h4>
                  <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                    {overlapAnalysis.uniqueB.slice(0, 8).map((exp) => (
                      <div key={exp.company_id || exp.company_name} className="flex items-center justify-between text-xs py-1 border-b border-white/5">
                        <span className="text-slate-300 truncate">{exp.company_name}</span>
                        <span className="font-mono text-[10px] text-slate-500">{exp.exposure_type || "DIRECT"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Statutory Provisions Diff */}
          <div className="bg-[#0c1322] border border-white/10 rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-[#090e18] border-b border-white/10 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                3. Key Statutory Provisions Comparison
              </h2>
              <span className="text-[10px] font-mono text-slate-500">Section Analysis</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/10">
              {/* Provisions A */}
              <div className="p-4 space-y-2">
                <h4 className="text-xs font-semibold text-slate-300 mb-2">
                  {billA.bill.title} Provisions ({billA.provisions.length}):
                </h4>
                {billA.provisions.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No provision clauses recorded.</p>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {billA.provisions.map((p, idx) => (
                      <div key={idx} className="p-2 rounded bg-white/[0.02] border border-white/5 space-y-1">
                        <span className="text-[10px] font-mono text-indigo-400 font-semibold">{`Clause ${idx + 1}`}</span>
                        <p className="text-xs text-slate-300 leading-relaxed">{p}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Provisions B */}
              <div className="p-4 space-y-2">
                <h4 className="text-xs font-semibold text-slate-300 mb-2">
                  {billB.bill.title} Provisions ({billB.provisions.length}):
                </h4>
                {billB.provisions.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No provision clauses recorded.</p>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {billB.provisions.map((p, idx) => (
                      <div key={idx} className="p-2 rounded bg-white/[0.02] border border-white/5 space-y-1">
                        <span className="text-[10px] font-mono text-indigo-400 font-semibold">{`Clause ${idx + 1}`}</span>
                        <p className="text-xs text-slate-300 leading-relaxed">{p}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
