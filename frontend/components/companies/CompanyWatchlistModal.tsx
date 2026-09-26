/**
 * components/companies/CompanyWatchlistModal.tsx
 * ===============================================
 * Modal dialog for subscribing a corporate entity to a user watchlist.
 * Uses existing FastAPI `/api/v1/watchlists` endpoints.
 * Supports selecting an existing watchlist or creating a new one inline.
 */

"use client";

import React, { useEffect, useState } from "react";
import type { CompanyDetailResponse, WatchlistResponse } from "@/types/api";
import { watchlistsApi } from "@/lib/api/watchlists";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export interface CompanyWatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  company: CompanyDetailResponse;
}

export function CompanyWatchlistModal({
  isOpen,
  onClose,
  company,
}: CompanyWatchlistModalProps) {
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

  const handleSubscribe = async () => {
    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      let targetWatchlistId = selectedId;

      // 1. Create new watchlist if requested
      if (isCreatingNew) {
        if (!newWlName.trim()) {
          setErrorMsg("Please provide a name for the new watchlist.");
          setSubmitting(false);
          return;
        }
        const created = await watchlistsApi.createWatchlist({
          name: newWlName.trim(),
          description: newWlDesc.trim() || undefined,
        });
        targetWatchlistId = created.watchlist_id;
      }

      if (!targetWatchlistId) {
        setErrorMsg("Please select or create a watchlist.");
        setSubmitting(false);
        return;
      }

      // 2. Add company to watchlist
      await watchlistsApi.addItem(targetWatchlistId, {
        entity_type: "company",
        entity_id: company.isin || company.company_id,
        display_name: company.company_name,
        notes: `Subscribed from Corporate Profile. Sector: ${company.sector || "General"}`,
      });

      setSuccessMsg(`Successfully added ${company.company_name} to your watchlist!`);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch {
      setErrorMsg("Failed to add company to watchlist. It may already be subscribed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="watchlist-modal-title"
    >
      <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 id="watchlist-modal-title" className="text-base font-semibold text-slate-100">
              Add Company to Watchlist
            </h3>
            <p className="text-xs text-slate-400 mt-0.5 font-medium truncate max-w-xs">
              {company.company_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-base p-1"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Company Identity Ribbon */}
        <div className="rounded-lg bg-slate-800/40 p-3 border border-slate-800 flex items-center justify-between text-xs">
          <div>
            <span className="font-semibold text-slate-200 block">{company.company_name}</span>
            <span className="text-slate-400 text-[11px] block mt-0.5">
              ISIN: {company.isin || "—"} · Sector: {company.sector || "General"}
            </span>
          </div>
          <Badge variant={company.is_quant_eligible ? "success" : "info"} size="xs">
            {company.is_quant_eligible ? "Quantitative" : "Intelligence"}
          </Badge>
        </div>

        {/* Feedback Messages */}
        {successMsg && (
          <div className="rounded-lg border border-emerald-800/60 bg-emerald-950/40 p-3 text-xs text-emerald-300 font-medium animate-fade-in">
            ✓ {successMsg}
          </div>
        )}

        {errorMsg && (
          <div className="rounded-lg border border-rose-800/60 bg-rose-950/40 p-3 text-xs text-rose-300 font-medium animate-fade-in">
            ⚠ {errorMsg}
          </div>
        )}

        {loading ? (
          <div className="py-6 text-center text-xs text-slate-400 space-y-2">
            <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-blue-500 border-r-transparent" />
            <p>Loading your watchlists...</p>
          </div>
        ) : (
          <div className="space-y-4 text-xs">
            {/* Toggle Existing vs New Watchlist */}
            <div className="flex items-center justify-between">
              <span className="text-slate-300 font-medium">Target Watchlist:</span>
              {watchlists.length > 0 && (
                <button
                  type="button"
                  onClick={() => setIsCreatingNew(!isCreatingNew)}
                  className="text-xs text-blue-400 hover:text-blue-300 underline"
                >
                  {isCreatingNew ? "Select existing watchlist" : "+ Create new watchlist"}
                </button>
              )}
            </div>

            {/* Select Existing Watchlist */}
            {!isCreatingNew && watchlists.length > 0 && (
              <div className="space-y-1.5">
                <select
                  value={selectedId}
                  onChange={(e) => setSelectedId(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
                  aria-label="Select watchlist"
                >
                  {watchlists.map((wl) => (
                    <option key={wl.watchlist_id} value={wl.watchlist_id}>
                      {wl.name} ({wl.items_count || wl.items?.length || 0} items)
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Create New Watchlist Inline */}
            {isCreatingNew && (
              <div className="space-y-2.5 rounded-lg border border-slate-800 bg-slate-800/20 p-3">
                <div>
                  <label htmlFor="new-wl-name" className="block text-[11px] text-slate-400 mb-1">
                    Watchlist Name *
                  </label>
                  <input
                    id="new-wl-name"
                    type="text"
                    placeholder="e.g., Heavy Industries Portfolio"
                    value={newWlName}
                    onChange={(e) => setNewWlName(e.target.value)}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="new-wl-desc" className="block text-[11px] text-slate-400 mb-1">
                    Description (optional)
                  </label>
                  <input
                    id="new-wl-desc"
                    type="text"
                    placeholder="e.g., Tracking legislative exposure across manufacturing"
                    value={newWlDesc}
                    onChange={(e) => setNewWlDesc(e.target.value)}
                    className="w-full rounded border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                disabled={submitting}
                className="text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSubscribe}
                disabled={submitting || (isCreatingNew && !newWlName.trim())}
                className="text-xs font-semibold"
              >
                {submitting ? "Subscribing..." : "Confirm Subscription"}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CompanyWatchlistModal;
