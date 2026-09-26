/**
 * app/sectors/page.tsx
 * ====================
 * Macro Sector Directory page.
 */

import type { Metadata } from "next";
import SectorsContent from "./SectorsContent";

export const metadata: Metadata = {
  title: "Macro Economic Sectors — Legislative Intelligence",
  description:
    "Explore India's macroeconomic sectors mapped against Central & State legislative interventions, corporate exposures, and quantified transmission mechanisms.",
};

export default function SectorsPage() {
  return <SectorsContent />;
}
