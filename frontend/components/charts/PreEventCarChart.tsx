/**
 * components/charts/PreEventCarChart.tsx
 * =======================================
 * Pre-Event Trading Windows CAR & MAR Statistics Visualizer for Seance.
 *
 * Implements:
 * - Dual-theme semantic CSS tokens (--color-positive, --color-negative, --chart-grid).
 * - Standardized Cumulative Abnormal Return (CAR) and Mean Abnormal Return (MAR) metrics.
 * - Tabular numerals on observation counts, significant pairs, and returns.
 * - Epistemic classification badge [DERIVED].
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { formatCAR, formatMAR, formatInteger, getDirectionGlyph } from "@/lib/formatters";
import type { PreEventWindowSummary } from "@/types/api";

export interface PreEventCarChartProps {
  windowSummaries: PreEventWindowSummary[];
  className?: string;
  onWindowClick?: (window: string) => void;
}

export function PreEventCarChart({
  windowSummaries,
  className,
  onWindowClick,
}: PreEventCarChartProps) {
  if (!windowSummaries || windowSummaries.length === 0) {
    return (
      <div className="p-8 text-center text-xs text-[var(--text-muted)] italic">
        No pre-event trading window CAR observations recorded.
      </div>
    );
  }

  return (
    <div className={cn("grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3", className)}>
      {windowSummaries.map((ws) => {
        const isPos = ws.mean_car > 0;
        const isNeg = ws.mean_car < 0;

        return (
          <Card
            key={ws.window}
            className="p-4 bg-[var(--bg-surface)] border-[var(--border-default)] transition-all hover:border-[var(--border-strong)] hover:shadow-xs space-y-2.5 cursor-pointer"
            onClick={() => onWindowClick && onWindowClick(ws.window)}
            role="button"
            tabIndex={0}
            aria-label={`Window ${ws.window}: Mean CAR ${formatCAR(ws.mean_car)}, ${ws.observation_count} observations`}
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <span className="font-mono font-bold text-xs px-2 py-0.5 rounded border border-[var(--color-model)]/30 bg-[var(--color-model)]/10 text-[var(--color-model)]">
                {ws.window}
              </span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono tabular-nums">
                {formatInteger(ws.observation_count)} obs
              </span>
            </div>

            {/* Metrics */}
            <div className="space-y-1.5 text-xs pt-1">
              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)]">Mean CAR:</span>
                <span
                  className={cn(
                    "font-mono font-bold tabular-nums flex items-center gap-1",
                    isPos
                      ? "text-[var(--color-positive)]"
                      : isNeg
                      ? "text-[var(--color-negative)]"
                      : "text-[var(--text-secondary)]"
                  )}
                >
                  <span className="text-[9px]" aria-hidden="true">
                    {getDirectionGlyph(ws.mean_car)}
                  </span>
                  <span>{formatCAR(ws.mean_car)}</span>
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)]">Mean MAR:</span>
                <span className="font-mono tabular-nums text-[var(--text-secondary)]">
                  {formatMAR(ws.mean_mar)}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)]">Sig. Pairs:</span>
                <span className="font-mono font-semibold tabular-nums text-[var(--color-warning)]">
                  {formatInteger(ws.significant_pairs_count)}
                </span>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

export default PreEventCarChart;
