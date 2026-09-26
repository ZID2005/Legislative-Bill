import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";
export const metadata: Metadata = { title: "Compare Bills" };
export default function CompareePage() {
  return (
    <PlaceholderPage title="Bill Comparison" icon="⚖"
      description="Side-by-side comparison of two or more Central bills. Compare provisions, corporate exposures, predictions, and AI analysis."
      sections={[
        { name: "Bill Selector", description: "Select up to 3 bills to compare" },
        { name: "Provision Comparison", description: "Side-by-side regulatory provisions" },
        { name: "Exposure Overlap", description: "Companies affected by multiple bills" },
        { name: "Prediction Comparison", description: "Market predictions across bills for same companies" },
      ]}
    />
  );
}
