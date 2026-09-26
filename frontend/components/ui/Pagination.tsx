/**
 * components/ui/Pagination.tsx
 * ============================
 * Pagination controls for paginated API responses.
 */

import React from "react";
import { cn } from "@/lib/utils";

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
        "flex items-center justify-between text-sm text-slate-400",
        className
      )}
    >
      <p>
        Showing{" "}
        <span className="font-medium text-slate-300">
          {new Intl.NumberFormat("en-IN").format(start)}–
          {new Intl.NumberFormat("en-IN").format(end)}
        </span>{" "}
        of{" "}
        <span className="font-medium text-slate-300">
          {new Intl.NumberFormat("en-IN").format(total)}
        </span>
      </p>

      <div className="flex items-center gap-1" role="navigation" aria-label="Pagination">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          aria-label="Previous page"
          className={cn(
            "px-2.5 py-1.5 rounded border text-xs font-medium transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
            page === 1
              ? "border-slate-800 text-slate-600 cursor-not-allowed"
              : "border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600"
          )}
        >
          ← Prev
        </button>

        <span className="px-3 py-1.5 text-slate-400 text-xs">
          {page} / {pages}
        </span>

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === pages}
          aria-label="Next page"
          className={cn(
            "px-2.5 py-1.5 rounded border text-xs font-medium transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
            page === pages
              ? "border-slate-800 text-slate-600 cursor-not-allowed"
              : "border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600"
          )}
        >
          Next →
        </button>
      </div>
    </div>
  );
}

export default Pagination;
