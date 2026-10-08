/**
 * components/ui/InstitutionalTable.tsx
 * =====================================
 * Task 8.31C — Institutional High-Density Data Table.
 *
 * Implements FactSet/Bloomberg-grade density:
 * - Sticky header with hairline precision separator
 * - Tabular monospace numbers for all quantitative metrics
 * - Sortable columns with visual indicators
 * - Interactive row selection & hover states
 * - Dual responsive handling
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

export interface TableColumn<T> {
  key: string;
  header: string;
  align?: "left" | "center" | "right";
  width?: string;
  sortable?: boolean;
  isNumeric?: boolean;
  render?: (item: T, index: number) => React.ReactNode;
}

export interface InstitutionalTableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  keyExtractor: (item: T, index: number) => string | number;
  compact?: boolean;
  striped?: boolean;
  stickyHeader?: boolean;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  className?: string;
  caption?: string;
  defaultSortKey?: string;
  defaultSortDirection?: "asc" | "desc";
}

export function InstitutionalTable<T extends Record<string, any>>({
  columns,
  data,
  keyExtractor,
  compact = true,
  striped = true,
  stickyHeader = true,
  emptyMessage = "No matching records found.",
  onRowClick,
  className,
  caption,
  defaultSortKey,
  defaultSortDirection = "desc",
}: InstitutionalTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | undefined>(defaultSortKey);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">(defaultSortDirection);

  const handleHeaderClick = (col: TableColumn<T>) => {
    if (!col.sortable) return;
    if (sortKey === col.key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(col.key);
      setSortDirection("desc");
    }
  };

  const sortedData = React.useMemo(() => {
    if (!sortKey) return data;
    return [...data].sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      let comparison = 0;
      if (typeof valA === "number" && typeof valB === "number") {
        comparison = valA - valB;
      } else {
        comparison = String(valA).localeCompare(String(valB));
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [data, sortKey, sortDirection]);

  return (
    <div className={cn("w-full overflow-x-auto rounded-lg border border-white/10 bg-[#0c1322]", className)}>
      <table className="w-full text-left border-collapse" role="table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr
            className={cn(
              "border-b border-white/10 bg-[#090e18] text-slate-400 font-semibold uppercase tracking-wider text-[10px]",
              stickyHeader && "sticky top-0 z-10"
            )}
          >
            {columns.map((col) => {
              const isCurrentSort = sortKey === col.key;
              return (
                <th
                  key={col.key}
                  scope="col"
                  style={{ width: col.width }}
                  onClick={() => handleHeaderClick(col)}
                  className={cn(
                    "py-2.5 px-3 select-none",
                    col.align === "right" || col.isNumeric ? "text-right" : col.align === "center" ? "text-center" : "text-left",
                    col.sortable && "cursor-pointer hover:text-slate-200 transition-colors"
                  )}
                >
                  <div className={cn(
                    "inline-flex items-center gap-1.5",
                    (col.align === "right" || col.isNumeric) && "justify-end"
                  )}>
                    <span>{col.header}</span>
                    {col.sortable && (
                      <span className="text-[9px] text-slate-500">
                        {isCurrentSort ? (sortDirection === "asc" ? "▲" : "▼") : "⇅"}
                      </span>
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {sortedData.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="py-8 text-center text-xs text-slate-500 italic bg-[#0c1322]"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sortedData.map((item, index) => {
              const key = keyExtractor(item, index);
              const isEven = index % 2 === 0;
              return (
                <tr
                  key={key}
                  onClick={() => onRowClick && onRowClick(item)}
                  className={cn(
                    "transition-colors duration-100",
                    striped && !isEven ? "bg-[#090e18]/40" : "bg-[#0c1322]",
                    onRowClick ? "cursor-pointer hover:bg-[#121b2f]" : "hover:bg-white/[0.02]"
                  )}
                >
                  {columns.map((col) => {
                    const value = item[col.key];
                    const content = col.render ? col.render(item, index) : value;
                    return (
                      <td
                        key={col.key}
                        className={cn(
                          compact ? "py-2 px-3 text-xs" : "py-3 px-3 text-sm",
                          col.isNumeric ? "font-mono tabular-nums text-slate-200 text-right" : "text-slate-300",
                          col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"
                        )}
                      >
                        {content ?? "—"}
                      </td>
                    );
                  })}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

export default InstitutionalTable;
