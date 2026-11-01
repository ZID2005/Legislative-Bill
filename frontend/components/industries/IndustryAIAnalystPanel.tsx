/**
 * components/industries/IndustryAIAnalystPanel.tsx
 * ================================================
 * Grounded AI Industry Analyst panel with prompt chips and persona adaptation.
 */

import React, { useState } from "react";
import { aiApi } from "@/lib/api/ai";
import { Badge } from "@/components/ui/Badge";
import type { AIAskResponse } from "@/types/api";

export interface IndustryAIAnalystPanelProps {
  industryId: string;
  industryName: string;
}

const PROMPT_CHIPS = [
  "Explain the main legislative drivers affecting this industry.",
  "Which companies have documented exposure?",
  "Compare Central and State exposure.",
  "Explain the economic transmission mechanisms.",
  "Which exposures have quantitative market analysis?",
  "Summarize the main risks and uncertainties.",
];

export function IndustryAIAnalystPanel({
  industryId,
  industryName,
}: IndustryAIAnalystPanelProps) {
  const [question, setQuestion] = useState("");
  const [persona, setPersona] = useState<"GENERAL_PUBLIC" | "INVESTOR" | "POLICY_RESEARCHER">("INVESTOR");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (qText?: string) => {
    const query = qText || question;
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await aiApi.ask({
        question: query.trim(),
        context_type: "industry",
        context_id: industryId,
        persona: persona,
      });
      setResponse(res);
    } catch (err: any) {
      setError(
        err?.message ||
          "AI Analyst explanation is temporarily offline. Fallback to factual profile records below."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section aria-labelledby="ai-analyst-heading" className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-900/60 border border-purple-700/50 text-purple-200 text-sm">
            ✦
          </div>
          <div>
            <h2 id="ai-analyst-heading" className="text-lg font-semibold text-[var(--text-primary)]">
              AI Industry Analyst
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              Grounded, multi-persona synthesis strictly using validated parliamentary & corporate intelligence
            </p>
          </div>
        </div>

        {/* Persona Selector */}
        <div className="inline-flex rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] p-1 text-xs">
          <button
            type="button"
            onClick={() => setPersona("INVESTOR")}
            className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
              persona === "INVESTOR"
                ? "bg-purple-950/60 text-purple-300 border border-purple-800/40"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Investor
          </button>
          <button
            type="button"
            onClick={() => setPersona("POLICY_RESEARCHER")}
            className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
              persona === "POLICY_RESEARCHER"
                ? "bg-purple-950/60 text-purple-300 border border-purple-800/40"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Policy
          </button>
          <button
            type="button"
            onClick={() => setPersona("GENERAL_PUBLIC")}
            className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
              persona === "GENERAL_PUBLIC"
                ? "bg-purple-950/60 text-purple-300 border border-purple-800/40"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Public
          </button>
        </div>
      </div>

      {/* Main Panel Box */}
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-card)]/80 p-5 shadow-lg space-y-4">
        {/* Chips */}
        <div>
          <span className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider block mb-2">
            Suggested Analysis Queries:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {PROMPT_CHIPS.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => {
                  setQuestion(chip);
                  handleAsk(chip);
                }}
                disabled={loading}
                className="rounded-full border border-[var(--border-strong)]/80 bg-[var(--bg-elevated)]/60 px-3 py-1 text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-white hover:border-slate-600 transition-colors disabled:opacity-50"
              >
                {chip}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={`Ask a grounded question about ${industryName}...`}
            className="flex-1 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)]/90 px-3.5 py-2 text-xs text-[var(--text-primary)] placeholder-[var(--input-placeholder)] focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-purple-600 px-4 py-2 text-xs font-semibold text-[var(--text-primary)] hover:bg-purple-500 transition-colors disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <span>Analyze</span>
                <span>✦</span>
              </>
            )}
          </button>
        </form>

        {/* Error / Offline Alert */}
        {error && (
          <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-3 text-xs text-rose-300">
            <span className="font-semibold">Notice:</span> {error}
          </div>
        )}

        {/* AI Output Response */}
        {response && (
          <div className="rounded-lg border border-purple-900/40 bg-purple-950/10 p-4 space-y-3">
            <div className="flex items-center justify-between text-xs text-purple-300 border-b border-purple-900/30 pb-2">
              <span className="font-semibold">Synthesized Analysis ({response.persona})</span>
              {response.is_cached && (
                <Badge variant="purple" size="xs">Cached Synthesis</Badge>
              )}
            </div>

            <div className="text-xs text-[var(--text-primary)] leading-relaxed whitespace-pre-line space-y-2">
              {response.content}
            </div>

            <div className="text-[10px] text-[var(--text-faint)] pt-2 border-t border-[var(--border-default)]/80 italic">
              {response.disclaimer}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default IndustryAIAnalystPanel;
