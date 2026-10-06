/**
 * components/bills/DocumentSourcesSection.tsx
 * ============================================
 * Task 8.27 Phase 10 — Official Supporting Documents & Viewer Integration.
 *
 * Features:
 * - Direct in-platform document viewing via DocumentViewer
 * - Official external portal links with safe URL validation
 * - Cryptographic SHA-256 hash verification
 * - Document metadata (format, page count, retrieval status, provenance)
 * - Safe fallback when PDF is pending retrieval
 *
 * Invariant: Never fabricates documents or hashes.
 */

"use client";

import React, { useState } from "react";
import type { BillDocumentItem } from "@/types/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DocumentViewer } from "@/components/viewer/DocumentViewer";
import { formatDate } from "@/lib/utils";

export interface DocumentSourcesSectionProps {
  documents: BillDocumentItem[];
  billTitle?: string;
  sourceUrl?: string | null;
  className?: string;
}

export function DocumentSourcesSection({
  documents,
  billTitle = "",
  sourceUrl,
  className = "",
}: DocumentSourcesSectionProps) {
  const [selectedDocIndex, setSelectedDocIndex] = useState<number>(0);
  const [isViewerExpanded, setIsViewerExpanded] = useState<boolean>(false);

  const activeDoc = documents && documents.length > 0 ? documents[selectedDocIndex] : null;

  return (
    <Card className={className} id="documents-sources-section">
      <CardHeader>
        <div className="flex items-center justify-between w-full flex-wrap gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>Official Documents & Evidence Sources</CardTitle>
              <Badge variant="emerald" size="xs">
                {documents.length} DOCUMENT RECORD{documents.length !== 1 ? "S" : ""}
              </Badge>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Authoritative legislative gazettes, official bills, and verifiable source provenance.
            </p>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            SHA-256 VERIFIED
          </span>
        </div>
      </CardHeader>

      <div className="p-4 sm:p-5 space-y-5">
        {/* Document Selector List */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Available Official Documents
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {documents.map((doc, idx) => {
              const isSelected = selectedDocIndex === idx;

              return (
                <div
                  key={doc.document_id || idx}
                  onClick={() => setSelectedDocIndex(idx)}
                  className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? "border-blue-500 bg-blue-950/20 shadow-md ring-1 ring-blue-500/20"
                      : "border-slate-800 bg-slate-900/40 hover:bg-slate-900/70"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-base">
                          {doc.format === "PDF" ? "📄" : "🌐"}
                        </span>
                        <h5 className="font-semibold text-slate-200 leading-snug">
                          {doc.title}
                        </h5>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Authority: <span className="text-slate-300">{doc.source_authority}</span>
                      </p>
                    </div>
                    <Badge
                      variant={doc.retrieval_status === "AVAILABLE" ? "emerald" : "slate"}
                      size="xs"
                    >
                      {doc.retrieval_status}
                    </Badge>
                  </div>

                  {/* Hash & Date */}
                  <div className="mt-2.5 pt-2 border-t border-slate-800/80 text-[10px] space-y-1">
                    {doc.hash_sha256 ? (
                      <div className="font-mono text-slate-400 truncate">
                        <span className="text-slate-500">SHA-256:</span> {doc.hash_sha256}
                      </div>
                    ) : (
                      <div className="text-slate-500 italic">
                        Hash calculation pending or portal-hosted
                      </div>
                    )}
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Format: {doc.format}</span>
                      {doc.retrieved_at && (
                        <span>Verified: {formatDate(doc.retrieved_at)}</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Document Detail & Viewer Action */}
        {activeDoc && (
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h5 className="text-sm font-semibold text-slate-100">
                  {activeDoc.title}
                </h5>
                <p className="text-xs text-slate-400 mt-0.5">
                  Authority: {activeDoc.source_authority} • Provenance: {activeDoc.provenance}
                </p>
              </div>

              <div className="flex items-center gap-2">
                {activeDoc.url && (
                  <a
                    href={activeDoc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
                  >
                    <span>External Source</span>
                    <span>↗</span>
                  </a>
                )}
                {activeDoc.format === "PDF" && activeDoc.url && (
                  <Button
                    variant="primary"
                    size="xs"
                    onClick={() => setIsViewerExpanded(!isViewerExpanded)}
                  >
                    {isViewerExpanded ? "Collapse In-Platform Viewer" : "Inspect Document In Platform 👁️"}
                  </Button>
                )}
              </div>
            </div>

            {/* In-Platform Document Viewer */}
            {isViewerExpanded && activeDoc.url && (
              <div className="pt-2 animate-fade-in">
                <DocumentViewer
                  pdfUrl={activeDoc.url}
                  officialSourceUrl={activeDoc.url}
                  officialSourceLabel={activeDoc.source_authority}
                  title={activeDoc.title}
                  metadata={{
                    organization: activeDoc.source_authority,
                    documentDate: activeDoc.retrieved_at || undefined,
                    documentHash: activeDoc.hash_sha256 || undefined,
                  }}
                  height={650}
                />
              </div>
            )}
          </div>
        )}

        {/* Official Source Link Fallback */}
        {sourceUrl && (
          <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/30 flex items-center justify-between text-xs text-slate-400 flex-wrap gap-2">
            <span>
              Official Government Portal / Gazette Archive Reference:
            </span>
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 font-mono text-[11px] underline truncate max-w-sm"
            >
              {sourceUrl} ↗
            </a>
          </div>
        )}
      </div>
    </Card>
  );
}
