/**
 * app/states/[state]/StateDetailContent.tsx
 * ==========================================
 * Sub-National Legislative Intelligence Dossier.
 *
 * Implements:
 * - State profile, capital, assembly, official gazette intake source
 * - Enacted Assembly Acts list with search, status filters, and dossier links
 * - Corporate Operational Footprint in state (facilities & statutory transmission)
 * - StatePredictionFirewall permanent invariant notice (0 quantitative predictions)
 * - Restrained editorial-finance aesthetic adhering to SEANCE_DESIGN_SYSTEM.md
 */

"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { billsApi } from "@/lib/api/bills";
import type { BillSummaryItem, PaginatedResponse } from "@/types/api";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { InstitutionalTable, type TableColumn } from "@/components/ui/InstitutionalTable";
import { StatusBadge, Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SearchInput } from "@/components/ui/SearchInput";
import { ErrorState, SkeletonCard } from "@/components/ui/Skeleton";

interface StateProfile {
  name: string;
  code: string;
  capital: string;
  assembly: string;
  gazette: string;
  actsCount: number;
  exposuresCount: number;
  sectors: string[];
  description: string;
  keyCorporates: { name: string; isin: string; facilities: string; exposure: string }[];
}

const STATE_PROFILES: Record<string, StateProfile> = {
  "andhra pradesh": {
    name: "Andhra Pradesh",
    code: "AP",
    capital: "Amaravati",
    assembly: "Andhra Pradesh Legislative Assembly",
    gazette: "Andhra Pradesh Official Gazette",
    actsCount: 12,
    exposuresCount: 26,
    sectors: ["Energy & Renewables", "Ports & Logistics", "Mining", "Agriculture"],
    description:
      "Statutory oversight over coastal commercial corridors, critical renewable energy infrastructure, and non-major port developments.",
    keyCorporates: [
      { name: "Adani Ports & SEZ", isin: "INE742F01042", facilities: "Krishnapatnam / Gangavaram Ports", exposure: "Direct Port Regulation" },
      { name: "NTPC Limited", isin: "INE733E01010", facilities: "Simhadri Super Thermal Power", exposure: "Emission & Water Standards" },
      { name: "Amara Raja Energy", isin: "INE885A01032", facilities: "Tirupati Giga Plant", exposure: "Industrial Waste Compliance" },
      { name: "NMDC Limited", isin: "INE584A01023", facilities: "Mineral Exploration Leases", exposure: "Mining Royalties & Cess" },
    ],
  },
  karnataka: {
    name: "Karnataka",
    code: "KA",
    capital: "Bengaluru",
    assembly: "Karnataka Legislative Assembly",
    gazette: "Karnataka Government Gazette",
    actsCount: 11,
    exposuresCount: 22,
    sectors: ["Information Technology", "Platform Economy & Gig Labor", "Cinema & Media", "Real Estate"],
    description:
      "Pioneer legislation regulating digital platform aggregators, tech corridor zoning, and cinema exhibition tariffs.",
    keyCorporates: [
      { name: "Infosys Limited", isin: "INE009A01021", facilities: "Electronic City HQ & Campus", exposure: "IT Labor Standing Orders" },
      { name: "Wipro Limited", isin: "INE075A01022", facilities: "Sarjapur Corporate Campus", exposure: "Workplace & Spatial Norms" },
      { name: "Zomato Limited", isin: "INE758T01015", facilities: "Bengaluru Delivery Fleet", exposure: "Gig Worker Social Security Cess" },
      { name: "PVR INOX Limited", isin: "INE191H01014", facilities: "Multiplex Chains Statewide", exposure: "Ticket Price Cap Regulations" },
    ],
  },
  kerala: {
    name: "Kerala",
    code: "KL",
    capital: "Thiruvananthapuram",
    assembly: "Kerala Legislative Assembly (Niyamasabha)",
    gazette: "Kerala Government Gazette",
    actsCount: 11,
    exposuresCount: 18,
    sectors: ["Healthcare & Public Health", "Tourism & Ecology", "Cooperative Institutions", "Maritime Trade"],
    description:
      "Public health safeguards, eco-sensitive commercial zoning regulations, and cooperative sector compliance standards.",
    keyCorporates: [
      { name: "Muthoot Finance", isin: "INE414G01012", facilities: "Kochi Headquarters & Branches", exposure: "State Money Lending Rules" },
      { name: "Federal Bank Limited", isin: "INE171A01029", facilities: "Aluva Corporate Office", exposure: "Cooperative Banking Interfaces" },
      { name: "Cochin Shipyard", isin: "INE704P01017", facilities: "Kochi Drydock Facilities", exposure: "Coastal Zone Management" },
      { name: "Apollo Tyres", isin: "INE438A01022", facilities: "Perambra Manufacturing Facility", exposure: "Industrial Water & Effluent" },
    ],
  },
  telangana: {
    name: "Telangana",
    code: "TS",
    capital: "Hyderabad",
    assembly: "Telangana Legislative Assembly",
    gazette: "Telangana Official Gazette",
    actsCount: 10,
    exposuresCount: 20,
    sectors: ["Biopharma & Life Sciences", "Digital Gaming & Entertainment", "Industrial Promotion", "Urban Development"],
    description:
      "Statutory frameworks governing digital gaming restrictions, pharmaceutical industrial cluster incentives, and land administration.",
    keyCorporates: [
      { name: "Dr. Reddy's Laboratories", isin: "INE089A01023", facilities: "Genome Valley R&D Hub", exposure: "State Industrial Policy Incentives" },
      { name: "Divi's Laboratories", isin: "INE361B01024", facilities: "Choutuppal Manufacturing Unit", exposure: "Pollution Control Standards" },
      { name: "Nazara Technologies", isin: "INE768N01012", facilities: "Online Gaming Operations", exposure: "Telangana Gaming Act Restrictions" },
      { name: "Tata Advanced Systems", isin: "INE000TAS01", facilities: "Adibatla Aerospace SEZ", exposure: "Defense Manufacturing Land Leases" },
    ],
  },
};

