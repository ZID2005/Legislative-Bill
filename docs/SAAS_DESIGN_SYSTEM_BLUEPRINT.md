# MODERN SAAS DESIGN SYSTEM BLUEPRINT
## India Legislative Intelligence & Market Impact Platform
**Document Version:** 1.0.0  
**Status:** Architecture Specification & Redesign Blueprint  
**Execution Gate:** READ-ONLY SPECIFICATION (No source files modified).

---

## 1. Design Philosophy: Modern Enterprise SaaS

The platform must evolve from its current "AI dashboard template" aesthetic into a **Modern Enterprise SaaS** product. The design philosophy embodies four pillars:

1. **Restrained Editorial Authority:** The interface prioritizes institutional trust over decorative flourishes. It takes inspiration from products like **Linear**, **Stripe**, **Vercel**, and institutional terminals (**Bloomberg Law**, **FactSet**), balancing high data density with generous negative space and visual hierarchy.
2. **Epistemic Clarity:** Every analytical signal must be unambiguously classified. The system visually segregates confirmed statutory facts from econometrically derived estimates, qualitative intelligence, and speculative commentary.
3. **Dual-Theme Equivalence:** Light and Dark modes are designed as first-class citizens with equal contrast calibration, harmonious palettes, and zero inverted color artifacts.
4. **Purposeful Interaction:** Eliminates arbitrary visual noise (such as 120px blurred gradient spheres, emojis, and uncoordinated glowing borders). Introduces tactile micro-interactions (keyboard navigation, instant command palettes, crisp drawers, and smooth transitions).

---

## 2. Typography System

### 2.1 Font Families
- **Primary Interface Font:** `Inter` (Google Fonts via `next/font/google`). Clean, highly legible neutral grotesque sans-serif with excellent micro-kerning and optical sizing.
- **Quantitative & Monospace Font:** `JetBrains Mono` or `SF Mono`. Monospace font optimized for tabular figures, statutory citation codes, ISINs, and event study windows (`[-1,+1]`).

### 2.2 Numerical Legibility & Tabular Figures
All financial figures, event window estimates, p-values, t-statistics, and dates must use:
```css
font-variant-numeric: tabular-nums lining-nums;
```
This guarantees strict vertical column alignment across rows and tables without jitter.

### 2.3 Type Scale & Hierarchy

| Token | CSS Size / Leading | Weight | Tracking | Usage |
|---|---|---|---|---|
| `display` | `2.25rem (36px)` / `1.15` | `700` (Bold) | `-0.03em` | Major page hero statements (Landing, Overview) |
| `headline-1` | `1.75rem (28px)` / `1.20` | `600` (Semibold) | `-0.025em` | Primary workspace headers (`/workspace`, `/portfolio`) |
| `headline-2` | `1.375rem (22px)` / `1.25` | `600` (Semibold) | `-0.02em` | Section headers, Dossier titles |
| `title` | `1.0625rem (17px)` / `1.35` | `600` (Semibold) | `-0.015em` | Card titles, drawer headers, dialog titles |
| `subheading` | `0.875rem (14px)` / `1.40` | `500` (Medium) | `-0.01em` | Table column groups, secondary module headers |
| `body` | `0.8125rem (13px)` / `1.50` | `400` (Regular) | `0` | Primary table cells, statutory summaries, dossier copy |
| `body-sm` | `0.75rem (12px)` / `1.45` | `400` (Regular) | `0` | Metadata labels, helper copy, timestamp stamps |
| `caption` | `0.6875rem (11px)` / `1.35` | `500` (Medium) | `+0.02em` | Table headers, epistemic subtext, breadcrumbs |
| `micro` | `0.625rem (10px)` / `1.20` | `700` (Bold) | `+0.08em` | Epistemic badges, firewall stamps, ticker pills |

---

## 3. Semantic Design Tokens & Dual-Theme Color Palette

To avoid hardcoded Tailwind colors (`bg-slate-950`, `text-slate-400`), the entire styling system will transition to CSS Custom Properties organized under semantic tokens.

### 3.1 Token Matrix (Dark vs. Light)

