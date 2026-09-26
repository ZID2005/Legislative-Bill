/**
 * app/bills/page.tsx
 * ==================
 * Bill listing page with filters.
 */

import type { Metadata } from "next";
import BillsContent from "./BillsContent";

export const metadata: Metadata = {
  title: "Bills",
  description: "Central and State legislative bills directory with comprehensive filtering.",
};

export default function BillsPage() {
  return <BillsContent />;
}
