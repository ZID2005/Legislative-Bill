/**
 * app/ai-analyst/page.tsx
 * =======================
 * Grounded AI Analyst Terminal.
 */

import type { Metadata } from "next";
import AIAnalystContent from "./AIAnalystContent";

export const metadata: Metadata = {
  title: "Grounded AI Analyst Terminal",
  description:
    "Institutional conversational research terminal grounded in official parliamentary records, state gazettes, and econometric exposure networks. Zero financial advice.",
};

export default function AIAnalystPage() {
  return <AIAnalystContent />;
}
