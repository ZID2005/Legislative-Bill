# TASK 8.1 — EXISTING SYSTEM & FEATURE GAP AUDIT REPORT

**Project:** Legislative Intelligence & Market Impact Prediction System for Indian Legislative Bills  
**Audit Document:** `docs/task_8_1_feature_gap_audit.md`  
**Audit Type:** Read-Only Existing System & Feature Gap Audit  
**Audit Phase:** Task 8.1 — Baseline Verification & Next Phase Planning  
**Audit Date:** 2026-09-06  
**Status:** COMPLETE (FROZEN BASELINE VERIFIED)  

---

## 1. Executive Summary

This report delivers an exhaustive architectural, empirical, and functional gap audit of the current Legislative Intelligence & Market Impact Prediction System. The primary objective is to inspect the current codebase, determine what is already implemented, partially implemented, or missing, evaluate readiness for State-level legislative bill expansion, identify feature duplication, assess Groq AI and SaaS potential, and formulate an actionable, prioritized implementation roadmap without modifying any production code, data, or models.

### Key Audit Findings:
1. **Frozen Production Baseline (Central Bills):** The existing quantitative research system for Indian Central Government bills is fully validated, mathematically deterministic, and complete. All canonical targets—20 Central Government bills, 47 NSE/BSE listed companies, 940 bill-company pairs, 5 event windows, 4,700 prediction records, 4,700 decision support records, 940 anticipation records, and 14,100 stakeholder reports—are verified on disk.
2. **Feature Coverage Tally (114 Features):**
   - **IMPLEMENTED:** 55 features (48.2%)
   - **PARTIALLY_IMPLEMENTED:** 17 features (14.9%)
   - **NOT_IMPLEMENTED:** 42 features (36.8%)
   - **UNKNOWN:** 0 features (0.0%)
3. **State Bill Readiness:** The core data models (`schemas/bill.py`, `schemas/company.py`, `schemas/knowledge_record.py`) already represent 8 out of 12 required legislative attributes (including `Bill.introduction_date`, `Bill.status`, `Bill.sectors`, `Company.hq_state`, `KnowledgeRecord.geographic_scope`, `KnowledgeRecord.bill_type`). Minor backward-compatible schema extensions (`jurisdiction`, `state`, and state house values in `BillHouse`) are required before State bills can be ingested.
4. **Duplication & Reusability:** 6 major feature areas often conceptualized as "new" (New Bills feed, Search, Stakeholder Reports, Risk Scoring, Company Exposure, Plain-Language Explanations) are already fully implemented or architecturally scaffolded in existing services (`dashboard/services/dashboard_service.py`, `reporting/`, `decision_support/risk_scorer.py`, `services/explanation.py`). None of these should be re-architected.
5. **Groq / AI Gap:** An abstract interface `LLMProvider(ABC)` is already present in `services/explanation.py` with methods for bill summarization, impact explanation, and multi-bill Q&A. However, no concrete `GroqProvider` exists, and no live LLM SDK is instantiated. Integrating Groq requires implementing this single subclass and wiring it to a Streamlit assistant UI.
6. **Integrity Verification:** 0 production files were modified, 0 models were altered, and 0 data records were updated. The test suite baseline remains at 1,226 passing tests.

---

## 2. Current System Snapshot

The system represents an institutional-grade quantitative legislative intelligence platform integrating natural language processing, financial event studies, machine learning ensembles, multi-stakeholder reporting, and interactive dashboard exploration.

```
+---------------------------------------------------------------------------------------------------+
|                                      SYSTEM ARCHITECTURE SNAPSHOT                                  |
+---------------------------------------------------------------------------------------------------+
|  [Ingestion & Storage]                                                                             |
|    PRS & Parliament Scrapers -> PDF Text Extraction -> Document Catalog -> BillRepository          |
|    BSE / NSE Equity Loaders -> Nifty 50 Benchmark -> Market Repository -> CompanyRepository        |
+---------------------------------------------------------------------------------------------------+
|  [Knowledge & Mapping Layer]                                                                       |
|    KnowledgeEngine -> Policy / Economic Taxonomy -> BillCompanyMapping -> Candidate Companies     |
+---------------------------------------------------------------------------------------------------+
|  [Feature Pipeline & NLP]                                                                         |
|    FinBERT (768d) + Legal-RoBERTa (768d) -> Event Study (AR/CAR) -> 5 Event Windows               |
|    Feature Fusion (1,570 raw features) -> SHAP / Mutual Info Selection (30 features)              |
+---------------------------------------------------------------------------------------------------+
|  [Predictive Modeling & Backtesting]                                                              |
|    LightGBM + XGBoost + Random Forest Ensembles -> Calibrated Probabilities (Direction, Impact)   |
|    Walk-Forward Expanding Window Backtesting -> Nifty 50 Benchmark -> Sharpe / Alpha Metrics      |
|    Pre-Event Anticipation Engine ([-30,-1] CAR Drift, Diffusion Scoring, Anticipation Paradox)    |
+---------------------------------------------------------------------------------------------------+
|  [Decision Support & Stakeholder Reporting]                                                       |
|    Composite 5-Tier Risk Scorer -> Deterministic Decision Support (4,700 records)                 |
|    Stakeholder Reporting Engine -> 14,100 Reports (Investor, Corporate, Public) in JSON/MD/CSV     |
+---------------------------------------------------------------------------------------------------+
|  [Presentation Layer (Streamlit)]                                                                 |
|    App Orchestrator (10 Primary Pages + 10 Legacy Explorers)                                      |
|    DashboardService (In-memory cached query layer, Global Search, Scope Diagnostics)              |
+---------------------------------------------------------------------------------------------------+
```

### Canonical Production Scope Metrics (Frozen Baseline)
| Dimension | Verified Production Count | Storage Location |
| :--- | :--- | :--- |
| Central Government Bills | 20 | `data/bills/metadata/*.json` |
| Production Companies | 47 | `data/companies/companies.json` |
| Bill-Company Pairs | 940 | `data/mappings/*.json` |
| Event Windows | 5 (`[-1,+1]`, `[0,+1]`, `[0,+2]`, `[0,+5]`, `[-5,+5]`) | Feature / Prediction indices |
| Total Prediction Records | 4,700 | `data/predictions/*.json` |
| Total Decision Records | 4,700 | `data/decision_support/*.json` |
| Total Anticipation Records | 940 | `data/anticipation/scores/*.json` |
| Total Stakeholder Reports | 14,100 | `data/reports/stakeholder_reports/*/*.json` |
| Ground Truth Labels | 4,700 | `data/labels/*.json` |
| Event Study Records | 4,700 | `data/event_studies/*.json` |
| Automated Test Baseline | 1,226 / 1,226 passing (100%) | `tests/` |

---

## 3. Existing Feature Inventory

A systematic audit across all 19 functional areas of the repository confirms the following implementation state:

1. **Data Ingestion Modules (`ingestion/`):**
   - Central bills: `ingestion/parliament/` (`discovery.py`, `downloader.py`, `extractor.py`, `parser.py`, `normalizer.py`, `service.py`, `connector.py`). Highly robust with rate limiting and retry logic.
   - Listed equities: `ingestion/companies/company_loader.py` and `ingestion/market/market_loader.py`.
   - News / External: `ingestion/external/news_loader.py` is a non-functional placeholder raising `NotImplementedError`.
2. **Legislative Repositories (`storage/`):**
   - `storage/bill_repository.py`: CRUD and indexed querying (`get_by_year`, `get_by_ministry`, `get_by_status`, `get_by_sector`).
   - `storage/catalog.py`: Production dataset catalog tracking records, hashes, and staleness.
3. **Bill Schemas / Models (`schemas/`):**
   - `schemas/bill.py`: `Bill` dataclass with 38 fields, lifecycle `BillStatus` enum (12 values), and `BillHouse` enum (`lok_sabha`, `rajya_sabha`, `unknown`).
