/**
 * components/ui/CommandPalette.tsx
 * =================================
 * Task 8.31C — Institutional Command Palette (⌘K).
 *
 * Supports fast keyboard navigation, entity prefixes, and system actions:
 * - /b: Scope to Legislative Bills (Central & State)
 * - /c: Scope to Master Companies (ISIN, Ticker, or Corporate Name)
 * - /s: Scope to Macro Sectors and Granular Industries
 * - /p: Scope to Market Impact Predictions
 * - >: System Navigation Shortcuts (e.g., > workspace, > monitoring)
 */

"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSearch } from "@/hooks/useSearch";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";

export interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

interface CommandAction {
  id: string;
  title: string;
  subtitle?: string | null;
  category: "system" | "bills" | "companies" | "sectors" | "predictions";
  route: string;
  badge?: string;
  icon?: string;
}

const SYSTEM_COMMANDS: CommandAction[] = [
  { id: "cmd_workspace", title: "Open Personalized Workspace", subtitle: "What changed since I last looked?", category: "system", route: "/workspace", icon: "🏛", badge: "DAILY HUB" },
  { id: "cmd_bills", title: "Open Legislative Directory", subtitle: "Canonical Central & State Acts Index", category: "system", route: "/bills", icon: "📜", badge: "INDEX" },
  { id: "cmd_explorer", title: "Open Legislative Explorer", subtitle: "Multi-facet discovery across 66 acts", category: "system", route: "/explorer", icon: "🔍", badge: "EXPLORE" },
  { id: "cmd_compare", title: "Open Bill Comparison Workbench", subtitle: "Side-by-side statutory diff", category: "system", route: "/bills/compare", icon: "⚖", badge: "TOOL" },
  { id: "cmd_predictions", title: "Open Market Predictions Engine", subtitle: "4,700 event-study records & horizons", category: "system", route: "/predictions", icon: "📈", badge: "ECONOMETRIC" },
  { id: "cmd_risk", title: "Open Legislative Risk Matrix", subtitle: "Systemic risk classifications & ISIN calculator", category: "system", route: "/risk", icon: "⚠", badge: "RISK" },
  { id: "cmd_anticipation", title: "Open Pre-Event Anticipation Analytics", subtitle: "940 market diffusion scores & news evidence", category: "system", route: "/anticipation", icon: "⏱", badge: "SIGNAL" },
  { id: "cmd_companies", title: "Open Corporate Directory", subtitle: "70 entities: 47 Quant + 20 Intel + 3 Ref", category: "system", route: "/companies", icon: "🏢", badge: "UNIVERSE" },
  { id: "cmd_industries", title: "Open Industries Taxonomy", subtitle: "Granular industries & sector mapping", category: "system", route: "/industries", icon: "🏭", badge: "TAXONOMY" },
  { id: "cmd_sectors", title: "Open Macro Economic Sectors", subtitle: "Macro policy transmission map", category: "system", route: "/sectors", icon: "⬡", badge: "MACRO" },
  { id: "cmd_states", title: "Open Sub-National Legislative Registry", subtitle: "State assembly acts — AP, KA, KL, TS", category: "system", route: "/states", icon: "🗺", badge: "STATES" },
  { id: "cmd_portfolio", title: "Open Portfolio Exposure Workspace", subtitle: "Holdings exposure, CSV upload & impact", category: "system", route: "/portfolio", icon: "💼", badge: "PORTFOLIO" },
  { id: "cmd_reports", title: "Open Institutional Report Center", subtitle: "7 audit report templates (PDF/CSV)", category: "system", route: "/reports", icon: "📑", badge: "REPORTS" },
  { id: "cmd_ai", title: "Launch Grounded AI Analyst Terminal", subtitle: "Conversational research & citations", category: "system", route: "/ai-analyst", icon: "✦", badge: "AI" },
  { id: "cmd_monitoring", title: "Open Legislative Monitoring Center", subtitle: "Source crawlers, check history & diffs", category: "system", route: "/monitoring", icon: "📡", badge: "HEALTH" },
  { id: "cmd_coverage", title: "Open Platform Coverage Audit", subtitle: "Verified baseline invariants & SHA-256", category: "system", route: "/coverage", icon: "📊", badge: "AUDIT" },
  { id: "cmd_alerts", title: "Open Legislative Alerts Center", subtitle: "Severity-filtered triggers & alert rules", category: "system", route: "/alerts", icon: "🔔", badge: "ALERTS" },
  { id: "cmd_settings", title: "Open Organization & User Settings", subtitle: "RBAC, preferences, API keys", category: "system", route: "/settings", icon: "⚙", badge: "SETTINGS" },
];

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [activeFilter, setActiveFilter] = useState<"all" | "bills" | "companies" | "sectors" | "predictions" | "commands">("all");

  const { results, search, clearSearch } = useSearch();

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setActiveFilter("all");
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      clearSearch();
    }
  }, [open, clearSearch]);

  // Handle prefix parsing
  let effectiveQuery = query.trim();
  let prefixMode: "all" | "bills" | "companies" | "sectors" | "predictions" | "commands" = activeFilter;

  if (effectiveQuery.startsWith("/b ") || effectiveQuery === "/b") {
    prefixMode = "bills";
    effectiveQuery = effectiveQuery.slice(2).trim();
  } else if (effectiveQuery.startsWith("/c ") || effectiveQuery === "/c") {
    prefixMode = "companies";
    effectiveQuery = effectiveQuery.slice(2).trim();
  } else if (effectiveQuery.startsWith("/s ") || effectiveQuery === "/s") {
    prefixMode = "sectors";
    effectiveQuery = effectiveQuery.slice(2).trim();
  } else if (effectiveQuery.startsWith("/p ") || effectiveQuery === "/p") {
    prefixMode = "predictions";
    effectiveQuery = effectiveQuery.slice(2).trim();
  } else if (effectiveQuery.startsWith("> ") || effectiveQuery === ">") {
    prefixMode = "commands";
    effectiveQuery = effectiveQuery.slice(1).trim();
  }

  // Trigger search if effectiveQuery has length
  useEffect(() => {
    if (effectiveQuery && prefixMode !== "commands") {
      search(effectiveQuery);
    }
  }, [effectiveQuery, prefixMode, search]);

  // Build combined items list
  const combinedItems = React.useMemo(() => {
    const list: CommandAction[] = [];

    // If command mode or query starts with '>', prioritize system commands
    if (prefixMode === "commands" || (effectiveQuery && prefixMode === "all")) {
      const filteredCommands = SYSTEM_COMMANDS.filter((cmd) => {
        if (!effectiveQuery) return true;
        return (
          cmd.title.toLowerCase().includes(effectiveQuery.toLowerCase()) ||
          cmd.route.toLowerCase().includes(effectiveQuery.toLowerCase()) ||
          cmd.subtitle?.toLowerCase().includes(effectiveQuery.toLowerCase())
        );
      });
      list.push(...filteredCommands);
    }

    // Add backend search results if available
    if (results && results.items && prefixMode !== "commands") {
      const searchItems: CommandAction[] = results.items
        .filter((item) => {
          if (prefixMode === "bills") {
            return item.category === "bills_central" || item.category === "bills_state";
          }
          if (prefixMode === "companies") {
            return item.category === "companies_quant" || item.category === "companies_intel";
          }
          if (prefixMode === "sectors") {
            return item.category === "sectors" || item.category === "industries";
          }
          if (prefixMode === "predictions") {
            return item.category === "bills_central" || item.category === "companies_quant";
          }
          return true;
        })
        .map((item, idx) => ({
          id: `res_${idx}_${item.url}`,
          title: item.title,
          subtitle: item.subtitle,
          category: item.category.startsWith("bills") ? "bills" : item.category.startsWith("companies") ? "companies" : "sectors",
          route: item.url,
          icon: item.category.startsWith("bills") ? "📜" : item.category.startsWith("companies") ? "🏢" : "⬡",
          badge: item.category.toUpperCase().replace("_", " "),
        }));
      list.push(...searchItems);
    }

    // If query is empty and not in commands mode, show top suggested commands & popular routes
    if (!effectiveQuery && prefixMode === "all") {
      list.push(...SYSTEM_COMMANDS.slice(0, 8));
    }

    return list;
  }, [effectiveQuery, prefixMode, results]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < combinedItems.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : combinedItems.length - 1));
    } else if (e.key === "Enter" && combinedItems[selectedIndex]) {
      e.preventDefault();
      const target = combinedItems[selectedIndex];
      router.push(target.route);
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto p-4 sm:p-6 md:p-20"
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
      onKeyDown={handleKeyDown}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Palette container */}
      <div className="relative mx-auto max-w-2xl transform overflow-hidden rounded-xl border border-white/10 bg-[#0c1322] shadow-2xl transition-all">
        {/* Search Input Bar */}
        <div className="flex items-center border-b border-white/10 bg-[#090e18] px-4 py-3">
          <span className="text-base text-slate-400 mr-3 select-none">🔍</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a bill, company, ticker, ISIN, or command (/b, /c, /s, >)..."
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
            autoComplete="off"
            spellCheck="false"
          />
          <span className="ml-3 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] font-mono text-slate-400 select-none">
            ESC
          </span>
        </div>

        {/* Filter Pills Strip */}
        <div className="flex items-center gap-1.5 px-4 py-2 border-b border-white/5 bg-[#090e18]/60 overflow-x-auto text-[11px]">
          <span className="text-slate-500 font-semibold uppercase tracking-wider text-[9px] mr-1">Scope:</span>
          {[
            { id: "all", label: "All" },
            { id: "bills", label: "/b Bills" },
            { id: "companies", label: "/c Companies" },
            { id: "sectors", label: "/s Sectors" },
            { id: "predictions", label: "/p Predictions" },
            { id: "commands", label: "> Commands" },
          ].map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => {
                setActiveFilter(f.id as any);
                setSelectedIndex(0);
              }}
              className={cn(
                "px-2 py-0.5 rounded transition-colors whitespace-nowrap",
                prefixMode === f.id
                  ? "bg-indigo-600 text-white font-medium"
                  : "bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 divide-y divide-white/5">
          {combinedItems.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500">
              No matching records or commands for <span className="text-slate-300 font-mono">"{query}"</span>.
            </div>
          ) : (
            combinedItems.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    router.push(item.route);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={cn(
                    "flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors duration-75",
                    isSelected ? "bg-[#121b2f] border border-indigo-500/30" : "hover:bg-white/[0.02]"
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <span className="text-base flex-shrink-0 opacity-80">{item.icon ?? "•"}</span>
                    <div className="min-w-0 flex-1">
                      <p className={cn("text-xs font-medium truncate", isSelected ? "text-white" : "text-slate-200")}>
                        {item.title}
                      </p>
                      {item.subtitle && (
                        <p className="text-[11px] text-slate-500 truncate mt-0.5">{item.subtitle}</p>
                      )}
                    </div>
                  </div>
                  {item.badge && (
                    <span className="flex-shrink-0 text-[9.5px] font-mono px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer info bar */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-white/10 bg-[#090e18] text-[10px] text-slate-500">
          <div className="flex items-center gap-3">
            <span><strong className="text-slate-400">↑↓</strong> Navigate</span>
            <span><strong className="text-slate-400">↵</strong> Select</span>
            <span><strong className="text-slate-400">ESC</strong> Close</span>
          </div>
          <span className="font-mono text-slate-500">LegisIntel Precision Search</span>
        </div>
      </div>
    </div>
  );
}

export default CommandPalette;
