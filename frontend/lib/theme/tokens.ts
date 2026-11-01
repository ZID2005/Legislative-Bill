/**
 * lib/theme/tokens.ts
 * ===================
 * Seance Design System Tokens — Single Source of Truth
 *
 * Implements the Editorial-Finance Visual Foundation:
 * - Institutional credibility and mathematical precision
 * - 8-point spatial scale and restrained corner radii
 * - 9-level typography scale with editorial serif accent and tabular numerals
 * - Light, Dark, and System dual-theme semantic color tokens
 * - Epistemic classification palette ([FACT], [OBSERVED], [DERIVED], [INTERPRETATION], [PREDICTION], [EVIDENCE])
 * - Restrained motion tokens with prefers-reduced-motion compatibility
 * - 3-tier layout density standard (compact, standard, relaxed)
 */

export const fontFamilies = {
  sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  serif: '"Newsreader", "Charter", "Bitstream Charter", "Georgia", "Cambria", "Times New Roman", serif',
  mono: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
} as const;

export interface TypographyToken {
  family: string;
  size: string;
  sizeRem: string;
  lineHeight: string;
  weight: number;
  tracking: string;
  role: string;
  fontStyle?: string;
  numeric?: string;
  textTransform?: string;
}

export const typographyScale: Record<string, TypographyToken> = {
  display: {
    family: fontFamilies.sans,
    size: "32px",
    sizeRem: "2.0rem",
    lineHeight: "1.15",
    weight: 700,
    tracking: "-0.03em",
    role: "Primary command center titles, major platform milestones",
  },
  headline: {
    family: fontFamilies.sans,
    size: "22px",
    sizeRem: "1.375rem",
    lineHeight: "1.25",
    weight: 600,
    tracking: "-0.02em",
    role: "Dossier headers, Portfolio workspace title, Settings header",
  },
  title: {
    family: fontFamilies.sans,
    size: "16px",
    sizeRem: "1.0rem",
    lineHeight: "1.35",
    weight: 600,
    tracking: "-0.015em",
    role: "Section headers, card group titles, modal headers",
  },
  subhead: {
    family: fontFamilies.sans,
    size: "14px",
    sizeRem: "0.875rem",
    lineHeight: "1.40",
    weight: 500,
    tracking: "-0.01em",
    role: "Table column categories, module descriptions",
  },
  body: {
    family: fontFamilies.sans,
    size: "13px",
    sizeRem: "0.8125rem",
    lineHeight: "1.55",
    weight: 400,
    tracking: "0",
    role: "Primary analytical text, summaries, descriptions",
  },
  legal: {
    family: fontFamilies.serif,
    size: "14px",
    sizeRem: "0.875rem",
    lineHeight: "1.65",
    weight: 400,
    tracking: "0",
    fontStyle: "italic",
    role: "Gazette legal text, official statutory quotes, preamble",
  },
  tabular: {
    family: fontFamilies.mono,
    size: "12px",
    sizeRem: "0.75rem",
    lineHeight: "1.40",
    weight: 500,
    tracking: "0",
    numeric: "tabular-nums lining-nums",
    role: "Predictions, event windows, CAR values, ISINs, dates",
  },
  caption: {
    family: fontFamilies.sans,
    size: "11px",
    sizeRem: "0.6875rem",
    lineHeight: "1.35",
    weight: 500,
    tracking: "+0.02em",
    role: "Column headers, footnotes, timestamps, data status",
  },
  micro: {
    family: fontFamilies.sans,
    size: "10px",
    sizeRem: "0.625rem",
    lineHeight: "1.20",
    weight: 700,
    tracking: "+0.08em",
    textTransform: "uppercase",
    role: "Epistemic badges, firewall stamps, ticker chips",
  },
};

/**
 * 8-Point Spatial Scale
 */
export const spacingScale = {
  "0.5": "0.25rem", // 4px
  "1": "0.5rem",    // 8px
  "1.5": "0.75rem", // 12px
  "2": "1.0rem",    // 16px
  "3": "1.5rem",    // 24px
  "4": "2.0rem",    // 32px
  "6": "3.0rem",    // 48px
  "8": "4.0rem",    // 64px
} as const;

/**
 * Restrained Radii Scale (Eliminating bulbous cards)
 */
