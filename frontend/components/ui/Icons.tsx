/**
 * components/ui/Icons.tsx
 * =======================
 * Seance Standardized Vector Icon System.
 *
 * Lightweight, zero-dependency, institutional-grade SVGs:
 * - Fixed 24x24 viewBox with calibrated stroke weights (1.75 - 2px)
 * - Uses `currentColor` for seamless theme synchronization
 * - Accessible by default with `aria-hidden="true"` (or custom label)
 * - Predictable sizing scale: xs (12px), sm (14px), md (16px), lg (20px), xl (24px)
 *
 * Replaces secondary interface emojis across navigation, tables, and toolbars
 * while maintaining brand distinction from `BrandEmblem`.
 */

import React from "react";
import { cn } from "@/lib/utils";

export type IconSize = "xs" | "sm" | "md" | "lg" | "xl" | number;

export interface IconProps extends React.SVGAttributes<SVGSVGElement> {
  size?: IconSize;
  className?: string;
  title?: string;
}

function resolveSizeClasses(size: IconSize): { sizeClass?: string; inlineSize?: number } {
  if (typeof size === "number") {
    return { inlineSize: size };
  }
  switch (size) {
    case "xs":
      return { sizeClass: "w-3 h-3" };
    case "sm":
      return { sizeClass: "w-3.5 h-3.5" };
    case "md":
      return { sizeClass: "w-4 h-4" };
    case "lg":
      return { sizeClass: "w-5 h-5" };
    case "xl":
      return { sizeClass: "w-6 h-6" };
    default:
      return { sizeClass: "w-4 h-4" };
  }
}

function BaseSvg({
  size = "md",
  className,
  title,
  children,
  ...props
}: IconProps & { children: React.ReactNode }) {
  const { sizeClass, inlineSize } = resolveSizeClasses(size);
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("inline-block flex-shrink-0 align-middle", sizeClass, className)}
      style={inlineSize ? { width: inlineSize, height: inlineSize } : undefined}
      aria-hidden={title ? undefined : "true"}
      role={title ? "img" : undefined}
      aria-label={title}
      {...props}
    >
      {title && <title>{title}</title>}
      {children}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Navigation & Institutional Hub Icons
// ---------------------------------------------------------------------------

export function WorkspaceIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M3 21h18M3 10h18M5 10v11M19 10v11M9 10v11M15 10v11M12 3l9 7H3l9-7z" />
    </BaseSvg>
  );
}

export function BillsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
    </BaseSvg>
  );
}

export function ExplorerIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.35-4.35M11 8v6M8 11h6" />
    </BaseSvg>
  );
}

export function StatesIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
      <line x1="8" y1="2" x2="8" y2="18" />
      <line x1="16" y1="6" x2="16" y2="22" />
    </BaseSvg>
  );
}

export function LatestBillsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </BaseSvg>
  );
}

export function CalendarIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </BaseSvg>
  );
}

export function FeedIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="12" cy="12" r="2" />
      <path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 19.07a10 10 0 0 1 0-14.14" />
    </BaseSvg>
  );
}

export function CompareIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="18" cy="18" r="3" />
      <circle cx="6" cy="6" r="3" />
      <path d="M13 6h3a2 2 0 0 1 2 2v7M11 18H8a2 2 0 0 1-2-2V9" />
    </BaseSvg>
  );
}

export function OverviewIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" />
      <rect x="3" y="16" width="7" height="5" rx="1" />
    </BaseSvg>
  );
}

export function PredictionsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </BaseSvg>
  );
}

export function RiskIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </BaseSvg>
  );
}

export function AnticipationIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="12" cy="13" r="8" />
      <path d="M12 9v4l2.5 2.5M10 2h4M12 2v3" />
    </BaseSvg>
  );
}

export function CompaniesIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" />
      <path d="M6 12H4a2 2 0 0 0-2 2v8h4M18 9h2a2 2 0 0 1 2 2v11h-4" />
      <path d="M10 6h4M10 10h4M10 14h4M10 18h4" />
    </BaseSvg>
  );
}

export function IndustriesIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M2 20h20M4 20V9l6 4V9l6 4V4h4v16" />
    </BaseSvg>
  );
}

export function SectorsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M12 2l7.5 4.33v8.67L12 22l-7.5-4.33V6.33z" />
      <path d="M12 12l7.5-3M12 12v10M12 12L4.5 9" />
    </BaseSvg>
  );
}

export function PortfolioIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </BaseSvg>
  );
}

export function ReportsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </BaseSvg>
  );
}

export function AiAnalystIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4z" />
      <path d="M18 2l1 2.5L21.5 5.5 19 6.5 18 9l-1-2.5-2.5-1 2.5-1z" strokeWidth={1.4} />
    </BaseSvg>
  );
}

export function MonitoringIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <path d="M22 10H2M7 15l2-3 3 5 3-4 2 2" />
    </BaseSvg>
  );
}

export function CoverageIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="m9 12 2 2 4-4" />
    </BaseSvg>
  );
}

export function WatchlistIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </BaseSvg>
  );
}

export function AlertsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </BaseSvg>
  );
}

export function NotificationsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M22 12h-6l-2 3h-4l-2-3H2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-7z" />
      <path d="M5.45 5.11 2 12v0h20v0l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </BaseSvg>
  );
}

export function SettingsIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </BaseSvg>
  );
}

// ---------------------------------------------------------------------------
// Control & Interaction Icons
// ---------------------------------------------------------------------------

export function SearchIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </BaseSvg>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </BaseSvg>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polyline points="20 6 9 17 4 12" />
    </BaseSvg>
  );
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </BaseSvg>
  );
}

export function ChevronDownIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polyline points="6 9 12 15 18 9" />
    </BaseSvg>
  );
}

export function ChevronUpIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polyline points="18 15 12 9 6 15" />
    </BaseSvg>
  );
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polyline points="9 18 15 12 9 6" />
    </BaseSvg>
  );
}

export function ChevronLeftIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polyline points="15 18 9 12 15 6" />
    </BaseSvg>
  );
}

export function ArrowUpIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <line x1="12" y1="19" x2="12" y2="5" />
      <polyline points="5 12 12 5 19 12" />
    </BaseSvg>
  );
}

export function ArrowDownIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <line x1="12" y1="5" x2="12" y2="19" />
      <polyline points="19 12 12 19 5 12" />
    </BaseSvg>
  );
}

export function ArrowUpDownIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="m7 15 5 5 5-5M7 9l5-5 5 5" />
    </BaseSvg>
  );
}

export function FilterIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </BaseSvg>
  );
}

export function DownloadIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </BaseSvg>
  );
}

export function ExternalLinkIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </BaseSvg>
  );
}

export function MaximizeIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
    </BaseSvg>
  );
}

export function MinimizeIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
    </BaseSvg>
  );
}

export function ZoomInIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </BaseSvg>
  );
}

export function ZoomOutIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </BaseSvg>
  );
}

export function InfoIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </BaseSvg>
  );
}

export function AlertCircleIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </BaseSvg>
  );
}

export function AlertTriangleIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </BaseSvg>
  );
}

export function ShieldIcon(props: IconProps) {
  return (
    <BaseSvg {...props}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </BaseSvg>
  );
}

export function SpinnerIcon({ className, size = "md", ...props }: IconProps) {
  const { sizeClass, inlineSize } = resolveSizeClasses(size);
  return (
    <svg
      className={cn("animate-spin text-current", sizeClass, className)}
      style={inlineSize ? { width: inlineSize, height: inlineSize } : undefined}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
      {...props}
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
