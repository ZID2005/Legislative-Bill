/**
 * components/companies/CompanyHeader.tsx
 * =======================================
 * Production header for the Corporate Intelligence Profile.
 * Supports both Quantitative companies and Intelligence-only entities.
 *
 * Displays:
 * - Full entity name, legal identity, aliases
 * - Badges: Quantitative vs Intelligence Only, Capability Tier, Listing Status,
 *   Ownership Type, Entity Type, Prediction Availability, Data Quality
 * - Ticker symbols (NSE / BSE), ISIN, Corporate Group Name, Sector, Industry, HQ Location
 * - Quick Actions: Add to Watchlist, Ask AI Copilot, View in Explorer, Share Profile
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import type { CompanyDetailResponse } from "@/types/api";
import { Badge, SourceBadge } from "@/components/ui/Badge";
import { CapabilityBadge } from "@/components/coverage/CapabilityBadge";
import { Button } from "@/components/ui/Button";

export interface CompanyHeaderProps {
  company: CompanyDetailResponse;
  onOpenWatchlist?: () => void;
  onSelectTab?: (tabId: string) => void;
  className?: string;
}

export function CompanyHeader({
  company,
  onOpenWatchlist,
  onSelectTab,
  className = "",
}: CompanyHeaderProps) {
  const [copied, setCopied] = useState(false);

  const isQuant = company.is_quant_eligible;
  const isListed = company.listing_status.toLowerCase() === "listed";
  const capLevel = isQuant ? 1 : 2;

  const handleShare = async () => {
    try {
      if (typeof window !== "undefined") {
        await navigator.clipboard.writeText(window.location.href);
        setCopied(true);
        setTimeout(() => setCopied(false), 2500);
      }
    } catch {
      // ignore clipboard error
    }
  };

  // Format entity type label
  const formatEntityType = (type: string) => {
    switch (type.toLowerCase()) {
      case "listed_company":
        return "Listed Corporate";
      case "unlisted_company":
        return "Unlisted Corporate";
      case "state_owned_enterprise":
        return "State-Owned Enterprise";
      case "statutory_corporation":
        return "Statutory Corporation";
      case "public_utility":
        return "Public Utility";
      case "cooperative":
        return "Cooperative Society";
      case "reference_entity":
        return "Reference Entity";
      default:
        return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }
  };

  return (
    <header className={`space-y-4 ${className}`} aria-label="Company Profile Header">
      {/* Breadcrumbs */}
      <nav className="text-xs text-slate-500 flex items-center gap-1.5" aria-label="Breadcrumb">
        <Link href="/explorer" className="hover:text-slate-300 transition-colors">
          India Explorer
        </Link>
        <span aria-hidden="true">›</span>
        <Link href="/companies" className="hover:text-slate-300 transition-colors">
          Companies
        </Link>
        <span aria-hidden="true">›</span>
        <span className="text-slate-300 font-medium truncate max-w-sm" aria-current="page">
          {company.company_name}
        </span>
      </nav>

      {/* Main Header Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 backdrop-blur-sm p-6 shadow-xl relative overflow-hidden">
        {/* Subtle decorative gradient glow */}
        <div
          className={`absolute -right-20 -top-20 w-64 h-64 rounded-full blur-3xl pointer-events-none opacity-15 ${
            isQuant ? "bg-emerald-500" : "bg-amber-500"
          }`}
          aria-hidden="true"
        />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          {/* Entity Identity & Badges */}
          <div className="space-y-3 flex-1 min-w-0">
            {/* Status Badges Row */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Universe Classification Badge */}
              <Badge
                variant={isQuant ? "success" : "warning"}
                size="sm"
                className="font-semibold tracking-wide"
              >
                {isQuant ? "📈 QUANTITATIVE" : "🔬 INTELLIGENCE ONLY"}
              </Badge>

              {/* Capability Level */}
              <CapabilityBadge level={capLevel} size="xs" />

              {/* Listing Status */}
              <Badge
                variant={isListed ? "primary" : "slate"}
                size="xs"
                className="font-medium"
              >
                {isListed ? "LISTED" : "UNLISTED"}
              </Badge>

              {/* Ownership / Entity Type */}
              <Badge variant="muted" size="xs" className="text-slate-400 border-slate-700">
                {formatEntityType(company.entity_type)}
              </Badge>

              {/* Prediction Availability */}
              <Badge
                variant={company.market_prediction_available ? "success" : "slate"}
                size="xs"
              >
                {company.market_prediction_available
                  ? "PREDICTION AVAILABLE"
                  : "PREDICTION UNAVAILABLE"}
              </Badge>

              {/* Data Quality */}
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 rounded px-2 py-0.5">
                <span aria-hidden="true">✓</span> {company.data_quality_label || "VERIFIED"}
              </span>

              {/* Source Provenance Badge */}
              <SourceBadge type="FACT" size="xs" showTooltip />
            </div>

            {/* Entity Name & Group */}
            <div>
              <div className="flex flex-wrap items-baseline gap-3">
                <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 tracking-tight">
                  {company.company_name}
                </h1>
                {company.group_name && (
                  <span className="text-sm font-medium text-slate-400 bg-slate-800/60 border border-slate-700/60 rounded px-2.5 py-0.5">
                    {company.group_name}
                  </span>
                )}
              </div>
              {company.legal_identity && company.legal_identity !== company.company_name && (
                <p className="text-xs text-slate-400 mt-1">
                  Legal Entity: <span className="text-slate-300">{company.legal_identity}</span>
                </p>
              )}
            </div>

            {/* Identifiers & Industry Ribbon */}
            <div className="flex flex-wrap items-center gap-y-1.5 gap-x-4 text-xs text-slate-400 pt-1">
              {company.ticker_nse && (
                <span className="flex items-center gap-1.5">
                  <span className="text-slate-500 font-mono">NSE:</span>
                  <span className="font-semibold text-slate-200">{company.ticker_nse}</span>
                </span>
              )}
              {company.ticker_bse && (
                <span className="flex items-center gap-1.5">
                  <span className="text-slate-500 font-mono">BSE:</span>
                  <span className="font-semibold text-slate-200">{company.ticker_bse}</span>
                </span>
              )}
              {company.isin && (
                <span className="flex items-center gap-1.5">
                  <span className="text-slate-500 font-mono">ISIN:</span>
                  <span className="font-mono text-slate-300">{company.isin}</span>
                </span>
              )}
              <span className="hidden sm:inline text-slate-700">•</span>
              <span className="text-slate-300 font-medium">
                {company.sector || "Diversified"}
              </span>
              {company.industry && (
                <>
                  <span className="text-slate-600">/</span>
                  <span className="text-slate-400">{company.industry}</span>
                </>
              )}
              {(company.hq_city || company.hq_state) && (
                <>
                  <span className="hidden sm:inline text-slate-700">•</span>
                  <span className="text-slate-400 flex items-center gap-1">
                    <span aria-hidden="true">📍</span>
                    {[company.hq_city, company.hq_state].filter(Boolean).join(", ")}
                  </span>
                </>
              )}
            </div>

            {/* Aliases where available */}
            {company.aliases && company.aliases.length > 0 && (
              <p className="text-xs text-slate-500">
                Also known as:{" "}
                <span className="text-slate-400">{company.aliases.join(", ")}</span>
              </p>
            )}
          </div>

          {/* Quick Actions Panel */}
          <div className="flex flex-wrap lg:flex-col items-center lg:items-stretch gap-2 lg:min-w-[190px]">
            <Button
              variant="primary"
              size="sm"
              onClick={onOpenWatchlist}
              className="w-full justify-center text-xs font-semibold shadow-sm"
              aria-label="Add company to watchlist"
            >
              ⭐ Add to Watchlist
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => onSelectTab?.("ai")}
              className="w-full justify-center text-xs font-medium border-slate-700 hover:bg-slate-800 text-slate-300"
              aria-label="Ask AI Analyst"
            >
              🤖 Ask AI Analyst
            </Button>

            <Link
              href={`/explorer?company=${encodeURIComponent(company.isin || company.company_id)}`}
              className="w-full"
            >
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-center text-xs font-medium border-slate-700 hover:bg-slate-800 text-slate-300"
              >
                🧭 View in Explorer
              </Button>
            </Link>

            <Button
              variant="ghost"
              size="sm"
              onClick={handleShare}
              className="w-full justify-center text-xs text-slate-400 hover:text-white"
              aria-label="Share company profile link"
            >
              {copied ? "✓ Copied Link" : "🔗 Share Profile"}
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default CompanyHeader;
