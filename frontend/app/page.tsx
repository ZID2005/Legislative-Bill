/**
 * app/page.tsx
 * ============
 * Premium SaaS Landing Page & Product Overview.
 *
 * Task 8.19 — SaaS Launch Readiness, Authentication & End-to-End User Journey.
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { UserSession, authApi } from "@/lib/api/auth";

export default function LandingPage() {
  const [session, setSession] = useState<UserSession | null>(null);

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
      // Also try background getMe
      authApi.getMe().then(setSession).catch(() => {});
    }
  }, []);

  return (
    <div className="min-h-full bg-slate-950 text-slate-100 selection:bg-blue-600 selection:text-white pb-20">
      {/* Top Banner / Ticker */}
      <div className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-2 text-xs text-slate-400 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-semibold text-slate-200">PRODUCTION ENGINE ONLINE</span>
          <span className="text-slate-600">|</span>
          <span>Central Event Studies: 20 Acts · 4,700 Predictions</span>
          <span className="text-slate-600">|</span>
          <span>State Coverage: 44 Acts (AP, KA, KL, TS)</span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="text-slate-400">SOC-2 Audit Trail: Active</span>
          <span className="text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded">
            Statutory Firewalls Locked
          </span>
        </div>
      </div>

      {/* Hero Section */}
      <section className="relative px-6 pt-16 pb-20 max-w-7xl mx-auto text-center overflow-hidden">
        {/* Subtle background glow */}
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-10 flex items-center justify-center opacity-25 pointer-events-none"
        >
          <div className="h-96 w-[45rem] rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 blur-[120px]" />
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/30 bg-blue-950/40 text-blue-400 text-xs font-medium mb-6">
          <span className="text-blue-300">New Milestone</span>
          <span className="text-slate-500">·</span>
          <span>SaaS Platform Hardened & Multi-Tenant Onboarding Live</span>
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
          India Legislative Intelligence &amp;{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-teal-300">
            Market Impact Predictions
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-300 max-w-3xl mx-auto font-normal leading-relaxed">
          The definitive regulatory analytics engine linking Parliament bills, State gazettes, and
          corporate exposure networks to quantitative securities with mathematically rigorous event studies.
        </p>

        {/* Action Buttons */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/workspace"
            className="px-6 py-3.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg shadow-blue-600/30 transition-all focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            Launch Command Center →
          </Link>
          {session ? (
            <Link
              href="/settings"
              className="px-6 py-3.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-sm transition-all"
            >
              Organization Settings ({session.display_name})
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="px-6 py-3.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-slate-500"
              >
                Sign In to Tenant
              </Link>
              <Link
                href="/signup"
                className="px-6 py-3.5 rounded-lg bg-emerald-900/40 hover:bg-emerald-800/40 border border-emerald-700/60 text-emerald-300 font-semibold text-sm transition-all"
              >
                Create Organization Account
              </Link>
            </>
          )}
          <Link
            href="/onboarding"
            className="px-6 py-3.5 rounded-lg bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800 text-slate-400 hover:text-slate-200 font-medium text-sm transition-all"
          >
            Interactive Tour (8 Steps)
          </Link>
        </div>

        {/* Real Analytical Metrics Cards */}
        <div className="mt-16 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 max-w-6xl mx-auto">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold text-white">20</div>
            <div className="text-xs text-slate-400 mt-1 font-medium">Central Acts Scanned</div>
            <div className="text-[10px] text-blue-400 mt-0.5">22 Scanned Records</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold text-teal-400">44</div>
            <div className="text-xs text-slate-400 mt-1 font-medium">State Acts Enacted</div>
            <div className="text-[10px] text-teal-500 mt-0.5">AP=12, KA=11, KL=11, TS=10</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold text-indigo-400">47</div>
            <div className="text-xs text-slate-400 mt-1 font-medium">Quant Securities</div>
            <div className="text-[10px] text-indigo-500 mt-0.5">NSE/BSE Listed</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold text-amber-400">4,700</div>
            <div className="text-xs text-slate-400 mt-1 font-medium">Predictions</div>
            <div className="text-[10px] text-amber-500 mt-0.5">940 Pairs × 5 Windows</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold text-purple-400">70</div>
            <div className="text-xs text-slate-400 mt-1 font-medium">Total Companies</div>
            <div className="text-[10px] text-purple-500 mt-0.5">47 Quant + 23 Intel</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center">
            <div className="text-2xl sm:text-3xl font-bold text-emerald-400">104</div>
            <div className="text-xs text-slate-400 mt-1 font-medium">Exposures</div>
            <div className="text-[10px] text-emerald-500 mt-0.5">18 Central + 86 State</div>
          </div>
        </div>
      </section>

      {/* Architectural Guarantees & Firewalls */}
      <section className="px-6 py-12 max-w-6xl mx-auto border-t border-slate-800/80">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            Architectural Guarantees &amp; Firewalls
          </h2>
          <p className="mt-2 text-sm text-slate-400 max-w-2xl mx-auto">
            Strict separation between quantitative econometric predictions, statutory state facts, and enterprise tenant boundaries.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
            <div className="h-1 bg-blue-500 absolute top-0 left-0 right-0" />
            <div className="text-blue-400 text-lg mb-2">🛡 State Prediction Firewall</div>
            <h3 className="font-semibold text-white text-base mb-2">Zero State Stock Predictions</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Enforced by both Python backend and TypeScript UI firewalls. State acts feature 0 stock predictions, 0 directional forecasts, and 0 anticipation scores. Dedicated to statutory compliance and corporate exposure intelligence.
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
            <div className="h-1 bg-amber-500 absolute top-0 left-0 right-0" />
            <div className="text-amber-400 text-lg mb-2">🔒 Intelligence Firewall</div>
            <h3 className="font-semibold text-white text-base mb-2">Non-Listed Entity Isolation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Non-public/private entities (23 intelligence companies) are strictly segregated from financial prediction models. Unbroken isolation ensures econometric models run strictly on liquid NSE/BSE quant securities.
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
            <div className="h-1 bg-emerald-500 absolute top-0 left-0 right-0" />
            <div className="text-emerald-400 text-lg mb-2">🏢 Multi-Tenant SaaS Isolation</div>
            <h3 className="font-semibold text-white text-base mb-2">Rigorous RBAC &amp; Audit Trail</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Complete tenant partitioning across watchlists, alert rules, AI telemetry, and activity logs. 4 distinct roles: OWNER, ADMIN, MEMBER, VIEWER. Append-only tamper-resistant audit logging.
            </p>
          </div>
        </div>
      </section>

      {/* Feature Pillar Grid */}
      <section className="px-6 py-12 max-w-6xl mx-auto border-t border-slate-800/80">
        <h2 className="text-2xl font-bold text-white mb-8 text-center">Core Platform Workflows</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <Link
            href="/explorer"
            className="group block p-5 rounded-xl bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800 hover:border-slate-700 transition-all"
          >
            <div className="text-2xl mb-3">🔍</div>
            <div className="font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
              Legislative Explorer
            </div>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Search and filter across all 66 acts, 70 corporations, and regulatory stages.
            </p>
          </Link>

          <Link
            href="/predictions"
            className="group block p-5 rounded-xl bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800 hover:border-slate-700 transition-all"
          >
            <div className="text-2xl mb-3">📈</div>
            <div className="font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
              Market Predictions
            </div>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Event study windows [-1,+1] to [-10,+10] with statistical confidence intervals.
            </p>
          </Link>

          <Link
            href="/watchlists"
            className="group block p-5 rounded-xl bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800 hover:border-slate-700 transition-all"
          >
            <div className="text-2xl mb-3">⭐</div>
            <div className="font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
              Custom Watchlists
            </div>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Curate portfolio baskets of bills, companies, and states with automated change alerts.
            </p>
          </Link>

          <Link
            href="/ai-analyst"
            className="group block p-5 rounded-xl bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800 hover:border-slate-700 transition-all"
          >
            <div className="text-2xl mb-3">✦</div>
            <div className="font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
              Grounded AI Analyst
            </div>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Synthesize parliamentary intent and corporate risks with verified statutory citations.
            </p>
          </Link>
        </div>
      </section>

      {/* Enterprise Footer */}
      <footer className="mt-16 border-t border-slate-800/80 pt-8 px-6 text-center text-xs text-slate-500 max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          India Legislative Intelligence Platform · Institutional Quantitative Analytics
        </div>
        <div className="flex gap-4">
          <Link href="/overview" className="hover:text-slate-300">Overview</Link>
          <Link href="/monitoring" className="hover:text-slate-300">Monitoring</Link>
          <Link href="/settings" className="hover:text-slate-300">Settings</Link>
          <Link href="/onboarding" className="hover:text-slate-300">Onboarding</Link>
        </div>
      </footer>
    </div>
  );
}
