/**
 * components/ui/DataStatusBadge.tsx
 * ====================================
 * Epistemic data status and lifecycle badges for Seance.
 *
 * Implements dual-theme calibrated tokens for:
 *   LIVE              — recently discovered legislative data (not modelled)
 *   MODELLED          — quantitative market model available
 *   INTELLIGENCE      — qualitative economic analysis only
 *   PLANNED           — not yet ingested into the pipeline
 *   NEW               — recently ingested record
 *   RECENT            — discovered in the last 7 days
 *   ACTIVE            — currently active in parliamentary process
 *   AMENDED           — bill has been amended
 *   PASSED            — enacted/passed
 *   ASSENT_PENDING    — awaiting presidential/gubernatorial assent
 *   NOTIFIED          — published in official gazette
 *   ARCHIVED          — historical record
 *   UPCOMING          — scheduled for future consideration
 *   SOURCE_UNVERIFIED — provenance not independently confirmed
 */

import React from "react";
import { cn } from "@/lib/utils";

export type DataStatusType =
  | "LIVE"
  | "MODELLED"
  | "INTELLIGENCE"
  | "PLANNED"
  | "NEW"
  | "RECENT"
  | "ACTIVE"
  | "AMENDED"
  | "PASSED"
  | "ASSENT_PENDING"
  | "NOTIFIED"
  | "ARCHIVED"
  | "UPCOMING"
  | "SOURCE_UNVERIFIED"
  | "FACT"
  | "OBSERVED"
  | "DERIVED"
  | "INTERPRETATION"
  | "PREDICTION";

interface DataStatusBadgeProps {
  status: DataStatusType;
  size?: "xs" | "sm";
  showDot?: boolean;
  className?: string;
}

const STATUS_CONFIG: Record<
  DataStatusType,
  { label: string; colorClass: string; dotClass?: string }
> = {
  LIVE: {
    label: "LIVE",
    colorClass: "bg-[var(--color-success-bg)] border-[var(--color-success-border)] text-[var(--color-success)]",
    dotClass: "bg-[var(--color-success)]",
  },
  MODELLED: {
    label: "MODELLED",
    colorClass: "bg-[var(--color-model)]/12 border-[var(--color-model)]/30 text-[var(--color-model)]",
  },
  INTELLIGENCE: {
    label: "INTELLIGENCE",
    colorClass: "bg-[var(--color-warning)]/12 border-[var(--color-warning)]/30 text-[var(--color-warning)]",
  },
  PLANNED: {
    label: "PLANNED",
    colorClass: "bg-[var(--bg-secondary)] border-[var(--border-default)] text-[var(--text-muted)]",
  },
  NEW: {
    label: "NEW",
    colorClass: "bg-[var(--action-primary)]/12 border-[var(--action-primary)]/30 text-[var(--action-primary)]",
    dotClass: "bg-[var(--action-primary)]",
  },
  RECENT: {
    label: "RECENT",
    colorClass: "bg-[var(--color-info-bg)] border-[var(--color-info-border)] text-[var(--color-info)]",
  },
  ACTIVE: {
    label: "ACTIVE",
    colorClass: "bg-[var(--color-success-bg)] border-[var(--color-success-border)] text-[var(--color-success)]",
    dotClass: "bg-[var(--color-success)]",
  },
  AMENDED: {
    label: "AMENDED",
    colorClass: "bg-[var(--color-warning)]/15 border-[var(--color-warning)]/35 text-[var(--color-warning)]",
  },
  PASSED: {
    label: "PASSED",
    colorClass: "bg-[var(--color-success-bg)] border-[var(--color-success-border)] text-[var(--color-success)]",
  },
  ASSENT_PENDING: {
    label: "ASSENT PENDING",
    colorClass: "bg-[var(--color-warning)]/15 border-[var(--color-warning)]/35 text-[var(--color-warning)]",
  },
  NOTIFIED: {
    label: "NOTIFIED",
    colorClass: "bg-[var(--color-info-bg)] border-[var(--color-info-border)] text-[var(--color-info)]",
  },
  ARCHIVED: {
    label: "ARCHIVED",
    colorClass: "bg-[var(--bg-secondary)] border-[var(--border-default)] text-[var(--text-muted)]",
  },
  UPCOMING: {
    label: "UPCOMING",
    colorClass: "bg-[var(--color-ai)]/12 border-[var(--color-ai)]/30 text-[var(--color-ai)]",
  },
  SOURCE_UNVERIFIED: {
    label: "SOURCE UNVERIFIED",
    colorClass: "bg-[var(--color-danger-bg)] border-[var(--color-danger-border)] text-[var(--color-danger)]",
  },
  FACT: {
    label: "FACT",
    colorClass: "badge-epistemic-fact",
  },
  OBSERVED: {
    label: "OBSERVED",
    colorClass: "badge-epistemic-observed",
  },
  DERIVED: {
    label: "DERIVED",
    colorClass: "badge-epistemic-derived",
  },
  INTERPRETATION: {
    label: "INTERPRETATION",
    colorClass: "badge-epistemic-interpretation",
  },
  PREDICTION: {
    label: "PREDICTION",
    colorClass: "badge-epistemic-prediction",
  },
};

