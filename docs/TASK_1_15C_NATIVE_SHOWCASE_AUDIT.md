# TASK 1.15C — SEANCE NATIVE ANIMATED INTELLIGENCE SHOWCASE AUDIT

## 1. Executive Summary & Objective

**Task 1.15C** upgrades the Seance eight-stage immersive onboarding showcase from a screenshot-based visual presentation to a **native, animated intelligence frontend showcase** built from actual React components, CSS compositions, SVG graphics, animated charts, data visualizations, legislative timelines, exposure networks, and interface elements.

The previous Task 1.15B implementation established:
- A deep charcoal / near-black visual foundation (`#080808` canvas, `#252525` outer frame, `#111111` inner surface, `#161616` / `#191919` elevated cards).
- 60/40 showcase-dominant desktop composition (`lg:col-span-7` vs `lg:col-span-5`).
- True spring-physics direction-aware transitions (`cubic-bezier(0.16, 1, 0.3, 1)`).
- Layered interactive hover depth.

However, the primary visual assets inside the `FeatureCarousel` remained static screenshots (`stage1_bill_dossier.png`, `stage1_statutory_mechanics.png`, etc.).

**Mission**: Eliminate dependency on screenshots as primary showcase visual assets. Replace them with eight high-fidelity, native React visual compositions representing an institutional intelligence terminal while preserving the existing eight-step onboarding workflow, multi-tenant persistence, form validation, and backend functionality.

---

## 2. Component & Architecture Inventory

### 2.1 FeatureCarousel Architecture (`frontend/components/ui/feature-carousel.tsx`)
- **Outer Shell**: Large rounded container with `#252525` hairline border and `#111111` inner surface.
- **Top Header**: Tag counter (`STAGE 01 · FOUNDATION`, etc.) and step indicators (`01 / 08`).
- **Stage Container**: Aspect-ratio bounded display area (`max-w-[560px] aspect-[16/10]`).
- **Footer**: Metadata description, active metrics pills, and interactive step tabs.
- **Physics Engine**: CSS keyframe animations `fcPrimaryInForward`, `fcPrimaryInBackward`, `fcSecondaryInForward`, `fcSecondaryInBackward` using `cubic-bezier(0.16, 1, 0.3, 1)` easing with 550ms/650ms durations.
- **Reduced Motion Support**: `@media (prefers-reduced-motion: reduce)` disables multi-axis transforms and falls back to clean opacity transitions.
- **Showcase Slots Needed**: The showcase container must be generalized to accept native React visual elements (`nativeVisual?: React.ReactNode` or a data-driven composition selector per stage) while retaining spring physics, direction awareness, and hover depth.

### 2.2 Onboarding Page Architecture (`frontend/app/onboarding/page.tsx`)
- **Layout**: Full-screen standalone route (`app/onboarding/layout.tsx` + `page.tsx`), zero dashboard chrome leakage.
- **State Schema**: `OnboardingState` managing step (1–8), `orgName`, `industryFocus`, `teamSize`, `persona`, `selectedJurisdictions`, `selectedBills`, `digestFrequency`, `inAppAlerts`, `emailAlerts`.
- **Form Columns**: Left column (`lg:col-span-5`) handles user input, draft persistence in `localStorage`, and validation.
- **Showcase Column**: Right column (`lg:col-span-7`) hosts `FeatureCarousel`, synchronized with `state.step`.
- **Completion Redirection**: On step 8 finish, calls `watchlistsApi.createWatchlist`, `watchlistsApi.addItem`, `alertsApi.updatePreferences`, clears draft, and transitions to `/workspace`.

### 2.3 Vector Icon & Visual Utilities (`frontend/components/ui/Icons.tsx`)
- Standardized SVG system with 24x24 viewBox and 1.75–2px stroke weights.
- Key icons available: `WorkspaceIcon`, `BillsIcon`, `ExplorerIcon`, `StatesIcon`, `PredictionsIcon`, `AiAnalystIcon`, `MonitoringIcon`, `CoverageIcon`, `WatchlistIcon`, `AlertsIcon`, `ShieldIcon`, `CheckIcon`, `CheckCircleIcon`, `ChevronRightIcon`, `SearchIcon`.

