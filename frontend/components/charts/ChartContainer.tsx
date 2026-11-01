/**
 * components/charts/ChartContainer.tsx
 * =====================================
 * Standard Institutional Chart Wrapper Container for Seance.
 *
 * Implements:
 * - Dual-theme surface, border, and typography tokens.
 * - Epistemic classification headers ([OBSERVED], [PREDICTION], [DERIVED], etc.).
 * - Non-color legend markers (solid/dash line types, symbols, glyphs).
 * - Empty, loading, and error state transitions.
 * - Bounded positioning context for floating tooltips.
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { Skeleton } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";

export interface LegendItem {
  label: string;
  color: string;
  lineStyle?: "solid" | "dashed" | "dotted";
  markerShape?: "circle" | "diamond" | "square";
  description?: string;
}

export interface ChartContainerProps {
  title: string;
  subtitle?: string;
  epistemicTier?: "FACT" | "OBSERVED" | "DERIVED" | "INTERPRETATION" | "PREDICTION" | "EVIDENCE";
  legendItems?: LegendItem[];
  headerRight?: React.ReactNode;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  empty?: boolean;
  emptyMessage?: string;
  className?: string;
  children: React.ReactNode;
  id?: string;
  "aria-label"?: string;
}

export function ChartContainer({
  title,
  subtitle,
  epistemicTier,
  legendItems,
  headerRight,
  loading = false,
  error = null,
  onRetry,
  empty = false,
  emptyMessage = "No econometric data available for this selection.",
  className,
  children,
  id,
  "aria-label": ariaLabel,
}: ChartContainerProps) {
  return (
    <Card
      id={id}
      className={cn(
        "relative overflow-hidden border-[var(--chart-border)] bg-[var(--bg-surface)] transition-colors",
        className
      )}
      role="figure"
      aria-label={ariaLabel || title}
    >
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 w-full border-b border-[var(--border-subtle)] pb-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-sm font-bold tracking-tight text-[var(--text-primary)]">
                {title}
              </CardTitle>
              {epistemicTier && <EpistemicBadge type={epistemicTier} size="xs" />}
            </div>
            {subtitle && (
              <p className="text-xs text-[var(--text-muted)] mt-0.5 leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {headerRight}
          </div>
        </div>
      </CardHeader>

      {/* Legend bar if items present */}
      {legendItems && legendItems.length > 0 && (
        <div className="flex flex-wrap items-center gap-4 px-5 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)] text-[11px] text-[var(--text-secondary)]">
          <span className="text-[10px] uppercase tracking-wider font-semibold text-[var(--text-muted)]">
            Legend:
          </span>
          {legendItems.map((item, idx) => (
            <div key={idx} className="flex items-center gap-1.5" title={item.description}>
              {/* Visual marker */}
              <span className="flex items-center justify-center h-3 w-4" aria-hidden="true">
                {item.lineStyle === "dashed" ? (
                  <span
                    className="inline-block w-4 h-0.5 border-t-2 border-dashed"
                    style={{ borderColor: item.color }}
                  />
                ) : item.markerShape === "diamond" ? (
                  <span
                    className="inline-block h-2 w-2 rotate-45"
                    style={{ backgroundColor: item.color }}
                  />
                ) : (
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                )}
              </span>
              <span className="font-medium text-[var(--text-secondary)]">{item.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Main Chart Body State Machine */}
      <div className="relative p-5">
        {loading ? (
          <div className="space-y-3 py-6" aria-label="Loading chart data">
            <Skeleton className="h-6 w-1/4" />
            <Skeleton className="h-48 w-full" />
            <div className="flex justify-between pt-2">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-16" />
            </div>
          </div>
        ) : error ? (
          <div className="py-12 text-center space-y-3" role="alert">
            <span className="text-2xl" aria-hidden="true">⚠️</span>
            <p className="text-xs text-[var(--color-danger)] font-medium max-w-md mx-auto">
              {error}
            </p>
            {onRetry && (
              <Button variant="outline" size="xs" onClick={onRetry}>
                Retry Loading
              </Button>
            )}
          </div>
        ) : empty ? (
          <div className="py-12 text-center space-y-2">
            <span className="text-2xl text-[var(--text-muted)]" aria-hidden="true">📊</span>
            <p className="text-xs text-[var(--text-muted)] font-medium">
              {emptyMessage}
            </p>
          </div>
        ) : (
          children
        )}
      </div>
    </Card>
  );
}

export default ChartContainer;
