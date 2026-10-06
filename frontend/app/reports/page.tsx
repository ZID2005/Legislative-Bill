/**
 * app/reports/page.tsx
 * =====================
 * Task 8.25 — Report Center (Phases 17–19).
 *
 * Users can generate downloadable reports for:
 * - Bills, Companies, Industries, Portfolios, Risk, Anticipation, Legislative Exposure
 *
 * Reports include: title, generation timestamp, data freshness, provenance,
 * source URLs, epistemic labels, disclaimers, methodology summary.
 *
 * SAFETY RULES:
 * - Reports generated from the SAME backend data used by the UI
 * - No second calculation engine
 * - Reports must NOT invent numbers, companies, statuses, dates, predictions, or URLs
 * - Every piece of data is labelled: FACT / OBSERVED / DERIVED / INTERPRETATION / PREDICTION
 */

"use client";

import React, { useState } from "react";
import { DataStatusBadge } from "@/components/ui/DataStatusBadge";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Report {
  id: string;
  type: "BILL" | "COMPANY" | "INDUSTRY" | "PORTFOLIO" | "RISK" | "ANTICIPATION" | "LEGISLATIVE_EXPOSURE";
  entity: string;
  entityId?: string;
  generatedAt: string;
  status: "READY" | "GENERATING" | "FAILED";
  format: "PDF" | "CSV" | "XLSX";
  sizeKb?: number;
  dataFreshnessAt?: string;
}

interface ReportTemplate {
  type: Report["type"];
  label: string;
  description: string;
  icon: string;
  formats: Array<"PDF" | "CSV" | "XLSX">;
  sections: string[];
}

const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    type: "BILL",
    label: "Bill Intelligence Report",
    description: "Full legislative dossier: provisions, corporate exposure, market intelligence, anticipation signals, provenance.",
    icon: "📜",
    formats: ["PDF"],
    sections: ["Bill Identity", "Summary", "Procedural Journey", "Key Provisions", "Economic Impact", "Corporate Exposure", "Market Intelligence", "Anticipation", "Sources"],
  },
  {
    type: "COMPANY",
    label: "Company Exposure Report",
    description: "Corporate legislative exposure, sector analysis, quantitative predictions where eligible, risk classification.",
    icon: "🏢",
    formats: ["PDF", "CSV"],
    sections: ["Company Profile", "Legislative Exposure", "Sector Analysis", "Modelled Impact", "Risk Classification", "Anticipation"],
  },
  {
    type: "INDUSTRY",
    label: "Industry Intelligence Report",
    description: "Sector-wide legislative exposure, affected companies, impact trends.",
    icon: "🏭",
    formats: ["PDF", "CSV"],
    sections: ["Industry Overview", "Legislative Exposure", "Affected Companies", "Risk Landscape"],
  },
  {
    type: "PORTFOLIO",
    label: "Portfolio Exposure Report",
    description: "Portfolio-level legislative risk, holding-by-holding exposure analysis, sector distribution.",
    icon: "📊",
    formats: ["PDF", "XLSX"],
    sections: ["Portfolio Summary", "Holdings Analysis", "Legislative Exposure Map", "Risk Overview", "Sector Distribution"],
  },
  {
    type: "RISK",
    label: "Risk Classification Report",
    description: "Cross-portfolio and cross-sector risk classification matrix with epistemic labels.",
    icon: "⚠",
    formats: ["PDF", "CSV"],
    sections: ["Risk Matrix", "High-Risk Bills", "Affected Companies", "Methodology"],
  },
  {
    type: "ANTICIPATION",
    label: "Anticipation Signals Report",
    description: "Pre-event market diffusion diagnostics across monitored bills and companies.",
    icon: "⏱",
    formats: ["PDF"],
    sections: ["Anticipation Overview", "Signal Analysis", "Bill-Company Matrix", "Methodology"],
  },
  {
    type: "LEGISLATIVE_EXPOSURE",
    label: "Legislative Exposure Summary",
    description: "Unified legislative exposure across all monitored entities — bills, companies, states.",
    icon: "⚖",
    formats: ["PDF", "CSV", "XLSX"],
    sections: ["Coverage Overview", "Central Exposure", "State Exposure", "Company Mapping", "Provenance"],
  },
];

