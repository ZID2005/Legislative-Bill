# Dashboard Architecture & Institutional Reference Guide

**Task:** 7.4.2 — Bill Intelligence + Analytical Dashboard  
**System:** Legislative Intelligence & Market Impact Prediction System — India 2024  
**Version:** v2.0  
**Architectural Mode:** Strict Read-Only Presentation Layer  

---

## Table of Contents

1. [Architecture Overview & Workflow](#1-architecture-overview--workflow)
2. [Complete Page Directory & Capabilities](#2-complete-page-directory--capabilities)
   - [2.1 Overview & Newly Introduced Bills (`overview.py`)](#21-overview--newly-introduced-bills-overviewpy)
   - [2.2 All Bills Master Table (`bills.py`)](#22-all-bills-master-table-billspy)
   - [2.3 Bill Intelligence Deep Dive (`bill_detail.py`)](#23-bill-intelligence-deep-dive-bill_detailpy)
   - [2.4 Company Intelligence Comparative Matrix (`companies.py`)](#24-company-intelligence-comparative-matrix-companiespy)
   - [2.5 Company Detail Exposure Breakdown (`company_detail.py`)](#25-company-detail-exposure-breakdown-company_detailpy)
   - [2.6 Market Impact Predictions (`predictions.py`)](#26-market-impact-predictions-predictionspy)
   - [2.7 Risk Overview & 2D Matrix (`risk.py`)](#27-risk-overview--2d-matrix-riskpy)
   - [2.8 Anticipation & Pricing-In Analysis (`anticipation.py`)](#28-anticipation--pricing-in-analysis-anticipationpy)
   - [2.9 Historical Backtesting (`backtesting.py`)](#29-historical-backtesting-backtestingpy)
   - [2.10 Academic Methodology Blueprint (`methodology.py`)](#210-academic-methodology-blueprint-methodologypy)
3. [End-to-End Analytical Workflow](#3-end-to-end-analytical-workflow)
4. [Global Search Architecture](#4-global-search-architecture)
5. [Stakeholder Views & Multi-Perspective Synthesis](#5-stakeholder-views--multi-perspective-synthesis)
6. [Data Scope Reconciliation & Empirical Source-of-Truth](#6-data-scope-reconciliation--empirical-source-of-truth)
7. [Research Integrity & Non-Leakage Guarantees](#7-research-integrity--non-leakage-guarantees)
8. [Running the Dashboard & Verification](#8-running-the-dashboard--verification)

---

## 1. Architecture Overview & Workflow

The Legislative Intelligence & Market Impact Dashboard is structured as a decoupled, modular, presentation-only web application built using Streamlit and Plotly.

```
dashboard/
├── app.py                          # Main Streamlit application entry point & router
├── __init__.py
├── pages/
│   ├── overview.py                 # [7.4.1/7.4.2] Home + Newly Introduced Bills Feed
│   ├── bills.py                    # [7.4.2] 📜 All Bills Master Searchable Table
│   ├── bill_detail.py              # [7.4.2] 🔍 Bill Intelligence Full Dossier
│   ├── companies.py                # [7.4.2] 🏢 Company Intelligence (47 entities)
│   ├── company_detail.py           # [7.4.2] 🏢 Company Detail Drilldown
│   ├── predictions.py              # [7.4.2] 📈 Market Impact Predictions & Charts
│   ├── risk.py                     # [7.4.2] ⚠️ Risk Overview (Tiers & 2D Matrix)
│   ├── anticipation.py             # [7.4.2] 🔍 Anticipation & Pricing-In Analysis
│   ├── backtesting.py              # [7.4.2] 🔬 Historical Walk-Forward Backtesting
│   ├── methodology.py              # [7.4.2] 📐 18-Stage Academic Methodology
│   └── ...                         # Legacy exploratory views (maintained for compatibility)
├── components/
│   ├── bill_cards.py               # Feed card renderers
│   ├── cards.py                    # KPI summary metric cards
│   ├── filters.py                  # Feed and search filter widgets
│   ├── tables.py                   # Data tables and badge stylers
│   ├── filter_sidebar.py           # Multi-dimensional global filter sidebar
│   ├── disclaimer.py               # Institutional research disclaimers
│   ├── header.py                   # Diagnostic header
│   └── report_viewer.py            # Stakeholder report viewer
├── services/
│   ├── dashboard_service.py        # Authoritative read-only data access service
│   ├── data_service.py             # Enriched DataFrame provider
│   └── scope_service.py            # Empirical scope reconciliation service
└── filters/
    └── filter_engine.py            # In-memory DataFrame filter engine
```

---

## 2. Complete Page Directory & Capabilities

### 2.1 Overview & Newly Introduced Bills (`overview.py`)
- **Primary Purpose**: Executive entry point with top-level system KPIs and the Newly Introduced Bills Feed.
- **Key Logic**: Identifies new bills using `Bill.introduction_date` exclusively (the date formally tabled in Parliament). PDF download dates, file creation dates, and prediction generation dates are never used.
- **Features**: Configurable date range filters (7d, 14d, 30d, 90d, All time), market impact summaries, company exposure table, and active universe diagnostic panel.

### 2.2 All Bills Master Table (`bills.py`)
- **Primary Purpose**: Comprehensive, searchable, filterable, and sortable directory of all 20 production Central Government legislative bills.
- **Columns**:
  - `Bill` (Official title)
  - `Bill Number` (e.g. `120/2024`)
  - `Introduction Date` (Sorted newest first by default)
  - `House` (Lok Sabha / Rajya Sabha)
  - `Ministry / Department` (Sponsoring ministerial authority)
  - `Bill Type` (Derived ministerial taxonomy, e.g. Financial / Banking, Transport / Maritime, Energy)
  - `Status` (Introduced, Pending, Passed Both, Assented, etc.)
  - `Affected Sectors` (GICS aligned economic sectors)
  - `Affected Companies` (Count of mapped corporate entities)
  - `Market Direction` (Positive, Negative, Neutral)
  - `Market Moving` (Calibrated probability of generating abnormal volatility)
  - `Impact Strength` (Low, Medium, High, Very High)
  - `Risk` (Very Low to Very High)
- **Interactive Capabilities**: Free-text search across 6 fields, column sorting, categorical filters, and one-click "Inspect Bill" action redirecting to Bill Intelligence.

### 2.3 Bill Intelligence Deep Dive (`bill_detail.py`)
- **Primary Purpose**: End-to-end analytical dossier for a selected legislative enactment.
- **Sections**:
  1. **Legislative Metadata**: Sponsoring ministry, department, parliamentary bill number, introduction date, house, and lifecycle status.
  2. **Plain-English Summary**: Extracted from official source knowledge/metadata. If unavailable, strictly presents `"Summary not available."` without AI hallucination.
  3. **Key Areas**: Affected sectors, sub-industries, listed corporate participants, and policy domains.
  4. **Market Impact Forecast**: Predicted direction, calibrated probabilities ($P_{\text{pos}}, P_{\text{neg}}, P_{\text{neut}}$), market-moving likelihood, impact strength, model confidence tier, and continuous impact score. All probabilities preserved exactly as persisted.
  5. **Risk & Uncertainty**: Composite risk score, canonical risk category, confidence-related risk discount, tail-risk flags, and textual uncertainty explanation.
  6. **Anticipation & Pricing-In**: Pre-event diffusion classification (No Evidence, Weak, Moderate, Strong), mean anticipation score, and evidence summary.
     - *Mandatory Language Guard*: Never states "insider trading occurred." Uses academically defensible phrasing: *"Evidence suggests that relevant information may have been partially or fully priced in before formal introduction."*
     - *Mandatory Legal Notice*: *"Anticipation evidence is not proof of insider trading."*
  7. **Legislative Timeline**: Authoritative milestone progression (Introduction $\to$ Consideration $\to$ Passage $\to$ Assent) displaying only verified dates, with `"Date unavailable"` for missing stages.
  8. **Affected Company Cohort**: Filterable and sortable corporate exposure table (sortable by impact score, risk, confidence, or market-moving probability) with direct drill-down links to Company Detail.
  9. **Stakeholder Dossiers**: Tabbed selector for **Investor**, **Business / Corporate**, and **Public / Citizen** perspectives.

### 2.4 Company Intelligence Comparative Matrix (`companies.py`)
- **Primary Purpose**: Cross-sectional corporate exposure comparative matrix covering all 47 production BSE/NSE listed entities.
- **Metrics Computed per Company**:
  - Primary Sector & Sub-Industry
  - Number of Associated Legislative Bills
  - Positive, Negative, and Neutral Exposure Counts
  - Market-Moving Exposure Count ($P \ge 0.50$)
  - Average Impact Score & Average Risk Score
  - Strong Pre-Event Anticipation Exposure Count
- **Interactive Drilldown**: Direct selection and navigation to Company Detail.

### 2.5 Company Detail Exposure Breakdown (`company_detail.py`)
- **Primary Purpose**: Entity-specific legislative impact dossier.
- **Features**: Corporate profile (ISIN, Ticker, Sector, Industry), aggregate exposure statistics, complete table of associated bills with directional forecasts, and integrated synthesized company report dossier from `ReportRepository`.

### 2.6 Market Impact Predictions (`predictions.py`)
- **Primary Purpose**: High-level statistical visualization of the prediction universe.
- **Visualizations (Plotly)**:
  - Direction Distribution (Positive / Neutral / Negative donut chart)
  - Impact Strength Distribution (Low, Medium, High, Very High bar chart)
  - Model Confidence Distribution (Low, Medium, High bar chart)
  - Market-Moving Probability Distribution (Continuous histogram)
- **Controls**: Multi-dimensional filtering by bill, company, sector, direction, impact, and risk.

### 2.7 Risk Overview & 2D Matrix (`risk.py`)
- **Primary Purpose**: Empirical risk analysis across the 5 canonical tiers codified in Task 7.2 (`VERY_LOW`, `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`).
- **Displays**: Counts, percentages, average impact scores, and average confidence levels per tier.
- **2D Risk Matrix**: Scatter plot contrasting Impact Intensity vs Composite Risk Score.
- **Drilldowns**: Interactive bill and company isolation filters.

### 2.8 Anticipation & Pricing-In Analysis (`anticipation.py`)
- **Primary Purpose**: Econometric auditing of pre-event information diffusion ($T = -30$ to $-2$).
- **Features**: Evidence tier distributions (`NO_EVIDENCE`, `WEAK_EVIDENCE`, `MODERATE_EVIDENCE`, `STRONG_EVIDENCE`), theoretical breakdown of **The Anticipation Paradox**, searchable candidate pair table, and institutional disclaimers.

### 2.9 Historical Backtesting (`backtesting.py`)
- **Primary Purpose**: Retrospective performance auditing of walk-forward out-of-sample trading strategies (Task 6.4).
- **Critical Distinction**: Emphasizes that **Historical Backtesting** (retrospective out-of-sample simulation) is strictly isolated from **Forward Production Predictions** (live inference on 2024 bills).
- **Metrics**: Cumulative return, annualized Sharpe ratio, maximum drawdown, trade signals, hit rate, out-of-sample Macro F1, Balanced Accuracy, MCC, and ROC-AUC.
- **Charts**: Strategy vs Benchmark cumulative equity curves and drawdown timeseries.

### 2.10 Academic Methodology Blueprint (`methodology.py`)
- **Primary Purpose**: Comprehensive 18-stage academic blueprint covering every pipeline stage from Gazette ingestion to stakeholder synthesis.
- **Deep Dives**: Strict temporal separation, anti-lookahead guardrails, feature fusion, and the Anticipation Paradox.

---

## 3. End-to-End Analytical Workflow

The dashboard enables seamless hierarchical navigation across the entire intelligence lifecycle:

$$\begin{matrix}
\text{🆕 Newly Introduced Bills Feed} & \longrightarrow & \text{📜 All Bills Directory} \\
\downarrow & & \downarrow \\
\text{🔍 Bill Intelligence Dossier} & \longrightarrow & \text{🎯 Key Economic Sectors} \\
\downarrow & & \downarrow \\
\text{🏢 Affected Companies Cohort} & \longrightarrow & \text{🏢 Company Detail Profile} \\
\downarrow & & \downarrow \\
\text{📈 Market Impact Probabilities} & \longrightarrow & \text{⚠️ Risk & Uncertainty Profile} \\
\downarrow & & \downarrow \\
\text{🛡️ Pre-Event Anticipation Diffusion} & \longrightarrow & \text{👥 Multi-Stakeholder Interpretation}
\end{matrix}$$

---

## 4. Global Search Architecture

The sidebar features a universal bill search engine implemented via `DashboardService.search_bills(query)`.
- **Searchable Dimensions**: Bill title, parliamentary bill number, sponsoring ministry, department, economic sectors, bill category, and bill slug identifier.
- **Behavior**: Case-insensitive substring matching returning real-time hit summaries. Selecting a hit allows jumping directly to the bill's intelligence dossier via Streamlit session state navigation.

---

## 5. Stakeholder Views & Multi-Perspective Synthesis

Persisted qualitative dossiers from `ReportRepository` (`data/reports/`) are dynamically rendered for each bill:

| Stakeholder Lens | Focus Areas | Key Output Content |
|---|---|---|
| **💼 Investor** | Market impact, directional bias, portfolio risk | Calibrated direction probabilities, market-moving likelihood, impact magnitude, tail-risk flags, uncertainty discounts. |
| **🏢 Business / Corporate** | Regulatory compliance, operational headwinds | Ministerial jurisdiction, sector alignment, operational bottlenecks, capital expenditure implications. |
| **🌍 Public / Citizen** | Plain-English societal relevance | Non-technical bill summary, consumer and employment relevance, parliamentary sponsorship context. |

---

## 6. Data Scope Reconciliation & Empirical Source-of-Truth

### 6.1 The Discrepancy Investigated
During Task 7.4.1 runtime and testing discussions, an observation of **20 Bills, 10 Companies, 60 Pairs** (or 18 companies / 50 decision records in Task 7.3 runtime batches) was documented.

### 6.2 Empirical Audit Findings
A file-by-file audit of `data/` revealed the exact empirical provenance:
1. **Bills (22 master vs 20 production)**:
   - `data/bills/metadata/` contains 22 JSON files.
   - 20 files represent genuine Central Government legislative acts/bills introduced in Parliament during 2024.
   - 2 files (`key-issues-and-analysis.json` [PRS brief] and `service-bill.json` [test stub]) are non-legislative stubs and were excluded from ML feature engineering.
2. **Companies (50 master vs 47 production)**:
   - `data/companies/companies.json` contains 50 master companies.
   - 3 companies (`INE214G01026`, `INE155A01022`, `INE040A01034`) lacked necessary market model liquidity and were excluded during Task 4.x event study construction, leaving 47 production companies.
3. **10 Companies / 60 Pairs / 50 Records**:
   - In `data/mappings/`, sector-specific candidate mappings were built: Banking mapped 10 companies, Maritime shipping mapped 8 companies ($10 + 8 = 18$ companies).
   - In Task 7.3 runtime tests, pilot runs were executed across focused cohorts (e.g. Banking: 10 companies $\times$ 5 event windows = 50 decision records).
   - In preliminary dashboard prototyping, mapping subsets comprising 10 companies or 60 pairs were tested.
4. **Authoritative Production Scope**:
   - The production pipeline computed the full Cartesian product of all 20 active bills, 47 active companies, and 5 event windows:
     $$20 \text{ bills} \times 47 \text{ companies} = 940 \text{ pairs}$$
     $$940 \text{ pairs} \times 5 \text{ event windows} = 4,700 \text{ prediction and decision records}$$
   - **All 4,700 records exist verified on disk** in `data/predictions/` and `data/decision_support/`.
   - **14,100 stakeholder reports** exist verified on disk in `data/reports/` ($4,700 \times 3$).
   - **940 anticipation candidate scores** exist verified on disk in `data/anticipation/scores/`.

### 6.3 Authoritative Scope Table

| Entity / Dimension | Authoritative Production Count | Master Repo Count | Scope Resolution Status |
|---|---|---|---|
| **Legislative Bills** | **20** | 22 | 2 non-legislative stubs excluded |
| **Mapped Companies** | **47** | 50 | 3 illiquid companies excluded |
| **Event Windows** | **5** | 5 | `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]` |
| **Candidate Pairs** | **940** | 940 | $20 \times 47$ |
| **Prediction Records** | **4,700** | 4,700 | Full universe verified |
| **Decision-Support Records** | **4,700** | 4,700 | Full universe verified |
| **Anticipation Scores** | **940** | 940 | Full universe verified |
| **Stakeholder Reports** | **14,100** | 14,100 | $4,700 \times 3$ verified |
| **Integrity Verdict** | **PRODUCTION_FULL_PARITY** | — | Verified on disk |

---

## 7. Research Integrity & Non-Leakage Guarantees

1. **Zero Dynamic Retraining**: The dashboard operates exclusively as a presentation consumer. Models are never retrained or modified from the UI.
2. **Probability Preservation**: Stored probabilities ($P_{\text{pos}}, P_{\text{neg}}, P_{\text{neut}}$) and impact scores are displayed exactly as stored.
3. **Strict Temporal Isolation**: Predictive features are restricted strictly to pre-event information ($\mathcal{F}_{T \le 0}$). Future price action is never used in prediction views.
4. **Anticipation Guardrails**: Anticipation is framed strictly as statistical pre-event market drift and informational diffusion. Explicit disclaimers prohibit interpreting drift as insider trading.
5. **Backtest Isolation**: Historical backtesting simulations are visually and conceptually separated from forward-looking live predictions.

---

---

## 8. Running the Dashboard & Verification

### Launch
```bash
streamlit run dashboard/app.py
```

### Automated Test Verification
```bash
# Run Task 7.4.3 QA & Research-Integrity test suite
pytest tests/test_dashboard_qa.py -v

# Run full dashboard test suite (138 tests)
pytest tests/test_dashboard_qa.py tests/test_dashboard_v2.py tests/test_dashboard_service.py \
       tests/test_dashboard_components.py tests/test_dashboard_filters.py tests/test_dashboard_pages.py \
       tests/test_dashboard_scope.py tests/test_dashboard_charts.py tests/test_dashboard_services.py -v
```

---

## 9. Task 7.4.3 — UX, Runtime QA & Research-Integrity Hardening

### 9.1 Newly Introduced Bill Definition & Date Logic
- **Authoritative Date Invariant**: Bill recency is determined strictly by `Bill.introduction_date` (the official parliamentary tabling date).
- **Prohibited Timestamps**: PDF download date, metadata file creation date, text embedding timestamp, and prediction execution timestamp are strictly forbidden from determining recency.
- **Filter Coverage**: Validated across 7-day, 30-day, 90-day, custom calendar intervals, and empty/no-results states.

### 9.2 Bill Classification & Provenance Quality
- **Official vs System-Derived Distinction**: The UI explicitly differentiates:
  - `Official Parliamentary Classification`: Authoritative PRS / Parliament metadata (e.g., *Government Bill (PRS Source)*).
  - `System-Derived Policy Category`: Heuristic mapping based on sponsoring ministry and NLP bill provisions (e.g., *System-derived category: Financial / Banking*).
- **No False Authority**: Heuristic sector categories are never presented as official parliamentary acts of classification.

### 9.3 Legislative Status Integrity
- **Ungrounded Inference Prohibition**: The system never infers or guesses `Passed`, `Assented`, `Withdrawn`, or `Lapsed` without explicit source verification.
- **Missing Data Fallback**: When status metadata is absent or empty, the UI displays `"Status not available."`.

### 9.4 Probabilistic Language & Non-Advisory Safety
- **Definitive Claims Banned**: Zero occurrences of `"will increase"`, `"will decrease"`, `"guaranteed return"`, or `"guaranteed profit"`.
- **Probabilistic Phrasing**: Model estimates are labeled with explicit confidence bounds, e.g. *"model estimates"*, *"predicted probability"*, *"potential market impact"*.
- **Investment Advice Safety**: The platform strictly prohibits buy/sell directives or personalized investment advice. All financial visualizations feature academic research disclaimers.

### 9.5 Anticipation Language & Academic Compliance
- **Zero Insider Accusations**: Terminology such as *"insider trading occurred"* or *"insiders traded"* is strictly prohibited.
- **Mandatory Compliance Disclaimer**: Every anticipation and methodology view displays:
  > *"Anticipation evidence is not proof of insider trading. It reflects observable pre-event market information diffusion and institutional pricing-in."*

### 9.6 Ground-Truth & Backtesting Isolation
- **No Ground-Truth Leakage**: Realized post-event market returns, actual CAR values, and ex-post direction labels are never loaded into prediction inputs or displayed in forward prediction dossiers.
- **Historical Backtesting Boundaries**: Walk-forward historical backtests are clearly separated from live forward predictions to eliminate lookahead confusion.

### 9.7 Bitwise Artifact Immutability
- SHA256 bitwise hashing before and after runtime interaction validates that `data/predictions/`, `data/decision_support/`, `data/anticipation/`, `data/backtests/`, and `data/reports/` remain 100% immutable during dashboard operations.

