/**
 * app/bills/[billId]/page.tsx
 * ===========================
 * Bill detail dossier — fetches real data from API.
 * Applies State Prediction Firewall for State bills.
 */

import type { Metadata } from "next";
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
  return <BillDetailContent billId={billId} />;
}
