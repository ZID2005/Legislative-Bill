/**
 * app/overview/page.tsx
 * =====================
 * Platform Overview — fetches real coverage data from GET /api/v1/coverage.
 *
 * CRITICAL RULES:
 * - All statistics fetched from API, NEVER hardcoded
 * - If API is unavailable, shows proper error state
 * - State stock predictions always shown as 0 (statutory guarantee)
 */

import type { Metadata } from "next";
import { Suspense } from "react";
import OverviewContent from "./OverviewContent";
import { SkeletonCard } from "@/components/ui/Skeleton";

export const metadata: Metadata = {
  title: "Overview",
  description: "India Legislative Intelligence Platform — platform coverage and capability overview.",
};

function OverviewSkeleton() {
  return (
    <div className="p-6 space-y-6">
      <div className="h-8 w-80 bg-slate-800 rounded animate-pulse" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </div>
  );
}

export default function OverviewPage() {
  return (
    <Suspense fallback={<OverviewSkeleton />}>
      <OverviewContent />
    </Suspense>
  );
}
