# TASK 8.14.5 — Bill Detail Dossier Implementation

**India Legislative Intelligence & Market Impact Prediction Platform**  
**Document Version:** 1.0.0  
**Status:** Complete  
**Date:** September 19, 2026  

---

## Executive Summary

Task 8.14.5 delivers the production-quality **Bill Detail Dossier** at `/bills/[billId]`, serving as the primary core intelligence hub of the platform.

The Bill Detail Dossier unifies:
1. **Official Legislation & Identity:** Full title, bill number, house, legislature, status, filing and assent dates.
2. **Key Statutory Provisions:** Extracted statutory clauses, amended statutes, regulatory authority, financial/tax terms, and enforcement penalties.
3. **Policy & Economic Impact Intelligence:** Primary and secondary economic sectors, policy domains, constituent groups, geographic scope, and market relevance.
4. **Evidence-Backed Corporate Exposure:** Direct and indirect exposure vectors, strength levels, mechanisms, and statutory claims.
5. **Central Market Predictions:** Multi-horizon econometric projections across 5 event windows with decision-support drill-downs for eligible Central bills.
6. **State Prediction Firewall:** Strict enforcement of 0 quantitative predictions for all State legislation via `StatePredictionFirewall`.
7. **Central Non-Modelled Disclosure:** Explicit disclosure for Central bills outside the frozen 20 quantitative production set.
8. **Pre-Event Anticipation Analysis:** Pre-event market and diffusion metrics, anticipation classification, evidence summary, and neutral institutional framing.
9. **Stakeholder Intelligence:** Multi-persona analysis (Investor, Business Owner, Employee, Consumer, Farmer, MSME, Public, Industry) with strict separation of `FACT`, `DERIVED`, `INTERPRETATION`, and `PREDICTION`.
10. **Authoritative Source & Provenance:** PRS and official parliament/assembly portal URLs, official PDF gazette documents, data quality tags, and field-level provenance audit map.
11. **Grounded Groq AI Copilot:** Grounded analytical explanation using Groq LLaMA-3.3 inference through FastAPI (`/api/v1/ai/explain/bill/{id}` and `/api/v1/ai/ask`).
12. **Watchlist Integration:** Direct subscription to user watchlists supporting existing and inline-created lists via `/api/v1/watchlists`.

---

## 1. Page Architecture & Flow

The dossier operates strictly according to the platform's multi-tier architecture:

```
Next.js Page (/bills/[billId])
         │
         ▼
BillDetailContent (Client Component)
  ├─ billsApi.getBill(billId)
  ├─ billsApi.getBillPredictions(billId)
  ├─ billsApi.getBillCompanies(billId)
  ├─ billsApi.getBillAnticipation(billId)
  ├─ watchlistsApi.listWatchlists()
  └─ aiApi.explainBill() / aiApi.ask()
         │
         ▼ (HTTP JSON REST)
FastAPI REST API Layer (/api/v1)
  ├─ GET  /api/v1/bills/{bill_id}
  ├─ GET  /api/v1/bills/{bill_id}/predictions
  ├─ GET  /api/v1/bills/{bill_id}/companies
  ├─ GET  /api/v1/bills/{bill_id}/anticipation
  ├─ GET  /api/v1/predictions/{prediction_id}/decision
  ├─ GET  /api/v1/ai/explain/bill/{bill_id}
  ├─ POST /api/v1/ai/ask
  ├─ GET  /api/v1/watchlists
  └─ POST /api/v1/watchlists/{id}/items
         │
         ▼
Authoritative Repositories (Python Domain Singletons)
  ├─ UnifiedLegislativeDiscoveryService
  ├─ StateKnowledgeRepository (data/state_bills/knowledge)
  ├─ KnowledgeRepository (data/bills/knowledge)
  ├─ CompanyExposureRepository & StateCorporateExposureRepository
  ├─ PredictionRepository & DecisionRepository (4,700 frozen records)
  ├─ AnticipationRepository (940 frozen pairs)
  ├─ WatchlistService & WatchlistRepository
  └─ AIExplanationService (Groq LLaMA-3.3 with offline fallback guard)
```

---

## 2. API Dependencies & Contracts Consumed

