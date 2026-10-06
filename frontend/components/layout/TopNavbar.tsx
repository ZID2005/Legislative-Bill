/**
 * components/layout/TopNavbar.tsx
 * =================================
 * Task 8.25 — Modern SaaS top navigation bar.
 *
 * Structure:
 *   [Logo] [Discover ▾] [Analyze ▾] [Monitor ▾] [Portfolio] [Reports] [AI]
 *   Right: [Search ⌘K] [Notifications] [User ▾]
 *
 * - Dropdown mega-menus for main sections
 * - Mobile hamburger → drawer
 * - Keyboard accessible (Escape to close dropdowns)
 * - Active route highlighting
 * - Reduced-motion safe
 */

"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSearch } from "@/hooks/useSearch";
import { UserSession, authApi } from "@/lib/api/auth";
import type { SearchResultItem } from "@/types/api";

// ---------------------------------------------------------------------------
// Nav structure
// ---------------------------------------------------------------------------

interface NavChild {
  label: string;
  href: string;
  description?: string;
  badge?: "LIVE" | "NEW" | "AI";
  icon?: string;
}

interface NavGroup {
  id: string;
  label: string;
  icon?: string;
  href?: string; // if set, direct link (no dropdown)
  children?: NavChild[];
  badge?: "LIVE" | "NEW" | "AI";
}

const NAV_GROUPS: NavGroup[] = [
  {
    id: "discover",
    label: "Discover",
    children: [
      { label: "Overview", href: "/overview", icon: "◉", description: "Platform KPIs & coverage metrics" },
      { label: "Legislative Explorer", href: "/explorer", icon: "🔍", description: "Unified search across all 66 bills & 70 companies" },
      { label: "Bills", href: "/bills", icon: "📜", description: "Central Parliament & State Assembly legislation" },
      { label: "Companies", href: "/companies", icon: "🏢", description: "Corporate intelligence universe — 70 entities" },
      { label: "Industries", href: "/industries", icon: "🏭", description: "Industry classification & sector taxonomy" },
      { label: "States", href: "/states", icon: "🗺", description: "State legislative coverage — AP, KA, KL, TS" },
      { label: "Live Discovery", href: "/live-discovery", icon: "📡", description: "Newest legislative records & recent introductions", badge: "LIVE" },
      { label: "Latest Bills", href: "/latest-bills", icon: "⚡", description: "Most recently introduced & discovered bills", badge: "LIVE" },
      { label: "Upcoming Legislation", href: "/upcoming-legislation", icon: "📅", description: "Scheduled sessions & known procedural milestones" },
    ],
  },
  {
    id: "analyze",
    label: "Analyze",
    children: [
      { label: "Market Predictions", href: "/predictions", icon: "📈", description: "Event study windows [-1,+1] to [-10,+10]" },
      { label: "Risk Matrix", href: "/risk", icon: "⚠", description: "Legislative risk classification & scoring" },
      { label: "Anticipation", href: "/anticipation", icon: "⏱", description: "Pre-event market diffusion diagnostics" },
      { label: "Bill Compare", href: "/bills/compare", icon: "⚖", description: "Side-by-side bill comparison analysis" },
    ],
  },
  {
    id: "monitor",
    label: "Monitor",
    children: [
      { label: "Workspace", href: "/workspace", icon: "🏛", description: "Personalized legislative command center" },
      { label: "Legislative Monitoring", href: "/monitoring", icon: "📡", description: "Source tracking & freshness indicators" },
      { label: "Watchlists", href: "/watchlists", icon: "⭐", description: "Custom entity watchlists with alerts" },
      { label: "Alerts", href: "/alerts", icon: "🔔", description: "Legislative change alert rules" },
      { label: "Notifications", href: "/notifications", icon: "📬", description: "In-app notification center" },
      { label: "Coverage", href: "/coverage", icon: "📊", description: "Platform coverage metrics & data freshness" },
    ],
  },
  {
    id: "portfolio",
    label: "Portfolio",
    href: "/portfolio",
    badge: "NEW",
  },
  {
    id: "reports",
    label: "Reports",
    href: "/reports",
    badge: "NEW",
  },
  {
    id: "ai",
    label: "AI",
    href: "/ai-analyst",
    icon: "✦",
    badge: "AI",
  },
];

// ---------------------------------------------------------------------------
// Badge renderer
// ---------------------------------------------------------------------------

function NavBadge({ badge }: { badge: "LIVE" | "NEW" | "AI" }) {
  if (badge === "LIVE") {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-emerald-500/15 border border-emerald-500/25 text-emerald-400">
        <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
        LIVE
      </span>
    );
  }
  if (badge === "NEW") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-blue-500/15 border border-blue-500/25 text-blue-400">
        NEW
      </span>
    );
  }
  if (badge === "AI") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-violet-500/15 border border-violet-500/25 text-violet-400">
        AI
      </span>
    );
  }
  return null;
}

