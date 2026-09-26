/**
 * components/bills/ProvenancePanel.tsx
 * ====================================
 * Source and Provenance panel for the Bill Detail Dossier.
 * Displays authoritative links, document links, data freshness, and field-level provenance audit map.
 */

"use client";

import React from "react";
import type { BillSummaryItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, Badge } from "@/components/ui/Badge";

export interface ProvenancePanelProps {
  bill: BillSummaryItem;
  provenance: Record<string, string>;
  className?: string;
}

export function ProvenancePanel({
  bill,
  provenance,
  className = "",
}: ProvenancePanelProps) {
  const provEntries = Object.entries(provenance || {});

  const getTierVariant = (tier: string) => {
    switch (tier.toUpperCase()) {
      case "AUTHORITATIVE":
        return "emerald";
      case "DERIVED":
      case "SYSTEM_DERIVED":
        return "primary";
      case "UNAVAILABLE":
        return "muted";
      case "NONE":
        return "slate";
      default:
        return "default";
    }
  };

  return (
    <div className={`space-y-4 ${className}`} aria-label="Source and provenance panel">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2 w-full">
            <div>
              <CardTitle>Authoritative Source &amp; Data Provenance</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Official document links, statutory gazette references, and cryptographic provenance audit.
              </p>
            </div>
            <SourceBadge type="FACT" size="xs" showTooltip />
          </div>
        </CardHeader>

        <div className="space-y-5">
          {/* Primary Source Reference Links */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Official Portal */}
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Official Legislative Portal
                </span>
                <Badge variant="primary" size="xs">
                  Source
                </Badge>
              </div>
              {bill.source_url ? (
                <div>
                  <a
                    href={bill.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-400 hover:text-blue-300 underline break-all flex items-center gap-1.5 font-mono"
                  >
                    <span>{bill.source_url}</span>
                    <span aria-hidden="true">↗</span>
                  </a>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Verified record from primary assembly/parliament registry.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  Primary web URL unavailable in registry.
                </p>
              )}
            </div>

            {/* Official PDF Document */}
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Official Gazette / Bill PDF
                </span>
                <Badge variant="emerald" size="xs">
                  Document
                </Badge>
              </div>
              {bill.pdf_url ? (
                <div>
                  <a
                    href={bill.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-emerald-400 hover:text-emerald-300 underline break-all flex items-center gap-1.5 font-mono"
                  >
                    <span>{bill.pdf_url}</span>
                    <span aria-hidden="true">↗</span>
                  </a>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Authoritative legislative gazette publication document.
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">
                  Digital PDF document link not cataloged.
                </p>
              )}
            </div>
          </div>

          {/* Quality & Freshness Verification Ribbon */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg border border-slate-800/80 bg-slate-900/40 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Data Quality:</span>
              <Badge variant="emerald" size="xs">
                ✓ {bill.data_quality || "VERIFIED"}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Data Sufficiency:</span>
              <span className="font-semibold text-slate-300 font-mono">
                {bill.data_sufficiency}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Jurisdiction Authority:</span>
              <span className="text-slate-300">
                {bill.jurisdiction === "central" ? "Parliament of India" : `${bill.state} Assembly`}
              </span>
            </div>
          </div>

          {/* Field-by-Field Provenance Audit Map */}
          {provEntries.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Field-Level Provenance Audit Map
              </h4>
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300" aria-label="Field provenance table">
                  <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th scope="col" className="py-2 px-3">Field Name</th>
                      <th scope="col" className="py-2 px-3">Authority Classification</th>
                      <th scope="col" className="py-2 px-3">Standard / Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono text-[11px]">
                    {provEntries.map(([field, tier]) => (
                      <tr key={field} className="hover:bg-slate-900/40">
                        <td className="py-2 px-3 text-slate-300">
                          {field.replace(/_/g, " ")}
                        </td>
                        <td className="py-2 px-3">
                          <Badge variant={getTierVariant(tier)} size="xs">
                            {tier}
                          </Badge>
                        </td>
                        <td className="py-2 px-3 text-slate-500 font-sans">
                          {tier === "AUTHORITATIVE"
                            ? "Primary government legislative record"
                            : tier === "DERIVED" || tier === "SYSTEM_DERIVED"
                            ? "Deterministic text-extraction pipeline"
                            : "Not recorded in primary gazette"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

export default ProvenancePanel;
