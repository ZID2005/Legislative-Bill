"use client";

/**
 * components/brand/SeanceBrand.tsx
 * ================================
 * Reusable Seance Brand Lockup Component
 * Combines the bespoke BrandEmblem with the institutional wordmark and optional sub-label.
 */

import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { BrandEmblem, BrandEmblemProps } from "./BrandEmblem";

export interface SeanceBrandProps {
  size?: "sm" | "md" | "lg";
  showSublabel?: boolean;
  sublabel?: string;
  href?: string | null;
  className?: string;
  emblemVariant?: BrandEmblemProps["variant"];
  onClick?: () => void;
  "aria-label"?: string;
}

const sizeConfig = {
  sm: {
    emblemSize: "sm" as const,
    nameClasses: "text-sm font-bold tracking-tight leading-none",
    sublabelClasses: "text-[9px] font-mono leading-tight tracking-wider",
    gap: "gap-2",
  },
  md: {
    emblemSize: "md" as const,
    nameClasses: "text-base font-bold tracking-tight leading-none",
    sublabelClasses: "text-[10px] font-mono leading-tight tracking-wider",
    gap: "gap-2.5",
  },
  lg: {
    emblemSize: "lg" as const,
    nameClasses: "text-xl sm:text-2xl font-extrabold tracking-tight leading-none",
    sublabelClasses: "text-xs font-mono leading-tight tracking-widest",
    gap: "gap-3",
  },
};

export function SeanceBrand({
  size = "sm",
  showSublabel = true,
  sublabel = "Decision Intelligence",
  href = "/",
  className,
  emblemVariant = "brand",
  onClick,
  "aria-label": customAriaLabel,
}: SeanceBrandProps) {
  const config = sizeConfig[size] || sizeConfig.sm;
  const accessibleLabel = customAriaLabel || `Seance ${sublabel ? `· ${sublabel}` : ""}`;

  const content = (
    <>
      <BrandEmblem
        size={config.emblemSize}
        variant={emblemVariant}
        aria-hidden={true}
        className="group-hover:scale-105"
      />
      <div className="flex flex-col text-left">
        <span
          className={cn(
            config.nameClasses,
            "text-[var(--text-primary)] transition-colors"
          )}
        >
          Seance
        </span>
        {showSublabel && (
          <span
            className={cn(
              config.sublabelClasses,
              "text-[var(--text-muted)] uppercase mt-0.5"
            )}
          >
            {sublabel}
          </span>
        )}
      </div>
    </>
  );

  const containerClasses = cn(
    "flex items-center flex-shrink-0 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] rounded-md",
    config.gap,
    className
  );

  if (href) {
    return (
      <Link
        href={href}
        className={containerClasses}
        aria-label={accessibleLabel}
        onClick={onClick}
      >
        {content}
      </Link>
    );
  }

  return (
    <div
      className={containerClasses}
      aria-label={accessibleLabel}
      onClick={onClick}
      role="banner"
    >
      {content}
    </div>
  );
}

export default SeanceBrand;
