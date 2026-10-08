/**
 * app/states/[state]/page.tsx
 * ============================
 * State Legislative Detail Dossier.
 */

import type { Metadata } from "next";
import StateDetailContent from "./StateDetailContent";

interface Params {
  params: Promise<{ state: string }>;
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { state } = await params;
  const decoded = decodeURIComponent(state);
  return {
    title: `${decoded} — State Legislative Intelligence`,
    description: `Sub-national legislative dossier for ${decoded}. Assembly acts, corporate operational footprints, and statutory invariant adherence.`,
  };
}

export default async function StateDetailPage({ params }: Params) {
  const { state } = await params;
  return <StateDetailContent stateParam={state} />;
}
