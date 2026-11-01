# TASK 1.4 — SEANCE DATA VISUALIZATION, CHART SYSTEM & FINANCIAL DENSITY AUDIT

**Project Name:** Seance  
**Platform Full Title:** Legislative Bill Impact Prediction & Decision Intelligence Platform  
**Document Version:** 1.0.0  
**Audit Date:** October 10, 2026  
**Phase:** Phase 1 — Modernization Foundation  
**Task:** 1.4 — Data Visualization, Chart System & Financial Density Calibration  
**Frozen Baseline SHA-256:** `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7` (Verified Intact)  

---

## 1. Executive Summary

Task 1.4 focuses on standardizing Seance's charting system, econometric event-study representations, abnormal-return displays, and quantitative table presentations into a cohesive, accessible, dual-theme visualization framework.

Prior to this audit, data visualizations in Seance operated with:
1. Zero third-party chart dependencies (no Recharts, Chart.js, or D3 in `package.json`), relying on ad-hoc SVG fragments and HTML progress bars.
2. Inconsistent dark-only color encoding (`bg-slate-900`, `bg-slate-950`, `border-slate-800`, `bg-emerald-950`, etc.) that suffers low contrast or illegibility when toggled to Light mode.
3. Inconsistent financial typography, with numeric values alternating between proportional sans-serif and monospace, lacking universal tabular numeral alignment (`font-variant-numeric: tabular-nums`).
4. Event-horizon comparisons (`[-1,+1]` to `[-10,+10]`) rendered as flat text rows or segmented button strips without standard econometric trajectory or abnormal return visualization.
5. Ad-hoc browser native `title` tooltips or overflow-clipped tooltips lacking dual-theme styling and keyboard accessibility.

This audit establishes the blueprint for migrating all visualizations to semantic CSS tokens, introducing shared dual-theme chart primitives, standardizing financial formatting, and preserving all epistemic distinctions and production analytical invariants without altering analytical methodology or backend datasets.

---

## 2. Inventory of Existing Charting & Quantitative Surfaces

### 2.1 Dependencies and Charting Infrastructure
Inspection of `frontend/package.json` confirms:
- **Framework:** Next.js 16.3.5 (App Router with Turbopack).
- **Core Engine:** React 19.2.8 (`react`, `react-dom`).
- **Styling:** Tailwind CSS v4 with `@import "tailwindcss"`.
- **Chart Dependencies:** None. No external charting libraries are installed. All visualization primitives are zero-dependency SVG, CSS, and HTML components.
- **Decision:** In accordance with the mandate (*"Preserve existing chart libraries unless the audit identifies a concrete blocker"*), Seance will preserve its clean, zero-dependency SVG architecture. We will introduce a standardized, accessible SVG visualization suite in `frontend/components/charts/`.

### 2.2 Component-by-Component Visualization Inventory