4. **Company Repositories (`storage/company_repository.py`):**
   - Complete entity store with lookup by ISIN, ticker, sector, and market cap category.
5. **Sector / Knowledge-Layer Modules (`knowledge/`, `mapping/`):**
   - `knowledge/engine.py`: Rules-based taxonomy classifying bills into 15 sectors, policy domains, economic domains, and regulatory authorities.
   - `mapping/engine.py`: Maps bills to candidate companies using sector overlap and keyword heuristics.
6. **Prediction Modules (`prediction/`, `services/prediction.py`):**
   - `prediction/engine.py`, `prediction/decision_engine.py`, `prediction/model_selector.py`, `prediction/validator.py`: Multi-model ensemble generating direction, impact strength, confidence, and market-moving probability.
7. **Backtesting Modules (`backtesting/`):**
   - `backtesting/engine.py`, `strategy.py`, `metrics.py`, `visualizer.py`, `overlap_detector.py`, `financial_validator.py`: Walk-forward out-of-sample portfolio simulation against Nifty 50.
8. **Anticipation Modules (`anticipation/`):**
   - `anticipation/engine.py`, `scorer.py`, `market_analyzer.py`, `signal_detector.py`: Evaluates pre-event information diffusion across 4 lookback windows (`[-30,-1]`, `[-15,-1]`, `[-5,-1]`, `[-2,-1]`).
9. **Decision-Support Modules (`decision_support/`):**
   - `decision_support/engine.py`, `risk_scorer.py`, `stakeholder_synthesizer.py`, `validator.py`: Generates composite risk scores and 3 tailored stakeholder narratives.
10. **Reporting Modules (`reporting/`):**
    - `reporting/engine.py`, `investor_reporter.py`, `business_reporter.py`, `public_reporter.py`, `bill_aggregator.py`, `company_aggregator.py`, `formatter.py`: Formats reports to JSON, Markdown, and CSV.
11. **Dashboard Pages / Components (`dashboard/`):**
    - 10 primary pages (`overview.py`, `bills.py`, `bill_detail.py`, `companies.py`, `company_detail.py`, `predictions.py`, `risk.py`, `anticipation.py`, `backtesting.py`, `methodology.py`) plus 10 legacy/explorer views.
    - Modular components for cards, filters, tables, charts, disclaimers, and report viewers.
12. **Dashboard Services (`dashboard/services/`):**
    - `dashboard_service.py`: High-performance, in-memory cached data provider.
    - `data_service.py`: Decision DataFrame builder.
    - `scope_service.py`: Scope diagnostic auditor.
13. **AI / Groq Code:**
    - `services/explanation.py`: Abstract `LLMProvider(ABC)` and `ExplanationService`. Concrete Groq implementation is absent.
14. **Notification / Alert Code:**
    - Absent from code; documented conceptually in roadmap.
15. **Authentication / User Management:**
    - Absent from code.
16. **Export / Report-Download Functionality:**
    - Backend supports JSON, Markdown, and CSV (`reporting/formatter.py`). Download buttons exist in `report_viewer.py` and explorer pages. Primary pages lack prominent download widgets; PDF export is missing.
17. **Search / Filter Functionality:**
    - Global sidebar search, master table search, multi-field dropdown filters, and lookback filters exist.
18. **Configuration / Settings (`config/`):**
    - `config/settings.py` manages all paths and environmental variables. Groq API keys and State bill settings are not yet defined.
19. **Automated Tests (`tests/`):**
    - 1,226 unit, integration, and regression tests validating all layers.

---

## 4. Feature Gap Matrix

The following matrix audits all 114 candidate features across 10 functional domains.  
**Allowed Statuses:** `IMPLEMENTED` | `PARTIALLY_IMPLEMENTED` | `NOT_IMPLEMENTED` | `UNKNOWN`

### A. LEGISLATIVE COVERAGE
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Central Government bills | IMPLEMENTED | 20 bills in catalog | `data/bills/metadata/`, `schemas/bill.py`, `storage/bill_repository.py` | Complete pipeline: scraping, PDF, metadata, text extraction, knowledge, mapping | None for Central bills | Baseline frozen | P0 |
| 2 | State bills | NOT_IMPLEMENTED | 0 state records | `schemas/bill.py`, `storage/bill_repository.py` | None | Scraper/loader, PDF storage, state metadata, state bill parsing | State legislative portals lack uniform APIs | P0 |
| 3 | Central vs State classification | NOT_IMPLEMENTED | No jurisdiction enum | `schemas/bill.py`, `schemas/knowledge_record.py` | `KnowledgeRecord.geographic_scope` set to "National" | `jurisdiction` or `level` field on `Bill` schema and query filters | Schema extension must be backward-compatible | P0 |
| 4 | State identification | PARTIALLY_IMPLEMENTED | Available on Company | `schemas/company.py`, `schemas/bill.py` | `Company.hq_state` is populated for 47 companies | `Bill.state` attribute does not exist | Must distinguish Central (null) from State names | P0 |
| 5 | State-wise bill browsing | NOT_IMPLEMENTED | No state UI selector | `dashboard/pages/bills.py`, `dashboard/services/dashboard_service.py` | National bill browsing | State dropdown, state-filtered table views, state summary cards | Depends on State bill ingestion | P0 |
| 6 | Legislature identification | PARTIALLY_IMPLEMENTED | Lok/Rajya Sabha only | `schemas/bill.py` (`BillHouse` enum) | `lok_sabha`, `rajya_sabha`, `unknown` | `vidhan_sabha` (Assembly) and `vidhan_parishad` (Council) | Enum expansion must preserve string serialization | P0 |
| 7 | Ministry/Department identification | IMPLEMENTED | Ministry strings | `schemas/bill.py`, `schemas/knowledge_record.py` | `Bill.ministry`, `KnowledgeRecord.department`, taxonomy mapping | None for Central; State departments can reuse existing fields | State departments use different naming conventions | P0 |
| 8 | Bill type classification | IMPLEMENTED | Category mapping | `schemas/knowledge_record.py`, `dashboard/services/dashboard_service.py` | `KnowledgeRecord.bill_type`, `classify_bill()` with 10+ policy categories | Formal State bill type taxonomy | None | P1 |
| 9 | Bill status | IMPLEMENTED | 12 status states | `schemas/bill.py` (`BillStatus` enum) | Complete lifecycle (introduced, pending, passed, assented, etc.) | None | Standardized across Indian legislatures | P0 |
| 10 | Bill introduction date | IMPLEMENTED | Authoritative date | `schemas/bill.py` (`Bill.introduction_date`) | Canonical parliamentary tabling date enforced system-wide | None | Baseline frozen | P0 |
| 11 | Official source/provenance | IMPLEMENTED | PRS & Lok Sabha | `schemas/bill.py`, `storage/catalog.py`, `docs/data_provenance.md` | Source URLs, SHA-256 checksums, dataset catalog entries | State portal provenance tracking | None | P0 |
| 12 | Bill PDF/document access | IMPLEMENTED | PDF downloader | `data/bills/pdfs/`, `ingestion/parliament/downloader.py` | Local PDF storage, URL links, text extraction pipelines | PDF access for State bills | State portal PDFs are often scanned images | P0 |
| 13 | Related bills | IMPLEMENTED | Slugs stored | `schemas/bill.py` (`related_bills`, `related_acts`) | Relationship lists captured during ingestion | State-Central cross-referencing | None | P1 |

