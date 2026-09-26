/**
 * components/ui/PlaceholderPage.tsx
 * ==================================
 * Reusable placeholder for pages not yet fully implemented.
 * Shows intended information architecture.
 */

import React from "react";
import { cn } from "@/lib/utils";

export interface PlaceholderPageProps {
  title: string;
  description: string;
  icon?: string;
  sections?: Array<{ name: string; description: string }>;
  comingSections?: string[];
  className?: string;
}

export function PlaceholderPage({
  title,
  description,
  icon = "🚧",
  sections,
  comingSections,
  className,
}: PlaceholderPageProps) {
  return (
    <div className={cn("p-6 animate-fade-in", className)}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl" aria-hidden="true">{icon}</span>
          <h1 className="text-xl font-bold text-slate-100">{title}</h1>
        </div>
        <p className="text-sm text-slate-400 max-w-2xl">{description}</p>
      </div>

      {/* Planned sections */}
      {sections && sections.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Planned Sections
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {sections.map((section) => (
              <div
                key={section.name}
                className="rounded-lg border border-slate-800 bg-slate-900 p-4 opacity-60"
              >
                <h3 className="text-sm font-semibold text-slate-300 mb-1">{section.name}</h3>
                <p className="text-xs text-slate-500">{section.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next task notice */}
      <div className="rounded-lg border border-blue-900/40 bg-blue-950/20 p-4 max-w-lg">
        <div className="flex items-start gap-2">
          <span className="text-blue-400 text-sm mt-0.5" aria-hidden="true">ℹ</span>
          <div>
            <p className="text-xs font-semibold text-blue-300 mb-1">
              Full implementation in Task 8.14.4
            </p>
            <p className="text-xs text-slate-400">
              This page foundation is established. Complete functionality including real API
              integration, advanced filters, and visualizations will be implemented in
              TASK 8.14.4 — SaaS Overview + India Legislative Explorer Implementation.
            </p>
            {comingSections && comingSections.length > 0 && (
              <ul className="mt-2 space-y-0.5">
                {comingSections.map((s) => (
                  <li key={s} className="text-xs text-slate-500 flex items-center gap-1.5">
                    <span aria-hidden="true">·</span> {s}
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