| Component Path | Current Visual Mechanism | Econometric / Financial Scope | Identified Issues |
|---|---|---|---|
| `frontend/components/bills/CentralPredictionSection.tsx` | HTML table + modal drawer | Central bill quantitative predictions across 5 event windows (`[-1,+1]` to `[-10,+10]`) | Hardcoded slate dark classes (`bg-slate-900/90`, `bg-slate-950/40`, `border-slate-800`); lack of tabular numerals on confidence percentages; modal drawer has hardcoded dark styling. |
| `frontend/components/companies/CompanyPredictionsSection.tsx` | HTML table + window selector tabs | Listed company quantitative projections across event windows with market-moving classification | Hardcoded slate backgrounds (`bg-slate-900/50`, `bg-slate-850`); non-standardized probability percentage formatting; missing dual-theme tokens. |
| `frontend/components/companies/CompanyExposureMatrix.tsx` | Filterable table with exposure badges | Corporate legislative touchpoints, mechanisms, and direct/indirect vectors | Hardcoded slate backgrounds; table headers lack semantic theme tokens; relevance tags need consistent typography. |
| `frontend/components/bills/CorporateExposureTable.tsx` | High-density table with drawer | Verified corporate exposure mechanisms and directness | Partially migrated in Task 1.3, but lacks tabular numeral density and right-aligned metrics. |
| `frontend/app/predictions/PredictionsContent.tsx` | Tabbed filter matrix + horizon comparison panel | 4,700 Central event-study predictions; comparative event-window metrics | Horizon comparison rendered only as plain stat cards; unmodeled horizons (`[0,1]`, `[0,2]`, `[0,5]`) lack visual distinction; hardcoded dark styles throughout. |
| `frontend/app/predictions/[predictionId]/PredictionDetailContent.tsx` | Epistemic separation grid + horizon comparison cards | Single prediction detail with confidence, probability, risk metrics, and alternative horizons | Horizon comparison rendered as basic colored boxes; probability bar uses hardcoded `bg-amber-500` / `bg-slate-500`; hardcoded dark classes (`bg-slate-950`). |
| `frontend/app/risk/RiskContent.tsx` | 5-tier risk band cards + stacked proportional bar + portfolio table + profile tables | 5-tier deterministic risk model (`VERY_LOW` to `VERY_HIGH`), pricing-in absorption, event-window risk, sector risk dispersion | `RISK_BAND_COLORS` dictionary contains hardcoded dark classes (`bg-emerald-950/40`, etc.); stacked bar uses inline widths without dual-theme tooltips; portfolio table lacks tabular numerals. |
| `frontend/app/anticipation/AnticipationContent.tsx` | Stat cards + pre-event trading windows CAR breakdown + 940-pair diffusion matrix | Pre-event Cumulative Abnormal Returns (`mean_car`, `mean_mar`, `significant_pairs_count`) across pre-announcement windows | CAR metrics lack sign formatting (`+` / `-`); window stats lack visual distribution curve or bar representation; hardcoded dark styling (`bg-slate-950`, `bg-indigo-950/50`). |
| `frontend/components/anticipation/AnticipationEvidenceSection.tsx` | Evidence cards + signal metrics | Econometric signal metrics (`car_magnitude`, `z_score`, `volatility`) paired with public news evidence | Numeric scores lack tabular alignment; `car_magnitude` lacks basis points / percentage formatting; evidence credibility breakdown lacks visual density. |
| `frontend/components/industries/IndustryMarketIntelligence.tsx` | Metric breakdown cards + member predictions table | Industry aggregate projections across 5 event horizons | Hardcoded slate classes (`bg-slate-900`, `bg-slate-800`); positive/negative cards lack semantic token references. |
| `frontend/components/ui/InstitutionalTable.tsx` | Shared high-density data table primitive | Universal tabular display with sorting, keyboard navigation, and sticky header | Numeric formatting requires explicit `font-mono tabular-nums` enforcement and standardized right-alignment; missing variable density preset (`compact`, `dense`, `relaxed`). |

---

## 3. Detailed Audit of Hardcoded Styles, Tooltips, and Typography

### 3.1 Hardcoded Chart & Visual Colors
1. **Risk Bands (`RiskContent.tsx` lines 22-28)**:
   ```ts
   const RISK_BAND_COLORS = {
     VERY_LOW: { bg: "bg-emerald-950/40", text: "text-emerald-400", border: "border-emerald-800/60", bar: "bg-emerald-500" },
     LOW: { bg: "bg-blue-950/40", text: "text-blue-400", border: "border-blue-800/60", bar: "bg-blue-500" },
     MODERATE: { bg: "bg-amber-950/40", text: "text-amber-400", border: "border-amber-800/60", bar: "bg-amber-500" },
     HIGH: { bg: "bg-orange-950/40", text: "text-orange-400", border: "border-orange-800/60", bar: "bg-orange-500" },
     VERY_HIGH: { bg: "bg-rose-950/40", text: "text-rose-400", border: "border-rose-800/60", bar: "bg-rose-500" },
   };
   ```
   *Defect:* In Light mode, `bg-emerald-950/40` renders as an opaque near-black patch on light surfaces with near-invisible text (`text-emerald-400`). Must be migrated to semantic CSS variables with calibrated light/dark surface and text tokens.

