/**
 * app/companies/[companyId]/page.tsx
 * ===================================
 * Company detail dossier with Intelligence Firewall.
 */

import type { Metadata } from "next";
import CompanyDetailContent from "./CompanyDetailContent";

interface Params {
  params: Promise<{ companyId: string }>;
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { companyId } = await params;
  return {
    title: `Company: ${companyId}`,
    description: `Corporate intelligence dossier for ${companyId}.`,
  };
}

export default async function CompanyDetailPage({ params }: Params) {
  const { companyId } = await params;
  return <CompanyDetailContent companyId={companyId} />;
}