export const radiiScale = {
  none: "0px",
  sm: "4px",   // Micro indicators, epistemic pills
  md: "6px",   // Small controls, buttons, badges
  lg: "8px",   // Form inputs, select menus, small containers
  xl: "12px",  // Structural containers, inspection panels, modals
  full: "9999px", // Tickers, avatar chips
} as const;

/**
 * Content Width Architecture
 */
export const contentWidths = {
  prose: "680px",       // Maximum reading column for optimal ocular sweep
  container: "1280px",   // Standard desktop content container (max-w-7xl)
  matrix: "1440px",      // High-density analytical data grids & matrices
} as const;

/**
 * Density Scale Rules
 */
export const densityScale = {
  compact: {
    name: "compact",
    rowHeight: "36px",
    cellPadding: "py-2 px-3",
    fontSize: "12px",
    purpose: "Tables, matrices, portfolio rosters, high-frequency surveillance",
  },
  standard: {
    name: "standard",
    rowHeight: "44px",
    cellPadding: "py-3 px-4",
    fontSize: "13px",
    purpose: "Workspaces, dashboards, settings panels",
  },
  relaxed: {
    name: "relaxed",
    rowHeight: "auto",
    cellPadding: "py-4 px-5",
    fontSize: "14px",
    lineHeight: "1.65",
    purpose: "Editorial reading, statutory clauses, executive briefings",
  },
} as const;

/**
 * Motion Tokens (Subtle, purposeful, non-distracting)
 */
export const motionTokens = {
  duration: {
    fast: "150ms",
    base: "200ms",
    slow: "350ms",
  },
  easing: {
    editorial: "cubic-bezier(0.16, 1, 0.3, 1)",
    subtle: "cubic-bezier(0.4, 0, 0.2, 1)",
  },
  transitions: {
    editorial: "all 200ms cubic-bezier(0.16, 1, 0.3, 1)",
    subtle: "all 150ms ease",
    fast: "all 150ms ease",
  },
} as const;

/**
 * Epistemic Classification Palette
 */
export const epistemicColors = {
  FACT: {
    dark: { text: "#34d399", bg: "rgba(16, 185, 129, 0.10)", border: "rgba(16, 185, 129, 0.25)" },
    light: { text: "#047857", bg: "rgba(5, 150, 105, 0.08)", border: "rgba(5, 150, 105, 0.30)" },
    description: "Official Gazette, Parliamentary record, or verified statutory clause",
  },
  OBSERVED: {
    dark: { text: "#38bdf8", bg: "rgba(14, 165, 233, 0.10)", border: "rgba(14, 165, 233, 0.25)" },
    light: { text: "#0369a1", bg: "rgba(2, 132, 199, 0.08)", border: "rgba(2, 132, 199, 0.30)" },
    description: "Historical market price, traded return, or recorded event timestamp",
  },
  DERIVED: {
    dark: { text: "#818cf8", bg: "rgba(99, 102, 241, 0.10)", border: "rgba(99, 102, 241, 0.25)" },
    light: { text: "#4338ca", bg: "rgba(79, 70, 229, 0.08)", border: "rgba(79, 70, 229, 0.30)" },
    description: "Econometric calculation, OLS market model residual, CAR, or t-statistic",
  },
  INTERPRETATION: {
    dark: { text: "#fbbf24", bg: "rgba(245, 158, 11, 0.10)", border: "rgba(245, 158, 11, 0.25)" },
    light: { text: "#b45309", bg: "rgba(217, 119, 6, 0.08)", border: "rgba(217, 119, 6, 0.30)" },
    description: "Grounded AI policy analysis, executive summary, or stakeholder assessment",
  },
  PREDICTION: {
    dark: { text: "#c084fc", bg: "rgba(168, 85, 247, 0.10)", border: "rgba(168, 85, 247, 0.25)" },
    light: { text: "#7e22ce", bg: "rgba(147, 51, 234, 0.08)", border: "rgba(147, 51, 234, 0.30)" },
    description: "Econometric event-study projection across the 5 authoritative horizons",
  },
  EVIDENCE: {
    dark: { text: "#2dd4bf", bg: "rgba(20, 184, 166, 0.10)", border: "rgba(20, 184, 166, 0.25)" },
    light: { text: "#0f766e", bg: "rgba(13, 148, 136, 0.08)", border: "rgba(13, 148, 136, 0.30)" },
    description: "Official publication, parliamentary bulletin, or corroborated news item",
  },
} as const;