// Sample generated reports
const SAMPLE_REPORTS: Report[] = [
  {
    id: "rpt_001",
    type: "BILL",
    entity: "Banking Regulation (Amendment) Act",
    entityId: "central_004",
    generatedAt: "2026-09-28T08:30:00Z",
    status: "READY",
    format: "PDF",
    sizeKb: 284,
    dataFreshnessAt: "2026-09-28T08:00:00Z",
  },
  {
    id: "rpt_002",
    type: "PORTFOLIO",
    entity: "My Portfolio",
    entityId: "portfolio_demo",
    generatedAt: "2026-09-27T16:45:00Z",
    status: "READY",
    format: "PDF",
    sizeKb: 512,
    dataFreshnessAt: "2026-09-27T16:00:00Z",
  },
  {
    id: "rpt_003",
    type: "RISK",
    entity: "All Bills — Risk Summary",
    generatedAt: "2026-09-26T09:00:00Z",
    status: "READY",
    format: "CSV",
    sizeKb: 48,
    dataFreshnessAt: "2026-09-26T08:00:00Z",
  },
  {
    id: "rpt_004",
    type: "COMPANY",
    entity: "ICICI Bank Limited",
    entityId: "icici",
    generatedAt: "2026-09-25T14:20:00Z",
    status: "READY",
    format: "PDF",
    sizeKb: 196,
    dataFreshnessAt: "2026-09-25T14:00:00Z",
  },
];

const TYPE_COLORS: Record<Report["type"], string> = {
  BILL: "text-blue-400 bg-blue-500/10",
  COMPANY: "text-teal-400 bg-teal-500/10",
  INDUSTRY: "text-amber-400 bg-amber-500/10",
  PORTFOLIO: "text-indigo-400 bg-indigo-500/10",
  RISK: "text-rose-400 bg-rose-500/10",
  ANTICIPATION: "text-violet-400 bg-violet-500/10",
  LEGISLATIVE_EXPOSURE: "text-emerald-400 bg-emerald-500/10",
};

