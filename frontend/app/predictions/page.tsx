import type { Metadata } from "next";
import { Suspense } from "react";
import PredictionsContent from "./PredictionsContent";

export const metadata: Metadata = {
  title: "Prediction Analytics | India Legislative Pulse",
  description:
    "Empirical market impact predictions for Central Parliament legislation across 47 quantitative securities. Multi-window event horizon comparisons, confidence distributions, and epistemic provenance.",
};

export default function PredictionsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--bg-base)] p-8 text-[var(--text-muted)]">Loading prediction analytics...</div>}>
      <PredictionsContent />
    </Suspense>
  );
}