| Capability | FastAPI Endpoint | Response Schema | Client Method |
| :--- | :--- | :--- | :--- |
| **Bill Dossier** | `GET /api/v1/bills/{bill_id}` | `BillDetailResponse` | `billsApi.getBill(id)` |
| **Predictions** | `GET /api/v1/bills/{bill_id}/predictions` | `BillPredictionStatusResponse` | `billsApi.getBillPredictions(id)` |
| **Exposures** | `GET /api/v1/bills/{bill_id}/companies` | `list[BillCompanyExposure]` | `billsApi.getBillCompanies(id)` |
| **Anticipation** | `GET /api/v1/bills/{bill_id}/anticipation` | `dict[str, Any]` | `billsApi.getBillAnticipation(id)` |
| **Decision Record** | `GET /api/v1/predictions/{id}/decision` | `DecisionRecordResponse` | `predictionsApi.getPredictionDecision(id)` |
| **Stakeholder Report** | `GET /api/v1/reports/{b}/{c}/{w}/{s}` | `StakeholderReportResponse` | `predictionsApi.getStakeholderReportByKey(...)` |
| **AI Explain** | `GET /api/v1/ai/explain/bill/{id}` | `AIAskResponse` | `aiApi.explainBill(id, op, persona)` |
| **AI Grounded Ask** | `POST /api/v1/ai/ask` | `AIAskResponse` | `aiApi.ask(body)` |
| **Watchlist List** | `GET /api/v1/watchlists` | `list[WatchlistResponse]` | `watchlistsApi.listWatchlists()` |
| **Watchlist Add** | `POST /api/v1/watchlists/{id}/items` | `WatchlistItemResponse` | `watchlistsApi.addItem(id, body)` |

---

## 3. Bill Identity & Header

Implemented in `frontend/components/bills/BillHeader.tsx`:
- **Breadcrumbs:** `India Explorer › Bills › [Bill Title]`
- **Authority Badges:**
  - `JurisdictionBadge`: `🏛 Central Parliament` vs `🗺 [State] Assembly`
  - `StatusBadge`: `passed_both`, `introduced`, `pending`, `assented`, etc.
  - `CapabilityBadge`: Level 1 (Central Modelled), Level 2 (State Intelligence Only), Level 3 (Union Roadmap)
  - `MarketRelevanceBadge`: HIGH, MEDIUM, LOW, NONE
  - `SourceBadge`: `FACT` (verified parliamentary source)
  - `Data Quality`: `✓ VERIFIED`
- **Metadata Ribbon:**
  - Legislature name
  - Chamber/House of introduction
  - Year of introduction
  - Authoritative introduction date
  - Authoritative assent date (when granted)
- **Dossier Quick Actions:**
  - ⭐ Add to Watchlist (opens `WatchlistModal`)
  - 📄 Official PDF (opens official gazette document in new tab)
  - 🏛 Official Portal (opens primary government URL in new tab)
  - ⚖ Compare Bill (navigates to `/bills/compare?bill1={billId}`)
  - 🤖 Ask AI (activates AI Copilot tab)
  - 🔗 Share (copies canonical URL with feedback notification)

---

## 4. Procedural Timeline

Implemented in `frontend/components/bills/ProceduralJourney.tsx`:
- Tracks milestones across the legislative lifecycle:
  1. **Tabled & Formally Introduced:** Date from `bill.introduction_date` or `"Date not available"`. Chamber from `bill.house`.
  2. **First Chamber Passage:** Active debate or completed passage based strictly on status.
  3. **Legislative Passage:** Both houses or single assembly passage based on status.
  4. **Presidential / Governor Assent:** Date from `bill.assent_date` or `"Date not available"`.
  5. **Official Gazette Notification:** Authoritative enactment publication status.
- **Strict Invariant Guarantee:** Intermediate dates are rendered as `"Date not available"` unless explicitly recorded in source gazettes. No dates are inferred or synthetically generated.

---

## 5. Key Provisions & Legal Framework

Implemented in `frontend/components/bills/KeyProvisions.tsx`:
- Sourced dynamically from `StateKnowledgeRepository` (for State legislation) and `KnowledgeRepository` (for Central legislation).
- Features:
  - **Statutory Objective / Preamble:** Statement of Objects and Reasons rendered in distinct blockquote styling.
  - **Identified Key Provisions:** Sequenced statutory provisions with `§` clause numbering.
  - **Regulatory / Administrative Authority:** Sponsoring ministry or state administrative department.
  - **Amended Statutes:** Intersecting Acts modified by the bill.
  - **Financial & Tax Provisions:** Explicit statutory fee, duty, and tax rate terms.
  - **Penalties & Enforcement:** Statutory inspection, compliance, and enforcement clauses.

---

## 6. Policy & Economic Intelligence

