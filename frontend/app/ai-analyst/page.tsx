import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";
export const metadata: Metadata = { title: "AI Analyst" };
export default function AIAnalystPage() {
  return (
    <PlaceholderPage title="AI Analyst" icon="✦"
      description="Groq LLM-powered AI analyst for legislative intelligence. Grounded Q&A on bills and companies with FACT/DERIVED/INTERPRETATION/PREDICTION source distinctions. No financial advice."
      sections={[
        { name: "Ask a Question", description: "Query the AI on any bill or company in context" },
        { name: "Persona Selection", description: "General Public / Investor / Policy Researcher perspectives" },
        { name: "Source Citations", description: "All answers grounded in official legislative records" },
        { name: "FACT/DERIVED/INTERPRETATION/PREDICTION labels", description: "Clear epistemic status on each claim" },
      ]}
    />
  );
}
