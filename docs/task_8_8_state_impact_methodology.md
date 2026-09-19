# Task 8.8: State Economic & Market Impact Methodology Layer

> **Critical Notice**: Task 8.8 establishes State economic and market-impact readiness. It does **not** predict State stock-market outcomes. State market predictions remain strictly **0**.

---

## Executive Summary

Task 8.8 introduces an **additive, structured, and deterministic methodology layer** for evaluating the economic and potential market relevance of Indian State legislation within the **India Legislative Intelligence & Market Impact Prediction Platform**.

Operating across all 44 analyzed State bills spanning 4 pilot States (**Andhra Pradesh**, **Karnataka**, **Kerala**, and **Telangana**), this layer addresses 10 core evaluative questions:
1. **What type of economic impact can this bill have?**
2. **Which economic mechanisms are involved?**
3. **Which stakeholders/businesses bear or receive the effect?**
4. **Which companies are exposed?**
5. **How strong is the exposure?**
6. **Is there enough evidence to assess economic impact?**
7. **Is there enough data to assess market impact?**
8. **Is the bill eligible for future State stock modeling?**
9. **Should the bill remain economic-only?**
10. **What additional data would be required before modeling?**

---

## Core Epistemic Distinction: Economic Impact vs. Stock Market Impact

A primary architectural principle enforced in Task 8.8 is:
$$\text{Economic Impact} \neq \text{Stock Market Impact}$$

A State bill frequently introduces substantial real-economy consequences without any transmission to listed securities. The platform evaluates State legislation through the following sequential pipeline:

```
LEGISLATION (State Gazette / Corpus)
    ↓
POLICY / PROVISION (Knowledge Layer, Task 8.4)
    ↓
ECONOMIC MECHANISM (Taxonomy & Profiles, Task 8.6 & 8.8 Phase 1)
    ↓
SECTOR / STAKEHOLDER EFFECT (Stakeholder Engine, Task 8.6)
    ↓
CORPORATE EXPOSURE (Corporate Exposure Layer, Task 8.7)
    ↓
MARKET RELEVANCE (Methodology, Task 8.8 Phase 4)
    ↓
DATA SUFFICIENCY (14-Point Data Audit, Task 8.8 Phase 6)
    ↓
FUTURE MODEL ELIGIBILITY (10-Point Scorecard, Task 8.8 Phase 5 & 11)
```

### Tripartite Bill Classification
1. **Economic-Only / Non-Market Bills (23 bills)**: Substantive economic, social, or administrative impact (e.g. panchayat governance, bovine breeding, veterinary councils, university statutes, repeal of obsolete laws) with **zero listed-company exposure**. Market relevance is strictly `NONE` and modeling eligibility is strictly `NOT_ELIGIBLE`.
2. **Conditionally Eligible Bills (21 bills)**: Verified listed corporate exposure exists (e.g. gig worker aggregator cess, industrial investment incentives, electricity duty, commercial vehicle taxation), but additional data (historical parquets or live anticipation signals) is required prior to econometric or event-study modeling.
3. **Eligible Bills (0 bills in Task 8.8)**: Full event study readiness requires live crawlers and complete historical pricing across all candidate tickers. No bill is artificially forced into `ELIGIBLE` status.

---

## 1. Economic Mechanism Taxonomy (Phase 1)

Task 8.8 defines a closed 26-mechanism taxonomy covering direct statutory and real-economy transmission channels:

