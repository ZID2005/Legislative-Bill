/**
 * components/ui/DataStatusBadge.tsx
 * ====================================
 * Task 8.25 — Epistemic data type labels.
 *
 * Clearly distinguishes:
 *   LIVE          — recently discovered legislative data (not modelled)
 *   MODELLED      — quantitative market model available
 *   INTELLIGENCE  — qualitative economic analysis only
 *   PLANNED       — not yet ingested into the pipeline
 *   NEW           — just discovered
 *   RECENT        — discovered in the last 7 days
 *   ACTIVE        — currently in legislative process
 *   AMENDED       — bill has been amended
 *   PASSED        — enacted/passed
 *   ASSENT_PENDING — awaiting presidential/gubernatorial assent
 *   NOTIFIED      — published in official gazette
 *   ARCHIVED      — historical record
 *   UPCOMING      — scheduled for future consideration
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
    colorClass: "bg-emerald-500/12 border-emerald-500/25 text-emerald-400",
    dotClass: "bg-emerald-400",
  },
  MODELLED: {
    label: "MODELLED",
    colorClass: "bg-indigo-500/12 border-indigo-500/25 text-indigo-300",
  },
  INTELLIGENCE: {
    label: "INTELLIGENCE",
    colorClass: "bg-amber-500/12 border-amber-500/25 text-amber-400",
  },
  PLANNED: {
    label: "PLANNED",
    colorClass: "bg-slate-700/30 border-slate-600/30 text-slate-500",
  },
  NEW: {
    label: "NEW",
    colorClass: "bg-blue-500/12 border-blue-500/25 text-blue-400",
    dotClass: "bg-blue-400",
  },
  RECENT: {
    label: "RECENT",
    colorClass: "bg-teal-500/12 border-teal-500/25 text-teal-400",
  },
  ACTIVE: {
    label: "ACTIVE",
    colorClass: "bg-emerald-500/12 border-emerald-500/25 text-emerald-400",
    dotClass: "bg-emerald-400",
  },
  AMENDED: {
    label: "AMENDED",
    colorClass: "bg-orange-500/12 border-orange-500/25 text-orange-400",
  },
  PASSED: {
    label: "PASSED",
    colorClass: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300",
  },
  ASSENT_PENDING: {
    label: "ASSENT PENDING",
    colorClass: "bg-amber-500/12 border-amber-500/25 text-amber-400",
  },
  NOTIFIED: {
    label: "NOTIFIED",
    colorClass: "bg-blue-500/12 border-blue-500/25 text-blue-400",
  },
  ARCHIVED: {
    label: "ARCHIVED",
    colorClass: "bg-slate-700/30 border-slate-600/30 text-slate-500",
  },
  UPCOMING: {
    label: "UPCOMING",
    colorClass: "bg-violet-500/12 border-violet-500/25 text-violet-400",
  },
  SOURCE_UNVERIFIED: {
    label: "SOURCE UNVERIFIED",
    colorClass: "bg-rose-500/12 border-rose-500/25 text-rose-400",
  },
  FACT: {
    label: "FACT",
    colorClass: "bg-emerald-500/12 border-emerald-500/25 text-emerald-400",
  },
  OBSERVED: {
    label: "OBSERVED",
    colorClass: "bg-blue-500/12 border-blue-500/25 text-blue-400",
  },
  DERIVED: {
    label: "DERIVED",
    colorClass: "bg-indigo-500/12 border-indigo-500/25 text-indigo-400",
  },
  INTERPRETATION: {
    label: "INTERPRETATION",
    colorClass: "bg-amber-500/12 border-amber-500/25 text-amber-400",
  },
  PREDICTION: {
    label: "PREDICTION",
    colorClass: "bg-violet-500/12 border-violet-500/25 text-violet-400",
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
    colorClass: "bg-slate-700/30 border-slate-600/30 text-slate-500",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-bold tracking-wider uppercase",
        size === "xs" ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-[10px]",
        config.colorClass,
        className
      )}
    >
      {(showDot || config.dotClass) && config.dotClass && (
        <span
          className={cn("w-1 h-1 rounded-full flex-shrink-0", config.dotClass, {
            "animate-pulse": status === "LIVE" || status === "ACTIVE" || status === "NEW",
          })}
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
      bg: "bg-emerald-950/30 border-emerald-800/30",
      dot: "bg-emerald-400 animate-pulse",
      title: "LIVE LEGISLATIVE DATA",
      desc: "Recently discovered. Not yet modelled. Provenance tracked.",
      badge: <DataStatusBadge status="LIVE" showDot />,
    },
    modelled: {
      bg: "bg-indigo-950/30 border-indigo-800/30",
      dot: "bg-indigo-400",
      title: "FROZEN ANALYTICAL MODEL",
      desc: "Quantitative market model available. Event study horizons: [-1,+1] to [-10,+10].",
      badge: <DataStatusBadge status="MODELLED" />,
    },
    intelligence: {
      bg: "bg-amber-950/20 border-amber-800/20",
      dot: "bg-amber-400",
      title: "QUALITATIVE INTELLIGENCE ONLY",
      desc: "Economic exposure analysis. No stock predictions available.",
      badge: <DataStatusBadge status="INTELLIGENCE" />,
    },
    mixed: {
      bg: "bg-slate-900/60 border-slate-700/30",
      dot: "bg-slate-400",
      title: "MIXED DATA LAYERS",
      desc: "Live discovery data and frozen analytical models displayed together. See individual record labels.",
      badge: null,
    },
  };

  const c = configs[type];
  return (
    <div
      className={cn(
        "flex items-start gap-3 px-4 py-3 rounded-lg border text-xs",
        c.bg,
        className
      )}
      role="note"
    >
      <span className={cn("w-2 h-2 rounded-full mt-0.5 flex-shrink-0", c.dot)} />
      <div>
        <span className="font-bold text-slate-200 tracking-wider uppercase text-[10px]">
          {c.title}
        </span>
        <p className="text-slate-400 mt-0.5">{c.desc}</p>
      </div>
      {c.badge && <div className="ml-auto flex-shrink-0">{c.badge}</div>}
    </div>
  );
}

export default DataStatusBadge;
