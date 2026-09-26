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
    <Suspense fallback={<div className="min-h-screen bg-slate-950 p-8 text-slate-400">Loading risk analytics...</div>}>
      <RiskContent />
    </Suspense>
  );
}