// ---------------------------------------------------------------------------
// Dropdown menu
// ---------------------------------------------------------------------------

function DropdownMenu({
  group,
  onClose,
}: {
  group: NavGroup;
  onClose: () => void;
}) {
  if (!group.children) return null;
  return (
    <div
      className="absolute top-full left-0 mt-1 w-80 rounded-xl border border-white/8 bg-slate-900/95 backdrop-blur-xl shadow-2xl shadow-black/40 z-50 dropdown-enter overflow-hidden"
      role="menu"
    >
      <div className="p-2">
        {group.children.map((child) => (
          <Link
            key={child.href}
            href={child.href}
            onClick={onClose}
            role="menuitem"
            className="flex items-start gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 transition-colors group"
          >
            {child.icon && (
              <span className="text-base mt-0.5 flex-shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                {child.icon}
              </span>
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
                  {child.label}
                </span>
                {child.badge && <NavBadge badge={child.badge} />}
              </div>
              {child.description && (
                <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                  {child.description}
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Search result item
// ---------------------------------------------------------------------------

const categoryLabels: Record<string, string> = {
  bills_central: "Central Bill",
  bills_state: "State Bill",
  companies_quant: "Quant Co.",
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

function SearchResultItem({
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
      className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/5 transition-colors group"
    >
      <span className="text-sm flex-shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
        {categoryIcons[item.category] ?? "•"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-slate-200 font-medium truncate group-hover:text-white transition-colors">
          {item.title}
        </p>
        {item.subtitle && (
          <p className="text-xs text-slate-500 truncate">{item.subtitle}</p>
        )}
      </div>
      <span className="flex-shrink-0 text-[10px] bg-white/5 border border-white/8 rounded px-1.5 py-0.5 text-slate-500">
        {categoryLabels[item.category] ?? item.category}
      </span>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Mobile drawer
// ---------------------------------------------------------------------------

function MobileDrawer({
  open,
  onClose,
  session,
}: {
  open: boolean;
  onClose: () => void;
  session: UserSession | null;
}) {
  const pathname = usePathname();

  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Drawer */}
      <div
        className="fixed inset-y-0 left-0 z-50 w-80 bg-slate-900 border-r border-white/8 flex flex-col animate-slide-in-left"
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
      >
        {/* Drawer header */}
        <div className="flex items-center justify-between p-4 border-b border-white/8 flex-shrink-0">
          <Link href="/" onClick={onClose} className="flex items-center gap-2.5">
            <span className="text-blue-400 text-xl">⚖</span>
            <div>
              <span className="text-sm font-bold text-white">LegisIntel</span>
              <p className="text-[9px] text-slate-600">India · v1.0</p>
            </div>
          </Link>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Close navigation"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable nav content */}
        <nav className="flex-1 overflow-y-auto py-3 px-3" aria-label="Mobile navigation">
          {NAV_GROUPS.map((group) => (
            <div key={group.id} className="mb-3">
              {/* Group label */}
              <div className="px-2 py-1 mb-1">
                <span className="text-[10px] font-bold tracking-widest uppercase text-slate-600">
                  {group.id === "portfolio" || group.id === "reports" || group.id === "ai"
                    ? ""
                    : group.label}
                </span>
              </div>

              {/* Direct link groups */}
              {group.href && (
                <Link
                  href={group.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                    pathname === group.href || pathname?.startsWith(group.href + "/")
                      ? "bg-blue-500/15 text-blue-300 border border-blue-500/20"
                      : "text-slate-300 hover:bg-white/5 hover:text-white"
                  )}
                >
                  {group.icon && <span className="text-base">{group.icon}</span>}
                  <span>{group.label}</span>
                  {group.badge && <NavBadge badge={group.badge} />}
                </Link>
              )}

              {/* Children nav items */}
              {group.children && (
                <ul className="space-y-0.5">
                  {group.children.map((child) => {
                    const isActive = pathname === child.href ||
                      (child.href !== "/" && pathname?.startsWith(child.href));
                    return (
                      <li key={child.href}>
                        <Link
                          href={child.href}
                          onClick={onClose}
                          className={cn(
                            "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
                            isActive
                              ? "bg-blue-500/15 text-blue-300"
                              : "text-slate-400 hover:text-white hover:bg-white/5"
                          )}
                        >
                          {child.icon && (
                            <span className="text-sm w-5 text-center flex-shrink-0">
                              {child.icon}
                            </span>
                          )}
                          <span className="truncate">{child.label}</span>
                          {child.badge && <NavBadge badge={child.badge} />}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          ))}
        </nav>

        {/* Drawer footer */}
        <div className="border-t border-white/8 p-3 flex-shrink-0">
          <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg">
            <div className="h-7 w-7 rounded-full bg-slate-700 border border-white/10 flex items-center justify-center text-xs font-bold text-slate-200 flex-shrink-0">
              {session?.display_name?.charAt(0)?.toUpperCase() ?? "U"}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-200 truncate">
                {session?.display_name || "Analyst"}
              </p>
              <p className="text-[10px] text-slate-600 truncate">
                {session?.role || "VIEWER"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Main TopNavbar
// ---------------------------------------------------------------------------

export function TopNavbar() {
  const pathname = usePathname();
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [session, setSession] = useState<UserSession | null>(null);

  const { query, results, loading, search, clearSearch } = useSearch();
  const searchRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);

  // Load session
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("auth_user");
      if (stored) {
        try { setSession(JSON.parse(stored)); } catch { /* ignore */ }
      }
      authApi.getMe().then(setSession).catch(() => {});
    }
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (e.key === "Escape") {
        setSearchOpen(false);
        setActiveDropdown(null);
        setProfileOpen(false);
        clearSearch();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [clearSearch]);

  // Click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
        clearSearch();
      }
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setActiveDropdown(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [clearSearch]);

  const isGroupActive = useCallback((group: NavGroup): boolean => {
    if (group.href) {
      return pathname === group.href || (!!pathname && pathname.startsWith(group.href + "/"));
    }
    if (group.children) {
      return group.children.some(
        (c) => pathname === c.href || (pathname?.startsWith(c.href) && c.href !== "/")
      );
    }
    return false;
  }, [pathname]);

  const closeDropdown = () => setActiveDropdown(null);

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-30 h-14 navbar-blur bg-slate-950/90 border-b border-white/6 flex items-center"
        role="banner"
      >
        <div className="flex items-center w-full px-4 gap-1">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 mr-3 flex-shrink-0 group"
            aria-label="LegisIntel home"
          >
            <span className="text-blue-400 text-xl group-hover:text-blue-300 transition-colors">⚖</span>
            <div className="hidden sm:block">
              <span className="text-sm font-bold text-white tracking-tight">LegisIntel</span>
              <p className="text-[9px] text-slate-600 leading-none">India · v1.0</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav
            ref={navRef}
            className="hidden lg:flex items-center gap-0.5 flex-1"
            aria-label="Main navigation"
          >
            {NAV_GROUPS.map((group) => {
              const isActive = isGroupActive(group);
              const isOpen = activeDropdown === group.id;

              if (group.href && !group.children) {
                // Direct link
                return (
                  <Link
                    key={group.id}
                    href={group.href}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      isActive
                        ? "text-white bg-white/8"
                        : "text-slate-400 hover:text-white hover:bg-white/5"
                    )}
                  >
                    {group.icon && <span className="text-sm">{group.icon}</span>}
                    {group.label}
                    {group.badge && <NavBadge badge={group.badge} />}
                  </Link>
                );
              }

              // Dropdown group
              return (
                <div key={group.id} className="relative">
                  <button
                    onClick={() => setActiveDropdown(isOpen ? null : group.id)}
                    onMouseEnter={() => setActiveDropdown(group.id)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                      isActive || isOpen
                        ? "text-white bg-white/8"
                        : "text-slate-400 hover:text-white hover:bg-white/5"
                    )}
                    aria-expanded={isOpen}
                    aria-haspopup="true"
                  >
                    {group.label}
                    <svg
                      className={cn("h-3 w-3 transition-transform duration-150", isOpen && "rotate-180")}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2.5}
                      aria-hidden="true"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {isOpen && (
                    <div onMouseLeave={closeDropdown}>
                      <DropdownMenu group={group} onClose={closeDropdown} />
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-1.5 ml-auto">
            {/* Search */}
            <div ref={searchRef} className="relative">
              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                aria-label="Open global search (⌘K)"
                id="global-search-btn"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <circle cx={11} cy={11} r={8} />
                  <path strokeLinecap="round" d="M21 21l-4.35-4.35" />
                </svg>
                <span className="hidden sm:inline text-xs">Search</span>
                <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-mono bg-white/5 border border-white/8 rounded text-slate-600">
                  ⌘K
                </kbd>
              </button>

              {/* Search dropdown */}
              {searchOpen && (
                <div className="absolute right-0 top-full mt-2 w-[min(520px,90vw)] rounded-xl border border-white/8 bg-slate-900/98 backdrop-blur-xl shadow-2xl z-50 overflow-hidden dropdown-enter">
                  <div className="p-3 border-b border-white/8">
                    <div className="flex items-center gap-2.5">
                      <svg className="h-4 w-4 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <circle cx={11} cy={11} r={8} />
                        <path strokeLinecap="round" d="M21 21l-4.35-4.35" />
                      </svg>
                      <input
                        type="text"
                        value={query}
                        onChange={(e) => { search(e.target.value); }}
                        placeholder="Search bills, companies, industries, states…"
                        className="flex-1 bg-transparent text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none"
                        autoFocus
                        aria-label="Global search"
                      />
                      <kbd className="flex-shrink-0 text-[10px] text-slate-600 font-mono bg-white/5 border border-white/8 rounded px-1.5 py-0.5">
                        Esc
                      </kbd>
                    </div>
                  </div>

                  {loading && (
                    <div className="px-4 py-4 flex items-center gap-2 text-xs text-slate-500">
                      <span className="inline-block w-3 h-3 border border-slate-600 border-t-slate-300 rounded-full animate-spin" />
                      Searching across all records…
                    </div>
                  )}

                  {!loading && query.length > 0 && results && results.total_matches === 0 && (
                    <div className="px-4 py-8 text-center text-sm text-slate-500">
                      No results for &ldquo;{query}&rdquo;
                    </div>
                  )}

                  {!loading && results && results.total_matches > 0 && (
                    <div className="max-h-[360px] overflow-y-auto">
                      {/* Group results by category */}
                      {Object.entries(
                        results.items.slice(0, 12).reduce((acc, item) => {
                          const cat = categoryLabels[item.category] ?? item.category;
                          if (!acc[cat]) acc[cat] = [];
                          acc[cat].push(item);
                          return acc;
                        }, {} as Record<string, typeof results.items>)
                      ).map(([cat, items]) => (
                        <div key={cat}>
                          <div className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-600 border-b border-white/5">
                            {cat}
                          </div>
                          {items.map((item) => (
                            <SearchResultItem
                              key={item.id}
                              item={item}
                              onClose={() => { setSearchOpen(false); clearSearch(); }}
                            />
                          ))}
                        </div>
                      ))}
                      {results.total_matches > 12 && (
                        <div className="border-t border-white/8 px-4 py-2 text-xs text-slate-600 text-center">
                          {results.total_matches - 12} more results — refine your query
                        </div>
                      )}
                    </div>
                  )}

                  {!loading && query.length === 0 && (
                    <div className="px-4 py-4">
                      <p className="text-xs font-medium text-slate-500 mb-2">Quick links</p>
                      <div className="grid grid-cols-2 gap-1">
                        {[
                          { href: "/bills", label: "All Bills", icon: "📜" },
                          { href: "/companies", label: "Companies", icon: "🏢" },
                          { href: "/predictions", label: "Predictions", icon: "📈" },
                          { href: "/live-discovery", label: "Live Discovery", icon: "📡" },
                        ].map((link) => (
                          <Link
                            key={link.href}
                            href={link.href}
                            onClick={() => { setSearchOpen(false); clearSearch(); }}
                            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                          >
                            <span>{link.icon}</span>
                            {link.label}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Notifications */}
            <Link
              href="/notifications"
              className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              aria-label="Notifications"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </Link>

            {/* User profile */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-xs font-bold text-white hover:opacity-90 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
                aria-label="User account menu"
                aria-expanded={profileOpen}
              >
                {session?.display_name?.charAt(0)?.toUpperCase() ?? "U"}
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-60 rounded-xl border border-white/8 bg-slate-900/98 backdrop-blur-xl shadow-2xl py-2 z-50 dropdown-enter">
                  <div className="px-4 py-2.5 border-b border-white/8">
                    <p className="font-semibold text-white text-sm truncate">
                      {session?.display_name || "Analyst Account"}
                    </p>
                    <p className="text-xs text-slate-400 truncate mt-0.5">
                      {session?.email || "Local Session"}
                    </p>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                        {session?.role || "VIEWER"}
                      </span>
                      <span className="text-[10px] text-slate-600 font-mono truncate">
                        {session?.tenant_id || "default"}
                      </span>
                    </div>
                  </div>

                  <div className="py-1">
                    <Link
                      href="/workspace"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                    >
                      <span>🏛</span> Workspace
                    </Link>
                    <Link
                      href="/settings"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                    >
                      <span>⚙</span> Settings
                    </Link>
                    <Link
                      href="/onboarding"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                    >
                      <span>✦</span> Onboarding Tour
                    </Link>
                  </div>

                  <div className="border-t border-white/8 pt-1">
                    {session ? (
                      <button
                        onClick={async () => {
                          setProfileOpen(false);
                          await authApi.logout();
                          window.location.href = "/login";
                        }}
                        className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-rose-400 hover:bg-white/5 transition-colors"
                      >
                        <span>→</span> Sign Out
                      </button>
                    ) : (
                      <Link
                        href="/login"
                        onClick={() => setProfileOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-sm text-blue-400 hover:bg-white/5 transition-colors"
                      >
                        Sign In / Register
                      </Link>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              aria-label="Open navigation menu"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      <MobileDrawer
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        session={session}
      />
    </>
  );
}

export default TopNavbar;
