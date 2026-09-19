# Task 8.12.1 — Company & Industry Intelligence Gap Audit + Expansion Design

**India Legislative Intelligence & Market Impact Prediction Platform**
**Audit Date:** 2026-09-15
**Status:** AUDIT COMPLETE — DESIGN PROPOSED — IMPLEMENTATION DEFERRED to 8.12.2+

---

## 1. Executive Summary

This audit inspects the complete company intelligence layer of the India Legislative Intelligence Platform, documents what currently exists, identifies gaps, and designs an expanded company intelligence architecture.

### Key Findings at a Glance

| Metric | Value |
|--------|-------|
| Central quantitative companies (FROZEN) | **47** |
| Companies in `companies.json` (seed master) | **50** |
| Companies in `state_company_universe.py` | **~75** (listed + unlisted) |
| Central bill-company mapping files | **22** |
| Central bill-company candidate pairs | **104** (across 22 mapping files) |
| Prediction JSON files | **4,701** |
| State bill files | **182** |
| State stock-market predictions | **0** (by design, enforced) |
| Anticipation score files | **1,900** |
| Distinct sectors (Central taxonomy) | **24** |
| Distinct sectors (State taxonomy) | **41** |
| Unlisted/public-sector entities tracked | **5** (KSEB, KSRTC-KL, KSRTC-KA, APGENCO, TSGENCO) |
| Companies without full metadata | **~30** (missing hq_city, website, ticker in `companies.json`) |

### Central Baseline Integrity

- CENTRAL_BASELINE_CHANGED = **false** — No Central predictions modified
- STATE_PREDICTIONS_CREATED = **0** — State bills carry qualitative exposure only
- TESTS_RUN = **74** | TESTS_PASSED = **74** | TESTS_FAILED = **0**

---

## 2. Current Architecture

### 2.1 System Layers

```
Parliament/State Bills (Ingestion)
        |
Bill Schema (schemas/bill.py)
        |
Knowledge Record (schemas/knowledge_record.py + knowledge/engine.py)
        |
Sector Mapper (mapping/sector_mapper.py)
        |
Company Repository (storage/company_repository.py)
        |  <- data/companies/companies.json (50 seed companies)
Bill-Company Mapping (schemas/mapping_record.py -> data/mappings/)
        |
    [Central path]                    [State path]
Feature Engineering               State Corporate Exposure Engine
Prediction Engine                 (knowledge/state_corporate_exposure_engine.py)
Decision Support                  State Company Universe
Backtesting/Event Study           (knowledge/state_company_universe.py)
        |                                 |
Anticipation Engine               StateCorporateExposure records
        |                         (schemas/state_corporate_exposure.py)
Dashboard (companies.py,                  |
 company_detail.py)               State Impact Assessment
                                  (schemas/state_impact_assessment.py)
```

### 2.2 File Inventory — Company-Related

| File | Purpose | Status |
|------|---------|--------|
| `schemas/company.py` | Core `Company` dataclass | Production |
| `schemas/state_corporate_exposure.py` | `StateCorporateExposure` + `CorporateExposureEvidence` + `StatePresenceRecord` | Production |
| `data/companies/companies.json` | 50-company seed master (used by `CompanyRepository`) | Production |
| `ingestion/companies/company_loader.py` | NSE live scraper + offline seed fallback | Production |
| `storage/company_repository.py` | CRUD + search API for companies | Production |
| `mapping/sector_mapper.py` | Bill->Company mapping via sector taxonomy | Production |
| `knowledge/state_company_universe.py` | ~75 company State universe with enriched presence records | Production |
| `knowledge/state_corporate_exposure_engine.py` | Evidence-backed exposure engine for State bills | Production |
| `knowledge/sector_domain_mapping.csv` | 24-sector bill->domain->authority mapping | Production |
| `knowledge/state_economic_taxonomy.py` | 41-sector State economic taxonomy | Production |
| `knowledge/company_sector.csv` | Company ISIN -> sector override map | Production |
| `dashboard/pages/companies.py` | Company Intelligence master page | Production |
| `dashboard/pages/company_detail.py` | Company detail dossier page | Production |
| `dashboard/pages/company_explorer.py` | Company explorer page | Production |

---

## 3. Existing Company Universe

### 3.1 Central Quantitative Prediction Universe (FROZEN — 47 Companies)

These 47 companies are used in: Central bill-company mappings, feature engineering, ML model training, predictions, decision support, backtesting, event studies, anticipation scoring, and stakeholder reports. **They must not be modified.**

The companies span the following sectors:

| Sector | Representative Companies |
|--------|--------------------------|
| Banking & Financial Services | HDFC Bank, ICICI Bank, SBI, Axis Bank, Kotak Mahindra, Bajaj Finance, Bajaj Finserv, LIC, SBI Life, HDFC Life |
| Technology | TCS, Infosys, Wipro, HCL Technologies, Tech Mahindra, LTIMindtree |
| Energy | Reliance Industries, NTPC, ONGC, Power Grid, Tata Power, Adani Green, Adani Power |
| Manufacturing (Automobiles) | Tata Motors, Maruti Suzuki, M&M, Eicher Motors, Hero Motocorp, Bajaj Auto |
| Consumer Goods & FMCG | HUL, ITC, Nestle, Britannia, Tata Consumer, Asian Paints |
| Metals & Mining | Tata Steel, JSW Steel, Hindalco, Coal India |
| Healthcare & Pharmaceuticals | Sun Pharma, Cipla, Dr. Reddy's, Apollo Hospitals |
| Infrastructure | L&T, UltraTech Cement, Grasim, Siemens, ABB |
| Telecommunications | Bharti Airtel |

