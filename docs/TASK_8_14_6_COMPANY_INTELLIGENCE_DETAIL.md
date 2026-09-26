# TASK 8.14.6 — Company Intelligence Detail Implementation

**India Legislative Intelligence & Market Impact Prediction Platform**  
**Document Version:** 1.0.0  
**Status:** Complete  
**Date:** September 19, 2026  

---

## Executive Summary

Task 8.14.6 delivers the production-quality **Corporate Intelligence Profile** at `/companies/[companyId]`. This page serves as the definitive institutional hub for analyzing how Indian legislation impacts listed enterprises, unlisted entities, public sector undertakings, and regional infrastructure operators.

A fundamental pillar of this implementation is the **rigorous, architectural distinction between two corporate universes**:
1. **MODE A — Quantitative / Prediction-Eligible Listed Companies (47 Central securities):**
   - Listed on NSE/BSE with active equity modeling across 20 Central enactments.
   - 940 pairs, 4,700 multi-horizon econometric predictions, 4,700 decision support records, 940 pre-event anticipation scores.
2. **MODE B — Intelligence-Only / Qualitative Companies & Entities (20 intelligence entities + 3 reference entities):**
   - Unlisted corporates, statutory authorities, and public utilities.
   - Subject to the permanently active `IntelligenceCompanyFirewall`: **strictly 0 stock predictions, 0 returns, and 0 price targets**.

The application enforces total statutory isolation: state-level legislative exposures across both universes are strictly qualitative intelligence and never generate synthetic or fabricated equity predictions.

---

## 1. Architectural Blueprint & Data Flow

The profile adheres to the platform's multi-tier architecture with FastAPI as the authoritative source of truth:

```
Next.js Page (/companies/[companyId])
         │
         ▼
CompanyDetailContent (Client Component Orchestrator)
  ├─ companiesApi.getCompany(companyId)
  ├─ companiesApi.getCompanyPredictions(companyId)
  ├─ companiesApi.getCompanyExposures(companyId)
  ├─ companiesApi.getCompanyAnticipation(companyId)
  ├─ companiesApi.listCompanies(...)
  ├─ watchlistsApi.listWatchlists()
  └─ aiApi.explainCompany() / aiApi.ask()
         │
         ▼ (HTTP JSON REST)
FastAPI REST API Layer (/api/v1)
  ├─ GET  /api/v1/companies/{company_id}
  ├─ GET  /api/v1/companies/{company_id}/predictions
  ├─ GET  /api/v1/companies/{company_id}/exposures
  ├─ GET  /api/v1/companies/{company_id}/anticipation
  ├─ GET  /api/v1/companies/{company_id}/bills/{bill_id}/explain
  ├─ GET  /api/v1/predictions/{prediction_id}/decision
  ├─ GET  /api/v1/ai/explain/company/{company_id}
  ├─ POST /api/v1/ai/ask
  ├─ GET  /api/v1/watchlists
  └─ POST /api/v1/watchlists/{id}/items
         │
         ▼
Authoritative Repositories (Python Domain Singletons)
  ├─ UnifiedLegislativeDiscoveryService
  ├─ CompanyExposureRepository (Central quantitative & qualitative exposures)
  ├─ StateCorporateExposureRepository (86 state exposures across 44 state bills)
  ├─ PredictionRepository & DecisionRepository (4,700 frozen records)
  ├─ AnticipationRepository (940 frozen pairs)
  ├─ WatchlistService & WatchlistRepository
  └─ AIExplanationService (Groq LLaMA-3.3 with offline fallback guard)
```

---

## 2. API Dependencies & Contracts Consumed

