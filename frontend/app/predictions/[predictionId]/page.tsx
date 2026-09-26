import type { Metadata } from "next";
import { Suspense } from "react";
import PredictionDetailContent from "./PredictionDetailContent";

export const metadata: Metadata = {
  title: "Prediction Dossier | India Legislative Pulse",
  description: "Comprehensive quantitative prediction dossier with decision support, risk categorization, pre-event anticipation context, and epistemic separation.",
};

export default async function PredictionDetailPage({
  params,
}: {
  params: Promise<{ predictionId: string }>;
}) {
  const { predictionId } = await params;

  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 p-8 text-slate-400">Loading prediction dossier...</div>}>
      <PredictionDetailContent predictionId={predictionId} />
    </Suspense>
  );
}