```css
/* Proposed Semantic Color Architecture */
:root, [data-theme="dark"] {
  /* Surface Geometry */
  --color-page-bg:           #080c14;  /* Deep Institutional Navy-Black */
  --color-surface-base:      #0d131f;  /* Primary Card / Table Surface */
  --color-surface-raised:    #121b2b;  /* Elevated Popover / Drawer Surface */
  --color-surface-hover:     #172235;  /* Hover State for Rows and Cards */
  --color-surface-active:    #1c2940;  /* Active Selection State */

  /* Hairline Precision Borders */
  --color-border-subtle:     rgba(255, 255, 255, 0.06);
  --color-border-default:    rgba(255, 255, 255, 0.10);
  --color-border-strong:     rgba(255, 255, 255, 0.18);
  --color-border-focus:      #3b82f6;

  /* Typography */
  --color-text-primary:      #f8fafc;  /* Maximum Contrast Copy */
  --color-text-secondary:    #94a3b8;  /* Supporting Analytical Text */
  --color-text-muted:        #64748b;  /* Column Headers, Footnotes */
  --color-text-faint:        #475569;  /* Inactive Toggles, Watermarks */

  /* Semantic Brand & Accents */
  --color-brand-primary:     #3b82f6;  /* Institutional Blue */
  --color-brand-primary-fg:  #ffffff;
  --color-brand-glow:        rgba(59, 130, 246, 0.12);

  /* Financial & Epistemic Semantics */
  --color-positive:          #10b981;  /* Positive CAR / Enacted Law */
  --color-positive-bg:       rgba(16, 185, 129, 0.10);
  --color-positive-border:   rgba(16, 185, 129, 0.25);

  --color-negative:          #f43f5e;  /* Negative CAR / High Vulnerability */
  --color-negative-bg:       rgba(244, 63, 94, 0.10);
  --color-negative-border:   rgba(244, 63, 94, 0.25);

  --color-warning:           #f59e0b;  /* Interpretation / Assent Pending */
  --color-warning-bg:        rgba(245, 158, 11, 0.10);
  --color-warning-border:    rgba(245, 158, 11, 0.25);

  --color-intel:             #06b6d4;  /* State Acts / Corporate Intel */
  --color-intel-bg:          rgba(6, 182, 212, 0.10);
  --color-intel-border:      rgba(6, 182, 212, 0.25);

  --color-ai:                #8b5cf6;  /* Groq AI Citations & Analyst */
  --color-ai-bg:             rgba(139, 92, 246, 0.10);
  --color-ai-border:         rgba(139, 92, 246, 0.25);
}

[data-theme="light"] {
  /* Surface Geometry */
  --color-page-bg:           #f8fafc;  /* Crisp Off-White */
  --color-surface-base:      #ffffff;  /* Pure White Container */
  --color-surface-raised:    #f1f5f9;  /* Elevated Card / Popover */
  --color-surface-hover:     #f8fafc;  /* Row Hover State */
  --color-surface-active:    #e2e8f0;  /* Active Tab / Button */

  /* Hairline Precision Borders */
  --color-border-subtle:     rgba(0, 0, 0, 0.05);
  --color-border-default:    rgba(0, 0, 0, 0.09);
  --color-border-strong:     rgba(0, 0, 0, 0.16);
  --color-border-focus:      #2563eb;

  /* Typography */
  --color-text-primary:      #0f172a;  /* Maximum Contrast Ink */
  --color-text-secondary:    #475569;  /* Supporting Analytical Text */
  --color-text-muted:        #64748b;  /* Column Headers, Footnotes */
  --color-text-faint:        #94a3b8;  /* Inactive Toggles */

  /* Semantic Brand & Accents */
  --color-brand-primary:     #2563eb;  /* Strong Enterprise Blue */
  --color-brand-primary-fg:  #ffffff;
  --color-brand-glow:        rgba(37, 99, 235, 0.08);

  /* Financial & Epistemic Semantics */
  --color-positive:          #059669;
  --color-positive-bg:       rgba(5, 150, 105, 0.08);
  --color-positive-border:   rgba(5, 150, 105, 0.22);

  --color-negative:          #e11d48;
  --color-negative-bg:       rgba(225, 29, 72, 0.08);
  --color-negative-border:   rgba(225, 29, 72, 0.22);

  --color-warning:           #d97706;
  --color-warning-bg:        rgba(217, 119, 6, 0.08);
  --color-warning-border:    rgba(217, 119, 6, 0.22);

  --color-intel:             #0891b2;
  --color-intel-bg:          rgba(8, 145, 178, 0.08);
  --color-intel-border:      rgba(8, 145, 178, 0.22);

  --color-ai:                #7c3aed;
  --color-ai-bg:             rgba(124, 58, 237, 0.08);
  --color-ai-border:         rgba(124, 58, 237, 0.22);
}
```

---

## 4. Epistemic Taxonomy & Data Status Badges

The platform's core identity rests on scientific rigor. Decorative badges must be replaced with the standardized 5-tier Epistemic Taxonomy and 4-tier Modeling Level system.

### 4.1 Epistemic Taxonomy
Every piece of quantitative or qualitative insight is labelled:

