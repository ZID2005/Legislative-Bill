/**
 * app/coverage/page.tsx
 * ========================
 * Platform Coverage & Research Integrity — server entry point.
 * Task 8.14.9.
 */

import type { Metadata } from "next";
import { CoverageContent } from "./CoverageContent";

export const metadata: Metadata = {
  title: "Platform Coverage & Research Integrity",
  description:
    "Repository-verified coverage metrics for the India Legislative Intelligence Platform. "
    + "Central Parliament: 20 bills, 47 companies, 4,700 predictions. "
    + "State: 4 states, 44 bills, 0 predictions. "
    + "Company: 70 total, 47 quantitative.",
};

export default function CoveragePage() {
  return <CoverageContent />;
}
