# TASK 8.14.3 — Next.js SaaS Frontend Foundation

**India Legislative Intelligence & Market Impact Prediction Platform**  
**Document Version:** 1.0.0  
**Status:** Complete  
**Date:** September 19, 2026  

---

## Executive Summary

Task 8.14.3 establishes the foundation of the production-facing SaaS frontend for the **India Legislative Intelligence & Market Impact Prediction Platform**. Built on Next.js 16 (App Router), React 19, TypeScript, and Tailwind CSS, this frontend serves as the institutional interface for policy analysts, market strategists, risk officers, and compliance executives.

The frontend is strictly decoupled from backend computation: **the verified FastAPI backend (Task 8.14.2) is the single source of truth**. The frontend communicates exclusively via standard HTTP REST requests to the FastAPI endpoints (`http://localhost:8000/api/v1`) and enforces strict institutional firewalling to uphold mathematical and institutional integrity.

---

## 1. Architectural Principles & Critical Rules

### 1.1 Single Source of Truth
- The frontend **never** accesses local storage JSONs or Python repositories directly.
- The frontend **never** calculates predictions, confidence scores, or sector aggregations in TypeScript.
- The frontend **never** invents or estimates mock predictions for State bills.
- All data displayed originates directly from the FastAPI backend API endpoints.

### 1.2 Dual Institutional Firewalls

#### Firewall 1: State Prediction Firewall (`StatePredictionFirewall.tsx`)
- **Institutional Context:** Predictive machine learning models (trained on historical Parliamentary legislative outcomes and BSE/NSE market indices) apply exclusively to Central legislation. State legislative outcomes are subject to federal dynamics, regional coalition structures, and distinct state assembly procedural timelines that are not modelled in the quantitative prediction engine.
- **Frontend Enforcement:** When displaying any State bill dossier, predictive cards, probabilistic gauges, and market impact projections are strictly blocked.
- **Institutional Disclosure:** Instead of predictions, the platform displays an informative badge (`State Intelligence Only`), a legal/methodological disclosure explaining why predictions are unavailable, and analytical coverage notes.

#### Firewall 2: Intelligence Company Firewall (`IntelligenceCompanyFirewall.tsx`)
- **Institutional Context:** The platform monitors two distinct classes of corporate entities:
  1. *Quantitative Impact Companies:* Publicly listed entities with historical stock price series correlated to Central legislative announcements.
  2. *Intelligence-Only Companies:* Unlisted, regional, cooperative, or private firms tracked for policy exposure and qualitative impact without quantitative price predictions.
- **Frontend Enforcement:** Intelligence-only entities are barred from displaying price fluctuation models or stock volatility forecasts, displaying instead regulatory exposure vectors, qualitative risk ratings, and supply chain dependencies.

---

## 2. Directory Structure & Information Architecture

```
frontend/
├── app/
│   ├── layout.tsx                     # Institutional Root Layout (Sidebar + Header + Shell)
│   ├── globals.css                    # Design system tokens & Tailwind CSS configuration
│   ├── page.tsx                       # Root redirect -> /overview
│   ├── overview/                      # Real-time Executive Overview (Live API connection)
│   │   ├── page.tsx
│   │   └── OverviewContent.tsx
│   ├── explorer/                      # Unified Legislative & Corporate Discovery
│   ├── bills/                         # Central & State Bills Discovery
│   │   ├── page.tsx
│   │   ├── BillsContent.tsx
│   │   ├── [billId]/                  # Bill Dossier with StatePredictionFirewall
│   │   │   ├── page.tsx
│   │   │   └── BillDetailContent.tsx
│   │   └── compare/                   # Legislative Comparative Analysis
│   ├── companies/                     # Corporate Universe Discovery
│   │   ├── page.tsx
│   │   └── [companyId]/               # Company Dossier with IntelligenceCompanyFirewall
│   │       ├── page.tsx
│   │       └── CompanyDetailContent.tsx
│   ├── predictions/                   # Quantitative Prediction Engine (Central Only)
│   │   ├── page.tsx
│   │   └── [predictionId]/
│   ├── states/                        # State Intelligence Assemblies (KA, MH, TN, DL)
│   ├── risk/                          # Portfolio & Policy Risk Aggregation
│   ├── anticipation/                  # Pre-introduction Legislative Signals
│   ├── monitoring/                    # Real-time Web & Gazette Scrapers Status
│   ├── watchlists/                    # User & Portfolio Legislative Watchlists
│   ├── alerts/                        # Real-time Triggered Alerts Center
│   ├── notifications/                 # In-App & Multi-channel Dispatch
│   ├── ai-analyst/                    # Groq LLaMA-3.3 Institutional Q&A
│   ├── coverage/                      # System Coverage & Health Registry
│   ├── sectors/                       # 14 Economic Sectors Breakdown
│   ├── industries/                    # 48 Sub-industry Exposure Matrices
│   └── settings/                      # API Keys, Org Preferences, Theme Settings
├── components/
│   ├── ui/                            # Atomic UI primitives (Badge, Button, Card, Skeleton, etc.)
│   ├── layout/                        # Shell layout (Sidebar, Header, Navigation)
│   ├── firewalls/                     # StatePredictionFirewall, IntelligenceCompanyFirewall
│   └── coverage/                      # CapabilityBadge, CoverageStatus
├── hooks/                             # Custom React hooks (useApi, useCoverage, useSearch)
├── lib/
│   ├── api/                           # Typed API clients for all 12 backend services
│   ├── errors.ts                      # Standardized ApiError & network error handling
│   └── utils.ts                       # Classnames, formatters, currency helpers
├── types/
│   └── api.ts                         # Complete TypeScript interfaces mirroring FastAPI Pydantic schemas
└── __tests__/                         # Vitest + React Testing Library test suites
```

