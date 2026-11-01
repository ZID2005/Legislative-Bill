/**
 * components/layout/Header.tsx
 * =============================
 * Top navigation header with global search (Cmd+K), notification bell,
 * and user profile popover for Seance.
 * Dual-theme synchronized using semantic design tokens and vector iconography.
 */

"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useSearch } from "@/hooks/useSearch";
import { SearchInput } from "@/components/ui/SearchInput";
import type { SearchResultItem } from "@/types/api";
import { UserSession, authApi } from "@/lib/api/auth";
import {
  BillsIcon,
  CompaniesIcon,
  IndustriesIcon,
  SectorsIcon,
  StatesIcon,
  MonitoringIcon,
  NotificationsIcon,
  SettingsIcon,
  AiAnalystIcon,
  SpinnerIcon,
} from "@/components/ui/Icons";

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

function CategoryIcon({ category }: { category: string }) {
  switch (category) {
    case "bills_central":
    case "bills_state":
      return <BillsIcon size="sm" />;
    case "companies_quant":
    case "companies_intel":
      return <CompaniesIcon size="sm" />;
    case "industries":
      return <IndustriesIcon size="sm" />;
    case "sectors":
      return <SectorsIcon size="sm" />;
    case "states":
      return <StatesIcon size="sm" />;
    case "monitoring":
      return <MonitoringIcon size="sm" />;
    default:
      return <span className="w-1.5 h-1.5 rounded-full bg-[var(--action-primary)]" />;
  }
}

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
      className="flex items-start gap-3 px-4 py-2.5 hover:bg-[var(--bg-card-hover)] transition-colors focus-visible:outline-none focus-visible:bg-[var(--bg-card-hover)]"
    >
      <span className="text-[var(--text-muted)] mt-0.5 flex-shrink-0 inline-flex items-center" aria-hidden="true">
        <CategoryIcon category={item.category} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-[var(--text-primary)] font-medium truncate">{item.title}</p>
        {item.subtitle && (
          <p className="text-[11px] text-[var(--text-muted)] truncate mt-0.5">{item.subtitle}</p>
        )}
      </div>
      <span className="flex-shrink-0 text-[10px] bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded px-1.5 py-0.5 text-[var(--text-muted)] font-mono">
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
      className="h-14 flex items-center justify-between px-5 bg-[var(--bg-nav)] border-b border-[var(--border-default)] backdrop-blur-md flex-shrink-0 z-30"
      role="banner"
    >
      {/* Left — page title */}
      {title && (
        <h1 className="text-sm font-semibold tracking-tight text-[var(--text-primary)] truncate max-w-xs hidden sm:block">
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
          placeholder="Search bills, companies, states… (⌘K)"
          shortcutHint="⌘K"
          className="w-full"
        />

        {/* Search results dropdown */}
        {searchOpen && query.length > 0 && (
          <div
            className="absolute left-0 right-0 top-full mt-1.5 z-50 rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] shadow-2xl overflow-hidden animate-fade-in"
            role="listbox"
            aria-label="Search results"
          >
            {loading && (
              <div className="px-4 py-3 text-xs text-[var(--text-muted)] flex items-center gap-2">
                <SpinnerIcon size="xs" />
                <span>Searching intelligence universe…</span>
              </div>
            )}

            {!loading && results && results.total_matches === 0 && (
              <div className="px-4 py-5 text-xs text-[var(--text-muted)] text-center">
                No records found for &ldquo;{query}&rdquo;
              </div>
            )}

            {!loading && results && results.total_matches > 0 && (
              <div className="max-h-96 overflow-y-auto divide-y divide-[var(--border-subtle)]">
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
                  <div className="px-4 py-2 text-xs text-[var(--text-muted)] text-center bg-[var(--bg-base)]">
                    {results.total_matches - 10} additional records match — refine query
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
          className="relative p-2 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount} unread)` : ""}`}
        >
          <NotificationsIcon size="sm" />
          {notificationCount > 0 && (
            <span
              className="absolute top-1 right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-[var(--action-primary)] text-[9px] font-bold text-[var(--text-primary)] shadow-xs"
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
            className="h-8 w-8 rounded-full bg-[var(--action-primary)]/12 border border-[var(--action-primary)]/25 flex items-center justify-center text-xs font-bold text-[var(--action-primary)] hover:bg-[var(--action-primary)]/20 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
            aria-label="User account menu"
            aria-expanded={profileOpen}
          >
            {session?.display_name ? session.display_name.charAt(0).toUpperCase() : "S"}
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-60 rounded-2xl bg-[var(--bg-elevated)] border border-[var(--border-default)] shadow-2xl py-2 z-50 text-xs animate-fade-in">
              <div className="px-4 py-3 border-b border-[var(--border-default)]">
                <p className="font-semibold text-[var(--text-primary)] truncate">
                  {session?.display_name || "Seance Analyst"}
                </p>
                <p className="text-[11px] text-[var(--text-muted)] truncate mt-0.5">
                  {session?.email || "institutional@seance.internal"}
                </p>
                <div className="mt-2 flex items-center gap-1.5">
                  <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[var(--action-primary)]/15 text-[var(--action-primary)] border border-[var(--action-primary)]/30">
                    {session?.role || "ANALYST"}
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)] font-mono truncate">
                    {session?.tenant_id || "default_tenant"}
                  </span>
                </div>
              </div>

              <div className="py-1">
                <Link
                  href="/settings"
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                >
                  <SettingsIcon size="xs" />
                  <span>Organization &amp; Settings</span>
                </Link>
                <Link
                  href="/onboarding"
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                >
                  <AiAnalystIcon size="xs" />
                  <span>Onboarding Wizard</span>
                </Link>
              </div>

              <div className="border-t border-[var(--border-default)] my-1" />

              {session ? (
                <button
                  onClick={async () => {
                    setProfileOpen(false);
                    await authApi.logout();
                    window.location.href = "/login";
                  }}
                  className="w-full text-left px-4 py-2 text-[var(--color-danger)] hover:bg-[var(--color-danger-bg)] transition-colors"
                >
                  Sign Out
                </button>
              ) : (
                <Link
                  href="/login"
                  onClick={() => setProfileOpen(false)}
                  className="block px-4 py-2 text-[var(--action-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
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
