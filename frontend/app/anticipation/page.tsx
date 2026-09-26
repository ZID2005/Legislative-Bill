import type { Metadata } from "next";
import { Suspense } from "react";
import AnticipationContent from "./AnticipationContent";

export const metadata: Metadata = {
  title: "Pre-Event Information Diffusion | India Legislative Pulse",
  description:
    "Pre-event information diffusion diagnostics and Anticipation Paradox analysis across 940 Central bill-company pairs. Multi-window CAR statistics and neutral classification tiers.",
};

export default function AnticipationPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 p-8 text-slate-400">Loading anticipation analytics...</div>}>
      <AnticipationContent />
    </Suspense>
  );
}