| Capability | FastAPI Route | Response Schema | Client Method |
| :--- | :--- | :--- | :--- |
| **Company Profile** | `GET /api/v1/companies/{id}` | `CompanyDetailResponse` | `companiesApi.getCompany(id)` |
| **Prediction Projections** | `GET /api/v1/companies/{id}/predictions` | `CompanyPredictionStatusResponse` | `companiesApi.getCompanyPredictions(id)` |
| **Legislative Exposures** | `GET /api/v1/companies/{id}/exposures` | `list[CompanyBillExposure]` | `companiesApi.getCompanyExposures(id)` |
| **Anticipation Scores** | `GET /api/v1/companies/{id}/anticipation` | `CompanyAnticipationResponse` | `companiesApi.getCompanyAnticipation(id)` |
| **Decision Record** | `GET /api/v1/predictions/{id}/decision` | `DecisionRecordResponse` | `predictionsApi.getPredictionDecision(id)` |
| **AI Grounded Explain** | `GET /api/v1/ai/explain/company/{id}` | `AIAskResponse` | `aiApi.explainCompany(id, op, persona)` |
| **AI Grounded Ask** | `POST /api/v1/ai/ask` | `AIAskResponse` | `aiApi.ask(body)` |
| **Watchlist Index** | `GET /api/v1/watchlists` | `list[WatchlistResponse]` | `watchlistsApi.listWatchlists()` |
| **Watchlist Subscription**| `POST /api/v1/watchlists/{id}/items` | `WatchlistItemResponse` | `watchlistsApi.addItem(id, body)` |

### Backend Route Additions in Task 8.14.6:
1. `GET /api/v1/companies/{company_id}/anticipation`:
   - Inspects `company_id` against the frozen quantitative set (47 companies).
   - If non-quantitative or intelligence entity, returns firewall-protected response with `available: false`, `reason: "INTELLIGENCE_ONLY_ENTITY"`, and `scores: []`.
   - If quantitative, retrieves all company anticipation scores from `AnticipationRepository.get_scores_by_company(isin)`.
2. `GET /api/v1/companies/{company_id}/bills/{bill_id}/explain`:
   - Alias to `ai_service.explain_company_bill_impact(...)` providing bill-company pair grounding.

---

## 3. Two-Universe Discrimination (Mode A vs Mode B)

The UI never confuses or conflates the quantitative and qualitative universes:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          MODE A: QUANTITATIVE                          │
├────────────────────────────────────────────────────────────────────────┤
│ • Entity Type: Listed Indian Corporate (47 securities)                 │
│ • Header Badges: 📈 QUANTITATIVE · Level 1 Market Modelled · LISTED    │
│ • Tabs Available: Overview · Footprint · Transmission · Regional ·     │
│                   Predictions · Anticipation · Stakeholders · Audit    │
│ • Market Predictions: Multi-horizon econometric models ([0,1], [0,2],  │
│   [0,5], [-1,+1], [-5,+5]) with confidence, alpha, and decisions.      │
│ • Anticipation: Pre-event diffusion scores and diagnostic flags.       │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                        MODE B: INTELLIGENCE ONLY                       │
├────────────────────────────────────────────────────────────────────────┤
│ • Entity Type: Unlisted / State-Owned / Public Utility (23 entities)   │
│ • Header Badges: 🔬 INTELLIGENCE ONLY · Level 2 Intelligence · UNLISTED│
│ • Prediction Tab: Displays "Prediction Firewall" tab with shield icon. │
│ • Firewall Card: IntelligenceCompanyFirewall permanently active:       │
│   "Market prediction unavailable for this entity. Intelligence-only    │
│   entities are qualitative by design. Stock predictions remain 0."     │
│ • Anticipation Tab: Displays "Anticipation Diagnostics Not Applicable".│
│ • Footprint & Regional: Full statutory exposure matrix remains active. │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Frontend Component Hierarchy

The profile dossier is organized modularly under `frontend/components/companies/`:

```
frontend/components/companies/
├── CompanyHeader.tsx
│   ├── Breadcrumb navigation
│   ├── Universe classification badges (📈 QUANTITATIVE vs 🔬 INTELLIGENCE ONLY)
│   ├── Exchange tickers (NSE / BSE), ISIN, Sector, Industry, Corporate Group
│   ├── Data Quality tag (✓ VERIFIED) and Semantic Badge (FACT)
│   ├── Watchlist action button (⭐ Add to Watchlist)
│   └── Quick summary metrics (Central bills, State bills, Direct/Indirect vectors)
├── CompanyOverview.tsx
│   ├── Business profile & operational summary
│   ├── Sector & core industry alignment
│   ├── Legislative exposure distribution card (Total, Central, State, Direct, Indirect)
│   ├── Key corporate metadata grid (CIN, ISIN, Ownership, Regulators, Facilities)
│   └── Statutory isolation notice for regional operations
├── CompanyExposureMatrix.tsx
│   ├── Interactive filter toolbar (Search by title, Filter by jurisdiction: All / Central / State)
│   ├── Responsive tabular exposure matrix with clickable bill links
│   ├── Direct vs Indirect exposure vector badges
│   ├── Evidence strength indicators (STRONG, MODERATE, WEAK)
│   └── Documented economic mechanism chips
├── EconomicTransmissionSection.tsx
│   ├── Step-by-step visual transmission flow:
│   │   [Statutory Provision] → [Transmission Channel] → [Corporate Financial Impact]
│   ├── Direct channels (CapEx mandates, compliance costs, royalty formulas)
│   ├── Indirect channels (Supply chain friction, feedstock availability, demand shifts)
│   └── Quantitative vs Qualitative impact boundary demarcation
├── StateGeographicSection.tsx
│   ├── Active operating states distribution
│   ├── Key operational facilities and infrastructure assets
│   ├── State legislative exposure dossier
│   └── Statutory Isolation Warning Card:
│       "State stock predictions remain strictly 0. State exposures provide
│       qualitative regulatory intelligence without generating equity models."
├── CompanyPredictionsSection.tsx
│   ├── Event window filter ([0,1], [0,2], [0,5], [-1,+1], [-5,+5])
│   ├── Central Market Impact Projections table (Direction, Magnitude, Confidence, Alpha)
│   ├── Interactive decision support drilldown drawer:
│   │   Confidence band, reasoning summary, statutory drivers, scenario risk factors
│   ├── Prediction unavailable fallback state
│   └── IntelligenceCompanyFirewall shield card for Mode B entities
├── CompanyAnticipationSection.tsx
│   ├── Information diffusion evidence classifications:
│   │   STRONG_EVIDENCE, MODERATE_EVIDENCE, WEAK_EVIDENCE, NO_DIFFUSION
│   ├── Composite anticipation score gauges
│   ├── Signal breakdown (Market abnormal volume vs Parliamentary media volume)
│   ├── Institutional Disclaimer:
│   │   "Pre-event diagnostics measure aggregate public information diffusion only.
│   │   They do not allege or imply insider trading or illicit market conduct."
│   └── Firewall fallback for Mode B entities
├── CompanyStakeholderIntelligence.tsx
│   ├── Multi-perspective impact assessments:
│   │   Investor · Executive · Compliance · Vendor · Consumer · Regional Public
│   └── Mandatory semantic classification badges:
│       [FACT] · [DERIVED] · [INTERPRETATION] · [PREDICTION]
├── CompanyAIPanel.tsx
│   ├── Grounded analytical copilot powered by Groq LLaMA-3.3
│   ├── One-click contextual prompt chips:
│   │   "What legislation affects this company?"
│   │   "What economic mechanisms connect bills to this company?"
│   │   "What are the primary state regulatory risks?"
│   │   "Summarize legislative exposure for executives."
│   ├── Provenance attribution badges and grounded response rendering
│   └── Graceful offline fallback guard
├── CompanyProvenanceSection.tsx
│   ├── Data Quality & Verification Audit
│   ├── Source provenance (Corporate Registrar, Stock Exchange, Gazette, PRS)
│   └── Traceable statutory evidence records list
├── CompanyWatchlistModal.tsx
│   ├── Selection of existing user watchlists
│   ├── Inline creation of new thematic watchlists
│   ├── Notification toggle (Email / Slack alerts)
│   └── Subscribes via POST /api/v1/watchlists/{id}/items
└── RelatedCompaniesCard.tsx
    ├── Peer companies in the same sector or corporate group
    ├── Quantitative vs Qualitative indicators for peer entities
    └── Clickable routing to peer dossiers
```

