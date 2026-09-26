/**
 * components/monitoring/EpistemicLabel.tsx
 * =========================================
 * Displays epistemic classification badges:
 * [OBSERVED] [DERIVED] [INTERPRETATION] [PREDICTION]
 *
 * OBSERVED: A source reported/contained this item.
 * DERIVED: The system detected a difference between versions.
 * INTERPRETATION: An analyst/AI explanation.
 * PREDICTION: Only existing validated model outputs.
 */

import React from "react";

export type EpistemicStatus = "OBSERVED" | "DERIVED" | "INTERPRETATION" | "PREDICTION" | "FACT";

interface EpistemicLabelProps {
  status: EpistemicStatus | string;
  className?: string;
  showIcon?: boolean;
}

const CONFIG: Record<string, { label: string; color: string; icon: string; title: string }> = {
  OBSERVED: {
    label: "OBSERVED",
    color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    icon: "📡",
    title: "A source reported or contained this item directly.",
  },
  DERIVED: {
    label: "DERIVED",
    color: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    icon: "⚙",
    title: "The system detected a difference between two versions.",
  },
  FACT: {
    label: "FACT",
    color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    icon: "✓",
    title: "Verified factual information from official sources.",
  },
  INTERPRETATION: {
    label: "INTERPRETATION",
    color: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    icon: "💬",
    title: "An analyst or AI explanation of what this may mean.",
  },
  PREDICTION: {
    label: "PREDICTION",
    color: "bg-purple-500/15 text-purple-400 border-purple-500/30",
    icon: "📊",
    title: "An existing validated model output. Not created from monitoring.",
  },
};

export function EpistemicLabel({ status, className = "", showIcon = true }: EpistemicLabelProps) {
  const cfg = CONFIG[status?.toUpperCase()] ?? CONFIG.DERIVED;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-sm border text-xs font-mono font-semibold tracking-wider ${cfg.color} ${className}`}
      title={cfg.title}
      aria-label={`Epistemic status: ${cfg.label}`}
    >
      {showIcon && <span aria-hidden="true">{cfg.icon}</span>}
      [{cfg.label}]
    </span>
  );
}