### B. LEGISLATIVE KNOWLEDGE / DISCOVERY
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 14 | New Bills feed | IMPLEMENTED | Overview page feed | `dashboard/pages/overview.py`, `dashboard/services/dashboard_service.py` | Introduction date-based feed with 7-365 day lookbacks | State bill filtering option | None | P0 |
| 15 | Bill search | IMPLEMENTED | Global & page search | `dashboard/app.py`, `dashboard/pages/bills.py`, `dashboard_service.py` | Full-text substring search on title, number, ministry, sector, category | Search by State / Legislature | None | P0 |
| 16 | Advanced filters | IMPLEMENTED | Sidebar & expanders | `dashboard/components/filter_sidebar.py`, `dashboard/pages/bills.py` | Filters for Ministry, Sector, Direction, Risk, Anticipation, Window | State / Jurisdiction filters | None | P0 |
| 17 | Date filtering | PARTIALLY_IMPLEMENTED | Feed lookback & sort | `dashboard/pages/overview.py`, `dashboard/pages/bills.py` | Fixed lookback windows (7-365d) and date column sorting | Custom arbitrary date-range picker (`st.date_input`) | Low complexity | P1 |
| 18 | Sector filtering | IMPLEMENTED | Multi-select / dropdown | `dashboard/components/filter_sidebar.py`, `dashboard/pages/companies.py` | 15 NSE/SEBI sector filters | None | None | P0 |
| 19 | Ministry/Department filtering | IMPLEMENTED | Dropdown in sidebar | `dashboard/components/filter_sidebar.py`, `dashboard/pages/bills.py` | Sponsoring ministry filter | State department normalization | None | P1 |
| 20 | State filtering | NOT_IMPLEMENTED | No filter logic | `dashboard/components/filter_sidebar.py`, `dashboard/filters/filter_engine.py` | None | State filter dropdown in sidebar and master tables | Depends on State bill schema | P0 |
| 21 | Bill-type filtering | IMPLEMENTED | Category dropdown | `dashboard/pages/bills.py` | Filter by 10+ derived bill categories | Filter by formal legal type (Money, Ordinary, Constitutional) | Minor metadata enhancement | P1 |
| 22 | Bill timeline/history | IMPLEMENTED | Milestone timeline | `dashboard/pages/bill_detail.py` (Section 6) | Introduction, assent, and gazette milestone presentation | Committee hearing dates | None | P1 |
| 23 | Bill comparison | NOT_IMPLEMENTED | No side-by-side view | `dashboard/pages/` | None | Side-by-side comparative viewer for 2 bills | Low risk; high demo value | P1 |
| 24 | Plain-language bill explanation | IMPLEMENTED | Plain summaries | `dashboard/pages/bill_detail.py` (Section 1), `schemas/decision.py` | Deterministic plain-English summary of bill and key changes | Dynamic LLM-generated interactive plain explanation | Depends on Groq integration | P0 |
| 25 | Key provisions | IMPLEMENTED | Core changes box | `dashboard/pages/bill_detail.py`, `schemas/knowledge_record.py` | Key legal provisions displayed in executive dossier | Clause-by-clause diffing | None | P1 |
| 26 | Who is affected | IMPLEMENTED | Stakeholder lists | `schemas/knowledge_record.py`, `dashboard/pages/bill_detail.py` | Stakeholder groups and affected company tables | Quantified direct vs indirect exposure scores | None | P1 |
| 27 | Sector classification | IMPLEMENTED | Knowledge engine | `knowledge/engine.py`, `knowledge/sector_domain_mapping.csv` | Primary and secondary sector classification | Sub-sector mapping for state-level industries | None | P0 |
| 28 | Policy-domain classification | IMPLEMENTED | Domain mapping | `knowledge/engine.py`, `schemas/knowledge_record.py` | Policy domain and economic domain classification | None | None | P1 |
| 29 | Source/provenance display | IMPLEMENTED | Audit diagnostics | `dashboard/pages/overview.py`, `dashboard/pages/methodology.py` | Portal URLs, checksums, verified document counts | State portal provenance links | None | P0 |

### C. STATE-SPECIFIC INTELLIGENCE
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 30 | State-specific sectors | NOT_IMPLEMENTED | National sectors only | `knowledge/sector_domain_mapping.csv` | National SEBI sectors | State sectoral GDP weightings (e.g. MH BFSI, GJ Chemicals) | Requires state economic data collection | P1 |
| 31 | State-specific companies | PARTIALLY_IMPLEMENTED | `Company.hq_state` | `schemas/company.py`, `data/companies/companies.json` | Headquarters state is recorded for all 47 production companies | State-level company directory, regional operating footprint | HQ state does not equal operational footprint | P0 |
| 32 | State-specific economic exposure | NOT_IMPLEMENTED | No state macro data | `mapping/` | National company exposure | GSDP exposure metrics, state revenue breakdown | Data availability limited for listed equities | P2 |
| 33 | State-specific stakeholder groups | NOT_IMPLEMENTED | National groups only | `knowledge/sector_domain_mapping.csv` | National stakeholder groups | State farmer unions, state trade bodies, local municipal bodies | Manual curation needed | P1 |
| 34 | Listed vs unlisted company distinction | PARTIALLY_IMPLEMENTED | `listing_status` field | `schemas/company.py` | Field exists (`listing_status = "Listed"`) | Ingestion of unlisted / MSME private entities | Modeling unlisted firms lacks market price labels | P2 |
| 35 | State → sector mapping | NOT_IMPLEMENTED | No mapping file | `knowledge/` | None | Matrix mapping Indian States to key driver sectors | Low complexity; high analytical value | P0 |
| 36 | State → company mapping | PARTIALLY_IMPLEMENTED | Query by HQ state | `storage/company_repository.py` | Can filter existing companies by `hq_state` | Explicit mapping table and regional subsidiary modeling | Straightforward extension | P0 |
| 37 | State → stakeholder mapping | NOT_IMPLEMENTED | No state mapping | `knowledge/` | None | Mapping connecting states to local constituent groups | Medium complexity | P1 |

### D. MARKET INTELLIGENCE
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 38 | Market direction prediction | IMPLEMENTED | 4,700 predictions | `data/predictions/`, `schemas/prediction.py`, `models/` | POSITIVE / NEGATIVE / NEUTRAL calibrated probabilities | None for Central bills | Baseline frozen | P0 |
| 39 | Market-moving probability | IMPLEMENTED | Probability values | `schemas/prediction.py`, `schemas/decision.py` | Continuous probability [0.0 - 1.0] and binary classification | None | Baseline frozen | P0 |
| 40 | Impact strength | IMPLEMENTED | Categorical strength | `schemas/prediction.py`, `prediction/engine.py` | LOW / MEDIUM / HIGH / VERY_HIGH across all records | None | Baseline frozen | P0 |
| 41 | Prediction confidence | IMPLEMENTED | Confidence classes | `schemas/prediction.py`, `decision_support/risk_scorer.py` | LOW / MEDIUM / HIGH confidence with probability distribution | None | Baseline frozen | P0 |
| 42 | Risk score | IMPLEMENTED | Composite risk score | `decision_support/risk_scorer.py`, `schemas/decision.py` | Continuous score [0.0 - 1.0] and 5 tiers (VERY_LOW to VERY_HIGH) | None | Baseline frozen | P0 |
| 43 | Company exposure | IMPLEMENTED | 940 pairs | `data/mappings/`, `dashboard/pages/company_detail.py` | Mapped candidate companies, tickers, sectors, and industries | State bill company exposure | Baseline frozen | P0 |
| 44 | Sector exposure | IMPLEMENTED | Sector aggregations | `dashboard/charts/sector_charts.py`, `dashboard/pages/predictions.py` | Aggregated predictions, direction distribution by sector | State-level sector breakdowns | Baseline frozen | P0 |
| 45 | Historical market reaction | IMPLEMENTED | 4,700 event studies | `data/event_studies/`, `labeling/event_study.py` | Abnormal returns (AR) and CAR across 5 event windows | Event studies for State bills | Baseline frozen | P0 |
| 46 | Event-study visualization | IMPLEMENTED | Plotly CAR plots | `dashboard/pages/anticipation.py`, `dashboard/charts/distribution_charts.py` | Interactive CAR trajectory plots, distribution charts | Side-by-side multi-window overlay | Baseline frozen | P0 |
| 47 | Model explanation / SHAP | IMPLEMENTED | SHAP values | `explainability/`, `storage/explainability_repository.py` | TreeExplainer SHAP feature importance, top impact drivers | Dynamic local explanation per State bill | Baseline frozen | P0 |
| 48 | Anticipation/pricing-in analysis | IMPLEMENTED | 940 anticipation files | `anticipation/`, `data/anticipation/scores/` | Pre-event CAR drift, diffusion tiers, non-insider disclaimers | Live news media signal integration | Baseline frozen | P0 |

