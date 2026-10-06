import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return "0";
  return new Intl.NumberFormat("en-IN").format(value);
}

export function formatDate(dateStr: string | Date | null | undefined): string {
  if (!dateStr) return "—";
  try {
    const d = typeof dateStr === "string" ? new Date(dateStr) : dateStr;
    if (isNaN(d.getTime())) return String(dateStr);
    return new Intl.DateTimeFormat("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(d);
  } catch {
    return String(dateStr);
  }
}

export type CapabilityLevel = 1 | 2 | 3;

export function getCapabilityLevel(
  jurisdiction?: string | null,
  eligibility?: string | null
): CapabilityLevel {
  const jur = jurisdiction?.trim().toLowerCase();
  const elig = eligibility?.trim().toUpperCase();

  if (jur === "central" && (elig === "ELIGIBLE" || elig === "MODELLED")) {
    return 1;
  }
  if (elig === "PLANNED" || jur === "planned") {
    return 3;
  }
  return 2;
}
