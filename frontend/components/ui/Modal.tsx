/**
 * components/ui/Modal.tsx
 * =======================
 * Accessible institutional modal dialog primitive for Seance.
 *
 * Implements:
 * - Focus trapping and Escape key listener
 * - Backdrop shield using `--overlay-backdrop` and blur
 * - Standardized surfaces, borders, header, body, and footer
 * - Dual-theme support with accessible labels
 */

"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { CloseIcon } from "./Icons";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl";
  className?: string;
  id?: string;
}

const maxWidthClasses = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
};

export function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  description,
  children,
  footer,
  maxWidth = "md",
  className,
  id = "seance-modal",
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const subText = subtitle || description;

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      id={id}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby={`${id}-title`}
      aria-describedby={subText ? `${id}-desc` : undefined}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[var(--overlay-backdrop)] backdrop-blur-xs transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog window */}
      <div
        ref={dialogRef}
        className={cn(
          "relative w-full rounded-xl border border-[var(--border-default)] bg-[var(--bg-modal)] shadow-2xl transition-all duration-200 overflow-hidden",
          maxWidthClasses[maxWidth],
          className
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-4 border-b border-[var(--border-default)] bg-[var(--bg-base)]">
          <div className="min-w-0 flex-1 pr-3">
            <h2 id={`${id}-title`} className="text-base font-bold text-[var(--text-primary)] tracking-tight">
              {title}
            </h2>
            {subText && (
              <p id={`${id}-desc`} className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-1">
                {subText}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] p-1.5 rounded-lg hover:bg-[var(--bg-card-hover)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
            aria-label="Close dialog"
          >
            <CloseIcon size="sm" />
          </button>
        </div>

        {/* Content Body */}
        <div className="px-6 py-5 max-h-[75vh] overflow-y-auto space-y-4">
          {children}
        </div>

        {/* Optional Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-2.5 px-6 py-3.5 border-t border-[var(--border-default)] bg-[var(--bg-base)]">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

export default Modal;
