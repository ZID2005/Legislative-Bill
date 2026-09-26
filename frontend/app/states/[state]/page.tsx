import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";
export const metadata: Metadata = { title: "State Detail" };
export default async function StateDetailPage({ params }: { params: Promise<{ state: string }> }) {
  const { state } = await params;
  const stateName = decodeURIComponent(state);
  return (
    <PlaceholderPage title={`State: ${stateName}`} icon="🗺"
      description={`State legislative intelligence for ${stateName}. Includes bills, corporate exposures, economic sectors, and coverage status. State stock predictions: strictly 0.`}
      sections={[
        { name: "State Profile", description: "Legislative assembly, authority, economic sectors" },
        { name: "Bills", description: "State assembly bills with official PDF sources" },
        { name: "Corporate Exposures", description: "Evidence-backed company exposure records" },
        { name: "Prediction Status", description: "Statutory guarantee: 0 stock predictions" },
      ]}
    />
  );
}