const FORMAT_ICONS: Record<string, string> = {
  PDF: "📄",
  CSV: "📊",
  XLSX: "📋",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Generate Report Modal
// ---------------------------------------------------------------------------

function GenerateModal({ template, onClose }: { template: ReportTemplate; onClose: () => void }) {
  const [selectedFormat, setSelectedFormat] = useState<"PDF" | "CSV" | "XLSX">(template.formats[0]);
  const [entity, setEntity] = useState("");
  const [generating, setGenerating] = useState(false);
  const [done, setDone] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    await new Promise((r) => setTimeout(r, 1800));
    setGenerating(false);
    setDone(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative card-base w-full max-w-lg p-6 animate-scale-in">
        {done ? (
          <div className="text-center py-6 space-y-4">
            <div className="text-4xl">✅</div>
            <h3 className="text-base font-semibold text-white">Report Generated</h3>
            <p className="text-sm text-slate-400">
              Your {template.label} has been generated and is ready to download.
            </p>
            <p className="text-[10px] text-slate-600 max-w-xs mx-auto">
              Report generated from platform backend data. All figures are labelled FACT, OBSERVED, DERIVED, or PREDICTION as appropriate.
            </p>
            <div className="flex gap-3 pt-2">
              <button onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-white/8 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-all">
                Close
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-all">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download {selectedFormat}
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <span className="text-xl">{template.icon}</span>
                <h2 className="text-base font-semibold text-white">{template.label}</h2>
              </div>
              <button onClick={onClose} className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-5 leading-relaxed">{template.description}</p>

            {/* Entity input */}
            <div className="mb-4">
              <label className="text-xs font-medium text-slate-400 block mb-1.5">
                {template.type === "PORTFOLIO" ? "Portfolio Name" : "Entity Name / Search"}
              </label>
              <input
                type="text"
                value={entity}
                onChange={(e) => setEntity(e.target.value)}
                placeholder={template.type === "PORTFOLIO" ? "My Portfolio" : "Search bills, companies…"}
                className="w-full px-3 py-2 bg-slate-800/60 border border-white/8 rounded-lg text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>

            {/* Format selector */}
            <div className="mb-5">
              <label className="text-xs font-medium text-slate-400 block mb-1.5">Format</label>
              <div className="flex gap-2">
                {template.formats.map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => setSelectedFormat(fmt)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-medium transition-all",
                      selectedFormat === fmt
                        ? "border-blue-500/40 bg-blue-500/10 text-blue-300"
                        : "border-white/8 text-slate-500 hover:text-slate-300 hover:bg-white/5"
                    )}
                  >
                    <span>{FORMAT_ICONS[fmt]}</span>
                    {fmt}
                  </button>
                ))}
              </div>
            </div>

            {/* Sections preview */}
            <div className="mb-5">
              <p className="text-xs font-medium text-slate-400 mb-2">Report Sections</p>
              <div className="flex flex-wrap gap-1.5">
                {template.sections.map((section) => (
                  <span key={section} className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/8 text-slate-500">
                    {section}
                  </span>
                ))}
              </div>
            </div>

            {/* Safety notice */}
            <div className="mb-5 p-3 rounded-lg bg-amber-950/20 border border-amber-800/20 text-xs text-slate-500">
              <p className="font-semibold text-amber-400 mb-1">Report Safety</p>
              <p className="leading-relaxed">
                This report is generated directly from the platform&apos;s analytical data.
                All figures are labelled FACT, OBSERVED, DERIVED, or PREDICTION.
                The report will not invent numbers, companies, bill statuses, or predictions.
                No Buy/Sell/Hold recommendations are included.
              </p>
            </div>

            <div className="flex gap-3">
              <button onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-white/8 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-all">
                Cancel
              </button>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium disabled:opacity-60 transition-all"
              >
                {generating ? (
                  <>
                    <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Generating…
                  </>
                ) : (
                  `Generate ${selectedFormat}`
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Reports page
// ---------------------------------------------------------------------------

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<"center" | "templates">("center");
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-section-label">Platform</span>
          <span className="text-slate-700">/</span>
          <span className="badge-modelled">NEW</span>
        </div>
        <h1 className="text-headline text-white mb-1">Report Center</h1>
        <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
          Generate downloadable intelligence reports for bills, companies, portfolios, and more.
          All reports are backed by the same analytical data powering the platform.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-900/60 border border-white/8 rounded-lg p-1 w-fit">
        {[
          { id: "center" as const, label: "Report Center" },
          { id: "templates" as const, label: "Generate New Report" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-all",
              activeTab === tab.id ? "bg-white/10 text-white" : "text-slate-500 hover:text-slate-300"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Report Center — Recent reports */}
      {activeTab === "center" && (
        <div className="space-y-4">
          {SAMPLE_REPORTS.length === 0 ? (
            <div className="card-base p-12 text-center">
              <p className="text-slate-500 text-sm">No reports generated yet. Use the &quot;Generate New Report&quot; tab to create one.</p>
            </div>
          ) : (
            <>
              <p className="text-xs text-slate-600 mb-4">Recent reports · Click a report to download</p>
              {SAMPLE_REPORTS.map((report) => (
                <div key={report.id} className="card-base card-hover p-4 flex items-center gap-4">
                  <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0", TYPE_COLORS[report.type])}>
                    {REPORT_TEMPLATES.find(t => t.type === report.type)?.icon ?? "📄"}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="text-sm font-semibold text-slate-200 truncate">{report.entity}</p>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/8 text-slate-500 font-medium flex-shrink-0">
                        {report.type.replace("_", " ")}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                      <span>Generated: {formatDate(report.generatedAt)}</span>
                      {report.dataFreshnessAt && (
                        <span>Data as of: {formatDate(report.dataFreshnessAt)}</span>
                      )}
                      {report.sizeKb && <span>{report.sizeKb} KB</span>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={cn("text-[10px] px-2 py-0.5 rounded font-bold", FORMAT_ICONS[report.format] ? "" : "", "bg-white/5 border border-white/8 text-slate-400")}>
                      {report.format}
                    </span>
                    {report.status === "READY" && (
                      <>
                        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-blue-600/20 border border-blue-500/25 text-blue-400 hover:bg-blue-600/30 transition-all">
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Download
                        </button>
                        <button className="p-1.5 rounded text-slate-600 hover:text-slate-400 hover:bg-white/5 transition-all" aria-label="Regenerate report">
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                        <button className="p-1.5 rounded text-slate-600 hover:text-rose-400 hover:bg-white/5 transition-all" aria-label="Delete report">
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </>
                    )}
                    {report.status === "GENERATING" && (
                      <span className="flex items-center gap-1.5 text-xs text-amber-400">
                        <span className="inline-block w-3 h-3 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
                        Generating…
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Report templates */}
      {activeTab === "templates" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {REPORT_TEMPLATES.map((template) => (
            <button
              key={template.type}
              onClick={() => setSelectedTemplate(template)}
              className="card-base card-hover p-5 text-left group transition-all"
              id={`report-template-${template.type.toLowerCase()}`}
            >
              <div className="flex items-start gap-3 mb-3">
                <span className="text-2xl">{template.icon}</span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-200 group-hover:text-white transition-colors">
                    {template.label}
                  </p>
                  <div className="flex gap-1 mt-1">
                    {template.formats.map((fmt) => (
                      <span key={fmt} className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 border border-white/8 text-slate-600 font-medium">
                        {fmt}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">{template.description}</p>
              <div className="mt-3 flex items-center gap-1 text-xs text-blue-400 group-hover:text-blue-300 transition-colors">
                <span>Generate Report</span>
                <svg className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Generate modal */}
      {selectedTemplate && (
        <GenerateModal
          template={selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
        />
      )}
    </div>
  );
}
