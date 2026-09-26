import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";

export const metadata: Metadata = {
  title: "Companies",
  description: "Corporate intelligence universe — quantitative and intelligence entities.",
};

export default function CompaniesPage() {
  return (
    <PlaceholderPage
      title="Companies"
      icon="🏢"
      description="Corporate intelligence universe. 70 total entities: 47 quantitative prediction-eligible companies, 20 intelligence-only entities, and 3 reference records. Protected by an active quantitative firewall."
      sections={[
        { name: "Quantitative Universe", description: "47 NSE/BSE listed companies with market predictions" },
        { name: "Intelligence Entities", description: "20 unlisted/state entities — qualitative only" },
        { name: "Exposure Network", description: "104 evidence-backed legislative exposure records" },
        { name: "Sector Filter", description: "Browse by economic sector and industry" },
      ]}
      comingSections={[
        "Full paginated company listing with filters",
        "Quantitative vs Intelligence visual distinction",
        "Exposure count sorting",
      ]}
    />
  );
}
