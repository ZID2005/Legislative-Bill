/**
 * components/charts/EventStudyChart.tsx
 * =====================================
 * Institutional Econometric Event-Study Trajectory & Abnormal Return SVG Chart.
 *
 * Implements:
 * - Dual-theme semantic CSS tokens:
 *   --chart-grid, --chart-axis, --chart-axis-text, --chart-observed, --color-model, --chart-zero-line.
 * - Clear visual distinction between Realized/Observed returns and Model Predictions:
 *   - Observed: Solid stroke + Circular nodes (●) + [OBSERVED]
 *   - Prediction: Dashed stroke + Diamond nodes (◆) + [PREDICTION]
 * - Authoritative 5-horizon and pre-event timeline mapping around T0.
 * - Interactive accessible tooltips with tabular numbers and sign conventions.
 * - Epistemic non-color indicators (WCAG 2.2 AA).
 */

"use client";

import React, { useState, useId } from "react";
import { cn } from "@/lib/utils";
import { formatPercent, getDirectionGlyph } from "@/lib/formatters";
import { ChartContainer, type LegendItem } from "./ChartContainer";
import { ChartTooltip, type TooltipItem } from "./ChartTooltip";

export interface EventStudyPoint {
  day: number; // day offset relative to T0 (-10, -5, -3, -1, 0, 1, 3, 5, 10)
  label: string; // e.g. "T-5", "T0", "T+5"
  observedReturn?: number | null; // realized / backtested historical return
  predictedReturn?: number | null; // model econometric forecast
  windowName?: string; // e.g. "[-5,+5]"
  isModeled?: boolean;
}

export interface EventStudyChartProps {
  title?: string;
  subtitle?: string;
  points: EventStudyPoint[];
  t0Label?: string;
  className?: string;
  height?: number;
  width?: number;
  id?: string;
}

