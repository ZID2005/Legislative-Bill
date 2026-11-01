/**
 * components/workspace/AIWorkspaceAssistant.tsx
 * =============================================
 * Grounded AI Legislative Assistant embedded in the personalized workspace.
 * Queries the user's active watchlists, triggered alerts, and monitored entities.
 * Dual-theme synchronized for Seance.
 */

"use client";

import React, { useState } from "react";
import { aiApi } from "@/lib/api/ai";
import type { AIAskResponse, AIPersona } from "@/types/api";
import { AiAnalystIcon, SpinnerIcon, ShieldIcon } from "@/components/ui/Icons";
import { Button } from "@/components/ui/Button";

const PROMPT_CHIPS = [
  "What changed in my watchlists?",
  "Summarize my unread alerts.",
  "Which watched bills changed?",
  "Which watched companies have new legislative exposure?",
  "Explain my latest risk updates.",
  "What State legislative activity affects my watchlists?",
];

const PERSONAS: { id: AIPersona; label: string }[] = [
  { id: "GENERAL_PUBLIC", label: "General Public" },
  { id: "INVESTOR", label: "Investor" },
  { id: "CORPORATE_POLICY", label: "Corporate Policy" },
];

export function AIWorkspaceAssistant() {
  const [question, setQuestion] = useState("");
  const [selectedPersona, setSelectedPersona] = useState<AIPersona>("INVESTOR");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (queryText: string) => {
    const q = queryText.trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.ask({
        question: q,
        context_type: "workspace",
        context_id: "workspace_home",
        persona: selectedPersona,
      });
      setResponse(res);
    } catch (err: unknown) {
      console.error("AI assistant query failed:", err);
      setError("Unable to generate response. Please verify backend connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleAsk(question);
  };

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 shadow-xs transition-colors">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[var(--border-default)]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--action-primary)]/10 border border-[var(--action-primary)]/20 flex items-center justify-center text-[var(--action-primary)] flex-shrink-0 shadow-xs">
            <AiAnalystIcon size="lg" />
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
              <span>Workspace AI Assistant</span>
              <span className="text-[10px] uppercase font-mono font-bold tracking-wider px-2 py-0.5 rounded-full bg-[var(--action-primary)]/15 text-[var(--action-primary)] border border-[var(--action-primary)]/30">
                Grounded
              </span>
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Personalized qualitative intelligence grounded in your monitored bills, companies, and alert streams.
            </p>
          </div>
        </div>

        {/* Persona Select */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-[var(--text-muted)]">Perspective:</span>
          <div className="flex rounded-xl bg-[var(--bg-secondary)] p-1 border border-[var(--border-default)]">
            {PERSONAS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedPersona(p.id)}
                className={`px-2.5 py-1 text-xs rounded-lg transition-colors font-medium ${
                  selectedPersona === p.id
                    ? "bg-[var(--action-primary)] text-[var(--text-primary)] shadow-xs font-semibold"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Suggested Chips */}
      <div className="mt-4">
        <p className="text-[11px] font-semibold text-[var(--text-muted)] mb-2 uppercase tracking-wider">
          Suggested Inquiries
        </p>
        <div className="flex flex-wrap gap-2">
          {PROMPT_CHIPS.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuestion(chip);
                handleAsk(chip);
              }}
              className="text-xs px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-default)] hover:border-[var(--action-primary)]/40 transition-all text-left shadow-xs"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Query Form */}
      <form onSubmit={onSubmit} className="mt-4 flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your watchlists, regulatory risks, or alerts..."
          className="flex-1 bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-transparent focus:ring-2 focus:ring-[var(--focus-ring)] transition-all"
        />
        <Button
          type="submit"
          variant="primary"
          disabled={loading || !question.trim()}
          loading={loading}
          className="px-5 py-2.5 font-semibold"
        >
          Ask
        </Button>
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-4 p-3.5 rounded-xl bg-[var(--color-danger-bg)] border border-[var(--color-danger-border)] text-xs text-[var(--color-danger)] font-medium">
          {error}
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !response && (
        <div className="mt-4 p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-default)] animate-pulse space-y-2.5">
          <div className="h-3 bg-[var(--skeleton-bg)] rounded w-3/4" />
          <div className="h-3 bg-[var(--skeleton-bg)] rounded w-5/6" />
          <div className="h-3 bg-[var(--skeleton-bg)] rounded w-2/3" />
        </div>
      )}

      {/* AI Response Display */}
      {response && !loading && (
        <div className="mt-5 p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-default)] space-y-4">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] border-b border-[var(--border-default)] pb-2.5">
            <span className="font-semibold text-[var(--text-primary)]">Qualitative Intelligence Brief</span>
            <span className="text-[11px] text-[var(--text-muted)] font-mono">
              Model: {response.model || "Groq LLaMA 3.3 70B"}
            </span>
          </div>

          <div className="text-sm text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap">
            {response.content}
          </div>

          {/* Grounding sources */}
          {((response.grounding_sources || response.provenance_sources) && (response.grounding_sources || response.provenance_sources)!.length > 0) && (
            <div className="pt-3 border-t border-[var(--border-default)]">
              <p className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
                Grounding Evidence Sources
              </p>
              <div className="flex flex-wrap gap-2">
                {(response.grounding_sources || response.provenance_sources)!.map((src: string, i: number) => (
                  <span
                    key={i}
                    className="text-[11px] px-2.5 py-1 rounded-md bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border-default)] font-mono shadow-xs"
                  >
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Epistemic disclaimer */}
          <div className="pt-2 text-[11px] text-[var(--text-muted)] italic bg-[var(--bg-card)] p-3 rounded-lg border border-[var(--border-subtle)] flex items-start gap-2">
            <span className="text-[var(--color-warning)] mt-0.5" aria-hidden="true">
              <ShieldIcon size="xs" />
            </span>
            <span>{response.disclaimer || "Institutional Disclaimer: AI-generated qualitative analysis for institutional research only. Does not constitute financial, investment, or legal advice."}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIWorkspaceAssistant;
