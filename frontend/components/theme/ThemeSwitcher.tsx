"use client";

/**
 * components/theme/ThemeSwitcher.tsx
 * ==================================
 * Reusable Theme Switcher Control for Seance
 *
 * Supports 3 explicit modes:
 * - Light (Institutional daytime clarity)
 * - Dark (High-contrast institutional terminal)
 * - System (Operating system preference synchronization)
 *
 * Fully accessible (WCAG 2.2 AA):
 * - Semantic radiogroup pattern with aria-checked
 * - Full keyboard navigation (Arrows, Tab, Space, Enter)
 * - High-contrast active indicators
 */

import React, { useRef } from "react";
import { cn } from "@/lib/utils";
import { useTheme, ThemePreference } from "@/hooks/useTheme";

export interface ThemeSwitcherProps {
  className?: string;
  size?: "sm" | "md";
  showLabels?: boolean;
}

interface ThemeOption {
  id: ThemePreference;
  label: string;
  ariaLabel: string;
  icon: React.ReactNode;
}

export function ThemeSwitcher({
  className,
  size = "sm",
  showLabels = false,
}: ThemeSwitcherProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const groupRef = useRef<HTMLDivElement>(null);

  const options: ThemeOption[] = [
    {
      id: "light",
      label: "Light",
      ariaLabel: "Light theme",
      icon: (
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      ),
    },
    {
      id: "dark",
      label: "Dark",
      ariaLabel: "Dark theme",
      icon: (
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      ),
    },
    {
      id: "system",
      label: "System",
      ariaLabel: `System preference (${resolvedTheme})`,
      icon: (
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>
      ),
    },
  ];

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let nextIndex = index;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault();
      nextIndex = (index + 1) % options.length;
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      nextIndex = (index - 1 + options.length) % options.length;
    } else {
      return;
    }

    const nextOption = options[nextIndex];
    if (nextOption) {
      setTheme(nextOption.id);
      const buttons = groupRef.current?.querySelectorAll<HTMLButtonElement>("button");
      buttons?.[nextIndex]?.focus();
    }
  };

  const isSmall = size === "sm";

  return (
    <div
      ref={groupRef}
      role="radiogroup"
      aria-label="Theme preference"
      className={cn(
        "inline-flex items-center p-0.5 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] text-[var(--text-muted)]",
        className
      )}
    >
      {options.map((option, idx) => {
        const isSelected = theme === option.id;

        return (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={isSelected}
            aria-label={option.ariaLabel}
            tabIndex={isSelected ? 0 : -1}
            onClick={() => setTheme(option.id)}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            className={cn(
              "relative inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-all duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]",
              isSmall ? "px-2 py-1 text-xs" : "px-2.5 py-1.5 text-sm",
              isSelected
                ? "bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-xs border border-[var(--border-strong)]"
                : "hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] border border-transparent"
            )}
          >
            {option.icon}
            {showLabels && <span>{option.label}</span>}
          </button>
        );
      })}
    </div>
  );
}

export default ThemeSwitcher;
