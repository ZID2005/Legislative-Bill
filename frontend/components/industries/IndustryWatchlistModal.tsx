/**
 * components/industries/IndustryWatchlistModal.tsx
 * ================================================
 * Modal dialog for subscribing an Industry entity to a user watchlist.
 * Uses existing FastAPI `/api/v1/watchlists` endpoints.
 * Supports selecting an existing watchlist or creating a new one inline.
 */

"use client";

import React, { useEffect, useState } from "react";
import type { WatchlistResponse } from "@/types/api";
import { watchlistsApi } from "@/lib/api/watchlists";

export interface IndustryWatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  industry: {
    industry_id: string;
    name: string;
    sector: string;
  };
}

export function IndustryWatchlistModal({
  isOpen,
  onClose,
  industry,
}: IndustryWatchlistModalProps) {
  const [watchlists, setWatchlists] = useState<WatchlistResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedId, setSelectedId] = useState<string>("");
  const [notes, setNotes] = useState("");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Inline creation
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newWlName, setNewWlName] = useState("");
  const [newWlDesc, setNewWlDesc] = useState("");

  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;
    async function loadWatchlists() {
      setLoading(true);
      setErrorMsg(null);
      setSuccessMsg(null);
      try {
        const list = await watchlistsApi.listWatchlists();
        if (!cancelled) {
          setWatchlists(list);
          if (list.length > 0) {
            setSelectedId(list[0].watchlist_id);
          } else {
            setIsCreatingNew(true);
          }
        }
      } catch {
        if (!cancelled) {
          setErrorMsg("Failed to load your watchlists. Please try again.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadWatchlists();
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setSubmitting(true);

    try {
      let targetId = selectedId;

      if (isCreatingNew) {
        if (!newWlName.trim()) {
          setErrorMsg("Please enter a watchlist name.");
          setSubmitting(false);
          return;
        }
        const created = await watchlistsApi.createWatchlist({
          name: newWlName.trim(),
          description: newWlDesc.trim() || undefined,
        });
        targetId = created.watchlist_id;
      }

      if (!targetId) {
        setErrorMsg("Please select or create a watchlist.");
        setSubmitting(false);
        return;
      }

      await watchlistsApi.addItem(targetId, {
        entity_type: "INDUSTRY",
        entity_id: industry.industry_id,
        display_name: industry.name,
        notes: notes.trim() || undefined,
      });

      setSuccessMsg(`Successfully added '${industry.name}' to watchlist.`);
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err: unknown) {
      console.error("Failed to add industry to watchlist:", err);
      setErrorMsg("Failed to add to watchlist. It may already be in this watchlist.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-xs">
      <div
        className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="industry-watchlist-modal-title"
      >
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <span className="text-amber-400">⭐</span>
            <h3 id="industry-watchlist-modal-title" className="text-base font-semibold text-slate-100">
              Add Industry to Watchlist
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-sm p-1"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Industry Preview */}
        <div className="mb-4 rounded-lg bg-slate-950 border border-slate-800 p-3 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
              INDUSTRY
            </span>
            <span className="text-xs font-semibold text-slate-200">{industry.name}</span>
          </div>
          <p className="text-xs text-slate-400">
            Sector: <strong className="text-slate-300">{industry.sector}</strong>
          </p>
        </div>

        {errorMsg && (
          <div className="mb-4 rounded-lg bg-red-950/50 border border-red-800 p-3 text-xs text-red-200">
            {errorMsg}
          </div>
        )}

        {successMsg && (
          <div className="mb-4 rounded-lg bg-emerald-950/50 border border-emerald-800 p-3 text-xs text-emerald-200">
            ✓ {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {loading ? (
            <div className="py-4 text-center text-xs text-slate-500">
              Loading watchlists...
            </div>
          ) : (
            <>
              {/* Watchlist Select vs Create */}
              {!isCreatingNew ? (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-medium text-slate-300">
                      Choose Watchlist
                    </label>
                    <button
                      type="button"
                      onClick={() => setIsCreatingNew(true)}
                      className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                    >
                      + New Watchlist
                    </button>
                  </div>
                  <select
                    value={selectedId}
                    onChange={(e) => setSelectedId(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                  >
                    {watchlists.map((wl) => (
                      <option key={wl.watchlist_id} value={wl.watchlist_id}>
                        {wl.name} ({wl.items?.length ?? 0} items)
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-slate-300">
                      Create New Watchlist
                    </label>
                    {watchlists.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setIsCreatingNew(false)}
                        className="text-xs text-slate-400 hover:text-slate-200"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    required
                    value={newWlName}
                    onChange={(e) => setNewWlName(e.target.value)}
                    placeholder="Watchlist Name (e.g. Cleantech & Energy)"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                  <input
                    type="text"
                    value={newWlDesc}
                    onChange={(e) => setNewWlDesc(e.target.value)}
                    placeholder="Description (Optional)"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              {/* Internal notes */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Monitoring Note (Optional)
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Critical focus for upcoming budget session"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>
            </>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || submitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm"
            >
              {submitting ? "Saving..." : "Add to Watchlist"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default IndustryWatchlistModal;
