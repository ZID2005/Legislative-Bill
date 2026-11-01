/**
 * components/settings/SettingsNav.tsx
 * ===================================
 * Master-detail sidebar navigation for the Settings & Governance hub.
 *
 * Implements:
 * - 4 approved governance sections:
 *     1. Account & Security
 *     2. Organization & Team
 *     3. Notifications & Delivery
 *     4. Data Governance & Privacy
 * - Visual hierarchy with section titles, descriptions, and active state indicators
 * - Responsive layout: master-detail sidebar on desktop, horizontal segmented bar on mobile
 */

"use client";

import React from "react";

export type SettingsSectionId = "account" | "organization" | "notifications" | "privacy";

export interface SettingsSectionItem {
  id: SettingsSectionId;
  title: string;
  shortTitle: string;
  description: string;
  icon: string;
}

export const SETTINGS_SECTIONS: SettingsSectionItem[] = [
  {
    id: "account",
    title: "Account & Security",
    shortTitle: "Account",
    description: "Identity, session HMAC cryptography, and authentication invariants",
    icon: "🛡",
  },
  {
    id: "organization",
    title: "Organization & Team",
    shortTitle: "Organization",
    description: "Tenant details, evaluation tier, RBAC team directory & provisioning",
    icon: "🏢",
  },
  {
    id: "notifications",
    title: "Notifications & Delivery",
    shortTitle: "Notifications",
    description: "Alert dispatch master switch, digest schedule, severity & quiet hours",
    icon: "🔔",
  },
  {
    id: "privacy",
    title: "Data Governance & Privacy",
    shortTitle: "Governance",
    description: "Grounded AI metering, tenant JSON export, immutability & lifecycle",
    icon: "⚖",
  },
];

export interface SettingsNavProps {
  activeSection: SettingsSectionId;
  onSelectSection: (section: SettingsSectionId) => void;
}

export function SettingsNav({ activeSection, onSelectSection }: SettingsNavProps) {
  return (
    <nav aria-label="Settings Sections" className="w-full">
      {/* Desktop / Tablet Vertical Sidebar */}
      <div className="hidden md:flex flex-col space-y-1.5 p-1 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl">
        {SETTINGS_SECTIONS.map((sec) => {
          const isActive = activeSection === sec.id;
          return (
            <button
              key={sec.id}
              type="button"
              onClick={() => onSelectSection(sec.id)}
              className={`text-left p-3 rounded-lg transition-all duration-150 flex items-start gap-3 group focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)] ${
                isActive
                  ? "bg-[var(--bg-secondary)] border-l-2 border-l-blue-600 dark:border-l-blue-400 pl-2.5 shadow-xs"
                  : "hover:bg-[var(--bg-card-hover)] border-l-2 border-l-transparent"
              }`}
              aria-current={isActive ? "page" : undefined}
            >
              <span className="text-base select-none mt-0.5" aria-hidden="true">
                {sec.icon}
              </span>
              <div className="min-w-0 flex-1">
                <span
                  className={`text-xs font-semibold block leading-tight ${
                    isActive
                      ? "text-[var(--text-primary)] font-bold"
                      : "text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]"
                  }`}
                >
                  {sec.title}
                </span>
                <span className="text-[10px] text-[var(--text-muted)] line-clamp-2 mt-0.5 leading-snug">
                  {sec.description}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Mobile Horizontal Segmented Control */}
      <div className="flex md:hidden overflow-x-auto gap-1 p-1 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl">
        {SETTINGS_SECTIONS.map((sec) => {
          const isActive = activeSection === sec.id;
          return (
            <button
              key={sec.id}
              type="button"
              onClick={() => onSelectSection(sec.id)}
              className={`px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                isActive
                  ? "bg-blue-600 text-white shadow-xs"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]"
              }`}
              aria-current={isActive ? "page" : undefined}
            >
              <span aria-hidden="true">{sec.icon}</span>
              <span>{sec.shortTitle}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

export default SettingsNav;

