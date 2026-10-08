/**
 * app/states/page.tsx
 * ====================
 * Sub-National Legislative Intelligence Registry (States).
 */

import type { Metadata } from "next";
import StatesContent from "./StatesContent";

export const metadata: Metadata = {
  title: "State Legislative Intelligence Registry",
  description:
    "Sub-national legislative coverage: 4 active pilot states (44 acts, 86 exposures) and 24 planned expansion states. State stock predictions: strictly 0.",
};

export default function StatesPage() {
  return <StatesContent />;
}