export function EventStudyChart({
  title = "Econometric Event-Study Trajectory",
  subtitle = "Multi-horizon Cumulative Abnormal Return (CAR) path around legislative event date (T0)",
  points,
  t0Label = "T0: Enactment Date",
  className,
  height = 240,
  width = 600,
  id,
}: EventStudyChartProps) {
  const chartId = useId();
  const [activePoint, setActivePoint] = useState<{
    point: EventStudyPoint;
    x: number;
    y: number;
  } | null>(null);

  if (!points || points.length === 0) {
    return (
      <ChartContainer
        title={title}
        subtitle={subtitle}
        empty
        emptyMessage="No econometric event study returns recorded for this pair."
        className={className}
        id={id}
      >
        <div />
      </ChartContainer>
    );
  }

  // Padding inside SVG canvas
  const padding = { top: 25, right: 35, bottom: 40, left: 55 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  // Determine min and max values across series
  const allValues: number[] = [];
  points.forEach((p) => {
    if (typeof p.observedReturn === "number") allValues.push(p.observedReturn);
    if (typeof p.predictedReturn === "number") allValues.push(p.predictedReturn);
  });

  const rawMin = allValues.length > 0 ? Math.min(...allValues, 0) : -0.05;
  const rawMax = allValues.length > 0 ? Math.max(...allValues, 0) : 0.05;
  // Pad bounds symmetrically for clean baseline
  const absBound = Math.max(Math.abs(rawMin), Math.abs(rawMax), 0.02) * 1.25;
  const yMin = -absBound;
  const yMax = absBound;

  // Scale mapping functions
  const getX = (index: number) => {
    if (points.length <= 1) return padding.left + plotWidth / 2;
    return padding.left + (index / (points.length - 1)) * plotWidth;
  };

  const getY = (val: number) => {
    const range = yMax - yMin;
    const norm = (val - yMin) / (range || 1);
    return padding.top + (1 - norm) * plotHeight;
  };

  const zeroY = getY(0);

  // Generate SVG path for observed points
  const observedCoords = points
    .map((p, idx) => (typeof p.observedReturn === "number" ? { x: getX(idx), y: getY(p.observedReturn), p } : null))
    .filter(Boolean) as { x: number; y: number; p: EventStudyPoint }[];

  const observedPath =
    observedCoords.length > 1
      ? observedCoords.reduce((acc, curr, i) => `${acc} ${i === 0 ? "M" : "L"} ${curr.x} ${curr.y}`, "")
      : "";

  // Generate SVG path for predicted points
  const predictedCoords = points
    .map((p, idx) => (typeof p.predictedReturn === "number" ? { x: getX(idx), y: getY(p.predictedReturn), p } : null))
    .filter(Boolean) as { x: number; y: number; p: EventStudyPoint }[];

  const predictedPath =
    predictedCoords.length > 1
      ? predictedCoords.reduce((acc, curr, i) => `${acc} ${i === 0 ? "M" : "L"} ${curr.x} ${curr.y}`, "")
      : "";

  // Legend items
  const legendItems: LegendItem[] = [
    {
      label: "Realized Abnormal Return",
      color: "var(--chart-observed)",
      lineStyle: "solid",
      markerShape: "circle",
      description: "Historical observed CAR derived from trading data [OBSERVED]",
    },
    {
      label: "Econometric Model Forecast",
      color: "var(--color-model)",
      lineStyle: "dashed",
      markerShape: "diamond",
      description: "Backtested econometric event-study prediction [PREDICTION]",
    },
    {
      label: "Zero Return Benchmark",
      color: "var(--chart-reference)",
      lineStyle: "solid",
      description: "Neutral 0.00% benchmark return line",
    },
  ];

  // Tooltip items
  const tooltipItems: TooltipItem[] = activePoint
    ? [
        ...(typeof activePoint.point.observedReturn === "number"
          ? [
              {
                label: "Observed CAR",
                value: formatPercent(activePoint.point.observedReturn, { showSign: true }),
                color: "var(--chart-observed)",
                glyph: getDirectionGlyph(activePoint.point.observedReturn),
                isNumeric: true,
              },
            ]
          : []),
        ...(typeof activePoint.point.predictedReturn === "number"
          ? [
              {
                label: "Model Forecast",
                value: formatPercent(activePoint.point.predictedReturn, { showSign: true }),
                color: "var(--color-model)",
                glyph: getDirectionGlyph(activePoint.point.predictedReturn),
                isNumeric: true,
              },
            ]
          : []),
      ]
    : [];

  return (
    <ChartContainer
      title={title}
      subtitle={subtitle}
      epistemicTier="PREDICTION"
      legendItems={legendItems}
      className={className}
      id={id}
    >
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto select-none overflow-visible"
          aria-labelledby={`chart-title-${chartId}`}
          role="img"
        >
          <title id={`chart-title-${chartId}`}>{title}</title>

          {/* Grid lines (horizontal) */}
          {[-absBound, -absBound / 2, 0, absBound / 2, absBound].map((val, idx) => {
            const y = getY(val);
            const isZero = Math.abs(val) < 0.0001;
            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke={isZero ? "var(--chart-zero-line)" : "var(--chart-grid)"}
                  strokeWidth={isZero ? 1.5 : 1}
                  strokeDasharray={isZero ? "none" : "3 3"}
                />
                {/* Y-axis tick label */}
                <text
                  x={padding.left - 8}
                  y={y + 3.5}
                  textAnchor="end"
                  className="font-mono text-[9px] tabular-nums"
                  fill="var(--chart-axis-text)"
                >
                  {formatPercent(val, { showSign: true, decimals: 1 })}
                </text>
              </g>
            );
          })}

          {/* Vertical T0 Announcement Line */}
          {(() => {
            const t0Index = points.findIndex((p) => p.day === 0);
            if (t0Index >= 0) {
              const x = getX(t0Index);
              return (
                <g>
                  <line
                    x1={x}
                    y1={padding.top}
                    x2={x}
                    y2={height - padding.bottom}
                    stroke="var(--chart-axis)"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                  />
                  <text
                    x={x}
                    y={padding.top - 6}
                    textAnchor="middle"
                    fill="var(--chart-axis-text)"
                    className="font-mono text-[9px] font-semibold uppercase tracking-wider"
                  >
                    T0 Event
                  </text>
                </g>
              );
            }
            return null;
          })()}

          {/* Observed Series Line (Solid) */}
          {observedPath && (
            <path
              d={observedPath}
              fill="none"
              stroke="var(--chart-observed)"
              strokeWidth={2.2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Predicted Series Line (Dashed) */}
          {predictedPath && (
            <path
              d={predictedPath}
              fill="none"
              stroke="var(--color-model)"
              strokeWidth={2.2}
              strokeDasharray="5 3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Data Points (Observed: Circles) */}
          {observedCoords.map((coord, idx) => (
            <circle
              key={`obs-${idx}`}
              cx={coord.x}
              cy={coord.y}
              r={4}
              fill="var(--bg-surface)"
              stroke="var(--chart-observed)"
              strokeWidth={2}
              className="cursor-pointer transition-transform hover:scale-150"
              tabIndex={0}
              role="button"
              aria-label={`Observed ${coord.p.label}: ${formatPercent(coord.p.observedReturn, { showSign: true })}`}
              onMouseEnter={() => setActivePoint({ point: coord.p, x: coord.x, y: coord.y })}
              onMouseLeave={() => setActivePoint(null)}
              onFocus={() => setActivePoint({ point: coord.p, x: coord.x, y: coord.y })}
              onBlur={() => setActivePoint(null)}
            />
          ))}

          {/* Data Points (Predicted: Diamonds) */}
          {predictedCoords.map((coord, idx) => {
            const size = 4.5;
            return (
              <polygon
                key={`pred-${idx}`}
                points={`${coord.x},${coord.y - size} ${coord.x + size},${coord.y} ${coord.x},${coord.y + size} ${coord.x - size},${coord.y}`}
                fill="var(--bg-surface)"
                stroke="var(--color-model)"
                strokeWidth={2}
                className="cursor-pointer transition-transform hover:scale-150"
                tabIndex={0}
                role="button"
                aria-label={`Forecast ${coord.p.label}: ${formatPercent(coord.p.predictedReturn, { showSign: true })}`}
                onMouseEnter={() => setActivePoint({ point: coord.p, x: coord.x, y: coord.y })}
                onMouseLeave={() => setActivePoint(null)}
                onFocus={() => setActivePoint({ point: coord.p, x: coord.x, y: coord.y })}
                onBlur={() => setActivePoint(null)}
              />
            );
          })}

          {/* X-axis ticks and labels */}
          {points.map((p, idx) => {
            const x = getX(idx);
            return (
              <g key={`x-${idx}`}>
                <line
                  x1={x}
                  y1={height - padding.bottom}
                  x2={x}
                  y2={height - padding.bottom + 4}
                  stroke="var(--chart-axis)"
                  strokeWidth={1}
                />
                <text
                  x={x}
                  y={height - padding.bottom + 16}
                  textAnchor="middle"
                  fill="var(--chart-axis-text)"
                  className="font-mono text-[9px]"
                >
                  {p.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Tooltip */}
        {activePoint && (
          <ChartTooltip
            visible={Boolean(activePoint)}
            title={activePoint.point.windowName || activePoint.point.label}
            subtitle={activePoint.point.day === 0 ? t0Label : `Day ${activePoint.point.day > 0 ? `+${activePoint.point.day}` : activePoint.point.day}`}
            epistemicTier="PREDICTION"
            items={tooltipItems}
            x={activePoint.x}
            y={activePoint.y}
          />
        )}
      </div>
    </ChartContainer>
  );
}

export default EventStudyChart;