Note: `companies.json` contains 50 records; 3 additional entries exist in the seed file beyond the frozen 47.

### 3.2 State Company Universe (Production — ~75 entities)

`knowledge/state_company_universe.py` contains a richer set:

**Section 1 — Central companies enriched with State presence data** (47 companies with `StatePresenceRecord` entries for AP, Karnataka, Kerala, Telangana)

**Section 2 — State-relevant listed companies** (additional to Central 47):
- GMR Airports Infrastructure Limited (GMRINFRA) — Aviation/Infrastructure
- Container Corporation of India Limited (CONCOR) — Logistics/Rail Freight
- Blue Dart Express Limited (BLUEDART) — Express Logistics

**Section 3 — Unlisted / Public-Sector Entities:**
- Andhra Pradesh Power Generation Corporation — `UNLISTED-AP-GENCO`
- Kerala State Road Transport Corporation — `UNLISTED-KL-RTC`
- Kerala State Electricity Board Limited — `UNLISTED-KL-KSEB`
- Telangana State Power Generation Corporation — `UNLISTED-TS-GENCO`
- Karnataka State Road Transport Corporation — `UNLISTED-KA-RTC`

---

## 4. Existing Company Fields

### 4.1 `Company` Schema Fields (schemas/company.py)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `isin` | str | Yes | Standard ISIN or custom UNLISTED-* ID |
| `company_name` | str | Yes | Registered name |
| `sector` | str | Yes | NSE/SEBI sector |
| `ticker_nse` | str | No | NSE ticker; empty for unlisted |
| `ticker_bse` | str | No | BSE ticker |
| `bse_code` | str | No | BSE 6-digit code |
| `industry` | str | No | Industry group |
| `sub_industry` | str | No | More granular sub-industry |
| `market_cap_category` | MarketCapCategory | No | LARGE/MID/SMALL/UNKNOWN |
| `market_cap_cr` | float\|None | No | Approximate market cap in crore |
| `hq_state` | str | No | HQ state (India state name) |
| `hq_city` | str | No | HQ city |
| `website` | str | No | Official URL |
| `listing_date` | date\|None | No | First listing date |
| `is_active` | bool | No | Active/delisted flag |
| `listing_status` | str | No | "Listed" / "Unlisted" |
| `aliases` | list[str] | No | Name variants |
| `exchange` | str | No | "NSE", "BSE", "NSE/BSE" |
| `business_description` | str | No | Business summary |
| `state_presences` | list[StatePresenceRecord] | No | Structured State operations |
| `facilities` | list[dict] | No | Facility list |
| `subsidiaries` | list[str] | No | Subsidiary names |
| `business_activities` | list[str] | No | Key business activities |

**Currently missing fields (gaps requiring 8.12.2 schema extension):**
- No `universe_type` — cannot distinguish quantitative vs intelligence-only at schema level
- No `entity_type` — no structured classification (subsidiary/PSE/unlisted)
- No `group_name` — no conglomerate group tracking (Tata Group, Adani Group)
- No `ownership_type` — no private/government/foreign classification
- No `products` / `services` — no structured product catalog
- No `data_sources` — no field for evidence provenance on the Company itself
- No `data_quality_score` — no completeness scoring
- No `watchlist_eligible` — no flag for alert readiness
- `listing_date` is null for all 50 `companies.json` entries

### 4.2 `StateCorporateExposure` Schema Fields (schemas/state_corporate_exposure.py)

| Field | Type | Notes |
|-------|------|-------|
| `bill_id` | str | Links to Bill |
| `state` | str | State of bill |
| `company_id` | str | ISIN or UNLISTED-* ID |
| `company_name` | str | Company name |
| `ticker` | str | NSE/BSE ticker (empty if unlisted) |
| `exchange` | str | Exchange identifier |
| `listed_status` | str | listed / unlisted / subsidiary_of_listed / private / public_sector_entity |
| `sector` | str | Primary sector |
| `sub_sector` | str | Sub-sector |
| `business_activity` | str | Activity creating exposure |
| `state_presence` | list[str] | Presence types in this state |
| `presence_type` | str | Dominant presence |
| `exposure_type` | str | regulatory / taxation / labour / licensing / infrastructure / etc |
| `exposure_direction` | str | positive / negative / mixed / neutral / unknown |
| `exposure_strength` | str | HIGH / MEDIUM / LOW / UNKNOWN |
| `direct_indirect` | str | DIRECT / INDIRECT / UNKNOWN |
| `geographic_scope` | str | state_specific / regional / multi_state / national_with_state_operations |
| `mechanism` | str | Statutory mechanism (compliance, taxation, labour_requirement) |
| `evidence` | list[CorporateExposureEvidence] | Evidence chain |
| `confidence` | str | HIGH / MEDIUM / LOW / UNKNOWN |
| `provenance` | dict | Source provenance |
| `source_urls` | list[str] | Reference URLs |
| `missing_information` | list[str] | Information gaps |
| `verified_at` | str | UTC timestamp (auto) |
| `schema_version` | str | Schema version (auto) |

### 4.3 `CorporateExposureEvidence` Fields

| Field | Description |
|-------|-------------|
| `source_type` | bill_text / company_filing / annual_report / regulatory_filing / government_record / official_website |
| `reference` | Section/clause or annual report page reference |
| `claim` | Factual statement substantiated by the reference |
| `url` | Direct URL to the source (optional) |

---

## 5. Existing Exposure Pipeline

