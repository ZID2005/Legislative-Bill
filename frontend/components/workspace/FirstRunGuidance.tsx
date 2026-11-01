/**
 * components/workspace/FirstRunGuidance.tsx
 * =========================================
 * TASK 1.15I — ONBOARDING-TO-PLATFORM HANDOFF & PERSONALIZED FIRST-RUN EXPERIENCE.
 *
 * Lightweight, progressive-disclosure first-run guidance tour for new and returning
 * users navigating the Seance platform.
 *
 * Capabilities:
 * 1. Six structured discovery modules:
 *    - 1. Command Center (Personalized decision desk & telemetry)
 *    - 2. Bill Intelligence & Dossiers (Full texts, procedural timelines, PDF sources)
 *    - 3. Company Exposure (Vulnerability matrix, quant modeled vs intel quarantine)
 *    - 4. Predictions & Anticipation (Central event studies, 0 State predictions)
 *    - 5. Workspace & Portfolio (Holdings sensitivity, custom watchlists)
 *    - 6. Settings & Data Governance (Tenant security, cryptographic audit trail, data export)
 * 2. Uncluttered, non-blocking presentation: user can freely interact with the page.
 * 3. Step progression with step dots, Previous, Next, and Skip options.
 * 4. Dismiss button that persists state to localStorage (seance_first_run_guidance_dismissed).
 * 5. Reopenable anytime from the Workspace Header.
 * 6. Responsive across 1440x900, 768x1024, and 375x812 with reduced-motion support.
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { setGuidanceDismissed } from "@/lib/onboarding/handoff";

export interface GuidanceStep {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  icon: string;
  description: string;
  keyPillars: string[];
  routeHref: string;
  routeLabel: string;
}

export const GUIDANCE_STEPS: GuidanceStep[] = [
  {
    id: "command-center",
    number: 1,
    title: "Command Center & Decision Hub",
    subtitle: "Your Unified Legislative Desk",
    icon: "⚖",
    description:
      "Consolidates monitored bills, corporate exposures, unread alerts, and real-time activity feeds. Grounded with epistemic status badges: [OBSERVED] ⟂ [DERIVED] ⟂ [PREDICTION].",
    keyPillars: [
      "Attention summary strip with live metrics",
      "Epistemic activity feed without polling noise",
      "Integrated Groq LLaMA 3.3 70B AI Workspace Assistant",
    ],
    routeHref: "/workspace",
    routeLabel: "Explore Command Center →",
  },
  {
    id: "bills",
    number: 2,
    title: "Bill Intelligence & Dossiers",
    subtitle: "Parliament Acts & State Assemblies",
    icon: "📜",
    description:
      "Deep legislative dossiers covering Central Parliament and State legislative assemblies (AP, KA, KL, TS). Read clause-level provisions, official PDFs, and procedural timelines.",
    keyPillars: [
      "Authoritative provenance with SHA-256 integrity",
      "Clause-by-clause amendment comparison",
      "Executive summaries and stakeholder perspectives",
    ],
    routeHref: "/bills",
    routeLabel: "Browse Bill Dossiers →",
  },
  {
    id: "companies",
    number: 3,
    title: "Corporate Exposure Networks",
    subtitle: "Direct & Sector Regulatory Vulnerabilities",
    icon: "🏢",
    description:
      "70 monitored Indian listed companies across 22 sectors. Strictly separates quantitative modeled equities from qualitative intelligence-only quarantined entities.",
    keyPillars: [
      "Exposure linkage scores and sensitivity ratings",
      "Sector beta and regulatory risk matrix",
      "Intelligence-only company isolation safeguards",
    ],
    routeHref: "/companies",
    routeLabel: "View Corporate Universe →",
  },
  {
    id: "predictions",
    number: 4,
    title: "Predictions & Anticipation Intelligence",
    subtitle: "Econometric Horizons & Early Signals",
    icon: "📈",
    description:
      "Multi-window Cumulative Abnormal Return (CAR) modeling for Central bills. Pre-event public disclosures and velocity tracking. Strictly 0 State bill stock predictions.",
    keyPillars: [
      "Econometric event studies on Central legislation",
      "Pre-event anticipation evidence & velocity signals",
      "Statutory firewall: zero State stock predictions",
    ],
    routeHref: "/predictions",
    routeLabel: "Inspect Predictions →",
  },
  {
    id: "portfolio",
    number: 5,
    title: "Workspace & Portfolio Features",
    subtitle: "Holdings Sensitivity & Custom Watchlists",
    icon: "💼",
    description:
      "Map your actual equity holdings against active legislative measures. Generate printable executive impact reports and configure severity-based alert delivery rules.",
    keyPillars: [
      "Portfolio holdings matching & sensitivity analysis",
      "Multi-entity custom watchlists (bills, companies, sectors)",
      "Daily and weekly regulatory digest scheduling",
    ],
    routeHref: "/portfolio",
    routeLabel: "Open Portfolio Exposure →",
  },
  {
    id: "settings",
    number: 6,
    title: "Settings & Data Governance",
    subtitle: "Tenant Security & Cryptographic Auditing",
    icon: "⚙",
    description:
      "Manage tenant organization profile, invite team members with role-based access (RBAC), verify HMAC cryptographic signatures, and export immutable JSON tenant archives.",
    keyPillars: [
      "RBAC member directory (Owner, Admin, Member, Viewer)",
      "Alert delivery channels (In-App & Email)",
      "JSON data export and statutory immutability records",
    ],
    routeHref: "/settings",
    routeLabel: "Manage Governance →",
  },
];

export interface FirstRunGuidanceProps {
  onDismiss: () => void;
  className?: string;
}

export function FirstRunGuidance({ onDismiss, className = "" }: FirstRunGuidanceProps) {
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const step = GUIDANCE_STEPS[activeStepIndex];
  const isFirst = activeStepIndex === 0;
  const isLast = activeStepIndex === GUIDANCE_STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      handleDismiss();
    } else {
      setActiveStepIndex((prev) => Math.min(prev + 1, GUIDANCE_STEPS.length - 1));
    }
  };

  const handlePrev = () => {
    setActiveStepIndex((prev) => Math.max(prev - 1, 0));
  };

  const handleDismiss = () => {
    setGuidanceDismissed(true);
    onDismiss();
  };

  return (
    <div
      data-testid="first-run-guidance"
      role="region"
      aria-label="First-Run Platform Guidance"
      className={`relative rounded-xl border border-blue-500/30 bg-blue-500/[0.04] p-5 sm:p-6 space-y-4 shadow-sm transition-all ${className}`}
    >
      {/* -------------------------------------------------------------------
       * Header: Badge, Step Indicator & Close Button
       * ------------------------------------------------------------------- */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-blue-500/20">
        <div className="flex items-center gap-2">
          <span className="text-base" aria-hidden="true">
            🧭
          </span>
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
            Platform Discovery Guide
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-700 dark:text-blue-300 border border-blue-500/30 font-semibold">
            {step.number} of {GUIDANCE_STEPS.length}
          </span>
        </div>

        {/* Dismiss Button */}
        <button
          type="button"
          onClick={handleDismiss}
          data-testid="dismiss-guidance-btn"
          aria-label="Dismiss platform guidance tour"
          className="text-xs px-2.5 py-1 rounded-md bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border-default)] transition-colors flex items-center gap-1.5 focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          <span>Dismiss Tour</span>
          <span aria-hidden="true">✕</span>
        </button>
      </div>

      {/* -------------------------------------------------------------------
       * Step Content Body
       * ------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
        {/* Left Column: Icon + Step Title + Description */}
        <div className="md:col-span-7 space-y-2.5">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl p-2 rounded-lg bg-[var(--bg-base)] border border-blue-500/25 flex-shrink-0" aria-hidden="true">
              {step.icon}
            </span>
            <div>
              <span className="text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wide">
                {step.subtitle}
              </span>
              <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)] tracking-tight">
                {step.title}
              </h3>
            </div>
          </div>

          <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed">
            {step.description}
          </p>

          <div className="pt-1">
            <Link
              href={step.routeHref}
              className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline"
            >
              <span>{step.routeLabel}</span>
            </Link>
          </div>
        </div>

        {/* Right Column: Key Capabilities Pillars */}
        <div className="md:col-span-5 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg p-3.5 space-y-2">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-[var(--text-muted)] block">
            Key Architecture &amp; Safeguards:
          </span>
          <ul className="space-y-1.5 text-xs text-[var(--text-secondary)]">
            {step.keyPillars.map((pillar, i) => (
              <li key={i} className="flex items-start gap-1.5 leading-snug">
                <span className="text-blue-500 font-bold text-xs mt-0.5">•</span>
                <span>{pillar}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* -------------------------------------------------------------------
       * Navigation Controls: Step Dots + Prev / Next / Finish
       * ------------------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-blue-500/20">
        {/* Step dots */}
        <div className="flex items-center gap-1.5" aria-label="Tour progress dots">
          {GUIDANCE_STEPS.map((s, idx) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveStepIndex(idx)}
              aria-label={`Jump to step ${idx + 1}: ${s.title}`}
              aria-current={idx === activeStepIndex ? "step" : undefined}
              className={`h-2 rounded-full transition-all ${
                idx === activeStepIndex
                  ? "w-6 bg-blue-600 dark:bg-blue-400"
                  : "w-2 bg-[var(--border-strong)] hover:bg-blue-400/50"
              }`}
            />
          ))}
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handlePrev}
            disabled={isFirst}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md border transition-colors ${
              isFirst
                ? "border-[var(--border-subtle)] text-[var(--text-faint)] cursor-not-allowed opacity-50"
                : "border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
            }`}
          >
            ← Previous
          </button>

          <button
            type="button"
            onClick={handleNext}
            data-testid="guidance-next-btn"
            className="px-4 py-1.5 text-xs font-semibold rounded-md bg-blue-600 hover:bg-blue-500 text-white shadow-xs transition-colors"
          >
            {isLast ? "Got it, Explore Workspace ✓" : "Next Capability →"}
          </button>
        </div>
      </div>
    </div>
  );
}

