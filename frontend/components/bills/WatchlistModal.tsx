/**
 * components/bills/WatchlistModal.tsx
 * ===================================
 * Modal dialog for subscribing a bill to a user watchlist.
 * Uses existing FastAPI `/api/v1/watchlists` endpoints.
 * Supports choosing an existing watchlist or creating a new one inline.
 */

"use client";

import React, { useEffect, useState } from "react";
import type { BillSummaryItem, WatchlistResponse } from "@/types/api";
import { watchlistsApi } from "@/lib/api/watchlists";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export interface WatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  bill: BillSummaryItem;
}

export function WatchlistModal({ isOpen, onClose, bill }: WatchlistModalProps) {
  const [watchlists, setWatchlists] = useState<WatchlistResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedId, setSelectedId] = useState<string>("");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Inline creation state
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
      } catch (err: any) {
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

  const handleAddToWatchlist = async () => {
    setErrorMsg(null);
    setSubmitting(true);
    try {
      let targetId = selectedId;

      // If user wants to create a new watchlist first
      if (isCreatingNew) {
        if (!newWlName.trim()) {
          setErrorMsg("Please enter a name for the new watchlist.");
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
        entity_type: "bill",
        entity_id: bill.bill_id,
        display_name: bill.short_title || bill.title,
      });

      setSuccessMsg("Bill successfully subscribed to watchlist!");
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to add bill to watchlist.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="watchlist-modal-title"
    >
      <div className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-5 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-base" aria-hidden="true">⭐</span>
            <h3 id="watchlist-modal-title" className="text-sm font-bold text-slate-100">
              Add to Watchlist
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Bill Snapshot */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 space-y-1">
          <p className="text-xs font-semibold text-slate-200 line-clamp-2">
            {bill.title}
          </p>
          <div className="flex items-center gap-2 text-[10px] text-slate-500">
            <span>{bill.jurisdiction === "central" ? "Central Parliament" : bill.state}</span>
            <span>·</span>
            <span>{bill.status}</span>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="py-8 text-center text-xs text-slate-400 space-y-2">
            <div className="h-4 w-32 bg-slate-800 rounded mx-auto animate-pulse" />
            <p>Loading your watchlists...</p>
          </div>
        ) : successMsg ? (
          <div className="py-6 text-center space-y-2">
            <span className="text-3xl text-emerald-400 block animate-bounce" aria-hidden="true">
              ✓
            </span>
            <p className="text-xs font-semibold text-emerald-300">{successMsg}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Watchlist Options */}
            {!isCreatingNew && watchlists.length > 0 ? (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 block">
                  Select Target Watchlist:
                </label>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {watchlists.map((wl) => (
                    <label
                      key={wl.watchlist_id}
                      className={`flex items-center justify-between p-2.5 rounded-lg border cursor-pointer transition-colors ${
                        selectedId === wl.watchlist_id
                          ? "border-blue-500 bg-blue-950/30 text-slate-100"
                          : "border-slate-800 bg-slate-950/40 text-slate-400 hover:bg-slate-800/40"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="watchlist_select"
                          value={wl.watchlist_id}
                          checked={selectedId === wl.watchlist_id}
                          onChange={() => setSelectedId(wl.watchlist_id)}
                          className="text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-xs font-medium">{wl.name}</span>
                        {wl.is_default && (
                          <Badge variant="primary" size="xs">
                            Default
                          </Badge>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {wl.items_count} items
                      </span>
                    </label>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => setIsCreatingNew(true)}
                  className="text-xs text-blue-400 hover:text-blue-300 font-medium pt-1"
                >
                  + Create a new watchlist
                </button>
              </div>
            ) : (
              /* Create New Watchlist Form */
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-300">
                    Create New Watchlist
                  </label>
                  {watchlists.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setIsCreatingNew(false)}
                      className="text-xs text-blue-400 hover:text-blue-300"
                    >
                      Choose existing
                    </button>
                  )}
                </div>

                <div className="space-y-1.5">
                  <input
                    type="text"
                    placeholder="Watchlist Name (e.g. Banking & Shipping Bills)"
                    value={newWlName}
                    onChange={(e) => setNewWlName(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                  />
                  <input
                    type="text"
                    placeholder="Description (optional)"
                    value={newWlDesc}
                    onChange={(e) => setNewWlDesc(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            )}

            {errorMsg && (
              <p className="text-xs text-rose-400 leading-snug">{errorMsg}</p>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleAddToWatchlist}
                disabled={submitting}
                id="btn-confirm-add-watchlist"
              >
                {submitting ? "Adding..." : "Add Bill"}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default WatchlistModal;
