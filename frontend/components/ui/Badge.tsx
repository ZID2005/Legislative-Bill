/**
 * components/ui/Badge.tsx
 * ========================
 * Standardized institutional badge system for Seance.
 *
 * Implements:
 * - Base Badge with dual-theme calibrated semantic tokens
 * - JurisdictionBadge (Central vs State)
 * - StatusBadge (Legislative & system statuses)
 * - SourceBadge (Epistemic source taxonomy with descriptions)
 * - PredictionBadge (Direction and confidence)
 * - ExposureBadge (Direct/indirect, strength, type)
 * - ModelStatusBadge (Strict statutory model status firewall)
 *
 * Epistemic guarantee: Badges combine symbolic/icon markers with explicit text
 * labels and tooltips so meaning is never communicated through color alone.
 */

import React from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Base Badge
// ---------------------------------------------------------------------------

export type BadgeVariant =
  | "default"
  | "primary"
  | "blue"
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
  default:
    "bg-[var(--bg-secondary)] text-[var(--text-secondary)] border-[var(--border-default)]",
  primary:
    "bg-[var(--action-primary)]/12 text-[var(--action-primary)] border-[var(--action-primary)]/30",
  blue:
    "bg-[var(--color-state)]/12 text-[var(--color-state)] border-[var(--color-state)]/30",
  success:
    "bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success-border)]",
  warning:
    "bg-[var(--color-warning)]/12 text-[var(--color-warning)] border-[var(--color-warning)]/30",
  danger:
    "bg-[var(--color-danger-bg)] text-[var(--color-danger)] border-[var(--color-danger-border)]",
  info:
    "bg-[var(--color-info-bg)] text-[var(--color-info)] border-[var(--color-info-border)]",
  muted:
    "bg-[var(--bg-secondary)] text-[var(--text-muted)] border-[var(--border-subtle)]",
  purple:
    "bg-[var(--color-model)]/12 text-[var(--color-model)] border-[var(--color-model)]/30",
  amber:
    "bg-[var(--color-warning)]/12 text-[var(--color-warning)] border-[var(--color-warning)]/30",
  emerald:
    "bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success-border)]",
  rose:
    "bg-[var(--color-danger-bg)] text-[var(--color-danger)] border-[var(--color-danger-border)]",
  slate:
    "bg-[var(--bg-secondary)] text-[var(--text-secondary)] border-[var(--border-default)]",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "xs" | "sm" | "md";
  className?: string;
  icon?: React.ReactNode;
}

export function Badge({
  children,
  variant = "default",
  size = "sm",
  className,
  icon,
  ...props
}: BadgeProps) {
  const sizeClasses = {
    xs: "text-[10px] px-1.5 py-0.5",
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border font-medium tracking-wide whitespace-nowrap transition-colors select-none",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {icon && <span aria-hidden="true" className="inline-flex items-center">{icon}</span>}
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
    <Badge
      variant={isCentral ? "primary" : "info"}
      size={size}
      aria-label={`Jurisdiction: ${isCentral ? "Central Parliament" : state ?? "State"}`}
    >
      <span aria-hidden="true">{isCentral ? "🏛" : "🗺"}</span>
      <span>{isCentral ? "Central" : (state ?? "State")}</span>
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// StatusBadge — Bill or System Status
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
      className="uppercase tracking-widest font-mono font-bold"
      {...(showTooltip && desc ? { title: desc } : {})}
    >
      {type}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// PredictionBadge — Direction and Confidence
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
    <Badge variant={variant} size={size} className="font-mono">
      <span aria-hidden="true">{arrow}</span>
      <span>{direction}</span>
      {confidence ? <span className="opacity-75"> · {confidence}</span> : null}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// ExposureBadge — Exposure Vector and Strength
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

// ---------------------------------------------------------------------------
// ModelStatusBadge — Task 8.27 Strict Model Status Firewall
// ---------------------------------------------------------------------------

export function ModelStatusBadge({
  status,
  label,
  size = "xs",
}: {
  status?: string;
  label?: string;
  size?: "xs" | "sm" | "md";
}) {
  const norm = (status || "").toUpperCase();
  const isModelled = norm === "MODELLED" || norm.includes("CENTRAL QUANTITATIVE");
  const isPending = norm === "PENDING_REVIEW" || norm.includes("PENDING REVIEW");
  const isLive = isPending || norm === "KNOWLEDGE_ONLY" || norm.startsWith("LIVE");
  const isNotEligible = norm === "NOT_ELIGIBLE" || norm.includes("NOT ELIGIBLE");

  const variant: BadgeVariant = isModelled
    ? "emerald"
    : isLive
    ? "purple"
    : isNotEligible
    ? "slate"
    : "amber";

  const displayLabel =
    label ||
    (isModelled
      ? "MODELLED — CENTRAL QUANTITATIVE"
      : isLive
      ? isPending
        ? "LIVE — PENDING REVIEW"
        : "LIVE — KNOWLEDGE ONLY"
      : "NOT ELIGIBLE FOR STOCK MODEL");

  const icon = isModelled ? "📊" : isLive ? "🌐" : "🛡";

  return (
    <Badge variant={variant} size={size} className="font-mono tracking-tight font-semibold">
      <span aria-hidden="true">{icon}</span>
      <span>{displayLabel}</span>
    </Badge>
  );
}

export default Badge;