2. **Prediction Directions & Returns**:
   - `CentralPredictionSection.tsx`: hardcoded `text-amber-400`, `text-rose-400`, `text-slate-400`.
   - `PredictionDetailContent.tsx`: hardcoded `text-emerald-400`, `text-rose-400`, `text-blue-400`, `text-amber-400`.
   - `AnticipationContent.tsx`: `text-emerald-400` when `ws.mean_car > 0`, `text-rose-400` when `ws.mean_car < 0`.

3. **Chart Grid & Axis Elements**:
   - Currently, there are no reusable grid and axis tokens referenced by visualizers. While `--chart-grid` and `--chart-axis` exist in `globals.css`, they are not connected to any component.
   - Specific token `--chart-axis-text` is missing in `globals.css`.

### 3.2 Tooltip Audit
- **Current State:** Visualizations rely predominantly on HTML `title="..."` attributes (e.g. `RiskContent.tsx` line 286: `title="${band}: ${count} (${pct.toFixed(1)}%)"`).
- **Defects:**
  * Browser native tooltips have delayed triggers (~700ms), cannot be styled, do not respect the active theme, cannot render rich financial metrics, and are inaccessible to screen readers or keyboard-only navigation.
  * In drawers and modals (`CentralPredictionSection.tsx`, `ContextDrawer.tsx`), any CSS tooltips with `overflow: hidden` on parent containers are clipped.
- **Requirement:** Implement a dedicated `ChartTooltip` component that supports custom rendering, instant hover/focus positioning, dual-theme semantic tokens (`--chart-tooltip-bg`, `--chart-tooltip-text`, `--chart-tooltip-border`), and collision detection to avoid viewport clipping.

### 3.3 Financial Typography & Alignment
- **Tabular Numerals:** Many numeric metrics (e.g., probability, confidence, risk score) are rendered with default proportional fonts (`font-sans` or standard `font-mono` without `tabular-nums`). When numbers change during filtering or updates, character widths fluctuate, disrupting column alignment.
- **Column Alignment:** Tables in `RiskContent.tsx`, `PredictionsContent.tsx`, and `CentralPredictionSection.tsx` left-align numeric columns (e.g. decisions count, risk score, confidence percentage) instead of aligning numbers right.
- **Precision & Rounding:**
  * Risk scores vary between `.toFixed(2)` and `.toFixed(3)` across components.
  * Probabilities vary between `(val * 100).toFixed(1)` and raw values.
  * Mean CAR and MAR vary between 2 and 4 decimal places.
  * Missing values: rendered variously as `"0"`, `"0.00"`, `"null"`, `"N/A"`, or `"—"`.
- **Sign Conventions:** Cumulative Abnormal Returns (CAR) do not consistently show the explicit plus sign (`+`) for positive returns, reducing scan speed in quantitative event-study evaluation.

---

## 4. Semantic Visualization Tokens Architecture

### 4.1 Token Mapping & Standardization in `frontend/app/globals.css`

The following semantic visualization tokens are defined for both Dark (baseline default) and Light themes:

