/**
 * components/companies/CompanyAIPanel.tsx
 * =======================================
 * Grounded Groq AI Assistant for Corporate Profiles.
 * Sourced through FastAPI `/api/v1/ai/explain/company/{id}` and `/api/v1/ai/ask`.
 *
 * Strict Compliance:
 * - Grounded strictly in validated parliamentary & corporate intelligence.
 * - Robust offline fallback when Groq LLM inference is disabled or unreachable.
 * - Zero secret leakage (never exposes API keys or internal traces).
 * - Strict non-financial advice disclaimer on all outputs.
 */

"use client";

import React, { useState } from "react";
import type { CompanyDetailResponse, AIAskResponse } from "@/types/api";
import { aiApi } from "@/lib/api/ai";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge, SourceBadge } from "@/components/ui/Badge";

export interface CompanyAIPanelProps {
  company: CompanyDetailResponse;
  className?: string;
}

export function CompanyAIPanel({ company, className = "" }: CompanyAIPanelProps) {
  const isQuant = company.is_quant_eligible;

  // Selected persona state
  const [persona, setPersona] = useState<string>("GENERAL_PUBLIC");

  // Freeform question state
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<AIAskResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Quick Prompt Chips
  const promptChips = [
    "What legislation affects this company?",
    "Why is this company exposed to these bills?",
    "Which States are relevant to this company?",
    "What economic mechanisms connect bills to this company?",
    isQuant
      ? "Explain the modelled prediction."
      : "Why is prediction unavailable for this entity?",
  ];

  // Submit grounded question
  const handleSubmit = async (qText: string) => {
    if (!qText.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await aiApi.ask({
        context_type: "company",
        context_id: company.isin || company.company_id,
        question: qText.trim(),
        persona,
      });
      setAiResponse(res);
    } catch {
      setErrorMsg(
        "AI explanation service is temporarily unreachable. Grounded parliamentary facts remain available across other tabs."
      );
    } finally {
      setLoading(false);
    }
  };

  // Run full company profile synthesis
  const handleSynthesizeProfile = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await aiApi.explainCompany(company.isin || company.company_id, persona);
      setAiResponse(res);
    } catch {
      setErrorMsg("Failed to synthesize corporate profile intelligence.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 w-full">
          <div className="flex items-center gap-2">
            <span className="text-lg" aria-hidden="true">🤖</span>
            <CardTitle>AI Corporate Intelligence Analyst</CardTitle>
            <SourceBadge type="INTERPRETATION" size="xs" showTooltip />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Perspective:</span>
            <select
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              aria-label="Select AI Analyst Persona"
            >
              <option value="GENERAL_PUBLIC">General Public</option>
              <option value="INVESTOR">Institutional Investor</option>
              <option value="CORPORATE_ANALYST">Corporate Legal / Strategy</option>
              <option value="POLICY_RESEARCHER">Policy Researcher</option>
            </select>
          </div>
        </div>
      </CardHeader>

      <div className="space-y-4">
        {/* Intro */}
        <p className="text-xs text-slate-400 leading-relaxed">
          Ask grounded questions regarding <strong className="text-slate-200">{company.company_name}</strong>'s legislative footprint, statutory provisions, and transmission mechanisms.
          All answers are grounded strictly in validated project repositories with offline fallback guard.
        </p>

        {/* Quick Prompt Chips */}
        <div>
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
            Recommended Prompt Chips:
          </span>
          <div className="flex flex-wrap gap-2">
            {promptChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(chip);
                  handleSubmit(chip);
                }}
                disabled={loading}
                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 rounded-full px-3 py-1 transition-colors text-left"
              >
                {chip}
              </button>
            ))}
          </div>
        </div>

        {/* Freeform Question Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(question);
          }}
          className="flex flex-col sm:flex-row gap-2 pt-2"
        >
          <input
            type="text"
            placeholder={`Ask about ${company.company_name}'s exposures, states, or mechanisms...`}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            className="flex-1 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            aria-label="Ask AI a question"
          />
          <div className="flex gap-2">
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={loading || !question.trim()}
              className="text-xs shrink-0"
            >
              {loading ? "Analysing..." : "Ask Analyst"}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleSynthesizeProfile}
              disabled={loading}
              className="text-xs shrink-0 border-slate-700"
            >
              Full Profile Synthesis
            </Button>
          </div>
        </form>

        {/* Error Alert */}
        {errorMsg && (
          <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-3 text-xs text-rose-300">
            {errorMsg}
          </div>
        )}

        {/* AI Answer Card */}
        {aiResponse && (
          <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-5 space-y-3 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <div className="flex items-center gap-2">
                <span className="text-base" aria-hidden="true">💡</span>
                <h4 className="text-xs font-semibold text-slate-200">
                  AI Analytical Response ({aiResponse.persona})
                </h4>
                {aiResponse.success ? (
                  <Badge variant="success" size="xs">Grounded</Badge>
                ) : (
                  <Badge variant="warning" size="xs">Offline Fallback</Badge>
                )}
              </div>
              {aiResponse.is_cached && (
                <span className="text-[10px] text-slate-500 font-mono">Cached Insight</span>
              )}
            </div>

            {/* Content Body */}
            <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-line space-y-2">
              {aiResponse.content}
            </div>

            {/* Provenance & Disclaimer Footer */}
            <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-slate-500">
              <div className="flex flex-wrap items-center gap-1.5">
                <span>Sources:</span>
                {aiResponse.provenance_sources?.map((src, i) => (
                  <span key={i} className="text-slate-400 font-medium">
                    {src}{i < (aiResponse.provenance_sources?.length ?? 1) - 1 ? " • " : ""}
                  </span>
                ))}
              </div>
              <span className="italic text-slate-500 text-[10px]">
                {aiResponse.disclaimer || "Analytical explanation only; not investment advice."}
              </span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

export default CompanyAIPanel;