---

## 3. API Client Layer

The API client layer (`lib/api/`) provides strongly-typed fetch wrappers that map directly to the FastAPI endpoints verified in Task 8.14.2:

| Client Module | Backend Service | Primary Endpoints |
|---|---|---|
| `client.ts` | Base HTTP Handler | Configurable `NEXT_PUBLIC_API_BASE_URL` with retry and error serialization |
| `coverage.ts` | System Coverage API | `GET /api/v1/coverage` |
| `bills.ts` | Legislative Bills API | `GET /api/v1/bills`, `GET /api/v1/bills/{id}` |
| `companies.ts` | Company Exposure API | `GET /api/v1/companies`, `GET /api/v1/companies/{id}` |
| `predictions.ts` | Prediction Engine API | `GET /api/v1/predictions`, `GET /api/v1/predictions/{id}` |
| `states.ts` | State Assembly API | `GET /api/v1/states`, `GET /api/v1/states/{code}` |
| `search.ts` | Unified Search API | `GET /api/v1/search?q={query}` |
| `monitoring.ts` | Scraper Monitor API | `GET /api/v1/monitoring/status` |
| `watchlists.ts` | Watchlist Service | `GET /api/v1/watchlists`, `POST /api/v1/watchlists` |
| `alerts.ts` | Alert Matcher API | `GET /api/v1/alerts/events` |
| `notifications.ts` | Notification Dispatch | `GET /api/v1/notifications` |
| `ai.ts` | AI Analyst Service | `POST /api/v1/ai/query` |

---

## 4. Institutional Design System & UI Components

A refined institutional palette tailored for financial markets and government affairs:
- **Primary Navy:** Deep slate navy (`#0B132B`, `#1C2541`) for high-contrast data visualization.
- **Accent Emerald:** Positive regulatory indicators and high confidence markers (`#10B981`, `#059669`).
- **Accent Amber/Ruby:** Moderate and high regulatory risk signals (`#F59E0B`, `#EF4444`).
- **Jurisdiction Tokens:** Saffron accent for Central Parliament (`#EA580C`), Azure for State Assemblies (`#2563EB`).

Key reusable components implemented:
1. `Badge`: Supports status, jurisdiction, exposure level, and confidence indicators.
2. `Card` & `StatCard`: High-density metric display with trend indicators.
3. `Skeleton`: Layout-matching placeholders for suspense and data fetching states.
4. `SearchInput`: Debounced search interface with keyboard accessibility.
5. `PlaceholderPage`: Professional informational architecture shells for upcoming modules.

---

## 5. Verification & Testing

### 5.1 Static Type Analysis
- **TypeScript:** Strict typecheck executed via `tsc --noEmit`.
- **Result:** `0 errors across all source and test files`.

### 5.2 Unit and Component Testing
- **Framework:** Vitest 5.0 with `@testing-library/react` and `@testing-library/jest-dom`.
- **Coverage Areas:**
  - API Client error handling and timeout scenarios.
  - State Prediction Firewall blocking logic and informational displays.
  - Intelligence Company Firewall disclosure logic.
  - Capability badge jurisdiction rendering.
  - Overview executive dashboard data orchestration.

---

## 6. Conclusion

Task 8.14.3 successfully establishes a rock-solid, production-grade Next.js SaaS frontend foundation. It guarantees strict adherence to backend authority, models institutional governance through programmatic firewalls, and prepares the platform for production deployment and high-frequency analytical workflows.
