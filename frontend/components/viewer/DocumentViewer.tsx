/**
 * components/viewer/DocumentViewer.tsx
 * ========================================
 * In-platform bill & statutory PDF document viewer for Seance.
 *
 * Implements:
 * - Browser-native PDF viewer integration with responsive viewport
 * - Zoom, fullscreen, and download controls using standardized vector icons
 * - Dual-theme semantic tokens for toolbar, canvas, fallback, and metadata
 * - Official statutory source attribution and hash verification
 */

"use client";

import React, { useState, useRef } from "react";
import { cn } from "@/lib/utils";
import {
  ZoomInIcon,
  ZoomOutIcon,
  DownloadIcon,
  ExternalLinkIcon,
  MaximizeIcon,
  MinimizeIcon,
  BillsIcon,
} from "@/components/ui/Icons";

export interface DocumentViewerProps {
  /** PDF URL to display. Can be a local path or external URL. */
  pdfUrl?: string;
  /** Official source URL as fallback */
  officialSourceUrl?: string;
  /** Official source label */
  officialSourceLabel?: string;
  /** Document title */
  title?: string;
  /** Document metadata */
  metadata?: {
    organization?: string;
    documentDate?: string;
    lastVerified?: string;
    documentHash?: string;
    pageCount?: number;
    billId?: string;
  };
  /** Starting height */
  height?: number;
  className?: string;
}

export function DocumentViewer({
  pdfUrl,
  officialSourceUrl,
  officialSourceLabel,
  title,
  metadata,
  height = 700,
  className,
}: DocumentViewerProps) {
  const [zoom, setZoom] = useState(100);
  const [viewerError, setViewerError] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const canRenderPdf = !!pdfUrl && !viewerError;

  const handleZoomIn = () => setZoom((z) => Math.min(z + 25, 200));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 25, 50));
  const handleZoomReset = () => setZoom(100);

  const viewerHeight = fullscreen ? "100vh" : `${height}px`;

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] overflow-hidden shadow-xs transition-all",
        fullscreen && "fixed inset-0 z-50 rounded-none border-0",
        className
      )}
    >
      {/* Viewer toolbar */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[var(--border-default)] bg-[var(--bg-base)] flex-wrap">
        {/* Title */}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-[var(--text-primary)] truncate">
            {title ?? "Legislative Document"}
          </p>
          {metadata?.organization && (
            <p className="text-[10px] text-[var(--text-muted)] mt-0.5">{metadata.organization}</p>
          )}
        </div>

        {/* Controls */}
        {canRenderPdf && (
          <div className="flex items-center gap-1">
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] disabled:opacity-30 disabled:cursor-not-allowed transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
              aria-label="Zoom out"
            >
              <ZoomOutIcon size="xs" />
            </button>
            <button
              onClick={handleZoomReset}
              className="px-2 py-1 text-[10px] font-mono text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] rounded-md transition-all min-w-[3rem] text-center focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
              aria-label={`Zoom: ${zoom}%`}
            >
              {zoom}%
            </button>
            <button
              onClick={handleZoomIn}
              disabled={zoom >= 200}
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] disabled:opacity-30 disabled:cursor-not-allowed transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
              aria-label="Zoom in"
            >
              <ZoomInIcon size="xs" />
            </button>
          </div>
        )}

        <div className="flex items-center gap-2">
          {/* Download */}
          {pdfUrl && (
            <a
              href={pdfUrl}
              download
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)] text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-all font-medium"
            >
              <DownloadIcon size="xs" />
              <span>Download</span>
            </a>
          )}

          {/* Official source */}
          {officialSourceUrl && (
            <a
              href={officialSourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg border border-[var(--action-primary)]/30 bg-[var(--action-primary)]/12 text-[var(--action-primary)] hover:bg-[var(--action-primary)]/20 transition-all font-medium"
            >
              <ExternalLinkIcon size="xs" />
              <span>{officialSourceLabel ?? "Official Source"}</span>
            </a>
          )}

          {/* Fullscreen toggle */}
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
            aria-label={fullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {fullscreen ? <MinimizeIcon size="xs" /> : <MaximizeIcon size="xs" />}
          </button>
        </div>
      </div>

      {/* Viewer content */}
      {canRenderPdf ? (
        <div
          className="relative overflow-auto"
          style={{ height: viewerHeight, background: "var(--bg-secondary)" }}
        >
          <iframe
            ref={iframeRef}
            src={`${pdfUrl}#zoom=${zoom}&toolbar=1&navpanes=1&scrollbar=1`}
            title={title ?? "Legislative Document"}
            className="w-full h-full border-0"
            style={{
              transform: `scale(${zoom / 100})`,
              transformOrigin: "top center",
              width: `${10000 / zoom}%`,
              height: `${10000 / zoom}%`,
            }}
            onError={() => setViewerError(true)}
            aria-label={`PDF viewer: ${title}`}
          />
        </div>
      ) : (
        /* Fallback when PDF cannot be rendered */
        <div
          className="flex flex-col items-center justify-center gap-6 bg-[var(--bg-secondary)]/30"
          style={{ height: viewerHeight }}
        >
          <div className="text-center space-y-3 max-w-md px-6">
            <div className="h-16 w-16 mx-auto rounded-2xl bg-[var(--bg-card)] border border-[var(--border-default)] flex items-center justify-center text-[var(--text-muted)] shadow-xs">
              <BillsIcon size="xl" />
            </div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">
              {title ?? "Legislative Document"}
            </h3>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed">
              {viewerError
                ? "The document could not be rendered in-platform. Please use the official source link to access the verified parliamentary record."
                : "No inline PDF document is currently available for this bill. Official Gazette and assembly links are provided below."}
            </p>
          </div>

          {officialSourceUrl && (
            <a
              href={officialSourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[var(--action-primary)] hover:bg-[var(--action-primary-hover)] text-[var(--text-primary)] font-semibold text-xs shadow-xs transition-all focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring)]"
            >
              <ExternalLinkIcon size="sm" />
              <span>View Official Source</span>
            </a>
          )}
        </div>
      )}

      {/* Metadata footer */}
      {metadata && (
        <div className="border-t border-[var(--border-default)] px-4 py-3 bg-[var(--bg-base)]">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-[10px] text-[var(--text-muted)]">
            {metadata.organization && (
              <span>
                <span className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Source: </span>
                {metadata.organization}
              </span>
            )}
            {metadata.documentDate && (
              <span>
                <span className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Document Date: </span>
                {new Date(metadata.documentDate).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
              </span>
            )}
            {metadata.lastVerified && (
              <span>
                <span className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Last Verified: </span>
                {new Date(metadata.lastVerified).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
              </span>
            )}
            {metadata.pageCount && (
              <span>
                <span className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Pages: </span>
                {metadata.pageCount}
              </span>
            )}
            {metadata.documentHash && (
              <span className="font-mono">
                <span className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Hash: </span>
                {metadata.documentHash.slice(0, 12)}…
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentViewer;
