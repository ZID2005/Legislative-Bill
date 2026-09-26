/**
 * components/monitoring/SourceHealthBadge.tsx
 * =============================================
 * Status badge for monitoring source health.
 * Uses icons + text — never color alone — for accessibility.
 *
 * Statuses from SourceStatus enum:
 * IMPLEMENTED | NOT_IMPLEMENTED | PLANNED | ERROR | DISABLED
 * Runtime health: HEALTHY | DEGRADED | NEVER_CHECKED
 */

import React from "react";

export type SourceHealthStatus =
  | "IMPLEMENTED"
  | "NOT_IMPLEMENTED"
  | "PLANNED"
  | "ERROR"
  | "DISABLED"
  | "HEALTHY"
  | "DEGRADED"
  | "NEVER_CHECKED"
  | string;

interface SourceHealthBadgeProps {
  status: SourceHealthStatus;
  className?: string;
  size?: "sm" | "md";
}

const STATUS_CONFIG: Record<string, { label: string; icon: string; color: string; description: string }> = {
  IMPLEMENTED: {
    label: "Implemented",
    icon: "✓",
    color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    description: "Source is implemented and actively monitored",
  },
  HEALTHY: {
    label: "Healthy",
    icon: "✓",
    color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    description: "Source is operational with no recent errors",
  },
  DEGRADED: {
    label: "Degraded",
    icon: "⚠",
    color: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    description: "Source has recent errors but was previously healthy",
  },
  PLANNED: {
    label: "Planned",
    icon: "◦",
    color: "bg-slate-500/15 text-slate-400 border-slate-500/30",
    description: "Source is planned but not yet implemented",
  },
  NOT_IMPLEMENTED: {
    label: "Not Implemented",
    icon: "–",
    color: "bg-slate-500/15 text-slate-400 border-slate-500/30",
    description: "Source is configured but not yet implemented",
  },
  ERROR: {
    label: "Error",
    icon: "✕",
    color: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    description: "Source check failed",
  },
  DISABLED: {
    label: "Disabled",
    icon: "○",
    color: "bg-slate-600/15 text-slate-500 border-slate-600/30",
    description: "Source monitoring is disabled",
  },
  NEVER_CHECKED: {
    label: "Never Checked",
    icon: "?",
    color: "bg-amber-500/15 text-amber-500 border-amber-500/30",
    description: "Source has not yet been checked",
  },
};

export function SourceHealthBadge({ status, className = "", size = "sm" }: SourceHealthBadgeProps) {
  const key = status?.toUpperCase().replace(/ /g, "_") ?? "NOT_IMPLEMENTED";
  const cfg = STATUS_CONFIG[key] ?? {
    label: status,
    icon: "?",
    color: "bg-slate-500/15 text-slate-400 border-slate-500/30",
    description: status,
  };

  const sizeClass = size === "md" ? "px-2.5 py-1 text-xs" : "px-2 py-0.5 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded border font-medium ${sizeClass} ${cfg.color} ${className}`}
      title={cfg.description}
      role="status"
      aria-label={`Source status: ${cfg.label}`}
    >
      <span aria-hidden="true" className="font-bold">{cfg.icon}</span>
      {cfg.label}
    </span>
  );
}
