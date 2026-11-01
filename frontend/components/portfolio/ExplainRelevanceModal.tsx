/**
 * components/portfolio/ExplainRelevanceModal.tsx
 * ==============================================
 * Grounded AI relevance explanation dialog using accessible Modal primitive.
 *
 * Implements:
 * - Evidence-backed linkage synthesis explaining why a measure affects user holdings
 * - Epistemic classification badge (FACT, INTERPRETATION, PREDICTION)
 * - Strict non-financial advice disclaimer
 * - Focus trapping and Escape listener
 */

"use client";

import React from "react";
import { Modal } from "@/components/ui/Modal";
import type { ExplainRelevanceResponse } from "@/types/api";

export interface ExplainRelevanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  loading: boolean;
  result: ExplainRelevanceResponse | null;
  billTitle?: string;
}

export function ExplainRelevanceModal({
  isOpen,
  onClose,
  loading,
  result,
  billTitle,
}: ExplainRelevanceModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Grounded Relevance Analysis"
      subtitle={billTitle || "Legislative linkage explanation"}
      maxWidth="lg"
      footer={
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-1.5 rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-xs font-semibold text-[var(--text-primary)] border border-[var(--border-default)] transition-colors"
        >
          Close Analysis
        </button>
      }
    >
      {loading ? (
        <div className="py-10 text-center space-y-2">
          <div className="inline-block animate-spin text-xl text-blue-500">⏳</div>
          <p className="text-xs font-mono text-[var(--text-muted)]">
            Synthesizing evidence-backed linkages across bill provisions and holdings…
          </p>
        </div>
      ) : result ? (
        <div className="space-y-4 text-xs">
          {/* Status & Tier Header */}
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-hairline)]">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)]">Relevance Tier:</span>
              <span className="font-bold text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded-sm bg-amber-500/10 border border-amber-500/25">
                {result.relevance_tier}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)]">Model Status:</span>
              <span className="font-mono text-[10px] text-[var(--text-secondary)]">
                {result.model_status}
              </span>
            </div>
          </div>

          {/* Explanation Text */}
          <div className="p-3.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-default)] space-y-2">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
              Evidentiary Synthesis
            </h4>
            <p className="leading-relaxed text-[var(--text-primary)] whitespace-pre-wrap font-body text-xs sm:text-sm">
              {result.explanation}
            </p>
          </div>

          {/* Affected Holdings */}
          {result.affected_holdings && result.affected_holdings.length > 0 && (
            <div className="text-[11px] text-[var(--text-secondary)]">
              <span className="font-semibold text-[var(--text-primary)]">Correlated Holdings: </span>
              {result.affected_holdings.join(", ")}
            </div>
          )}

          {/* Epistemic Governance Disclaimer */}
          <div className="p-2.5 rounded-md bg-[var(--color-info-bg)] border border-[var(--color-info-border)] text-[10px] text-[var(--text-muted)] leading-normal">
            <span className="font-semibold text-[var(--color-info)]">Epistemic Guarantee: </span>
            {result.disclaimer || "Non-financial decision support only. State stock predictions strictly equal zero."}
          </div>
        </div>
      ) : (
        <div className="py-6 text-center text-xs text-[var(--text-muted)]">
          No analysis result available.
        </div>
      )}
    </Modal>
  );
}

export default ExplainRelevanceModal;

