"use client";

/**
 * components/brand/BrandEmblem.tsx
 * =================================
 * Seance Bespoke Precision Vector Brand Emblem
 *
 * Geometric Rationale:
 * - Upper Pediment: Statutory authority, legislative enactments, and institutional governance.
 * - Dynamic Mid-Tier: Econometric event-study transmission, market impact, and anticipation.
 * - Foundation Base: Ground truth, empirical evidence, and statutory auditability.
 * - Core Nexus: Precision decision intelligence at the intersection of law and economics.
 *
 * Fully scalable from 16px to 64px+ with zero rasterization artifacts.
 * Adapts seamlessly across Light and Dark themes.
 */

import React from "react";
import { cn } from "@/lib/utils";

export interface BrandEmblemProps {
  size?: "xs" | "sm" | "md" | "lg" | "xl" | number;
  className?: string;
  variant?: "brand" | "monochrome";
  "aria-hidden"?: boolean;
  "aria-label"?: string;
}

const sizeMap = {
  xs: 16,
  sm: 20,
  md: 24,
  lg: 32,
  xl: 48,
};

export function BrandEmblem({
  size = "md",
  className,
  variant = "brand",
  "aria-hidden": ariaHidden,
  "aria-label": ariaLabel,
}: BrandEmblemProps) {
  const pixelSize = typeof size === "number" ? size : sizeMap[size] || 24;
  const isAccessible = !ariaHidden && Boolean(ariaLabel);

  return (
    <svg
      width={pixelSize}
      height={pixelSize}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("flex-shrink-0 transition-transform duration-200", className)}
      role={isAccessible ? "img" : undefined}
      aria-label={isAccessible ? ariaLabel || "Seance Emblem" : undefined}
      aria-hidden={ariaHidden ?? (ariaLabel ? undefined : true)}
    >
      {/* Upper Pediment: Legislative Enactment & Statutory Apex */}
      <path
        d="M16 2.5L27.5 9.25L16 16L4.5 9.25L16 2.5Z"
        fill={variant === "brand" ? "url(#seance-apex-grad)" : "currentColor"}
        fillOpacity={variant === "brand" ? 1 : 0.95}
      />

      {/* Mid Horizon: Econometric Impact & Anticipation Wave */}
      <path
        d="M5 14L16 20.5L27 14L27 18.5L16 25L5 18.5L5 14Z"
        fill={variant === "brand" ? "url(#seance-impact-grad)" : "currentColor"}
        fillOpacity={variant === "brand" ? 0.85 : 0.65}
      />

      {/* Foundation Base: Empirical Evidence & Institutional Grounding */}
      <path
        d="M8.5 22L16 26.5L23.5 22L23.5 25L16 29.5L8.5 25L8.5 22Z"
        fill={variant === "brand" ? "url(#seance-base-grad)" : "currentColor"}
        fillOpacity={variant === "brand" ? 0.75 : 0.45}
      />

      {/* Analytical Nexus: Decision Intelligence Core Diamond */}
      <path
        d="M16 9.5L20 12L16 14.5L12 12L16 9.5Z"
        fill={variant === "brand" ? "#67e8f9" : "currentColor"}
        fillOpacity={variant === "brand" ? 0.9 : 0.85}
      />

      {/* Subtle Hairline Equilibrium Spine */}
      <line
        x1="16"
        y1="3"
        x2="16"
        y2="29"
        stroke="currentColor"
        strokeWidth="0.75"
        strokeOpacity="0.25"
      />

      {variant === "brand" && (
        <defs>
          <linearGradient id="seance-apex-grad" x1="4.5" y1="2.5" x2="27.5" y2="16" gradientUnits="userSpaceOnUse">
            <stop stopColor="#3b82f6" />
            <stop offset="1" stopColor="#6366f1" />
          </linearGradient>
          <linearGradient id="seance-impact-grad" x1="5" y1="14" x2="27" y2="25" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0284c7" />
            <stop offset="1" stopColor="#818cf8" />
          </linearGradient>
          <linearGradient id="seance-base-grad" x1="8.5" y1="22" x2="23.5" y2="29.5" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0ea5e9" />
            <stop offset="1" stopColor="#38bdf8" />
          </linearGradient>
        </defs>
      )}
    </svg>
  );
}

export default BrandEmblem;