### E. STAKEHOLDER INTELLIGENCE
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 49 | Investor perspective | IMPLEMENTED | 4,700 reports | `reporting/investor_reporter.py`, `data/reports/stakeholder_reports/investor/` | Tailored investor dossiers with market impact, risk, and pricing-in | State bill investor reports | Baseline frozen | P0 |
| 50 | Business-owner perspective | IMPLEMENTED | 4,700 reports | `reporting/business_reporter.py`, `data/reports/stakeholder_reports/business/` | Regulatory exposure, operational implications, compliance impact | State-specific regulatory dossiers | Baseline frozen | P0 |
| 51 | Public/citizen perspective | IMPLEMENTED | 4,700 reports | `reporting/public_reporter.py`, `data/reports/stakeholder_reports/public/` | Plain-English summary, consumer price impact, societal context | Local regional citizen perspectives | Baseline frozen | P0 |
| 52 | Additional stakeholder categories | NOT_IMPLEMENTED | Only 3 enums exist | `schemas/report.py` (`StakeholderType` enum) | INVESTOR, BUSINESS, PUBLIC | REGULATOR, LABOUR, STATE_GOVERNMENT categories | Requires expanding report generation templates | P2 |
| 53 | Stakeholder-specific reports | IMPLEMENTED | 14,100 reports | `reporting/engine.py`, `schemas/report.py` | Complete persistence layer with deterministic IDs and validation | State bill stakeholder reports | Baseline frozen | P0 |

### F. PRODUCT FEATURES
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 54 | Watchlist | NOT_IMPLEMENTED | No watchlist code | `dashboard/` | None | User watchlist data model and in-session UI | Streamlit session state can provide lightweight MVP | P1 |
| 55 | Bill favourites | NOT_IMPLEMENTED | No bookmarking | `dashboard/pages/bills.py` | None | Star/favorite icon to pin bills in dashboard | Low complexity | P1 |
| 56 | Company watchlist | NOT_IMPLEMENTED | No watchlist code | `dashboard/pages/companies.py` | None | Watchlist table of monitored equities | Low complexity | P1 |
| 57 | Sector watchlist | NOT_IMPLEMENTED | No watchlist code | `dashboard/pages/` | None | Sector tracking dashboard view | Low complexity | P2 |
| 58 | State watchlist | NOT_IMPLEMENTED | No watchlist code | `dashboard/pages/` | None | Multi-state comparison watchlist | Depends on State bills | P2 |
| 59 | Alerts/notifications | NOT_IMPLEMENTED | Roadmap only | `docs/roadmap.md` | None | Alert trigger engine (in-app, email, or webhook) | Requires backend daemon or scheduler | P2 |
| 60 | New-bill alerts | NOT_IMPLEMENTED | None | `ingestion/` | Newly arrived bills feed | Notification dispatcher when new bill is detected | Requires email/SMS service | P2 |
| 61 | Watchlist alerts | NOT_IMPLEMENTED | None | `dashboard/` | None | Alerting when bookmarked bill changes status | Requires background state tracking | P3 |
| 62 | High-impact bill alerts | NOT_IMPLEMENTED | None | `decision_support/` | None | High-visibility warning banner for high-risk bills | In-dashboard UI alert is feasible without backend | P1 |
| 63 | Report export | PARTIALLY_IMPLEMENTED | JSON in viewer | `dashboard/components/report_viewer.py` | Download Report JSON for individual reports | Unified download panel on primary pages | Low complexity | P0 |
| 64 | PDF export | NOT_IMPLEMENTED | No PDF library | `reporting/formatter.py` | None | ReportLab / WeasyPrint automated PDF dossier generation | Requires PDF generation library dependency | P1 |
| 65 | CSV export | PARTIALLY_IMPLEMENTED | Formatter exists | `reporting/formatter.py`, `dashboard/pages/bill_explorer.py` | CSV serialisation in backend and legacy explorer pages | "⬇️ Export CSV" button on primary `bills.py` and `predictions.py` | Simple Streamlit frontend addition | P0 |
| 66 | Saved reports | NOT_IMPLEMENTED | No report store | `dashboard/` | Static reports in `data/reports/` | Custom filtered report bundle saving | Requires persistence layer | P2 |

### G. NEWS / ANTICIPATION CONTEXT
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 67 | News/media integration | NOT_IMPLEMENTED | Stub with error | `ingestion/external/news_loader.py` | Stub class raising `NotImplementedError` | NewsAPI / RSS news scraper and article storage | External API cost & rate limits | P2 |
| 68 | Media coverage volume | NOT_IMPLEMENTED | Documented absent | `academic_anticipation_audit.md` | None | Article count aggregation per bill over time | Depends on news ingestion | P2 |
| 69 | Google Trends/search-interest integration | NOT_IMPLEMENTED | Documented absent | `runtime_anticipation_report.md` | Pre-event price CAR proxy | `pytrends` pipeline tracking search volume spikes | Rate limits from Google Trends | P2 |
| 70 | GDELT integration | NOT_IMPLEMENTED | Documented absent | `academic_anticipation_audit.md` | Schema field `source: str` in anticipation schema | GDELT BigQuery / API ingestion pipeline | High data volume | P2 |
| 71 | Bill-related news timeline | NOT_IMPLEMENTED | None | `dashboard/pages/bill_detail.py` | Legislative milestone timeline | News headline timeline leading up to introduction | Depends on news loader | P2 |
| 72 | Pre-introduction information analysis | PARTIALLY_IMPLEMENTED | Market drift only | `anticipation/engine.py`, `data/anticipation/scores/` | Quantitative CAR analysis across 4 pre-event windows | Non-market multi-modal media evidence | Preserved baseline integrity | P1 |

### H. AI / GROQ
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 73 | Groq integration | NOT_IMPLEMENTED | Abstract base only | `services/explanation.py` | `LLMProvider(ABC)` with 3 abstract methods | `GroqProvider` class, `groq` SDK integration, API client | Requires Groq API key | P0 |
| 74 | Bill Q&A | PARTIALLY_IMPLEMENTED | Service method | `services/explanation.py` (`ask_question`) | Context building across bills with dummy provider test | Live conversational response generation | High demo & presentation value | P0 |
| 75 | Plain-language AI explanation | PARTIALLY_IMPLEMENTED | Template/rule-based | `dashboard/pages/bill_detail.py`, `services/explanation.py` | Static plain summaries from PRS / knowledge engine | Dynamic, contextual LLM bill summaries via Groq | Seamless drop-in | P0 |
| 76 | Investor-oriented AI explanation | PARTIALLY_IMPLEMENTED | Rule-based report | `reporting/investor_reporter.py` | Structured institutional investor report text | Dynamic LLM synthesis of portfolio risk and valuation impact | Prompt engineering | P1 |
| 77 | Business-oriented AI explanation | PARTIALLY_IMPLEMENTED | Rule-based report | `reporting/business_reporter.py` | Regulatory summary and compliance sectors | Dynamic corporate advisory narrative | Prompt engineering | P1 |
| 78 | Citizen-oriented AI explanation | PARTIALLY_IMPLEMENTED | Rule-based report | `reporting/public_reporter.py` | Consumer impact summary | Dynamic layman explainer of rights and pocketbook impact | Prompt engineering | P1 |
| 79 | AI explanation of prediction | PARTIALLY_IMPLEMENTED | SHAP + templates | `decision_support/stakeholder_synthesizer.py` | Deterministic decision reason and SHAP importance | Natural language translation of SHAP drivers | High FYP viva value | P1 |
| 80 | AI explanation of risk | PARTIALLY_IMPLEMENTED | 5-tier breakdown | `decision_support/risk_scorer.py` | Multi-factor risk component breakdown | Dynamic LLM risk synthesis | Prompt engineering | P1 |
| 81 | AI source/evidence grounding | NOT_IMPLEMENTED | None | `services/explanation.py` | Full text stored in bill records | Retrieval-augmented generation (RAG) with exact clause citations | Improves factual accuracy | P1 |
| 82 | AI safety/financial-advice guardrails | PARTIALLY_IMPLEMENTED | Static disclaimers | `schemas/report.py`, `dashboard/components/disclaimer.py` | Legal research disclaimers hardcoded in UI and reports | Automated system prompt guardrails against investment advice | Essential for responsible AI deployment | P0 |

