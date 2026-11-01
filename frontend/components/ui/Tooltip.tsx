/**
 * components/ui/Tooltip.tsx
 * =========================
 * Accessible institutional tooltip component for Seance.
 *
 * Implements:
 * - Hover and keyboard focus reveal
 * - Accessible aria-describedby linkage
 * - Dual-theme elevated surface tokens
 */

"use client";

import React, { useState, useId } from "react";
import { cn } from "@/lib/utils";

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  position?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function Tooltip({
  content,
  children,
  position = "top",
  className,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const tooltipId = useId();

  const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  const trigger = React.cloneElement(children, {
    onMouseEnter: () => setVisible(true),
    onMouseLeave: () => setVisible(false),
    onFocus: () => setVisible(true),
    onBlur: () => setVisible(false),
    "aria-describedby": visible ? tooltipId : undefined,
  } as React.HTMLAttributes<HTMLElement>);

  return (
    <div className="relative inline-flex items-center">
      {trigger}
      {visible && (
        <div
          id={tooltipId}
          role="tooltip"
          className={cn(
            "absolute z-50 whitespace-nowrap rounded-lg px-2.5 py-1 text-[11px] font-medium leading-tight",
            "bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-default)] shadow-lg pointer-events-none animate-fade-in",
            positionClasses[position],
            className
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}

export default Tooltip;