### 5.1 Central Exposure Pipeline

```
Bill (schemas/bill.py)
    + KnowledgeRecord (primary_sector, secondary_sectors, keywords, ministry)
         |
    SectorMapper.map_bill_to_companies()
         | (deterministic rule engine — sector + ministry + keyword matching)
    BillCompanyMapping (candidate_companies + confidence scores)
         | (stored in data/mappings/ — 22 files, 104 candidate pairs)
    FeatureEngineering -> ML Training -> PredictionEngine
         |
    PredictionRecord (direction, strength, confidence, impact_score)
         |
    DecisionRecord + AnticipatioRecord + StakeholderReport
```

**Confidence scoring factors (Central SectorMapper):**
- Primary sector match: +0.50
- Secondary sector match: +0.30
- Industry/sub-industry keyword match: +0.10–0.20
- Ministry-to-sector regulation match: +0.20
- Company name/alias mentioned in bill text: +0.10

### 5.2 State Exposure Pipeline

```
State Bill (schemas/bill.py with state field)
    + StateBillEconomicProfile (sector, activities, stakeholders, readiness)
         |
    StateCorporateExposureEngine.analyze_bill_exposure()
         | (evidence-backed, provision-grounded)
    StateCorporateExposure records
         |
    StateImpactAssessment (qualitative — ZERO stock predictions)
         |
    Dashboard / Groq AI explanation (verified context only)
```

**Evidence chain (State exposure):**
```
State Bill Provision -> Policy Domain -> Economic Sector
    -> Business Activity -> State Presence (StatePresenceRecord)
    -> Company -> CorporateExposureEvidence -> StateCorporateExposure
```

---

## 6. Current Strengths

1. **Dual-universe design already in place** — The system already distinguishes between Central (quantitative prediction) and State (qualitative intelligence) universes. The state company universe is independent.

2. **Listed/unlisted distinction enforced** — `listed_status` field in both `Company` and `StateCorporateExposure`; unlisted companies use `UNLISTED-*` ISIN format.

3. **Evidence-backed exposure** — `CorporateExposureEvidence` with `source_type`, `reference`, `claim`, and `url`. Predictive-term guardrails enforced in `__post_init__`.

4. **Forbidden predictive terms** — Runtime validation in `StateCorporateExposure.__post_init__` prevents insertion of stock prediction language.

5. **State presence granularity** — `StatePresenceRecord` captures presence types (manufacturing/plant/office/logistics), facility locations, and evidence source.

6. **Sector taxonomy breadth** — 41-sector state taxonomy vs 24-sector Central taxonomy. Covers agriculture, fisheries, gig economy, municipal services.

7. **CompanyRepository API** — Full CRUD + search by sector, market cap, state, ticker. Offline seed fallback on NSE scrape failure.

8. **Validation layer** — `Validator.validate_company()` enforces name, sector, website URL format, and valid Indian state.

9. **Groq AI integration** — AI explanation layer calls Groq only for verified context enrichment, not fabrication.

10. **Test coverage** — 74 tests covering schema, serialization, repository CRUD, exposure classification, evidence, and state-isolation invariants (including `test_state_predictions_remain_zero`).

---

## 7. Current Gaps

### 7.1 Structural Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No `universe_type` field on Company | HIGH | Cannot distinguish quantitative vs intelligence-only at schema level |
| No `entity_type` field | HIGH | No structured subsidiary/PSE/unlisted classification |
| No `group_name` field | MEDIUM | No conglomerate group tracking |
| No `products` / `services` field | MEDIUM | Only `business_activities` (unstructured) |
| No `data_sources` on base Company | MEDIUM | Evidence provenance tracked on exposure but not on Company itself |
| No `data_quality_score` | MEDIUM | No field for metadata completeness scoring |
| No `watchlist_eligible` flag | MEDIUM | No structured indicator of alert readiness |
| `listing_date` is null for all 50 companies | LOW | All `companies.json` entries missing listing date |
| `market_cap_cr` values are static seeds | MEDIUM | Not refreshed from live data |
| `company_sector.csv` has minimal entries | MEDIUM | ISIN->sector override map is sparse |

### 7.2 Coverage Gaps

| Category | Currently Implemented | Gap |
|----------|----------------------|-----|
| Food delivery / gig-economy | None | Swiggy (unlisted), Zomato (listed: ZOMATO) |
| E-commerce platforms | None | Amazon India (unlisted subsidiary), Flipkart (unlisted subsidiary) |
| Reliance Industries | Present (Central + State) | Jio Platforms, Reliance Retail as separate entities |
| Tata Group | TCS, Tata Motors, Tata Steel, Tata Power, Tata Consumer | Missing: Tata Chemicals, Indian Hotels, Titan, Voltas |
| Adani Group | Adani Enterprises, Adani Green, Adani Power | Missing: Adani Ports, Adani Total Gas, Adani Wilmar |
| Telecom | Bharti Airtel | Missing: Vodafone Idea, BSNL, MTNL |
| Healthcare | Sun Pharma, Cipla, Dr. Reddy's, Apollo | Missing: Fortis, Max Health, Narayana Health, Aster |
| Logistics | CONCOR, Blue Dart | Missing: Delhivery, Ecom Express, XpressBees |
| Consumer / Retail | HUL, ITC, Nestle, Asian Paints | Missing: DMart, Nykaa, V-Mart |
| State utilities | APGENCO, TSGENCO, KSEB, KSRTC (KL+KA) | Missing: TANGEDCO, BESCOM, state DISCOMs for new states |
| Mid/Small cap | Blue Dart (mid-cap) | Very few mid/small cap entities |
| Industry groups | Not implemented | CII, FICCI, NASSCOM not tracked |
| Sector-level intelligence | Not implemented | No sector-level aggregation pages |

