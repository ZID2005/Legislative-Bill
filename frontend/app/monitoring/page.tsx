/**
 * app/monitoring/page.tsx
 * ========================
 * Legislative Monitoring & Discovery Center — server entry point.
 * Task 8.14.9.
 */

import type { Metadata } from "next";
import { MonitoringCenterContent } from "./MonitoringCenterContent";

export const metadata: Metadata = {
  title: "Legislative Monitoring & Discovery Center",
  description:
    "Real-time legislative monitoring and discovery for Central Parliament and State Assemblies. "
    + "Automated change detection, source registry, check history, and AI-grounded analysis.",
};

export default function MonitoringPage() {
  return <MonitoringCenterContent />;
}
