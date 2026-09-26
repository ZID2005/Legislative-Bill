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
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⭐</span>
            <span className="text-xs uppercase tracking-widest font-bold text-amber-400">
              Workspace Portfolios
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
            Entity Watchlists
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
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
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="p-12 text-center text-slate-500">
          Loading your active watchlists...
        </div>
      )}

      {/* Empty State */}
      {!loading && watchlists.length === 0 && (
        <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800 space-y-4 max-w-lg mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-3xl flex items-center justify-center mx-auto">
            ⭐
          </div>
          <h3 className="text-lg font-semibold text-slate-100">No Watchlists Yet</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Create your first watchlist to monitor bills affecting your company portfolios and subscribe to automated legislative alerts.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
          >
            Create Your First Watchlist
          </button>
        </div>
      )}

      {/* Watchlist Cards Grid */}
      {!loading && watchlists.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {watchlists.map((wl) => (
            <div
              key={wl.watchlist_id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition-colors shadow-sm space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                    wl.is_active ? "bg-emerald-950 text-emerald-300 border border-emerald-800" : "bg-slate-800 text-slate-400"
                  }`}>
                    {wl.is_active ? "Active" : "Archived"}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    Created {new Date(wl.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-100 hover:text-blue-400 transition-colors">
                  <Link href={`/watchlists/${wl.watchlist_id}`}>{wl.name}</Link>
                </h3>
                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {wl.description || "No description provided."}
                </p>
              </div>

              <div className="space-y-3 pt-3 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Monitored Items</span>
                  <span className="font-semibold text-slate-200">
                    {wl.items?.length ?? wl.items_count ?? 0} items
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Alert Rules</span>
                  <span className="font-semibold text-slate-200">
                    {wl.rules?.length ?? wl.alert_rules?.length ?? 0} rules
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <Link
                    href={`/watchlists/${wl.watchlist_id}`}
                    className="flex-1 text-center px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 text-xs font-semibold rounded-lg border border-blue-500/30 transition-colors"
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
                    className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 transition-colors"
                  >
                    ✎
                  </button>
                  <button
                    onClick={() => handleDelete(wl.watchlist_id, wl.name)}
                    title="Delete Watchlist"
                    className="p-2 bg-slate-800 hover:bg-red-950 text-slate-400 hover:text-red-300 text-xs rounded-lg border border-slate-700 hover:border-red-800 transition-colors"
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
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100">Create New Watchlist</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Watchlist Name *
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Energy & Critical Minerals Portfolio"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Focus areas, rationale, or legislative tracking notes..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !newName.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm"
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
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100">Edit Watchlist</h3>
              <button
                onClick={() => setEditingWl(null)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Watchlist Name *
                </label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingWl(null)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !editName.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm"
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
