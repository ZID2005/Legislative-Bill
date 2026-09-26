/**
 * components/coverage/CapabilityBadge.tsx
 * ========================================
 * Coverage-aware components:
 * - CapabilityBadge — Level 1 / Level 2 / Level 3 indicator
 * - PredictionAvailability — what's available for an entity
 * - CoverageStatus — platform-wide coverage overview widget
 */

import React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";

// ---------------------------------------------------------------------------
// CapabilityBadge
// ---------------------------------------------------------------------------

export type CapabilityLevel = 1 | 2 | 3;

const levelConfig: Record<
  CapabilityLevel,
  { label: string; sublabel: string; colorClass: string; borderClass: string; dotClass: string }
> = {
  1: {
    label: "Market Modelled",
    sublabel: "Level 1 — Quantitative predictions available",
    colorClass: "text-emerald-300",
    borderClass: "border-emerald-700/50",
    dotClass: "bg-emerald-400",
  },
  2: {
    label: "Legislative Intelligence",
    sublabel: "Level 2 — No market predictions",
    colorClass: "text-blue-300",
    borderClass: "border-blue-700/50",
    dotClass: "bg-blue-400",
  },
  3: {
    label: "Planned Coverage",
    sublabel: "Level 3 — Roadmap (not yet ingested)",
    colorClass: "text-slate-400",
    borderClass: "border-slate-700",
    dotClass: "bg-slate-500",
  },
};

export interface CapabilityBadgeProps {
  level: CapabilityLevel;
  size?: "xs" | "sm" | "md";
  showTooltip?: boolean;
  className?: string;
}

export function CapabilityBadge({
  level,
  size = "sm",
  showTooltip = false,
  className,
}: CapabilityBadgeProps) {
  const config = levelConfig[level];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-medium",
        config.colorClass,
        config.borderClass,
        "bg-slate-900/80",
        size === "xs" && "text-[10px]",
        size === "sm" && "text-xs",
        size === "md" && "text-sm",
        className
      )}
      title={showTooltip ? config.sublabel : undefined}
      aria-label={`Coverage: ${config.label}`}
    >
      <span
        className={cn("inline-block w-1.5 h-1.5 rounded-full", config.dotClass)}
        aria-hidden="true"
      />
      L{level} · {config.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Standardized Coverage Badges (Task 8.16 Institutional Language)
// ---------------------------------------------------------------------------

export type StandardCoverageTier =
  | "LEVEL 1 QUANTITATIVE"
  | "STATE QUALITATIVE"
  | "LEVEL 2 INTELLIGENCE ONLY"
  | "REFERENCE";

const standardCoverageConfig: Record<
  StandardCoverageTier,
  { label: string; sublabel: string; colorClass: string; borderClass: string; dotClass: string }
> = {
  "LEVEL 1 QUANTITATIVE": {
    label: "LEVEL 1 QUANTITATIVE",
    sublabel: "Central Quantitative Market Models Available",
    colorClass: "text-emerald-300",
    borderClass: "border-emerald-700/50",
    dotClass: "bg-emerald-400",
  },
  "STATE QUALITATIVE": {
    label: "STATE QUALITATIVE",
    sublabel: "State Legislative & Economic Intelligence (Strictly 0 Market Predictions)",
    colorClass: "text-blue-300",
    borderClass: "border-blue-700/50",
    dotClass: "bg-blue-400",
  },
  "LEVEL 2 INTELLIGENCE ONLY": {
    label: "LEVEL 2 INTELLIGENCE ONLY",
    sublabel: "Corporate Intelligence Universe (Firewalled from Market Models)",
    colorClass: "text-amber-300",
    borderClass: "border-amber-700/50",
    dotClass: "bg-amber-400",
  },
  REFERENCE: {
    label: "REFERENCE",
    sublabel: "Non-Predictive Reference Entity",
    colorClass: "text-slate-400",
    borderClass: "border-slate-700",
    dotClass: "bg-slate-500",
  },
};

export interface CoverageBadgeProps {
  tier: StandardCoverageTier | string;
  size?: "xs" | "sm" | "md";
  showTooltip?: boolean;
  className?: string;
}

export function CoverageBadge({
  tier,
  size = "sm",
  showTooltip = false,
  className,
}: CoverageBadgeProps) {
  const normTier = (tier?.toUpperCase().replace(/\s+/g, " ") || "REFERENCE") as StandardCoverageTier;
  const config = standardCoverageConfig[normTier] || standardCoverageConfig["REFERENCE"];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-bold uppercase tracking-wider",
        config.colorClass,
        config.borderClass,
        "bg-slate-900/80",
        size === "xs" && "text-[9px]",
        size === "sm" && "text-[11px]",
        size === "md" && "text-xs",
        className
      )}
      title={showTooltip ? config.sublabel : undefined}
      aria-label={`Coverage tier: ${config.label}`}
    >
      <span
        className={cn("inline-block w-1.5 h-1.5 rounded-full", config.dotClass)}
        aria-hidden="true"
      />
      {config.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// PredictionAvailability
// ---------------------------------------------------------------------------

export interface PredictionAvailabilityProps {
  available: boolean;
  jurisdiction: string;
  universeType?: string;
  firewallStatus?: string | null;
  message?: string | null;
  className?: string;
}

export function PredictionAvailability({
  available,
  jurisdiction,
  universeType,
  firewallStatus,
  message,
  className,
}: PredictionAvailabilityProps) {
  const isStateBill = jurisdiction?.toLowerCase() === "state";
  const isIntelOnly = universeType === "intelligence";

  if (available) {
    return (
      <div
        className={cn(
          "inline-flex items-center gap-2 rounded-md border border-emerald-700/40 bg-emerald-900/20 px-3 py-1.5",
          className
        )}
        role="status"
      >
        <span className="w-2 h-2 rounded-full bg-emerald-400" aria-hidden="true" />
        <span className="text-xs font-medium text-emerald-300">
          Market predictions available
        </span>
      </div>
    );
  }

  const reason = isStateBill
    ? "State legislation"
    : isIntelOnly
    ? "Intelligence entity"
    : firewallStatus ?? "Not eligible";

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-800/40 px-3 py-1.5",
        className
      )}
      role="status"
    >
      <span className="w-2 h-2 rounded-full bg-slate-500" aria-hidden="true" />
      <span className="text-xs text-slate-400">
        No market predictions · <span className="text-slate-500">{reason}</span>
      </span>
    </div>
  );
}

