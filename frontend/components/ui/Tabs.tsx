/**
 * components/ui/Tabs.tsx
 * ======================
 * Accessible tab navigation component.
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface Tab {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

export interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
  size?: "sm" | "md";
}

export function Tabs({
  tabs,
  activeTab,
  onTabChange,
  className,
  size = "md",
}: TabsProps) {
  const sizeClasses = {
    sm: "text-xs px-3 py-1.5",
    md: "text-sm px-4 py-2",
  };

  return (
    <div
      role="tablist"
      aria-label="Navigation tabs"
      className={cn(
        "flex items-center gap-1 border-b border-slate-800",
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "inline-flex items-center gap-1.5 font-medium border-b-2 -mb-px transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded-t",
              sizeClasses[size],
              isActive
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600"
            )}
          >
            {tab.icon && (
              <span className="text-base" aria-hidden="true">
                {tab.icon}
              </span>
            )}
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={cn(
                  "ml-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                  isActive
                    ? "bg-blue-900/60 text-blue-300"
                    : "bg-slate-800 text-slate-400"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default Tabs;
