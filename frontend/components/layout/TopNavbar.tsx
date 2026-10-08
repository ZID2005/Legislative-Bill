/**
 * components/layout/TopNavbar.tsx
 * =================================
 * Task 8.31C — Modern Institutional Top Navigation Bar.
 *
 * Implements the approved 5-workspace institutional navigation:
 * 1. Legislation Hub (/bills, /explorer, /states, /latest-bills, /upcoming-legislation, /live-discovery, /bills/compare, /overview)
 * 2. Markets & Risk Hub (/predictions, /risk, /anticipation)
 * 3. Corporate Universe Hub (/companies, /industries, /sectors)
 * 4. Portfolio & Executive Hub (/portfolio, /reports, /workspace)
 * 5. System & Observability Hub (/monitoring, /coverage, /watchlists, /alerts, /notifications)
 *
 * Global Institutional Anchors:
 * - Brand/Home: /
 * - Primary Anchor: /workspace ("What changed since I last looked?")
 * - Direct Anchors: /portfolio, /reports
 * - Command Palette (⌘K)
 * - Live Monitoring Pulse (Real API telemetry from /monitoring/overview)
 * - AI Analyst Quick Launch (✦ /ai-analyst)
 * - Notification Bell (/notifications)
 * - User Profile & Tenant Switcher (/settings, /coverage)
 */

"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSearch } from "@/hooks/useSearch";
import { UserSession, authApi } from "@/lib/api/auth";
import { monitoringApi } from "@/lib/api/monitoring";
import { CommandPalette } from "@/components/ui/CommandPalette";
import type { SearchResultItem } from "@/types/api";

// ---------------------------------------------------------------------------
// Nav types and structures
// ---------------------------------------------------------------------------

export interface NavChild {
  label: string;
  href: string;
  description?: string;
  badge?: "LIVE" | "NEW" | "AI";
  icon?: string;
}

export interface NavGroup {
  id: string;
  label: string;
  icon?: string;
  href?: string; // if set, direct link (no dropdown)
  children?: NavChild[];
  badge?: "LIVE" | "NEW" | "AI";
}