export interface JurisdictionBadgeProps {
  jurisdiction: string;
  state?: string | null;
  size?: "xs" | "sm" | "md";
  className?: string;
}

export function JurisdictionBadge({
  jurisdiction,
  state,
  size = "sm",
  className,
}: JurisdictionBadgeProps) {
  const isCentral = jurisdiction?.toLowerCase() === "central";
  const sizeClasses = {
    xs: "text-[10px] px-1.5 py-0.5",
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
  };

  if (isCentral) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded font-medium border border-amber-600/40 bg-amber-950/30 text-amber-300",
          sizeClasses[size],
          className
        )}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" aria-hidden="true" />
        Central Parliament
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded font-medium border border-blue-600/40 bg-blue-950/30 text-blue-300",
        sizeClasses[size],
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-blue-400" aria-hidden="true" />
      {state ? `${state} Assembly` : "State Assembly"}
    </span>
  );
}

// ---------------------------------------------------------------------------
// MarketRelevanceBadge
// ---------------------------------------------------------------------------

export function MarketRelevanceBadge({
  relevance,
  size = "xs",
}: {
  relevance?: string | null;
  size?: "xs" | "sm" | "md";
}) {
  const r = (relevance ?? "NONE").toUpperCase();
  const variant =
    r === "HIGH"
      ? "rose"
      : r === "MEDIUM"
      ? "amber"
      : r === "LOW"
      ? "primary"
      : "muted";

  return (
    <Badge variant={variant} size={size}>
      Relevance: {r}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// CorporateExposureBadge
// ---------------------------------------------------------------------------

export function CorporateExposureBadge({
  count,
  size = "xs",
}: {
  count: number;
  size?: "xs" | "sm" | "md";
}) {
  if (count <= 0) {
    return (
      <Badge variant="muted" size={size}>
        0 Exposures
      </Badge>
    );
  }

  return (
    <Badge variant="emerald" size={size}>
      {count} {count === 1 ? "Exposure" : "Exposures"}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// CoverageStatus — compact platform overview
// ---------------------------------------------------------------------------

export interface CoverageStatusProps {
  centralBills?: number;
  stateBills?: number;
  companies?: number;
  stateStockPredictions?: number;
  className?: string;
}

export function CoverageStatus({
  centralBills = 20,
  stateBills = 44,
  companies = 70,
  stateStockPredictions = 0,
  className,
}: CoverageStatusProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-slate-800 bg-slate-900 p-4",
        className
      )}
      aria-label="Platform coverage overview"
    >
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
        Platform Coverage
      </p>
      <div className="space-y-1.5 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-400">Central bills</span>
          <span className="font-semibold text-emerald-300">{centralBills} modelled</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">State bills</span>
          <span className="font-semibold text-blue-300">{stateBills} intelligence</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Companies</span>
          <span className="font-semibold text-slate-200">{companies} tracked</span>
        </div>
        <div className="flex justify-between border-t border-slate-800 pt-1.5">
          <span className="text-slate-500">State stock predictions</span>
          <Badge variant="slate" size="xs">
            {stateStockPredictions} · Statutory 0
          </Badge>
        </div>
      </div>
    </div>
  );
}


