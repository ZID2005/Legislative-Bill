/**
 * components/monitoring/JurisdictionBanner.tsx
 * =============================================
 * Displays the Central vs State jurisdiction separation notice
 * and the State prediction firewall statement.
 *
 * This component is non-negotiable in the monitoring center.
 * It must always be visible.
 */

import React from "react";

interface JurisdictionBannerProps {
  variant?: "full" | "compact";
  className?: string;
}

export function JurisdictionBanner({ variant = "full", className = "" }: JurisdictionBannerProps) {
  if (variant === "compact") {
    return (
      <div
        className={`rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-2 text-xs text-amber-300 ${className}`}
        role="note"
        aria-label="Jurisdiction and prediction scope notice"
      >
        <span className="font-semibold">⚖ Monitoring Notice:</span>{" "}
        Monitoring identifies source activity and changes. It does{" "}
        <strong>not</strong> constitute a market prediction.{" "}
        <span className="text-amber-400 font-semibold">
          State stock predictions remain strictly 0.
        </span>
      </div>
    );
  }

  return (
    <div
      className={`rounded-xl border border-slate-700 bg-slate-900/60 overflow-hidden ${className}`}
      role="region"
      aria-label="Jurisdiction coverage and prediction scope"
    >
      <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2">
        <span className="text-amber-400 text-lg" aria-hidden="true">⚖</span>
        <h2 className="text-sm font-semibold text-slate-200">
          Legislative Monitoring — Coverage & Scope
        </h2>
      </div>

      <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-800">
        {/* Central */}
        <div className="px-5 py-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/30 text-blue-300 text-xs font-semibold">
              🏛 Central Parliament
            </span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            Production market-analysis coverage exists for the validated Central universe.
          </p>
          <ul className="mt-2 space-y-1 text-xs text-slate-400">
            <li>• 20 production bills monitored</li>
            <li>• 47 quantitative securities covered</li>
            <li>• Quantitative market analysis available where predictions exist</li>
          </ul>
        </div>

        {/* State */}
        <div className="px-5 py-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-purple-500/15 border border-purple-500/30 text-purple-300 text-xs font-semibold">
              🗳 State Legislatures
            </span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            State legislative monitoring and economic intelligence are supported.
          </p>
          <ul className="mt-2 space-y-1 text-xs text-slate-400">
            <li>• 4 states implemented · 24 states planned</li>
            <li>• 44 state bills monitored · 86 corporate exposures</li>
            <li>
              •{" "}
              <span className="text-amber-400 font-semibold">
                State stock predictions remain strictly 0
              </span>
            </li>
          </ul>
          <p className="mt-2 text-xs text-amber-400/80 italic">
            Monitoring a State bill does not produce a market prediction.
          </p>
        </div>
      </div>

      <div className="px-5 py-3 border-t border-slate-800 bg-slate-950/40">
        <p className="text-xs text-slate-500">
          <span className="font-semibold text-slate-400">Architecture: </span>
          OFFICIAL SOURCE → MONITORING → CHANGE DETECTION → LEGISLATIVE DISCOVERY
          → KNOWLEDGE UPDATE → EXPOSURE UPDATE → OPTIONAL DOWNSTREAM ANALYSIS.
          Monitoring never automatically triggers model retraining or prediction generation.
        </p>
      </div>
    </div>
  );
}
