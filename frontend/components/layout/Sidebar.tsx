/**
 * components/layout/Sidebar.tsx
 * ==============================
 * Institutional collapsible sidebar navigation for Seance.
 * Five sections: WORKSPACE, DISCOVER, ANALYZE, MONITOR, AI, SETTINGS.
 *
 * Implements:
 * - Seance brand identity with BrandEmblem
 * - Standardized vector iconography
 * - Dual-theme semantic tokens
 * - ARIA navigation landmark and current page attributes
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { SeanceBrand } from "@/components/brand/SeanceBrand";
import { BrandEmblem } from "@/components/brand/BrandEmblem";
import {
  WorkspaceIcon,
  WatchlistIcon,
  AlertsIcon,
  NotificationsIcon,
  OverviewIcon,
  ExplorerIcon,
  BillsIcon,
  CompaniesIcon,
  IndustriesIcon,
  SectorsIcon,
  StatesIcon,
  PredictionsIcon,
  RiskIcon,
  AnticipationIcon,
  MonitoringIcon,
  CoverageIcon,
  AiAnalystIcon,
  SettingsIcon,
  ChevronLeftIcon,
} from "@/components/ui/Icons";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ size?: any; className?: string }>;
  badge?: string;
  description?: string;
}

interface NavSection {
  section: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    section: "WORKSPACE",
    items: [
      { label: "Workspace", href: "/workspace", icon: WorkspaceIcon, description: "Personal legislative command center" },
      { label: "Watchlists", href: "/watchlists", icon: WatchlistIcon, description: "Custom entity watchlists" },
      { label: "Alerts", href: "/alerts", icon: AlertsIcon, description: "Legislative change alerts" },
      { label: "Notifications", href: "/notifications", icon: NotificationsIcon, description: "In-app notification center" },
    ],
  },
  {
    section: "DISCOVER",
    items: [
      { label: "Overview", href: "/overview", icon: OverviewIcon, description: "Platform KPIs & coverage" },
      { label: "Explorer", href: "/explorer", icon: ExplorerIcon, description: "Unified legislative discovery" },
      { label: "Bills", href: "/bills", icon: BillsIcon, description: "Central & State legislation" },
      { label: "Companies", href: "/companies", icon: CompaniesIcon, description: "Corporate intelligence universe" },
      { label: "Industries", href: "/industries", icon: IndustriesIcon, description: "Industry classification" },
      { label: "Sectors", href: "/sectors", icon: SectorsIcon, description: "Economic sector taxonomy" },
      { label: "States", href: "/states", icon: StatesIcon, description: "State legislative coverage" },
    ],
  },
  {
    section: "ANALYZE",
    items: [
      { label: "Predictions", href: "/predictions", icon: PredictionsIcon, description: "Market impact predictions" },
      { label: "Risk", href: "/risk", icon: RiskIcon, description: "Risk classification matrix" },
      { label: "Anticipation", href: "/anticipation", icon: AnticipationIcon, description: "Pre-event market diffusion" },
    ],
  },
  {
    section: "MONITOR",
    items: [
      { label: "Legislative Monitoring", href: "/monitoring", icon: MonitoringIcon, description: "Legislative source tracking" },
      { label: "Coverage", href: "/coverage", icon: CoverageIcon, description: "Platform coverage metrics" },
    ],
  },
  {
    section: "AI",
    items: [
      { label: "AI Analyst", href: "/ai-analyst", icon: AiAnalystIcon, description: "Groq AI explanations & Q&A" },
    ],
  },
  {
    section: "SETTINGS",
    items: [
      { label: "Settings", href: "/settings", icon: SettingsIcon, description: "Account & delivery preferences" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-[var(--bg-surface)] border-r border-[var(--border-default)] transition-all duration-200 select-none",
        collapsed ? "w-16" : "w-60"
      )}
      aria-label="Main navigation"
    >
      {/* Brand + collapse toggle */}
      <div className="flex items-center justify-between px-3.5 py-3 border-b border-[var(--border-default)] flex-shrink-0">
        {!collapsed ? (
          <div className="min-w-0 pr-1">
            <SeanceBrand size="sm" sublabel="Terminal" />
          </div>
        ) : (
          <div className="mx-auto">
            <BrandEmblem size="sm" variant="brand" />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeftIcon
            size="sm"
            className={cn("transition-transform duration-200", collapsed && "rotate-180")}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {NAV_SECTIONS.map((section) => (
          <div key={section.section}>
            {!collapsed && (
              <p className="px-2.5 pb-1 text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-[0.15em]">
                {section.section}
              </p>
            )}
            <ul role="list" className="space-y-0.5">
              {section.items.map((item) => {
                const IconComponent = item.icon;
                const isActive =
                  pathname === item.href ||
                  (item.href === "/industries" &&
                    (pathname?.startsWith("/industry") || pathname?.startsWith("/industries"))) ||
                  (item.href !== "/overview" &&
                    item.href !== "/industries" &&
                    pathname?.startsWith(item.href));

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all duration-150",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]",
                        isActive
                          ? "bg-[var(--action-primary)]/12 text-[var(--action-primary)] font-semibold border border-[var(--action-primary)]/25"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                      )}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <span
                        className={cn(
                          "flex-shrink-0 inline-flex items-center justify-center",
                          isActive ? "text-[var(--action-primary)]" : "text-[var(--text-muted)]"
                        )}
                        aria-hidden="true"
                      >
                        <IconComponent size="sm" />
                      </span>
                      {!collapsed && (
                        <span className="truncate">
                          {item.label}
                        </span>
                      )}
                      {!collapsed && item.badge && (
                        <span className="ml-auto flex-shrink-0 rounded-full bg-[var(--action-primary)]/15 border border-[var(--action-primary)]/30 px-1.5 py-0.2 text-[9px] font-mono font-semibold text-[var(--action-primary)]">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Bottom user placeholder */}
      {!collapsed && (
        <div className="border-t border-[var(--border-default)] p-3 flex-shrink-0 bg-[var(--bg-base)]">
          <div className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 hover:bg-[var(--bg-card-hover)] transition-colors cursor-pointer">
            <div className="h-6 w-6 rounded-full bg-[var(--action-primary)]/15 border border-[var(--action-primary)]/30 flex items-center justify-center text-[10px] text-[var(--action-primary)] font-bold flex-shrink-0">
              S
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-[var(--text-primary)] truncate">Seance Analyst</p>
              <p className="text-[10px] text-[var(--text-muted)] truncate">Decision Intelligence</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
