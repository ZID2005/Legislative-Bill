/**
 * app/companies/page.tsx
 * =======================
 * Master Corporate Intelligence Universe (70 Companies).
 */

import type { Metadata } from "next";
import CompaniesContent from "./CompaniesContent";

export const metadata: Metadata = {
  title: "Corporate Intelligence Universe",
  description:
    "70 Master Corporate Entities indexed across Central and State legislative exposure networks. 47 Quantitative Securities, 20 Intelligence-Only Entities.",
};

export default function CompaniesPage() {
  return <CompaniesContent />;
}