### 2.4 Chart Components (`frontend/components/charts/`)
- Existing chart primitives: `EventStudyChart.tsx`, `HorizonComparisonVisualizer.tsx`, `RiskDistributionVisualizer.tsx`, `PreEventCarChart.tsx`, `ChartContainer.tsx`, `ChartTooltip.tsx`.
- All use clean native SVG paths, CSS transitions, and SVG geometric shapes. Zero external heavy chart libraries required.

### 2.5 Hardware Mockup Component: `IPhone17ProMax` (`frontend/components/ui/apple-iphone-17-pro.tsx`)
- Currently referenced in specification but not yet implemented.
- **Required Specification**:
  - Props: `children?: React.ReactNode`, `batteryLevel?: number` (default 94), `dynamicIslandSize?: DynamicIslandSize` ("default" | "compact" | "expanded" | "minimal"), `frameColor?: "graphite" | "silver" | "gold" | "deep-blue" | "black"` (default "graphite"), `signalStrength?: number` (1–4), `time?: string` (default "9:41"), `onDynamicIslandTap?: () => void`, `className?: string`.
  - Design: Precision titanium/graphite curved perimeter, hairline bezel, Dynamic Island with interactive toggle, camera lens reflection, status bar (signal, Wi-Fi, battery pill), home indicator bar.
  - Sizing & Responsive Behavior: Perfectly bounded height and width, scale-adapted to fit inside the 16:10 / showcase viewport on desktop, tablet, and mobile without vertical or horizontal overflow.
  - Zero dependencies beyond React and Tailwind CSS.

### 2.6 Theme Tokens & Palette
- **Canvas Base**: `#080808`
- **Outer Frame**: `#252525`
- **Inner Surface**: `#111111`
- **Elevated Surfaces**: `#161616` / `#191919`
- **Borders**: `rgba(255, 255, 255, 0.08)` hairline, hover `rgba(255, 255, 255, 0.18)`
- **Primary Text**: `#F4F4F4`
- **Secondary Text**: `#A3A3A3`
- **Faint Text**: `#666666`
- **Accents**: Emerald (`#10B981` / `#34D399`) for verified statuses, Amber (`#F59E0B`) for review/in-progress, Blue (`#3B82F6`) for passage/direct relations.

---

## 3. Deprecated Screenshot Inventory

The following 10 screenshot assets will be completely removed from the primary showcase visual pipeline:
1. `stage1_bill_dossier.png`
2. `stage1_statutory_mechanics.png`
3. `stage2_workspace_telemetry.png`
4. `stage2_command_center.png`
5. `stage3_exposure_matrix.png`
6. `stage4_state_firewall.png`
7. `stage5_watchlist_seed.png`
8. `stage6_alert_rules.png`
9. `stage7_ai_analyst.png`
10. `stage8_launch_overview.png`

*Note*: The physical image files remain in `frontend/public/onboarding/` to prevent broken links in any legacy references or tests, but `FeatureCarousel` and `OnboardingPage` will render native React components instead.

---

## 4. Native Eight-Stage Intelligence Showcase Plan

