/**
 * components/bills/AIAssistantPanel.tsx
 * =====================================
 * Grounded Groq AI Explanations panel for the Bill Detail Dossier.
 * Connects to FastAPI `/api/v1/ai/explain/bill/{id}` and `/api/v1/ai/ask`.
 *
 * Guarantees:
 * - All context is sourced strictly from the backend repository.
 * - Zero client-side prediction creation or secret leakage.
 * - Robust fallback when offline or Groq inference is unreachable.
 * - Non-investment advice disclaimers on all outputs.
 */

"use client";

import React, { useState } from "react";
import type { AIAskResponse } from "@/types/api";
import { aiApi } from "@/lib/api/ai";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SourceBadge, Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export interface AIAssistantPanelProps {
  billId: string;
  billTitle: string;
  isState: boolean;
  className?: string;
}

interface PromptPreset {
  label: string;
  operation?: string;
  question?: string;
}

export function AIAssistantPanel({
  billId,
  billTitle,
  isState,
  className = "",
}: AIAssistantPanelProps) {
  const [persona, setPersona] = useState<string>("GENERAL_PUBLIC");
  const [customQuestion, setCustomQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const presets: PromptPreset[] = [
    { label: "What does this bill change?", operation: "WHY_IT_MATTERS" },
    { label: "Which sectors are affected?", operation: "SECTOR_IMPACT" },
    { label: "Which companies have documented exposure?", question: "Which companies have documented corporate exposure under this bill?" },
    { label: "Why is this bill market relevant?", operation: "MARKET_INTELLIGENCE" },
    ...(isState
      ? []
      : [
          { label: "Explain the prediction", operation: "RISK_PROFILE" },
          { label: "What anticipation evidence exists?", operation: "ANTICIPATION" },
        ]),
  ];

  const handlePresetClick = async (preset: PromptPreset) => {
    setLoading(true);
    setError(null);
    try {
      let res: AIAskResponse;
      if (preset.operation) {
        res = await aiApi.explainBill(billId, preset.operation, persona);
      } else if (preset.question) {
        res = await aiApi.ask({
          question: preset.question,
          context_type: "bill",
          context_id: billId,
          persona,
        });
      } else {
        throw new Error("Invalid prompt preset");
      }
      setResponse(res);
    } catch (err: any) {
      setError(
        "AI Explanation Copilot is operating in offline mode or currently unreachable. All authoritative legislative and exposure records remain accessible directly in this dossier."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customQuestion.trim() || loading) return;

    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.ask({
        question: customQuestion.trim(),
        context_type: "bill",
        context_id: billId,
        persona,
      });
      setResponse(res);
    } catch (err: any) {
      setError(
        "AI Explanation Copilot is operating in offline mode or currently unreachable. All authoritative legislative and exposure records remain accessible directly in this dossier."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`space-y-4 ${className}`} aria-label="Grounded AI Copilot section">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2 w-full">
            <div>
              <CardTitle>Grounded AI Legislative Copilot</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Query validated parliamentary knowledge using LLaMA-3.3 inference grounded in verified project repositories.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="primary" size="xs">
                Groq LLaMA-3.3
              </Badge>
              <SourceBadge type="INTERPRETATION" size="xs" showTooltip />
            </div>
          </div>
        </CardHeader>

        <div className="space-y-4">
          {/* Persona Selector Ribbon */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <span className="text-xs font-semibold text-slate-400">
              Analyst Perspective:
            </span>
            <div className="flex items-center gap-1.5 text-xs">
              {[
                { id: "GENERAL_PUBLIC", label: "General Public" },
                { id: "INVESTOR", label: "Institutional Investor" },
                { id: "POLICY_RESEARCHER", label: "Policy Researcher" },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setPersona(p.id)}
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                    persona === p.id
                      ? "bg-blue-600 text-white font-semibold"
                      : "bg-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Suggested Prompts */}
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Suggested Analytical Inquiries
            </p>
            <div className="flex flex-wrap gap-1.5">
              {presets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => handlePresetClick(preset)}
                  disabled={loading}
                  className="rounded-lg border border-slate-700/80 bg-slate-900/60 px-2.5 py-1.5 text-xs text-slate-300 hover:bg-slate-800 hover:border-slate-600 hover:text-white transition-all text-left disabled:opacity-50"
                >
                  💬 {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Question Input */}
          <form onSubmit={handleCustomSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder={`Ask a grounded question about ${billTitle}...`}
              value={customQuestion}
              onChange={(e) => setCustomQuestion(e.target.value)}
              disabled={loading}
              className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none disabled:opacity-50"
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={loading || !customQuestion.trim()}
              id="btn-ask-ai-submit"
            >
              {loading ? "Analyzing..." : "Ask Copilot"}
            </Button>
          </form>

          {/* Loading Indicator */}
          {loading && (
            <div className="rounded-lg border border-blue-900/40 bg-blue-950/20 p-4 animate-pulse space-y-2">
              <div className="h-4 w-48 bg-blue-900/40 rounded" />
              <div className="h-3 w-full bg-blue-900/30 rounded" />
              <div className="h-3 w-5/6 bg-blue-900/30 rounded" />
              <div className="h-3 w-4/6 bg-blue-900/30 rounded" />
            </div>
          )}

          {/* AI Response Card */}
          {response && !loading && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4 space-y-3 animate-fade-in">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-200">
                    AI Analytical Synthesis
                  </span>
                  <Badge variant="purple" size="xs">
                    {response.operation}
                  </Badge>
                  {response.is_cached && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      (cached)
                    </span>
                  )}
                </div>
                <SourceBadge type="INTERPRETATION" size="xs" />
              </div>

              {/* Formatted Content */}
              <div className="text-xs text-slate-200 leading-relaxed space-y-2 whitespace-pre-line font-sans">
                {response.content}
              </div>

              {/* Provenance & Disclaimer Footer */}
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                <span>
                  Sources:{" "}
                  <strong className="text-slate-400">
                    {response.provenance_sources?.join(", ") || "Project Ground Truth"}
                  </strong>
                </span>
                <span className="italic">{response.disclaimer}</span>
              </div>
            </div>
          )}

          {/* Fallback / Error State */}
          {error && !loading && (
            <div className="rounded-lg border border-amber-900/40 bg-amber-950/20 p-3.5 text-xs text-amber-200 leading-relaxed flex items-start gap-2.5">
              <span className="text-sm mt-0.5" aria-hidden="true">ℹ</span>
              <div>
                <span className="font-semibold text-amber-100">Fallback Notice:</span>{" "}
                {error}
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

export default AIAssistantPanel;
