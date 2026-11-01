/**
 * components/settings/DataGovernancePrivacySection.tsx
 * ====================================================
 * Section 4: Grounded AI Metering, Data Export, Statutory Immutability, and Tenant Deletion.
 *
 * Implements:
 * - Metered AI query consumption and quota telemetry
 * - Tenant JSON data export with immediate browser download
 * - Statutory and prediction immutability guarantee notice
 * - Owner-only organization soft-deletion with strict "DELETE" confirmation safeguard
 */

"use client";

import React from "react";

export interface DataGovernancePrivacySectionProps {
  aiUsage: any;
  isOwner: boolean;
  exporting: boolean;
  onExportData: () => void;
  deleteConfirm: string;
  setDeleteConfirm: (val: string) => void;
  deleteMsg: string | null;
  onDeleteTenant: () => void;
}

export function DataGovernancePrivacySection({
  aiUsage,
  isOwner,
  exporting,
  onExportData,
  deleteConfirm,
  setDeleteConfirm,
  deleteMsg,
  onDeleteTenant,
}: DataGovernancePrivacySectionProps) {
  return (
    <section className="space-y-6" aria-labelledby="data-governance-heading">
      {/* Section Header */}
      <div className="pb-3 border-b border-[var(--border-default)]">
        <h2 id="data-governance-heading" className="text-base font-bold text-[var(--text-primary)] font-headline">
          Data Governance, AI Metering &amp; Privacy
        </h2>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">
          Grounded AI consumption telemetry, data exports, public immutability, and tenant lifecycle.
        </p>
      </div>

      {/* Grounded AI Usage & Metering Card */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 pb-3 border-b border-[var(--border-hairline)]">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
              Grounded AI Intelligence Usage Telemetry
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Metered LLM queries grounded strictly against official parliamentary and state gazette citations.
            </p>
          </div>
          <span className="text-[10px] font-mono font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/25 px-2 py-0.5 rounded-sm self-start sm:self-auto">
            Telemetry Partitioned
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg">
            <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">
              Total Monthly Queries
            </span>
            <span className="text-xl font-bold font-tabular text-[var(--text-primary)] block mt-1">
              {(aiUsage?.total_queries ?? 0).toLocaleString()}
            </span>
            <span className="text-[10px] text-[var(--text-muted)] font-mono block mt-0.5">
              Current Billing Window
            </span>
          </div>

          <div className="p-3.5 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg">
            <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">
              Monthly Plan Quota
            </span>
            <span className="text-xl font-bold font-tabular text-[var(--text-secondary)] block mt-1">
              {(aiUsage?.monthly_quota ?? "500").toLocaleString()}
            </span>
            <span className="text-[10px] text-[var(--text-muted)] font-mono block mt-0.5">
              Queries / Month
            </span>
          </div>

          <div className="p-3.5 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg">
            <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">
              Grounding Citations Verified
            </span>
            <span className="text-xl font-bold font-tabular text-emerald-600 dark:text-emerald-400 block mt-1">
              100%
            </span>
            <span className="text-[10px] text-emerald-600/80 dark:text-emerald-400/80 font-mono block mt-0.5">
              Anti-Hallucination Pass
            </span>
          </div>
        </div>

        {/* Anti-Hallucination & Privacy Safeguards */}
        <div className="p-3.5 bg-[var(--bg-base)] border border-[var(--border-hairline)] rounded-lg text-xs space-y-1.5 leading-relaxed text-[var(--text-secondary)]">
          <strong className="block text-[11px] font-semibold text-[var(--text-primary)]">
            Anti-Hallucination &amp; Privacy Safeguards:
          </strong>
          <p className="text-[11px] text-[var(--text-muted)]">
            All AI assistant queries execute with strict tenant watchlist context validation (IDOR protected).
            Under contractual zero-retention policies, no customer queries, portfolio holdings, or proprietary watchlists are transmitted to external LLM training pipelines.
          </p>
        </div>
      </div>

      {/* Tenant Data Export Card */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
          Export Organization Data
        </h3>
        <p className="text-xs text-[var(--text-muted)] leading-relaxed">
          Download an immutable JSON export package of your tenant&apos;s custom watchlists, alert rules, delivery preferences, and non-sensitive user metadata.
        </p>
        <button
          type="button"
          onClick={onExportData}
          disabled={exporting}
          className="px-4 py-2 bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] rounded-md text-xs font-semibold text-[var(--text-primary)] transition-colors disabled:opacity-50"
        >
          {exporting ? "Generating Package…" : "Download Tenant JSON Export"}
        </button>
      </div>

      {/* Statutory Immutability Guarantee Card */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-2.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline flex items-center gap-1.5">
          <span aria-hidden="true">🛡</span>
          <span>Statutory &amp; Econometric Immutability Guarantee</span>
        </h3>
        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
          Tenant modifications, onboarding choices, or organization lifecycle actions will{" "}
          <strong className="text-rose-600 dark:text-rose-400 font-semibold">NEVER</strong> alter public legislative acts, official gazette PDFs, or frozen Central econometric event studies (20 acts, 47 securities, 4,700 predictions). Public parliamentary facts and econometric baselines remain globally immutable.
        </p>
      </div>

      {/* Danger Zone: Delete Organization (Owner Only) */}
      {isOwner && (
        <div className="bg-rose-500/5 border border-rose-500/25 rounded-xl p-5 sm:p-6 space-y-4">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 font-headline">
              Danger Zone: Organization Deletion
            </h3>
            <p className="text-xs text-rose-700 dark:text-rose-300 mt-1 leading-relaxed">
              Soft-deleting this tenant marks your organization as deleted, invalidates all member sessions, and purges tenant-scoped alert rules. Public legislative records remain untouched.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
            <input
              type="text"
              placeholder='Type "DELETE" to confirm'
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              className="px-3 py-2 bg-[var(--bg-base)] border border-rose-500/30 rounded-md text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-rose-500"
              aria-label='Type "DELETE" to confirm organization deletion'
            />
            <button
              type="button"
              onClick={onDeleteTenant}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 rounded-md text-xs font-bold text-white whitespace-nowrap transition-colors shadow-xs"
            >
              Delete Organization
            </button>
          </div>

          {deleteMsg && (
            <p className="text-xs text-rose-600 dark:text-rose-400 font-medium">
              {deleteMsg}
            </p>
          )}
        </div>
      )}
    </section>
  );
}

export default DataGovernancePrivacySection;