| Stage | Name | Component Name | Key Visual Elements | Epistemic Invariants & Terminology |
|---|---|---|---|---|
| **01** | Legislative Intelligence | `LegislativeJourneyVisual` | Animated timeline with 4 milestones: Bill Introduced, Committee Review, Legislative Passage, Presidential Assent. Active milestone pulsing indicator, progressive connecting line, bill metadata header. | Generic illustrative lifecycle. Accurate parliamentary terminology (Lok Sabha, Rajya Sabha, Joint Committee, Gazette Notification). |
| **02** | Workspace Command Center | `WorkspaceCommandCenterVisual` | Operational telemetry dashboard: monitored entities counters, active alert stream, source freshness indicator (Parliament, State Gazettes, MCA feeds), compact activity sparkline and feed items. | Labeled as illustrative demo data. No false claims of live server daemons running. |
| **03** | Corporate Exposure Network | `CorporateExposureNetworkVisual` | Animated SVG network graph connecting Bill node → Sector nodes (Telecom, Banking, Energy) → Corporate nodes (e.g. Bharti Airtel, HDFC Bank, Tata Power) with direct (solid) and indirect (dashed) progressive vectors. Interactive node hover tooltips. | Direct vs indirect exposure distinguished. Clear disclaimer that nodes illustrate mapping architecture. |
| **04** | State Statutory Intelligence | `StateIntelligenceMapVisual` | Stylized India jurisdiction SVG map with regional hubs (Central, Andhra Pradesh, Karnataka, Kerala, Telangana), Central vs State jurisdiction badge, and an uncompromised **StatePredictionFirewall** banner. | 0.00% stock prediction leakage guarantee. Explicit statement that state acts have zero quantitative equity predictions. |
| **05** | Watchlist Intelligence | `WatchlistIntelligenceVisual` | High-density institutional watchlist interface: company symbols (`BHARTIARTL`, `HDFCBANK`, `TATAPOWER`), bill IDs, exposure categories, animated selection badges, and status chips. | Grounded in approved catalog tickers or clearly labeled demo entries. |
| **06** | Alert Intelligence | `AlertIntelligenceVisual` | Interactive alert configuration console: SVG radial threshold gauge, severity levels (Low, Medium, High, Critical), trigger conditions, delivery channels (In-App, Digest, Webhook), frequency selector. | Movement is restrained. Explicit note that alerts are illustrative previews during onboarding. |
| **07** | AI Analyst & Mobile Intelligence | `SeanceMobileShowcase` | Premium `IPhone17ProMax` smartphone container with Dynamic Island interaction, hosting a complete native Seance mobile UI: Seance wordmark, compact bill dossier card, corporate exposure pill, mini event-study AR chart, and grounded AI Analyst citation preview. | Real React DOM components inside mobile screen. Responsive scale without overflow. Dynamic Island tap demonstration. |
| **08** | Workspace Launch | `WorkspaceLaunchVisual` | Integrated multi-pane terminal composition synthesizing elements from prior stages: procedural progress, exposure summary, model status, and readiness checklist with subtle atmospheric glow. | Elegant hierarchy. Clearly communicates readiness without claiming configuration is finished prior to clicking Launch. |

---

## 5. Architectural Component Structure

All native showcase components will be organized in a modular directory:
`frontend/components/onboarding/showcase/`:
- `index.ts` — Central export barrel
- `LegislativeJourneyVisual.tsx`
- `WorkspaceCommandCenterVisual.tsx`
- `CorporateExposureNetworkVisual.tsx`
- `StateIntelligenceMapVisual.tsx`
- `WatchlistIntelligenceVisual.tsx`
- `AlertIntelligenceVisual.tsx`
- `SeanceMobileShowcase.tsx`
- `WorkspaceLaunchVisual.tsx`

And `frontend/components/ui/apple-iphone-17-pro.tsx` for the standalone `IPhone17ProMax` smartphone frame.

---

## 6. Verification & Invariant Strategy
1. **Vitest Unit Tests**: Ensure existing tests pass without regressions; extend tests to assert native component mounting.
2. **TypeScript & Production Build**: Validate zero typing errors and pristine Next.js build.
3. **Playwright End-to-End Validation**: Execute full 8-stage browser walkthrough across Desktop (1440x900), Tablet (768x1024), and Mobile (375x812).
4. **Baseline Hash Check**: Verify `docs/production_baseline.json` SHA-256 remains `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`.

