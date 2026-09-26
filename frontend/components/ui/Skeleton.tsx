/**
 * components/ui/Skeleton.tsx
 * ==========================
 * Loading skeleton placeholders, EmptyState, and ErrorState components.
 */

import React from "react";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/lib/errors";

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
        "animate-pulse rounded bg-slate-800",
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
          className="h-4"
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
        "bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-3",
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
    <div className={cn("space-y-0.5", className)} aria-hidden="true">
      {/* Header */}
      <div className="flex gap-4 px-4 py-2 bg-slate-800/50 rounded-t">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-3.5 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="flex gap-4 px-4 py-3 border-b border-slate-800"
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
        "flex flex-col items-center justify-center py-16 px-6 text-center",
        className
      )}
      role="status"
    >
      {icon && (
        <div
          className="text-4xl mb-4 text-slate-600"
          aria-hidden="true"
        >
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-slate-300 mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-slate-500 max-w-md mb-6">{description}</p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ErrorState (API errors)
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
        "flex flex-col items-center justify-center py-12 px-6 text-center",
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <div className="text-3xl mb-3 text-rose-500" aria-hidden="true">
        ⚠
      </div>
      <h3 className="text-sm font-semibold text-rose-300 mb-2">
        Unable to load data
      </h3>
      <p className="text-sm text-slate-400 max-w-sm mb-5">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-sm text-blue-400 hover:text-blue-300 underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
        >
          Try again
        </button>
      )}
    </div>
  );
}
