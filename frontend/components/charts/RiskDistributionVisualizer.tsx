/**
 * components/charts/RiskDistributionVisualizer.tsx
 * =================================================
 * Dual-Theme 5-Tier Deterministic Risk Model Visualizer for Seance.
 *
 * Implements:
 * - Semantic CSS custom properties for all risk bands.
 * - Interactive proportional stacked distribution bar with accessible tooltips.
 * - Tabular numerals on all decision counts and percentages.
 * - Dual-theme calibrated light and dark surfaces.
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { formatInteger, formatPercent } from "@/lib/formatters";
import { ChartTooltip } from "./ChartTooltip";
import type { RiskBandDistribution } from "@/types/api";

export interface RiskDistributionVisualizerProps {
  distribution: Record<string, number> | RiskBandDistribution;
  totalDecisions: number;
  avgOverallRisk?: number;
  className?: string;
  onBandSelect?: (band: string) => void;
}

export const RISK_BAND_METADATA = [
  {
    band: "VERY_LOW",
    label: "Very Low Risk",
    range: "0.00 – 0.20",
    color: "var(--color-positive)",
    surface: "var(--color-positive)/10",
    border: "var(--color-positive)/25",
  },
  {
    band: "LOW",
    label: "Low Risk",
    range: "0.20 – 0.40",
    color: "var(--color-info)",
    surface: "var(--color-info)/10",
    border: "var(--color-info)/25",
  },
  {
    band: "MODERATE",
    label: "Moderate Risk",
    range: "0.40 – 0.60",
    color: "var(--color-warning)",
    surface: "var(--color-warning)/10",
    border: "var(--color-warning)/25",
  },
  {
    band: "HIGH",
    label: "High Risk",
    range: "0.60 – 0.80",
    color: "#f97316", // Orange 500
    surface: "rgba(249, 115, 22, 0.10)",
    border: "rgba(249, 115, 22, 0.25)",
  },
  {
    band: "VERY_HIGH",
    label: "Very High Risk",
    range: "0.80 – 1.00",
    color: "var(--color-negative)",
    surface: "var(--color-negative)/10",
    border: "var(--color-negative)/25",
  },
] as const;

export function RiskDistributionVisualizer({
  distribution,
  totalDecisions,
  avgOverallRisk,
  className,
  onBandSelect,
}: RiskDistributionVisualizerProps) {
  const [activeTooltip, setActiveTooltip] = useState<{
    band: string;
    label: string;
    count: number;
    pct: number;
    x: number;
    y: number;
  } | null>(null);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {RISK_BAND_METADATA.map(({ band, label, range, color, surface, border }) => {
          const count = distribution[band] || 0;
          const ratio = totalDecisions > 0 ? count / totalDecisions : 0;

          return (
            <Card
              key={band}
              style={{
                backgroundColor: surface.startsWith("var") ? `color-mix(in srgb, ${surface.split("/")[0]} 12%, transparent)` : surface,
                borderColor: border.startsWith("var") ? `color-mix(in srgb, ${border.split("/")[0]} 25%, transparent)` : border,
              }}
              className="p-4 transition-all hover:scale-[1.01] cursor-pointer"
              onClick={() => onBandSelect && onBandSelect(band)}
              role="button"
              tabIndex={0}
              aria-label={`${label}: ${formatInteger(count)} decisions (${formatPercent(ratio)})`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider font-semibold text-[var(--text-muted)] truncate">
                  {label}
                </span>
                <span className="text-[10px] font-mono text-[var(--text-muted)]">{range}</span>
              </div>
              <p
                className="text-2xl font-bold mt-2 font-mono tabular-nums"
                style={{ color }}
              >
                {formatInteger(count)}
              </p>
              <div className="mt-2 flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
                <span>{formatPercent(ratio, { decimals: 1 })} of total</span>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Proportional Stacked Bar with Accessible Tooltip */}
      <div className="relative">
        <div
          className="w-full h-3.5 rounded-full overflow-hidden flex shadow-inner border border-[var(--border-default)] bg-[var(--bg-secondary)]"
          role="progressbar"
          aria-label="Deterministic risk band distribution proportional bar"
        >
          {RISK_BAND_METADATA.map(({ band, label, color }) => {
            const count = distribution[band] || 0;
            const pct = totalDecisions > 0 ? (count / totalDecisions) * 100 : 0;

            return (
              <div
                key={band}
                className="h-full transition-all cursor-pointer hover:opacity-85"
                style={{
                  width: `${pct}%`,
                  backgroundColor: color.startsWith("var") ? color : color,
                }}
                onMouseEnter={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setActiveTooltip({
                    band,
                    label,
                    count,
                    pct,
                    x: rect.left + rect.width / 2,
                    y: rect.top,
                  });
                }}
                onMouseLeave={() => setActiveTooltip(null)}
                onClick={() => onBandSelect && onBandSelect(band)}
                role="button"
                tabIndex={0}
                aria-label={`${label}: ${formatInteger(count)} (${pct.toFixed(1)}%)`}
              />
            );
          })}
        </div>

        {activeTooltip && (
          <ChartTooltip
            visible={Boolean(activeTooltip)}
            title={activeTooltip.label}
            subtitle={`Risk Band: ${activeTooltip.band}`}
            epistemicTier="DERIVED"
            items={[
              { label: "Decisions Count", value: formatInteger(activeTooltip.count), isNumeric: true },
              { label: "Share of Total", value: `${activeTooltip.pct.toFixed(1)}%`, isNumeric: true },
            ]}
            x={activeTooltip.x}
            y={activeTooltip.y}
          />
        )}
      </div>
    </div>
  );
}

export default RiskDistributionVisualizer;
