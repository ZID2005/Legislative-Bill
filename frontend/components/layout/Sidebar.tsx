/**
 * components/layout/Sidebar.tsx
 * ==============================
 * Collapsible sidebar navigation for the SaaS platform.
 * Five sections: DISCOVER, ANALYZE, MONITOR, SYSTEM.
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: string;
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
      { label: "Workspace", href: "/workspace", icon: "🏛", description: "Personal legislative command center" },
      { label: "Watchlists", href: "/watchlists", icon: "⭐", description: "Custom entity watchlists" },
      { label: "Alerts", href: "/alerts", icon: "🔔", description: "Legislative change alerts" },
      { label: "Notifications", href: "/notifications", icon: "📬", description: "In-app notification center" },
    ],
  },
  {
    section: "DISCOVER",
    items: [
      { label: "Overview", href: "/overview", icon: "◉", description: "Platform KPIs & coverage" },
      { label: "Explorer", href: "/explorer", icon: "🔍", description: "Unified legislative discovery" },
      { label: "Bills", href: "/bills", icon: "📜", description: "Central & State legislation" },
      { label: "Companies", href: "/companies", icon: "🏢", description: "Corporate intelligence universe" },
      { label: "Industries", href: "/industries", icon: "🏭", description: "Industry classification" },
      { label: "Sectors", href: "/sectors", icon: "⬡", description: "Economic sector taxonomy" },
      { label: "States", href: "/states", icon: "🗺", description: "State legislative coverage" },
    ],
  },
  {
    section: "ANALYZE",
    items: [
      { label: "Predictions", href: "/predictions", icon: "📈", description: "Market impact predictions" },
      { label: "Risk", href: "/risk", icon: "⚠", description: "Risk classification matrix" },
      { label: "Anticipation", href: "/anticipation", icon: "⏱", description: "Pre-event market diffusion" },
    ],
  },
  {
    section: "MONITOR",
    items: [
      { label: "Legislative Monitoring", href: "/monitoring", icon: "📡", description: "Legislative source tracking" },
      { label: "Coverage", href: "/coverage", icon: "📊", description: "Platform coverage metrics" },
    ],
  },
  {
    section: "AI",
    items: [
      { label: "AI Analyst", href: "/ai-analyst", icon: "✦", description: "Groq AI explanations & Q&A" },
    ],
  },
  {
    section: "SETTINGS",
    items: [
      { label: "Settings", href: "/settings", icon: "⚙", description: "Account & delivery preferences" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-slate-950 border-r border-slate-800 transition-all duration-300",
        collapsed ? "w-14" : "w-60"
      )}
      aria-label="Main navigation"
    >
      {/* Logo + collapse toggle */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-slate-800 flex-shrink-0">
        {!collapsed && (
          <div>
            <div className="flex items-center gap-2">
              <span className="text-blue-400 text-lg font-bold">⚖</span>
              <span className="text-sm font-bold text-slate-100 leading-tight">
                LegisIntel
              </span>
            </div>
            <p className="text-[9px] text-slate-600 mt-0.5 pl-6">India · v1.0</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg
            className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path d="M11 19l-7-7 7-7M18 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {NAV_SECTIONS.map((section) => (
          <div key={section.section} className="mb-4">
            {!collapsed && (
              <p className="px-2 pb-1 text-[9px] font-bold text-slate-600 uppercase tracking-[0.15em]">
                {section.section}
              </p>
            )}
            <ul role="list" className="space-y-0.5">
              {section.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href === "/industries" && (pathname?.startsWith("/industry") || pathname?.startsWith("/industries"))) ||
                  (item.href !== "/overview" && item.href !== "/industries" && pathname?.startsWith(item.href));

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-all duration-150",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                        isActive
                          ? "bg-blue-900/30 text-blue-300 border border-blue-800/50"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                      )}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <span
                        className={cn(
                          "flex-shrink-0 text-base w-5 text-center",
                          isActive ? "text-blue-400" : "text-slate-500"
                        )}
                        aria-hidden="true"
                      >
                        {item.icon}
                      </span>
                      {!collapsed && (
                        <span className="truncate font-medium text-xs">
                          {item.label}
                        </span>
                      )}
                      {!collapsed && item.badge && (
                        <span className="ml-auto flex-shrink-0 rounded-full bg-blue-900/60 border border-blue-700/50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-300">
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
        <div className="border-t border-slate-800 p-3 flex-shrink-0">
          <div className="flex items-center gap-2.5 rounded-md px-2 py-1.5 hover:bg-slate-800 transition-colors cursor-pointer">
            <div className="h-6 w-6 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center text-xs text-slate-300 font-semibold flex-shrink-0">
              U
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-300 truncate">User</p>
              <p className="text-[10px] text-slate-600 truncate">Research Analyst</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