### 7.3 Functional Gaps

| Capability | Status |
|------------|--------|
| Company profile pages | Exists (Central-only in `company_detail.py`) |
| Bill-to-company discovery | Exists (`SectorMapper` + mapping pipeline) |
| Company-to-bill discovery | Partial — dashboard search only; no reverse index |
| Sector intelligence pages | Not implemented |
| Industry intelligence pages | Not implemented |
| Watchlists | Not implemented |
| Alerts | Not implemented |
| AI explanations for Central company exposure | Limited (Groq exists for State; weaker for Central) |
| Company-level monitoring | Partial (legislative monitoring exists; not company-centric) |

---

## 8. Intelligence Universe vs Prediction Universe

### 8.1 Two Distinct Universes

```
+---------------------------------------------------------------+
|  UNIVERSE A: QUANTITATIVE PREDICTION UNIVERSE                 |
|  ----------------------------------------------------------- |
|  Companies: 47 (FROZEN)                                       |
|  All listed on BSE/NSE with OHLCV history                     |
|  Eligible for: event study, ML prediction, backtesting        |
|  Central bills only (20 production bills)                     |
|  Produces: PredictionRecord, DecisionRecord, Anticipation     |
|  Status: FROZEN — DO NOT MODIFY                               |
+---------------------------------------------------------------+

         READ-ONLY (Universe A is a subset of Universe B)

+---------------------------------------------------------------+
|  UNIVERSE B: INTELLIGENCE / EXPOSURE UNIVERSE                 |
|  ----------------------------------------------------------- |
|  Companies: ~75 currently, expandable to 500+                 |
|  Listed AND unlisted                                          |
|  Public sector utilities included                             |
|  State-owned enterprises included                             |
|  Large private companies (Flipkart, Swiggy) included         |
|  Industry groups at sector level                              |
|  Central bills: qualitative exposure intelligence             |
|  State bills: qualitative exposure intelligence               |
|  Produces: StateCorporateExposure, StateImpactAssessment,    |
|            Company profiles, Sector intelligence              |
|  Status: EXPANDABLE                                           |
+---------------------------------------------------------------+
```

### 8.2 Eligibility Rules

| Criterion | Prediction Universe | Intelligence Universe |
|-----------|--------------------|-----------------------|
| Listed status | Required | Not required |
| Market data history | Required (3+ years OHLCV) | Not required |
| Active trading | Required | Not required |
| Valid INE* ISIN | Required | Custom UNLISTED-* allowed |
| Stock price prediction | Eligible | Prohibited |
| Qualitative exposure | Included | Included |
| State bill exposure | Excluded from predictions | Included |

---

## 9. Proposed Expanded Company Schema

The following fields are proposed additions to the `Company` dataclass in `schemas/company.py`. All are backward-compatible (optional with safe defaults). Implementation deferred to Task 8.12.2.

### 9.1 Proposed New Fields

```python
# Universe Classification (NEW — HIGH PRIORITY)
universe_type: str = "intelligence_only"
# "quantitative_prediction" | "intelligence_only"
# quantitative_prediction = frozen Central prediction universe
# intelligence_only = exposure/profile intelligence only

# Entity Classification (NEW — HIGH PRIORITY)
entity_type: str = "listed_company"
# "listed_company" | "unlisted_company" | "subsidiary" |
# "public_sector_enterprise" | "state_owned_utility" |
# "industry_group" | "sector_aggregate"

# Ownership & Group (NEW — MEDIUM PRIORITY)
ownership_type: str = "private"
# "private" | "government" | "public_sector" | "foreign_subsidiary" | "multinational"
parent_company: str = ""   # Parent entity name if subsidiary
group_name: str = ""       # Conglomerate group (e.g., "Tata Group", "Adani Group")

# Products & Services (NEW — MEDIUM PRIORITY)
products: list[str] = field(default_factory=list)
services: list[str] = field(default_factory=list)
customer_segments: list[str] = field(default_factory=list)  # B2B/B2C/B2G/etc

# Geographic Coverage (NEW — MEDIUM PRIORITY)
primary_states: list[str] = field(default_factory=list)
national_presence: bool = False   # Operates in 15+ states

# Registry Identifiers (NEW — MEDIUM PRIORITY)
cin: str = ""         # Corporate Identity Number (MCA21)
gstin_states: list[str] = field(default_factory=list)  # States with GSTIN presence

# Data Quality & Provenance (NEW — HIGH PRIORITY)
data_sources: list[str] = field(default_factory=list)
last_verified_date: str = ""   # ISO date of last manual verification
data_quality_score: float = 0.0  # 0.0-1.0 completeness score
evidence_notes: str = ""

# Watchlist & Alert Readiness (NEW — MEDIUM PRIORITY)
watchlist_eligible: bool = False
alert_keywords: list[str] = field(default_factory=list)

# Financial Context (NEW — LOW PRIORITY)
annual_revenue_cr: float | None = None   # From public annual report
employee_count_range: str = ""           # "0-100" | "100-1000" | "1000-10000" | "10000+"
ipo_date: date | None = None             # IPO date if recently listed

# Regulatory Footprint (NEW — MEDIUM PRIORITY)
regulated_by: list[str] = field(default_factory=list)   # Regulatory authorities
licenses: list[str] = field(default_factory=list)

# AI Explanation Support (NEW — LOW PRIORITY)
groq_context_summary: str = ""   # Pre-generated Groq context string
groq_last_updated: str = ""      # ISO timestamp of last AI enrichment

# Schema Version
schema_version: str = "2.0.0"
```

