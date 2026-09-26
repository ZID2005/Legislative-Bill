import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";
export const metadata: Metadata = { title: "States", description: "State legislative coverage — 4 active, 24 planned." };
export default function StatesPage() {
  return (
    <PlaceholderPage title="State Coverage" icon="🗺"
      description="India state legislative coverage. 4 active pilot states with 44 bills and 86 corporate exposures. 24 planned expansion states with 0 ingested bills. State stock predictions: strictly 0."
      sections={[
        { name: "Active States", description: "AP, Karnataka, Kerala, Telangana — 44 bills total" },
        { name: "Coverage Map", description: "Visual India state map with capability indicators" },
        { name: "Planned States", description: "24 roadmap states with planned ingestion dates" },
        { name: "State Bills", description: "Per-state bill listing with official sources" },
      ]}
    />
  );
}
