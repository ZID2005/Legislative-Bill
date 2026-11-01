/**
 * components/ui/Skeleton.tsx
 * ==========================
 * Standardized loading skeleton placeholders, EmptyState, and ErrorState components.
 * Dual-theme synchronized for light and dark modes with accessible recovery flows.
 */

import React from "react";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/lib/errors";
import { AlertCircleIcon, AlertTriangleIcon } from "./Icons";
import { Button } from "./Button";

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

export function Skeleton({
  className,
  height,
  width,
  style,
}: {
  className?: string;
  height?: string;
  width?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-[var(--skeleton-bg)]",
        className
      )}
      style={{ height, width, ...style }}
      aria-hidden="true"
    />
  );
}

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-3.5"
          width={i === lines - 1 ? "60%" : "100%"}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 space-y-3 shadow-xs",
        className
      )}
      aria-hidden="true"
    >
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-5 w-3/4" />
      <SkeletonText lines={2} />
      <div className="flex gap-2 pt-1">
        <Skeleton className="h-5 w-20 rounded-full" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
    </div>
  );
}

export function SkeletonTable({
  rows = 5,
  columns = 4,
  className,
}: {
  rows?: number;
  columns?: number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "space-y-0.5 rounded-xl border border-[var(--border-default)] overflow-hidden bg-[var(--bg-surface)]",
        className
      )}
      aria-hidden="true"
    >
      {/* Header */}
      <div className="flex gap-4 px-4 py-3 bg-[var(--bg-base)] border-b border-[var(--border-default)]">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-3.5 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="flex gap-4 px-4 py-3.5 border-b border-[var(--border-subtle)] last:border-b-0"
        >
          {Array.from({ length: columns }).map((_, j) => (
            <Skeleton key={j} className="h-4 flex-1" style={{ opacity: 1 - i * 0.12 }} />
          ))}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// EmptyState
// ---------------------------------------------------------------------------

export interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-6 text-center rounded-xl border border-dashed border-[var(--border-default)] bg-[var(--bg-secondary)]/30",
        className
      )}
      role="status"
    >
      {icon ? (
        <div className="mb-4 text-[var(--text-muted)] inline-flex items-center" aria-hidden="true">
          {icon}
        </div>
      ) : (
        <div className="mb-4 p-3 rounded-full bg-[var(--bg-card)] border border-[var(--border-default)] text-[var(--text-muted)]" aria-hidden="true">
          <AlertCircleIcon size="lg" />
        </div>
      )}
      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1.5">{title}</h3>
      {description && (
        <p className="text-xs text-[var(--text-muted)] max-w-md mb-5 leading-relaxed">{description}</p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ErrorState (API & Runtime Errors)
// ---------------------------------------------------------------------------

export interface ErrorStateProps {
  error: ApiError | Error | string | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ error, onRetry, className }: ErrorStateProps) {
  const message =
    typeof error === "string"
      ? error
      : error && "userMessage" in error
      ? (error as ApiError).userMessage
      : error?.message ?? "An unexpected error occurred.";

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-6 text-center rounded-xl border border-[var(--color-danger-border)] bg-[var(--color-danger-bg)]",
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <div className="mb-3 text-[var(--color-danger)]" aria-hidden="true">
        <AlertTriangleIcon size="lg" />
      </div>
      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">
        Unable to load data
      </h3>
      <p className="text-xs text-[var(--text-muted)] max-w-sm mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="border-[var(--color-danger-border)] text-[var(--text-primary)] hover:bg-[var(--color-danger-bg)]"
        >
          Try again
        </Button>
      )}
    </div>
  );
}

export default Skeleton;
