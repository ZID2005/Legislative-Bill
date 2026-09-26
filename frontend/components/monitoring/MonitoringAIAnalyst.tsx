/**
 * components/monitoring/MonitoringAIAnalyst.tsx
 * ================================================
 * Grounded AI monitoring assistant.
 * Receives monitoring context, answers questions grounded in actual data.
 *
 * Guardrails (enforced by backend):
 * - Does NOT invent legislative events
 * - Does NOT fabricate companies or exposure
 * - Does NOT create stock predictions
 * - Does NOT speculate about political motives
 * - Uses graceful fallback when context is unavailable
 */

"use client";

import React, { useState, useRef, useCallback } from "react";
import type { AIAskResponse } from "@/types/api";
import apiClient from "@/lib/api/client";

const PROMPT_CHIPS = [
  { id: "recent-changes", label: "What changed recently?", icon: "🔄" },
  { id: "new-central", label: "Show new Central bills.", icon: "🏛" },
  { id: "new-state", label: "Show new State legislative activity.", icon: "🗳" },
  { id: "explained", label: "Explain a legislative change.", icon: "💬" },
  { id: "companies", label: "Which companies are connected to recent changes?", icon: "🏢" },
  { id: "industries", label: "Which industries may be affected?", icon: "⚙" },
  { id: "confirmed-vs-derived", label: "What is confirmed versus derived?", icon: "🔍" },
];

interface MonitoringAIAnalystProps {
  className?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  epistemic?: string;
  isLoading?: boolean;
}

export function MonitoringAIAnalyst({ className = "" }: MonitoringAIAnalystProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const sendQuestion = useCallback(async (q: string) => {
    if (!q.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: q.trim() };
    setMessages((prev) => [...prev, userMsg, { role: "assistant", content: "", isLoading: true }]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await apiClient.post<AIAskResponse>("/api/v1/ai/ask", {
        question: q.trim(),
        context_type: "monitoring",
        context_id: "monitoring_overview",
        persona: "GENERAL_PUBLIC",
      });

      setMessages((prev) => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = {
          role: "assistant",
          content: res.content,
          isLoading: false,
        };
        return msgs;
      });
    } catch {
      setMessages((prev) => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = {
          role: "assistant",
          content:
            "The monitoring AI analyst is temporarily unavailable. Please check the monitoring overview for current system status.",
          isLoading: false,
        };
        return msgs;
      });
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }, [loading]);

  const handleChip = (chip: typeof PROMPT_CHIPS[0]) => sendQuestion(chip.label);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuestion(question);
    }
  };

  return (
    <div className={`flex flex-col rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden ${className}`} style={{ minHeight: "400px" }}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800 bg-slate-900/80 flex items-center gap-3">
        <span className="text-xl" aria-hidden="true">🤖</span>
        <div>
          <h3 className="text-sm font-semibold text-slate-200">AI Monitoring Analyst</h3>
          <p className="text-xs text-slate-500">
            Grounded in actual monitoring context · No fabricated events · No political speculation · No predictions
          </p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="px-5 py-2 border-b border-slate-800/50 bg-amber-500/5">
        <p className="text-xs text-amber-400/80">
          ⚖ Analytical monitoring context only. Not investment advice.
          State legislative monitoring does not generate stock predictions.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4" role="log" aria-live="polite" aria-label="AI monitoring conversation">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-3xl mb-3" aria-hidden="true">📡</div>
            <p className="text-slate-400 text-sm font-medium">Ask about legislative monitoring activity</p>
            <p className="text-slate-600 text-xs mt-1">
              The AI uses actual monitoring data as context. It will not fabricate events.
            </p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-blue-600/30 flex items-center justify-center text-sm shrink-0 mt-0.5" aria-hidden="true">
                  🤖
                </div>
              )}
              <div
                className={`max-w-[85%] rounded-xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600/20 border border-blue-500/20 text-slate-200 ml-auto"
                    : "bg-slate-800/60 border border-slate-700/40 text-slate-300"
                }`}
                role={msg.role === "assistant" ? "article" : undefined}
              >
                {msg.isLoading ? (
                  <div className="flex items-center gap-2 text-slate-500" aria-label="AI is thinking">
                    <span className="animate-pulse">●</span>
                    <span className="animate-pulse delay-75">●</span>
                    <span className="animate-pulse delay-150">●</span>
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center text-sm shrink-0 mt-0.5" aria-hidden="true">
                  👤
                </div>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Prompt chips */}
      {messages.length === 0 && (
        <div className="px-5 pb-3">
          <div className="text-xs text-slate-500 mb-2">Suggested questions:</div>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Suggested monitoring questions">
            {PROMPT_CHIPS.map((chip) => (
              <button
                key={chip.id}
                id={`chip-${chip.id}`}
                onClick={() => handleChip(chip)}
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700/60 hover:border-slate-600 hover:text-slate-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                <span aria-hidden="true">{chip.icon}</span>
                {chip.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-slate-800 px-4 py-3 flex items-end gap-3">
        <textarea
          ref={inputRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about monitoring activity, changes, sources..."
          rows={2}
          disabled={loading}
          className="flex-1 resize-none rounded-lg border border-slate-700 bg-slate-800/60 text-slate-200 text-sm px-3 py-2 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          aria-label="Monitoring question"
        />
        <button
          onClick={() => sendQuestion(question)}
          disabled={!question.trim() || loading}
          className="rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm px-4 py-2 font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 shrink-0"
          aria-label="Send question"
        >
          {loading ? "…" : "Ask"}
        </button>
      </div>
    </div>
  );
}