Implemented in `frontend/components/bills/PolicyEconomicIntelligence.tsx`:
- Sourced from unified discovery records and economic profiles.
- Dimensions:
  - Policy Domain classification
  - Impacted Economic Sectors (Primary sector marked with ★ Primary; Secondary sectors tagged)
  - Affected Stakeholder and Constituent groups
  - Geographic Scope (National or State territorial scope)
  - Qualitative Market Relevance score
  - Data Sufficiency evaluation
- **Methodological Standard:** Grounded in deterministic text extraction and taxonomy mapping. Zero speculative stock returns or asset price targets are derived from qualitative domains.

---

## 7. Corporate Exposure

Implemented in `frontend/components/bills/CorporateExposureTable.tsx`:
- Displays verified corporate entities with documented exposure vectors.
- Columns:
  - Company Name, Ticker, and ISIN
  - Primary Sector & Business Activity
  - Exposure Type (Operational, Regulatory, Revenue, Supply Chain)
  - Direct / Indirect exposure badge
  - Exposure Strength badge (HIGH, MEDIUM, LOW)
  - Economic Transmission Mechanism
  - State Relevance where applicable
  - Evidence claim details drawer
- Interactive Client Filtering:
  - Text search by company name, sector, or activity
  - Direct / Indirect filter toggle
  - Exposure strength level filter (HIGH / MEDIUM / LOW)
- Expandable Evidence Drawer:
  - Statutory claims and citations
  - Section references (e.g. `§ Section 4`)
  - Source report citations and links

---

## 8. Central Market Predictions

Implemented in `frontend/components/bills/CentralPredictionSection.tsx`:
- Rendered **only** when `has_predictions = true` and prediction records exist.
- Displays projections across 5 event windows (`[-1,+1]`, `[-5,+5]`, `[-20,+20]`, `[-30,-1]`, `[0,+90]`).
- Table fields:
  - Company Name & ISIN
  - Event Window
  - Projected Direction (`↑ POSITIVE`, `↓ NEGATIVE`, `→ NEUTRAL`)
  - Market-Moving Classification (`Yes/No` with probability %)
  - Impact Strength (`HIGH`, `MEDIUM`, `LOW`)
  - Model Confidence (`HIGH`, `MEDIUM`, `LOW` with % score)
  - Decision Support Action button
- **Decision Support Drawer:**
  - Loads `/api/v1/predictions/{id}/decision` on demand
  - Risk Category (`HIGH`, `MEDIUM`, `LOW`)
  - Pricing-in Risk (`HIGH`, `MODERATE`, `LOW`)
  - Impact Category (`TRANSFORMATIVE`, `MODERATE`, `MARGINAL`)
  - Risk Score and Impact Score
  - Institutional Decision Reason
  - Investor Perspective Summary
  - Corporate & Enterprise Summary
- **Regulatory Warning:** Explicit notice that projections reflect quantitative models and do not constitute investment advice.

---

## 9. State Prediction Firewall

Implemented via `components/firewalls/StatePredictionFirewall.tsx`:
- Strictly isolates all 44 State bills from Central quantitative stock market models.
- When a user views predictions for a State bill, the firewall engages immediately:
  - Renders: *"Market prediction is not currently available for State legislation."*
  - Clarifies that this is a deliberate statutory and econometric research boundary.
  - Highlights available Level 2 capabilities: Legislative Intelligence, Economic Impact Analysis, Corporate Exposure, Market Relevance.
  - Lists explicitly barred metrics: predicted stock returns, directional forecasts, buy/sell signals, model probabilities.
- State quantitative stock predictions remain strictly **0**.

---

## 10. Central Non-Modelled Bills

- For Central bills where `has_predictions = false` or `modeling_eligibility = NOT_ELIGIBLE` (e.g. `key-issues-and-analysis`, `service-bill`):
  - Renders an institutional disclosure banner: *"Market modelling is not currently available for this bill."*
  - Clarifies that the bill is outside the frozen 20 quantitative production set.
  - Zero empty charts or speculative tables are displayed.

---

## 11. Pre-Event Anticipation Analysis

Implemented in `frontend/components/bills/AnticipationSection.tsx`:
- Evaluates whether legislative information diffused into market volumes prior to formal introduction.
- For Central Modelled Bills:
  - Overall Anticipation Score (e.g. 0.738)
  - Diagnostic Tier (`MODERATE_EVIDENCE`, `WEAK_EVIDENCE`, etc.)
  - Pre-Event Signal Flag (`Flagged` vs `Unflagged`)
  - Confidence Level & Analyzed Universe count (47 companies)
  - Sample company scores table with Market Signal, Info Signal, and Decision Reason