| Semantic CSS Token | Role & Description | Dark Theme Value | Light Theme Value |
|---|---|---|---|
| `--color-positive` | Positive abnormal return, favorable movement | `#10b981` (Emerald 500) | `#059669` (Emerald 600) |
| `--color-negative` | Negative abnormal return, adverse movement | `#f43f5e` (Rose 500) | `#e11d48` (Rose 600) |
| `--color-model` | Model-derived estimate, forecast, or prediction | `#6366f1` (Indigo 500) | `#4f46e5` (Indigo 600) |
| `--chart-grid` | Gridlines, tick guides, background reference grid | `rgba(255, 255, 255, 0.08)` | `rgba(15, 23, 42, 0.07)` |
| `--chart-axis` | Axis baseline line and ruler border | `rgba(255, 255, 255, 0.18)` | `rgba(15, 23, 42, 0.18)` |
| `--chart-axis-text` | Axis tick values, category labels, unit labels | `#94a3b8` (Slate 400) | `#64748b` (Slate 500) |
| `--chart-border` | Chart container boundary and divider | `rgba(255, 255, 255, 0.10)` | `rgba(15, 23, 42, 0.12)` |
| `--chart-tooltip-bg` | Floating chart tooltip background surface | `#0c1322` (Elevated Navy) | `#ffffff` (Pure White) |
| `--chart-tooltip-text` | Primary tooltip typography | `#f8fafc` (Slate 50) | `#0f172a` (Slate 900) |
| `--chart-tooltip-border` | Tooltip elevation border | `rgba(255, 255, 255, 0.15)` | `rgba(15, 23, 42, 0.14)` |
| `--chart-observed` | Realized historical price / observable facts | `#38bdf8` (Sky 400) | `#0284c7` (Sky 600) |
| `--chart-reference` | Benchmark line, zero return axis, baseline | `#94a3b8` (Slate 400) | `#64748b` (Slate 500) |
| `--chart-zero-line` | Zero-return horizontal benchmark separator | `rgba(255, 255, 255, 0.30)` | `rgba(15, 23, 42, 0.30)` |
| `--chart-ci-band` | Econometric confidence interval shaded band | `rgba(99, 102, 241, 0.14)` | `rgba(79, 70, 229, 0.10)` |

### 4.2 Non-Color Indicator Guarantees
To prevent reliance on color alone (WCAG 2.2 AA / AAA):
1. **Directional Metrics:** All positive/negative return indicators pair colors with text labels (`+4.20%` / `-1.15%`), directional glyphs (`▲` / `▼`), and explicit badges (`POSITIVE` / `NEGATIVE` / `NEUTRAL`).
2. **Observed vs Predicted Series:**
   - Realized/observed series use solid line strokes (`stroke-dasharray="none"`) and circular vertex markers (`●`).
   - Model predictions use dashed line strokes (`stroke-dasharray="4 3"`) and diamond vertex markers (`◆`).
3. **Epistemic Labeling:** Visualizations display explicit badges: `[OBSERVED]`, `[PREDICTION]`, `[DERIVED]`.
4. **Epistemic Neutrality:** Clear institutional disclosure that market movement does not equate to societal or public welfare benefit.

---

## 5. Standard Chart Primitives to Introduce

To eliminate duplicated ad-hoc visualization fragments, the following reusable components will be created under `frontend/components/charts/`:

### 5.1 `ChartContainer.tsx`
- Responsive SVG/HTML wrapper with title, subtitle, epistemic classification badge, time window, and interactive legend.
- Handles responsive aspect ratios, auto-resizing, and accessible labels (`role="figure"`, `aria-label`).
- Standardized empty (`No econometric observations available`), loading (animated skeleton shimmer), and error states.

### 5.2 `ChartTooltip.tsx`
- Accessible, collision-aware tooltip positioning using dual-theme tokens.
- Supports tabular values, epistemic category tags, and timestamps.
- Zero viewport clipping when embedded inside drawers or tables.

### 5.3 `EventStudyChart.tsx`
- Visualizes multi-horizon event-study return trajectories across the authoritative 5 horizons (`[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`) or pre-event windows (`[-30,-1]`, `[-5,-1]`).
- Clear visual delineation of T0 (announcement date), pre-event window, and post-event window.
- Distinguishes observed historical return paths from model-generated estimates.
- Standardized zero-return benchmark line (`--chart-zero-line`).

### 5.4 `HorizonComparisonVisualizer.tsx`
- Interactive comparison matrix for bill-company pairs across horizons.
- Visualizes modeled vs unmodeled horizons with distinct styles.
- Shows directional probability breakdown with tabular percentages.

### 5.5 `RiskDistributionBar.tsx`
- Visualizes multi-tier risk distributions (e.g. 5-tier deterministic risk model in `/risk`).
- Dual-theme calibrated colors for `VERY_LOW`, `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`.
- Interactive hover/focus tooltips for each segment with tabular counts and percentages.

