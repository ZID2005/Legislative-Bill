# TASK 8.14.4 — SaaS Overview Dashboard & India Legislative Explorer Implementation

**India Legislative Intelligence & Market Impact Prediction Platform**  
**Document Version:** 1.0.0  
**Status:** Complete  
**Date:** September 19, 2026  

---

## Executive Summary

Task 8.14.4 delivers the first two core production-facing interfaces for the **India Legislative Intelligence & Market Impact Prediction Platform**:
1. **The SaaS Overview Dashboard (`/overview`):** The primary executive entry point into the platform, synthesizing real-time legislative telemetry, multi-tier coverage metrics, Central quantitative predictions, State assembly intelligence, and system surveillance status.
2. **The India Legislative Explorer (`/explorer`):** The unified discovery engine providing structured search and cross-entity exploration across Central Parliament and State Legislative Assemblies, strictly respecting institutional boundaries and capability tiers.

Both user interfaces are built strictly on top of the verified Next.js 16 (React 19, TypeScript) foundation and the FastAPI REST backend (`/api/v1`). All business logic, filtering, pagination, and predictions are driven exclusively by the backend; no local storage files are accessed directly, and zero mock predictions are generated on the client.

---

## 1. Architectural Invariants & Compliance Rules

| Rule | Implementation Guarantee | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Single Source of Truth** | All displayed metrics and records originate from FastAPI (`/api/v1/`). | Typed API clients (`billsApi`, `companiesApi`, `predictionsApi`, `monitoringApi`, `searchApi`). |
| **Zero Client-Side Calculation** | Prediction probabilities, anticipation scores, and exposure counts are never calculated in TypeScript. | Pure presentation layer rendering backend payloads. |
| **State Prediction Firewall** | State legislative records strictly feature 0 quantitative predictions. | `CapabilityBadge`, warning disclaimers, and disabled prediction links for all State assembly bills. |
| **Neutral Analytical Language** | Zero trading or investment advice; no "Buy", "Sell", "Hold", "Outperform", or price targets. | Professional terminology: "Projected Direction: Positive/Negative/Neutral", "Impact Probability", "Legislative Anticipation". |
| **Frozen Baseline Parity** | Central: 20 bills, 47 quant companies, 940 pairs, 4,700 predictions, 4,700 decisions.<br>State: 44 bills (AP 12, KA 11, KL 11, TG 10), 86 exposures, 0 predictions.<br>Universe: 70 companies (47 quant, 20 intel, 3 ref), 66 legislative records, 104 exposures. | Validated in component tests, E2E rendering, and backend API regression. |

---

## 2. SaaS Overview Dashboard (`/overview`)

The Overview dashboard (`frontend/app/overview/OverviewContent.tsx`) provides an executive view across 9 data-driven sections:

### 2.1 Component Architecture & Sections
1. **Hero & Quick Actions:**
   - Platform title, institutional tagline, and live connection indicator.
   - Quick Action links: "Explore Legislation", "Analyze Corporate Universe", "Quantitative Predictions", "AI Analyst Consultation".
2. **System Coverage Summary Metrics:**
   - Real-time stat cards displaying:
     - **20** Central Parliament Bills
     - **44** State Legislative Bills (AP, KA, KL, TG)
     - **47** Market-Modelled Companies
     - **70** Total Tracked Corporate Universe
     - **66** Unified Legislative Entities
     - **104** Evidence-Backed Corporate Exposures
3. **Institutional Capability Tiers:**
   - Visual breakdown of the three platform capability tiers:
     - **Level 1 (Central Market-Modelled):** 20 Parliamentary Acts with end-to-end quantitative impact modeling across 47 listed companies.
     - **Level 2 (State Assembly Intelligence):** 44 bills across 4 southern states with statutory 0-prediction firewall and qualitative corporate exposure tracking.
     - **Level 3 (Union Roadmap):** Surveillance coverage scheduled across 24 additional State and Union Territory Assemblies.
4. **Recent Legislative Activity Feed:**
   - Live stream of the most recent legislative developments fetched via `billsApi.listBills({ limit: 6, sort_by: "introduction_date", sort_order: "desc" })`.
   - Displays bill title, jurisdiction badge, state tag, status pill, and filing date.
