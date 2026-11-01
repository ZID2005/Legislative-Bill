/**
 * components/portfolio/ImportHoldingsModal.tsx
 * ============================================
 * Accessible dialog to import holdings via CSV or JSON format.
 *
 * Implements:
 * - CSV and JSON file drag/drop and selection
 * - Client-side validation of holdings schema
 * - Informative schema expectations and error handling
 */

"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";

export interface ImportHoldingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (holdings: any[]) => Promise<void>;
}

export function ImportHoldingsModal({ isOpen, onClose, onImport }: ImportHoldingsModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setLoading(true);

    try {
      const text = await file.text();
      let holdingsToImport: any[] = [];

      if (file.name.endsWith(".json")) {
        const parsed = JSON.parse(text);
        holdingsToImport = Array.isArray(parsed) ? parsed : [parsed];
      } else {
        // CSV parsing
        const lines = text.split("\n").filter((l) => l.trim().length > 0);
        if (lines.length < 2) {
          throw new Error("CSV file must contain a header row and at least one data row.");
        }

        const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());
        for (let i = 1; i < lines.length; i++) {
          const vals = lines[i].split(",").map((v) => v.trim());
          const item: Record<string, any> = {};
          headers.forEach((h, idx) => {
            item[h] = vals[idx] !== undefined ? vals[idx] : "";
          });

          const companyName = item.company_name || item.company || item.name;
          if (companyName) {
            holdingsToImport.push({
              company_name: companyName,
              isin: item.isin || undefined,
              ticker: item.ticker || undefined,
              sector: item.sector || undefined,
              industry: item.industry || undefined,
              quantity: item.quantity ? Number(item.quantity) : undefined,
              avg_purchase_price: item.avg_purchase_price ? Number(item.avg_purchase_price) : undefined,
            });
          }
        }
      }

      if (holdingsToImport.length === 0) {
        throw new Error("No valid holdings with company names found in the selected file.");
      }

      await onImport(holdingsToImport);
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to parse file format. Ensure valid CSV or JSON schema.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Import Portfolio Holdings"
      subtitle="Upload CSV or JSON file containing your asset roster"
      maxWidth="md"
    >
      <div className="space-y-4 text-xs">
        {error && (
          <div className="p-2.5 rounded-md bg-rose-500/10 border border-rose-500/25 text-rose-600 dark:text-rose-400">
            {error}
          </div>
        )}

        <div className="p-6 border-2 border-dashed border-[var(--border-default)] rounded-xl text-center space-y-2 hover:border-[var(--border-strong)] transition-colors bg-[var(--bg-secondary)]/40">
          <span className="text-3xl block" aria-hidden="true">📂</span>
          <p className="text-xs font-semibold text-[var(--text-primary)]">
            Select a CSV or JSON file to upload
          </p>
          <p className="text-[11px] text-[var(--text-muted)] max-w-xs mx-auto">
            Expected headers: <code className="font-mono text-[var(--text-secondary)]">company_name, isin, ticker, sector, industry, quantity, avg_purchase_price</code>
          </p>
          <div className="pt-2">
            <input
              type="file"
              accept=".csv,.json"
              disabled={loading}
              onChange={handleFileChange}
              className="text-xs text-[var(--text-muted)] file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer"
            />
          </div>
        </div>

        {loading && (
          <div className="text-center font-mono text-[var(--text-muted)] py-2">
            Importing holdings and calculating statutory exposure…
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-[var(--border-hairline)]">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-xs text-[var(--text-secondary)] border border-[var(--border-default)] transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </Modal>
  );
}

export default ImportHoldingsModal;

