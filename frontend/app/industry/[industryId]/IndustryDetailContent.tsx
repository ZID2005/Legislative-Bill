/**
 * app/industry/[industryId]/IndustryDetailContent.tsx
 * ====================================================
 * Industry Intelligence Dossier client component with 13 comprehensive sections (A through M).
 */

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { industriesApi } from "@/lib/api/industries";
import { IndustryHeader } from "@/components/industries/IndustryHeader";
import { IndustryExecutiveOverview } from "@/components/industries/IndustryExecutiveOverview";
import { IndustryLegislativeFootprint } from "@/components/industries/IndustryLegislativeFootprint";
import { IndustryCorporateExposure } from "@/components/industries/IndustryCorporateExposure";
import { EconomicTransmissionMap } from "@/components/industries/EconomicTransmissionMap";
import { IndustryMarketIntelligence } from "@/components/industries/IndustryMarketIntelligence";
import { IndustryRiskAnticipationContext } from "@/components/industries/IndustryRiskAnticipationContext";
import { IndustryAIAnalystPanel } from "@/components/industries/IndustryAIAnalystPanel";
import { IndustryProvenancePanel } from "@/components/industries/IndustryProvenancePanel";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import type { IndustryDossierResponse } from "@/types/api";

export interface IndustryDetailContentProps {
  industryId: string;
}

export default function IndustryDetailContent({ industryId }: IndustryDetailContentProps) {
  const [dossier, setDossier] = useState<IndustryDossierResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDossier = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await industriesApi.getIndustry(industryId);
      setDossier(data);
    } catch (err: any) {
      setError(
        err?.message ||
          `Industry '${industryId}' was not found in registered corporate or legislative datasets.`
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDossier();
  }, [industryId]);

  if (loading) {
    return (
      <div className="space-y-6 pb-12 animate-pulse">
        <div className="h-44 rounded-xl border border-slate-800 bg-slate-900/60 p-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-40 rounded-xl border border-slate-800 bg-slate-900/60 p-5" />
          <div className="h-40 rounded-xl border border-slate-800 bg-slate-900/60 p-5" />
        </div>
        <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/60 p-6" />
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-12 text-center space-y-4">
        <span className="text-3xl block">⚠️</span>
        <h1 className="text-lg font-bold text-white">Industry Dossier Not Found</h1>
        <p className="text-xs text-rose-300 max-w-md mx-auto">
          {error || `No verified industry dossier matches '${industryId}'.`}
        </p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <Link
            href="/industries"
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs text-slate-200 hover:text-white transition-colors"
          >
            ← Back to Industries
          </Link>
          <button
            type="button"
            onClick={loadDossier}
            className="rounded-lg bg-rose-900/60 border border-rose-700/50 px-4 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-800 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Section A: Industry Header */}
      <IndustryHeader dossier={dossier} />

      {/* Section B: Executive Overview (4-Zone Epistemic Separation) */}
      <IndustryExecutiveOverview dossier={dossier} />

      {/* Section E: Economic Transmission Map */}
      <EconomicTransmissionMap
        transmissionChains={dossier.transmission_chains}
        activeMechanisms={dossier.active_mechanisms}
      />

      {/* Section C: Legislative Footprint (Separating Central & State) */}
      <IndustryLegislativeFootprint
        centralBills={dossier.central_bills}
        stateBills={dossier.state_bills}
      />

      {/* Section D & J: Corporate Exposure & Company Network */}
      <IndustryCorporateExposure
        quantitativeCompanies={dossier.quantitative_companies}
        intelligenceCompanies={dossier.intelligence_companies}
        referenceCompanies={dossier.reference_companies}
      />

      {/* Section F: Central Market Intelligence (where available) */}
      <IndustryMarketIntelligence dossier={dossier} />

      {/* Section G: State Legislative Intelligence & State Prediction Firewall */}
      <section aria-labelledby="state-intelligence-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="state-intelligence-heading" className="text-lg font-semibold text-white">
            State Legislative Intelligence
          </h2>
          <span className="text-xs text-blue-400">
            {dossier.state_intelligence.states_covered.length > 0
              ? `Operational in: ${dossier.state_intelligence.states_covered.join(", ")}`
              : "No State Statutes Enacted"}
          </span>
        </div>

        <StatePredictionFirewall
          state={dossier.state_intelligence.states_covered.join(", ") || "State Assemblies"}
          predictionStatus={{
            is_modeled: false,
            message: dossier.state_intelligence.firewall_statement,
          } as any}
        />
      </section>

      {/* Section H & I: Risk Context and Anticipation Context */}
      <IndustryRiskAnticipationContext
        riskSummary={dossier.risk_summary}
        anticipationSummary={dossier.anticipation_summary}
      />

      {/* Section L: Grounded AI Industry Analyst Panel */}
      <IndustryAIAnalystPanel
        industryId={dossier.industry_id}
        industryName={dossier.name}
      />

      {/* Section K & M: Peer Sector Industries & Provenance */}
      <IndustryProvenancePanel
        provenanceSources={dossier.provenance_sources}
        relatedIndustries={dossier.related_industries}
      />
    </div>
  );
}