---

## 10. Proposed Evidence / Provenance Model

### 10.1 Evidence Chain (Mandatory for All Exposures)

Every company-legislation exposure MUST be explainable through:

```
Bill (statutory provision text)
    -> Sector/Industry (from taxonomy)
    -> Business Activity (what the company does that is affected)
    -> Geographic / State Presence (where the company operates)
    -> Company (entity with verified presence)
    -> Evidence (source type + reference + claim + URL)
    -> Exposure Assessment (strength, direction, type, confidence)
```

### 10.2 Evidence Classification Rules

#### Direct Exposure (`direct_indirect = "DIRECT"`)
Required evidence — at least ONE of:
- Company is explicitly named or regulated in the bill text
- Company's primary business activity is directly regulated by the bill
- Company holds a license/registration that the bill modifies
- Company's product/service is directly classified, taxed, or restricted by the bill

#### Indirect Exposure (`direct_indirect = "INDIRECT"`)
Required evidence — at least ONE of:
- Company operates in a sector that supplies/serves directly regulated industries
- Company's input costs or distribution channels are affected
- Company's customers are directly affected (demand-side)
- Company's State operations overlap with a geographically scoped bill

#### Exposure Strength Classification

| Strength | Criteria |
|----------|----------|
| HIGH | Core business activity regulated; significant revenue at stake; bill provision mandatory and immediate |
| MEDIUM | Partial operations affected; compliance cost but not core revenue threat; bill is likely relevant |
| LOW | Indirect or peripheral effect; marginal compliance cost; bill mentions sector broadly |
| UNKNOWN | Insufficient evidence; document in `missing_information`; do not assert |

#### Confidence Classification

| Confidence | Evidence Requirements |
|------------|----------------------|
| HIGH | 2+ grounded evidence items; annual report or official filing cited; State presence verified |
| MEDIUM | 1 grounded evidence item; official website or regulatory filing cited |
| LOW | Inference-only; no direct documentary evidence; flagged in `missing_information` |
| UNKNOWN | No verifiable evidence available; exposure claim must not be made |

### 10.3 Forbidden Predictive Terms (Enforced at schema level)

Prohibited in all exposure records: `price target`, `target price`, `buy rating`, `sell rating`, `hold rating`, `stock prediction`, `market return`, `abnormal return`, `cumulative abnormal return`, `average abnormal return`, `alpha forecast`, `trading strategy`, `portfolio recommendation`.

### 10.4 Evidence Source Priority

1. **Highest:** Company Annual Reports / Integrated Reports (BSE/NSE filings)
2. **High:** SEBI/Stock exchange filings (shareholding pattern, corporate actions, disclosures)
3. **High:** Official company websites (About Us, Locations, Products pages)
4. **Medium:** Regulatory authority filings (CERC, TRAI, IRDAI, RBI disclosures)
5. **Medium:** Government records (Ministry of Corporate Affairs, CIN registrations)
6. **Low:** Press releases / investor presentations (cross-validation required)
7. **Not accepted as primary evidence:** Wikipedia, news articles, analyst reports

---

## 11. Proposed Industry / Sector Hierarchy

### 11.1 Three-Level Hierarchy

```
Level 1: MACRO SECTOR         (8 groups — proposed)
    -> Level 2: SECTOR        (24 Central + 41 State — existing)
        -> Level 3: INDUSTRY  (company-level — existing in Company schema)
```

### 11.2 Proposed Macro Sectors

| Macro Sector | Includes |
|-------------|---------|
| Financial Services | Banking, Insurance, NBFCs, Capital Markets, Fintech |
| Technology & Digital | IT Services, Telecom, Data, AI, E-commerce, Gig Economy |
| Energy & Utilities | Oil & Gas, Power Generation, Renewables, Coal, LNG |
| Industry & Manufacturing | Automobiles, Steel, Cement, Chemicals, Textiles, Capital Goods |
| Consumer & Retail | FMCG, Food & Beverage, Retail, Consumer Durables, Paints |
| Healthcare & Life Sciences | Pharmaceuticals, Hospitals, Diagnostics, Medical Devices |
| Infrastructure & Logistics | Roads, Ports, Aviation, Rail, Real Estate, Express Freight |
| Agriculture & Rural | Agri-business, Food Processing, Rural Credit, MSME |

### 11.3 Coverage for Specific Company Categories

| Company/Category | Architecture Support | Proposed Classification |
|-----------------|---------------------|------------------------|
| Swiggy | Intelligence universe (unlisted) | Technology & Digital / Gig Economy / Food Delivery |
| Zomato (listed: ZOMATO) | Intelligence universe -> Prediction eligible (requires evidence + market data) | Technology & Digital / Food Delivery |
| Reliance Industries | Present in both universes | Energy + Technology & Digital + Consumer |
| Amazon India | Intelligence universe only (unlisted subsidiary) | Technology & Digital / E-commerce |
| Flipkart | Intelligence universe only (Walmart subsidiary, unlisted) | Technology & Digital / E-commerce |
| Tata Group additional | Intelligence universe | Multi-sector |
| Adani Ports, Adani Total Gas | Intelligence universe | Infrastructure + Energy |
| Vodafone Idea, BSNL | Intelligence universe | Technology & Digital / Telecom |
| Fortis, Narayana Health | Intelligence universe | Healthcare & Life Sciences |
| Delhivery, Ecom Express | Intelligence universe | Infrastructure & Logistics |
| DMart, Nykaa | Intelligence universe | Consumer & Retail |
| State DISCOMs/SEBs | Intelligence universe (unlisted) | Energy & Utilities / Regulated |

