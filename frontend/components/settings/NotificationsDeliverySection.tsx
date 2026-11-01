/**
 * components/settings/NotificationsDeliverySection.tsx
 * ====================================================
 * Section 3: Legislative Notification & Alert Delivery Preferences.
 *
 * Implements:
 * - Master alert subsystem toggle switch
 * - Digest frequency scheduler (Real-time, Daily, Weekly)
 * - Minimum severity threshold selector (Low, Medium, High, Critical)
 * - Quiet hours scheduler with start and end time inputs
 * - Accessible form submission and asynchronous status feedback
 */

"use client";

import React from "react";

export interface NotificationsDeliverySectionProps {
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
  minimumSeverity: string;
  setMinimumSeverity: (sev: string) => void;
  digestFrequency: string;
  setDigestFrequency: (freq: string) => void;
  quietHoursEnabled: boolean;
  setQuietHoursEnabled: (enabled: boolean) => void;
  quietHoursStart: string;
  setQuietHoursStart: (time: string) => void;
  quietHoursEnd: string;
  setQuietHoursEnd: (time: string) => void;
  alertsSaving: boolean;
  alertsSuccess: boolean;
  onSaveAlerts: (e: React.FormEvent) => void;
}

export function NotificationsDeliverySection({
  enabled,
  setEnabled,
  minimumSeverity,
  setMinimumSeverity,
  digestFrequency,
  setDigestFrequency,
  quietHoursEnabled,
  setQuietHoursEnabled,
  quietHoursStart,
  setQuietHoursStart,
  quietHoursEnd,
  setQuietHoursEnd,
  alertsSaving,
  alertsSuccess,
  onSaveAlerts,
}: NotificationsDeliverySectionProps) {
  return (
    <section className="space-y-6" aria-labelledby="notifications-delivery-heading">
      {/* Section Header */}
      <div className="pb-3 border-b border-[var(--border-default)]">
        <h2 id="notifications-delivery-heading" className="text-base font-bold text-[var(--text-primary)] font-headline">
          Notifications &amp; Delivery Preferences
        </h2>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">
          Configure real-time legislative dispatch triggers, digest frequencies, and quiet periods.
        </p>
      </div>

      <form onSubmit={onSaveAlerts} className="space-y-6">
        {alertsSuccess && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-xs text-emerald-700 dark:text-emerald-400 font-semibold flex items-center gap-2">
            <span aria-hidden="true">✓</span> Alert &amp; notification preferences successfully synchronized with backend.
          </div>
        )}

        {/* Master Alert Switch */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 flex items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-[var(--text-primary)]">
              Enable Legislative Alert Subsystem
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Master control for all automated event dispatches affecting watched bills and portfolio holdings.
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="sr-only peer"
              aria-label="Toggle alert subsystem"
            />
            <div className="w-11 h-6 bg-[var(--bg-secondary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--focus-ring)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 border border-[var(--border-strong)]"></div>
          </label>
        </div>

        {/* Delivery Schedule & Thresholds Card */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline pb-3 border-b border-[var(--border-hairline)]">
            Delivery Schedule &amp; Severity Thresholds
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="digestFrequency" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                Digest Frequency
              </label>
              <select
                id="digestFrequency"
                value={digestFrequency}
                onChange={(e) => setDigestFrequency(e.target.value)}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] font-medium focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
              >
                <option value="REALTIME">Real-time (Instant Notification)</option>
                <option value="DAILY">Daily Digest Briefing</option>
                <option value="WEEKLY">Weekly Executive Summary</option>
              </select>
              <span className="text-[10px] text-[var(--text-muted)] block mt-1">
                Determines how frequently batch digests are compiled and presented.
              </span>
            </div>

            <div>
              <label htmlFor="minimumSeverity" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                Minimum Severity Threshold
              </label>
              <select
                id="minimumSeverity"
                value={minimumSeverity}
                onChange={(e) => setMinimumSeverity(e.target.value)}
                className="w-full bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] font-medium focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
              >
                <option value="LOW">Low (All gazette notices &amp; introductions)</option>
                <option value="MEDIUM">Medium (Committee hearings &amp; statutory revisions)</option>
                <option value="HIGH">High (Floor passage &amp; presidential assent)</option>
                <option value="CRITICAL">Critical (Major market-moving regulatory shocks)</option>
              </select>
              <span className="text-[10px] text-[var(--text-muted)] block mt-1">
                Events below this severity will not trigger high-priority alerts.
              </span>
            </div>
          </div>
        </div>

        {/* Quiet Hours Card */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border-hairline)]">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
                Quiet Hours Scheduler
              </h3>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                Suppress non-critical dispatches during specified institutional quiet windows.
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={quietHoursEnabled}
                onChange={(e) => setQuietHoursEnabled(e.target.checked)}
                className="sr-only peer"
                aria-label="Toggle quiet hours"
              />
              <div className="w-11 h-6 bg-[var(--bg-secondary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--focus-ring)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 border border-[var(--border-strong)]"></div>
            </label>
          </div>

          {quietHoursEnabled && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div>
                <label htmlFor="quietHoursStart" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                  Quiet Window Start (IST)
                </label>
                <input
                  id="quietHoursStart"
                  type="time"
                  value={quietHoursStart}
                  onChange={(e) => setQuietHoursStart(e.target.value)}
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] font-mono font-tabular focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
                />
              </div>

              <div>
                <label htmlFor="quietHoursEnd" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                  Quiet Window End (IST)
                </label>
                <input
                  id="quietHoursEnd"
                  type="time"
                  value={quietHoursEnd}
                  onChange={(e) => setQuietHoursEnd(e.target.value)}
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] font-mono font-tabular focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
                />
              </div>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div>
          <button
            type="submit"
            disabled={alertsSaving}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-xs font-semibold text-white transition-colors shadow-xs"
          >
            {alertsSaving ? "Saving Preferences…" : "Save Notification Preferences"}
          </button>
        </div>
      </form>
    </section>
  );
}

export default NotificationsDeliverySection;

