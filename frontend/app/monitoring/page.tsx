/**
 * app/monitoring/page.tsx
 * ========================
 * Legislative Monitoring & Discovery Center — server entry point.
 * Task 8.14.9.
 */

import { Suspense } from "react";
import type { Metadata } from "next";
import { MonitoringCenterContent } from "./MonitoringCenterContent";

export const metadata: Metadata = {
  title: "Legislative Monitoring & Discovery Center",
  description:
    "Real-time legislative monitoring and discovery for Central Parliament and State Assemblies. "
    + "Automated change detection, source registry, check history, and AI-grounded analysis.",
};

function MonitoringLoadingFallback() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] p-8 text-xs font-mono text-[var(--text-muted)] flex items-center justify-center">
      <div className="flex items-center gap-3">
        <span className="w-2 h-2 rounded-full bg-[var(--accent-primary)] animate-ping" />
        <span>Loading institutional monitoring center…</span>
      </div>
    </div>
  );
}

export default function MonitoringPage() {
  return (
    <Suspense fallback={<MonitoringLoadingFallback />}>
      <MonitoringCenterContent />
    </Suspense>
  );
}

