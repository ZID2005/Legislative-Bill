/**
 * components/ui/Card.tsx
 * ======================
 * Institutional surface system: Card, CardHeader, CardTitle, CardBody, CardFooter,
 * and calibrated StatCard KPI tiles for Seance.
 *
 * Implements:
 * - Surface hierarchy: surface (default), secondary, elevated, subtle
 * - Interactive hover and elevation transitions
 * - Dual-theme calibrated colors for StatCard KPI highlights and trends
 */

import React from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Base Card
// ---------------------------------------------------------------------------

export type CardVariant = "default" | "surface" | "secondary" | "elevated" | "subtle";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  id?: string;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  variant?: CardVariant;
  hover?: boolean;
  interactive?: boolean;
}

const paddingClasses = {
  none: "",
  sm: "p-3.5",
  md: "p-5",
  lg: "p-6",
};

const variantSurfaceClasses: Record<CardVariant, string> = {
  default: "bg-[var(--bg-card)] border-[var(--border-default)] shadow-xs",
  surface: "bg-[var(--bg-surface)] border-[var(--border-default)] shadow-xs",
  secondary: "bg-[var(--bg-secondary)] border-[var(--border-default)] shadow-xs",
  elevated: "bg-[var(--bg-elevated)] border-[var(--border-strong)] shadow-md",
  subtle: "bg-[var(--bg-secondary)]/50 border-[var(--border-subtle)]",
};

export function Card({
  children,
  id,
  className,
  padding = "md",
  variant = "default",
  hover = false,
  interactive = false,
  onClick,
  ...props
}: CardProps) {
  const isInteractive = interactive || hover || !!onClick;

  return (
    <div
      id={id}
      onClick={onClick}
      role={isInteractive && onClick ? "button" : undefined}
      tabIndex={isInteractive && onClick ? 0 : undefined}
      className={cn(
        "border rounded-xl transition-all duration-200",
        variantSurfaceClasses[variant],
        isInteractive && [
          "cursor-pointer hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]",
          "hover:shadow-md hover:-translate-y-[1px] active:translate-y-0",
        ],
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card Layout Helpers
// ---------------------------------------------------------------------------

export function CardHeader({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between pb-3.5 mb-4 border-b border-[var(--border-default)]",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h3 className={cn("text-sm font-semibold tracking-tight text-[var(--text-primary)]", className)}>
      {children}
    </h3>
  );
}

export function CardDescription({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p className={cn("text-xs text-[var(--text-muted)] mt-0.5", className)}>
      {children}
    </p>
  );
}

export function CardBody({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("space-y-3", className)}>{children}</div>;
}

export const CardContent = CardBody;

export function CardFooter({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "pt-3.5 mt-4 border-t border-[var(--border-default)] flex items-center justify-between text-xs text-[var(--text-muted)]",
        className
      )}
    >
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// StatCard — Calibrated Institutional KPI Tile
// ---------------------------------------------------------------------------

export interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string | number;
  subLabel?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  highlight?: "default" | "blue" | "emerald" | "amber" | "rose" | "purple";
  className?: string;
  id?: string;
}

const highlightBorderMap = {
  default: "border-[var(--border-default)]",
  blue: "border-[var(--action-primary)]/40",
  emerald: "border-[var(--color-positive)]/40",
  amber: "border-[var(--color-warning)]/40",
  rose: "border-[var(--color-negative)]/40",
  purple: "border-[var(--color-model)]/40",
};

const highlightTextMap = {
  default: "text-[var(--text-primary)]",
  blue: "text-[var(--action-primary)]",
  emerald: "text-[var(--color-positive)]",
  amber: "text-[var(--color-warning)]",
  rose: "text-[var(--color-negative)]",
  purple: "text-[var(--color-model)]",
};

export function StatCard({
  label,
  value,
  subValue,
  subLabel,
  icon,
  trend,
  highlight = "default",
  className,
  id,
}: StatCardProps) {
  const trendIcon = trend === "up" ? "↑" : trend === "down" ? "↓" : null;
  const trendColor =
    trend === "up"
      ? "text-[var(--color-positive)]"
      : trend === "down"
      ? "text-[var(--color-negative)]"
      : "text-[var(--text-muted)]";

  return (
    <div
      id={id}
      className={cn(
        "bg-[var(--bg-card)] rounded-xl p-5 border shadow-xs transition-all duration-200",
        highlightBorderMap[highlight],
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
          {label}
        </p>
        {icon && (
          <span className="text-[var(--text-muted)] text-base inline-flex items-center" aria-hidden="true">
            {icon}
          </span>
        )}
      </div>
      <p
        className={cn(
          "text-2xl font-bold tracking-tight text-[var(--text-primary)] font-tabular tabular-nums",
          highlightTextMap[highlight]
        )}
      >
        {typeof value === "number"
          ? new Intl.NumberFormat("en-IN").format(value)
          : value}
      </p>
      {(subValue !== undefined || subLabel) && (
        <p className={cn("text-xs mt-2 font-medium flex items-center gap-1", trendColor)}>
          {trendIcon && <span aria-hidden="true">{trendIcon}</span>}
          <span className="font-tabular tabular-nums">
            {subValue !== undefined &&
              (typeof subValue === "number"
                ? new Intl.NumberFormat("en-IN").format(subValue)
                : subValue)}
            {subLabel && ` ${subLabel}`}
          </span>
        </p>
      )}
    </div>
  );
}

export default Card;
