# TASK 8.14.7 — Prediction, Risk & Anticipation Analytics UI Implementation

**India Legislative Intelligence & Market Impact Platform**  
**Document Version:** 1.0.0  
**Status:** Complete  
**Date:** September 19, 2026  

---

## Executive Summary

Task 8.14.7 delivers the production-quality research & analytics UI layer across the four primary predictive, risk, and information diffusion routes of the platform:
1. `/predictions`: Comprehensive Prediction Analytics dashboard with multi-dimensional filtering, coverage baselines, interactive event-horizon comparison, confidence distribution, and epistemic badging.
2. `/predictions/[predictionId]`: Single Prediction Dossier featuring 4-zone epistemic separation (`[FACT]`, `[DERIVED]`, `[PREDICTION]`, `[INTERPRETATION]`), decision support drilldown, pre-event diffusion context, stakeholder briefs, and institutional non-financial advice notices.
3. `/risk`: Institutional Risk Analytics dashboard with a 5-tier deterministic risk model (`VERY_LOW` to `VERY_HIGH`), pricing-in risk matrix, sector risk dispersion, tabbed bill & company risk profiles, and portfolio-level risk aggregation with watchlist integration and graceful qualitative-entity notices.
4. `/anticipation`: Pre-Event Information Diffusion dashboard evaluating all 940 evaluated pairs, 4 neutral classification tiers (`NO_EVIDENCE` to `STRONG_EVIDENCE`), pre-event trading windows CAR statistics, top flagged diffusion pairs, paginated filterable diagnostic matrix, and verbatim regulatory disclaimers.

---

## 1. Statutory Firewalls & Invariants

Throughout this implementation, strict architectural and statutory firewalls were enforced:
- **State Prediction Firewall (`StatePredictionFirewall`):** State assemblies have strictly 0 market predictions and 0 quantitative risk/anticipation scores. State assembly bills possess qualitative statutory exposure and compliance context only.
- **Intelligence Company Firewall (`IntelligenceCompanyFirewall`):** Unmodeled qualitative corporate intelligence entities have strictly 0 quantitative stock predictions or anticipation scores.
- **Zero Retraining / Data Mutation:** Central prediction, decision support, anticipation, event study, and backtest datasets remain frozen and read-only.
- **Backend-Derived Econometrics:** All calculations (CAR, market-moving probabilities, risk bands, pricing-in tiers, diffusion scores) remain strictly derived by backend services; no duplicate formulas in React.
- **Strictly Neutral Terminology:** No entity is accused of insider trading or illicit market conduct. Mandatory verbatim institutional disclaimer:
  > *"Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law."*
- **Regulatory Non-Financial Advice Notice:** Model outputs are strictly empirical research projections, never price targets or Buy/Sell/Hold advice.

---

## 2. Architecture & API Contracts

### A. FastAPI Endpoints & Routers

| Route | Method | Description |
|---|---|---|
| `/api/v1/predictions` | GET | Paginated predictions with filters: `bill_id`, `company_isin`, `sector`, `event_window`, `predicted_direction`, `predicted_market_moving`, `min_confidence`, `max_confidence`, `impact_strength`, `jurisdiction` |
| `/api/v1/predictions/{prediction_id}` | GET | Single prediction record with company name and sector enrichment |
| `/api/v1/predictions/{prediction_id}/decision` | GET | Decision support record with risk category, pricing-in risk, and stakeholder summaries |
| `/api/v1/predictions/{prediction_id}/anticipation` | GET | Anticipation score for single prediction record |
| `/api/v1/predictions/horizons/compare` | GET | Cross-horizon comparison across 5 validated event horizons with unmodeled horizon notices |
| `/api/v1/predictions/{prediction_id}/reports/{type}` | GET | Stakeholder report (`investor`, `business`, `public`) |
| `/api/v1/risk/summary` | GET | Aggregated risk metrics across 4,700 decision records: 5 risk bands, pricing-in distribution, sector breakdown, event window breakdown |
| `/api/v1/risk/bills` | GET | Bill-level risk profiles with dominant risk bands and high-risk enclave counts |
| `/api/v1/risk/companies` | GET | Company-level risk profiles with sector filters and prediction availability badges |
| `/api/v1/risk/portfolio` | POST | Portfolio-level risk aggregation by custom ISIN list or saved watchlist ID with graceful unmodeled company handling |
| `/api/v1/anticipation` | GET | Paginated anticipation diagnostics across 940 pairs with tier and flagged filters |
| `/api/v1/anticipation/summary` | GET | Aggregated anticipation summary: 4 neutral tiers, sector dispersion, multi-window CAR statistics, top flagged pairs, verbatim disclaimer |
| `/api/v1/anticipation/{bill_id}/{company_isin}` | GET | Single pair pre-event diagnostic detail |

### B. Frontend Clients & TypeScript Schemas

- `frontend/types/api.ts`: Defined `PredictionItem`, `HorizonComparisonItem`, `HorizonComparisonResponse`, `RiskBandDistribution`, `SectorRiskSummary`, `EventWindowRiskSummary`, `BillRiskSummary`, `CompanyRiskSummary`, `RiskSummaryResponse`, `PortfolioRiskRequest`, `PortfolioCompanyRiskItem`, `PortfolioRiskResponse`, `AnticipationItem`, `AnticipationSectorSummary`, `PreEventWindowSummary`, `FlaggedAnticipationPair`, `AnticipationSummaryResponse`.
- `frontend/lib/api/predictions.ts`: Typed client for all prediction endpoints including `compareHorizons`.
- `frontend/lib/api/risk.ts`: Typed client for risk summary, bills, companies, and portfolio evaluation.
- `frontend/lib/api/anticipation.ts`: Typed client for anticipation listing, summary, and single-pair detail.