---

## 12. Proposed Company Expansion Strategy

### 12.1 Expansion Principles

1. Expand intelligence universe first — new companies enter intelligence/exposure universe only
2. No automatic prediction creation — adding a company does not generate stock market predictions
3. Evidence first — no company added without at least one verifiable evidence source
4. State/sector scoping — additions driven by active State legislative bills and sectors
5. Quantitative eligibility gate — promotion to prediction universe requires strict eligibility check

### 12.2 Priority A — High Legislative Exposure, Evidence Available (Listed)

| Company | Ticker | Rationale |
|---------|--------|-----------|
| Zomato Limited | ZOMATO | Gig economy/labour bills, food safety, GST |
| Adani Ports & SEZ | ADANIPORTS | Port/infrastructure bills, land acquisition |
| Adani Total Gas | ATGL | Gas distribution bills, CNG/PNG regulations |
| Adani Wilmar | AWL | Food safety, FSSAI regulations |
| Delhivery Limited | DELHIVERY | Logistics bill, gig worker regulations |
| Titan Company | TITAN | GST on jewellery, hallmarking bills |
| Tata Chemicals | TATACHEM | Environmental bills, chemical regulation |

### 12.3 Priority B — Strategic Importance, Unlisted

| Company | Status | Rationale |
|---------|--------|-----------|
| Swiggy | Unlisted (recent IPO) | Gig economy labour bills, ONDC policy |
| Flipkart | Unlisted (Walmart subsidiary) | E-commerce FDI regulations, consumer protection |
| Amazon Seller Services Pvt Ltd | Unlisted subsidiary | E-commerce FDI regulations |
| Ola Cabs | Unlisted | Gig economy, motor vehicle regulations |
| BSNL | Unlisted (Government) | Telecom spectrum, 4G/5G allocation bills |
| BESCOM, TANGEDCO | Unlisted (State utilities) | State electricity bills in new coverage states |

### 12.4 Expansion Workflow

```
1. IDENTIFY trigger (active bill in new sector/state)
2. IDENTIFY candidate companies (sector + state presence)
3. COLLECT evidence (annual report / official website / filing)
4. VERIFY evidence (human review or Groq-assisted extraction)
5. ADD to intelligence universe (Company + StatePresenceRecord with evidence)
6. CREATE exposure record (StateCorporateExposure with CorporateExposureEvidence)
7. DO NOT create stock market prediction
8. ASSESS quantitative eligibility separately (market data sufficiency gate)
```

---

## 13. Integration Architecture

### 13.1 Full Integration Architecture (Current + Proposed)

```
Legislative Monitoring (Groq-powered, scheduled)
    [Central: Parliament website, PRS India]
    [State: AP Legislature, Karnataka Vidhana Soudha, Kerala Assembly, Telangana Assembly]
        |
Unified Legislative Discovery
    (knowledge/unified_bill_discovery_engine.py)
        |
Bill Knowledge Record
    (sector, ministry, policy_domain, keywords, geographic_scope)
        |
    +--------------------------------------+
    |  SECTOR / INDUSTRY INTELLIGENCE      |
    |  (knowledge/sector_domain_mapping.csv|
    |   knowledge/state_economic_taxonomy) |
    +--------------------------------------+
        |
    +------------------------------------------------------------------+
    |  COMPANY INTELLIGENCE LAYER (PROPOSED EXPANDED)                  |
    |                                                                  |
    |  Universe A (Quantitative): 47 frozen companies                  |
    |    -> Central bill-company mapping (sector_mapper.py)            |
    |    -> ML Predictions -> Backtesting -> Event Study               |
    |                                                                  |
    |  Universe B (Intelligence): ~75 -> 200+ companies                |
    |    -> State corporate exposure engine                            |
    |    -> Central qualitative exposure (proposed new capability)     |
    |    -> Evidence-backed exposure records                           |
    |    -> Company profile pages                                      |
    |    -> Sector/industry aggregation (proposed)                     |
    +------------------------------------------------------------------+
        |
    +--------------------------------------+
    |  EXPOSURE ASSESSMENT                 |
    |  DIRECT / INDIRECT                   |
    |  HIGH / MEDIUM / LOW / UNKNOWN       |
    |  Evidence chain validation           |
    +--------------------------------------+
        |
    +--------------------------------------+
    |  AI EXPLANATION (Groq)              |
    |  - Explain verified exposures only  |
    |  - Do not invent company claims     |
    |  - Reference bill provisions        |
    |  - Reference company filings        |
    +--------------------------------------+
        |
    +--------------------------------------+
    |  FUTURE WATCHLISTS & ALERTS         |
    |  - Company watchlist subscriptions  |
    |  - Sector alert thresholds          |
    |  - Bill keyword triggers            |
    |  - New bill notification            |
    +--------------------------------------+
```

### 13.2 New Integration Points Needed (8.12.2+)

| Integration Point | Currently | Proposed |
|-------------------|-----------|---------|
| Company->Bill reverse index | None | `CompanyRepository.get_bills_for_company(isin)` |
| Sector page aggregation | None | `SectorIntelligenceService.get_sector_profile(sector)` |
| Watchlist subscription | None | `WatchlistRepository` + alert trigger |
| Universe type gating | None | `Company.universe_type` + eligibility validator |
| Central qualitative exposure | Only quantitative | Evidence-backed qualitative layer |
| AI company profile generation | Limited | Groq-generated summaries from verified facts |

