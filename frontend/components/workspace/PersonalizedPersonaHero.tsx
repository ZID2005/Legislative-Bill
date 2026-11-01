/**
 * components/workspace/PersonalizedPersonaHero.tsx
 * ================================================
 * TASK 1.15I — ONBOARDING-TO-PLATFORM HANDOFF & PERSONALIZED FIRST-RUN EXPERIENCE.
 *
 * Implements the personalized Command Center hero reflecting the user's selected
 * organization, analytical persona, jurisdiction coverage, and preferences.
 *
 * Adapts presentation and recommended starting actions for:
 * - INVESTOR: Company exposure, Central predictions, anticipation intelligence.
 * - BUSINESS_OWNER: Statutory compliance, State gazettes, corporate exposure matrix.
 * - ANALYST_RESEARCHER: Bill dossiers, evidence provenance, prediction methodology.
 * - GENERAL_PUBLIC: Plain-language summaries, stakeholder perspectives, civic impact.
 *
 * Safeguards:
 * - Does not hide any core platform functionality.
 * - Does not create unsupported predictions or financial advice.
 * - Strictly preserves Central and State bill separation (0 State stock predictions).
 * - Preserves intelligence-only company quarantine.
 */

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  OnboardingHandoffData,
  PersonaConfig,
  getPersonaConfig,
  isHeroCollapsed,
  setHeroCollapsed,
} from "@/lib/onboarding/handoff";

export interface PersonalizedPersonaHeroProps {
  handoff: OnboardingHandoffData;
  onReopenGuidance?: () => void;
  className?: string;
}

export function PersonalizedPersonaHero({
  handoff,
  onReopenGuidance,
  className = "",
}: PersonalizedPersonaHeroProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setCollapsed(isHeroCollapsed());
  }, []);

  const config: PersonaConfig = getPersonaConfig(handoff.persona);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    setHeroCollapsed(next);
  };

  if (!mounted) {
    return null;
  }

  return (
    <section
      data-testid="personalized-persona-hero"
      aria-label="Personalized Command Desk Orientation"
      className={`rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-5 sm:p-6 space-y-4 shadow-xs transition-all ${className}`}
    >
      {/* -------------------------------------------------------------------
       * 1. Top Identity Strip: Organization, Persona Badge & Jurisdiction Scope
       * ------------------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-[var(--border-subtle)]">
        <div className="flex flex-wrap items-center gap-2">
          {/* Organization Tag */}
          <span
            data-testid="hero-org-badge"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-[var(--bg-base)] text-[var(--text-primary)] border border-[var(--border-default)] shadow-2xs font-mono"
          >
            <span>🏢</span>
            <span className="truncate max-w-[200px]">{handoff.orgName}</span>
          </span>

          {/* Persona Tag */}
          <span
            data-testid="hero-persona-badge"
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/25"
          >
            <span>{config.icon}</span>
            <span>{config.displayName}</span>
          </span>

          {/* Jurisdictions Scope */}
          <span
            data-testid="hero-jurisdictions-badge"
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono text-[var(--text-muted)] bg-[var(--bg-elevated)] border border-[var(--border-default)]"
          >
            <span className="text-[var(--text-faint)]">Coverage:</span>
            <span className="font-semibold text-[var(--text-secondary)]">
              {handoff.selectedJurisdictions.join(", ")}
            </span>
          </span>
        </div>

        {/* Action Controls: Guidance Reopen & Collapse Toggle */}
        <div className="flex items-center gap-2">
          {onReopenGuidance && (
            <button
              type="button"
              onClick={onReopenGuidance}
              data-testid="hero-open-guidance-btn"
              className="text-xs px-2.5 py-1 rounded bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-default)] transition-colors flex items-center gap-1.5"
            >
              <span>🧭</span>
              <span className="hidden sm:inline">First-Run Tour</span>
            </button>
          )}

          <button
            type="button"
            onClick={toggleCollapse}
            aria-expanded={!collapsed}
            data-testid="hero-toggle-collapse-btn"
            className="text-xs px-2.5 py-1 rounded bg-[var(--bg-base)] hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border-default)] transition-colors"
          >
            {collapsed ? "Expand Orientation ▼" : "Minimize ▲"}
          </button>
        </div>
      </div>

      {/* -------------------------------------------------------------------
       * 2. Orientation Body (Collapsible)
       * ------------------------------------------------------------------- */}
      {!collapsed && (
        <div className="space-y-4 pt-1 animate-in fade-in duration-200">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                {config.categoryLabel} First-Run Experience
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)]">
                Active Setup
              </span>
            </div>
            <h2
              data-testid="hero-headline"
              className="text-lg sm:text-xl font-bold text-[var(--text-primary)] tracking-tight"
            >
              {config.headline}
            </h2>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1 leading-relaxed max-w-4xl">
              {config.description}
            </p>
          </div>

          {/* Statutory Notice Strip */}
          <div
            data-testid="hero-statutory-notice"
            className="flex items-center gap-2 p-2.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] text-xs text-[var(--text-secondary)]"
          >
            <span className="text-blue-500 font-bold flex-shrink-0">⚖</span>
            <span className="flex-1 font-mono text-[11px] leading-relaxed">
              {config.statutoryNotice}
            </span>
          </div>

          {/* Recommended Starting Actions Grid */}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-2.5 flex items-center justify-between">
              <span>Recommended Starting Actions for {config.categoryLabel}</span>
              <span className="text-[10px] font-normal text-[var(--text-faint)] lowercase font-mono">
                all platform workflows remain active
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {config.recommendedActions.map((action, idx) => (
                <Link
                  key={idx}
                  href={action.href}
                  data-testid={`hero-action-${idx}`}
                  className="group p-3.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] hover:border-blue-500/40 hover:bg-[var(--bg-card-hover)] transition-all flex flex-col justify-between space-y-2.5"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-base" aria-hidden="true">
                        {action.icon}
                      </span>
                      <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                        {action.badge}
                      </span>
                    </div>
                    <h3 className="text-xs font-bold text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-[11px] text-[var(--text-muted)] leading-relaxed line-clamp-2">
                      {action.description}
                    </p>
                  </div>

                  <span className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform pt-1 border-t border-[var(--border-subtle)]">
                    <span>{action.actionText}</span>
                  </span>
                </Link>
              ))}
            </div>
          </div>

          {/* Key Analytical Focus Areas */}
          <div className="pt-2 border-t border-[var(--border-subtle)] flex flex-wrap items-center gap-2 text-xs">
            <span className="text-[11px] text-[var(--text-muted)] font-mono">Key Focus:</span>
            {config.keyFocusAreas.map((area, i) => (
              <span
                key={i}
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg-base)] text-[var(--text-secondary)] border border-[var(--border-default)]"
              >
                {area}
              </span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