---

## 3. UI Component Highlights

### 1. `/predictions` — Prediction Analytics Dashboard
- **Coverage Baseline Cards:** Verified 20 production bills, 47 quantitative companies, 940 pairs, 4,700 predictions, 5 event horizons, 0 State stock predictions.
- **Filter Bar:** Bill ID search, Company ISIN/symbol search, Sector dropdown, Event window dropdown, Predicted direction dropdown, Market-moving probability filter, Confidence threshold filter, Jurisdiction toggle.
- **Matrix Table:** Epistemic badges (`[FACT]`, `[DERIVED]`, `[PREDICTION]`), direction pill, market-moving progress bar, confidence score, impact tier, and direct link to prediction dossier.
- **Interactive Event-Horizon Comparison:** Multi-window tab strip (`[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`, `[0,1]`, `[0,2]`, `[0,5]`) showing modeled vs unmodeled horizons with clear explanation notices.
- **Confidence Distribution:** High (≥70%), Medium (40–70%), and Low (&lt;40%) statistical dispersion cards.
- **Grounded AI Analyst:** Grounded copilot with persona switcher (`INVESTOR`, `POLICY`, `GENERAL_PUBLIC`).

### 2. `/predictions/[predictionId]` — Single Prediction Dossier
- **Hero & Notice:** Non-financial advice disclaimer, bill and company badges, direction, confidence, and market-moving likelihood.
- **Zone 1: Verified Statutory & Entity Facts `[FACT]`:** Official bill ID, Central Parliament jurisdiction, ISIN, exchange ticker, economic sector.
- **Zone 2: Econometric Model Projections `[PREDICTION]`:** Event analysis window, direction, probability progress bar, impact tier, confidence score, model version.
- **Zone 3: Decision Support & Risk Classification `[DERIVED]`:** Deterministic risk band, pricing-in risk status, risk & impact scores, decision rationale, investor perspective, and corporate perspective.
- **Zone 4: Pre-Event Anticipation Context `[DERIVED]`:** Neutral classification tier, anticipation score, diffusion index, pre-event volume ratio, and mandatory disclaimer.
- **Stakeholder Reports Strip `[INTERPRETATION]`:** Tabbed view for Investor, Business, and Public briefs.
- **Cross-Horizon Navigation:** Comparative cards for the same pair across other temporal horizons.
- **Grounded AI Copilot & 404 Handling:** Integrated AI Analyst and graceful error/not-found states.

### 3. `/risk` — Institutional Risk Analytics Dashboard
- **5-Tier Deterministic Risk Model:** `VERY_LOW` (0.00–0.20), `LOW` (0.20–0.40), `MODERATE` (0.40–0.60), `HIGH` (0.60–0.80), `VERY_HIGH` (0.80–1.00) with cards and stacked proportional visual bar.
- **Pricing-in Risk Matrix:** Anticipatory absorption breakdown (`PRICED_IN`, `PARTIALLY_PRICED_IN`, `UNPRICED`, `NOT_APPLICABLE`).
- **Event Window Dispersion:** Risk scores across 5 event horizons.
- **Sector Risk Matrix:** Sector averages, total evaluations, high-risk count, and mini distribution bars.
- **Portfolio-Level Risk Aggregation:** Select saved watchlist or input custom comma-separated ISINs. Returns aggregate risk score, portfolio risk band, `SUFFICIENT_DATA` vs `INSUFFICIENT_DATA` status, and explicit informative notice regarding unmodeled qualitative intelligence entities.
- **Tabbed Entity Profiles:** Filterable Bill Risk Profiles and Company Risk Profiles with direct deep-links.

### 4. `/anticipation` — Pre-Event Information Diffusion Dashboard
- **Mandatory Verbatim Legal Disclaimer:** Rendered prominently at top and bottom:
  > *"Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law."*
- **Coverage Baseline:** 940 evaluated pairs, diffusion flags count, mean anticipation score, mean market signal, and mean info signal.
- **4 Neutral Classification Tiers:** `NO_EVIDENCE`, `WEAK_EVIDENCE`, `MODERATE_EVIDENCE`, `STRONG_EVIDENCE` with counts, percentages, descriptions, and stacked proportional bar.
- **Pre-Event Trading Windows CAR Statistics:** Analysis across `[-30,-21]`, `[-20,-11]`, `[-10,-3]`, `[-2,-1]`, `[-30,-1]` with Mean MAR, Mean CAR, observation counts, and statistically significant pairs count.
- **Highest Diffusion Pairs:** Top 10 ranked pairs with detected public signals.
- **940-Pair Diffusion Matrix:** Filterable by bill, company, classification tier, sector, and flagged-only toggle.

---

## 4. Verification & Test Suite Results

### A. Vitest Suite (Frontend)
- `__tests__/pages/predictions.test.tsx`: 5 tests passed.
- `__tests__/pages/prediction-detail.test.tsx`: 4 tests passed.
- `__tests__/pages/risk.test.tsx`: 4 tests passed.
- `__tests__/pages/anticipation.test.tsx`: 5 tests passed.
- **Total Frontend Test Suite:** 13 test files, **106 tests passed (100% pass rate)** in 20.91s.

### B. TypeScript Compilation
- `npm run typecheck`: **0 errors**.

### C. Next.js Production Build
- `npm run build`: Compiled successfully in 42s; all 22 static and dynamic routes generated cleanly.

### D. Pytest Suite (Backend)
- `tests/test_api_prediction_risk_anticipation.py`: 13 tests passed.
- `tests/test_api_endpoints.py`: 21 tests passed.
- **Total Backend Tests:** **34 passed (100% pass rate)**.
