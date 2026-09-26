/**
 * app/notifications/page.tsx
 * ===========================
 * Production Notification Center (Task 8.15).
 * In-app notifications feed, daily digests, and delivery status.
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { notificationsApi } from "@/lib/api/notifications";
import type {
  AlertGroupDigestResponse,
  NotificationResponse,
  NotificationSummaryResponse,
} from "@/types/api";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [digests, setDigests] = useState<AlertGroupDigestResponse[]>([]);
  const [summary, setSummary] = useState<NotificationSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab & Filter
  const [activeTab, setActiveTab] = useState<"FEED" | "DIGESTS">("FEED");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "UNREAD" | "ARCHIVED">("ALL");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const loadNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const isReadParam = statusFilter === "UNREAD" ? false : undefined;
      const isArchivedParam = statusFilter === "ARCHIVED" ? true : false;

      const [feedRes, sumRes, digRes] = await Promise.all([
        notificationsApi.listNotifications({
          page,
          limit: 20,
          is_read: isReadParam,
          is_archived: isArchivedParam,
        }),
        notificationsApi.getSummary().catch(() => null),
        notificationsApi.getDigests().catch(() => []),
      ]);

      setNotifications(feedRes.items || []);
      setTotal(feedRes.total || 0);
      setSummary(sumRes);
      setDigests(digRes || []);
    } catch (err: unknown) {
      console.error("Failed to load notifications:", err);
      setError("Unable to load notifications. Please check backend service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [page, statusFilter]);

  const handleMarkRead = async (id: string) => {
    try {
      await notificationsApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n))
      );
      if (summary) {
        setSummary({ ...summary, unread_count: Math.max(0, summary.unread_count - 1) });
      }
    } catch (err: unknown) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const handleArchive = async (id: string) => {
    try {
      await notificationsApi.archive(id);
      setNotifications((prev) => prev.filter((n) => n.notification_id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err: unknown) {
      console.error("Failed to archive notification:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      if (summary) {
        setSummary({ ...summary, unread_count: 0 });
      }
    } catch (err: unknown) {
      console.error("Failed to mark all as read:", err);
      alert("Failed to mark all notifications as read.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">📬</span>
            <span className="text-xs uppercase tracking-widest font-bold text-blue-400">
              Delivery Center
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
            Notification Center
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            In-app notification feed, digest groupings, and multi-channel delivery audit logs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {(summary?.unread_count ?? 0) > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors shadow-sm"
            >
              ✓ Mark All Read ({summary?.unread_count})
            </button>
          )}
          <Link
            href="/settings"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm"
          >
            Delivery Settings
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400 mb-1">Unread In-App</div>
          <div className="text-2xl font-bold text-amber-400">
            {loading ? "..." : summary?.unread_count ?? 0}
          </div>
          <span className="text-[11px] text-slate-500">Require attention</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400 mb-1">Total Delivered</div>
          <div className="text-2xl font-bold text-slate-100">
            {loading ? "..." : summary?.total_active ?? total}
          </div>
          <span className="text-[11px] text-slate-500">Delivered to user</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400 mb-1">Digest Bundles</div>
          <div className="text-2xl font-bold text-blue-400">
            {loading ? "..." : digests.length}
          </div>
          <span className="text-[11px] text-slate-500">Aggregated alert groups</span>
        </div>
      </div>

      {/* Tabs & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("FEED")}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === "FEED"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            In-App Feed ({total})
          </button>
          <button
            onClick={() => setActiveTab("DIGESTS")}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === "DIGESTS"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Aggregated Digests ({digests.length})
          </button>
        </div>

        {activeTab === "FEED" && (
          <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
            {(["ALL", "UNREAD", "ARCHIVED"] as const).map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st);
                  setPage(1);
                }}
                className={`px-3 py-1 font-medium rounded-md transition-colors ${
                  statusFilter === st ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="p-12 text-center text-slate-500">Loading notification stream...</div>
      )}

      {/* Feed Tab Content */}
      {!loading && activeTab === "FEED" && (
        <>
          {notifications.length === 0 ? (
            <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800 space-y-3 max-w-md mx-auto">
              <span className="text-3xl block">📬</span>
              <h3 className="text-base font-bold text-slate-100">No Notifications</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                You have no notifications matching this filter.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((n) => (
                <div
                  key={n.notification_id}
                  className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                    n.is_read
                      ? "bg-slate-900/60 border-slate-800/80 opacity-90"
                      : "bg-slate-900 border-blue-500/30 shadow-xs"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                        {n.notification_type || "IN_APP"}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(n.created_at).toLocaleString()}
                      </span>
                      {!n.is_read && (
                        <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" title="Unread" />
                      )}
                    </div>

                    <h4 className="text-sm font-semibold text-slate-100">
                      {n.title}
                    </h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {n.message}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800">
                    {!n.is_read && (
                      <button
                        onClick={() => handleMarkRead(n.notification_id)}
                        className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition-colors"
                      >
                        Mark Read
                      </button>
                    )}
                    <button
                      onClick={() => handleArchive(n.notification_id)}
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
        </>
      )}

      {/* Digests Tab Content */}
      {!loading && activeTab === "DIGESTS" && (
        <div className="space-y-4">
          {digests.length === 0 ? (
            <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800 space-y-3 max-w-md mx-auto">
              <span className="text-3xl block">🗞</span>
              <h3 className="text-base font-bold text-slate-100">No Digests Generated</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Aggregated digests are automatically created when multiple alerts occur within a configured time window.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {digests.map((dig) => (
                <div
                  key={dig.group_id}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 uppercase">
                      {dig.group_type}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(dig.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-100">
                    {dig.title}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {dig.summary}
                  </p>

                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                    <span>Bundled Events: <strong className="text-slate-200">{dig.event_count}</strong></span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      Severity: {dig.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
