/**
 * components/ui/PlaceholderPage.tsx
 * ==================================
 * Institutional placeholder for upcoming sections and modules.
 * Dual-theme token synchronized with accessible typography.
 */

import React from "react";
import { cn } from "@/lib/utils";
import { InfoIcon } from "./Icons";

export interface PlaceholderPageProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  sections?: Array<{ name: string; description: string }>;
  comingSections?: string[];
  className?: string;
}

export function PlaceholderPage({
  title,
  description,
  icon,
  sections,
  comingSections,
  className,
}: PlaceholderPageProps) {
  return (
    <div className={cn("p-6", className)}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          {icon ? (
            <span className="text-xl inline-flex items-center text-[var(--text-muted)]" aria-hidden="true">
              {icon}
            </span>
          ) : (
            <span className="text-xl inline-flex items-center text-[var(--text-muted)]" aria-hidden="true">
              <InfoIcon size="lg" />
            </span>
          )}
          <h1 className="text-xl font-bold tracking-tight text-[var(--text-primary)]">{title}</h1>
        </div>
        <p className="text-sm text-[var(--text-muted)] max-w-2xl leading-relaxed">{description}</p>
      </div>

      {/* Planned sections */}
      {sections && sections.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">
            Planned Information Architecture
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {sections.map((section) => (
              <div
                key={section.name}
                className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-card)] p-4 shadow-xs"
              >
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">{section.name}</h3>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">{section.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next task notice */}
      <div className="rounded-xl border border-[var(--action-primary)]/25 bg-[var(--action-primary)]/8 p-4 max-w-lg">
        <div className="flex items-start gap-3">
          <span className="text-[var(--action-primary)] mt-0.5" aria-hidden="true">
            <InfoIcon size="sm" />
          </span>
          <div>
            <p className="text-xs font-semibold text-[var(--text-primary)] mb-1">
              Architecture &amp; Foundation Established
            </p>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              This page foundation is established within Seance navigation and security guardrails.
              Full interactive visualizations, live datasets, and detailed filtering modules are scheduled.
            </p>
            {comingSections && comingSections.length > 0 && (
              <ul className="mt-2.5 space-y-1">
                {comingSections.map((s) => (
                  <li key={s} className="text-xs text-[var(--text-muted)] flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-[var(--action-primary)]" aria-hidden="true" />
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlaceholderPage;