5. **Central Market-Modelled Snapshot:**
   - Highlights recent quantitative predictions fetched via `predictionsApi.listPredictions({ limit: 6 })`.
   - Displays company name, event window (`immediate_1d`, `short_5d`, `medium_20d`), projected direction, and confidence score.
   - Strictly applies neutral institutional wording.
6. **State Assembly Intelligence Snapshot:**
   - Comprehensive state breakdown for Andhra Pradesh (12 bills), Karnataka (11 bills), Kerala (11 bills), and Telangana (10 bills).
   - Clear disclosure banner confirming that quantitative price modeling is barred by statute for state assembly bills.
7. **Corporate Exposure Snapshot:**
   - Universe snapshot fetched via `companiesApi.listCompanies({ limit: 6 })`.
   - Displays sector distribution, ticker/ISIN, and total associated legislative exposure vectors.
8. **Monitoring & Surveillance Status:**
   - Live telemetry card fetched via `monitoringApi.getStatus()`.
   - Displays total tracked scrapers, gazette ingestion workers, active status, and last sync timestamp.
9. **Strategic Navigation Cards:**
   - Deep-linking cards guiding users to Legislative Explorer, Corporate Universe, Alert Center, and System Coverage.

---

## 3. India Legislative Explorer (`/explorer`)

The India Legislative Explorer (`frontend/app/explorer/ExplorerContent.tsx`, wrapped in Next.js `Suspense` within `frontend/app/explorer/page.tsx`) offers institutional search and discovery across India's legislative landscape.

### 3.1 Dual Search Modes
1. **Structured Legislative Bills Mode:**
   - Queries `GET /api/v1/bills` with extensive parameter filtering.
   - Full server-side pagination with query caching.
   - Returns rich legislative cards featuring capability badges, parliamentary houses, status badges, sector tags, and impact indicators.
2. **Unified Cross-Entity Discovery Mode:**
   - Queries `GET /api/v1/search/unified`.
   - Searches across both legislative instruments and corporate entities simultaneously.
   - Categorizes matches by entity type (`bill` vs `company`) with entity-specific metadata.

### 3.2 Server-Side Filter Architecture
The Explorer sidebar and filter bar provide multi-dimensional slicing:
- **Search Query (`q`):** Debounced text search (350ms) matching bill titles, numbers, and summaries.
- **Jurisdiction (`jurisdiction`):** All, Central Parliament (`central`), or State Assemblies (`state`).
- **State Selection (`state`):** Filter by implemented states (`andhra_pradesh`, `karnataka`, `kerala`, `telangana`) or planned roadmap states (`maharashtra`, `tamil_nadu`, `delhi`, `gujarat`, etc.).
- **Legislative Status (`status`):** Introduced, Pending, Passed, Enacted, Lapsed, Withdrawn.
- **Year of Introduction (`year`):** Multi-year filtering.
- **Economic Sector (`sector`):** Technology, Banking & Finance, Energy & Power, Healthcare, Infrastructure, Agriculture, etc.
- **Market Relevance (`market_relevance`):** High, Moderate, Indirect, Nil.
- **Capability / Modeling Eligibility (`modeling_eligibility`):** Central Quant Modelled vs State Intelligence Only.

### 3.3 Planned State Roadmap Handling
When a user selects a state currently on the expansion roadmap (e.g., Maharashtra, Tamil Nadu, Uttar Pradesh, Gujarat), the Explorer dynamically renders a high-visibility roadmap banner:
- Discloses scheduled ingestion wave.
- Explains gazette scraping pipeline onboarding status.
- Avoids empty state confusion while keeping the user informed of platform horizons.

### 3.4 URL Synchronization & Clean State
- Filter and search state is bidirectional with browser history (`useSearchParams` and `useRouter`).
- Sharing or bookmarking a URL (e.g., `/explorer?jurisdiction=state&state=karnataka&sector=Technology`) reconstructs the exact filter state on page load.
- Default parameters (`page=1`) are pruned from the query string to keep institutional URLs clean and shareable.

---

## 4. Capability Badges & Institutional UI Components

Located in `frontend/components/coverage/CapabilityBadge.tsx`, these components visually enforce platform boundaries:

