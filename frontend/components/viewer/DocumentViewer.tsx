/**
 * components/viewer/DocumentViewer.tsx
 * ========================================
 * Task 8.25 — In-platform bill/PDF document viewer (Phase 11).
 *
 * Option A: PDF rendered inline via native browser PDF support (iframe/embed)
 * Option B: Fallback to "View Official Source" button
 *
 * Features:
 * - PDF viewer (browser-native)
 * - Page navigation
 * - Zoom controls
 * - Document metadata
 * - Source attribution
 * - Download option
 * - Official source fallback
 */

"use client";

import React, { useState, useRef } from "react";
import { cn } from "@/lib/utils";

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
        "card-base overflow-hidden",
        fullscreen && "fixed inset-0 z-50 rounded-none",
        className
      )}
    >
      {/* Viewer toolbar */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/8 bg-slate-900/60 flex-wrap">
        {/* Title */}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-slate-300 truncate">
            {title ?? "Legislative Document"}
          </p>
          {metadata?.organization && (
            <p className="text-[10px] text-slate-600">{metadata.organization}</p>
          )}
        </div>

        {/* Controls */}
        {canRenderPdf && (
          <div className="flex items-center gap-1">
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              aria-label="Zoom out"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
              </svg>
            </button>
            <button
              onClick={handleZoomReset}
              className="px-2 py-1 text-[10px] font-mono text-slate-400 hover:text-white hover:bg-white/5 rounded transition-all min-w-[3rem] text-center"
              aria-label={`Zoom: ${zoom}%`}
            >
              {zoom}%
            </button>
            <button
              onClick={handleZoomIn}
              disabled={zoom >= 200}
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              aria-label="Zoom in"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16M4 12h16" />
              </svg>
            </button>
          </div>
        )}

        <div className="flex items-center gap-1.5">
          {/* Download */}
          {pdfUrl && (
            <a
              href={pdfUrl}
              download
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg border border-white/8 text-slate-400 hover:text-white hover:bg-white/5 transition-all"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </a>
          )}

          {/* Official source */}
          {officialSourceUrl && (
            <a
              href={officialSourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg border border-blue-500/25 bg-blue-500/10 text-blue-400 hover:text-blue-300 hover:bg-blue-500/15 transition-all"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              {officialSourceLabel ?? "Official Source"}
            </a>
          )}

          {/* Fullscreen toggle */}
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="p-1.5 rounded text-slate-500 hover:text-white hover:bg-white/5 transition-all"
            aria-label={fullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {fullscreen ? (
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3" />
              </svg>
            ) : (
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Viewer content */}
      {canRenderPdf ? (
        <div
          className="relative overflow-auto"
          style={{ height: viewerHeight, background: "#1a2032" }}
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
          className="flex flex-col items-center justify-center gap-6 bg-slate-950/50"
          style={{ height: viewerHeight }}
        >
          <div className="text-center space-y-3 max-w-md px-6">
            <div className="h-16 w-16 mx-auto rounded-2xl bg-white/5 border border-white/8 flex items-center justify-center text-3xl">
              📄
            </div>
            <h3 className="text-base font-semibold text-slate-200">
              {title ?? "Legislative Document"}
            </h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              {viewerError
                ? "The document could not be rendered in-platform. Please use the official source to read the full text."
                : "No PDF document is currently available for this bill. Please use the official source link."}
            </p>
          </div>

          {officialSourceUrl && (
            <a
              href={officialSourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2.5 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              View Official Source
            </a>
          )}
        </div>
      )}

      {/* Metadata footer */}
      {metadata && (
        <div className="border-t border-white/8 px-4 py-3 bg-slate-900/40">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-[10px] text-slate-600">
            {metadata.organization && (
              <span>
                <span className="text-slate-700 uppercase tracking-wider">Source: </span>
                {metadata.organization}
              </span>
            )}
            {metadata.documentDate && (
              <span>
                <span className="text-slate-700 uppercase tracking-wider">Document Date: </span>
                {new Date(metadata.documentDate).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
              </span>
            )}
            {metadata.lastVerified && (
              <span>
                <span className="text-slate-700 uppercase tracking-wider">Last Verified: </span>
                {new Date(metadata.lastVerified).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
              </span>
            )}
            {metadata.pageCount && (
              <span>
                <span className="text-slate-700 uppercase tracking-wider">Pages: </span>
                {metadata.pageCount}
              </span>
            )}
            {metadata.documentHash && (
              <span className="font-mono">
                <span className="text-slate-700 uppercase tracking-wider">Hash: </span>
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