/**
 * Dual-Theme Calibrated Semantic Tokens
 */
export const themeColors = {
  dark: {
    surfaces: {
      base: "#070b12",
      surface: "#0c1322",
      secondary: "#121b2f",
      card: "#0c1322",
      cardHover: "#121b2f",
      elevated: "#162035",
      nav: "rgba(7, 11, 18, 0.95)",
      modal: "#0c1322",
    },
    text: {
      primary: "#f8fafc",
      secondary: "#94a3b8",
      muted: "#64748b",
      faint: "#475569",
      inverse: "#0f172a",
      link: "#60a5fa",
    },
    actions: {
      primary: "#3b82f6",
      primaryHover: "#60a5fa",
      secondary: "#1e293b",
      secondaryHover: "#334155",
      focusRing: "#3b82f6",
      active: "#2563eb",
    },
    borders: {
      subtle: "rgba(255, 255, 255, 0.06)",
      default: "rgba(255, 255, 255, 0.10)",
      strong: "rgba(255, 255, 255, 0.18)",
      hairline: "rgba(255, 255, 255, 0.07)",
    },
    semantic: {
      positive: "#10b981",
      negative: "#f43f5e",
      warning: "#f59e0b",
      model: "#6366f1",
      state: "#0284c7",
      intel: "#06b6d4",
      ai: "#a855f7",
    },
    charts: {
      series1: "#60a5fa",
      series2: "#818cf8",
      series3: "#34d399",
      series4: "#f472b6",
      series5: "#fbbf24",
      series6: "#2dd4bf",
      positive: "#10b981",
      negative: "#f43f5e",
      neutral: "#94a3b8",
      grid: "rgba(255, 255, 255, 0.08)",
      axis: "rgba(255, 255, 255, 0.18)",
      zeroLine: "rgba(255, 255, 255, 0.30)",
      ciBand: "rgba(99, 102, 241, 0.14)",
    },
  },
  light: {
    surfaces: {
      base: "#f8fafc",
      surface: "#ffffff",
      secondary: "#f1f5f9",
      card: "#ffffff",
      cardHover: "#f8fafc",
      elevated: "#ffffff",
      nav: "rgba(255, 255, 255, 0.95)",
      modal: "#ffffff",
    },
    text: {
      primary: "#0f172a",
      secondary: "#334155",
      muted: "#64748b",
      faint: "#94a3b8",
      inverse: "#f8fafc",
      link: "#1d4ed8",
    },
    actions: {
      primary: "#2563eb",
      primaryHover: "#1d4ed8",
      secondary: "#e2e8f0",
      secondaryHover: "#cbd5e1",
      focusRing: "#2563eb",
      active: "#1e40af",
    },
    borders: {
      subtle: "rgba(15, 23, 42, 0.06)",
      default: "rgba(15, 23, 42, 0.12)",
      strong: "rgba(15, 23, 42, 0.22)",
      hairline: "rgba(15, 23, 42, 0.08)",
    },
    semantic: {
      positive: "#059669",
      negative: "#e11d48",
      warning: "#d97706",
      model: "#4f46e5",
      state: "#0284c7",
      intel: "#0891b2",
      ai: "#9333ea",
    },
    charts: {
      series1: "#2563eb",
      series2: "#4f46e5",
      series3: "#059669",
      series4: "#db2777",
      series5: "#d97706",
      series6: "#0d9488",
      positive: "#059669",
      negative: "#e11d48",
      neutral: "#64748b",
      grid: "rgba(15, 23, 42, 0.07)",
      axis: "rgba(15, 23, 42, 0.18)",
      zeroLine: "rgba(15, 23, 42, 0.30)",
      ciBand: "rgba(79, 70, 229, 0.10)",
    },
  },
} as const;

export default {
  fontFamilies,
  typographyScale,
  spacingScale,
  radiiScale,
  contentWidths,
  densityScale,
  motionTokens,
  epistemicColors,
  themeColors,
};

