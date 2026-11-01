/**
 * components/charts/HorizonComparisonVisualizer.tsx
 * ==================================================
 * Interactive Multi-Horizon Comparison Matrix for Seance.
 *
 * Implements:
 * - Dual-theme semantic CSS tokens.
 * - Strict distinction between Authoritative 5 horizons and Unmodeled experimental horizons.
 * - Tabular numerals on all probabilities, risk scores, and directional percentages.
 * - Accessible keyboard navigation and non-color glyph indicators.
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Badge, PredictionBadge } from "@/components/ui/Badge";
import { formatProbability, formatRiskScore, formatEventWindow } from "@/lib/formatters";
import type { HorizonComparisonItem } from "@/types/api";

export interface HorizonComparisonVisualizerProps {
  comparisons: HorizonComparisonItem[];
  currentWindow?: string;
  onSelectWindow?: (window: string) => void;
  unmodeledNote?: string;
  className?: string;
}

export function HorizonComparisonVisualizer({
  comparisons,
  currentWindow,
  onSelectWindow,
  unmodeledNote = "Horizon not part of frozen 5-window production baseline",
  className,
}: HorizonComparisonVisualizerProps) {
  const [internalWin, setInternalWin] = useState<string>(
    currentWindow || comparisons[0]?.event_window || "[-1,+1]"
  );
  const selectedWin = currentWindow || internalWin;

  const handleSelect = (win: string) => {
    setInternalWin(win);
    if (onSelectWindow) onSelectWindow(win);
  };

  const activeItem = comparisons.find((c) => c.event_window === selectedWin);

  return (
    <div className={cn("space-y-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-5", className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-3">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
            <span>⏱</span> Event Horizons Evaluation Matrix
          </h4>
          <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
            Compare model sensitivity and statistical movement across temporal event horizons.
          </p>
        </div>
        <span className="text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-secondary)] px-2 py-0.5 rounded border border-[var(--border-subtle)]">
          5 Authoritative Horizons
        </span>
      </div>

      {/* Horizon Pill Selector Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2" role="tablist" aria-label="Event horizon selection">
        {comparisons.map((item) => {
          const isSelected = selectedWin === item.event_window;
          const isCurrent = currentWindow === item.event_window;

          return (
            <button
              key={item.event_window}
              type="button"
              role="tab"
              aria-selected={isSelected}
              onClick={() => handleSelect(item.event_window)}
              className={cn(
                "group relative flex flex-col items-center justify-center p-2 rounded-lg border text-center transition-all",
                isSelected
                  ? "border-[var(--action-primary)] bg-[var(--action-primary)]/10 ring-1 ring-[var(--action-primary)]"
                  : item.is_modeled
                  ? "border-[var(--border-default)] bg-[var(--bg-secondary)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)]"
                  : "border-[var(--border-subtle)] bg-[var(--bg-base)]/50 opacity-60 hover:opacity-90"
              )}
            >
              <span className="font-mono text-xs font-bold text-[var(--text-primary)]">
                {formatEventWindow(item.event_window)}
              </span>

              {item.is_modeled ? (
                <div className="mt-1 flex flex-col items-center gap-0.5">
                  <span
                    className={cn(
                      "text-[10px] font-semibold uppercase",
                      item.predicted_direction === "POSITIVE"
                        ? "text-[var(--color-positive)]"
                        : item.predicted_direction === "NEGATIVE"
                        ? "text-[var(--color-negative)]"
                        : "text-[var(--text-muted)]"
                    )}
                  >
                    {item.predicted_direction || "NEUTRAL"}
                  </span>
                  {item.predicted_market_moving && (
                    <span className="text-[9px] text-[var(--color-warning)] font-bold">
                      ⚡ Mkt-Moving
                    </span>
                  )}
                </div>
              ) : (
                <span className="text-[9px] text-[var(--text-faint)] mt-1 font-mono">
                  Unmodeled
                </span>
              )}

              {isCurrent && (
                <span className="absolute -top-1.5 -right-1 text-[8px] font-bold bg-[var(--action-primary)] text-[var(--text-primary)] px-1 rounded-full">
                  active
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Horizon Detail Card */}
      {activeItem && (
        <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-4 transition-all">
          {activeItem.is_modeled ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Direction & Impact */}
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] tracking-wider">
                  Direction & Probability
                </span>
                <div className="flex items-center gap-2 mt-1">
                  <PredictionBadge direction={activeItem.predicted_direction || "NEUTRAL"} size="sm" />
                </div>
                {activeItem.direction_probability && (
                  <div className="space-y-0.5 pt-2 text-[10px] font-mono text-[var(--text-secondary)]">
                    {Object.entries(activeItem.direction_probability).map(([dir, prob]) => (
                      <div key={dir} className="flex justify-between">
                        <span className="text-[var(--text-muted)]">{dir}:</span>
                        <span className="font-semibold tabular-nums">
                          {formatProbability(prob as number)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Market-Moving Likelihood */}
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] tracking-wider">
                  Market-Moving Likelihood
                </span>
                <p className="text-xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                  {formatProbability(activeItem.market_moving_probability)}
                </p>
                <Badge
                  variant={activeItem.predicted_market_moving ? "warning" : "default"}
                  size="xs"
                  className="mt-1"
                >
                  {activeItem.predicted_market_moving ? "Market-Moving Signal" : "Subdued Movement"}
                </Badge>
              </div>

              {/* Quantitative Impact Score */}
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] tracking-wider">
                  Impact Score
                </span>
                <p className="text-xl font-bold font-mono tabular-nums text-[var(--text-primary)] mt-1">
                  {formatRiskScore(activeItem.impact_score, 2)}
                </p>
                <span className="text-[10px] text-[var(--text-muted)] block">
                  Deterministic regression magnitude
                </span>
              </div>

              {/* Composite Decision Risk */}
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] tracking-wider">
                  Decision Risk Score
                </span>
                <p className="text-xl font-bold font-mono tabular-nums text-[var(--color-warning)] mt-1">
                  {formatRiskScore(activeItem.risk_score, 2)}
                </p>
                <span className="text-[10px] text-[var(--text-muted)] block">
                  Cross-sectional risk weighting
                </span>
              </div>
            </div>
          ) : (
            <div className="p-3 text-xs text-[var(--color-warning)] space-y-1">
              <p className="font-semibold flex items-center gap-1.5">
                <span>ℹ️</span> Horizon {activeItem.event_window} is not modeled in the validated dataset
              </p>
              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                {activeItem.note || unmodeledNote}. The 5 authoritative event windows are [-1,+1], [-3,+3], [-5,+5], [-5,+10], and [-10,+10].
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default HorizonComparisonVisualizer;
