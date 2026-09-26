/**
 * components/ui/Card.tsx
 * ======================
 * Card container and StatCard components for the analytics platform.
 */

import React from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Base Card
// ---------------------------------------------------------------------------

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  hover?: boolean;
}

const paddingClasses = {
  none: "",
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
};

export function Card({
  children,
  className,
  padding = "md",
  hover = false,
}: CardProps) {
  return (
    <div
      className={cn(
        "bg-slate-900 border border-slate-800 rounded-lg",
        hover &&
          "hover:border-slate-700 hover:bg-slate-800/50 transition-all duration-200 cursor-pointer",
        paddingClasses[padding],
        className
      )}
    >
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card Header, Body, Footer helpers
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
        "flex items-center justify-between pb-3 mb-4 border-b border-slate-800",
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
    <h3 className={cn("text-sm font-semibold text-slate-200", className)}>
      {children}
    </h3>
  );
}

export function CardBody({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("", className)}>{children}</div>;
}

// ---------------------------------------------------------------------------
// StatCard — KPI metric tile
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
}

const highlightBorderMap = {
  default: "border-slate-800",
  blue: "border-blue-700/50",
  emerald: "border-emerald-700/50",
  amber: "border-amber-700/50",
  rose: "border-rose-700/50",
  purple: "border-purple-700/50",
};

const highlightTextMap = {
  default: "text-white",
  blue: "text-blue-300",
  emerald: "text-emerald-300",
  amber: "text-amber-300",
  rose: "text-rose-300",
  purple: "text-purple-300",
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
}: StatCardProps) {
  const trendIcon =
    trend === "up" ? "↑" : trend === "down" ? "↓" : null;
  const trendColor =
    trend === "up"
      ? "text-emerald-400"
      : trend === "down"
      ? "text-rose-400"
      : "text-slate-400";

  return (
    <div
      className={cn(
        "bg-slate-900 rounded-lg p-5 border",
        highlightBorderMap[highlight],
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          {label}
        </p>
        {icon && (
          <span className="text-slate-500 text-base" aria-hidden="true">
            {icon}
          </span>
        )}
      </div>
      <p
        className={cn(
          "text-2xl font-bold tracking-tight",
          highlightTextMap[highlight]
        )}
      >
        {typeof value === "number"
          ? new Intl.NumberFormat("en-IN").format(value)
          : value}
      </p>
      {(subValue !== undefined || subLabel) && (
        <p className={cn("text-xs mt-1.5", trendColor)}>
          {trendIcon && <span>{trendIcon} </span>}
          {subValue !== undefined &&
            (typeof subValue === "number"
              ? new Intl.NumberFormat("en-IN").format(subValue)
              : subValue)}
          {subLabel && ` ${subLabel}`}
        </p>
      )}
    </div>
  );
}

export default Card;