export function DataStatusBadge({
  status,
  size = "xs",
  showDot = false,
  className,
}: DataStatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    colorClass: "bg-[var(--bg-secondary)] border-[var(--border-default)] text-[var(--text-muted)]",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-bold tracking-wider uppercase select-none transition-colors",
        size === "xs" ? "px-2 py-0.5 text-[9px]" : "px-2.5 py-0.5 text-[10px]",
        config.colorClass,
        className
      )}
    >
      {(showDot || config.dotClass) && config.dotClass && (
        <span
          className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", config.dotClass, {
            "animate-pulse": status === "LIVE" || status === "ACTIVE" || status === "NEW",
          })}
          aria-hidden="true"
        />
      )}
      {config.label}
    </span>
  );
}

/**
 * DataLayerBanner — top-of-section banner explaining data provenance
 */
export function DataLayerBanner({
  type,
  className,
}: {
  type: "live" | "modelled" | "intelligence" | "mixed";
  className?: string;
}) {
  const configs = {
    live: {
      bg: "bg-[var(--color-success-bg)] border-[var(--color-success-border)]",
      dot: "bg-[var(--color-success)] animate-pulse",
      title: "LIVE LEGISLATIVE DATA",
      desc: "Recently discovered. Not yet modelled. Provenance tracked.",
      badge: <DataStatusBadge status="LIVE" showDot />,
    },
    modelled: {
      bg: "bg-[var(--color-model)]/10 border-[var(--color-model)]/25",
      dot: "bg-[var(--color-model)]",
      title: "FROZEN ANALYTICAL MODEL",
      desc: "Quantitative market model available. Event study horizons: [-1,+1] to [-10,+10].",
      badge: <DataStatusBadge status="MODELLED" />,
    },
    intelligence: {
      bg: "bg-[var(--color-warning)]/10 border-[var(--color-warning)]/25",
      dot: "bg-[var(--color-warning)]",
      title: "QUALITATIVE INTELLIGENCE ONLY",
      desc: "Economic exposure analysis. No stock predictions available.",
      badge: <DataStatusBadge status="INTELLIGENCE" />,
    },
    mixed: {
      bg: "bg-[var(--bg-secondary)] border-[var(--border-default)]",
      dot: "bg-[var(--text-muted)]",
      title: "MIXED DATA LAYERS",
      desc: "Live discovery data and frozen analytical models displayed together. See individual record labels.",
      badge: null,
    },
  };

  const c = configs[type];
  return (
    <div
      className={cn(
        "flex items-start gap-3 px-4 py-3 rounded-xl border text-xs transition-colors",
        c.bg,
        className
      )}
      role="note"
    >
      <span className={cn("w-2 h-2 rounded-full mt-1 flex-shrink-0", c.dot)} aria-hidden="true" />
      <div>
        <span className="font-bold text-[var(--text-primary)] tracking-wider uppercase text-[10px]">
          {c.title}
        </span>
        <p className="text-[var(--text-secondary)] mt-0.5">{c.desc}</p>
      </div>
      {c.badge && <div className="ml-auto flex-shrink-0">{c.badge}</div>}
    </div>
  );
}

export default DataStatusBadge;