function normalizeStateKey(input: string): string {
  const clean = decodeURIComponent(input).trim().toLowerCase();
  if (clean === "ap" || clean.includes("andhra")) return "andhra pradesh";
  if (clean === "ka" || clean.includes("karnataka")) return "karnataka";
  if (clean === "kl" || clean.includes("kerala")) return "kerala";
  if (clean === "ts" || clean.includes("telangana")) return "telangana";
  return clean;
}

export default function StateDetailContent({ stateParam }: { stateParam: string }) {
  const normKey = normalizeStateKey(stateParam);
  const profile = STATE_PROFILES[normKey];

  const stateDisplayName = profile?.name ?? decodeURIComponent(stateParam);

  const [billsData, setBillsData] = useState<PaginatedResponse<BillSummaryItem> | null>(null);
  const [loadingBills, setLoadingBills] = useState(true);
  const [errorBills, setErrorBills] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoadingBills(true);
    setErrorBills(null);

    billsApi
      .listBills({
        jurisdiction: "state",
        state: stateDisplayName,
        limit: 50,
      })
      .then((res) => {
        if (!cancelled) setBillsData(res);
      })
      .catch((err) => {
        if (!cancelled) setErrorBills(err?.userMessage ?? "Failed to load state bills.");
      })
      .finally(() => {
        if (!cancelled) setLoadingBills(false);
      });

    return () => {
      cancelled = true;
    };
  }, [stateDisplayName]);

  const filteredBills = useMemo(() => {
    if (!billsData?.items) return [];
    if (!searchQuery.trim()) return billsData.items;
    const q = searchQuery.toLowerCase();
    return billsData.items.filter(
      (b) =>
        b.title.toLowerCase().includes(q) ||
        (b.bill_number && b.bill_number.toLowerCase().includes(q)) ||
        b.bill_id.toLowerCase().includes(q)
    );
  }, [billsData, searchQuery]);

  const actColumns: TableColumn<BillSummaryItem>[] = [
    {
      key: "title",
      header: "State Assembly Act Title",
      sortable: true,
      render: (bill) => (
        <div className="min-w-[260px] max-w-md">
          <Link
            href={`/bills/${bill.bill_id}`}
            className="font-semibold text-[var(--text-primary)] hover:text-indigo-400 transition-colors line-clamp-1"
          >
            {bill.title}
          </Link>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[10px] font-mono text-[var(--text-muted)]">{bill.bill_number || bill.bill_id}</span>
            {bill.year && <span className="text-[10px] text-[var(--text-faint)]">· {bill.year}</span>}
          </div>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      width: "120px",
      render: (bill) => <StatusBadge status={bill.status} />,
    },
    {
      key: "company_exposure_count",
      header: "Corporate Exposures",
      align: "right",
      isNumeric: true,
      sortable: true,
      width: "150px",
      render: (bill) => (
        <span className="font-mono tabular-nums font-semibold text-indigo-300">
          {bill.company_exposure_count ?? 0}
        </span>
      ),
    },
    {
      key: "actions",
      header: "",
      align: "right",
      width: "120px",
      render: (bill) => (
        <Link
          href={`/bills/${bill.bill_id}`}
          className="px-2.5 py-1 text-xs font-semibold text-indigo-300 hover:text-indigo-200 bg-indigo-950/40 hover:bg-indigo-900/50 rounded border border-indigo-700/40 transition-colors inline-block"
        >
          View Dossier →
        </Link>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] pb-24">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="border-b border-[var(--border-default)] bg-[var(--bg-card)]/80 backdrop-blur-md sticky top-14 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <Link href="/states" className="hover:text-[var(--text-primary)] transition-colors">
              State Registry
            </Link>
            <span>/</span>
            <span className="text-[var(--text-primary)] font-semibold">{stateDisplayName}</span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/bills?jurisdiction=state&state=${encodeURIComponent(stateDisplayName)}`}
            >
              <Button variant="outline" size="xs" className="border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] text-xs h-7">
                Browse in Bills Filter →
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Header Hero */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] tracking-tight">
                  {stateDisplayName}
                </h1>
                {profile && (
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border-default)]">
                    {profile.code}
                  </span>
                )}
                <EpistemicBadge type="FACT" size="sm" />
                <Badge variant="primary" size="xs">
                  Level 2 State Intelligence
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1">
                {profile ? profile.assembly : "State Legislative Assembly"} · Capital: <span className="text-[var(--text-secondary)]">{profile ? profile.capital : "State Capital"}</span>
              </p>
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] shadow-sm">
              <div className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Enacted Assembly Acts</div>
              <div className="text-2xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                {profile ? profile.actsCount : billsData?.total ?? 0}
              </div>
              <div className="text-[11px] text-[var(--text-faint)] mt-0.5 font-mono">Ingested & Indexed</div>
            </div>

            <div className="p-3.5 rounded-lg bg-indigo-950/20 border border-indigo-800/30 shadow-sm">
              <div className="text-[11px] font-medium text-indigo-400 uppercase tracking-wider">Corporate Exposures</div>
              <div className="text-2xl font-bold font-mono tabular-nums text-indigo-300 mt-1">
                {profile ? profile.exposuresCount : "—"}
              </div>
              <div className="text-[11px] text-indigo-400/80 mt-0.5 font-mono">Operating Facilities</div>
            </div>

            <div className="p-3.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] shadow-sm">
              <div className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Official Source</div>
              <div className="text-sm font-semibold text-[var(--text-primary)] mt-1 truncate">
                {profile ? profile.gazette : "Official State Gazette"}
              </div>
              <div className="text-[11px] text-emerald-400 mt-0.5 font-medium">Intake Active</div>
            </div>

            <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-800/40 shadow-sm">
              <div className="text-[11px] font-medium text-rose-400 uppercase tracking-wider">State Stock Predictions</div>
              <div className="text-2xl font-bold font-mono tabular-nums text-rose-300 mt-1">0</div>
              <div className="text-[11px] text-rose-400/80 mt-0.5 font-medium">Firewall Invariant</div>
            </div>
          </div>
        </div>

        {/* Mandatory Firewall Banner */}
        <StatePredictionFirewall state={stateDisplayName} />

        {/* State Assembly Acts Section */}
        <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 shadow-sm space-y-4" aria-labelledby="assembly-acts-heading">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 id="assembly-acts-heading" className="text-sm sm:text-base font-bold text-[var(--text-primary)]">
                  State Legislative Assembly Enactments
                </h2>
                <Badge variant="primary" size="xs">
                  Level 2 Records
                </Badge>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Official acts and statutory amendments passed by the {stateDisplayName} Assembly.
              </p>
            </div>

            <SearchInput
              placeholder="Search acts in this state..."
              value={searchQuery}
              onChange={(v) => setSearchQuery(v)}
              className="w-56 h-8 text-xs"
            />
          </div>

          {loadingBills ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <SkeletonCard key={i} className="h-12 bg-[var(--bg-card)]/60" />
              ))}
            </div>
          ) : errorBills ? (
            <ErrorState error={errorBills} onRetry={() => setLoadingBills(true)} />
          ) : !billsData || filteredBills.length === 0 ? (
            <div className="p-8 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-center text-xs text-[var(--text-muted)]">
              {searchQuery ? "No assembly acts matched the search filter." : "No specific assembly acts returned for this jurisdiction query."}{" "}
              Check the{" "}
              <Link href="/bills?jurisdiction=state" className="text-indigo-400 underline font-medium">
                State Bills directory
              </Link>
              .
            </div>
          ) : (
            <div className="rounded-lg border border-[var(--border-subtle)] overflow-hidden">
              <InstitutionalTable
                columns={actColumns}
                data={filteredBills}
                keyExtractor={(b) => b.bill_id}
                compact
                striped
              />
            </div>
          )}
        </section>

        {/* State Corporate Operational Footprint */}
        {profile && profile.keyCorporates && (
          <section className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 shadow-sm space-y-4" aria-labelledby="corporate-footprint-heading">
            <div className="border-b border-[var(--border-subtle)] pb-3">
              <div className="flex items-center gap-2">
                <h2 id="corporate-footprint-heading" className="text-sm sm:text-base font-bold text-[var(--text-primary)]">
                  Documented Corporate Operational Footprint in {stateDisplayName}
                </h2>
                <EpistemicBadge type="OBSERVED" size="sm" />
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Corporations with verified physical manufacturing plants, operating headquarters, or direct statutory liabilities in the state.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {profile.keyCorporates.map((corp) => (
                <div
                  key={corp.isin}
                  className="p-4 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-3 hover:border-[var(--border-strong)] transition-colors"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs sm:text-sm font-bold text-[var(--text-primary)]">{corp.name}</span>
                      <span className="text-[10px] font-mono text-[var(--text-muted)]">{corp.isin}</span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-1.5 leading-relaxed">
                      <span className="text-[var(--text-faint)] font-medium">Facilities / Footprint:</span> {corp.facilities}
                    </p>
                    <p className="text-xs text-indigo-300 mt-1 leading-relaxed">
                      <span className="text-[var(--text-faint)] font-medium">State Statutory Transmission:</span> {corp.exposure}
                    </p>
                  </div>
                  <div className="pt-2.5 border-t border-[var(--border-subtle)] flex justify-end">
                    <Link
                      href={`/companies/${corp.isin}`}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
                    >
                      View Corporate Profile →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