| Mechanism | Description | Primary State Bill Example |
| :--- | :--- | :--- |
| `taxation` | State levies, cess, stamp duty, motor vehicle tax, electricity duty | Karnataka Bill 29 of 2024 (Stamp Duty) |
| `subsidy` | Fiscal incentives, rebates, state subventions | AP Bill 11 of 2025 (Industrial Promotion) |
| `compliance_cost` | Mandatory registrations, returns, statutory reporting | AP Bill 14 of 2026 (Factories Shifts) |
| `labour_cost` | Minimum wage standards, welfare funds, working hours | Telangana Bill 11 of 2024 (Gig Workers) |
| `licensing` | Regulatory permits, accreditation, aquaculture authorization | AP Bill 20 of 2025 (Aquaculture Authority) |
| `regulation` | Statutory standard-setting, administrative inspection | Kerala Bill 168 of 2023 (Apartment Ownership) |
| `electricity_cost` | Electricity duty on captive generation and industrial supply | AP Bill 3 of 2026 (Electricity Duty) |
| `transportation_cost` | Road tax, vehicle fitness fees, transit permits | Telangana Bill 8 of 2024 (Motor Vehicles) |
| `investment` | Single-desk facilitation, industrial zone development | AP Bill 14 of 2025 (Economic Development) |
| `land` | Tenancy, master planning, zoning, real estate allotment | Karnataka Bill 34 of 2024 (Greater Bengaluru) |
| `environmental_cost` | Pollution control standards, hazardous material handling | AP Bill 11 of 2025 (Industrial Zones) |
| `public_spending` | State budget outlays, welfare board corpus creation | Kerala Bill 223 of 2024 (Cine Workers) |
| `employment` | Job creation mandates, local employment guidelines | Telangana Bill 11 of 2024 (Gig Workers) |
| `pricing` | Tariff setting, statutory ceiling, price disclosure | AP Bill 32 of 2025 (APGST Amendments) |
| `procurement` | State public procurement procedures | General statutory provisions |
| `market_access` | Statutory authorization to operate in State markets | Telangana Bill 11 of 2024 (Platform Aggregators) |

---

## 2. Economic Impact Direction & Strength (Phases 2 & 3)

### Economic Impact Direction
Direction represents qualitative real-economy welfare or burden:
- **`positive` (22 bills)**: Net economic benefits, statutory incentives, productivity enhancements, or consumer welfare improvements.
- **`mixed` (9 bills)**: Dispersed effects where taxpayers or commercial enterprises bear statutory costs/cess while government revenue or beneficiaries receive protections.
- **`neutral` (13 bills)**: Administrative nomenclature updates, repeal of obsolete enactments, or procedural clarifications.
- **`negative` (0 bills)**: No State legislation in the sample produced purely destructive net economic effects without public welfare objectives.

### Economic Impact Strength
Deterministic statutory scoring:
- **`HIGH` (35 bills)**: Explicit statutory mechanism with state-wide applicability (e.g. mandatory welfare fee, statutory electricity duty, fiscal subsidies, or industrial shifts).
- **`MEDIUM` (8 bills)**: Procedural statutory amendments or routine tax procedural harmonizations.
- **`LOW` (1 bill)**: Purely repealing obsolete statutes with negligible real-economy operational friction.

---

## 3. Market Relevance Framework (Phase 4)

Market relevance measures the proximity and strength of listed corporate exposure:

| Relevance | Empirical Count | Criteria | Examples |
| :--- | :---: | :--- | :--- |
| **`HIGH`** | **12 bills** | Direct listed-company exposure + explicit statutory applicability + clear financial channel | Telangana Gig Workers Bill (ZOMATO, SWIGGY); AP Electricity Duty Bill (ULTRACEMCO, TATAPOWER); AP Industrial Promotion Bill (RELIANCE, DRREDDY) |
| **`MEDIUM`** | **7 bills** | Direct listed-company exposure, but statewide revenue sensitivity or financial transmission elasticity is moderate | Karnataka Stamp Duty Bill (ICICIBANK, SBIN); Telangana GST Amendment (ITC, HINDUNILVR) |
| **`LOW`** | **2 bills** | Exclusively indirect listed-company exposure (e.g. vehicle manufacturers under motor vehicle registration tax) | Telangana Motor Vehicles Bill (M&M, TATAMOTORS); AP Motor Vehicles Bill |
| **`NONE`** | **23 bills** | Zero listed corporate exposure; entirely public administration, social, or local governance | Karnataka Disqualification Bill; Kerala Bovine Breeding Bill |

---

## 4. Transparent 10-Point Eligibility Scorecard (Phase 5 & 11)

Every State bill is evaluated against 10 explicit prerequisites before any future market modeling:

```
STATE BILL: telangana-vs-bill-11-2024
↓
Bill identity verified: YES
State jurisdiction verified: YES
Event date verified: YES (2024-07-26)
Economic mechanism identified: YES (labour_cost, compliance_cost)
Corporate exposure verified: YES (Zomato, Swiggy)
Listed company verified: YES (ZOMATO, SWIGGY on NSE)
Historical market data: NO (Parquet store pending download)
Benchmark data: YES (^NSEI)
Event date identifiable: YES (Introduction date: 2024-07-26)
Anticipation readiness: PARTIAL (Methodology ready, live crawlers unattached)
↓
Result: CONDITIONALLY_ELIGIBLE
```

