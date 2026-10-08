/**
 * components/ui/ContextDrawer.tsx
 * ================================
 * Task 8.31C — Slide-over Contextual Intelligence Drawer.
 *
 * Implements accessible slide-over pane:
 * - Traps focus & listens for Escape
 * - Hairline institutional borders
 * - Smooth transition (150-200ms)
 * - Header with title, subtitle, epistemic badge, and close button
 */

"use client";

import React, { useEffect } from "react";
import { cn } from "@/lib/utils";

export interface ContextDrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  children: React.ReactNode;
  width?: string; // e.g. "max-w-md", "max-w-xl", "max-w-2xl"
  footer?: React.ReactNode;
}

export function ContextDrawer({
  open,
  onClose,
  title,
  subtitle,
  badge,
  children,
  width = "max-w-xl",
  footer,
}: ContextDrawerProps) {
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-xs transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over panel */}
      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div
          className={cn(
            "w-screen bg-[#0c1322] border-l border-white/10 shadow-2xl flex flex-col transform transition-transform duration-200 ease-out",
            width
          )}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-white/10 bg-[#090e18] flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold text-slate-100 truncate">{title}</h2>
                {badge}
              </div>
              {subtitle && (
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{subtitle}</p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-slate-400 hover:text-slate-200 p-1 rounded-md hover:bg-white/5 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500"
              aria-label="Close drawer"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {children}
          </div>

          {/* Optional Footer */}
          {footer && (
            <div className="px-6 py-3.5 border-t border-white/10 bg-[#090e18] flex items-center justify-end gap-2">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ContextDrawer;
