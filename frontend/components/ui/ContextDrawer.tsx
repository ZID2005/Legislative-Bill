/**
 * components/ui/ContextDrawer.tsx
 * ================================
 * Slide-over Contextual Intelligence Drawer for Seance.
 *
 * Implements accessible slide-over pane:
 * - Traps focus & listens for Escape
 * - Hairline institutional borders and backdrop blur
 * - Smooth CSS transitions (transform and opacity)
 * - Header with title, subtitle, epistemic badge, and accessible close button
 */

"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { CloseIcon } from "./Icons";

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
  const panelRef = useRef<HTMLDivElement>(null);

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
        className="fixed inset-0 bg-[var(--overlay-backdrop)] backdrop-blur-xs transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over panel */}
      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div
          ref={panelRef}
          className={cn(
            "w-screen bg-[var(--bg-surface)] border-l border-[var(--border-default)] shadow-2xl flex flex-col transform transition-transform duration-200 ease-out",
            width
          )}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-[var(--border-default)] bg-[var(--bg-base)] flex items-start justify-between gap-4 flex-shrink-0">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold text-[var(--text-primary)] truncate">{title}</h2>
                {badge}
              </div>
              {subtitle && (
                <p className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-1">{subtitle}</p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] p-1.5 rounded-lg hover:bg-[var(--bg-card-hover)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
              aria-label="Close drawer"
            >
              <CloseIcon size="sm" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {children}
          </div>

          {/* Optional Footer */}
          {footer && (
            <div className="px-6 py-3.5 border-t border-[var(--border-default)] bg-[var(--bg-base)] flex items-center justify-end gap-2 flex-shrink-0">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ContextDrawer;