### 5.6 `PreEventCarChart.tsx`
- Visualizes pre-event trading window CAR (Cumulative Abnormal Return) statistics and MAR (Mean Abnormal Return) from `/anticipation`.
- Formatted percentages with sign indicators (`+` / `-`).

---

## 6. Financial Formatting & Density Standard (`frontend/lib/formatters.ts`)

A centralized, pure, unit-tested financial and quantitative formatting module will be created:

| Formatter Function | Input Example | Output Example | Fallback / Missing |
|---|---|---|---|
| `formatPercent(val, decimals, sign)` | `0.0425`, `2`, `true` | `+4.25%` | `—` |
| `formatPercent(val, decimals, sign)` | `-0.018`, `2`, `true` | `-1.80%` | `—` |
| `formatBps(val)` | `0.0075` | `+75 bps` | `—` |
| `formatCAR(val)` | `0.0341` | `+3.41% CAR` | `—` |
| `formatZScore(val)` | `2.341` | `z = 2.34` | `—` |
| `formatProbability(val)` | `0.654` | `65.4%` | `—` |
| `formatRiskScore(val)` | `0.452` | `0.452` | `—` |
| `formatCurrencyINR(val)` | `12500000` | `₹1,25,00,000` | `—` |
| `formatInteger(val)` | `4700` | `4,700` | `0` |
| `formatEventWindow(win)` | `"[-1,+1]"` | `[-1, +1]` | `—` |

**Table Density Standardization:**
- Update `InstitutionalTable.tsx` to support `density="dense" | "compact" | "normal"`.
- Ensure all numeric cells render with `font-mono tabular-nums text-right`.
- Preserve existing sorting, filtering, selection, and keyboard navigation.

---

## 7. Epistemic and Analytical Invariants

The following invariants are inviolable and will be verified throughout implementation:

1. **Frozen Production Baseline:**
   - Manifest: `docs/production_baseline.json`
   - Canonical SHA-256: `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`
   - Must remain 100% bit-for-bit unchanged.
2. **Statutory Firewalls:**
   - State prediction firewall: strictly **0** state stock predictions.
   - Intelligence company firewall: non-quant entities strictly barred from stock forecasts.
