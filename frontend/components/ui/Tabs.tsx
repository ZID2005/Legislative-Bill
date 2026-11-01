/**
 * components/ui/Tabs.tsx
 * ======================
 * Accessible institutional tab navigation component for Seance.
 * Dual-theme token synchronized with smooth transitions and ARIA semantics.
 *
 * Task 1.5B.1:
 * - Prevents tab clipping at <1200px viewports with shrink-0 and responsive scroll container.
 * - Dynamic scroll affordance (left/right navigation controls and indicators) when tabs overflow.
 * - Full WCAG 2.1 AA keyboard navigation (ArrowLeft, ArrowRight, Home, End).
 * - Automatic smooth scroll-into-view on tab selection.
 */

"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";

export interface Tab {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
  size?: "sm" | "md";
  variant?: "underline" | "pills";
}

export function Tabs({
  tabs,
  activeTab,
  onTabChange,
  className,
  size = "md",
  variant = "underline",
}: TabsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const sizeClasses = {
    sm: "text-xs px-3 py-1.5",
    md: "text-sm px-4 py-2",
  };

  const checkScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const { scrollLeft, scrollWidth, clientWidth } = el;
    setCanScrollLeft(scrollLeft > 4);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 4);
  }, []);

  useEffect(() => {
    checkScroll();
    const el = scrollRef.current;
    if (!el) return;

    el.addEventListener("scroll", checkScroll, { passive: true });
    window.addEventListener("resize", checkScroll);

    return () => {
      el.removeEventListener("scroll", checkScroll);
      window.removeEventListener("resize", checkScroll);
    };
  }, [checkScroll, tabs]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const activeBtn = el.querySelector<HTMLButtonElement>(`#tab-${activeTab}`);
    if (activeBtn && typeof activeBtn.scrollIntoView === "function") {
      activeBtn.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
    }
    checkScroll();
  }, [activeTab, checkScroll]);

  const scrollBy = (offset: number) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: offset, behavior: "smooth" });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let targetIndex = -1;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      targetIndex = (index + 1) % tabs.length;
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      targetIndex = (index - 1 + tabs.length) % tabs.length;
    } else if (e.key === "Home") {
      e.preventDefault();
      targetIndex = 0;
    } else if (e.key === "End") {
      e.preventDefault();
      targetIndex = tabs.length - 1;
    }

    if (targetIndex !== -1 && !tabs[targetIndex].disabled) {
      onTabChange(tabs[targetIndex].id);
      const el = scrollRef.current;
      const targetBtn = el?.querySelector<HTMLButtonElement>(`#tab-${tabs[targetIndex].id}`);
      targetBtn?.focus();
    }
  };

  if (variant === "pills") {
    return (
      <div className={cn("relative group/tabs w-full", className)}>
        {canScrollLeft && (
          <button
            type="button"
            onClick={() => scrollBy(-180)}
            aria-label="Scroll tabs left"
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-[var(--bg-card)]/90 text-[var(--text-secondary)] shadow-sm border border-[var(--border-default)] backdrop-blur-xs hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-all"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        <div
          ref={scrollRef}
          role="tablist"
          aria-label="Navigation tabs"
          className={cn(
            "flex flex-nowrap items-center gap-1.5 p-1 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-default)] overflow-x-auto scroll-smooth",
            "[scrollbar-width:thin] [scrollbar-color:var(--scrollbar-thumb)_transparent]"
          )}
        >
          {tabs.map((tab, idx) => {
            const isActive = tab.id === activeTab;
            return (
              <button
                key={tab.id}
                role="tab"
                id={`tab-${tab.id}`}
                disabled={tab.disabled}
                aria-disabled={tab.disabled}
                aria-selected={isActive}
                aria-controls={`tabpanel-${tab.id}`}
                onClick={() => !tab.disabled && onTabChange(tab.id)}
                onKeyDown={(e) => handleKeyDown(e, idx)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-lg font-medium transition-all duration-150 select-none shrink-0 whitespace-nowrap",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]",
                  sizeClasses[size],
                  tab.disabled && "opacity-40 cursor-not-allowed",
                  isActive
                    ? "bg-[var(--action-primary)] text-white shadow-xs font-semibold"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                )}
              >
                {tab.icon && (
                  <span className="inline-flex items-center" aria-hidden="true">
                    {tab.icon}
                  </span>
                )}
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span
                    className={cn(
                      "ml-0.5 rounded-full px-1.5 py-0.2 text-[10px] font-mono font-semibold",
                      isActive
                        ? "bg-white/20 text-white"
                        : "bg-[var(--bg-card)] text-[var(--text-muted)] border border-[var(--border-subtle)]"
                    )}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {canScrollRight && (
          <button
            type="button"
            onClick={() => scrollBy(180)}
            aria-label="Scroll tabs right"
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-[var(--bg-card)]/90 text-[var(--text-secondary)] shadow-sm border border-[var(--border-default)] backdrop-blur-xs hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-all"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={cn("relative group/tabs w-full", className)}>
      {canScrollLeft && (
        <button
          type="button"
          onClick={() => scrollBy(-200)}
          aria-label="Scroll tabs left"
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-[var(--bg-surface)]/95 text-[var(--text-secondary)] shadow-sm border border-[var(--border-default)] backdrop-blur-xs hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-all"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      )}

      <div
        ref={scrollRef}
        role="tablist"
        aria-label="Navigation tabs"
        className={cn(
          "flex flex-nowrap items-center gap-1 border-b border-[var(--border-default)] overflow-x-auto scroll-smooth",
          "[scrollbar-width:thin] [scrollbar-color:var(--scrollbar-thumb)_transparent] pb-0.5",
          canScrollLeft && "pl-8",
          canScrollRight && "pr-8"
        )}
      >
        {tabs.map((tab, idx) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              role="tab"
              id={`tab-${tab.id}`}
              disabled={tab.disabled}
              aria-disabled={tab.disabled}
              aria-selected={isActive}
              aria-controls={`tabpanel-${tab.id}`}
              onClick={() => !tab.disabled && onTabChange(tab.id)}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              className={cn(
                "inline-flex items-center gap-2 font-medium border-b-2 -mb-px transition-all duration-150 whitespace-nowrap select-none shrink-0",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] rounded-t",
                sizeClasses[size],
                tab.disabled && "opacity-40 cursor-not-allowed",
                isActive
                  ? "border-[var(--action-primary)] text-[var(--action-primary)] font-semibold"
                  : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]"
              )}
            >
              {tab.icon && (
                <span className="inline-flex items-center" aria-hidden="true">
                  {tab.icon}
                </span>
              )}
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={cn(
                    "ml-1 rounded-full px-1.5 py-0.5 text-[10px] font-mono font-semibold",
                    isActive
                      ? "bg-[var(--action-primary)]/15 text-[var(--action-primary)]"
                      : "bg-[var(--bg-secondary)] text-[var(--text-muted)] border border-[var(--border-subtle)]"
                  )}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {canScrollRight && (
        <button
          type="button"
          onClick={() => scrollBy(200)}
          aria-label="Scroll tabs right"
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-[var(--bg-surface)]/95 text-[var(--text-secondary)] shadow-sm border border-[var(--border-default)] backdrop-blur-xs hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-all"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default Tabs;
