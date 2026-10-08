/**
 * app/states/StatesContent.tsx
 * ============================
 * Task 8.31C — Modern Sub-National Legislative Intelligence Registry.
 *
 * Implements:
 * - 4 Implemented Pilot States: Andhra Pradesh (12), Karnataka (11), Kerala (11), Telangana (10)
 * - Total 44 Enacted State Acts, 86 Corporate Exposures
 * - 24 Planned Union Jurisdictions roadmap matrix
 * - Mandatory State Stock Prediction Firewall notice (State Predictions = 0)
 * - Deep links to state dossiers and filtered bill registers
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { cn } from "@/lib/utils";

interface ActiveStateData {
  id: string;
  code: string;
  name: string;
  capital: string;
  assembly: string;
  actsCount: number;
  exposuresCount: number;
  officialSource: string;
  sectors: string[];
  description: string;
}

const ACTIVE_STATES: ActiveStateData[] = [
  {
    id: "Andhra Pradesh",
    code: "AP",
    name: "Andhra Pradesh",
    capital: "Amaravati",
    assembly: "Andhra Pradesh Legislative Assembly",
    actsCount: 12,
    exposuresCount: 26,
    officialSource: "Andhra Pradesh Official Gazette",
    sectors: ["Energy & Renewables", "Ports & Logistics", "Mining", "Agriculture"],
    description:
      "Comprehensive legislative coverage of coastal corridor infrastructure, clean energy incentives, and mining regulatory reforms.",
  },
  {
    id: "Karnataka",
    code: "KA",
    name: "Karnataka",
    capital: "Bengaluru",
    assembly: "Karnataka Legislative Assembly",
    actsCount: 11,
    exposuresCount: 22,
    officialSource: "Karnataka Gazette & Legislative Secretariat",
    sectors: ["Information Technology", "Platform Economy & Labor", "Cinema & Media", "Urban Infrastructure"],
    description:
      "Key pioneer enactments including Platform Based Gig Workers Welfare Act and statutory municipal licensing amendments.",
  },
  {
    id: "Kerala",
    code: "KL",
    name: "Kerala",
    capital: "Thiruvananthapuram",
    assembly: "Kerala Legislative Assembly (Niyamasabha)",
    actsCount: 11,
    exposuresCount: 18,
    officialSource: "Kerala Government Gazette",
    sectors: ["Healthcare & Public Health", "Tourism & Ecology", "Cooperative Institutions", "Maritime Trade"],
    description:
      "Public health safeguards, eco-sensitive commercial zoning regulations, and cooperative sector compliance standards.",
  },
  {
    id: "Telangana",
    code: "TS",
    name: "Telangana",
    capital: "Hyderabad",
    assembly: "Telangana Legislative Assembly",
    actsCount: 10,
    exposuresCount: 20,
    officialSource: "Telangana Official Gazette",
    sectors: ["Biopharma & Life Sciences", "Digital Gaming & Entertainment", "Industrial Promotion", "Urban Development"],
    description:
      "Statutory frameworks governing digital gaming restrictions, pharmaceutical industrial cluster incentives, and land administration.",
  },
];

interface PlannedStateData {
  name: string;
  capital: string;
  zone: string;
  targetTimeline: string;
}

const PLANNED_STATES: PlannedStateData[] = [
  { name: "Maharashtra", capital: "Mumbai", zone: "Western", targetTimeline: "Phase II" },
  { name: "Tamil Nadu", capital: "Chennai", zone: "Southern", targetTimeline: "Phase II" },
  { name: "Gujarat", capital: "Gandhinagar", zone: "Western", targetTimeline: "Phase II" },
  { name: "Uttar Pradesh", capital: "Lucknow", zone: "Northern", targetTimeline: "Phase II" },
  { name: "Delhi (NCT)", capital: "New Delhi", zone: "Northern", targetTimeline: "Phase II" },
  { name: "West Bengal", capital: "Kolkata", zone: "Eastern", targetTimeline: "Phase III" },
  { name: "Rajasthan", capital: "Jaipur", zone: "Northern", targetTimeline: "Phase III" },
  { name: "Madhya Pradesh", capital: "Bhopal", zone: "Central", targetTimeline: "Phase III" },
  { name: "Punjab", capital: "Chandigarh", zone: "Northern", targetTimeline: "Phase III" },
  { name: "Haryana", capital: "Chandigarh", zone: "Northern", targetTimeline: "Phase III" },
  { name: "Odisha", capital: "Bhubaneswar", zone: "Eastern", targetTimeline: "Phase III" },
  { name: "Bihar", capital: "Patna", zone: "Eastern", targetTimeline: "Phase III" },
  { name: "Assam", capital: "Dispur", zone: "North-Eastern", targetTimeline: "Phase IV" },
  { name: "Jharkhand", capital: "Ranchi", zone: "Eastern", targetTimeline: "Phase IV" },
  { name: "Chhattisgarh", capital: "Raipur", zone: "Central", targetTimeline: "Phase IV" },
  { name: "Uttarakhand", capital: "Dehradun", zone: "Northern", targetTimeline: "Phase IV" },
  { name: "Himachal Pradesh", capital: "Shimla", zone: "Northern", targetTimeline: "Phase IV" },
  { name: "Goa", capital: "Panaji", zone: "Western", targetTimeline: "Phase IV" },
  { name: "Tripura", capital: "Agartala", zone: "North-Eastern", targetTimeline: "Phase IV" },
  { name: "Meghalaya", capital: "Shillong", zone: "North-Eastern", targetTimeline: "Phase IV" },
  { name: "Manipur", capital: "Imphal", zone: "North-Eastern", targetTimeline: "Phase IV" },
  { name: "Nagaland", capital: "Kohima", zone: "North-Eastern", targetTimeline: "Phase IV" },
  { name: "Sikkim", capital: "Gangtok", zone: "North-Eastern", targetTimeline: "Phase IV" },
  { name: "Arunachal Pradesh", capital: "Itanagar", zone: "North-Eastern", targetTimeline: "Phase IV" },
];

export default function StatesContent() {
  const [zoneFilter, setZoneFilter] = useState<string>("All");

  const filteredPlanned =
    zoneFilter === "All"
      ? PLANNED_STATES
      : PLANNED_STATES.filter((s) => s.zone === zoneFilter);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Breadcrumb */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xl">🗺</span>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
                Sub-National Legislative Intelligence Registry
              </h1>
              <EpistemicBadge type="FACT" size="sm" />
            </div>
            <p className="text-sm text-slate-400">
              Federated coverage of state legislative assemblies. 4 active pilot jurisdictions + 24 roadmap states.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/bills?jurisdiction=state"
              className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded border border-slate-700 transition-colors"
            >
              Browse 44 State Acts →
            </Link>
            <Link
              href="/coverage"
              className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded border border-slate-700 transition-colors"
            >
              System Coverage Audit →
            </Link>
          </div>
        </div>

        {/* Invariant Metric Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800">
            <div className="text-xs text-slate-400">Implemented States</div>
            <div className="text-2xl font-bold font-mono-num text-slate-100 mt-1">4</div>
            <div className="text-[11px] text-emerald-400 mt-0.5">AP, KA, KL, TS</div>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800">
            <div className="text-xs text-slate-400">Production State Acts</div>
            <div className="text-2xl font-bold font-mono-num text-slate-100 mt-1">44</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Enacted & Ingested</div>
          </div>
          <div className="p-3.5 rounded-lg bg-indigo-950/20 border border-indigo-800/30">
            <div className="text-xs text-indigo-400">Corporate Exposures</div>
            <div className="text-2xl font-bold font-mono-num text-indigo-300 mt-1">86</div>
            <div className="text-[11px] text-indigo-400/70 mt-0.5">Operational Links</div>
          </div>
          <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-800/40">
            <div className="text-xs text-rose-400">State Stock Predictions</div>
            <div className="text-2xl font-bold font-mono-num text-rose-300 mt-1">0</div>
            <div className="text-[11px] text-rose-400/80 mt-0.5 font-medium">Strict Firewall Invariant</div>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800">
            <div className="text-xs text-slate-400">Planned States</div>
            <div className="text-2xl font-bold font-mono-num text-slate-100 mt-1">24</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Union Expansion</div>
          </div>
        </div>
      </div>

      {/* Mandatory State Stock Prediction Firewall Banner */}
      <StatePredictionFirewall />

      {/* Implemented Pilot States Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Active Production Pilot States (4 Jurisdictions)
            </h2>
            <p className="text-xs text-slate-400">
              Full legislative indexing, official gazette intake, and corporate operational footprint mapping.
            </p>
          </div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/50 px-2.5 py-1 rounded-md">
            Level 2 Legislative Intelligence Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ACTIVE_STATES.map((state) => (
            <div
              key={state.code}
              className="p-5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-slate-100">{state.name}</span>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {state.code}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Capital: {state.capital} · {state.assembly}
                    </p>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-950/70 text-emerald-300 border border-emerald-800/40">
                    Active
                  </span>
                </div>

                <p className="text-xs text-slate-300/90 leading-relaxed">
                  {state.description}
                </p>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                  <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800">
                    <span className="text-[11px] text-slate-400 block">Enacted Acts</span>
                    <span className="text-lg font-bold font-mono-num text-slate-100">
                      {state.actsCount}
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800">
                    <span className="text-[11px] text-slate-400 block">Corporate Exposures</span>
                    <span className="text-lg font-bold font-mono-num text-indigo-300">
                      {state.exposuresCount}
                    </span>
                  </div>
                </div>

                {/* Economic Sectors */}
                <div>
                  <span className="text-[11px] text-slate-400 block mb-1">Key Statutory Sectors:</span>
                  <div className="flex flex-wrap gap-1">
                    {state.sectors.map((sec) => (
                      <span
                        key={sec}
                        className="text-[10px] px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60"
                      >
                        {sec}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="text-[11px] text-slate-500">
                  Source: <span className="text-slate-400">{state.officialSource}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                <Link
                  href={`/bills?jurisdiction=state&state=${encodeURIComponent(state.name)}`}
                  className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
                >
                  View {state.actsCount} State Bills →
                </Link>
                <Link
                  href={`/states/${encodeURIComponent(state.name)}`}
                  className="px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors"
                >
                  State Dossier →
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Planned Union Jurisdictions Roadmap */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Planned Expansion States (24 Union Jurisdictions)
            </h2>
            <p className="text-xs text-slate-400">
              Roadmap states scheduled for automated gazette scraping, statutory indexing, and exposure modeling.
            </p>
          </div>
          {/* Zone filter */}
          <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
            {["All", "Northern", "Western", "Southern", "Eastern", "Central", "North-Eastern"].map((z) => (
              <button
                key={z}
                onClick={() => setZoneFilter(z)}
                className={cn(
                  "px-2 py-1 rounded transition-colors",
                  zoneFilter === z
                    ? "bg-slate-800 text-slate-100 font-medium"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                {z}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {filteredPlanned.map((st) => (
            <div
              key={st.name}
              className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between h-24"
            >
              <div>
                <div className="flex items-start justify-between gap-1">
                  <span className="text-xs font-semibold text-slate-300 truncate">{st.name}</span>
                  <span className="text-[9px] font-mono px-1 rounded bg-slate-800 text-slate-400">
                    {st.targetTimeline}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 truncate">{st.capital}</div>
              </div>
              <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/60">
                <span>{st.zone} Zone</span>
                <span className="text-amber-400/80 font-mono">0 Acts</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