3. **Authoritative Analytical Universe:**
   - 20 Central production bills.
   - 47 quantitative securities.
   - 940 bill-company pairs.
   - 4,700 predictions and 4,700 decisions.
   - 940 anticipation scores.
   - 14,100 stakeholder reports.
   - 5 authoritative event horizons: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`.
4. **Epistemic Classifications:**
   - `[FACT]`: verified legislative and corporate facts.
   - `[OBSERVED]`: realized historical market returns.
   - `[DERIVED]`: systemic risk calculations and composite indices.
   - `[INTERPRETATION]`: stakeholder synthesis briefs.
   - `[PREDICTION]`: forward-looking econometric event-study outputs.
   - `[EVIDENCE]`: verified pre-event public disclosures.

---

## 8. Mapping of Changes to Components and Tests

| Component / File | Planned Changes | Associated Tests |
|---|---|---|
| `frontend/app/globals.css` | Add `--chart-axis-text`, `--chart-border`, `--chart-observed`, `--chart-reference`, `--chart-zero-line`, `--chart-ci-band` to `:root`, `[data-theme="dark"]`, and `[data-theme="light"]`. | `__tests__/theme/theme-foundation.test.tsx` |
| `frontend/lib/formatters.ts` (NEW) | Create institutional financial formatters: percentages, bps, CAR, z-score, probabilities, risk scores, currencies, tabular numerals. | `__tests__/lib/formatters.test.ts` (NEW) |
| `frontend/components/charts/ChartContainer.tsx` (NEW) | Reusable dual-theme chart container with epistemic badge, legend, empty/loading/error states. | `__tests__/charts/chart-components.test.tsx` (NEW) |
| `frontend/components/charts/ChartTooltip.tsx` (NEW) | Non-clipping, dual-theme, accessible floating chart tooltip primitive. | `__tests__/charts/chart-components.test.tsx` (NEW) |
| `frontend/components/charts/EventStudyChart.tsx` (NEW) | Multi-horizon econometric trajectory and abnormal return SVG chart with observed vs predicted styling. | `__tests__/charts/chart-components.test.tsx` (NEW) |
| `frontend/components/charts/HorizonComparisonVisualizer.tsx` (NEW) | Dual-theme horizon comparison card strip/matrix with modeled vs unmodeled status. | `__tests__/charts/chart-components.test.tsx` (NEW) |
| `frontend/components/charts/RiskDistributionVisualizer.tsx` (NEW) | 5-tier deterministic risk model bar and distribution visualizer using semantic tokens. | `__tests__/charts/chart-components.test.tsx` (NEW) |
| `frontend/components/charts/PreEventCarChart.tsx` (NEW) | Pre-event trading windows CAR statistics visualizer with dual-theme formatting. | `__tests__/charts/chart-components.test.tsx` (NEW) |
| `frontend/components/ui/InstitutionalTable.tsx` | Enhanced density presets (`dense`, `compact`, `normal`), strict `font-mono tabular-nums` for numeric cells, right alignment. | `__tests__/components/shared-components.test.tsx` |
| `frontend/components/bills/CentralPredictionSection.tsx` | Migrate table, decision modal, and horizon metrics to semantic tokens, formatters, and tabular numerals. | `__tests__/pages/bill-detail.test.tsx` |
| `frontend/app/predictions/PredictionsContent.tsx` | Integrate `HorizonComparisonVisualizer`, semantic tokens, tabular numerals, and formatters. | `__tests__/pages/predictions.test.tsx` |
| `frontend/app/predictions/[predictionId]/PredictionDetailContent.tsx` | Integrate `EventStudyChart` / `HorizonComparisonVisualizer`, semantic tokens, and tabular numbers. | `__tests__/pages/prediction-detail.test.tsx` |
| `frontend/app/risk/RiskContent.tsx` | Migrate `RISK_BAND_COLORS` to semantic tokens, integrate `RiskDistributionVisualizer`, right-align numeric table columns with tabular numbers. | `__tests__/pages/risk.test.tsx` |
| `frontend/app/anticipation/AnticipationContent.tsx` | Integrate `PreEventCarChart`, format CAR/MAR with sign, right-align table numbers with tabular numerals. | `__tests__/pages/anticipation.test.tsx` |
| `frontend/components/companies/CompanyPredictionsSection.tsx` | Migrate table and event-window tabs to semantic tokens and tabular numerals. | `__tests__/pages/company-detail.test.tsx` |
| `frontend/components/industries/IndustryMarketIntelligence.tsx` | Migrate metric cards and sample predictions table to semantic tokens and tabular numerals. | `__tests__/pages/industry-detail.test.tsx` |

---

## 9. Record of Ambiguous or Missing Requirements

1. **Unmodeled Horizons Handling:**
   - Horizons `[0,1]`, `[0,2]`, and `[0,5]` are explicitly marked as "unmodeled" in the frozen backend dataset. The visualization system will display them with clear disabled styling and explanatory tooltip ("Unmodeled horizon; event-study baseline utilizes symmetric pre/post event windows") rather than omitting them or generating synthetic values.
2. **Confidence Intervals:**
   - Confidence intervals are not present on individual pair point predictions in the frozen dataset (only point probabilities and impact tiers exist). Per task instructions (*"Do not add confidence intervals... if the underlying data does not provide them"*), we will not invent confidence interval bounds for individual predictions.
3. **Positive Market Movement vs Public Benefit:**
   - Clear epistemic notice must accompany all market movement visuals stating that market movement reflects equity price sensitivity and does not imply public policy success or consumer benefit.

---

## 10. Audit Sign-Off

The audit is complete. Application source code modification will proceed in structured phases adhering to the mapped components, semantic tokens, and analytical invariants documented above.
