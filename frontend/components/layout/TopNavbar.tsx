/**
 * components/layout/TopNavbar.tsx
 * =================================
 * Task 1.7A — Global Navigation Frame & Institutional Chrome.
 *
 * Implements the approved premium editorial-finance navigation:
 * 1. Streamlined 4-Hub Cognitive Model:
 *    - Legislation Hub (/bills, /explorer, /states, /latest-bills, /upcoming-legislation, /live-discovery, /bills/compare, /overview)
 *    - Markets & Risk Hub (/predictions, /risk, /anticipation)
 *    - Corporate Universe Hub (/companies, /industries, /sectors)
 *    - Institutional Direct Anchors: /workspace, /portfolio, /reports, /ai-analyst
 * 2. Strict Dual-Theme Polish:
 *    - Light, Dark, and System modes with calibrated semantic tokens
 *    - Zero hardcoded dark tints or invisible white text in daytime mode
 * 3. Accessibility & Motion:
 *    - Full keyboard navigation (Tab, Enter, Space, Arrows, Escape, ⌘K)
 *    - Mobile slide-over drawer with focus management and ARIA dialog
 *    - Respects prefers-reduced-motion
 *    - Live monitoring telemetry pulse (GET /api/v1/monitoring/overview)
 */

"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { UserSession, authApi } from "@/lib/api/auth";
import { monitoringApi } from "@/lib/api/monitoring";
import { portfolioApi } from "@/lib/api/portfolio";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { SeanceBrand } from "@/components/brand/SeanceBrand";
import { ThemeSwitcher } from "@/components/theme/ThemeSwitcher";
import { CollabToolbar, Collaborator, getAuthenticatedUserInitial } from "@/components/ui/collab-toolbar";
import { ImportHoldingsModal } from "@/components/portfolio/ImportHoldingsModal";

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
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-[var(--color-success-bg)] border border-[var(--color-success-border)] text-[var(--color-success)]">
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-success)] animate-pulse" />
        LIVE
      </span>
    );
  }
  if (badge === "NEW") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-[var(--color-info-bg)] border border-[var(--color-info-border)] text-[var(--color-info)]">
        NEW
      </span>
    );
  }
  if (badge === "AI") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-[var(--epistemic-prediction-bg)] border border-[var(--epistemic-prediction-border)] text-[var(--epistemic-prediction-text)]">
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
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Focus first focusable link inside dropdown on open
    const firstLink = menuRef.current?.querySelector<HTMLAnchorElement>("a");
    firstLink?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      onClose();
    }
  };

  if (!group.children) return null;

  return (
    <div
      ref={menuRef}
      onKeyDown={handleKeyDown}
      className="absolute top-full left-0 mt-1 w-84 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] shadow-2xl z-50 dropdown-enter overflow-hidden"
      role="menu"
      aria-label={`${group.label} navigation`}
    >
      <div className="p-1.5 divide-y divide-[var(--border-subtle)]">
        <div className="space-y-0.5">
          {group.children.map((child) => (
            <Link
              key={child.href}
              href={child.href}
              onClick={onClose}
              role="menuitem"
              className="flex items-start gap-2.5 px-3 py-2 rounded-md hover:bg-[var(--bg-card-hover)] transition-colors group focus:outline-none focus:bg-[var(--bg-card-hover)]"
            >
              {child.icon && (
                <span className="text-sm mt-0.5 flex-shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                  {child.icon}
                </span>
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-medium text-[var(--text-primary)] transition-colors">
                    {child.label}
                  </span>
                  {child.badge && <NavBadge badge={child.badge} />}
                </div>
                {child.description && (
                  <p className="text-[11px] text-[var(--text-muted)] mt-0.5 line-clamp-1">
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
  const drawerRef = useRef<HTMLDivElement>(null);

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
        className="fixed inset-0 bg-[var(--overlay-backdrop)] backdrop-blur-xs z-40 transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        ref={drawerRef}
        className="fixed inset-y-0 right-0 w-80 max-w-[85vw] bg-[var(--bg-surface)] border-l border-[var(--border-default)] z-50 flex flex-col shadow-2xl duration-200 ease-out transform"
        role="dialog"
        aria-label="Mobile navigation"
        aria-modal="true"
      >
        <div className="flex items-center justify-between px-4 py-3.5 border-b border-[var(--border-default)] bg-[var(--bg-base)]">
          <SeanceBrand
            size="sm"
            href={null}
            showSublabel={false}
            aria-label="Seance"
          />
          <button
            onClick={onClose}
            className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
            aria-label="Close navigation"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Mobile Theme Preference Selector */}
        <div className="px-4 py-2.5 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-surface)]">
          <span className="text-xs text-[var(--text-muted)] font-medium">Theme</span>
          <ThemeSwitcher size="sm" />
        </div>

        {/* Scrollable nav content */}
        <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-4" aria-label="Mobile navigation links">
          {/* Quick links */}
          <div className="grid grid-cols-2 gap-1.5 pb-2 border-b border-[var(--border-subtle)]">
            <Link
              href="/workspace"
              onClick={onClose}
              className={cn(
                "flex items-center gap-2 px-2.5 py-2 rounded text-xs font-medium transition-colors",
                pathname === "/workspace"
                  ? "bg-[var(--action-primary)] text-white font-semibold"
                  : "bg-[var(--bg-card)] border border-[var(--border-default)] text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
              )}
            >
              <span>🏛</span> Workspace
            </Link>
            <Link
              href="/portfolio"
              onClick={onClose}
              className={cn(
                "flex items-center gap-2 px-2.5 py-2 rounded text-xs font-medium transition-colors",
                pathname === "/portfolio"
                  ? "bg-[var(--action-primary)] text-white font-semibold"
                  : "bg-[var(--bg-card)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
              )}
            >
              <span>💼</span> Portfolio
            </Link>
          </div>

          {NAV_GROUPS.filter(g => g.id !== "workspace" && g.id !== "portfolio").map((group) => (
            <div key={group.id} className="space-y-1">
              <div className="px-2 py-0.5">
                <span className="text-[10px] font-bold tracking-wider uppercase text-[var(--text-muted)]">
                  {group.label}
                </span>
              </div>

              {group.href && (
                <Link
                  href={group.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded text-xs font-medium transition-colors",
                    pathname === group.href
                      ? "bg-[var(--bg-card-hover)] text-[var(--text-primary)] font-semibold border border-[var(--border-strong)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
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
                            isActive
                              ? "bg-[var(--bg-card-hover)] text-[var(--action-primary)] font-semibold border border-[var(--border-strong)]"
                              : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
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
          <div className="space-y-1 pt-2 border-t border-[var(--border-subtle)]">
            <div className="px-2 py-0.5">
              <span className="text-[10px] font-bold tracking-wider uppercase text-[var(--text-muted)]">
                System &amp; Observability
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
                    className={cn(
                      "flex items-center gap-2 px-2.5 py-1.5 rounded text-xs transition-colors",
                      pathname === item.href
                        ? "bg-[var(--bg-card-hover)] text-[var(--text-primary)] font-semibold"
                        : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                    )}
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
        <div className="border-t border-[var(--border-default)] p-3 bg-[var(--bg-base)] flex-shrink-0">
          <div className="flex items-center gap-2.5 px-2 py-1.5 rounded">
            <div className="h-7 w-7 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center text-xs font-bold text-[var(--text-primary)] flex-shrink-0">
              {getAuthenticatedUserInitial(session)}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-[var(--text-primary)] truncate">
                {session?.display_name || session?.name || "Analyst"}
              </p>
              <p className="text-[10px] text-[var(--text-muted)] font-mono truncate">
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
  const router = useRouter();

  // Task 1.15A: Suppress TopNavbar on /onboarding
  if (pathname === "/onboarding" || (typeof pathname === "string" && pathname.startsWith("/onboarding"))) {
    return null;
  }

  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [session, setSession] = useState<UserSession | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
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

  // Authenticated user avatar for the CollabToolbar (Phase 3: single avatar with uppercase initial)
  const authenticatedUser = React.useMemo<Collaborator>(() => {
    const initial = getAuthenticatedUserInitial(session);
    const displayName =
      (session?.display_name && session.display_name.trim()) ||
      (session?.name && session.name.trim()) ||
      (session?.email && session.email.split("@")[0]) ||
      "Institutional Analyst";

    return {
      name: displayName,
      initials: initial,
      role: session?.role || "MEMBER",
      tenantId: session?.tenant_id || "default",
      email: session?.email,
    };
  }, [session]);

  // Handle portfolio holdings file import from CollabToolbar
  const handleImportHoldings = async (holdings: any[]) => {
    try {
      const pfs = await portfolioApi.listPortfolios();
      const targetId = pfs[0]?.portfolio_id || "default_portfolio";
      await portfolioApi.importHoldings(targetId, holdings);
      setUploadModalOpen(false);
      if (pathname === "/portfolio") {
        window.location.reload();
      } else {
        router.push("/portfolio");
      }
    } catch (err) {
      console.error("Header holdings import error:", err);
      throw err;
    }
  };

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-30 h-14 navbar-blur bg-[var(--bg-nav)] border-b border-[var(--border-default)] flex items-center transition-colors duration-150"
        role="banner"
      >
        <div className="flex items-center w-full px-4 gap-2">
          {/* Brand Logo */}
          <SeanceBrand
            size="sm"
            href="/"
            showSublabel={false}
            className="mr-2 shrink-0"
            aria-label="Seance Home"
          />

          {/* Desktop Navigation */}
          <nav
            ref={navRef}
            className="hidden lg:flex items-center gap-0.5 flex-1 min-w-0"
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
                      "flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)] shrink-0",
                      isActive
                        ? "text-[var(--text-primary)] bg-[var(--bg-card-hover)] border border-[var(--border-strong)] font-semibold shadow-xs"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                    )}
                  >
                    {group.icon && <span className="text-xs">{group.icon}</span>}
                    <span>{group.label}</span>
                    {group.badge && <NavBadge badge={group.badge} />}
                  </Link>
                );
              }

              // Dropdown group
              return (
                <div key={group.id} className="relative shrink-0">
                  <button
                    onClick={() => setActiveDropdown(isOpen ? null : group.id)}
                    onMouseEnter={() => setActiveDropdown(group.id)}
                    onKeyDown={(e) => {
                      if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setActiveDropdown(group.id);
                      } else if (e.key === "Escape") {
                        setActiveDropdown(null);
                      }
                    }}
                    className={cn(
                      "flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]",
                      isActive || isOpen
                        ? "text-[var(--text-primary)] bg-[var(--bg-card-hover)] border border-[var(--border-strong)] font-semibold shadow-xs"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                    )}
                    aria-expanded={isOpen}
                    aria-haspopup="true"
                  >
                    <span>{group.label}</span>
                    <svg
                      className={cn("h-3 w-3 transition-transform duration-150 text-[var(--text-muted)]", isOpen && "rotate-180")}
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
          <div className="flex items-center gap-1.5 ml-auto shrink-0">
            {/* Command Palette Trigger Button (⌘K) */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-[var(--text-secondary)] bg-[var(--bg-surface)] border border-[var(--border-default)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
              aria-label="Open command palette (⌘K)"
              id="global-search-btn"
            >
              <svg className="h-3.5 w-3.5 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <circle cx={11} cy={11} r={8} />
                <path strokeLinecap="round" d="M21 21l-4.35-4.35" />
              </svg>
              <span className="hidden 2xl:inline">Search &amp; Commands</span>
              <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[9px] font-mono bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded text-[var(--text-muted)]">
                ⌘K
              </kbd>
            </button>

            {/* Live Monitoring Pulse Indicator */}
            <Link
              href="/monitoring"
              className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded border border-[var(--border-default)] bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] hover:border-[var(--border-strong)] transition-colors text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              title="Real-time legislative source health"
            >
              <span
                className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  pulseInfo.status === "healthy"
                    ? "bg-emerald-500 animate-pulse"
                    : pulseInfo.status === "degraded"
                    ? "bg-amber-500 animate-pulse"
                    : "bg-slate-400"
                )}
              />
              <span className="uppercase tracking-wider font-semibold">{pulseInfo.text}</span>
            </Link>

            {/* Notifications Bell */}
            <Link
              href="/notifications"
              className="relative p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
              aria-label="Notifications"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </Link>

            {/* Desktop Theme Switcher */}
            <ThemeSwitcher size="sm" className="hidden sm:inline-flex" />

            {/* Collaboration Toolbar & Secondary Actions Dropdown */}
            <div className="relative" ref={profileRef}>
              <CollabToolbar
                groups={[["chat"], "avatar", ["upload", "menu"]]}
                userAvatar={authenticatedUser}
                avatars={[authenticatedUser]}
                actionProps={{
                  chat: {
                    onClick: () => router.push("/ai-analyst"),
                    isActive: pathname === "/ai-analyst",
                    ariaLabel: "Grounded AI Analyst (/ai-analyst)",
                    title: "Open Grounded AI Analyst Terminal (/ai-analyst)",
                  },
                  upload: {
                    onClick: () => setUploadModalOpen(true),
                    ariaLabel: "Import Holdings CSV/JSON",
                    title: "Import Portfolio Holdings (CSV/JSON)",
                  },
                  menu: {
                    onClick: () => setProfileOpen((prev) => !prev),
                    isActive: profileOpen,
                    ariaLabel: "Secondary Header Menu",
                    title: "Account & Secondary Workspace Actions",
                  },
                }}
                onAvatarClick={() => setProfileOpen((prev) => !prev)}
              />

              {profileOpen && (
                <div
                  role="menu"
                  aria-label="User account and secondary workspace actions"
                  className="absolute right-0 mt-2 w-64 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface)] shadow-2xl py-2 z-50 dropdown-enter"
                >
                  <div className="px-4 py-2 border-b border-[var(--border-default)]">
                    <p className="font-semibold text-[var(--text-primary)] text-xs truncate">
                      {session?.display_name || "Institutional Analyst"}
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)] truncate mt-0.5">
                      {session?.email || "analyst@institutional.org"}
                    </p>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span className="text-[9.5px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-info-bg)] text-[var(--color-info)] border border-[var(--color-info-border)] uppercase font-semibold">
                        {session?.role || "MEMBER"}
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)] font-mono truncate">
                        {session?.tenant_id || "default"}
                      </span>
                    </div>
                  </div>

                  <div className="py-1 text-xs">
                    <Link
                      href="/workspace"
                      onClick={() => setProfileOpen(false)}
                      role="menuitem"
                      className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <span>🏛</span> Daily Workspace
                    </Link>
                    <Link
                      href="/watchlists"
                      onClick={() => setProfileOpen(false)}
                      role="menuitem"
                      className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <span>⭐</span> Custom Watchlists
                    </Link>
                    <Link
                      href="/alerts"
                      onClick={() => setProfileOpen(false)}
                      role="menuitem"
                      className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <span>🔔</span> Alerts Center
                    </Link>
                    <Link
                      href="/coverage"
                      onClick={() => setProfileOpen(false)}
                      role="menuitem"
                      className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <span>📊</span> Platform Coverage Audit
                    </Link>
                    <Link
                      href="/live-discovery"
                      onClick={() => setProfileOpen(false)}
                      role="menuitem"
                      className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <span>📡</span> Live Intake Feed
                    </Link>
                    <Link
                      href="/settings"
                      onClick={() => setProfileOpen(false)}
                      role="menuitem"
                      className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <span>⚙</span> Settings &amp; RBAC
                    </Link>
                    <Link
                      href="/onboarding"
                      onClick={() => setProfileOpen(false)}
                      role="menuitem"
                      className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      <span>✦</span> Onboarding Tour
                    </Link>
                  </div>

                  <div className="border-t border-[var(--border-subtle)] pt-1 text-xs">
                    {session ? (
                      <button
                        onClick={async () => {
                          setProfileOpen(false);
                          await authApi.logout();
                          window.location.href = "/login";
                        }}
                        role="menuitem"
                        className="w-full flex items-center gap-2.5 px-4 py-1.5 text-[var(--color-danger)] hover:bg-[var(--bg-card-hover)] transition-colors text-left font-medium"
                      >
                        <span>→</span> Sign Out
                      </button>
                    ) : (
                      <Link
                        href="/login"
                        onClick={() => setProfileOpen(false)}
                        role="menuitem"
                        className="flex items-center gap-2.5 px-4 py-1.5 text-[var(--action-primary)] hover:bg-[var(--bg-card-hover)] transition-colors font-medium"
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
              className="lg:hidden p-1.5 rounded-md text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]"
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

      {/* Portfolio Holdings Upload Modal */}
      <ImportHoldingsModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onImport={handleImportHoldings}
      />
    </>
  );
}

export default TopNavbar;
