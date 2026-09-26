/**
 * components/ui/Badge.tsx
 * ========================
 * Versatile badge component and all domain-specific badge variants:
 * - Badge (base)
 * - StatusBadge (bill/system status)
 * - JurisdictionBadge (CENTRAL | STATE)
 * - SourceBadge (FACT | DERIVED | INTERPRETATION | PREDICTION)
 * - PredictionBadge (direction + confidence)
 * - ExposureBadge (exposure type/strength)
 * - CapabilityBadge (Level 1/2/3)
 */

import React from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Base Badge
// ---------------------------------------------------------------------------

export type BadgeVariant =
  | "default"
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "muted"
  | "purple"
  | "amber"
  | "emerald"
  | "rose"
  | "slate";

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-slate-800 text-slate-200 border border-slate-700",
  primary: "bg-blue-900/60 text-blue-200 border border-blue-700/50",
  success: "bg-emerald-900/60 text-emerald-200 border border-emerald-700/50",
  warning: "bg-amber-900/60 text-amber-200 border border-amber-700/50",
  danger: "bg-rose-900/60 text-rose-200 border border-rose-700/50",
  info: "bg-sky-900/60 text-sky-200 border border-sky-700/50",
  muted: "bg-slate-800/80 text-slate-400 border border-slate-700/50",
  purple: "bg-purple-900/60 text-purple-200 border border-purple-700/50",
  amber: "bg-amber-900/60 text-amber-200 border border-amber-700/50",
  emerald: "bg-emerald-900/60 text-emerald-200 border border-emerald-700/50",
  rose: "bg-rose-900/60 text-rose-200 border border-rose-700/50",
  slate: "bg-slate-800 text-slate-300 border border-slate-600",
};

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "xs" | "sm" | "md";
  className?: string;
}

export function Badge({
  children,
  variant = "default",
  size = "sm",
  className,
}: BadgeProps) {
  const sizeClasses = {
    xs: "text-[10px] px-1.5 py-0.5",
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded font-medium tracking-wide whitespace-nowrap",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
}

// ---------------------------------------------------------------------------
// JurisdictionBadge
// ---------------------------------------------------------------------------

export function JurisdictionBadge({
  jurisdiction,
  state,
  size = "sm",
}: {
  jurisdiction: string;
  state?: string | null;
  size?: "xs" | "sm" | "md";
}) {
  const isCentral = jurisdiction?.toLowerCase() === "central";
  return (
    <Badge variant={isCentral ? "primary" : "info"} size={size}>
      {isCentral ? "🏛 Central" : `🗺 ${state ?? "State"}`}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// StatusBadge — bill or system status
// ---------------------------------------------------------------------------

const statusVariantMap: Record<string, BadgeVariant> = {
  passed: "success",
  enacted: "success",
  assented: "success",
  active: "success",
  introduced: "info",
  pending: "warning",
  tabled: "warning",
  lapsed: "muted",
  withdrawn: "muted",
  healthy: "success",
  degraded: "warning",
  error: "danger",
};

export function StatusBadge({
  status,
  size = "sm",
}: {
  status: string;
  size?: "xs" | "sm" | "md";
}) {
  const key = status?.toLowerCase().replace(/_/g, " ") ?? "";
  const variant = statusVariantMap[key] ?? "default";
  return (
    <Badge variant={variant} size={size}>
      {status}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// SourceBadge — FACT | OBSERVED | DERIVED | INTERPRETATION | PREDICTION
// ---------------------------------------------------------------------------

export type SourceType = "FACT" | "OBSERVED" | "DERIVED" | "INTERPRETATION" | "PREDICTION";

const sourceVariantMap: Record<SourceType, BadgeVariant> = {
  FACT: "emerald",
  OBSERVED: "info",
  DERIVED: "primary",
  INTERPRETATION: "amber",
  PREDICTION: "purple",
};

const sourceDescriptions: Record<SourceType, string> = {
  FACT: "Verified source information from official parliamentary or statutory records",
  OBSERVED: "Directly observed monitoring or source event from official legislative feeds",
  DERIVED: "Calculated from existing records via documented deterministic methodology",
  INTERPRETATION: "Reasoned human/AI explanation with cited evidentiary sources",
  PREDICTION: "Quantitative model-generated output with backtested confidence bounds",
};

export function SourceBadge({
  type,
  size = "xs",
  showTooltip = false,
}: {
  type: SourceType | string;
  size?: "xs" | "sm" | "md";
  showTooltip?: boolean;
}) {
  const t = (type as SourceType) ?? "FACT";
  const variant = sourceVariantMap[t] ?? "default";
  const desc = sourceDescriptions[t];

  return (
    <Badge
      variant={variant}
      size={size}
      className="uppercase tracking-widest"
      {...(showTooltip && desc ? { title: desc } : {})}
    >
      {type}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// PredictionBadge — direction and confidence
// ---------------------------------------------------------------------------

export function PredictionBadge({
  direction,
  confidence,
  size = "sm",
}: {
  direction: string;
  confidence?: string;
  size?: "xs" | "sm" | "md";
}) {
  const dir = direction?.toUpperCase();
  const variant: BadgeVariant =
    dir === "POSITIVE"
      ? "success"
      : dir === "NEGATIVE"
      ? "danger"
      : "muted";

  const arrow = dir === "POSITIVE" ? "↑" : dir === "NEGATIVE" ? "↓" : "→";

  return (
    <Badge variant={variant} size={size}>
      {arrow} {direction}
      {confidence ? ` · ${confidence}` : ""}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// ExposureBadge — exposure type and strength
// ---------------------------------------------------------------------------

export function ExposureBadge({
  type,
  strength,
  directIndirect,
  size = "xs",
}: {
  type?: string;
  strength?: string;
  directIndirect?: string;
  size?: "xs" | "sm" | "md";
}) {
  const strengthVariant: BadgeVariant =
    strength?.toUpperCase() === "HIGH"
      ? "danger"
      : strength?.toUpperCase() === "MEDIUM"
      ? "warning"
      : "muted";

  return (
    <span className="inline-flex items-center gap-1">
      {directIndirect && (
        <Badge
          variant={directIndirect.toUpperCase() === "DIRECT" ? "info" : "slate"}
          size={size}
        >
          {directIndirect}
        </Badge>
      )}
      {strength && (
        <Badge variant={strengthVariant} size={size}>
          {strength}
        </Badge>
      )}
      {type && (
        <Badge variant="default" size={size}>
          {type}
        </Badge>
      )}
    </span>
  );
}
