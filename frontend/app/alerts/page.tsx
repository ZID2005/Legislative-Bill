/**
 * app/alerts/page.tsx
 * ===================
 * Production Alerts Center (Task 8.15).
 * Feed of triggered legislative alerts with filtering, bulk actions, and deep links.
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { alertsApi } from "@/lib/api/alerts";
import type { AlertEventResponse } from "@/types/api";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertEventResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "UNREAD" | "ARCHIVED">("ALL");
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>("ALL");

  const loadAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const isReadParam = statusFilter === "UNREAD" ? false : undefined;
      const isArchivedParam = statusFilter === "ARCHIVED" ? true : false;
      const sevParam = severityFilter !== "ALL" ? severityFilter : undefined;
      const entParam = entityTypeFilter !== "ALL" ? entityTypeFilter : undefined;

      const [res, countRes] = await Promise.all([
        alertsApi.listAlerts({
          page,
          limit: 20,
          severity: sevParam,
          entity_type: entParam,
          is_read: isReadParam,
          is_archived: isArchivedParam,
        }),
        alertsApi.getUnreadCount().catch(() => ({ unread_count: 0 })),
      ]);

      setAlerts(res.items || []);
      setTotal(res.total || 0);
      setUnreadCount(countRes.unread_count || 0);
    } catch (err: unknown) {
      console.error("Failed to load alerts:", err);
      setError("Unable to load alerts. Please check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [page, severityFilter, statusFilter, entityTypeFilter]);

  const handleMarkRead = async (alertId: string) => {
    try {
      await alertsApi.markAsRead(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.alert_event_id === alertId ? { ...a, is_read: true } : a))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err: unknown) {
      console.error("Failed to mark alert as read:", err);
    }
  };

  const handleArchive = async (alertId: string) => {
    try {
      await alertsApi.archive(alertId);
      setAlerts((prev) => prev.filter((a) => a.alert_event_id !== alertId));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err: unknown) {
      console.error("Failed to archive alert:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await alertsApi.markAllAsRead();
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
      setUnreadCount(0);
    } catch (err: unknown) {
      console.error("Failed to mark all as read:", err);
      alert("Failed to mark all as read.");
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case "CRITICAL":
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800">
            CRITICAL
          </span>
        );
      case "HIGH":
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
            HIGH
          </span>
        );
      case "MEDIUM":
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
            MEDIUM
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            {severity.toUpperCase()}
          </span>
        );
    }
  };

  const getDeepLink = (alert: AlertEventResponse) => {
    const eType = (alert.entity_type || "").toUpperCase();
    if (eType === "BILL" && alert.entity_id) return `/bills/${alert.entity_id}`;
    if (eType === "COMPANY" && alert.entity_id) return `/companies/${alert.entity_id}`;
    if (eType === "INDUSTRY" && alert.entity_id) return `/industries/${alert.entity_id}`;
    return "#";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">🔔</span>
            <span className="text-xs uppercase tracking-widest font-bold text-blue-400">
              Personalized Alerts Center
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
            Legislative Alerts
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Real-time change events and threshold triggers evaluated against your monitored bills, companies, and watchlists.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors shadow-sm"
            >
              ✓ Mark All As Read ({unreadCount})
            </button>
          )}
          <Link
            href="/settings"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm flex items-center gap-1.5"
          >
            <span>⚙</span>
            <span>Alert Preferences</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        {/* Status filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Status:</span>
          <div className="flex rounded-lg bg-slate-950 p-1 border border-slate-800">
            {(["ALL", "UNREAD", "ARCHIVED"] as const).map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st);
                  setPage(1);
                }}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  statusFilter === st ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* Severity filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
            <option value="INFO">Info</option>
          </select>
        </div>

        {/* Entity type filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Entity:</span>
          <select
            value={entityTypeFilter}
            onChange={(e) => {
              setEntityTypeFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Entities</option>
            <option value="BILL">Bills</option>
            <option value="COMPANY">Companies</option>
            <option value="INDUSTRY">Industries</option>
            <option value="JURISDICTION">States</option>
          </select>
        </div>

        {/* Total count badge */}
        <div className="text-xs text-slate-400">
          Showing <strong className="text-slate-200">{alerts.length}</strong> of {total} alerts
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="p-12 text-center text-slate-500">Loading alerts feed...</div>
      )}

      {/* Empty State */}
      {!loading && alerts.length === 0 && (
        <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800 space-y-3 max-w-md mx-auto">
          <span className="text-3xl block">🔔</span>
          <h3 className="text-base font-bold text-slate-100">No Alerts Found</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            No legislative alerts match your current filter settings. Any status updates or risk rating changes on your watched items will appear here.
          </p>
        </div>
      )}

      {/* Alerts Feed */}
      {!loading && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((a) => (
            <div
              key={a.alert_event_id}
              className={`p-5 rounded-xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                a.is_read
                  ? "bg-slate-900/60 border-slate-800/80 opacity-90"
                  : "bg-slate-900 border-blue-500/30 shadow-xs"
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  {getSeverityBadge(a.severity)}
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                    {a.alert_type}
                  </span>
                  {a.entity_type && (
                    <span className="text-xs font-medium text-slate-400">
                      {a.entity_type}: <strong className="text-slate-200">{a.entity_id}</strong>
                    </span>
                  )}
                  {!a.is_read && (
                    <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" title="Unread" />
                  )}
                </div>

                <h3 className="text-sm font-bold text-slate-100 hover:text-blue-400 transition-colors">
                  {getDeepLink(a) !== "#" ? (
                    <Link href={getDeepLink(a)}>{a.title}</Link>
                  ) : (
                    a.title
                  )}
                </h3>

                <p className="text-xs text-slate-400 leading-relaxed max-w-4xl">
                  {a.summary}
                </p>

                <div className="text-[11px] text-slate-500 pt-1">
                  Triggered: {new Date(a.created_at).toLocaleString()}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 flex-shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-slate-800">
                {getDeepLink(a) !== "#" && (
                  <Link
                    href={getDeepLink(a)}
                    className="px-3 py-1.5 text-xs font-semibold bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg border border-blue-500/30 transition-colors"
                  >
                    View Dossier →
                  </Link>
                )}

                {!a.is_read && (
                  <button
                    onClick={() => handleMarkRead(a.alert_event_id)}
                    title="Mark as read"
                    className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
                  >
                    Mark Read
                  </button>
                )}

                <button
                  onClick={() => handleArchive(a.alert_event_id)}
                  title="Archive alert"
                  className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-red-950 text-slate-400 hover:text-red-300 rounded-lg border border-slate-700 hover:border-red-800 transition-colors"
                >
                  Archive
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-center gap-3 pt-6">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 disabled:opacity-40"
          >
            ← Previous
          </button>
          <span className="text-xs text-slate-400">
            Page {page} of {Math.ceil(total / 20)}
          </span>
          <button
            disabled={page >= Math.ceil(total / 20)}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
