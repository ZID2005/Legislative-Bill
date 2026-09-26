/**
 * components/layout/Header.tsx
 * =============================
 * Top navigation header with global search (Cmd+K), notification bell,
 * and user profile placeholder.
 */

"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useSearch } from "@/hooks/useSearch";
import { SearchInput } from "@/components/ui/SearchInput";
import type { SearchResultItem } from "@/types/api";
import { UserSession, authApi } from "@/lib/api/auth";

const categoryLabels: Record<string, string> = {
  bills_central: "Central Bill",
  bills_state: "State Bill",
  companies_quant: "Quantitative Co.",
  companies_intel: "Intel Entity",
  industries: "Industry",
  sectors: "Sector",
  states: "State",
  monitoring: "Monitoring",
};

const categoryIcons: Record<string, string> = {
  bills_central: "📜",
  bills_state: "📋",
  companies_quant: "📈",
  companies_intel: "🏢",
  industries: "🏭",
  sectors: "⬡",
  states: "🗺",
  monitoring: "📡",
};

function SearchResult({
  item,
  onClose,
}: {
  item: SearchResultItem;
  onClose: () => void;
}) {
  return (
    <Link
      href={item.url}
      onClick={onClose}
      className="flex items-start gap-3 px-4 py-2.5 hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:bg-slate-800"
    >
      <span className="text-sm mt-0.5 flex-shrink-0" aria-hidden="true">
        {categoryIcons[item.category] ?? "•"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-slate-200 font-medium truncate">{item.title}</p>
        {item.subtitle && (
          <p className="text-xs text-slate-500 truncate">{item.subtitle}</p>
        )}
      </div>
      <span className="flex-shrink-0 text-[10px] bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5 text-slate-500">
        {categoryLabels[item.category] ?? item.category}
      </span>
    </Link>
  );
}

export interface HeaderProps {
  title?: string;
  notificationCount?: number;
}

export function Header({ title, notificationCount = 0 }: HeaderProps) {
  const { query, results, loading, search, clearSearch } = useSearch();
  const [searchOpen, setSearchOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const [session, setSession] = useState<UserSession | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("auth_user");
      if (stored) {
        try {
          setSession(JSON.parse(stored));
        } catch {
          // ignore
        }
      }
      authApi.getMe().then(setSession).catch(() => {});
    }
  }, []);

  // Cmd+K / Ctrl+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (e.key === "Escape") {
        setSearchOpen(false);
        clearSearch();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [clearSearch]);

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
        clearSearch();
      }
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [clearSearch]);

  return (
    <header
      className="h-12 flex items-center justify-between px-4 bg-slate-950 border-b border-slate-800 flex-shrink-0"
      role="banner"
    >
      {/* Left — page title */}
      {title && (
        <h1 className="text-sm font-semibold text-slate-200 truncate max-w-xs hidden sm:block">
          {title}
        </h1>
      )}

      {/* Center — global search */}
      <div
        ref={containerRef}
        className={cn(
          "relative mx-auto",
          title ? "max-w-sm w-full" : "max-w-md w-full"
        )}
      >
        <SearchInput
          id="global-search"
          value={query}
          onChange={(v) => {
            search(v);
            setSearchOpen(true);
          }}
          onFocus={() => setSearchOpen(true)}
          placeholder="Search bills, companies, states…"
          shortcutHint="⌘K"
          className="w-full"
        />

        {/* Search results dropdown */}
        {searchOpen && (query.length > 0) && (
          <div
            className="absolute left-0 right-0 top-full mt-1 z-50 rounded-lg border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden"
            role="listbox"
            aria-label="Search results"
          >
            {loading && (
              <div className="px-4 py-3 text-xs text-slate-500 flex items-center gap-2">
                <span className="inline-block w-3 h-3 border border-slate-600 border-t-slate-300 rounded-full animate-spin" aria-hidden="true" />
                Searching…
              </div>
            )}

            {!loading && results && results.total_matches === 0 && (
              <div className="px-4 py-4 text-xs text-slate-500 text-center">
                No results for &ldquo;{query}&rdquo;
              </div>
            )}

            {!loading && results && results.total_matches > 0 && (
              <div className="max-h-96 overflow-y-auto">
                {results.items.slice(0, 10).map((item) => (
                  <SearchResult
                    key={item.id}
                    item={item}
                    onClose={() => {
                      setSearchOpen(false);
                      clearSearch();
                    }}
                  />
                ))}
                {results.total_matches > 10 && (
                  <div className="border-t border-slate-800 px-4 py-2 text-xs text-slate-600 text-center">
                    {results.total_matches - 10} more results — refine your query
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right — notifications + profile */}
      <div className="flex items-center gap-2">
        <Link
          href="/notifications"
          className="relative p-1.5 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount} unread)` : ""}`}
        >
          <svg
            className="h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          {notificationCount > 0 && (
            <span
              className="absolute -top-0.5 -right-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-blue-500 text-[9px] font-bold text-white"
              aria-hidden="true"
            >
              {notificationCount > 9 ? "9+" : notificationCount}
            </span>
          )}
        </Link>

        {/* User profile menu */}
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="User account menu"
            aria-expanded={profileOpen}
          >
            {session?.display_name ? session.display_name.charAt(0).toUpperCase() : "U"}
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl py-2 z-50 text-xs">
              <div className="px-4 py-2 border-b border-slate-800">
                <p className="font-semibold text-white truncate">
                  {session?.display_name || "Analyst Account"}
                </p>
                <p className="text-[11px] text-slate-400 truncate">
                  {session?.email || "Local Session"}
                </p>
                <div className="mt-1 flex items-center gap-1.5">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                    {session?.role || "VIEWER"}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono truncate">
                    {session?.tenant_id || "default_tenant"}
                  </span>
                </div>
              </div>

              <Link
                href="/settings"
                onClick={() => setProfileOpen(false)}
                className="block px-4 py-2 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                ⚙ Organization &amp; Settings
              </Link>
              <Link
                href="/onboarding"
                onClick={() => setProfileOpen(false)}
                className="block px-4 py-2 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                ✦ Onboarding Wizard
              </Link>

              <div className="border-t border-slate-800 my-1" />

              {session ? (
                <button
                  onClick={async () => {
                    setProfileOpen(false);
                    await authApi.logout();
                    window.location.href = "/login";
                  }}
                  className="w-full text-left px-4 py-2 text-red-400 hover:bg-slate-800 transition-colors"
                >
                  Sign Out
                </button>
              ) : (
                <Link
                  href="/login"
                  onClick={() => setProfileOpen(false)}
                  className="block px-4 py-2 text-blue-400 hover:bg-slate-800 transition-colors"
                >
                  Sign In / Register
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
