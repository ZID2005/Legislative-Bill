/**
 * app/explorer/page.tsx
 * =====================
 * India Legislative Explorer Page.
 * Wraps ExplorerContent in Suspense for App Router searchParams.
 */

import type { Metadata } from "next";
import { Suspense } from "react";
import ExplorerContent from "./ExplorerContent";
import { SkeletonCard } from "@/components/ui/Skeleton";

export const metadata: Metadata = {
  title: "India Legislative Explorer",
  description:
    "Search and explore Central and State legislation, economic intelligence, corporate exposure, and market-model availability across the Indian Union.",
};

function ExplorerSkeleton() {
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-pulse">
      <div className="h-8 w-72 bg-slate-800 rounded" />
      <div className="h-10 w-full bg-slate-800 rounded" />
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="h-96 bg-slate-800/60 rounded-xl" />
        <div className="lg:col-span-3 space-y-4">
          {[...Array(5)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ExplorerPage() {
  return (
    <Suspense fallback={<ExplorerSkeleton />}>
      <ExplorerContent />
    </Suspense>
  );
}
