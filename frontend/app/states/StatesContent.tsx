/**
 * app/states/StatesContent.tsx
 * ============================
 * Sub-National Legislative Intelligence Registry (States).
 *
 * Implements:
 * - Editorial-finance registry layout adhering to SEANCE_DESIGN_SYSTEM.md
 * - 4 Implemented Pilot States: Andhra Pradesh (12), Karnataka (11), Kerala (11), Telangana (10)
 * - Total 44 Enacted State Acts, 86 Corporate Exposures
 * - 24 Planned Union Jurisdictions roadmap matrix with zone filters
 * - Dual view modes: Tabular Institutional Comparison & Assembly Dossier Cards
 * - Mandatory State Stock Prediction Firewall notice (State Predictions = 0 strictly enforced)
 * - Deep links to state dossiers and filtered bill registers
 */

"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SearchInput } from "@/components/ui/SearchInput";
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
  const [activeViewMode, setActiveViewMode] = useState<"dossiers" | "table">("dossiers");
  const [stateSearch, setStateSearch] = useState("");
  const [zoneFilter, setZoneFilter] = useState<string>("All");

  const filteredActiveStates = useMemo(() => {
    if (!stateSearch.trim()) return ACTIVE_STATES;
    const q = stateSearch.toLowerCase();
    return ACTIVE_STATES.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.code.toLowerCase().includes(q) ||
        s.capital.toLowerCase().includes(q) ||
        s.sectors.some((sec) => sec.toLowerCase().includes(q))
    );
  }, [stateSearch]);

  const filteredPlanned = useMemo(() => {
    return PLANNED_STATES.filter((s) => {
      const matchesZone = zoneFilter === "All" || s.zone === zoneFilter;
      const matchesQuery =
        !stateSearch.trim() ||
        s.name.toLowerCase().includes(stateSearch.toLowerCase()) ||
        s.capital.toLowerCase().includes(stateSearch.toLowerCase());
      return matchesZone && matchesQuery;
    });
  }, [zoneFilter, stateSearch]);

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] pb-24">
      {/* Editorial Header */}
      <header className="border-b border-[var(--border-default)] bg-[var(--bg-card)]/80 backdrop-blur-md sticky top-14 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="text-xl" aria-hidden="true">🗺</span>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                  Sub-National Legislative Intelligence Registry
                </h1>
                <EpistemicBadge type="FACT" size="sm" />
                <Badge variant="primary" size="xs">
                  Level 2 Intelligence
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1 max-w-3xl leading-relaxed">
                Federated statutory coverage across Indian State Legislative Assemblies. 4 active production pilot jurisdictions (44 acts, 86 corporate exposures) and 24 roadmap union expansion states.
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Link href="/bills?jurisdiction=state">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  Browse 44 State Acts →
                </Button>
              </Link>
              <Link href="/coverage">
                <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-8">
                  System Coverage Audit →
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Invariant Metric Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3" aria-label="Jurisdictional Invariants">
          <div className="p-3.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] shadow-sm">
            <div className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Implemented States</div>
            <div className="text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">4</div>
            <div className="text-[11px] text-emerald-400 mt-0.5 font-medium font-mono">AP, KA, KL, TS</div>
          </div>

          <div className="p-3.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] shadow-sm">
            <div className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Production State Acts</div>
            <div className="text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">44</div>
            <div className="text-[11px] text-[var(--text-faint)] mt-0.5">Enacted & Ingested</div>
          </div>

          <div className="p-3.5 rounded-lg bg-indigo-950/20 border border-indigo-800/30 shadow-sm">
            <div className="text-[11px] font-medium text-indigo-400 uppercase tracking-wider">Corporate Exposures</div>
            <div className="text-2xl font-bold font-mono tabular-nums text-indigo-300 mt-1">86</div>
            <div className="text-[11px] text-indigo-400/80 mt-0.5">Operational Links</div>
          </div>

          <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-800/40 shadow-sm">
            <div className="text-[11px] font-medium text-rose-400 uppercase tracking-wider">State Stock Predictions</div>
            <div className="text-2xl font-bold font-mono tabular-nums text-rose-300 mt-1">0</div>
            <div className="text-[11px] text-rose-400/80 mt-0.5 font-medium">Strict Firewall Invariant</div>
          </div>

          <div className="p-3.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] shadow-sm">
            <div className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Planned States</div>
            <div className="text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">24</div>
            <div className="text-[11px] text-[var(--text-faint)] mt-0.5 font-mono">Union Expansion</div>
          </div>
        </div>

        {/* Mandatory State Stock Prediction Firewall Banner */}
        <StatePredictionFirewall />

        {/* Active Production Pilot States */}
        <section className="space-y-4" aria-labelledby="active-states-heading">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--border-subtle)] pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 id="active-states-heading" className="text-sm sm:text-base font-bold text-[var(--text-primary)]">
                  Active Production Pilot States (4 Jurisdictions)
                </h2>
                <Badge variant="primary" size="xs">
                  Level 2 Intelligence
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Full legislative indexing, official gazette intake, and corporate operational footprint mapping.
              </p>
            </div>

            {/* View Mode Toggle & Search */}
            <div className="flex items-center gap-2.5 flex-wrap">
              <SearchInput
                placeholder="Search state, capital, sector..."
                value={stateSearch}
                onChange={(v) => setStateSearch(v)}
                className="w-48 h-8 text-xs"
              />
              <div className="inline-flex rounded-lg border border-[var(--border-strong)] bg-[var(--bg-base)] p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setActiveViewMode("dossiers")}
                  className={cn(
                    "px-2.5 py-1 rounded text-[11px] font-medium transition-colors",
                    activeViewMode === "dossiers"
                      ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  )}
                >
                  Dossier Cards
                </button>
                <button
                  type="button"
                  onClick={() => setActiveViewMode("table")}
                  className={cn(
                    "px-2.5 py-1 rounded text-[11px] font-medium transition-colors",
                    activeViewMode === "table"
                      ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  )}
                >
                  Tabular Registry
                </button>
              </div>
            </div>
          </div>

          {/* Dossiers Grid View */}
          {activeViewMode === "dossiers" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredActiveStates.map((state) => (
                <div
                  key={state.code}
                  className="p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-default)] hover:border-[var(--border-strong)] transition-colors flex flex-col justify-between space-y-4 shadow-sm"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-base font-bold text-[var(--text-primary)]">{state.name}</span>
                          <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-base)] text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                            {state.code}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--text-muted)] mt-0.5">
                          Capital: <span className="text-[var(--text-secondary)]">{state.capital}</span> · {state.assembly}
                        </p>
                      </div>
                      <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
                        Active
                      </span>
                    </div>

                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                      {state.description}
                    </p>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[var(--border-subtle)]">
                      <div className="p-2.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                        <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">Enacted Acts</span>
                        <span className="text-lg font-bold font-mono tabular-nums text-[var(--text-primary)]">
                          {state.actsCount}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                        <span className="text-[10px] uppercase font-semibold text-indigo-400 block">Corporate Exposures</span>
                        <span className="text-lg font-bold font-mono tabular-nums text-indigo-300">
                          {state.exposuresCount}
                        </span>
                      </div>
                    </div>

                    {/* Economic Sectors */}
                    <div>
                      <span className="text-[11px] text-[var(--text-muted)] block mb-1">Key Statutory Sectors:</span>
                      <div className="flex flex-wrap gap-1">
                        {state.sectors.map((sec) => (
                          <span
                            key={sec}
                            className="text-[10px] px-2 py-0.5 rounded bg-[var(--bg-base)] text-[var(--text-secondary)] border border-[var(--border-subtle)]"
                          >
                            {sec}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="text-[11px] text-[var(--text-faint)]">
                      Gazette Source: <span className="text-[var(--text-muted)]">{state.officialSource}</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
                    <Link
                      href={`/bills?jurisdiction=state&state=${encodeURIComponent(state.name)}`}
                      className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      View {state.actsCount} State Bills →
                    </Link>
                    <Link
                      href={`/states/${encodeURIComponent(state.name)}`}
                      className="px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors"
                    >
                      State Dossier →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tabular Registry View */}
          {activeViewMode === "table" && (
            <div className="rounded-xl border border-[var(--border-default)] overflow-hidden bg-[var(--bg-card)]">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]/60 text-[var(--text-muted)]">
                    <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">State / Code</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Capital & Assembly</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Acts</th>
                    <th className="py-2.5 px-3 text-right font-semibold uppercase tracking-wider text-[11px]">Exposures</th>
                    <th className="py-2.5 px-3 font-semibold uppercase tracking-wider text-[11px]">Key Sectors</th>
                    <th className="py-2.5 px-4 text-right font-semibold uppercase tracking-wider text-[11px]">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)] text-[var(--text-secondary)]">
                  {filteredActiveStates.map((st) => (
                    <tr key={st.code} className="hover:bg-[var(--bg-base)]/80 transition-colors">
                      <td className="py-3 px-4 font-medium">
                        <Link href={`/states/${encodeURIComponent(st.name)}`} className="text-[var(--text-primary)] hover:text-indigo-400 font-semibold transition-colors">
                          {st.name}
                        </Link>
                        <span className="block text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                          Code: {st.code} · Level 2 Active
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-[var(--text-primary)] block">{st.capital}</span>
                        <span className="text-[10px] text-[var(--text-muted)] block truncate max-w-xs">{st.assembly}</span>
                      </td>
                      <td className="py-3 px-3 text-right font-mono tabular-nums font-semibold text-[var(--text-primary)]">
                        {st.actsCount}
                      </td>
                      <td className="py-3 px-3 text-right font-mono tabular-nums font-semibold text-indigo-300">
                        {st.exposuresCount}
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex flex-wrap gap-1 max-w-sm">
                          {st.sectors.map((sec) => (
                            <span key={sec} className="text-[10px] px-1.5 py-0.2 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
                              {sec}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link href={`/bills?jurisdiction=state&state=${encodeURIComponent(st.name)}`}>
                            <Button variant="outline" size="xs" className="border-[var(--border-default)] hover:bg-[var(--bg-elevated)] text-[11px] h-7">
                              Bills →
                            </Button>
                          </Link>
                          <Link href={`/states/${encodeURIComponent(st.name)}`}>
                            <Button variant="primary" size="xs" className="text-[11px] h-7 font-semibold">
                              Dossier →
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Planned Union Jurisdictions Roadmap */}
        <section className="space-y-4 pt-4 border-t border-[var(--border-default)]" aria-labelledby="planned-states-heading">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 id="planned-states-heading" className="text-sm sm:text-base font-bold text-[var(--text-primary)]">
                  Planned Expansion States (24 Union Jurisdictions)
                </h2>
                <Badge variant="default" size="xs">
                  Roadmap Pipeline
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Roadmap states scheduled for automated gazette scraping, statutory indexing, and exposure modeling.
              </p>
            </div>

            {/* Zone filter */}
            <div className="flex items-center gap-1 bg-[var(--bg-card)] p-1 rounded-lg border border-[var(--border-default)] text-xs flex-wrap">
              {["All", "Northern", "Western", "Southern", "Eastern", "Central", "North-Eastern"].map((z) => (
                <button
                  key={z}
                  type="button"
                  onClick={() => setZoneFilter(z)}
                  className={cn(
                    "px-2 py-0.5 rounded text-[11px] transition-colors",
                    zoneFilter === z
                      ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] font-medium shadow-sm"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
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
                className="p-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] flex flex-col justify-between h-24 hover:border-[var(--border-strong)] transition-colors shadow-sm"
              >
                <div>
                  <div className="flex items-start justify-between gap-1">
                    <span className="text-xs font-semibold text-[var(--text-primary)] truncate">{st.name}</span>
                    <span className="text-[9px] font-mono px-1 rounded bg-[var(--bg-base)] text-[var(--text-muted)] border border-[var(--border-subtle)]">
                      {st.targetTimeline}
                    </span>
                  </div>
                  <div className="text-[10px] text-[var(--text-faint)] mt-0.5 truncate">{st.capital}</div>
                </div>
                <div className="flex items-center justify-between text-[10px] text-[var(--text-faint)] pt-1 border-t border-[var(--border-subtle)]">
                  <span>{st.zone} Zone</span>
                  <span className="text-amber-400 font-mono">0 Acts</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