### I. FRONTEND / UX
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 83 | Existing dashboard | IMPLEMENTED | Complete app | `dashboard/app.py` | Full multi-page Streamlit dashboard | None | Baseline frozen | P0 |
| 84 | Dashboard overview | IMPLEMENTED | Home page | `dashboard/pages/overview.py` | KPIs, New Bills Feed, Market Summary, Exposure Table, Scope Card | None | Baseline frozen | P0 |
| 85 | All Bills page | IMPLEMENTED | Master table | `dashboard/pages/bills.py` | Searchable, sortable, filterable 20-bill table with deep linking | State bill columns and filters | Baseline frozen | P0 |
| 86 | Bill Intelligence page | IMPLEMENTED | Deep dive | `dashboard/pages/bill_detail.py` | 8-section dossier: summary, sectors, impact, risk, anticipation, timeline, companies, stakeholders | State bill support, AI chat drawer | Baseline frozen | P0 |
| 87 | Company Intelligence page | IMPLEMENTED | Company table | `dashboard/pages/companies.py` | 47-company comparative universe, market cap, exposure metrics | State filter dropdown | Baseline frozen | P0 |
| 88 | Company Detail page | IMPLEMENTED | Company dossier | `dashboard/pages/company_detail.py` | Per-company exposure, related bills, decision records, risk breakdown | None | Baseline frozen | P0 |
| 89 | Predictions page | IMPLEMENTED | Analytics view | `dashboard/pages/predictions.py` | Probability distributions, impact strength bars, sector breakdown | None | Baseline frozen | P0 |
| 90 | Risk page | IMPLEMENTED | Risk overview | `dashboard/pages/risk.py` | 5-tier risk breakdown, 2D risk matrix, confidence risk charts | None | Baseline frozen | P0 |
| 91 | Anticipation page | IMPLEMENTED | Diffusion view | `dashboard/pages/anticipation.py` | Diffusion tiers, CAR line charts, Anticipation Paradox explanation | Live news feed overlay | Baseline frozen | P0 |
| 92 | Historical Backtesting page | IMPLEMENTED | Strategy view | `dashboard/pages/backtesting.py` | Walk-forward equity curves, Nifty 50 alpha, Sharpe, drawdowns | None | Baseline frozen | P0 |
| 93 | Academic Methodology page | IMPLEMENTED | 18-stage guide | `dashboard/pages/methodology.py` | Exhaustive pipeline blueprint and research disclaimers | State bill methodology addition | Baseline frozen | P0 |
| 94 | Central/State navigation | NOT_IMPLEMENTED | Unified nav only | `dashboard/app.py` | Single sidebar navigation menu | Central vs State navigation toggle or segmented tabs | Crucial for State expansion | P0 |
| 95 | State selector | NOT_IMPLEMENTED | None | `dashboard/components/filter_sidebar.py` | None | Dedicated state dropdown / pill selector in UI | Straightforward Streamlit component | P0 |
| 96 | Sector explorer | IMPLEMENTED | Sector views | `dashboard/charts/sector_charts.py`, `dashboard/pages/companies.py` | Interactive Plotly sector charts | None | Baseline frozen | P0 |
| 97 | Company explorer | IMPLEMENTED | Explorer views | `dashboard/pages/companies.py`, `dashboard/pages/company_explorer.py` | Master company table with sector and cap filtering | None | Baseline frozen | P0 |
| 98 | Interactive charts | IMPLEMENTED | Plotly charts | `dashboard/charts/` | Plotly figures for distributions, backtest, risk matrix, CAR | None | Baseline frozen | P0 |
| 99 | Modern visual design | IMPLEMENTED | CSS & badges | `dashboard/pages/`, `dashboard/components/` | Custom CSS cards, semantic color badges, clean hierarchy | None | Baseline frozen | P0 |
| 100 | Responsive layout | IMPLEMENTED | Wide mode | `dashboard/app.py`, `dashboard/pages/` | Streamlit wide mode, multi-column layouts | None | Baseline frozen | P0 |
| 101 | User-friendly navigation | IMPLEMENTED | Deep linking | `dashboard/app.py`, `dashboard/pages/bills.py` | Seamless drilldown buttons ("Open Bill Intelligence", "⬅️ All Bills") | Breadcrumb trail | Baseline frozen | P0 |
| 102 | Search UX | IMPLEMENTED | Global & in-page | `dashboard/app.py`, `dashboard/pages/bills.py` | Global sidebar bill search with auto-complete; in-table search | None | Baseline frozen | P0 |
| 103 | Filter UX | IMPLEMENTED | Expanders | `dashboard/components/filter_sidebar.py`, `dashboard/pages/bills.py` | Compact collapsible expanders for secondary filters | None | Baseline frozen | P0 |
| 104 | AI assistant UI | NOT_IMPLEMENTED | None | `dashboard/` | None | Conversational chat drawer or Q&A tab on Bill Intelligence | Very high demo impact | P0 |

### J. SAAS / USER FEATURES
| # | Feature | Status | Evidence | Existing Files/Modules | What Is Already Available | What Is Missing | Dependencies/Risks | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 105 | User accounts | NOT_IMPLEMENTED | No auth schema | None | None | User database schema, registration, password hashing | Out of scope for academic baseline | P3 |
| 106 | Authentication | NOT_IMPLEMENTED | No login routes | None | None | Login/logout, JWT, OAuth, or Streamlit authenticator | Future SaaS phase | P3 |
| 107 | User profiles | NOT_IMPLEMENTED | None | None | None | Profile management, organization, role | Future SaaS phase | P3 |
| 108 | Personalized dashboard | NOT_IMPLEMENTED | None | None | None | Custom homepage widgets per user role | Future SaaS phase | P3 |
| 109 | Saved preferences | NOT_IMPLEMENTED | None | None | None | Persistent filter preferences, default sector/state | Future SaaS phase | P3 |
| 110 | Personal watchlists | NOT_IMPLEMENTED | None | None | None | Multi-device persistent watchlists saved to DB | Future SaaS phase | P3 |
| 111 | Notification preferences | NOT_IMPLEMENTED | None | None | None | Email digest frequency, SMS toggle | Future SaaS phase | P3 |
| 112 | Multi-user support | NOT_IMPLEMENTED | Single-tenant | `dashboard/app.py` | Stateless multi-session Streamlit execution | User tenant isolation and data ownership | Future SaaS phase | P3 |
| 113 | Subscription-ready architecture | NOT_IMPLEMENTED | None | None | None | Stripe/Razorpay billing, tier gating (Free, Pro, Enterprise) | Commercial roadmap | P3 |
| 114 | Usage tracking | NOT_IMPLEMENTED | None | None | None | API call metering, token counting, user activity logs | Commercial roadmap | P3 |

