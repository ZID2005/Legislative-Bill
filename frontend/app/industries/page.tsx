import type { Metadata } from "next";
import IndustriesContent from "./IndustriesContent";

export const metadata: Metadata = {
  title: "Industry Intelligence | India Legislative Platform",
  description:
    "Connect Indian Parliamentary and State legislation with affected economic sectors, member companies, transmission mechanisms, and available market analytics.",
};

export default function IndustriesPage() {
  return <IndustriesContent />;
}
