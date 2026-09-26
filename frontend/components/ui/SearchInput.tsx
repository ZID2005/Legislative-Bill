/**
 * components/ui/SearchInput.tsx
 * =============================
 * Search input component with clear button and keyboard shortcut hint.
 */

"use client";

import React, { useRef } from "react";
import { cn } from "@/lib/utils";

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
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
  onFocus,
  placeholder = "Search…",
  className,
  shortcutHint,
  autoFocus,
  id = "search-input",
}: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className={cn("relative flex items-center", className)}>
      {/* Search icon */}
      <svg
        className="absolute left-3 h-4 w-4 text-slate-500 pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>

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
          "w-full bg-slate-800/80 border border-slate-700 rounded-lg",
          "pl-9 pr-10 py-2 text-sm text-slate-100 placeholder:text-slate-500",
          "focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500",
          "transition-colors duration-150"
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
              inputRef.current?.focus();
            }}
            className="text-slate-500 hover:text-slate-300 transition-colors"
            aria-label="Clear search"
          >
            <svg
              className="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        ) : shortcutHint ? (
          <kbd className="hidden sm:inline-flex items-center gap-0.5 rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-500">
            {shortcutHint}
          </kbd>
        ) : null}
      </div>
    </div>
  );
}

export default SearchInput;
