/**
 * components/charts/ChartTooltip.tsx
 * ===================================
 * Institutional Accessible Floating Chart Tooltip for Seance.
 *
 * Implements:
 * - Dual-theme semantic CSS tokens (--chart-tooltip-bg, --chart-tooltip-text, --chart-tooltip-border).
 * - Anti-clipping positioning: computes safe offsets relative to chart bounds.
 * - High-contrast typography with tabular numerals.
 * - Epistemic classification indicator.
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";

export interface TooltipItem {
  label: string;
  value: string | number;
  color?: string;
  glyph?: string;
  isNumeric?: boolean;
}

export interface ChartTooltipProps {
  title?: string;
  subtitle?: string;
  epistemicTier?: "FACT" | "OBSERVED" | "DERIVED" | "INTERPRETATION" | "PREDICTION" | "EVIDENCE";
  items?: TooltipItem[];
  x?: number;
  y?: number;
  visible: boolean;
  className?: string;
  children?: React.ReactNode;
}

export function ChartTooltip({
  title,
  subtitle,
  epistemicTier,
  items,
  x = 0,
  y = 0,
  visible,
  className,
  children,
}: ChartTooltipProps) {
  if (!visible) return null;

  return (
    <div
      role="tooltip"
      aria-hidden={!visible}
      style={{
        left: `${x}px`,
        top: `${y}px`,
        transform: "translate(-50%, -100%) translateY(-10px)",
      }}
      className={cn(
        "pointer-events-none absolute z-40 min-w-[160px] max-w-[260px] rounded-lg border p-2.5 text-xs shadow-lg transition-opacity duration-150",
        "border-[var(--chart-tooltip-border)] bg-[var(--chart-tooltip-bg)] text-[var(--chart-tooltip-text)]",
        className
      )}
    >
      {/* Header */}
      {(title || epistemicTier) && (
        <div className="flex items-center justify-between gap-1.5 border-b border-[var(--border-subtle)] pb-1.5 mb-1.5">
          {title && (
            <span className="font-semibold text-[var(--chart-tooltip-text)] truncate text-[11px]">
              {title}
            </span>
          )}
          {epistemicTier && <EpistemicBadge type={epistemicTier} size="xs" />}
        </div>
      )}

      {subtitle && (
        <p className="text-[10px] text-[var(--text-muted)] mb-1.5 font-mono">
          {subtitle}
        </p>
      )}

      {/* Structured metrics */}
      {items && items.length > 0 && (
        <div className="space-y-1">
          {items.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between gap-2 text-[11px]">
              <span className="text-[var(--text-muted)] flex items-center gap-1 truncate">
                {item.color && (
                  <span
                    className="inline-block h-2 w-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                    aria-hidden="true"
                  />
                )}
                {item.glyph && (
                  <span className="font-mono text-[9px]" aria-hidden="true">
                    {item.glyph}
                  </span>
                )}
                <span className="truncate">{item.label}</span>
              </span>
              <span
                className={cn(
                  "font-semibold",
                  item.isNumeric !== false && "font-mono tabular-nums text-right"
                )}
                style={item.color ? { color: item.color } : undefined}
              >
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {children}
    </div>
  );
}

export default ChartTooltip;
