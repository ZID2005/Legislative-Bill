/**
 * components/ui/Pagination.tsx
 * ============================
 * Institutional pagination controls for paginated API responses.
 * Uses semantic dual-theme tokens and vector navigation chevrons.
 */

import React from "react";
import { cn } from "@/lib/utils";
import { ChevronLeftIcon, ChevronRightIcon } from "./Icons";

export interface PaginationProps {
  page: number;
  pages: number;
  total: number;
  limit: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({
  page,
  pages,
  total,
  limit,
  onPageChange,
  className,
}: PaginationProps) {
  if (pages <= 1) return null;

  const start = (page - 1) * limit + 1;
  const end = Math.min(page * limit, total);

  return (
    <div
      className={cn(
        "flex items-center justify-between text-xs text-[var(--text-muted)] select-none",
        className
      )}
    >
      <p>
        Showing{" "}
        <span className="font-semibold text-[var(--text-primary)] font-mono">
          {new Intl.NumberFormat("en-IN").format(start)}–
          {new Intl.NumberFormat("en-IN").format(end)}
        </span>{" "}
        of{" "}
        <span className="font-semibold text-[var(--text-primary)] font-mono">
          {new Intl.NumberFormat("en-IN").format(total)}
        </span>{" "}
        records
      </p>

      <div className="flex items-center gap-1.5" role="navigation" aria-label="Pagination">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          aria-label="Previous page"
          className={cn(
            "inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]",
            page === 1
              ? "border-[var(--border-subtle)] text-[var(--text-faint)] opacity-40 cursor-not-allowed bg-transparent"
              : "border-[var(--border-default)] text-[var(--text-primary)] bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] hover:border-[var(--border-strong)] active:translate-y-[0.5px]"
          )}
        >
          <ChevronLeftIcon size="xs" />
          <span>Prev</span>
        </button>

        <span className="px-2.5 py-1 text-[var(--text-muted)] font-mono text-xs">
          {page} / {pages}
        </span>

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === pages}
          aria-label="Next page"
          className={cn(
            "inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]",
            page === pages
              ? "border-[var(--border-subtle)] text-[var(--text-faint)] opacity-40 cursor-not-allowed bg-transparent"
              : "border-[var(--border-default)] text-[var(--text-primary)] bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] hover:border-[var(--border-strong)] active:translate-y-[0.5px]"
          )}
        >
          <span>Next</span>
          <ChevronRightIcon size="xs" />
        </button>
      </div>
    </div>
  );
}

export default Pagination;
