/**
 * lib/formatters.ts
 * ==================
 * Institutional Financial, Econometric & Quantitative Numeric Formatters for Seance.
 *
 * Implements:
 * - High-precision financial metrics: CAR, MAR, bps, z-scores, p-values, probabilities.
 * - Non-color glyph indicators (▲ / ▼ / ■) paired with sign encoding (+ / -).
 * - Standardized missing value representations ("—") preserving epistemic truth.
 * - Tabular numeral compatibility with font-variant-numeric: tabular-nums.
 *
 * Compliance Invariant:
 * - Never silently alters financial calculation inputs or signs.
 * - Strictly presents data as formatted strings for display.
 */

export interface FormatPercentOptions {
  decimals?: number;
  showSign?: boolean;
  fallback?: string;
  isRatio?: boolean; // if true, 0.05 => 5%. If false, 5 => 5%. Default true.
}

/**
 * Format a decimal or ratio as an institutional percentage string.
 * @example formatPercent(0.0425) => "+4.25%" (when showSign true)
 * @example formatPercent(-0.018) => "-1.80%"
 */
export function formatPercent(
  value: number | null | undefined,
  options: FormatPercentOptions = {}
): string {
  const { decimals = 2, showSign = false, fallback = "—", isRatio = true } = options;

  if (value === null || value === undefined || isNaN(Number(value))) {
    return fallback;
  }

  const num = Number(value);
  const pct = isRatio ? num * 100 : num;
  const fixed = pct.toFixed(decimals);

  if (showSign && pct > 0) {
    return `+${fixed}%`;
  }
  return `${fixed}%`;
}

/**
 * Format Cumulative Abnormal Return (CAR).
 * Always includes sign when non-zero.
 * @example formatCAR(0.0412) => "+4.12%"
 * @example formatCAR(-0.0215) => "-2.15%"
 */
export function formatCAR(
  value: number | null | undefined,
  decimals: number = 2,
  includeSuffix: boolean = false
): string {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return "—";
  }

  const formatted = formatPercent(value, { decimals, showSign: true, isRatio: true });
  return includeSuffix ? `${formatted} CAR` : formatted;
}

/**
 * Format Mean Abnormal Return (MAR).
 * High precision (typically 3 decimals).
 */
export function formatMAR(
  value: number | null | undefined,
  decimals: number = 3
): string {
  return formatPercent(value, { decimals, showSign: true, isRatio: true });
}

/**
 * Format basis points (bps). 1 bp = 0.0001 (0.01%).
 * @example formatBps(0.0075) => "+75 bps"
 */
export function formatBps(
  value: number | null | undefined,
  showSign: boolean = true
): string {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return "—";
  }

  const bps = Math.round(Number(value) * 10000);
  if (showSign && bps > 0) {
    return `+${bps} bps`;
  }
  return `${bps} bps`;
}

/**
 * Format econometric z-score.
 * @example formatZScore(2.341) => "z = 2.34"
 */
export function formatZScore(
  value: number | null | undefined,
  prefix: boolean = true,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return "—";
  }

  const fixed = Number(value).toFixed(decimals);
  return prefix ? `z = ${fixed}` : fixed;
}

/**
 * Format statistical p-value.
 * @example formatPValue(0.0004) => "p < 0.001"
 * @example formatPValue(0.034) => "p = 0.034"
 */
export function formatPValue(
  value: number | null | undefined,
  decimals: number = 3
): string {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return "—";
  }

  const p = Number(value);
  if (p < 0.001) {
    return "p < 0.001";
  }
  return `p = ${p.toFixed(decimals)}`;
}

/**
 * Format model or market probability (0.00 to 1.00 => 0.0% to 100.0%).
 */
export function formatProbability(
  value: number | null | undefined,
  decimals: number = 1
): string {
  return formatPercent(value, { decimals, showSign: false, isRatio: true });
}

/**
 * Format systemic or decision risk score (typically 0.00 to 1.00 or 0 to 100).
 */
export function formatRiskScore(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return "—";
  }
  return Number(value).toFixed(decimals);
}

/**
 * Format standard integer with Indian/international grouping.
 */
export function formatInteger(
  value: number | null | undefined,
  fallback: string = "0"
): string {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return fallback;
  }
  return new Intl.NumberFormat("en-IN").format(Math.round(Number(value)));
}

/**
 * Format Indian Rupee currency (INR).
 */
export function formatCurrencyINR(
  value: number | null | undefined,
  fallback: string = "—"
): string {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return fallback;
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

/**
 * Format event window string consistently with institutional spacing.
 * @example formatEventWindow("[-1,+1]") => "[-1, +1]"
 */
export function formatEventWindow(windowStr: string | null | undefined): string {
  if (!windowStr) return "—";
  return windowStr.replace(/,/g, ", ").replace(/\s+/g, " ").trim();
}

/**
 * Non-color directional indicator glyph.
 * Fulfills accessibility requirement: Do not use color as only indicator.
 */
export function getDirectionGlyph(
  valueOrDirection: number | string | null | undefined
): string {
  if (valueOrDirection === null || valueOrDirection === undefined) return "";
  if (typeof valueOrDirection === "number") {
    if (valueOrDirection > 0) return "▲";
    if (valueOrDirection < 0) return "▼";
    return "■";
  }
  const dir = String(valueOrDirection).toUpperCase();
  if (dir === "POSITIVE" || dir === "UP") return "▲";
  if (dir === "NEGATIVE" || dir === "DOWN") return "▼";
  return "■";
}

/**
 * Returns the CSS semantic color variable for a numeric return or direction string.
 */
export function getSemanticColorToken(
  valueOrDirection: number | string | null | undefined
): string {
  if (valueOrDirection === null || valueOrDirection === undefined) {
    return "var(--text-muted)";
  }
  if (typeof valueOrDirection === "number") {
    if (valueOrDirection > 0) return "var(--color-positive)";
    if (valueOrDirection < 0) return "var(--color-negative)";
    return "var(--color-neutral)";
  }
  const dir = String(valueOrDirection).toUpperCase();
  if (dir === "POSITIVE" || dir === "UP") return "var(--color-positive)";
  if (dir === "NEGATIVE" || dir === "DOWN") return "var(--color-negative)";
  return "var(--color-neutral)";
}