| Component | Visual Indicators | Context / Use Case |
| :--- | :--- | :--- |
| `CapabilityBadge` | **Level 1**: Blue badge ("Central Market-Modelled")<br>**Level 2**: Emerald badge ("State Intelligence Only")<br>**Level 3**: Amber badge ("Union Roadmap") | Displayed on all bill cards, headers, and detail dossiers. |
| `JurisdictionBadge` | **Central**: Indigo icon + "Central Parliament"<br>**State**: Teal icon + State Name / "State Assembly" | Immediate clarity on constitutional jurisdiction. |
| `MarketRelevanceBadge` | High (Purple), Moderate (Sky), Indirect (Slate), Nil (Gray) | Indicating legislative impact on financial markets. |
| `CorporateExposureBadge` | Direct, Indirect, Supply Chain, Regulatory | Classifying how companies are affected by legislation. |
| `PredictionAvailability` | Available (Green pill) vs Unavailable (Gray pill with explanation) | Enforcing zero predictions on State bills. |
| `CoverageStatus` | Implemented (Green) vs Planned (Amber) | Differentiating active assemblies from roadmap states. |

---

## 5. Verification & Test Evidence

### 5.1 Frontend Unit & Component Tests (`npm test`)
Ran Vitest test suites across all 7 frontend test files:
```
✓ components/__tests__/StatePredictionFirewall.test.tsx (8 tests)
✓ components/__tests__/IntelligenceCompanyFirewall.test.tsx (8 tests)
✓ components/__tests__/CapabilityBadge.test.tsx (12 tests)
✓ lib/api/__tests__/api-clients.test.ts (11 tests)
✓ app/overview/__tests__/OverviewContent.test.tsx (6 tests)
✓ app/explorer/__tests__/ExplorerContent.test.tsx (8 tests)
✓ app/__tests__/pages-smoke.test.tsx (2 tests)

Test Files  7 passed (7)
Tests       55 passed (55)
Start at    14:26:14
Duration    7.84s
```

### 5.2 TypeScript Compilation (`npm run typecheck`)
```
> frontend@0.1.0 typecheck
> tsc --noEmit
Exit Code: 0 (Zero errors)
```

### 5.3 Next.js Production Build (`npm run build`)
```
Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /ai-analyst
├ ○ /alerts
├ ○ /anticipation
├ ○ /bills
├ ○ /bills/[billId]
├ ○ /bills/compare
├ ○ /companies
├ ○ /companies/[companyId]
├ ○ /coverage
├ ○ /explorer
├ ○ /industries
├ ○ /monitoring
├ ○ /notifications
├ ○ /overview
├ ○ /predictions
├ ○ /predictions/[predictionId]
├ ○ /risk
├ ○ /sectors
├ ○ /settings
├ ○ /states
└ ○ /watchlists
+ First Load JS shared by all: 87.4 kB
✓ Compiled successfully
```

---

## 6. Baseline Consistency Verification

All metrics presented in the UI and tested in unit suites match the frozen project baseline:
- **Central Legislative Acts:** 20 verified bills.
- **Central Quantitative Companies:** 47 listed companies.
- **Central Bill-Company Pairs:** 940 pairs.
- **Central Predictions:** 4,700 records across 5 event windows (`immediate_1d`, `short_5d`, `medium_20d`, `pre_intro_30d`, `annual_90d`).
- **Central Decisions:** 4,700 decision support records.
- **State Assembly Bills:** 44 bills (Andhra Pradesh: 12, Karnataka: 11, Kerala: 11, Telangana: 10).
- **State Quantitative Predictions:** Strictly **0** (statutory isolation).
- **State Corporate Exposures:** 86 evidence-backed exposure mappings.
- **Total Corporate Universe:** 70 entities (47 quantitative, 20 intelligence-only, 3 reference).
- **Unified Legislative Entities:** 66 total records (20 Central + 44 State).
- **Total Unified Corporate Exposures:** 104 exposures.

---

## 7. Next Recommended Task

**Task 8.14.5 — Bill Detail Dossier Implementation**  
- Implement the comprehensive legislative dossier for Central and State bills at `/bills/[billId]`.
- Enforce the `StatePredictionFirewall` to conditionally render quantitative prediction tabs for Central bills and State assembly intelligence tabs for State bills.
- Integrate full text viewer, procedural journey timeline, economic sector vectors, company exposure matrices, and Groq LLaMA-3.3 policy Q&A panel.
