/**
 * components/ui/SearchInput.tsx
 * =============================
 * Institutional search input with vector iconography, clear button,
 * and keyboard shortcut indicator for Seance.
 */

"use client";

import React, { useRef } from "react";
import { cn } from "@/lib/utils";
import { SearchIcon, CloseIcon } from "./Icons";

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  onFocus?: () => void;
  placeholder?: string;
  className?: string;
  shortcutHint?: string;
  autoFocus?: boolean;
  id?: string;
}

export function SearchInput({
  value,
  onChange,
  onClear,
  onFocus,
  placeholder = "Search…",
  className,
  shortcutHint,
  autoFocus,
  id = "search-input",
}: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className={cn("relative flex items-center w-full", className)}>
      {/* Search icon */}
      <span className="absolute left-3 text-[var(--text-muted)] pointer-events-none inline-flex items-center" aria-hidden="true">
        <SearchIcon size="sm" />
      </span>

      <input
        ref={inputRef}
        id={id}
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={cn(
          "w-full bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-xl",
          "pl-9 pr-10 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)]",
          "focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring)] focus:border-transparent",
          "transition-all duration-150"
        )}
        aria-label={placeholder}
      />

      {/* Shortcut hint or clear button */}
      <div className="absolute right-3 flex items-center gap-1">
        {value ? (
          <button
            type="button"
            onClick={() => {
              onChange("");
              onClear?.();
              inputRef.current?.focus();
            }}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] p-0.5 rounded transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
            aria-label="Clear search"
          >
            <CloseIcon size="xs" />
          </button>
        ) : shortcutHint ? (
          <kbd className="hidden sm:inline-flex items-center gap-0.5 rounded border border-[var(--border-default)] bg-[var(--bg-card)] px-1.5 py-0.5 text-[10px] font-mono text-[var(--text-muted)] select-none">
            {shortcutHint}
          </kbd>
        ) : null}
      </div>
    </div>
  );
}

export default SearchInput;