- **Methodology & Terminology Disclosure:**
  - *"Pre-event information evidence suggests that some legislative or policy information may have been diffused or anticipated by market participants before formal legislative tabling."*
  - Strictly disclaims allegations of insider trading: *"These diagnostics reflect quantitative statistical volume/volatility patterns; they do NOT prove or allege non-public information leakage or insider trading."*
- For State Bills:
  - Renders: *"Anticipation Analysis Not Applicable to State Legislation."*

---

## 12. Stakeholder Intelligence

Implemented in `frontend/components/bills/StakeholderIntelligence.tsx`:
- Supported personas:
  1. Investor
  2. Business Owner
  3. Employee / Worker
  4. Consumer
  5. Farmer / Rural
  6. MSME / Small Enterprise
  7. General Public
  8. Corporate / Industry
- **Strict 4-Tier Semantic Separation:**
  1. `FACT` (Official Statutory Fact): Authoritative statutory mandate and legal status.
  2. `DERIVED` (Deterministic Mapping Vector): Sector classifications, exposed company counts, and compliance benchmarks.
  3. `INTERPRETATION` (Analytical Impact Interpretation): Economic transmission channels and operational adaptations.
  4. `PREDICTION` (Market & Sensitivity Tier): Quantitative sensitivity tier for modelled bills, or explicitly marked unavailable.
- Zero investment advice disclaimer.

---

## 13. Related Legislation

Implemented in `frontend/components/bills/RelatedBillsCard.tsx`:
- Sourced from `detail.related_bills` (populated from parliamentary knowledge records).
- Displays linked enactments with title, jurisdiction badge, state badge, and status.
- Direct navigation links to `/bills/[billId]`.
- Clean empty state when no related bills are cataloged.

---

## 14. Authoritative Source & Provenance Panel

Implemented in `frontend/components/bills/ProvenancePanel.tsx`:
- Authoritative Links:
  - Official Source Portal (`bill.source_url`)
  - Official Gazette / Bill PDF (`bill.pdf_url`)
- Verification Data:
  - Data Quality: `✓ VERIFIED`
  - Data Sufficiency: `COMPLETE` vs `INSUFFICIENT`
  - Authority: Parliament of India vs State Assembly
- **Field-Level Provenance Audit Map:**
  - Audits each field's authority tier: `AUTHORITATIVE`, `DERIVED`, `SYSTEM_DERIVED`, or `UNAVAILABLE`.
  - Enforces transparent data lineage for auditability.

---

## 15. Grounded Groq AI Copilot

Implemented in `frontend/components/bills/AIAssistantPanel.tsx`:
- Sourced from FastAPI `/api/v1/ai/explain/bill/{id}` and `/api/v1/ai/ask`.
- Features:
  - Analyst Perspective Switcher: General Public, Institutional Investor, Policy Researcher.
  - Suggested Inquiries:
    - *"What does this bill change?"*
    - *"Which sectors are affected?"*
    - *"Which companies have documented exposure?"*
    - *"Why is this bill market relevant?"*
    - *"Explain the prediction"*
    - *"What anticipation evidence exists?"*
  - Custom grounded question form.
  - Renders markdown content, operation type, caching tag, provenance sources, and disclaimer.
  - **Zero Secret Leakage / Robust Fallback:**
    - If Groq inference is unreachable or disabled, renders a safe fallback notice without error tracebacks or secret exposure.

---

## 16. Watchlist Integration

Implemented in `frontend/components/bills/WatchlistModal.tsx`:
- Triggered by "Add to Watchlist" button in header or sidebar.
- Queries `GET /api/v1/watchlists` to display user's existing watchlists.
- Supports selecting an existing watchlist or creating a new watchlist inline (`POST /api/v1/watchlists`).
- Subscribes bill via `POST /api/v1/watchlists/{id}/items` with `{ entity_type: "bill", entity_id: bill.bill_id }`.
- Multi-tenant isolated under current user context.

---

## 17. Responsive Design & Accessibility

- **Desktop (>= 1024px):** 2/3 main dossier content with horizontal tab bar + 1/3 contextual intelligence sticky sidebar.
- **Tablet (768px - 1023px):** Stacked dossier layout with full-width tabs and collapsible cards.
- **Mobile (< 768px):** Single-column stacked cards, horizontally scrollable tab ribbons and data tables, responsive touch targets.
- **Accessibility:**
  - Semantic HTML5 elements (`<header>`, `<nav>`, `<main>`, `<aside>`, `<table>`, `<ol>`, `<ul>`, `<blockquote>`).
  - Full ARIA tab patterns (`role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-controls`).
  - High-contrast color palette adhering to WCAG 2.1 AA standards.

