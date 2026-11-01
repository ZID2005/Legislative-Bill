import type { Metadata } from "next";
import { Suspense } from "react";
import RiskContent from "./RiskContent";

export const metadata: Metadata = {
  title: "Institutional Risk Analytics | India Legislative Pulse",
  description:
    "Institutional multi-horizon legislative risk classifications across 4,700 decision support records. Deterministic risk bands, sector dispersion, and portfolio-level risk aggregation.",
};

export default function RiskPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--bg-base)] p-8 text-[var(--text-muted)]">Loading risk analytics...</div>}>
      <RiskContent />
    </Suspense>
  );
}