export const NAV_GROUPS: NavGroup[] = [
  {
    id: "workspace",
    label: "Workspace",
    href: "/workspace",
    icon: "🏛",
  },
  {
    id: "legislation",
    label: "Legislation",
    children: [
      { label: "Bills Directory", href: "/bills", icon: "📜", description: "Canonical parliamentary act registry" },
      { label: "Legislative Explorer", href: "/explorer", icon: "🔍", description: "Dual-view multi-facet statutory discovery" },
      { label: "State Assemblies", href: "/states", icon: "🗺", description: "Sub-national legislative coverage — AP, KA, KL, TS" },
      { label: "Latest Enactments", href: "/latest-bills", icon: "⚡", description: "Central & State bills introduced", badge: "LIVE" },
      { label: "Upcoming Calendar", href: "/upcoming-legislation", icon: "📅", description: "Parliamentary sessions & committee agendas" },
      { label: "Live Intake Feed", href: "/live-discovery", icon: "📡", description: "Unmodelled gazette intake feed", badge: "LIVE" },
      { label: "Bill Comparison", href: "/bills/compare", icon: "⚖", description: "Side-by-side statutory provision diff" },
      { label: "Platform Overview", href: "/overview", icon: "◉", description: "System-wide coverage & baseline metrics" },
    ],
  },
  {
    id: "markets",
    label: "Markets & Risk",
    children: [
      { label: "Market Predictions", href: "/predictions", icon: "📈", description: "4,700 event-study records & 5 horizons" },
      { label: "Legislative Risk Matrix", href: "/risk", icon: "⚠", description: "Systemic risk classification & ISIN calculator" },
      { label: "Pre-Event Anticipation", href: "/anticipation", icon: "⏱", description: "940 diffusion scores & news evidence" },
    ],
  },
  {
    id: "entities",
    label: "Corporate Universe",
    children: [
      { label: "Corporate Directory", href: "/companies", icon: "🏢", description: "70 entities: 47 Quant + 20 Intel + 3 Ref" },
      { label: "Industries Taxonomy", href: "/industries", icon: "🏭", description: "13 sectors & granular industries" },
      { label: "Macro Economic Sectors", href: "/sectors", icon: "⬡", description: "Macro policy transmission map" },
    ],
  },
  {
    id: "portfolio",
    label: "Portfolio",
    href: "/portfolio",
    icon: "💼",
    badge: "NEW",
  },
  {
    id: "reports",
    label: "Reports",
    href: "/reports",
    icon: "📑",
    badge: "NEW",
  },
  {
    id: "ai",
    label: "AI Analyst",
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
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-emerald-500/15 border border-emerald-500/25 text-emerald-400">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        LIVE
      </span>
    );
  }
  if (badge === "NEW") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-blue-500/15 border border-blue-500/25 text-blue-400">
        NEW
      </span>
    );
  }
  if (badge === "AI") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-violet-500/15 border border-violet-500/25 text-violet-400">
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
      className="absolute top-full left-0 mt-1 w-84 rounded-lg border border-white/10 bg-[#0c1322] shadow-2xl shadow-black/80 z-50 dropdown-enter overflow-hidden"
      role="menu"
    >
      <div className="p-1.5 divide-y divide-white/5">
        <div className="space-y-0.5">
          {group.children.map((child) => (
            <Link
              key={child.href}
              href={child.href}
              onClick={onClose}
              role="menuitem"
              className="flex items-start gap-2.5 px-3 py-2 rounded-md hover:bg-[#121b2f] transition-colors group"
            >
              {child.icon && (
                <span className="text-sm mt-0.5 flex-shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                  {child.icon}
                </span>
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-medium text-slate-200 group-hover:text-white transition-colors">
                    {child.label}
                  </span>
                  {child.badge && <NavBadge badge={child.badge} />}
                </div>
                {child.description && (
                  <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                    {child.description}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Mobile Drawer
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
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-xs z-40 transition-opacity duration-200 lg:hidden"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        className="fixed inset-y-0 right-0 w-80 max-w-[85vw] bg-[#0c1322] border-l border-white/10 z-50 flex flex-col shadow-2xl duration-200 ease-out transform lg:hidden"
        role="dialog"
        aria-label="Mobile navigation"
      >
        <div className="flex items-center justify-between px-4 py-3.5 border-b border-white/10 bg-[#090e18]">
          <div className="flex items-center gap-2">
            <span className="text-blue-400 text-lg">⚖</span>
            <span className="text-sm font-bold text-white tracking-tight">LegisIntel</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            aria-label="Close navigation"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable nav content */}
        <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-4" aria-label="Mobile navigation">
          {/* Quick links */}
          <div className="grid grid-cols-2 gap-1.5 pb-2 border-b border-white/5">
            <Link
              href="/workspace"
              onClick={onClose}
              className="flex items-center gap-2 px-2.5 py-2 rounded bg-indigo-600/15 border border-indigo-500/25 text-indigo-300 text-xs font-medium"
            >
              <span>🏛</span> Workspace
            </Link>
            <Link
              href="/portfolio"
              onClick={onClose}
              className="flex items-center gap-2 px-2.5 py-2 rounded bg-white/5 border border-white/5 text-slate-300 text-xs font-medium"
            >
              <span>💼</span> Portfolio
            </Link>
          </div>

          {NAV_GROUPS.filter(g => g.id !== "workspace" && g.id !== "portfolio").map((group) => (
            <div key={group.id} className="space-y-1">
              <div className="px-2 py-0.5">
                <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400">
                  {group.label}
                </span>
              </div>

              {group.href && (
                <Link
                  href={group.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded text-xs font-medium transition-colors",
                    pathname === group.href ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5"
                  )}
                >
                  {group.icon && <span>{group.icon}</span>}
                  <span>{group.label}</span>
                  {group.badge && <NavBadge badge={group.badge} />}
                </Link>
              )}

              {group.children && (
                <ul className="space-y-0.5 pl-1">
                  {group.children.map((child) => {
                    const isActive = pathname === child.href;
                    return (
                      <li key={child.href}>
                        <Link
                          href={child.href}
                          onClick={onClose}
                          className={cn(
                            "flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors",
                            isActive ? "bg-indigo-600/20 text-indigo-300 font-medium" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                          )}
                        >
                          <div className="flex items-center gap-2 truncate">
                            {child.icon && <span className="opacity-70">{child.icon}</span>}
                            <span className="truncate">{child.label}</span>
                          </div>
                          {child.badge && <NavBadge badge={child.badge} />}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          ))}

          {/* System & Observability links */}
          <div className="space-y-1 pt-2 border-t border-white/5">
            <div className="px-2 py-0.5">
              <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400">
                System & Observability
              </span>
            </div>
            <ul className="space-y-0.5 pl-1">
              {[
                { href: "/monitoring", label: "Legislative Monitoring", icon: "📡" },
                { href: "/coverage", label: "Platform Coverage", icon: "📊" },
                { href: "/watchlists", label: "Custom Watchlists", icon: "⭐" },
                { href: "/alerts", label: "Alerts Center", icon: "🔔" },
                { href: "/notifications", label: "Notifications", icon: "📬" },
                { href: "/settings", label: "Settings & RBAC", icon: "⚙" },
              ].map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={onClose}
                    className="flex items-center gap-2 px-2.5 py-1.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  >
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </nav>

        {/* Drawer footer */}
        <div className="border-t border-white/10 p-3 bg-[#090e18] flex-shrink-0">
          <div className="flex items-center gap-2.5 px-2 py-1.5 rounded">
            <div className="h-7 w-7 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center text-xs font-bold text-slate-200 flex-shrink-0">
              {session?.display_name?.charAt(0)?.toUpperCase() ?? "U"}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-200 truncate">
                {session?.display_name || "Analyst"}
              </p>
              <p className="text-[10px] text-slate-400 font-mono truncate">
                {session?.role || "MEMBER"} · {session?.tenant_id || "default"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Main TopNavbar Component
// ---------------------------------------------------------------------------

export function TopNavbar() {
  const pathname = usePathname();
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [session, setSession] = useState<UserSession | null>(null);
  const [monitoringOverview, setMonitoringOverview] = useState<any>(null);
  const [monitoringLoading, setMonitoringLoading] = useState(true);

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

  // Fetch real monitoring pulse health
  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        setMonitoringLoading(true);
        const data = await monitoringApi.getOverview();
        if (isMounted) {
          setMonitoringOverview(data);
        }
      } catch {
        if (isMounted) {
          setMonitoringOverview(null);
        }
      } finally {
        if (isMounted) {
          setMonitoringLoading(false);
        }
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 60000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Keyboard shortcut ⌘K / Ctrl+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setCommandPaletteOpen(false);
        setActiveDropdown(null);
        setProfileOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Click outside to close dropdowns
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setActiveDropdown(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

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

  // Determine pulse status string and health color
  const pulseInfo = React.useMemo(() => {
    if (monitoringLoading && !monitoringOverview) {
      return { text: "CHECKING...", status: "loading" };
    }
    if (!monitoringOverview || typeof monitoringOverview.total_sources !== "number") {
      return { text: "STATUS UNKNOWN", status: "unknown" };
    }
    const total = monitoringOverview.total_sources;
    const enabled = monitoringOverview.enabled_sources ?? total;
    const isDegraded = monitoringOverview.system_status && monitoringOverview.system_status !== "OPERATIONAL";
    return {
      text: `${enabled}/${total} Active`,
      status: isDegraded ? "degraded" : "healthy",
    };
  }, [monitoringOverview, monitoringLoading]);

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-30 h-14 navbar-blur bg-[#070b12]/95 border-b border-white/10 flex items-center"
        role="banner"
      >
        <div className="flex items-center w-full px-4 gap-2">
          {/* Brand Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 mr-3 flex-shrink-0 group"
            aria-label="LegisIntel Home"
          >
            <span className="text-blue-400 text-lg group-hover:text-blue-300 transition-colors">⚖</span>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-white tracking-tight leading-none">LegisIntel</span>
              <span className="text-[9px] font-mono text-slate-400 leading-tight">Institutional Terminal</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav
            ref={navRef}
            className="hidden lg:flex items-center gap-1 flex-1"
            aria-label="Main navigation"
          >
            {NAV_GROUPS.map((group) => {
              const isActive = isGroupActive(group);
              const isOpen = activeDropdown === group.id;

              if (group.href && !group.children) {
                // Direct anchor
                return (
                  <Link
                    key={group.id}
                    href={group.href}
                    className={cn(
                      "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors",
                      isActive
                        ? "text-white bg-white/10 font-semibold"
                        : "text-slate-300 hover:text-white hover:bg-white/5"
                    )}
                  >
                    {group.icon && <span className="text-xs">{group.icon}</span>}
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
                      "flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors",
                      isActive || isOpen
                        ? "text-white bg-white/10 font-semibold"
                        : "text-slate-300 hover:text-white hover:bg-white/5"
                    )}
                    aria-expanded={isOpen}
                    aria-haspopup="true"
                  >
                    <span>{group.label}</span>
                    <svg
                      className={cn("h-3 w-3 transition-transform duration-150 text-slate-400", isOpen && "rotate-180")}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
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

          {/* Right Utility Controls */}
          <div className="flex items-center gap-2 ml-auto">
            {/* Command Palette Trigger Button (⌘K) */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs text-slate-300 bg-white/5 border border-white/10 hover:text-white hover:bg-white/10 transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500"
              aria-label="Open command palette (⌘K)"
              id="global-search-btn"
            >
              <svg className="h-3.5 w-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <circle cx={11} cy={11} r={8} />
                <path strokeLinecap="round" d="M21 21l-4.35-4.35" />
              </svg>
              <span className="hidden sm:inline">Search & Commands</span>
              <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[9px] font-mono bg-white/5 border border-white/10 rounded text-slate-400">
                ⌘K
              </kbd>
            </button>

            {/* Live Monitoring Pulse Indicator */}
            <Link
              href="/monitoring"
              className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded border border-white/10 bg-white/5 hover:bg-white/10 transition-colors text-[10px] font-mono text-slate-300"
              title="Real-time legislative source health"
            >
              <span
                className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  pulseInfo.status === "healthy"
                    ? "bg-emerald-400 animate-pulse"
                    : pulseInfo.status === "degraded"
                    ? "bg-amber-400 animate-pulse"
                    : "bg-slate-500"
                )}
              />
              <span className="uppercase tracking-wider">{pulseInfo.text}</span>
            </Link>

            {/* Notifications Bell */}
            <Link
              href="/notifications"
              className="relative p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500"
              aria-label="Notifications"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </Link>

            {/* User Profile Menu */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="h-7 w-7 rounded-full bg-slate-800 border border-white/20 flex items-center justify-center text-xs font-bold text-slate-100 hover:border-indigo-400 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500"
                aria-label="User account menu"
                aria-expanded={profileOpen}
              >
                {session?.display_name?.charAt(0)?.toUpperCase() ?? "A"}
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-64 rounded-lg border border-white/10 bg-[#0c1322] shadow-2xl py-2 z-50 dropdown-enter">
                  <div className="px-4 py-2 border-b border-white/10">
                    <p className="font-semibold text-white text-xs truncate">
                      {session?.display_name || "Institutional Analyst"}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {session?.email || "analyst@institutional.org"}
                    </p>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span className="text-[9.5px] font-mono px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 uppercase">
                        {session?.role || "MEMBER"}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono truncate">
                        {session?.tenant_id || "default"}
                      </span>
                    </div>
                  </div>

                  <div className="py-1 text-xs">
                    <Link
                      href="/workspace"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-1.5 text-slate-300 hover:bg-[#121b2f] hover:text-white transition-colors"
                    >
                      <span>🏛</span> Daily Workspace
                    </Link>
                    <Link
                      href="/watchlists"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-1.5 text-slate-300 hover:bg-[#121b2f] hover:text-white transition-colors"
                    >
                      <span>⭐</span> Custom Watchlists
                    </Link>
                    <Link
                      href="/alerts"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-1.5 text-slate-300 hover:bg-[#121b2f] hover:text-white transition-colors"
                    >
                      <span>🔔</span> Alerts Center
                    </Link>
                    <Link
                      href="/coverage"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-1.5 text-slate-300 hover:bg-[#121b2f] hover:text-white transition-colors"
                    >
                      <span>📊</span> Platform Coverage Audit
                    </Link>
                    <Link
                      href="/settings"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-1.5 text-slate-300 hover:bg-[#121b2f] hover:text-white transition-colors"
                    >
                      <span>⚙</span> Settings & RBAC
                    </Link>
                    <Link
                      href="/onboarding"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-1.5 text-slate-300 hover:bg-[#121b2f] hover:text-white transition-colors"
                    >
                      <span>✦</span> Onboarding Tour
                    </Link>
                  </div>

                  <div className="border-t border-white/10 pt-1 text-xs">
                    {session ? (
                      <button
                        onClick={async () => {
                          setProfileOpen(false);
                          await authApi.logout();
                          window.location.href = "/login";
                        }}
                        className="w-full flex items-center gap-2.5 px-4 py-1.5 text-rose-400 hover:bg-white/5 transition-colors"
                      >
                        <span>→</span> Sign Out
                      </button>
                    ) : (
                      <Link
                        href="/login"
                        onClick={() => setProfileOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-1.5 text-blue-400 hover:bg-white/5 transition-colors"
                      >
                        Sign In / Register
                      </Link>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Mobile Hamburger */}
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500"
              aria-label="Open navigation menu"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Slide-Over Drawer */}
      <MobileDrawer
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        session={session}
      />

      {/* Command Palette (⌘K) Modal */}
      <CommandPalette
        open={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />
    </>
  );
}

export default TopNavbar;