| Epistemic Tag | Meaning | Dark Theme Appearance | Light Theme Appearance |
|---|---|---|---|
| `[FACT]` | Verified parliamentary record, official gazette, enacted section. | Emerald text, 10% emerald background, 25% border. | Deep emerald text, 8% emerald background. |
| `[OBSERVED]` | Empirical market prices (NSE/BSE), trading volumes, dates. | Sky text, 10% sky background, 25% border. | Slate-sky text, 8% sky background. |
| `[DERIVED]` | Statistical aggregations, sector exposure counts, risk deciles. | Indigo text, 10% indigo background, 25% border. | Royal indigo text, 8% indigo background. |
| `[INTERPRETATION]` | Legal provisions summary, qualitative commentary. | Amber text, 10% amber background, 25% border. | Warm amber text, 8% amber background. |
| `[PREDICTION]` | Econometric event study outputs, CAR predictions, confidence bounds. | Purple text, 10% purple background, 25% border. | Deep purple text, 8% purple background. |

### 4.2 Modeling Status Taxonomy
Distinguishes econometric eligibility across Central acts and State acts:

| Badge | Application | Invariant Guarantee |
|---|---|---|
| `LIVE` | Automated unmodelled intake feed (`/live-discovery`, `/latest-bills`). | Strictly unmodelled; `isInAnalyticalModel = false`. |
| `MODELLED` | Central bills & quantitative securities (`/predictions`). | Immutable econometric baseline (SHA-256 protected). |
| `INTELLIGENCE` | State acts & intelligence-only corporations (`/states`, `/companies`). | **Zero stock predictions**; qualitative compliance only. |
| `PLANNED` | 24 expansion states under research. | Explicitly non-production; zero active datasets. |

---

## 5. UI Component Conventions

### 5.1 Tables (`InstitutionalTable.tsx`)
- **Density:** Default 36px row height with optional dense mode (28px).
- **Sticky Headers:** Top headers stick to `top-14` with solid surface background and bottom hairline border (`--color-border-default`).
- **Row Hover:** Subtle transition (`var(--color-surface-hover)`), zero horizontal shift.
- **Sorting:** Clean chevron indicators; instant client-side sort without page reload.

### 5.2 Context Drawers (`ContextDrawer.tsx`)
- Replaces cramped modal popups and deep page scrolling.
- Fixed 480px width on desktop (100% on mobile).
- Mounts at `z-50` with backdrop blur, focus trapping, and `Escape` key dismissal.
- Used for: Company Tear-Sheets, Bill Key Provisions, Source Inspection, and AI Citations.

### 5.3 Command Palette (`CommandPalette.tsx`)
- Trigger: `⌘K` (Mac) or `Ctrl+K` (Windows/Linux) or top navbar search button.
- Width: Max 640px, centered vertically at 20% viewport top.
- Keyboard navigation: Arrow keys to select, `Enter` to navigate, `Esc` to close.
- Categories: Bills, Companies, Sectors, States, Navigation Actions, AI Prompts.

### 5.4 Input Fields & Form Controls
- Height: 36px standard, 32px compact.
- Surface: `var(--color-surface-base)` with `1px solid var(--color-border-default)`.
- Focus Ring: High-contrast 2px blue ring (`--color-border-focus`) with 2px offset.
- Placeholders: Muted text (`var(--color-text-muted)`) with high-contrast text when filled.

---

## 6. Layout Grid, Max Widths & Responsive Breakpoints

The application shell adapts to modern enterprise screen resolutions:

```
Breakpoint Matrix:
- Mobile:      < 640px    (Single column, bottom navigation bar or top hamburger)
- Tablet:      640-1023px (2-column responsive grid, compact top bar)
- Desktop:     1024-1439px (12-column grid, max-w-7xl, full top navigation bar)
- Ultrawide:   ≥ 1440px   (16-column grid or max-w-[1600px] container, high-density tables)
```

- **Container Constraint:** Analytical workspaces use a consistent max container width:
  ```css
  max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8
  ```
- **Consistent Gutter:** 16px on mobile, 24px on tablet, 32px on desktop.

---

## 7. Design System Reference Matrix

| Feature | Anti-Pattern (Current) | Modern SaaS Pattern (Proposed) | Industry Reference |
|---|---|---|---|
| **Header Identity** | Raw emoji `⚖` + unstyled bold text | Precision vector mark + refined tracking typography | Linear, Stripe |
| **Color Semantics** | Hardcoded `#05090f` + generic purple glows | CSS custom property tokens with light/dark symmetry | Vercel, Tailwind v4 |
| **Data Presentation** | Repetitive rounded cards with heavy borders | High-density tables, divider lines, progressive drawers | Bloomberg Law, PitchBook |
| **Icons** | Emojis (`📜`, `📈`, `🏢`, `🔍`, `✦`) | Consistent 16px inline SVG vector iconography | Lucide / Custom SVG |
| **Search & Discovery** | Hidden dropdowns / bulky search bars | Global Command Palette (`⌘K`) with fuzzy match | Raycast, Linear |
| **Information Density** | Giant hero areas, unnecessary whitespace | Tight, information-rich, progressive disclosure | FactSet, Stripe Dashboard |
| **Interactive States** | Heavy glowing drop shadows | Hairline border shifts, subtle surface elevations | Tailwind UI, Linear |
