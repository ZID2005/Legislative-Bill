# Task 8.9 — Unified India Legislative Discovery & Search Architecture

## 1. Architectural Overview

The **Unified India Legislative Discovery Layer** provides an integrated search, exploration, and navigation interface spanning Central Parliament legislation and Indian State legislature enactments. It serves as an authoritative knowledge access layer while strictly honoring the isolation of the frozen Central quantitative prediction engines.

```
                               ┌────────────────────────────────┐
                               │  Streamlit Dashboard Frontend  │
                               │  - India Legislative Explorer  │
                               │  - Global Search with Badges   │
                               └───────────────┬────────────────┘
                                               │
                               ┌───────────────▼────────────────┐
                               │ UnifiedLegislativeDiscovery    │
                               │ Service (services/)            │
                               │ - UnifiedBillRecord Schema     │
                               │ - Deterministic Search Engine  │
                               │ - Multi-Facet Filter Engine    │
                               │ - Temporal Date Sorter         │
                               │ - Related Bills Graph Engine   │
                               └───────┬────────────────┬───────┘
                                       │                │
            ┌──────────────────────────▼──┐          ┌──▼──────────────────────────┐
            │   Central Parliament Layer   │          │   State Legislatures Layer  │
            │   - BillRepository (22)      │          │   - StateKnowledgeRepo (44) │
            │   - KnowledgeRepository      │          │   - StateBillRepo (44)      │
            │   - MappingRepository        │          │   - StateCorporateExposure  │
            │   - DecisionRepository       │          │   - StateImpactAssessment   │
            │   - 4,700 Predictions (FROZEN│          │   - Exactly 0 Predictions   │
            └─────────────────────────────┘          └─────────────────────────────┘
```

---

## 2. Central vs. State Discovery Comparison

| Discovery Dimension | Central Government Legislation | Indian State Legislation |
| :--- | :--- | :--- |
| **Legislative Scope** | National (Parliament of India) | State-Specific (Vidhan Sabha / Vidhan Parishad) |
| **Active Records** | 22 (20 modelled in production + 2 auxiliary) | 44 (12 AP, 11 KA, 11 KL, 10 TG) |
| **Official Houses** | Lok Sabha, Rajya Sabha | Vidhan Sabha, Vidhan Parishad |
| **Policy Categorization** | Ministry taxonomy + sector mapping | State 10-domain policy taxonomy |
| **Corporate Exposure** | 47 production BSE/NSE companies mapped | 86 state-level corporate exposures (direct/indirect) |
| **Market Relevance** | HIGH (modeled securities in production) | HIGH, MEDIUM, LOW, NONE (evaluated qualitatively) |
| **Market Modeling** | ELIGIBLE (active quantitative pipeline) | NOT_ELIGIBLE or CONDITIONALLY_ELIGIBLE |
| **Predictions** | **4,700 active stock return predictions** | **EXACTLY 0 (Strictly Isolated)** |
| **Detail Routing** | `🔍 Bill Intelligence` deep-dive flow | `📋 State Legislative Dossier` view |

---

## 3. Supported States & Coverage Transparency

Coverage is tracked in `data/state_bills/state_coverage_registry.json`.

### Active Implemented States (4 States — 44 Bills)
1. **Andhra Pradesh** (12 bills) — Official source: `aplegislature.org`
2. **Karnataka** (11 bills) — Official source: `kla.kar.nic.in`
3. **Kerala** (11 bills) — Official source: `niyamasabha.nic.in`
4. **Telangana** (10 bills) — Official source: `telanganalegislature.org.in`

### Planned / Not Yet Implemented (24 States + Union Territories)
All other 24 Indian States (Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Madhya Pradesh, Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, Sikkim, Tamil Nadu, Tripura, Uttar Pradesh, Uttarakhand, West Bengal) are registered as `PLANNED` with `bills_count: 0`.

**Architectural Rule:** The system never fabricates stub bills or generates synthetic records for un-ingested states.

---

## 4. Search and Filter Engine

- **Deterministic Ranking**:
  1. Exact title or bill number match (score: 100)
  2. Full query in title / bill number (score: 60-70)
  3. Query terms in title (score: +25/term)
  4. Query terms in sector/domain/stakeholder (score: +15-20/term)
  5. Query terms in summary text (score: +8/term)
- **Zero LLM Dependency**: All rankings are deterministic and rule-grounded.
- **Combined Filtering**: Jurisdiction, State, Policy Domain, Economic Sector, Stakeholder, Status, Year, Corporate Exposure, Market Relevance, Modeling Eligibility, Data Sufficiency.

---

## 5. Temporal Integrity & "New Bills" Discovery

- Sorting relies **strictly on authoritative legislative introduction dates** from official gazettes and parliamentary bulletins.
- The system **never infers an introduction date** from PDF modification times, file download times, or filesystem metadata.
- When an official introduction date is unavailable, it is preserved as `None` and rendered as `"Introduction date unavailable"`.

---

## 6. Why State Bills Are Not Routed into Central Market Prediction

1. **Constitutional Jurisdiction Separation**: State laws apply strictly within state boundaries, whereas Central laws apply pan-India.
2. **Revenue & Exposure Differences**: A company operating nationwide may have negligible exposure to a state-specific bill unless it has major physical assets, factories, or gig fleets in that state.
3. **Event Window Availability**: State legislative sessions do not always follow regular pre-announced calendars with minute-by-minute pricing diffusion.
4. **Research Integrity**: Presenting unvalidated state price predictions would introduce severe alpha distortion. Therefore, state predictions remain strictly 0 until state-level quantitative market models are formally trained and validated.

---

## 7. Adding Future States via Adapter Architecture

To add a new state (e.g., Maharashtra or Tamil Nadu):
1. Create a state adapter in `ingestion/state/` implementing `BaseStateAdapter`.
2. Ingest official gazette/proceedings metadata into `data/state_bills/metadata/<bill_id>.json`.
3. Download official PDFs into `data/state_bills/pdfs/<bill_id>.pdf`.
4. Run `StateKnowledgeService.process_all()` to build knowledge records, economic profiles, corporate exposures, and impact assessments.
5. Update `state_coverage_registry.json` status to `IMPLEMENTED`.
6. The `UnifiedLegislativeDiscoveryService` will automatically discover and aggregate the new state bills without modifying any application code.
