/**
 * components/bills/StakeholderIntelligence.tsx
 * ============================================
 * Multi-Persona Stakeholder Intelligence for the Bill Detail Dossier.
 * Features tabs for:
 * - Investor, Business Owner, Employee, Consumer, Farmer, MSME, General Public, Industry
 * Strictly separates:
 *   FACT | DERIVED | INTERPRETATION | PREDICTION
 */

"use client";

import React, { useState } from "react";
import type { BillSummaryItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge } from "@/components/ui/Badge";

export interface StakeholderIntelligenceProps {
  bill: BillSummaryItem;
  className?: string;
}

interface PersonaInfo {
  id: string;
  name: string;
  icon: string;
  fact: string;
  derived: string;
  interpretation: string;
  prediction: string;
}

export function StakeholderIntelligence({
  bill,
  className = "",
}: StakeholderIntelligenceProps) {
  const isState = bill.jurisdiction?.toLowerCase() === "state";
  const sectors = bill.economic_sectors.join(", ") || "General Economy";
  const policy = bill.policy_domain || "Statutory Governance";
  const isModelled = bill.modeling_eligibility === "ELIGIBLE" && !isState;

  const personas: PersonaInfo[] = [
    {
      id: "investor",
      name: "Investor",
      icon: "💼",
      fact: `Legislative enactment tabled in ${bill.legislature} affecting ${sectors}. Official status is '${bill.status}'.`,
      derived: `Exposes ${bill.company_exposure_count} verified companies across ${sectors}. Market relevance classified as ${bill.market_relevance}.`,
      interpretation: "Assesses regulatory capital requirements, operational headroom, and risk premiums across exposed listed entities.",
      prediction: isModelled
        ? "Quantitative event study projections indicate potential sector sensitivity across short/medium horizons."
        : "Quantitative market prediction is unavailable under statutory research invariants.",
    },
    {
      id: "business",
      name: "Business Owner",
      icon: "🏢",
      fact: `Applies legal rules under the supervisory framework of ${bill.policy_domain || "State / Central authorities"}.`,
      derived: "Establishes compliance obligations, statutory documentation requirements, and administrative reporting standards.",
      interpretation: "Direct enterprise adaptation required for operations, supply chain contracting, and supervisory inspections.",
      prediction: "Financial models evaluate corporate cash-flow sensitivity and margin adjustments.",
    },
    {
      id: "employee",
      name: "Employee / Worker",
      icon: "👷",
      fact: "Governs statutory employment conditions, institutional oversight, and enterprise operational guidelines.",
      derived: "Affects workforce deployment, occupational compliance standards, and organizational safety protocols.",
      interpretation: "May influence formal job creation, skill certification demands, or contractual stability depending on sector adoption.",
      prediction: "Macroeconomic labor elasticity parameters apply without specific equity forecast.",
    },
    {
      id: "consumer",
      name: "Consumer",
      icon: "🛒",
      fact: `Sets regulatory parameters for products and services delivered in ${sectors}.`,
      derived: "Establishes consumer transparency benchmarks, statutory dispute mechanisms, and service quality requirements.",
      interpretation: "Intended to promote fair trade, consumer rights protection, and pricing transparency in target markets.",
      prediction: "Qualitative consumption basket effects; zero equity asset price implication.",
    },
    {
      id: "farmer",
      name: "Farmer / Rural",
      icon: "🌾",
      fact: "Statutory provisions enacted by competent legislature with potential rural or agrarian implications.",
      derived: "Interfaces with procurement networks, rural infrastructure, cooperative institutions, or land administration.",
      interpretation: "Directly or indirectly touches agricultural input logistics, local markets, or rural economic stability.",
      prediction: "Rural demand proxy modeling only; no speculative price targets.",
    },
    {
      id: "msme",
      name: "MSME / Small Enterprise",
      icon: "🏪",
      fact: `Statutory guidelines applicable across small and medium enterprises in ${sectors}.`,
      derived: "Defines threshold compliance tiers, vendor registration mandates, and statutory exemptions.",
      interpretation: "Lower administrative compliance friction enables broader formal credit access and vendor integration.",
      prediction: "Working capital cycle impact based on statutory settlement periods.",
    },
    {
      id: "public",
      name: "General Public",
      icon: "🏛",
      fact: `Official public legislation enacted under constitutional authority of ${bill.legislature}.`,
      derived: "Public transparency, official gazette publication, and democratic accountability parameters.",
      interpretation: "Strengthens statutory governance, administrative predictability, and civic access to public services.",
      prediction: "Public welfare indicators are purely qualitative socio-economic metrics.",
    },
    {
      id: "industry",
      name: "Corporate / Industry",
      icon: "🏭",
      fact: `Formal legislative statute impacting industrial value chains in ${sectors}.`,
      derived: `Directly impacts ${bill.company_exposure_count} corporate entities with documented exposure vectors.`,
      interpretation: "Guides multi-year Capex allocations, environmental and safety certifications, and industrial trade competitiveness.",
      prediction: isModelled
        ? "Evaluated through multi-horizon event window prediction matrices."
        : "State assembly industry vectors evaluated through qualitative exposure indices.",
    },
  ];

  const [activePersona, setActivePersona] = useState<string>("investor");
  const selected = personas.find((p) => p.id === activePersona) || personas[0];

  return (
    <div className={`space-y-4 ${className}`} aria-label="Stakeholder intelligence section">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2 w-full">
            <div>
              <CardTitle>Stakeholder Impact Intelligence</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Analytical assessment across 8 constituent personas, with clear semantic tiering.
              </p>
            </div>
            <SourceBadge type="INTERPRETATION" size="xs" showTooltip />
          </div>
        </CardHeader>

        {/* Persona Navigation Pills */}
        <div className="flex flex-wrap gap-1.5 p-1 rounded-lg border border-slate-800 bg-slate-900/60 mb-5">
          {personas.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setActivePersona(p.id)}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                activePersona === p.id
                  ? "bg-blue-600 text-white shadow-sm font-semibold"
                  : "bg-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
              aria-selected={activePersona === p.id}
            >
              <span aria-hidden="true">{p.icon}</span>
              <span>{p.name}</span>
            </button>
          ))}
        </div>

        {/* Structured 4-Tier Semantic Breakdown */}
        <div className="space-y-3.5">
          {/* 1. FACT */}
          <div className="rounded-lg border border-emerald-900/40 bg-emerald-950/20 p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-300">
                1. Official Statutory Fact
              </span>
              <SourceBadge type="FACT" size="xs" />
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {selected.fact}
            </p>
          </div>

          {/* 2. DERIVED */}
          <div className="rounded-lg border border-blue-900/40 bg-blue-950/20 p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-300">
                2. Deterministic Mapping Vector
              </span>
              <SourceBadge type="DERIVED" size="xs" />
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {selected.derived}
            </p>
          </div>

          {/* 3. INTERPRETATION */}
          <div className="rounded-lg border border-amber-900/40 bg-amber-950/20 p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-300">
                3. Analytical Impact Interpretation
              </span>
              <SourceBadge type="INTERPRETATION" size="xs" />
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {selected.interpretation}
            </p>
          </div>

          {/* 4. PREDICTION */}
          <div className="rounded-lg border border-purple-900/40 bg-purple-950/20 p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-purple-300">
                4. Market &amp; Sensitivity Tier
              </span>
              <SourceBadge type="PREDICTION" size="xs" />
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {selected.prediction}
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-[11px] text-slate-500 italic mt-3 text-center">
          Stakeholder perspectives synthesize documented statutory facts with economic domain mappings. Zero individual financial advice is provided.
        </p>
      </Card>
    </div>
  );
}

export default StakeholderIntelligence;
