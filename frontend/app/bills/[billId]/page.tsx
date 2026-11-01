import type { Metadata } from "next";
import { Suspense } from "react";
import BillDetailContent from "./BillDetailContent";

interface Params {
  params: Promise<{ billId: string }>;
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { billId } = await params;
  return {
    title: `Bill: ${billId}`,
    description: `Legislative dossier for bill ${billId}.`,
  };
}

export default async function BillDetailPage({ params }: Params) {
  const { billId } = await params;
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--bg-base)] p-8 text-[var(--text-muted)]">Loading legislative dossier...</div>}>
      <BillDetailContent billId={billId} />
    </Suspense>
  );
}
