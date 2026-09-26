/**
 * app/industries/[industryId]/page.tsx
 * =====================================
 * Plural route alias to singular Industry Intelligence Dossier.
 */

import type { Metadata } from "next";
import IndustryDetailContent from "@/app/industry/[industryId]/IndustryDetailContent";

interface Params {
  params: Promise<{ industryId: string }>;
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { industryId } = await params;
  const decoded = decodeURIComponent(industryId).replace(/-/g, " ");
  const title = decoded
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  return {
    title: `${title} — Industry Intelligence Dossier`,
    description: `Comprehensive legislative footprint, corporate exposure, and economic transmission mechanisms for ${title}.`,
  };
}

export default async function PluralIndustryDetailPage({ params }: Params) {
  const { industryId } = await params;
  return <IndustryDetailContent industryId={industryId} />;
}
