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
          <h2 id="provenance-heading" className="text-lg font-semibold text-white">
            Data Provenance & Verification
          </h2>
          <p className="text-xs text-slate-400">
            Audit trail of official government registries and legislative sources
          </p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 space-y-3">
          {provenanceSources.map((src, idx) => (
            <div key={idx} className="rounded border border-slate-800 bg-slate-800/40 p-3 text-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">{src.source}</span>
                <span className="rounded bg-emerald-950/60 border border-emerald-700/50 px-1.5 py-0.2 text-[10px] font-medium text-emerald-300">
                  {src.verification_status}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">{src.source_type}</p>
              <p className="text-slate-300 text-[11px]">{src.evidence_text}</p>
              {src.verified_at && (
                <span className="text-[10px] text-slate-500 block pt-1">
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
          <h2 id="related-industries-heading" className="text-lg font-semibold text-white">
            Peer Sector Industries
          </h2>
          <p className="text-xs text-slate-400">
            Validated peer industries operating in the same economic sector
          </p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
          {relatedIndustries.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No additional peer industries in this sector.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {relatedIndustries.map((peer) => (
                <Link
                  key={peer.industry_id}
                  href={`/industry/${encodeURIComponent(peer.industry_id)}`}
                  className="rounded border border-slate-800 bg-slate-800/50 hover:bg-slate-800 hover:border-slate-700 p-3 transition-colors flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-medium text-slate-200 block">
                      {peer.name}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {peer.related_bills_count} related bills
                    </span>
                  </div>
                  <span className="text-xs text-slate-500">→</span>
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
