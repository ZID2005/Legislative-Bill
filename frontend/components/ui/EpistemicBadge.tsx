/**
 * components/ui/EpistemicBadge.tsx
 * =================================
 * Task 8.31C — Institutional Epistemic Classification Token.
 *
 * Enforces strict epistemic taxonomy across all analytical outputs:
 * - [FACT]: Official Gazette records, PRS legislative data, statutory clauses
 * - [OBSERVED]: Historical BSE/NSE equity returns, trading volumes, event dates
 * - [DERIVED]: Econometric OLS residuals, CAR %, t-statistic, beta coefficients
 * - [INTERPRETATION]: Grounded Groq AI executive summaries, policy analysis
 * - [PREDICTION]: Forward-looking event-study cumulative abnormal returns
 * - [EVIDENCE]: Parliamentary bulletins, gazette notifications, media mentions
 */

import React from "react";
import { cn } from "@/lib/utils";

export type EpistemicType =
  | "FACT"
  | "OBSERVED"
  | "DERIVED"
  | "INTERPRETATION"
  | "PREDICTION"
  | "EVIDENCE";

export interface EpistemicBadgeProps {
  type: EpistemicType | string;
  size?: "xs" | "sm" | "md";
  showBracket?: boolean;
  className?: string;
  tooltip?: string;
}

const EPISTEMIC_STYLES: Record<string, { className: string; label: string; description: string }> = {
  FACT: {
    className: "badge-epistemic-fact",
    label: "FACT",
    description: "Official Gazette, Parliamentary record, or verified statutory clause",
  },
  OBSERVED: {
    className: "badge-epistemic-observed",
    label: "OBSERVED",
    description: "Historical market price, traded return, or recorded event timestamp",
  },
  DERIVED: {
    className: "badge-epistemic-derived",
    label: "DERIVED",
    description: "Econometric calculation, OLS market model residual, CAR, or t-statistic",
  },
  INTERPRETATION: {
    className: "badge-epistemic-interpretation",
    label: "INTERPRETATION",
    description: "Grounded AI policy analysis, executive summary, or stakeholder assessment",
  },
  PREDICTION: {
    className: "badge-epistemic-prediction",
    label: "PREDICTION",
    description: "Econometric event-study projection across the 5 authoritative horizons",
  },
  EVIDENCE: {
    className: "badge-epistemic-evidence",
    label: "EVIDENCE",
    description: "Official publication, parliamentary bulletin, or corroborated news item",
  },
};

export function EpistemicBadge({
  type,
  size = "sm",
  showBracket = false,
  className,
  tooltip,
}: EpistemicBadgeProps) {
  const normalizedType = type.toUpperCase().replace(/[\[\]]/g, "").trim();
  const meta = EPISTEMIC_STYLES[normalizedType] || {
    className: "bg-slate-800 text-slate-300 border border-slate-700",
    label: normalizedType,
    description: "Epistemic classification",
  };

  const sizeClass =
    size === "xs"
      ? "text-[9px] px-1 py-0.2 tracking-wider"
      : size === "md"
      ? "text-xs px-2 py-0.5 tracking-wider"
      : "text-[10px] px-1.5 py-0.5 tracking-wider";

  const displayText = showBracket ? `[${meta.label}]` : meta.label;

  return (
    <span
      className={cn(
        "inline-flex items-center font-mono font-bold uppercase rounded leading-none transition-colors select-none",
        meta.className,
        sizeClass,
        className
      )}
      title={tooltip || meta.description}
      data-epistemic={meta.label}
    >
      {displayText}
    </span>
  );
}

export default EpistemicBadge;