---

## 14. Future Watchlist / Alert Readiness

### 14.1 Proposed WatchlistItem Schema

```python
@dataclass
class WatchlistItem:
    watchlist_id: str
    session_id: str
    entity_type: str     # "company" | "sector" | "bill_keyword"
    entity_id: str       # ISIN / sector_name / keyword
    alert_triggers: list[str]   # ["new_bill", "exposure_change", "sector_impact"]
    is_active: bool = True
    created_at: str = ""  # ISO timestamp
```

### 14.2 Alert Trigger Types

| Trigger | Requirement |
|---------|-------------|
| New bill in tracked sector | Bill knowledge record with matching sector |
| Company exposure classification change | StateCorporateExposure update for tracked company |
| HIGH strength exposure detected | exposure_strength = "HIGH" on new exposure record |
| New state bill affecting tracked company | State bill covering company's State presence |
| Central bill association for tracked company | New mapping record including tracked ISIN |

### 14.3 Watchlist Readiness per Company Category

| Category | Watchlist Ready | Limitation |
|----------|----------------|------------|
| Central 47 companies | Yes | Full alerts including market impact |
| State unlisted entities (KSEB, etc.) | Intelligence-only | No market price alerts possible |
| Zomato (proposed) | Yes once added | Needs schema entry and evidence |
| Swiggy (unlisted) | Intelligence-only | Unlisted = no market alerts |
| Flipkart/Amazon India | Intelligence-only | Unlisted subsidiaries |

---

## 15. Data Quality Rules

### 15.1 Mandatory Fields (No Exceptions)

All `Company` records entering the intelligence universe MUST have:
- `isin` (valid INE* or verified UNLISTED-* format)
- `company_name` (registered name)
- `sector` (from canonical taxonomy)
- `listing_status` ("Listed" or "Unlisted")
- `entity_type` (new field — proposed)
- `universe_type` (new field — proposed)
- At least ONE `data_sources` entry (new field — proposed)

### 15.2 Data Quality Score Formula (Proposed)

```python
def compute_data_quality_score(company: Company) -> float:
    score = 0.0
    if company.company_name: score += 0.15
    if company.sector: score += 0.10
    if company.industry: score += 0.05
    if company.hq_state: score += 0.10
    if company.website: score += 0.10
    if company.business_description: score += 0.10
    if company.business_activities: score += 0.10
    if company.state_presences: score += 0.15
    if company.data_sources: score += 0.10    # proposed field
    if company.listing_date or company.listing_status: score += 0.05
    return round(min(score, 1.0), 2)
```

### 15.3 Anti-Fabrication Rules

1. No fabricated ISINs — ISIN must be verified at NSE/BSE or marked UNLISTED-*
2. No fabricated tickers — Tickers must match official exchange listings
3. No fabricated facilities — State presences require annual report or official website citation
4. No fabricated subsidiaries — Subsidiary names must come from official company disclosures
5. No speculative revenue figures — `annual_revenue_cr` only from published company filings
6. Groq must explain, not invent — Groq may summarize grounded facts; may not create new facts

---

## 16. Non-Goals / Safety Boundaries

The following boundaries are ENFORCED AT DESIGN LEVEL and must be respected in all future implementation tasks.

### 16.1 Hard Boundaries

| Boundary | Rule |
|----------|------|
| Central prediction universe | FROZEN at 47 companies — adding a company to intelligence universe does NOT add it to prediction universe |
| Central predictions | DO NOT regenerate — 4,700 existing predictions are immutable |
| State stock-market predictions | ZERO state predictions — qualitative exposure only, enforced by `_FORBIDDEN_PREDICTIVE_TERMS` and `test_state_predictions_remain_zero` |
| Market data requirement | Quantitative prediction eligibility requires 3+ years OHLCV history + liquidity threshold |
| Evidence requirement | Any exposure claim requires at least ONE `CorporateExposureEvidence` item |
| Groq fabrication | Groq may not invent company exposures, facility locations, or financial metrics |
| Unlisted company predictions | Unlisted companies may never have stock-market predictions |
| Model retraining | Strictly prohibited without explicit user approval in a separate task |

### 16.2 Soft Boundaries (Guidelines)

- Prefer official exchange/regulatory filings over press releases
- Prefer company annual reports (BSE/NSE submission) over company websites for financial data
- Document all `missing_information` rather than guessing
- Mark confidence as LOW or UNKNOWN rather than fabricating HIGH confidence

---

## 17. Recommended Implementation Tasks for 8.12.2 onward

### Task 8.12.2 — Extend Company Schema (HIGH Priority)
**Goal:** Add `universe_type`, `entity_type`, `group_name`, `ownership_type`, `data_sources`, `data_quality_score`, `watchlist_eligible` to `Company` dataclass.
**Scope:** Schema update + backward-compatible migration of `companies.json` + state universe + tests.
**Constraint:** DO NOT retrain models. DO NOT modify Central predictions.

### Task 8.12.3 — Intelligence Universe Expansion: Priority A Listed Companies (HIGH Priority)
**Goal:** Add Priority A listed companies (Zomato, Adani Ports, Adani Total Gas, Delhivery, Titan, Tata Chemicals) to intelligence universe with evidence from annual reports.
**Scope:** Add to `state_company_universe.py` with `StatePresenceRecord` entries. Compute `data_quality_score`.
**Constraint:** Intelligence universe only. No prediction pipeline changes.

