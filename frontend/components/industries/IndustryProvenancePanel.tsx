/**
 * components/industries/IndustryProvenancePanel.tsx
 * =================================================
 * Verified data sources and citation audit trail for the industry intelligence dossier.
 */

import React from "react";
import type { ProvenanceSourceItem, RelatedIndustryItem } from "@/types/api";
import Link from "next/link";

export interface IndustryProvenancePanelProps {
  provenanceSources: ProvenanceSourceItem[];
  relatedIndustries: RelatedIndustryItem[];
}

export function IndustryProvenancePanel({
  provenanceSources,
  relatedIndustries,
}: IndustryProvenancePanelProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Provenance Card */}
      <section aria-labelledby="provenance-heading" className="space-y-4">
        <div>
          <h2 id="provenance-heading" className="text-lg font-semibold text-[var(--text-primary)]">
            Data Provenance & Verification
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Audit trail of official government registries and legislative sources
          </p>
        </div>

        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60 p-4 space-y-3">
          {provenanceSources.map((src, idx) => (
            <div key={idx} className="rounded border border-[var(--border-default)] bg-[var(--bg-elevated)]/40 p-3 text-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[var(--text-primary)]">{src.source}</span>
                <span className="rounded bg-emerald-950/60 border border-emerald-700/50 px-1.5 py-0.2 text-[10px] font-medium text-emerald-300">
                  {src.verification_status}
                </span>
              </div>
              <p className="text-[11px] text-[var(--text-muted)]">{src.source_type}</p>
              <p className="text-[var(--text-secondary)] text-[11px]">{src.evidence_text}</p>
              {src.verified_at && (
                <span className="text-[10px] text-[var(--text-faint)] block pt-1">
                  Last verified: {new Date(src.verified_at).toLocaleDateString()}
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Related Industries Card */}
      <section aria-labelledby="related-industries-heading" className="space-y-4">
        <div>
          <h2 id="related-industries-heading" className="text-lg font-semibold text-[var(--text-primary)]">
            Peer Sector Industries
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Validated peer industries operating in the same economic sector
          </p>
        </div>

        <div className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)]/60 p-4">
          {relatedIndustries.length === 0 ? (
            <p className="text-xs text-[var(--text-faint)] italic">No additional peer industries in this sector.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {relatedIndustries.map((peer) => (
                <Link
                  key={peer.industry_id}
                  href={`/industry/${encodeURIComponent(peer.industry_id)}`}
                  className="rounded border border-[var(--border-default)] bg-[var(--bg-elevated)]/50 hover:bg-[var(--bg-elevated)] hover:border-[var(--border-strong)] p-3 transition-colors flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-medium text-[var(--text-primary)] block">
                      {peer.name}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {peer.related_bills_count} related bills
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-faint)]">→</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default IndustryProvenancePanel;
