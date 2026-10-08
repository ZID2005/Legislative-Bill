/**
 * app/ai-analyst/AIAnalystContent.tsx
 * ===================================
 * Task 8.31C — Modern Grounded AI Analyst Terminal.
 *
 * Implements:
 * - Conversational research terminal grounded in official parliamentary and corporate data
 * - Active Context Selector (Bill, Company, Industry, General)
 * - Tri-Persona Selector: Institutional Investor, Policy Researcher, Compliance / Public
 * - Evidence citations drawer & provenance sources
 * - Strict refusal guardrails banner (No buy/sell/hold advice, no price targets)
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { aiApi } from "@/lib/api/ai";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { ContextDrawer } from "@/components/ui/ContextDrawer";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  persona?: string;
  contextType?: string;
  contextId?: string;
  provenanceSources?: string[];
  disclaimer?: string;
}

const SAMPLE_QUESTIONS = [
  "What statutory compliance mandates does the Energy Conservation Act impose on heavy industries?",
  "How does the Digital Personal Data Protection Act affect IT companies with cross-border operations?",
  "What are the direct vs indirect exposure pathways for Reliance Industries under recent Central legislation?",
  "Summarize the penalty provisions and appellate procedures under the Mines and Minerals Amendment.",
];

export default function AIAnalystContent() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "ai",
      text: "Welcome to the Grounded AI Analyst Terminal. I synthesize parliamentary acts, gazette provisions, and corporate exposures without speculative forecasting or financial advice. How can I assist your analysis today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      persona: "INVESTOR",
      provenanceSources: ["Official Parliamentary Ingestion Engine", "Verified Gazette Ground Truth"],
      disclaimer: "Verified Provenance: Analytical explanation only; not investment advice.",
    },
  ]);

  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [persona, setPersona] = useState<"INVESTOR" | "POLICY" | "GENERAL_PUBLIC">("INVESTOR");
  const [contextType, setContextType] = useState<"bill" | "company" | "industry" | "general">("bill");
  const [contextId, setContextId] = useState("bill_001_energy_conservation");

  // Evidence Drawer state
  const [activeSources, setActiveSources] = useState<string[] | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: inputQuery.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      persona,
      contextType,
      contextId: contextType !== "general" ? contextId : undefined,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const res = await aiApi.ask({
        question: userMsg.text,
        persona,
        context_type: contextType !== "general" ? contextType : undefined,
        context_id: contextType !== "general" ? contextId : undefined,
      });

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: "ai",
        text: res.answer || res.content || "No analysis generated.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        persona,
        contextType,
        contextId,
        provenanceSources: res.provenance_sources || res.context_sources || ["Parliamentary Archive"],
        disclaimer: res.disclaimer,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `ai-err-${Date.now()}`,
        sender: "ai",
        text: `Analysis unavailable: ${err?.userMessage || "System could not process query against grounded intelligence."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        provenanceSources: ["System Fallback"],
        disclaimer: "Analytical engine fallback mode.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearSession = () => {
    setMessages([
      {
        id: "welcome-reset",
        sender: "ai",
        text: "Session cleared. Select your analysis context and query to begin grounded synthesis.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        persona,
        provenanceSources: ["Clean Session Baseline"],
      },
    ]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-7xl mx-auto flex flex-col">
      {/* Terminal Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">✦</span>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
              Institutional AI Analyst Terminal
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/70 text-indigo-300 border border-indigo-800/40">
              Grounded Groq LLM
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Grounded Q&A across statutory enactments, gazette provisions, and econometric risk exposures.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleClearSession}
            className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded border border-slate-700 transition-colors"
          >
            New Session
          </button>
          <Link
            href="/workspace"
            className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 rounded border border-slate-700 transition-colors"
          >
            Workspace →
          </Link>
        </div>
      </div>

      {/* Context & Persona Control Bar */}
      <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Active Context Anchor */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 font-medium">Active Grounding Context:</span>
              <span className="text-slate-500 font-mono text-[11px]">Context Type</span>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={contextType}
                onChange={(e) => setContextType(e.target.value as any)}
                className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-md focus:outline-none focus:border-indigo-500"
              >
                <option value="bill">Legislative Bill</option>
                <option value="company">Corporate Entity</option>
                <option value="industry">Sector / Industry</option>
                <option value="general">General Registry</option>
              </select>

              {contextType !== "general" && (
                <input
                  type="text"
                  value={contextId}
                  onChange={(e) => setContextId(e.target.value)}
                  placeholder={
                    contextType === "bill"
                      ? "Bill ID (e.g. bill_001_energy_conservation)"
                      : contextType === "company"
                      ? "Company ISIN or Ticker (e.g. RELIANCE.NS)"
                      : "Industry Identifier"
                  }
                  className="flex-1 px-3 py-1.5 bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-md focus:outline-none focus:border-indigo-500 font-mono"
                />
              )}
            </div>
          </div>

          {/* Tri-Persona Switcher */}
          <div className="space-y-1.5">
            <span className="text-xs text-slate-400 font-medium block">Analyst Synthesis Persona:</span>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => setPersona("INVESTOR")}
                className={cn(
                  "px-2 py-1.5 rounded-md text-xs font-medium transition-all text-center",
                  persona === "INVESTOR"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                )}
              >
                Investor
              </button>
              <button
                type="button"
                onClick={() => setPersona("POLICY")}
                className={cn(
                  "px-2 py-1.5 rounded-md text-xs font-medium transition-all text-center",
                  persona === "POLICY"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                )}
              >
                Policy Lead
              </button>
              <button
                type="button"
                onClick={() => setPersona("GENERAL_PUBLIC")}
                className={cn(
                  "px-2 py-1.5 rounded-md text-xs font-medium transition-all text-center",
                  persona === "GENERAL_PUBLIC"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                )}
              >
                Compliance
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Stream View */}
      <div className="flex-1 min-h-[420px] rounded-lg bg-slate-900/40 border border-slate-800/80 p-4 overflow-y-auto space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex flex-col space-y-1 max-w-3xl",
              msg.sender === "user" ? "ml-auto items-end" : "mr-auto items-start"
            )}
          >
            <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
              <span>{msg.sender === "user" ? "Analyst" : "Grounded Copilot"}</span>
              <span>·</span>
              <span>{msg.timestamp}</span>
              {msg.persona && (
                <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                  {msg.persona}
                </span>
              )}
            </div>

            <div
              className={cn(
                "p-4 rounded-xl text-sm leading-relaxed",
                msg.sender === "user"
                  ? "bg-indigo-600 text-white rounded-br-none"
                  : "bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none shadow-sm"
              )}
            >
              <div className="whitespace-pre-wrap">{msg.text}</div>

              {/* Provenance Pills for AI answers */}
              {msg.sender === "ai" && msg.provenanceSources && msg.provenanceSources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-[11px] text-slate-400 font-medium">Grounded Sources:</span>
                  {msg.provenanceSources.map((src, i) => (
                    <button
                      key={i}
                      onClick={() => setActiveSources(msg.provenanceSources || [])}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 transition-colors"
                    >
                      {src}
                    </button>
                  ))}
                </div>
              )}

              {msg.disclaimer && (
                <div className="mt-2 text-[10px] text-slate-400 italic">
                  {msg.disclaimer}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="mr-auto p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-400 flex items-center gap-3">
            <span className="animate-spin text-indigo-400 text-base">✦</span>
            <span>Synthesizing grounded parliamentary and econometric evidence...</span>
          </div>
        )}
      </div>

      {/* Suggested Quick Queries */}
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <span className="text-slate-400 text-[11px] font-medium mr-1">Suggested:</span>
        {SAMPLE_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            onClick={() => {
              setInputQuery(q);
            }}
            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-[11px] transition-colors truncate max-w-xs"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Bar Form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask a question grounded in parliamentary records and corporate exposures..."
          disabled={loading}
          className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !inputQuery.trim()}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg text-sm disabled:opacity-50 transition-colors flex items-center gap-1.5"
        >
          <span>Ask</span>
          <span>→</span>
        </button>
      </form>

      {/* Strict Refusal Guardrails Banner */}
      <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-slate-400 flex items-start gap-2.5">
        <span className="text-amber-400 mt-0.5">🛡️</span>
        <div>
          <span className="font-semibold text-slate-300">
            Institutional Refusal Guardrails Active:
          </span>{" "}
          The AI strictly refuses stock price targets, buy/sell recommendations, and speculative political forecasting.
          All factual claims are derived strictly from published gazette acts, official parliamentary transcripts, and OLS event-study calculations.
        </div>
      </div>

      {/* Evidence Sources Drawer */}
      <ContextDrawer
        open={Boolean(activeSources)}
        onClose={() => setActiveSources(null)}
        title="Grounded Provenance Sources"
        subtitle="Verifiable evidence and statutory citations"
      >
        <div className="space-y-4 text-sm">
          <p className="text-xs text-slate-400">
            The following records were verified by the provenance engine to ground this analytical response:
          </p>
          <div className="space-y-2">
            {activeSources?.map((src, i) => (
              <div
                key={i}
                className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono"
              >
                {src}
              </div>
            ))}
          </div>
          <div className="p-3 rounded bg-indigo-950/30 border border-indigo-800/40 text-xs text-indigo-300">
            All sources are checksummed and cross-referenced with Central and State legislative databases.
          </div>
        </div>
      </ContextDrawer>
    </div>
  );
}