### Task 8.12.4 — Intelligence Universe Expansion: Priority B Unlisted (MEDIUM Priority)
**Goal:** Add major unlisted companies (Swiggy, Flipkart concept entity, BSNL, state utilities) with verified evidence.
**Scope:** UNLISTED-* format ISINs. Official government/company websites as evidence.
**Constraint:** Intelligence universe only. No ticker or market price references.

### Task 8.12.5 — Sector / Industry Intelligence Pages (MEDIUM Priority)
**Goal:** Build sector-level intelligence aggregation (bills per sector, companies per sector, exposure heatmap).
**Scope:** New dashboard page + `SectorIntelligenceService`. Read-only aggregation.

### Task 8.12.6 — Company-to-Bill Reverse Discovery (MEDIUM Priority)
**Goal:** Enable company-centric bill discovery (given ISIN -> which bills affect this company).
**Scope:** Reverse index in `CompanyRepository` + new dashboard explorer.

### Task 8.12.7 — Watchlist & Alert Infrastructure (LOW Priority — Future Product)
**Goal:** Design and implement `WatchlistRepository`, alert trigger engine, and notification hooks.
**Scope:** New schemas, repository, and dashboard components.
**Constraint:** No market price predictions for unlisted companies.

### Task 8.12.8 — Groq AI Company Profile Generation (LOW Priority)
**Goal:** Pre-generate AI company intelligence summaries using Groq, stored in `groq_context_summary`.
**Scope:** Batch Groq enrichment for intelligence universe companies, human verification required.

---

## 18. Machine-Readable Summary

```yaml
AUDIT_TASK: "8.12.1"
AUDIT_DATE: "2026-09-15"

CURRENT_COMPANIES:
  companies_json_total: 50
  central_quantitative_universe: 47
  state_company_universe_total: 75
  intelligence_universe_approx: 75

CENTRAL_QUANTITATIVE_COMPANIES: 47
STATE_INTELLIGENCE_COMPANIES: 75

LISTED_COMPANIES:
  central_quantitative: 47
  state_additional_listed: 3
  total_listed_tracked: 50

UNLISTED_COMPANIES:
  state_public_sector: 5
  total_unlisted_tracked: 5

CURRENT_EXPOSURES:
  central_bill_mapping_files: 22
  central_bill_company_candidate_pairs: 104
  central_predictions_files: 4701
  central_anticipation_files: 1900
  state_bill_files: 182
  state_corporate_exposures: "generated_on_demand"

MAJOR_GAPS:
  - "No universe_type field on Company schema"
  - "No entity_type field for PSE/subsidiary classification"
  - "No data_quality_score field"
  - "No watchlist infrastructure"
  - "No sector intelligence pages"
  - "Missing: Zomato, Adani Ports, Adani Total Gas, Delhivery, Titan, Tata Chemicals"
  - "Missing: Swiggy, Flipkart, Amazon India (unlisted)"
  - "Missing: Vodafone Idea, BSNL"
  - "Missing: Fortis, Narayana Health, Max Health"
  - "Missing: state DISCOMs beyond current 4-state coverage"
  - "No company-to-bill reverse discovery index"
  - "listing_date null for all 50 companies in companies.json"
  - "market_cap_cr values are static seeds, not refreshed"

PROPOSED_NEW_CAPABILITIES:
  - "Expanded Company schema v2.0.0"
  - "Priority A: 7 new listed companies in intelligence universe"
  - "Priority B: 6 new unlisted companies in intelligence universe"
  - "Sector intelligence pages"
  - "Company-to-bill reverse discovery"
  - "Watchlist and alert infrastructure"
  - "Groq AI company profile generation"
  - "Data quality scoring"

CENTRAL_BASELINE_CHANGED: false
STATE_PREDICTIONS_CREATED: 0
TESTS_RUN: 74
TESTS_PASSED: 74
TESTS_FAILED: 0

RECOMMENDED_NEXT_TASK: "8.12.2 — Extend Company Schema"
```

---

## Appendix: Files Inspected

| File | Purpose |
|------|---------|
| `schemas/company.py` | Core Company schema |
| `schemas/state_corporate_exposure.py` | State exposure, evidence, state presence schemas |
| `data/companies/companies.json` | 50-company production seed master |
| `ingestion/companies/company_loader.py` | NSE live loader + seed enrichment (50 SEED_COMPANIES) |
| `storage/company_repository.py` | Company CRUD repository |
| `mapping/sector_mapper.py` | Bill->Company mapping engine (deterministic) |
| `knowledge/state_company_universe.py` | ~75 state company universe with presence records |
| `knowledge/state_corporate_exposure_engine.py` | State exposure analysis engine |
| `knowledge/sector_domain_mapping.csv` | 24-sector Central bill->domain->authority mapping |
| `knowledge/state_economic_taxonomy.py` | 41-sector state economic taxonomy |
| `knowledge/company_sector.csv` | Company ISIN->sector overrides |
| `dashboard/pages/companies.py` | Company Intelligence master page |
| `dashboard/pages/company_detail.py` | Company detail dossier page |
| `dashboard/pages/company_explorer.py` | Company explorer page |
| `tests/test_company_intelligence.py` | Company schema + repository tests (11 tests) |
| `tests/test_state_corporate_exposure.py` | State exposure tests including zero-prediction invariants (30 tests) |
| `tests/test_placeholder.py` | Baseline utility tests (33 tests) |
| `docs/task_8_7_state_corporate_exposure.md` | Prior state corporate exposure task documentation |

*Report generated by Task 8.12.1 audit. Do NOT proceed to 8.12.2 implementation without explicit user approval.*
