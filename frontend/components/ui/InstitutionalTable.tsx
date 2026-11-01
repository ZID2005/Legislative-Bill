/**
 * components/ui/InstitutionalTable.tsx
 * =====================================
 * Institutional High-Density Data Table for Seance.
 *
 * Implements FactSet/Bloomberg-grade density & rigor:
 * - Sticky header with hairline precision separator
 * - Tabular monospace numbers for all quantitative metrics
 * - Sortable columns with vector indicators and aria-sort
 * - Interactive row selection, keyboard accessibility & hover states
 * - Dual responsive handling and theme-aware borders
 */

"use client";

import React, { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { ArrowUpIcon, ArrowDownIcon, ArrowUpDownIcon } from "./Icons";

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
  keyExtractor?: (item: T, index: number) => string | number;
  compact?: boolean;
  density?: "dense" | "compact" | "normal";
  striped?: boolean;
  stickyHeader?: boolean;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  selectedKey?: string | number | null;
  className?: string;
  caption?: string;
  defaultSortKey?: string;
  defaultSortDirection?: "asc" | "desc";
  id?: string;
}

export function InstitutionalTable<T extends Record<string, any>>({
  columns,
  data,
  keyExtractor,
  compact = true,
  density,
  striped = true,
  stickyHeader = true,
  emptyMessage = "No matching records found.",
  onRowClick,
  selectedKey,
  className,
  caption,
  defaultSortKey,
  defaultSortDirection = "desc",
  id,
}: InstitutionalTableProps<T>) {
  // Resolve effective density: density prop takes precedence over compact boolean
  const effectiveDensity = density || (compact ? "compact" : "normal");
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

  const sortedData = useMemo(() => {
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
    <div
      id={id}
      className={cn(
        "w-full overflow-x-auto rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] shadow-xs transition-colors",
        className
      )}
    >
      <table className="w-full text-left border-collapse" role="table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr
            className={cn(
              "border-b border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--text-muted)] font-semibold uppercase tracking-wider text-[10px]",
              stickyHeader && "sticky top-0 z-10 backdrop-blur-xs"
            )}
          >
            {columns.map((col) => {
              const isCurrentSort = sortKey === col.key;
              const ariaSort = isCurrentSort
                ? sortDirection === "asc"
                  ? "ascending"
                  : "descending"
                : col.sortable
                ? "none"
                : undefined;

              return (
                <th
                  key={col.key}
                  scope="col"
                  aria-sort={ariaSort}
                  style={{ width: col.width }}
                  onClick={() => handleHeaderClick(col)}
                  className={cn(
                    effectiveDensity === "dense"
                      ? "py-1.5 px-3 text-[10px]"
                      : effectiveDensity === "normal"
                      ? "py-3 px-3.5 text-xs"
                      : "py-2.5 px-3.5 text-[10px]",
                    "select-none transition-colors",
                    col.align === "right" || col.isNumeric
                      ? "text-right"
                      : col.align === "center"
                      ? "text-center"
                      : "text-left",
                    col.sortable &&
                      "cursor-pointer hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                  )}
                >
                  <div
                    className={cn(
                      "inline-flex items-center gap-1.5",
                      (col.align === "right" || col.isNumeric) && "justify-end"
                    )}
                  >
                    <span>{col.header}</span>
                    {col.sortable && (
                      <span className="text-[var(--text-muted)] inline-flex items-center" aria-hidden="true">
                        {isCurrentSort ? (
                          sortDirection === "asc" ? (
                            <ArrowUpIcon size="xs" className="text-[var(--action-primary)]" />
                          ) : (
                            <ArrowDownIcon size="xs" className="text-[var(--action-primary)]" />
                          )
                        ) : (
                          <ArrowUpDownIcon size="xs" className="opacity-40" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--border-subtle)]">
          {sortedData.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="py-10 text-center text-xs text-[var(--text-muted)] italic bg-[var(--bg-surface)]"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sortedData.map((item, index) => {
              const key = keyExtractor ? keyExtractor(item, index) : (item.id ?? item.key ?? index);
              const isEven = index % 2 === 0;
              const isSelected = selectedKey !== undefined && selectedKey !== null && selectedKey === key;

              return (
                <tr
                  key={key}
                  onClick={() => onRowClick && onRowClick(item)}
                  tabIndex={onRowClick ? 0 : undefined}
                  onKeyDown={
                    onRowClick
                      ? (e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            onRowClick(item);
                          }
                        }
                      : undefined
                  }
                  className={cn(
                    "transition-colors duration-100",
                    isSelected
                      ? "bg-[var(--action-primary)]/10 border-l-2 border-l-[var(--action-primary)]"
                      : striped && !isEven
                      ? "bg-[var(--bg-secondary)]/40"
                      : "bg-[var(--bg-surface)]",
                    onRowClick
                      ? "cursor-pointer hover:bg-[var(--bg-card-hover)] focus-visible:bg-[var(--bg-card-hover)] focus-visible:outline-none"
                      : "hover:bg-[var(--table-row-hover)]"
                  )}
                >
                  {columns.map((col) => {
                    const value = item[col.key];
                    const content = col.render ? col.render(item, index) : value;
                    return (
                      <td
                        key={col.key}
                        className={cn(
                          effectiveDensity === "dense"
                            ? "py-1.5 px-3 text-[11px]"
                            : effectiveDensity === "normal"
                            ? "py-3.5 px-3.5 text-sm"
                            : "py-2.5 px-3.5 text-xs",
                          col.isNumeric
                            ? "font-mono font-tabular tabular-nums text-[var(--text-primary)] text-right"
                            : "text-[var(--text-secondary)]",
                          col.align === "right" || col.isNumeric
                            ? "text-right"
                            : col.align === "center"
                            ? "text-center"
                            : "text-left"
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