---

## 18. Performance & Optimization

- Parallel asynchronous fetching via `Promise.all` for bill detail, predictions, exposures, and anticipation.
- Caching headers on backend API endpoints.
- Lazy/on-demand loading for decision support records and AI explanations to avoid superfluous network payloads.
- Client-side memoized filtering on corporate exposures (`useMemo`).

---

## 19. Automated Verification Evidence

### 19.1 Vitest Unit & Page Test Suite (`npm test`)
### 19.1 Frontend Automated Test Suite (`npm test`)
```
 Test Files  8 passed (8)
      Tests  70 passed (70)
   Duration  9.60s
Exit Code: 0 (All 8 test files passed, 70 passed, 0 failed)
```

Tested all 8 test files including the comprehensive 16-test suite in `frontend/__tests__/pages/bill-detail.test.tsx`:
- Central modelled bill renders prediction section.
- Central non-modelled bill renders prediction-unavailable state.
- State bill renders `StatePredictionFirewall`.
- State bill does not render prediction metrics.
- Company exposure renders correctly with search and filters.
- No-exposure state renders informative message.
- Procedural timeline renders missing dates as `"Date not available"`.
- Related bills list renders and links.
- Source & provenance panel renders links and audit map.
- Watchlist modal opens and displays user watchlists.
- AI explanation success state renders grounded content.
- AI explanation unavailable fallback renders clean message.
- API failure displays error state with retry.
- Bill not found 404 displays institutional not found card.
- Loading skeleton state renders properly.
- `FACT`, `DERIVED`, `INTERPRETATION`, `PREDICTION` distinction verified.

### 19.2 TypeScript Compilation (`npm run typecheck`)
```
> frontend@0.1.0 typecheck
> tsc --noEmit
Exit Code: 0 (Zero errors)
```

### 19.3 Production Bundle Compilation (`npm run build`)
```
▲ Next.js 16.3.5 (Turbopack)
✓ Compiled successfully in 41s
✓ Generating static pages using 11 workers (22/22) in 5.7s
Route (app)
├ ƒ /bills/[billId]
Exit Code: 0
```

### 19.4 Backend FastAPI REST Endpoint Tests
```
.venv\Scripts\python -m pytest tests/test_api_endpoints.py -q
================= 20 passed, 4 warnings in 392.80s (0:06:32) ==================
Exit Code: 0 (20 passed, 0 failed)
```

---

## 20. Baseline Invariants Verification

All metrics presented across the dossier match the frozen baseline:
- **Central Legislative Bills:** 20 production bills.
- **Central Quantitative Companies:** 47 listed companies.
- **Central Bill-Company Pairs:** 940 pairs.
- **Central Predictions:** 4,700 records.
- **Central Decision Records:** 4,700 records.
- **Central Anticipation Scores:** 940 scores.
- **Central Stakeholder Reports:** 14,100 reports.
- **State Assembly Bills:** 44 bills (Andhra Pradesh: 12, Karnataka: 11, Kerala: 11, Telangana: 10).
- **State Quantitative Predictions:** Strictly **0** (verified by `StatePredictionFirewall`).
- **State Corporate Exposures:** 86 exposures.
- **Corporate Universe:** 70 companies (47 quantitative, 20 intelligence-only, 3 reference).
- **Unified Legislative Entities:** 66 records (20 Central + 44 State + 2 non-legislative).
- **Total Corporate Exposures:** 104 exposures.

---

## 21. Known Limitations & Future Work

- **Historical Passage Dates:** State legislative assembly portals do not consistently record intermediate floor vote dates; these are correctly displayed as `"Date not available"` in compliance with research integrity guidelines.
- **Company Detail Linkage:** Clicking on exposed corporate entities currently routes to `/companies/[companyId]`, which will be fully implemented in Task 8.14.6.

---

## 22. Exact Next Task

**TASK 8.14.6 — COMPANY INTELLIGENCE DETAIL IMPLEMENTATION**  
Build the production-quality corporate intelligence profile at `/companies/[companyId]`, integrating:
- Corporate identity, listing data, and corporate structure
- Quantitative market model coverage for the 47 listed entities
- Qualitative legislative footprint for the 20 intelligence entities
- Intelligence Company Firewall for non-modeled corporate entities
- Exposed bill matrices and statutory transmission mechanism links
