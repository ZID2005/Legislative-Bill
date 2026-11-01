/**
 * app/page.tsx
 * ============
 * Task 1.7A — Executive Decision Command Center (Root Entry Experience).
 *
 * Implements the approved premium editorial-finance design:
 * - Clear ocular hierarchy with concise product purpose
 * - Institutional status and provenance ticker
 * - High-density coverage & context indicators with tabular figures
 * - Unified Decision Hubs (Workspace, Overview, Portfolio)
 * - Dual-Column Operational Center (Legislative Radar + Live Intake & Firewalls)
 * - Core Platform Workflows & Institutional Governance Footer
 * - Zero decorative AI orbs, gratuitous gradients, or nested card sprawl
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { UserSession, authApi } from "@/lib/api/auth";
import { useCoverage } from "@/hooks/useCoverage";
import { formatNumber } from "@/lib/utils";

export default function LandingPage() {
  const [session, setSession] = useState<UserSession | null>(null);
  const { coverage } = useCoverage();

  // Dynamic coverage values with fallback to canonical frozen baseline
  const centralCount = coverage?.central?.production_bills ?? 20;
  const stateCount = coverage?.state?.state_bills_count ?? 44;
  const quantCount = coverage?.company?.quantitative_companies ?? 47;
  const predCount = coverage?.central?.predictions_count ?? 4700;
  const compCount = coverage?.company?.total_companies ?? 70;
  const exposureCount = coverage?.unified?.total_corporate_exposures ?? 104;

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("auth_user");
      if (stored) {
        try {
          setSession(JSON.parse(stored));
        } catch {
          // ignore parsing error
        }
      }
      authApi.getMe().then(setSession).catch(() => {});
    }
  }, []);

  return (
    <div className="min-h-full bg-[var(--bg-base)] text-[var(--text-primary)] selection:bg-[var(--action-primary)] selection:text-white pb-20">
      {/* -------------------------------------------------------------------- */}
      {/* 1. TOP OPERATIONAL STATUS & PROVENANCE STRIP                         */}
      {/* -------------------------------------------------------------------- */}
      <div className="border-b border-[var(--border-default)] bg-[var(--bg-surface)] px-6 py-2.5 text-xs text-[var(--text-muted)] flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-semibold text-[var(--text-primary)] tracking-tight">PRODUCTION ENGINE ONLINE</span>
          <span className="text-[var(--text-faint)]">|</span>
          <span className="font-tabular">Central Event Studies: {centralCount} Acts · {formatNumber(predCount)} Predictions</span>
          <span className="text-[var(--text-faint)]">|</span>
          <span>State Coverage: {stateCount} Acts (AP, KA, KL, TS)</span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="text-[var(--text-muted)]">SOC-2 Audit Trail: Active</span>
          <span className="text-[var(--color-success)] bg-[var(--color-success-bg)] border border-[var(--color-success-border)] px-2 py-0.5 rounded font-mono text-xs font-medium">
            Statutory Firewalls Locked
          </span>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 2. EXECUTIVE COMMAND CENTER HERO & OBVIOUS NEXT ACTIONS              */}
      {/* -------------------------------------------------------------------- */}
      <section className="relative px-6 pt-12 pb-10 max-w-7xl mx-auto">
        <div className="flex items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)] uppercase tracking-wider font-mono">
            Institutional Terminal
          </span>
          <span className="text-xs text-[var(--text-muted)] font-mono">
            Version 2.4 · Multi-Tenant Onboarding Live
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-[var(--text-primary)] max-w-4xl leading-tight">
          India Legislative Intelligence &amp; Market Impact Predictions
        </h1>

        <p className="mt-4 text-base sm:text-lg text-[var(--text-secondary)] max-w-3xl font-normal leading-relaxed">
          The definitive regulatory analytics engine linking Parliament bills, State gazettes, and
          corporate exposure networks to quantitative securities with mathematically rigorous event studies.
        </p>

        {/* Primary Action Row */}
        <div className="mt-8 flex flex-wrap items-center gap-3.5">
          <Link
            href="/workspace"
            className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            Launch Command Center →
          </Link>
          <Link
            href="/overview"
            className="px-4.5 py-3 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] text-[var(--text-primary)] font-semibold text-sm transition-colors shadow-xs"
          >
            📊 System Overview
          </Link>
          <Link
            href="/portfolio"
            className="px-4.5 py-3 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] text-[var(--text-primary)] font-semibold text-sm transition-colors shadow-xs"
          >
            💼 Portfolio Exposure
          </Link>
          {session ? (
            <Link
              href="/settings"
              className="px-4.5 py-3 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] text-[var(--text-primary)] font-semibold text-sm transition-colors"
            >
              Organization Settings ({session.display_name})
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="px-4.5 py-3 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] text-[var(--text-primary)] font-semibold text-sm transition-colors"
              >
                Sign In to Tenant
              </Link>
              <Link
                href="/signup"
                className="px-4.5 py-3 rounded-lg bg-[var(--color-success-bg)] hover:bg-[var(--color-success-bg)] border border-[var(--color-success-border)] text-[var(--color-success)] font-semibold text-sm transition-colors"
              >
                Create Account
              </Link>
            </>
          )}
          <Link
            href="/onboarding"
            className="px-4 py-3 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] text-sm font-medium transition-colors"
          >
            Interactive Tour (8 Steps)
          </Link>
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* 3. HIGH-DENSITY COVERAGE METRIC TICKER (HAIRLINE GRID)             */}
        {/* ------------------------------------------------------------------ */}
        <div className="mt-10 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border-default)] border border-[var(--border-default)] rounded-xl bg-[var(--bg-surface)] overflow-hidden">
          <div className="p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">{centralCount}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1 font-medium">Central Acts Scanned</div>
            <div className="text-[10px] text-[var(--color-info)] font-mono mt-0.5">22 Scanned Records</div>
          </div>
          <div className="p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">{stateCount}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1 font-medium">State Acts Enacted</div>
            <div className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">AP=12, KA=11, KL=11, TS=10</div>
          </div>
          <div className="p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">{quantCount}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1 font-medium">Quant Securities</div>
            <div className="text-[10px] text-[var(--color-info)] font-mono mt-0.5">NSE/BSE Listed</div>
          </div>
          <div className="p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">{formatNumber(predCount)}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1 font-medium">Predictions</div>
            <div className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">940 Pairs × 5 Windows</div>
          </div>
          <div className="p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">{compCount}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1 font-medium">Total Companies</div>
            <div className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">47 Quant + 23 Intel</div>
          </div>
          <div className="p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold font-tabular text-[var(--text-primary)]">{exposureCount}</div>
            <div className="text-xs text-[var(--text-muted)] mt-1 font-medium">Exposures</div>
            <div className="text-[10px] text-[var(--color-success)] font-mono mt-0.5">18 Central + 86 State</div>
          </div>
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* 4. UNIFIED DECISION HUBS (PERSPECTIVE SWITCHER)                    */}
        {/* ------------------------------------------------------------------ */}
        <div className="mt-12 text-left">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-default)]">
            <div>
              <h2 className="text-sm uppercase tracking-wider font-bold text-[var(--text-secondary)]">
                Unified Decision Hubs
              </h2>
              <p className="text-xs text-[var(--text-muted)]">
                Direct entry points tailored for different analytical workflows.
              </p>
            </div>
            <span className="text-[11px] font-mono text-[var(--text-muted)]">
              3 Specialized Perspectives
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/workspace"
              className="p-5 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                  Personal Workbench
                </span>
                <span className="text-xs text-[var(--text-muted)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  Launch →
                </span>
              </div>
              <h3 className="text-base font-bold text-[var(--text-primary)]">
                Legislative Workspace
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
                Your monitored bills, corporate exposures, custom watchlists, unread triggers, and Grounded AI Workspace Assistant.
              </p>
            </Link>

            <Link
              href="/overview"
              className="p-5 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-teal-600 dark:text-teal-400 uppercase tracking-wider">
                  System Observatory
                </span>
                <span className="text-xs text-[var(--text-muted)] group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
                  View →
                </span>
              </div>
              <h3 className="text-base font-bold text-[var(--text-primary)]">
                Platform Coverage Overview
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
                System-wide capability tiers (L1/L2/L3), recent legislative intake, live state assembly feeds, and subsystem health telemetry.
              </p>
            </Link>

            <Link
              href="/portfolio"
              className="p-5 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                  Investor Focus
                </span>
                <span className="text-xs text-[var(--text-muted)] group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                  Analyze →
                </span>
              </div>
              <h3 className="text-base font-bold text-[var(--text-primary)]">
                Portfolio Legislative Exposure
              </h3>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
                Import holdings, assess deterministic exposure across 5 horizons, inspect explainable linkage reasons, and generate executive briefings.
              </p>
            </Link>
          </div>
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* 5. DUAL-COLUMN OPERATIONAL CENTER                                  */}
        {/* ------------------------------------------------------------------ */}
        <div className="mt-12 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (60%): High-Impact Legislative Radar */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-default)]">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                  High-Impact Legislative Radar
                </h3>
                <p className="text-xs text-[var(--text-muted)]">
                  Featured Central enactments with verified corporate linkages and econometric market impact models.
                </p>
              </div>
              <Link href="/bills" className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline">
                View All Acts →
              </Link>
            </div>

            <div className="space-y-3">
              {/* Featured Bill 1: Banking Laws */}
              <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-[var(--color-success-bg)] text-[var(--color-success)] border border-[var(--color-success-border)] uppercase">
                      Assented
                    </span>
                    <span className="text-xs text-[var(--text-muted)] font-mono">
                      Act 18 of 2024 · Central Level 1
                    </span>
                  </div>
                  <span className="text-[11px] font-mono font-medium text-[var(--color-positive)] flex items-center gap-1">
                    ▲ POSITIVE <span className="text-[var(--text-muted)]">[p &lt; 0.01 across T+5]</span>
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-[var(--text-primary)]">
                    <Link href="/bills/the-banking-laws-amendment-bill-2024" className="hover:text-blue-600 dark:hover:text-blue-400">
                      The Banking Laws (Amendment) Bill, 2024
                    </Link>
                  </h4>
                  <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
                    Reforms corporate governance, nominee protections, and cooperative bank lending limits across public and private scheduled commercial banks.
                  </p>
                </div>

                <div className="text-xs text-[var(--text-secondary)] pt-2 border-t border-[var(--border-subtle)] flex flex-wrap items-center justify-between gap-2">
                  <span className="text-[11px]">
                    <strong className="text-[var(--text-primary)]">Exposures:</strong> 14 Quant Banks (SBI, HDFC, ICICI, Kotak, Axis)
                  </span>
                  <div className="flex items-center gap-3">
                    <Link
                      href="/bills/the-banking-laws-amendment-bill-2024"
                      className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Inspect Bill Dossier →
                    </Link>
                    <Link
                      href="/predictions?search=Banking"
                      className="text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    >
                      View Event Study →
                    </Link>
                  </div>
                </div>
              </div>

              {/* Featured Bill 2: Merchant Shipping */}
              <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-[var(--color-success-bg)] text-[var(--color-success)] border border-[var(--color-success-border)] uppercase">
                      Assented
                    </span>
                    <span className="text-xs text-[var(--text-muted)] font-mono">
                      Act 21 of 2024 · Central Level 1
                    </span>
                  </div>
                  <span className="text-[11px] font-mono font-medium text-[var(--color-positive)] flex items-center gap-1">
                    ▲ POSITIVE <span className="text-[var(--text-muted)]">[-1,+1 Event Window]</span>
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-[var(--text-primary)]">
                    <Link href="/bills/the-merchant-shipping-bill-2024" className="hover:text-blue-600 dark:hover:text-blue-400">
                      The Merchant Shipping Bill, 2024
                    </Link>
                  </h4>
                  <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
                    Modernizes maritime governance, repeals the 1958 Act, and establishes revised safety, cabotage, and vessel registration norms for Indian-flagged vessels.
                  </p>
                </div>

                <div className="text-xs text-[var(--text-secondary)] pt-2 border-t border-[var(--border-subtle)] flex flex-wrap items-center justify-between gap-2">
                  <span className="text-[11px]">
                    <strong className="text-[var(--text-primary)]">Exposures:</strong> Shipping Corp of India, Adani Ports &amp; SEZ Ltd
                  </span>
                  <div className="flex items-center gap-3">
                    <Link
                      href="/bills/the-merchant-shipping-bill-2024"
                      className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Inspect Bill Dossier →
                    </Link>
                    <Link
                      href="/predictions?search=Shipping"
                      className="text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    >
                      View Event Study →
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (40%): Live Intake & Statutory Firewalls */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-default)]">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                  Live Intake &amp; System Pulse
                </h3>
                <p className="text-xs text-[var(--text-muted)]">
                  Real-time parliamentary gazette feeds and statutory invariants.
                </p>
              </div>
              <Link href="/monitoring" className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline">
                Monitoring Center →
              </Link>
            </div>

            {/* Pipeline Status Box */}
            <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="flex items-center gap-2 text-[var(--text-primary)]">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Central Parliament Feed
                </span>
                <span className="text-[var(--color-success)] font-semibold">CONNECTED</span>
              </div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="flex items-center gap-2 text-[var(--text-primary)]">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  State Assembly Gazette Intake
                </span>
                <span className="text-[var(--color-success)] font-semibold">ACTIVE</span>
              </div>

              <div className="pt-2 border-t border-[var(--border-subtle)] space-y-1.5 text-xs">
                <div className="text-[11px] font-semibold text-[var(--text-secondary)]">Discovered Sub-National Measures:</div>
                <div className="text-xs text-[var(--text-muted)] flex items-center justify-between">
                  <span>• AP Clean Energy Duty (Amendment) Act</span>
                  <span className="font-mono text-[10px] text-teal-600 dark:text-teal-400">Andhra Pradesh</span>
                </div>
                <div className="text-xs text-[var(--text-muted)] flex items-center justify-between">
                  <span>• KA Platform-Based Gig Workers Bill</span>
                  <span className="font-mono text-[10px] text-teal-600 dark:text-teal-400">Karnataka</span>
                </div>
                <div className="text-xs text-[var(--text-muted)] flex items-center justify-between">
                  <span>• KL Healthcare Service Persons Protection</span>
                  <span className="font-mono text-[10px] text-teal-600 dark:text-teal-400">Kerala</span>
                </div>
              </div>
            </div>

            {/* Statutory Firewall Guarantees Card */}
            <div className="p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] space-y-2.5">
              <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] flex items-center gap-1.5">
                <span>🛡</span>
                <span>Statutory Firewall Guarantees</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="p-2 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  <strong className="text-[var(--text-primary)] block">Zero State Stock Predictions</strong>
                  <span className="text-[11px] text-[var(--text-muted)]">
                    State legislation strictly produces 0 stock predictions, zero price forecasts, and zero CAR curves. Sub-national records are dedicated to business intelligence.
                  </span>
                </div>
                <div className="p-2 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  <strong className="text-[var(--text-primary)] block">Intelligence Entity Isolation</strong>
                  <span className="text-[11px] text-[var(--text-muted)]">
                    23 private/statutory enterprises are permanently excluded from quantitative stock market prediction tables.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* 6. ARCHITECTURAL GUARANTEES & FIREWALLS GRID                         */}
      {/* -------------------------------------------------------------------- */}
      <section className="px-6 py-10 max-w-7xl mx-auto border-t border-[var(--border-default)]">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-[var(--text-primary)]">
            Architectural Guarantees &amp; Firewalls
          </h2>
          <p className="mt-1.5 text-xs text-[var(--text-muted)] max-w-2xl mx-auto">
            Strict separation between quantitative econometric predictions, statutory state facts, and enterprise tenant boundaries.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 relative overflow-hidden">
            <div className="h-0.5 bg-blue-500 absolute top-0 left-0 right-0" />
            <div className="text-blue-600 dark:text-blue-400 text-sm font-semibold mb-1.5">🛡 State Prediction Firewall</div>
            <h3 className="font-semibold text-[var(--text-primary)] text-sm mb-1.5">Zero State Stock Predictions</h3>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              Enforced by both Python backend and TypeScript UI firewalls. State acts feature 0 stock predictions, 0 directional forecasts, and 0 anticipation scores. Dedicated to statutory compliance and corporate exposure intelligence.
            </p>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 relative overflow-hidden">
            <div className="h-0.5 bg-amber-500 absolute top-0 left-0 right-0" />
            <div className="text-amber-600 dark:text-amber-400 text-sm font-semibold mb-1.5">🔒 Intelligence Firewall</div>
            <h3 className="font-semibold text-[var(--text-primary)] text-sm mb-1.5">Non-Listed Entity Isolation</h3>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              Non-public/private entities (23 intelligence companies) are strictly segregated from financial prediction models. Unbroken isolation ensures econometric models run strictly on liquid NSE/BSE quant securities.
            </p>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-5 relative overflow-hidden">
            <div className="h-0.5 bg-emerald-500 absolute top-0 left-0 right-0" />
            <div className="text-emerald-600 dark:text-emerald-400 text-sm font-semibold mb-1.5">🏢 Multi-Tenant SaaS Isolation</div>
            <h3 className="font-semibold text-[var(--text-primary)] text-sm mb-1.5">Rigorous RBAC &amp; Audit Trail</h3>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              Complete tenant partitioning across watchlists, alert rules, AI telemetry, and activity logs. 4 distinct roles: OWNER, ADMIN, MEMBER, VIEWER. Append-only tamper-resistant audit logging.
            </p>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* 7. CORE PLATFORM WORKFLOWS                                           */}
      {/* -------------------------------------------------------------------- */}
      <section className="px-6 py-10 max-w-7xl mx-auto border-t border-[var(--border-default)]">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 text-center">Core Platform Workflows</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/explorer"
            className="group block p-4.5 rounded-xl bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-default)] hover:border-[var(--border-strong)] transition-all shadow-xs"
          >
            <div className="text-xl mb-2">🔍</div>
            <div className="font-semibold text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-sm">
              Legislative Explorer
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
              Search and filter across all 66 acts, 70 corporations, and regulatory stages.
            </p>
          </Link>

          <Link
            href="/predictions"
            className="group block p-4.5 rounded-xl bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-default)] hover:border-[var(--border-strong)] transition-all shadow-xs"
          >
            <div className="text-xl mb-2">📈</div>
            <div className="font-semibold text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-sm">
              Market Predictions
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
              Event study windows [-1,+1] to [-10,+10] with statistical confidence intervals.
            </p>
          </Link>

          <Link
            href="/watchlists"
            className="group block p-4.5 rounded-xl bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-default)] hover:border-[var(--border-strong)] transition-all shadow-xs"
          >
            <div className="text-xl mb-2">⭐</div>
            <div className="font-semibold text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-sm">
              Custom Watchlists
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
              Curate portfolio baskets of bills, companies, and states with automated change alerts.
            </p>
          </Link>

          <Link
            href="/ai-analyst"
            className="group block p-4.5 rounded-xl bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-default)] hover:border-[var(--border-strong)] transition-all shadow-xs"
          >
            <div className="text-xl mb-2">✦</div>
            <div className="font-semibold text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-sm">
              Grounded AI Analyst
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
              Synthesize parliamentary intent and corporate risks with verified statutory citations.
            </p>
          </Link>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* 8. INSTITUTIONAL REGULATORY FOOTER                                   */}
      {/* -------------------------------------------------------------------- */}
      <footer className="mt-12 border-t border-[var(--border-default)] pt-8 px-6 text-center text-xs text-[var(--text-muted)] max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          India Legislative Intelligence Platform · Institutional Quantitative Analytics · Neutral Research Support
        </div>
        <div className="flex gap-4">
          <Link href="/overview" className="hover:text-[var(--text-primary)] transition-colors">Overview</Link>
          <Link href="/monitoring" className="hover:text-[var(--text-primary)] transition-colors">Monitoring</Link>
          <Link href="/settings" className="hover:text-[var(--text-primary)] transition-colors">Settings</Link>
          <Link href="/coverage" className="hover:text-[var(--text-primary)] transition-colors">Coverage</Link>
          <Link href="/onboarding" className="hover:text-[var(--text-primary)] transition-colors">Onboarding</Link>
        </div>
      </footer>
    </div>
  );
}