---

## 5. Strict Neutral Framing & Compliance Guardrails

To prevent misinterpretation in regulated capital markets, the profile enforces strict institutional terminology:

1. **No Buy/Sell/Hold Recommendations:**
   - Predictions are labeled strictly as:  
     `Multi-Horizon Econometric Projections` / `Directional Market Impact`.
   - Values are reported as econometric abnormal returns ($\Delta\%$) with confidence intervals ($p$-values, confidence scores), never advisory buy/sell ratings.
2. **Pre-Event Anticipation Disclaimer:**
   - Explicitly displays:
     > *"🛡️ Institutional Disclaimer: Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law."*
3. **Statutory Isolation Disclaimer:**
   - Explicitly displays:
     > *"🛡️ Statutory Isolation Guarantee: State legislative exposure records represent qualitative operational intelligence. State stock predictions remain strictly 0 to preserve model integrity."*
4. **Epistemic Classification:**
   - Every substantive insight is tagged with its epistemic status:  
     `FACT` (statutory filing, gazette entry), `DERIVED` (econometric calculation), `INTERPRETATION` (policy analyst synthesis), or `PREDICTION` (forward-looking econometric projection).

---

## 6. Verification & Test Suite

The implementation has been thoroughly verified across all layers:

### A. Frontend Vitest Integration Tests (`frontend/__tests__/pages/company-detail.test.tsx`)
**18 comprehensive test cases covering:**
1. Quantitative company profile rendering (Mode A indicators)
2. Intelligence-only company profile rendering (Mode B indicators)
3. Company not found (404 state)
4. Company exposure list & distribution counts
5. Exposure matrix filters (search query, jurisdiction toggle)
6. Central prediction section with event windows & neutral wording
7. Prediction unavailable state
8. `IntelligenceCompanyFirewall` engagement
9. State exposure section & statutory isolation guarantee
10. Market relevance qualitative classification
11. Pre-event anticipation diagnostics & non-allegation disclaimer
12. Source provenance panel & data quality audit
13. Watchlist action & modal subscription
14. Grounded AI assistant query resolution
15. AI unreachable graceful offline fallback
16. Network/server error retry state
17. Loading skeleton display
18. Explicit semantic badges (`FACT`, `DERIVED`, `INTERPRETATION`, `PREDICTION`)

**Results:**
```
✓ __tests__/pages/company-detail.test.tsx (18 tests) [PASSED]
Test Files: 9 passed (9)
Tests:      88 passed (88)
Duration:   13.03s
```

### B. TypeScript Compilation
```
> frontend@0.1.0 typecheck
> tsc --noEmit
Exit code: 0 (0 errors)
```

### C. Production Build
```
> frontend@0.1.0 build
> next build
✓ Compiled successfully in 36.3s
✓ Generating static pages using 11 workers (22/22) in 5.4s
Route (app): /companies/[companyId] (Dynamic server-rendered on demand)
Exit code: 0
```

### D. FastAPI Backend Regression Suite (`tests/test_api_endpoints.py`)
```
======================= 21 passed, 4 warnings in 15.06s =======================
Exit code: 0
```

---

## 7. Baseline Alignment

All platform frozen data invariants remain strictly preserved:
- **Central Legislative Scope:** 20 Central bills, 47 quantitative companies, 940 pairs, 4,700 predictions, 4,700 decisions, 940 anticipation scores.
- **State Legislative Scope:** 44 bills across 11 states, 44 PDFs, 44 knowledge records, 86 corporate exposures, strictly 0 state predictions.
- **Corporate Scope:** 70 total entities (47 quantitative listed securities, 20 intelligence entities, 3 reference entities).
- **Unified Scope:** 66 legislative records, 104 company exposures.
