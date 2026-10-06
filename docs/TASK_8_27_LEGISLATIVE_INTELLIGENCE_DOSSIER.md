# TASK 8.27 — LEGISLATIVE INTELLIGENCE ENRICHMENT & BILL DOSSIER 2.0

## Executive Summary

Task 8.27 upgrades the legislative knowledge layer into a comprehensive **Legislative Intelligence Dossier (Dossier 2.0)** across Central, State, and Live-discovered bills. The implementation adheres strictly to the **Separation of Epistemic Tiers** (`FACT`, `INTERPRETATION`, `PREDICTION`) and enforces the **Immutable Analytical Invariant**: zero automatic stock predictions for newly discovered or State bills.

---

## 1. Epistemic Architecture Separation

| Tier | Definition | Verification Standard | Example |
| :--- | :--- | :--- | :--- |
| **FACT** | Directly verifiable from an authoritative official source | Parliamentary gazette, official PDF SHA-256, legislative bulletin | Introduction date, official bill number, statutory text |
| **INTERPRETATION** | Derived explanation, synthesis, or non-technical summary | Grounded reasoning referencing documented statutory sections | Plain-language brief, sector transmission channels |
| **PREDICTION** | Quantitative model projections with backtested confidence | Frozen analytical model (20 Central bills, 47 companies, 940 pairs) across authoritative horizons: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]` | Multi-horizon cumulative abnormal return projections |

### Epistemic Rules:
1. **Never conflate tiers**: An explanation or impact interpretation is never labeled or presented as a statutory fact.
2. **Document vs. Legislative Status Separation**: Modifications to document metadata (file re-indexing, PDF hash updates, URL updates) are partitioned into `document_changes` and are strictly separated from `legislative_changes` (formal procedural transitions). A document re-crawl is never claimed as a statutory status change.
3. **No financial advice**: Stakeholder views and corporate linkages describe statutory transmission channels; they strictly do not provide Buy/Sell/Hold or investment recommendations, nor do they rank stakeholders.

---

## 2. Model Status & Firewall Classifications

| Model Status Code | Badge Label | Eligibility & Description | Prediction Availability |
| :--- | :--- | :--- | :--- |
| `MODELLED` | `MODELLED — CENTRAL QUANTITATIVE` | Exactly the 20 frozen Central production bills in the baseline dataset | **Yes** (4,700 predictions across 5 authoritative horizons: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`) |
| `NOT_ELIGIBLE` | `NOT ELIGIBLE FOR STOCK MODEL` | All 44 State bills and Central non-legislative auxiliary records (`key-issues-and-analysis`, `service-bill`) | **No** (Statutory 0 predictions) |
| `KNOWLEDGE_ONLY` | `LIVE — KNOWLEDGE ONLY` | Live-discovered bills ingested via monitoring pipeline | **No** (Strict firewall) |
| `PENDING_REVIEW` | `LIVE — PENDING REVIEW` | Live measures queued for quantitative analytical methodology review | **No** (Strict firewall) |

---

## 3. Dossier 2.0 Domain Models & Schemas

Created in `schemas/bill_dossier.py` and exposed via `api/schemas.py`:

```python
class EnrichedBillDossier:
    identity: DossierIdentity
    status: DossierStatus
    content: DossierContent
    impact_context: DossierImpactContext
    provenance: DossierProvenance
    model_status: str                       # MODELLED | NOT_ELIGIBLE | KNOWLEDGE_ONLY | PENDING_REVIEW
    model_status_label: str
    model_status_description: str
    prediction_available: bool
    timeline: list[TimelineEvent]
    change_summary: BillChangeSummary
    stakeholder_views: dict[str, StakeholderPersonaView]
    sector_exposures: list[SectorExposureItem]
    company_exposures: list[LinkedCompanyExposureItem]
    documents: list[BillDocumentItem]
    ai_explanation: Optional[dict]
```

---

## 4. Key Subsystem Implementations

### 4.1 Chronological Evidence-Based Timeline (`LegislativeTimeline.tsx`)
- Synthesizes authoritative procedural journey milestones (`INTRODUCTION`, `COMMITTEE`, `FIRST_CHAMBER_PASSAGE`, `SECOND_CHAMBER_PASSAGE`, `PRESIDENTIAL_ASSENT`, `GAZETTE_NOTIFICATION`).
- Incorporates verified monitoring change events from `LiveKnowledgeRepository`.
- Visual stage badges, chamber indicators, official document links, and verification flags.

### 4.2 Structured "What Changed?" View (`WhatChangedView.tsx`)
- Partitions modifications into:
  - `legislative_changes`: Field transitions (status, stage, ministry, bill number) with before/after diffs and authoritative source.
  - `document_changes`: File-level modifications (PDF hash, file size, URL) with cryptographic verification.
- Displays prominent **Strict Epistemic Separation Notice**.

### 4.3 Plain-Language Non-Technical Briefing (`PlainLanguageSection.tsx`)
- Answers the 5 canonical non-expert questions:
  1. What is this bill?
  2. What does it change?
  3. Who could be affected?
  4. Why could it matter economically?
  5. What is still unknown or pending?
- Includes explicit `INTERPRETATION` epistemic notice and grounded source citations.

