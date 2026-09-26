/**
 * components/workspace/AIWorkspaceAssistant.tsx
 * =============================================
 * Grounded AI Legislative Assistant embedded in the personalized workspace.
 * Queries the user's active watchlists, triggered alerts, and monitored entities.
 */

"use client";

import React, { useState } from "react";
import { aiApi } from "@/lib/api/ai";
import type { AIAskResponse, AIPersona } from "@/types/api";

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
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 text-xl font-bold">
            ✦
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Workspace AI Assistant
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 border border-blue-700/40">
                Grounded
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Personalized qualitative intelligence grounded in your monitored bills, companies, and alert streams.
            </p>
          </div>
        </div>

        {/* Persona Select */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Perspective:</span>
          <div className="flex rounded-lg bg-slate-800/80 p-0.5 border border-slate-700">
            {PERSONAS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedPersona(p.id)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  selectedPersona === p.id
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
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
        <p className="text-[11px] font-medium text-slate-400 mb-2 uppercase tracking-wider">
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
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/70 hover:bg-slate-800 text-slate-300 hover:text-blue-300 border border-slate-750 hover:border-blue-500/40 transition-all text-left"
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
          className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2 shadow-sm"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <span>Ask</span>
              <span>→</span>
            </>
          )}
        </button>
      </form>

      {/* Error display */}
      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-900/30 border border-red-700/50 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !response && (
        <div className="mt-4 p-4 rounded-lg bg-slate-950/60 border border-slate-800 animate-pulse space-y-2.5">
          <div className="h-3 bg-slate-800 rounded w-3/4" />
          <div className="h-3 bg-slate-800 rounded w-5/6" />
          <div className="h-3 bg-slate-800 rounded w-2/3" />
        </div>
      )}

      {/* AI Response Display */}
      {response && !loading && (
        <div className="mt-5 p-5 rounded-lg bg-slate-950 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
            <span className="font-semibold text-slate-200">Qualitative Intelligence Brief</span>
            <span className="text-[11px] text-slate-400 font-mono">
              Model: {response.model || "Groq LLaMA 3.3 70B"}
            </span>
          </div>

          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed whitespace-pre-wrap">
            {response.content}
          </div>

          {/* Grounding sources */}
          {((response.grounding_sources || response.provenance_sources) && (response.grounding_sources || response.provenance_sources)!.length > 0) && (
            <div className="pt-3 border-t border-slate-800">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Grounding Evidence Sources
              </p>
              <div className="flex flex-wrap gap-2">
                {(response.grounding_sources || response.provenance_sources)!.map((src: string, i: number) => (
                  <span
                    key={i}
                    className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono"
                  >
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Epistemic disclaimer */}
          <div className="pt-2 text-[11px] text-slate-400 italic bg-slate-900/50 p-2.5 rounded border border-slate-800">
            ⚠ {response.disclaimer || "Institutional Disclaimer: AI-generated qualitative analysis for institutional research only. Does not constitute financial, investment, or legal advice."}
          </div>
        </div>
      )}
    </div>
  );
}

export default AIWorkspaceAssistant;
