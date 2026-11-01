/**
 * components/bills/BillHeader.tsx
 * ================================
 * Institutional header for the Bill Detail Dossier.
 * Features:
 * - Breadcrumb navigation (India Explorer › Bills › Title)
 * - Authority & status badges (Jurisdiction, Status, Capability, Market Relevance, Source)
 * - Official title and parliament/assembly bill number
 * - Legislative metadata ribbon (House, Legislature, Year, Intro Date, Assent Date)
 * - Header action buttons (Watchlist, Official PDF, Source, Compare, Ask AI, Share)
 */

"use client";

import React, { useState } from "react";
import Link from "next/link";
import type { BillSummaryItem } from "@/types/api";
import {
  JurisdictionBadge,
  StatusBadge,
  SourceBadge,
  ModelStatusBadge,
  Badge,
} from "@/components/ui/Badge";
import {
  CapabilityBadge,
  MarketRelevanceBadge,
} from "@/components/coverage/CapabilityBadge";
import { Button } from "@/components/ui/Button";
import { formatDate, getCapabilityLevel } from "@/lib/utils";

export interface BillHeaderProps {
  bill: BillSummaryItem;
  modelStatus?: string;
  modelStatusLabel?: string;
  onOpenWatchlist?: () => void;
  onAskAIClick?: () => void;
  className?: string;
}

export function BillHeader({
  bill,
  modelStatus,
  modelStatusLabel,
  onOpenWatchlist,
  onAskAIClick,
  className = "",
}: BillHeaderProps) {
  const [copied, setCopied] = useState(false);
  const capLevel = getCapabilityLevel(bill.jurisdiction, bill.modeling_eligibility);

  const handleShare = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2500);
      });
    }
  };

  return (
    <header className={`space-y-4 ${className}`} aria-label="Bill identity and summary">
      {/* Breadcrumb Navigation */}
      <nav
        className="text-xs text-[var(--text-faint)] flex items-center flex-wrap gap-1.5"
        aria-label="Breadcrumb"
      >
        <Link
          href="/explorer"
          className="hover:text-[var(--text-secondary)] transition-colors"
        >
          India Explorer
        </Link>
        <span aria-hidden="true">›</span>
        <Link
          href="/bills"
          className="hover:text-[var(--text-secondary)] transition-colors"
        >
          Bills
        </Link>
        <span aria-hidden="true">›</span>
        <span className="text-[var(--text-secondary)] font-medium truncate max-w-md">
          {bill.short_title || bill.title}
        </span>
      </nav>

      {/* Badges Ribbon */}
      <div className="flex flex-wrap items-center gap-2">
        <JurisdictionBadge jurisdiction={bill.jurisdiction} state={bill.state} />
        <StatusBadge status={bill.status} />
        <ModelStatusBadge
          status={modelStatus || (bill.jurisdiction?.toLowerCase() === "central" && bill.modeling_eligibility === "ELIGIBLE" ? "MODELLED" : "NOT_ELIGIBLE")}
          label={modelStatusLabel}
          size="xs"
        />
        <CapabilityBadge level={capLevel} size="xs" />
        <MarketRelevanceBadge relevance={bill.market_relevance} size="xs" />
        <SourceBadge type="FACT" size="xs" showTooltip />
        {bill.data_quality && (
          <Badge variant="emerald" size="xs">
            ✓ {bill.data_quality}
          </Badge>
        )}
      </div>

      {/* Main Title & Bill Number */}
      <div className="space-y-1">
        <div className="flex flex-wrap items-baseline gap-2">
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)] tracking-tight leading-snug">
            {bill.title}
          </h1>
        </div>
        {bill.bill_number && (
          <p className="text-xs font-mono text-[var(--text-muted)]">
            Official Bill No.:{" "}
            <span className="text-[var(--text-secondary)] font-medium">{bill.bill_number}</span>
          </p>
        )}
      </div>

      {/* Legislative Metadata Ribbon */}
      <div className="flex flex-wrap items-center gap-y-2 gap-x-5 text-xs text-[var(--text-muted)] pt-1 border-t border-[var(--border-default)]/80">
        <div className="flex items-center gap-1.5">
          <span className="text-[var(--text-faint)]">Legislature:</span>
          <span className="font-medium text-[var(--text-primary)]">{bill.legislature}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[var(--text-faint)]">Chamber:</span>
          <span className="font-medium text-[var(--text-primary)]">{bill.house || "—"}</span>
        </div>
        {bill.year && (
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--text-faint)]">Year:</span>
            <span className="font-medium text-[var(--text-primary)]">{bill.year}</span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <span className="text-[var(--text-faint)]">Introduced:</span>
          <span className="font-medium text-[var(--text-primary)]">
            {bill.introduction_date
              ? formatDate(bill.introduction_date)
              : "Date not available"}
          </span>
        </div>
        {bill.assent_date && (
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--text-faint)]">Assent:</span>
            <span className="font-medium text-[var(--text-primary)]">
              {formatDate(bill.assent_date)}
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-2 pt-2">
        <Button
          variant="primary"
          size="sm"
          onClick={onOpenWatchlist}
          id="btn-add-watchlist"
          aria-label="Add bill to watchlist"
        >
          ⭐ Add to Watchlist
        </Button>

        {bill.pdf_url && (
          <a
            href={bill.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            id="btn-official-pdf"
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)]/80 px-3 py-1.5 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] hover:text-white transition-colors"
          >
            📄 Official PDF ↗
          </a>
        )}

        {bill.source_url && (
          <a
            href={bill.source_url}
            target="_blank"
            rel="noopener noreferrer"
            id="btn-official-source"
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)]/80 px-3 py-1.5 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] hover:text-white transition-colors"
          >
            🏛 Official Portal ↗
          </a>
        )}

        <Link
          href={`/bills/compare?bill1=${encodeURIComponent(bill.bill_id)}`}
          id="btn-compare-bill"
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-elevated)]/80 px-3 py-1.5 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] hover:text-white transition-colors"
        >
          ⚖ Compare Bill
        </Link>

        {onAskAIClick && (
          <Button
            variant="outline"
            size="sm"
            onClick={onAskAIClick}
            id="btn-ask-ai"
          >
            🤖 Ask AI
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={handleShare}
          id="btn-share-bill"
          aria-label="Share bill dossier link"
        >
          {copied ? "✓ Copied!" : "🔗 Share"}
        </Button>
      </div>
    </header>
  );
}

export default BillHeader;
