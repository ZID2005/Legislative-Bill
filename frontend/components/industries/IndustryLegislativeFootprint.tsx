/**
 * components/industries/IndustryLegislativeFootprint.tsx
 * ======================================================
 * Displays all related bills affecting this industry, separating Central and State legislation.
 */

import React, { useState } from "react";
import Link from "next/link";
import { JurisdictionBadge, StatusBadge, ExposureBadge } from "@/components/ui/Badge";
import type { IndustryBillItem } from "@/types/api";

export interface IndustryLegislativeFootprintProps {
  centralBills: IndustryBillItem[];
  stateBills: IndustryBillItem[];
}

export function IndustryLegislativeFootprint({
  centralBills,
  stateBills,
}: IndustryLegislativeFootprintProps) {
  const [activeTab, setActiveTab] = useState<"ALL" | "CENTRAL" | "STATE">("ALL");

  const totalCount = centralBills.length + stateBills.length;
  const displayedBills =
    activeTab === "CENTRAL"
      ? centralBills
      : activeTab === "STATE"
      ? stateBills
      : [...centralBills, ...stateBills];

  return (
    <section aria-labelledby="legislative-footprint-heading" className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 id="legislative-footprint-heading" className="text-lg font-semibold text-[var(--text-primary)]">
            Legislative Footprint
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Authoritative Parliamentary and State Assembly acts affecting this industry
          </p>
        </div>

        {/* Tab Strip */}
        <div className="inline-flex rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] p-1 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab("ALL")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              activeTab === "ALL"
                ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            All Acts ({totalCount})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("CENTRAL")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              activeTab === "CENTRAL"
                ? "bg-amber-950/60 text-amber-300 border border-amber-800/40"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Central Parliament ({centralBills.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("STATE")}
            className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
              activeTab === "STATE"
                ? "bg-blue-950/60 text-blue-300 border border-blue-800/40"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            State Assemblies ({stateBills.length})
          </button>
        </div>
      </div>

      {/* Bills Cards List */}
      {displayedBills.length === 0 ? (
        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/40 p-8 text-center">
          <p className="text-sm text-[var(--text-muted)]">No legislative records documented for this selection.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {displayedBills.map((bill) => {
            const isCentral = bill.jurisdiction.toLowerCase() === "central";
            return (
              <div
                key={`${bill.jurisdiction}-${bill.bill_id}`}
                className="group rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60 hover:bg-[var(--bg-card)] hover:border-[var(--border-strong)] p-4 transition-all duration-200"
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <JurisdictionBadge jurisdiction={bill.jurisdiction} state={bill.state} size="xs" />
                      <StatusBadge status={bill.legislative_status} size="xs" />
                      <ExposureBadge strength={bill.exposure_strength} size="xs" />
                      {bill.economic_mechanism && (
                        <span className="rounded bg-[var(--bg-elevated)] border border-[var(--border-strong)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-secondary)] uppercase">
                          {bill.economic_mechanism}
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-400 transition-colors">
                      <Link href={`/bills/${encodeURIComponent(bill.bill_id)}`}>
                        {bill.bill_title}
                      </Link>
                    </h3>

                    <p className="text-xs text-[var(--text-muted)]">
                      Policy Domain: <span className="text-[var(--text-secondary)] font-medium">{bill.policy_domain}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Link
                      href={`/bills/${encodeURIComponent(bill.bill_id)}`}
                      className="rounded bg-[var(--bg-elevated)] px-2.5 py-1 text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-white transition-colors"
                    >
                      View Bill Dossier →
                    </Link>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-[var(--border-default)]/60 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-[var(--text-muted)]">
                  <p className="text-[var(--text-muted)] italic text-[11px]">
                    {bill.provisions_summary}
                  </p>
                  <div className="flex items-center gap-1.5 flex-shrink-0 text-[11px]">
                    <span className="text-[var(--text-faint)]">Exposed Entities:</span>
                    <span className="text-[var(--text-secondary)] font-medium">
                      {bill.exposed_company_names.slice(0, 3).join(", ")}
                      {bill.exposed_company_names.length > 3 && ` +${bill.exposed_company_names.length - 3} more`}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default IndustryLegislativeFootprint;
