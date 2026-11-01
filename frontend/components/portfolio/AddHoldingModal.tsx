/**
 * components/portfolio/AddHoldingModal.tsx
 * ========================================
 * Accessible dialog form to add a company holding to the user's active portfolio.
 *
 * Implements:
 * - Proper form control labels and focus management
 * - Tabular numbers for price and share quantity
 * - Input validation and accessible error feedback
 */

"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import type { PortfolioHoldingItem } from "@/types/api";

export interface AddHoldingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (holding: Partial<PortfolioHoldingItem>) => Promise<void>;
}

export function AddHoldingModal({ isOpen, onClose, onSave }: AddHoldingModalProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    const form = e.currentTarget;
    const fd = new FormData(form);
    const companyName = String(fd.get("company_name") || "").trim();

    if (!companyName) {
      setError("Company Name is required.");
      return;
    }

    setSubmitting(true);
    try {
      await onSave({
        company_name: companyName,
        isin: String(fd.get("isin") || "").trim() || undefined,
        ticker: String(fd.get("ticker") || "").trim() || undefined,
        sector: String(fd.get("sector") || "").trim() || undefined,
        industry: String(fd.get("industry") || "").trim() || undefined,
        quantity: fd.get("quantity") ? Number(fd.get("quantity")) : undefined,
        avg_purchase_price: fd.get("avg_purchase_price") ? Number(fd.get("avg_purchase_price")) : undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to add holding.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Portfolio Holding"
      subtitle="Track legislative exposure for an equity, PSU, or corporate entity"
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
        {error && (
          <div className="p-2.5 rounded-md bg-rose-500/10 border border-rose-500/25 text-rose-600 dark:text-rose-400">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="company_name" className="block text-[var(--text-muted)] font-medium mb-1">
            Company Name *
          </label>
          <input
            id="company_name"
            name="company_name"
            required
            placeholder="e.g. Reliance Industries Limited"
            className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)] transition-colors"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="isin" className="block text-[var(--text-muted)] font-medium mb-1">
              ISIN (optional)
            </label>
            <input
              id="isin"
              name="isin"
              placeholder="e.g. INE002A01018"
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] font-mono placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
            />
          </div>
          <div>
            <label htmlFor="ticker" className="block text-[var(--text-muted)] font-medium mb-1">
              Ticker / Symbol (optional)
            </label>
            <input
              id="ticker"
              name="ticker"
              placeholder="e.g. RELIANCE"
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] font-mono placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="sector" className="block text-[var(--text-muted)] font-medium mb-1">
              Sector
            </label>
            <input
              id="sector"
              name="sector"
              placeholder="e.g. Energy"
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
            />
          </div>
          <div>
            <label htmlFor="industry" className="block text-[var(--text-muted)] font-medium mb-1">
              Industry
            </label>
            <input
              id="industry"
              name="industry"
              placeholder="e.g. Oil & Gas"
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="quantity" className="block text-[var(--text-muted)] font-medium mb-1">
              Shares Quantity
            </label>
            <input
              id="quantity"
              name="quantity"
              type="number"
              min="0"
              placeholder="e.g. 50"
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] font-tabular placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
            />
          </div>
          <div>
            <label htmlFor="avg_purchase_price" className="block text-[var(--text-muted)] font-medium mb-1">
              Average Price (₹)
            </label>
            <input
              id="avg_purchase_price"
              name="avg_purchase_price"
              type="number"
              step="0.01"
              min="0"
              placeholder="e.g. 2650.00"
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-primary)] font-tabular placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
            />
          </div>
        </div>

        <div className="pt-3 flex items-center justify-end gap-2 border-t border-[var(--border-hairline)]">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-xs text-[var(--text-secondary)] border border-[var(--border-default)] transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white transition-colors shadow-xs"
          >
            {submitting ? "Saving…" : "Save Holding"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default AddHoldingModal;