---

## 5. Duplicate / Overlap Analysis

A critical finding of this audit is that several features frequently requested as "new" are **already implemented** under existing modules. Rebuilding these components would introduce technical debt, risk breaking baseline test determinism, and waste engineering bandwidth.

```
+----------------------------------------------------------------------------------------------------+
|                                    FEATURE OVERLAP & REUSE ARCHITECTURE                            |
+----------------------------------------------------------------------------------------------------+
|  Requested Concept             Existing Subsystem                      Extension Recommendation    |
|  -----------------             ------------------                      ------------------------    |
|  1. "New Bills Feed"       ->  DashboardService.get_newly_arrived_bills() Extend with state param  |
|  2. "Bill Search"          ->  DashboardService.search_bills()         Extend to search state/leg  |
|  3. "Stakeholder Reports"  ->  reporting/ + DecisionSupportRecord       Reuse templates for State   |
|  4. "Risk Scoring"         ->  decision_support/risk_scorer.py          Feed State records to engine|
|  5. "Company Exposure"     ->  mapping/ + DashboardService              Add state-level filter      |
|  6. "Plain AI Summary"     ->  ExplanationService + public_summary     Plug Groq into LLMProvider  |
+----------------------------------------------------------------------------------------------------+
```

### Detailed Overlap Items:

1. **New Bills Feed:**
   - *Existing Implementation:* `DashboardService.get_newly_arrived_bills()` and `overview.py` (`_render_newly_arrived_bills_section`). Uses strictly `Bill.introduction_date` with configurable lookback windows.
   - *New Requested Feature:* Newly Introduced Bills Feed.
   - *Can existing implementation be extended?* **YES.**
   - *Recommended Action:* Do NOT rebuild. Add an optional `state: Optional[str] = None` parameter to `get_newly_arrived_bills()` to filter between Central and State bills.

2. **Bill Search:**
   - *Existing Implementation:* Global sidebar search in `dashboard/app.py` calling `DashboardService.search_bills()`, and in-table search in `dashboard/pages/bills.py`.
   - *New Requested Feature:* Multi-criteria legislative search.
   - *Can existing implementation be extended?* **YES.**
   - *Recommended Action:* Extend `search_bills()` to include `state` and `legislature` attributes when State bills are ingested.

3. **Stakeholder Reports:**
   - *Existing Implementation:* `reporting/investor_reporter.py`, `business_reporter.py`, and `public_reporter.py` which generated 14,100 validated reports on disk, accompanied by `decision_support/stakeholder_synthesizer.py`.
   - *New Requested Feature:* Multi-perspective stakeholder intelligence.
   - *Can existing implementation be extended?* **YES.**
   - *Recommended Action:* Reuse the existing reporting engine and data models (`schemas/report.py`). Do NOT create a separate report generator for State bills.

4. **Risk Scoring:**
   - *Existing Implementation:* `decision_support/risk_scorer.py` computing composite risk from confidence risk, impact magnitude, pricing-in risk, and directional uncertainty across all 4,700 records.
   - *New Requested Feature:* Risk analysis and risk scoring.
   - *Can existing implementation be extended?* **YES.**
   - *Recommended Action:* The risk calculation formula is mathematically validated and frozen. Any future State bill predictions should pass through this exact scorer.

5. **Company Exposure:**
   - *Existing Implementation:* `mapping/engine.py` mapping bills to companies, and `DashboardService.get_company_exposure_table()`.
   - *New Requested Feature:* Company exposure mapping.
   - *Can existing implementation be extended?* **YES.**
   - *Recommended Action:* Reuse `BillCompanyMapping`. When State bills are introduced, incorporate `Company.hq_state` to calculate regional vs national exposure.

6. **Plain-Language Explanations:**
   - *Existing Implementation:* `services/explanation.py` (`summarize_bill()`) and `DecisionSupportRecord.public_summary`.
   - *New Requested Feature:* Plain-language AI bill explanation.
   - *Can existing implementation be extended?* **YES.**
   - *Recommended Action:* Implement `GroqProvider` as a subclass of `LLMProvider(ABC)` in `services/explanation.py`. The service will invoke Groq when online, and fall back gracefully to the deterministic `public_summary` when offline.

---

## 6. State Bill Readiness Assessment

The current system was architected primarily for Indian Central Government parliamentary bills. However, an inspection of the underlying data models and storage layers reveals substantial architectural readiness for State bills:

### Field-by-Field Readiness Matrix:
| Field / Capability | Existing Status in Codebase | Exact Existing File | Action Required for State Bill Phase |
| :--- | :--- | :--- | :--- |
| **`jurisdiction`** | Missing (implicit "Central") | `schemas/bill.py` | Add `jurisdiction: str = "Central"` (Values: `"Central"`, `"State"`) |
| **`state`** | Present on `Company`, missing on `Bill` | `schemas/company.py:84`, `schemas/bill.py` | Add `state: Optional[str] = None` to `Bill` dataclass (e.g. `"Maharashtra"`, `"Karnataka"`) |
| **`legislature`** | House enum present (`lok_sabha`, `rajya_sabha`) | `schemas/bill.py:47` (`BillHouse`) | Extend `BillHouse` enum to include `vidhan_sabha`, `vidhan_parishad` or add `legislature_name: str` |
| **`department`** | Present in `KnowledgeRecord`, `ministry` in `Bill` | `schemas/knowledge_record.py:23`, `schemas/bill.py:78` | State departments can map directly into `Bill.ministry` or add `department: str = ""` alias |
| **`bill_id` / slug** | Fully supported | `schemas/bill.py:67` | Format: `{state-slug}-{bill-slug}-{year}` (e.g. `"mh-cooperative-societies-2024"`) |
| **`bill_type`** | Supported in KnowledgeRecord & taxonomy | `schemas/knowledge_record.py:31` | Already defaults to `"Ordinary Bill"`; maps to policy categories |
| **`introduction_date`** | Fully supported | `schemas/bill.py:83` | Standard ISO `datetime.date`. Enforces same temporal non-leakage rules |
| **`status`** | Fully supported | `schemas/bill.py:30` (`BillStatus`) | State legislative statuses map directly to existing 12 enum values |
| **`sectors`** | Fully supported | `schemas/bill.py:113`, `schemas/knowledge_record.py:26` | 15 SEBI sectors apply equally to state economic domains |
| **`companies`** | Supported via mapping and `hq_state` | `schemas/company.py`, `storage/company_repository.py` | Companies already have `hq_state` (e.g. Maharashtra, Karnataka) |
| **`stakeholders`** | Supported in Knowledge & Reports | `schemas/knowledge_record.py:28`, `schemas/report.py` | Stakeholder engine handles arbitrary stakeholder strings |
| **`sources`** | Supported | `schemas/bill.py:118` | `Bill.source` accepts any portal identifier (e.g. `"prs_state"`, `"maha_vidhansabha"`) |

### Architectural Verdict on State Bills:
- **No fundamental redesign required.** The existing schema architecture can ingest State bills with only **3 backward-compatible optional fields** on `Bill` (`jurisdiction`, `state`, `legislature`).
- The existing Central bill dataset (`data/bills/metadata/*.json`) will remain 100% untouched and backward-compatible by defaulting `jurisdiction="Central"` and `state=None`.

---

## 7. Frontend Gap Assessment

The Streamlit dashboard currently encompasses 20 pages (10 primary production pages and 10 legacy explorer pages), supported by 10 modular UI component files and 3 core service engines.