### 4.4 Multi-Persona Stakeholder Intelligence (`StakeholderIntelligence.tsx`)
- Structured views across 5 canonical personas:
  - `INVESTOR`: Regulatory capital, compliance cost, operational headroom (No Buy/Sell/Hold).
  - `BUSINESS_OWNER`: Operational adaptation, compliance filings, supply chain contracting.
  - `EMPLOYEE_PROFESSIONAL`: Labor standards, workplace safety, certification demands.
  - `COMMON_CITIZEN`: Public rights, service transparency, consumer dispute redressal.
  - `RESEARCHER`: Constitutional competency, legislative drafting, comparative federalism.
- Displays distinct cards for Fact, Derived Vector, Interpretation, and Market Sensitivity Tier.

### 4.5 Sector & Industry Exposure (`SectorIndustrySection.tsx`)
- Integrated with `Macro Sector Directory` and `IndustryIntelligenceService`.
- Classifies exposures into `DIRECT` (primary statutory mandate) and `INDIRECT` (downstream/supply chain).
- Maps regulated business activities and canonical industry classifications without relying on company name similarity.

### 4.6 Document Viewer Integration & SHA-256 Provenance (`DocumentSourcesSection.tsx`)
- In-platform document viewing via `DocumentViewer`.
- Safe URL validation against external parliamentary and assembly portals.
- SHA-256 cryptographic checksum display with verification badges.
- Safe fallbacks for portal-only or pending-retrieval documents without fabricating hashes.

---

## 5. API Endpoints

All endpoints support multi-tenant isolation headers (`X-Tenant-ID`, `X-User-ID`):

| Endpoint | Method | Response Model | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/bills/{bill_id}` | `GET` | `BillDetailResponse` | Enhanced legacy detail endpoint with backward compatibility |
| `/api/v1/bills/{bill_id}/dossier` | `GET` | `EnrichedBillDossierResponse` | Complete unified Dossier 2.0 |
| `/api/v1/bills/{bill_id}/timeline` | `GET` | `BillTimelineResponse` | Chronological evidence-grounded timeline |
| `/api/v1/bills/{bill_id}/changes` | `GET` | `BillChangesResponse` | Structured document vs legislative change summary |
| `/api/v1/bills/{bill_id}/plain-language`| `GET` | `PlainLanguageResponse` | 5-question non-expert brief |
| `/api/v1/bills/{bill_id}/stakeholders` | `GET` | `BillStakeholdersResponse` | 5 canonical stakeholder views |
| `/api/v1/bills/{bill_id}/sectors` | `GET` | `BillSectorExposureResponse` | Macro Sector Directory exposures |
| `/api/v1/bills/{bill_id}/documents` | `GET` | `BillDocumentsResponse` | Official documents with SHA-256 metadata |
| `/api/v1/bills/{bill_id}/model-status` | `GET` | `BillModelStatusResponse` | Model status & prediction availability boundaries |

---

## 6. Frontend Assembly

- **Bill Header**: Integrated `ModelStatusBadge` (`MODELLED — CENTRAL QUANTITATIVE`, `NOT ELIGIBLE FOR STOCK MODEL`, `LIVE — KNOWLEDGE ONLY`, `LIVE — PENDING REVIEW`).
- **Bill Detail Layout**: 12 responsive tabs:
  1. `overview`: Plain-Language Brief, Executive Summary, Procedural Journey, Policy & Economic Vectors
  2. `timeline`: Chronological Event Timeline
  3. `changes`: What Changed View with Document vs Legislative Separation
  4. `provisions`: Statutory Provisions with Authority Badges
  5. `sectors`: Affected Sectors & Industries
  6. `exposures`: Documented Corporate Exposure Table
  7. `predictions`: Central Market Predictions (or State Prediction Firewall)
  8. `anticipation`: Pre-Event Legislative Anticipation & Diffusion
  9. `stakeholders`: 5-Persona Stakeholder Intelligence
  10. `documents`: In-Platform Viewer & SHA-256 Source Documents
  11. `ai`: Grounded Groq AI Explanations Copilot
  12. `provenance`: Authoritative Source Metadata & Gazette Links

---

## 7. Verification & Invariance Results

### 7.1 Backend Unit & Integration Tests
- **`tests/test_task_8_27_dossier.py`**: **20 passed in 2.28s** (100% pass rate).
- **`tests/test_task_8_26_live_intelligence.py`**: **30 passed in 0.95s** (100% pass rate).
- **`tests/test_analytical_firewall_regression.py::test_state_statutory_baseline_and_zero_prediction_firewall`**: **PASSED**.

### 7.2 Frontend Tests & Build
- **`npm --prefix frontend run typecheck`**: **0 errors** (TypeScript validation clean).
- **`npm --prefix frontend test -- --run`**: **22 test files passed, 205 tests passed**.
- **`npm --prefix frontend run build`**: **Compiled successfully, 31 routes generated**.

### 7.3 Frozen Analytical Baseline Hash
- **`shasum -a 256 docs/production_baseline.json`**:
  `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7` (**MATCHED / UNMODIFIED**).
- Central baseline: 20 production bills, 47 quant companies, 940 pairs, 4700 predictions across 5 authoritative windows (`[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`), 4700 decisions, 940 anticipation scores.
- State baseline: 44 bills, 0 stock predictions, 0 decisions, 0 anticipation scores.
