/**
 * app/watchlists/page.tsx
 * =======================
 * Production Watchlist Management Page (Task 8.15).
 * List, create, edit, deactivate, and view multi-dimensional watchlists.
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { watchlistsApi } from "@/lib/api/watchlists";
import type { WatchlistResponse } from "@/types/api";
import { ErrorState, SkeletonCard } from "@/components/ui/Skeleton";

export default function WatchlistsPage() {
  const [watchlists, setWatchlists] = useState<WatchlistResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Edit Modal State
  const [editingWl, setEditingWl] = useState<WatchlistResponse | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const loadWatchlists = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await watchlistsApi.listWatchlists();
      setWatchlists(data);
    } catch (err: unknown) {
      console.error("Failed to load watchlists:", err);
      setError("Unable to load watchlists. Please verify backend service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWatchlists();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    setSubmitting(true);
    try {
      await watchlistsApi.createWatchlist({
        name: newName.trim(),
        description: newDesc.trim() || undefined,
      });
      setNewName("");
      setNewDesc("");
      setShowCreateModal(false);
      await loadWatchlists();
    } catch (err: unknown) {
      console.error("Failed to create watchlist:", err);
      alert("Failed to create watchlist. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingWl || !editName.trim()) return;

    setSubmitting(true);
    try {
      await watchlistsApi.updateWatchlist(editingWl.watchlist_id, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
      });
      setEditingWl(null);
      await loadWatchlists();
    } catch (err: unknown) {
      console.error("Failed to update watchlist:", err);
      alert("Failed to update watchlist.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (watchlistId: string, name: string) => {
    if (!confirm(`Are you sure you want to deactivate and remove '${name}'?`)) return;

    try {
      await watchlistsApi.deleteWatchlist(watchlistId);
      await loadWatchlists();
    } catch (err: unknown) {
      console.error("Failed to delete watchlist:", err);
      alert("Failed to delete watchlist.");
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] p-6 sm:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border-default)] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⭐</span>
            <span className="text-xs uppercase tracking-widest font-bold text-amber-500 dark:text-amber-400">
              Workspace Portfolios
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            Entity Watchlists
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-1 max-w-2xl">
            Group legislative bills, public companies, sectors, and states into custom watchlists with attached alert trigger rules.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 shadow-sm"
        >
          <span>+</span>
          <span>Create Watchlist</span>
        </button>
      </div>

      {error && (
        <ErrorState error={error} onRetry={loadWatchlists} />
      )}

      {/* Loading state */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {/* Empty State */}
      {!loading && watchlists.length === 0 && (
        <div
          data-testid="empty-watchlists-state"
          className="p-10 sm:p-12 text-center bg-[var(--bg-card)]/50 rounded-2xl border border-[var(--border-default)] space-y-4 max-w-xl mx-auto shadow-sm"
        >
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-500 dark:text-amber-400 text-3xl flex items-center justify-center mx-auto" aria-hidden="true">
            ⭐
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--text-primary)]">No Watchlists Yet</h3>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1 max-w-md mx-auto leading-relaxed">
              Watchlists let you curate custom tracking sets of parliamentary bills, state gazettes, corporate entities, and sectors. Receive automated epistemic alerts and change-feed updates as regulatory events progress.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-2.5 pt-2">
            <button
              onClick={() => setShowCreateModal(true)}
              data-testid="create-first-watchlist-btn"
              className="w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs sm:text-sm font-semibold rounded-lg transition-colors shadow-sm"
            >
              Create Your First Watchlist
            </button>
            <Link
              href="/bills"
              className="w-full sm:w-auto px-4 py-2.5 bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs sm:text-sm font-semibold rounded-lg border border-[var(--border-default)] transition-colors"
            >
              Browse Legislative Bills →
            </Link>
            <Link
              href="/companies"
              className="w-full sm:w-auto px-4 py-2.5 bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs sm:text-sm font-semibold rounded-lg border border-[var(--border-default)] transition-colors"
            >
              Explore Companies →
            </Link>
          </div>
        </div>
      )}

      {/* Watchlist Cards Grid */}
      {!loading && watchlists.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {watchlists.map((wl) => (
            <div
              key={wl.watchlist_id}
              className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 flex flex-col justify-between hover:border-[var(--border-strong)] transition-colors shadow-sm space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                    wl.is_active ? "bg-[var(--color-success-bg)] text-[var(--color-success-text)] border border-[var(--color-success-border)]" : "bg-[var(--bg-elevated)] text-[var(--text-muted)]"
                  }`}>
                    {wl.is_active ? "Active" : "Archived"}
                  </span>
                  <span className="text-[11px] text-[var(--text-faint)]">
                    Created {new Date(wl.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="text-base font-bold text-[var(--text-primary)] hover:text-blue-400 transition-colors">
                  <Link href={`/watchlists/${wl.watchlist_id}`}>{wl.name}</Link>
                </h3>
                <p className="text-xs text-[var(--text-muted)] line-clamp-2 leading-relaxed">
                  {wl.description || "No description provided."}
                </p>
              </div>

              <div className="space-y-3 pt-3 border-t border-[var(--border-default)]/80">
                <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                  <span>Monitored Items</span>
                  <span className="font-semibold text-[var(--text-primary)]">
                    {wl.items?.length ?? wl.items_count ?? 0} items
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                  <span>Alert Rules</span>
                  <span className="font-semibold text-[var(--text-primary)]">
                    {wl.rules?.length ?? wl.alert_rules?.length ?? 0} rules
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <Link
                    href={`/watchlists/${wl.watchlist_id}`}
                    className="flex-1 text-center px-3 py-2 bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 text-xs font-semibold rounded-lg border border-blue-500/30 transition-colors"
                  >
                    Open Workspace →
                  </Link>
                  <button
                    onClick={() => {
                      setEditingWl(wl);
                      setEditName(wl.name);
                      setEditDesc(wl.description || "");
                    }}
                    title="Edit Name & Description"
                    className="p-2 bg-[var(--bg-elevated)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] text-xs rounded-lg border border-[var(--border-strong)] transition-colors"
                  >
                    ✎
                  </button>
                  <button
                    onClick={() => handleDelete(wl.watchlist_id, wl.name)}
                    title="Delete Watchlist"
                    className="p-2 bg-[var(--bg-elevated)] hover:bg-red-950 text-[var(--text-muted)] hover:text-red-300 text-xs rounded-lg border border-[var(--border-strong)] hover:border-red-800 transition-colors"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
              <h3 className="text-base font-bold text-[var(--text-primary)]">Create New Watchlist</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Watchlist Name *
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Energy & Critical Minerals Portfolio"
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Focus areas, rationale, or legislative tracking notes..."
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !newName.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  {submitting ? "Creating..." : "Create Watchlist"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingWl && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
              <h3 className="text-base font-bold text-[var(--text-primary)]">Edit Watchlist</h3>
              <button
                onClick={() => setEditingWl(null)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Watchlist Name *
                </label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingWl(null)}
                  className="px-4 py-2 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !editName.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  {submitting ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