### Eligibility Classification Outcomes across 44 Bills:
- **`NOT_ELIGIBLE`**: **23 bills** (all bills with zero corporate exposure).
- **`CONDITIONALLY_ELIGIBLE`**: **21 bills** (all bills with listed corporate exposure; awaiting historical parquets and live anticipation signal integration).
- **`ELIGIBLE`**: **0 bills** (strictly preserved to prevent premature modeling without full data completeness).
- **`INSUFFICIENT_DATA`**: **0 bills** (all candidate bills have verified identities and dates).

---

## 5. Event Date Quality & Roles (Phase 7)

State legislative tracking distinguishes between procedural roles:
- **`PRIMARY_EVENT_DATE`**: Earliest verified public statutory date (`introduction` date where available; otherwise `assent` date).
- **`ALTERNATIVE_EVENT_DATES`**: Secondary milestones (`assent` date, `gazette` date, or `commencement` date).

### Quality Distribution:
- **`HIGH` (5 bills)**: Both introduction date and Governor assent date verified.
- **`MEDIUM` (36 bills)**: Single verified statutory date (either introduction or assent).
- **`NONE` (3 bills)**: Andhra Pradesh Bills 21, 23, and 29 of 2026 awaiting gazette date publication.

---

## 6. Data Sufficiency Assessment (Phase 6)

Audited across 14 dimensions:
1. `bill_date`
2. `bill_text`
3. `event_timing`
4. `state`
5. `sector`
6. `stakeholder`
7. `company_exposure`
8. `company_listing`
9. `ticker`
10. `historical_prices`
11. `benchmark_prices`
12. `trading_calendar_coverage`
13. `corporate_evidence`
14. `anticipation_information`

**Sufficiency Results**:
- **`PARTIAL`**: **13 bills** (bills with exposure whose tickers already exist in Central parquet store, such as UltraTech, Reliance, Tata Power, Tata Motors).
- **`INSUFFICIENT`**: **31 bills** (23 non-corporate bills + 8 bills with candidate tickers not yet downloaded to local store).

---

## 7. State-Wise Analysis Summary (Phase 15)

| Metric | Andhra Pradesh | Karnataka | Kerala | Telangana | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Bills Assessed** | **12** | **11** | **11** | **10** | **44** |
| **Bills with Corporate Exposure** | 7 | 5 | 2 | 7 | **21** |
| **Bills without Exposure (Economic-Only)**| 5 | 6 | 9 | 3 | **23** |
| **HIGH Market Relevance** | 4 | 3 | 1 | 4 | **12** |
| **MEDIUM Market Relevance** | 2 | 2 | 1 | 2 | **7** |
| **LOW Market Relevance** | 1 | 0 | 0 | 1 | **2** |
| **NONE Market Relevance** | 5 | 6 | 9 | 3 | **23** |
| **CONDITIONALLY_ELIGIBLE** | 7 | 5 | 2 | 7 | **21** |
| **NOT_ELIGIBLE** | 5 | 6 | 9 | 3 | **23** |
| **Total Corporate Exposures** | 47 | 16 | 3 | 20 | **86** |

---

## 8. Anti-Leakage Controls & Freeze Verification

1. **Strict Isolation from Central**:
   - Central metadata bills: **22** (Unchanged)
   - Central predictions: **4,700** (Unchanged)
   - Central decision records: **4,700** (Unchanged)
   - Central anticipation records: **940** (Unchanged)
2. **State Predictions**:
   - Total State market predictions: **EXACTLY ZERO**.
3. **No Hindsight Bias**:
   - Eligibility decisions are strictly based on pre-event statutory provisions, company operating footprints, and historical data existence. No future stock returns or post-event prices were consulted.

---

## Conclusion

Task 8.8 establishes the analytical bridge between qualitative State legislative knowledge and quantitative market readiness. It provides complete auditability and guarantees that future market-impact modeling will operate solely on vetted, verified, and data-sufficient State legislation.