### 1. Existing Frontend Strengths:
- **Comprehensive Analytical Flow:** Direct navigation from macro KPIs -> New Bills Feed -> All Bills master table -> Bill Intelligence -> Affected Company View -> Company Detail.
- **Academic Rigor:** Prominent disclaimers, mathematical formula references, non-insider anticipation terminology, and zero-modification banners.
- **Deep Linking:** Interactive buttons allow drilling down between bills, companies, and risk profiles.
- **Responsive Visuals:** Clean Plotly charts for distribution, risk matrix, backtest equity curves, and sector exposure.

### 2. Frontend Gaps Identified:
- **Central vs State Scope Navigation:** No UI toggle to switch between Central Government and State Government legislation.
- **State Selection / Filtering:** Missing state dropdowns in the global filter sidebar and table headers.
- **Data Export Accessibility:** Although `reporting/formatter.py` supports CSV and JSON, the primary 10 production pages lack one-click CSV/PDF download buttons.
- **Interactive AI Assistant:** No in-app chat drawer or conversational Q&A widget to query bill provisions.
- **Date Range Selector:** Master tables rely on sorting or fixed lookbacks rather than flexible calendar date pickers.

### 3. Separation of Frontend Changes:

#### A. FRONTEND-ONLY FEATURES (No Backend Service Changes Required)
These features can be built immediately using already available data:
1. **CSV Export Buttons on Primary Pages:** Add `st.download_button(df.to_csv(), "bills.csv")` to `bills.py`, `predictions.py`, and `companies.py`.
2. **Date Range Filter Widget:** Add `st.date_input` to `bills.py` to filter existing `Introduction Date` rows.
3. **Bill Comparison Viewer:** Implement a side-by-side comparison page comparing two selected bills using `service.get_bill_detail_data()`.
4. **Company State Filter:** Add a "Headquarters State" filter to `companies.py` using existing `Company.hq_state`.
5. **In-Session Watchlist / Bookmarking:** Implement session-state bookmarking (`st.session_state["watchlist"] = []`) allowing users to pin favorite bills.
6. **Central / State UI Tabs:** Add navigation tabs in the sidebar preparing the UI structure for state legislation.

#### B. BACKEND + FRONTEND FEATURES (Requires Data & Services)
1. **State Bill Ingestion & Browsing:** Ingesting state PDFs, parsing metadata, and rendering state bills.
2. **Groq AI Chat Assistant:** Building `GroqProvider` in backend and adding conversational chat UI in Streamlit.
3. **PDF Report Export:** Implementing a PDF generation engine (`reporting/pdf_formatter.py`) and wiring download buttons.
4. **State-Level Economic & Sector Mapping:** Modeling state GDP weights and mapping local companies.

---

## 8. Product Feature Gap Assessment

| Product Feature | Current State | Feasibility | MVP Recommendation |
| :--- | :--- | :--- | :--- |
| **Watchlist / Favorites** | NOT_IMPLEMENTED | High (Frontend session state) | Implement `st.session_state["favorites"]` with star icons in tables; allow filtering table to "Favorites Only". |
| **Alerts / Notifications** | NOT_IMPLEMENTED | Medium | Add in-app notification banners on the Overview page for "High-Impact Bills (P > 70%)". Defer email/SMS. |
| **Report Export (CSV / JSON)**| PARTIALLY_IMPLEMENTED | High | Expose one-click download buttons on all master tables and bill detail dossiers. |
| **Report Export (PDF)** | NOT_IMPLEMENTED | Medium | Build a lightweight PDF template generator using ReportLab for 1-page executive bill summaries. |
| **Saved Searches / Filters** | NOT_IMPLEMENTED | Low-Medium | Persist filter state across page reloads via session state. |

---

## 9. Groq / AI Gap Assessment

The codebase contains an elegant, pre-designed extension point for Groq LLM integration in `services/explanation.py`.

### Existing Architecture:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_summary(self, bill_title: str, bill_text: str) -> str: ...
    @abstractmethod
    async def generate_explanation(self, bill_title: str, company_name: str, sector: str, predicted_impact: str) -> str: ...
    @abstractmethod
    async def chat_response(self, query: str, context: str) -> str: ...
```

### Missing Components:
1. **`GroqProvider` Implementation:** A concrete class inheriting from `LLMProvider` utilizing the official `groq` Python SDK (`groq.AsyncGroq`).
2. **Model Selection:** Use `llama-3.3-70b-versatile` or `mixtral-8x7b-32768` for high-throughput, low-latency inference.
3. **Safety & Financial Guardrails:** System prompts must strictly instruct the model:
   - Provide objective, factual explanations of legislative text.
   - Never offer financial, trading, or investment advice.
   - Always append the mandatory institutional research disclaimer.
4. **Streamlit Chat UI:** An interactive conversational assistant drawer on `bill_detail.py` allowing examiners and users to ask questions like:
   - *"What are the penalties under Section 4 of this bill?"*
   - *"Why is the banking sector predicted to have negative market impact?"*

---

## 10. SaaS Readiness Assessment

Evaluating the system against commercial SaaS multi-tenant criteria:

| Dimension | Current State | Readiness Score | Evaluation |
| :--- | :--- | :---: | :--- |
| **Data Multi-Tenancy** | Single shared disk storage | 1 / 5 | Designed for academic open-science research. No tenant partitioning. |
| **Authentication & AuthZ** | None | 1 / 5 | No user login, JWT tokens, or role-based access control. |
| **State Persistence** | Stateless Streamlit execution | 2 / 5 | Ephemeral session state; resets on page reload. |
| **Subscription & Gating** | None | 1 / 5 | All data and features are universally accessible. |
| **API Architecture** | Python class repositories | 3 / 5 | Repositories and services are cleanly decoupled; can be easily wrapped with FastAPI. |
| **Cost / Scalability** | Low compute overhead | 4 / 5 | Pre-computed static prediction artifacts serve queries in < 5 ms. |

**Verdict:** The platform is an exceptional **Research & Intelligence Workstation**. Converting it into a commercial SaaS platform is a **P3 (Post-FYP)** objective that should follow backend API wrapping (FastAPI) and PostgreSQL integration.

---

## 11. P0 / P1 / P2 / P3 Prioritization

Priorities are established based on **Final Year Project (FYP) demo value**, academic research merit, user usefulness, and feasibility while strictly safeguarding the frozen baseline:

```
+---------------------------------------------------------------------------------------------------+
|                                      FEATURE PRIORITIZATION MATRIX                                 |
+---------------------------------------------------------------------------------------------------+
|  P0 — MUST HAVE (Core FYP Value & State Extension)                                                |
|  - State Bill Data Model & Pilot Ingestion (Maharashtra / Karnataka)                              |
|  - Central vs State Classification & Navigation Toggle                                            |
|  - State Identification & State-Wise Bill Browsing                                                |
|  - State -> Company & State -> Sector Exposure Mapping                                            |
|  - Groq LLM Integration (GroqProvider in services/explanation.py)                                 |
|  - Interactive AI Bill Q&A Assistant UI in Dashboard                                              |
|  - CSV Export on Master Dashboard Tables                                                          |
+---------------------------------------------------------------------------------------------------+
|  P1 — HIGH VALUE (Academic Polish & Analytical Depth)                                             |
|  - Bill Comparison Tool (Side-by-side comparative analysis)                                       |
|  - Automated PDF Analytical Report Generation (ReportLab)                                         |
|  - In-Session Watchlist / Bookmarking UI                                                          |
|  - Flexible Calendar Date Range Filtering (st.date_input)                                         |
|  - Dynamic AI Explanation of Prediction & Risk Drivers (SHAP text translation)                    |
|  - AI Prompt Safety & Financial Advice Guardrails                                                 |
|  - State-Specific Economic Exposure & Stakeholder Profiles                                        |
+---------------------------------------------------------------------------------------------------+
|  P2 — NICE TO HAVE (Research Extensions & Secondary Features)                                     |
|  - In-Dashboard High-Impact Alert Banners                                                         |
|  - External News / Media Article Ingestion (NewsAPI / GDELT pilot)                                 |
|  - Google Trends Search Volume Integration for Anticipation Context                               |
|  - Additional Stakeholder Categories (Regulator, Labour Unions)                                   |
|  - Saved Custom Filter Bundles                                                                    |
+---------------------------------------------------------------------------------------------------+
|  P3 — FUTURE SaaS (Commercial Enterprise Platform)                                                |
|  - User Accounts & Authentication (OAuth / JWT)                                                   |
|  - PostgreSQL Multi-Tenant Database                                                               |
|  - Email / SMS / Webhook Push Notifications                                                       |
|  - Subscription Billing & Tier-Based Feature Gating                                               |
|  - API Metering & Usage Telemetry                                                                 |
+---------------------------------------------------------------------------------------------------+
```

---

## 12. Recommended Development Roadmap

The recommended sequence for future development tasks preserves the frozen Central Government baseline while expanding capabilities:

### PHASE A — State Bill Integration
- **Objective:** Ingest, parse, and store pilot State legislative bills (e.g. Maharashtra, Karnataka) without altering existing Central bill records.
- **Features:** Backward-compatible schema fields (`jurisdiction`, `state`, `legislature`), State bill scraper/loader, state metadata directory (`data/bills/state_metadata/`).
- **Dependencies:** `schemas/bill.py`, `storage/bill_repository.py`.
- **Expected Files:** `schemas/bill.py`, `ingestion/state/` (new module), `storage/state_bill_repository.py` (new).
- **Testing Requirements:** State bill serialization roundtrip, isolated catalog updates, 0 Central bill regressions.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

### PHASE B — Legislative Knowledge & Discovery Features
- **Objective:** Extend knowledge layer, search, and filtering to cover State bills and multi-jurisdictional queries.
- **Features:** Multi-jurisdiction search, state/department filtering, bill comparison tool, enhanced date-range filtering.
- **Dependencies:** Phase A state bills.
- **Expected Files:** `dashboard/services/dashboard_service.py`, `dashboard/filters/filter_engine.py`, `knowledge/engine.py`.
- **Testing Requirements:** Multi-filter query tests, search ranking tests, null-safety checks.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

### PHASE C — State Sector, Company & Stakeholder Intelligence
- **Objective:** Connect state bills to economic impact via existing company HQ states and sector dependencies.
- **Features:** State → sector mapping, State → company exposure derivation, state stakeholder profiles.
- **Dependencies:** Phase A, Phase B, existing `data/companies/companies.json`.
- **Expected Files:** `mapping/state_mapping.py` (new), `schemas/company.py`, `reporting/`.
- **Testing Requirements:** Company exposure verification, sector coverage tests.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

### PHASE D — Product Features (Exports & Watchlists)
- **Objective:** Provide practical productivity tools for analysts, investors, and policymakers.
- **Features:** CSV data export on all tables, PDF dossier export engine, in-session watchlist/favorites.
- **Dependencies:** Streamlit UI, `reporting/formatter.py`.
- **Expected Files:** `reporting/formatter.py`, `reporting/pdf_formatter.py` (new), `dashboard/pages/bills.py`, `dashboard/pages/bill_detail.py`.
- **Testing Requirements:** Export formatting tests, byte stream generation tests, session state tests.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

### PHASE E — Groq AI Integration
- **Objective:** Implement high-performance, cost-effective LLM summarization, multi-lens explanations, and conversational bill Q&A using Groq API.
- **Features:** Concrete `GroqProvider` implementing `LLMProvider`, system prompt guardrails (anti-hallucination, no financial advice), interactive chat UI in dashboard.
- **Dependencies:** `services/explanation.py`, `groq` python SDK, valid Groq API key in `.env`.
- **Expected Files:** `services/groq_provider.py` (new), `services/explanation.py`, `dashboard/components/chat_assistant.py` (new), `dashboard/pages/bill_detail.py`.
- **Testing Requirements:** Mocked LLM API tests, prompt safety guardrail tests, latency/fallback tests.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

### PHASE F — Frontend Enhancement
- **Objective:** Elevate dashboard visual polish and unify Central and State bill navigation into a seamless user experience.
- **Features:** Central vs State navigation switch, State explorer page, responsive filter bar enhancements, interactive AI assistant drawer, enhanced Plotly charts.
- **Dependencies:** Phases A-E.
- **Expected Files:** `dashboard/app.py`, `dashboard/pages/overview.py`, `dashboard/pages/bills.py`, `dashboard/components/`.
- **Testing Requirements:** Streamlit component rendering tests, end-to-end UI navigation tests.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

### PHASE G — Final Integration & QA
- **Objective:** Comprehensive cross-module validation, regression testing, and performance profiling.
- **Features:** End-to-end integration test suite, scope diagnostic verification, load testing, latency benchmarking.
- **Dependencies:** All previous phases.
- **Expected Files:** `tests/`, `docs/`.
- **Testing Requirements:** Full test suite passing with 0 regressions against the 1,226 baseline tests.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

### PHASE H — Documentation & Viva Preparation
- **Objective:** Produce academic thesis documentation, architecture diagrams, slides, and demonstration scripts for Final Year Project defense.
- **Features:** System architecture documentation, research paper / thesis chapter on multi-level legislative intelligence, presentation deck, recorded demo walkthrough.
- **Dependencies:** Completed project.
- **Expected Files:** `docs/`, `README.md`.
- **Testing Requirements:** Documentation link integrity, citation verification.
- **Existing Production Baseline:** **100% FROZEN & UNCHANGED.**

---

## 13. Existing-System Protection Verification

To verify that this audit strictly maintained the integrity of the frozen production system, the working tree was checked:

```powershell
git status --short
```

### Protection Checklist:
- [x] **0 Production Code Changes:** No files in `ingestion/`, `knowledge/`, `mapping/`, `prediction/`, `decision_support/`, `reporting/`, or `dashboard/` were modified during this task.
- [x] **0 Production Data Changes:** All 4,700 predictions, 4,700 decision records, 940 anticipation records, 14,100 reports, and 20 bill metadata files remain bit-for-bit identical.
- [x] **0 Model Changes:** Pre-trained LightGBM, XGBoost, and Random Forest model binaries in `models/artefacts/` were not retrained or altered.
- [x] **0 Backtesting Logic Changes:** Walk-forward simulation parameters and financial validation formulas were not touched.
- [x] **0 Dashboard Modifications:** Dashboard pages and services were inspected in read-only mode without code edits.
- [x] **0 Destructive Shell Commands:** No deletion, renaming, or overwrite operations were executed.

---

## 14. Test Baseline

The automated test suite was verified:

- **Total Tests Collected:** 1,226 tests across all modules
- **Total Tests Passing:** 1,226 / 1,226 (100%)
- **Test Failures:** 0
- **Test Errors:** 0
- **Test Baseline Status:** **INTACT & FULLY VERIFIED**

```
=============== 1226 passed, 1119 warnings in 854.22s (0:14:14) ===============
```

---

## 15. Final Recommendation

Based on this comprehensive audit, the highest-priority, highest-value next task for the project is:

> **RECOMMENDED NEXT TASK: Phase E.1 — Groq LLM Provider & Interactive AI Bill Assistant**  
> **Rationale:**  
> 1. The abstract interface `LLMProvider(ABC)` in `services/explanation.py` is already designed and fully tested with mocks.  
> 2. Groq's high-speed inference (Llama 3.3 70B @ 300+ tokens/sec) delivers immediate, dramatic demo impact for Final Year Project evaluators and viva presentations.  
> 3. It operates cleanly as an additive service without modifying any existing frozen data, models, backtesting, or risk-scoring pipelines.  
> 4. Following Groq AI integration, **Phase A (State Bill Ingestion & Schema Extension)** should be initiated as the structural foundation for multi-jurisdictional intelligence.

---
*Report generated and validated autonomously as part of Task 8.1.*
