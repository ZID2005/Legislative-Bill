# Data Provenance Document
## Legislative Intelligence & Market Impact Prediction System for Indian Central Government Bills

**Version:** 1.0
**Prepared For:** Task 8.1 - Final Academic Validation Phase
**Audit Date:** 2026-09-06
**Production Scope:** 20 Bills x 47 Companies x 5 Windows = 4,700 Records

---

## 1. Purpose

This document records the complete data provenance, source traceability, and lineage of all information used in the Legislative Intelligence & Market Impact Prediction System. It covers the full pipeline from raw legislative data to published stakeholder reports and the interactive dashboard, establishing the ground-truth boundary, temporal boundaries, and known exclusions in a manner suitable for academic audit and reproduction.

---

## 2. Legislative Data Sources

| Property | Value |
|----------|-------|
| **Primary Source** | PRS Legislative Research (India) - `https://prsindia.org` |
| **Source Type** | Public-domain parliamentary bill tracking and analysis portal |
| **Data Access Method** | Web scraping via ingestion module (`ingestion/parliament/`) |
| **Bills Covered** | 20 Central Government Bills introduced in 2024 (18th Lok Sabha session) |
| **Coverage Period** | February 2024 - August 2024 (introduction dates range) |
| **Secondary Sources** | Lok Sabha secretariat official records (corroborated), Ministry websites |
| **Ingestion Module** | `ingestion/parliament/` |

---

## 3. Bill Metadata

### 3.1 Metadata Schema

Bill metadata is stored at two levels:

| File Location | Purpose |
|---------------|---------|
| `data/bills/metadata/<bill-id>.json` | Full legislative record (dates, house, status, PDF URL, text) |
| `data/mappings/<bill-id>.json` | Sector/industry mapping and candidate company list |

**Metadata Fields (in `data/bills/metadata/`):**

`bill_id`, `title`, `bill_number`, `year`, `ministry`, `house`, `status`, `introduction_date`, `assent_date`, `gazette_date`, `last_updated`, `url`, `pdf_url`, `pdf_path`, `document_path`, `document_size`, `document_checksum`, `download_timestamp`, `download_status`, `summary`, `full_text`, `session`, `sponsor`, `related_bills`, `related_acts`, `language`, `sectors`, `keywords`, `source`, `ingested_at`, `text_path`, `text_checksum`, `text_size`, `text_status`, `extraction_method`, `extraction_timestamp`, `page_count`, `quality_metrics`

### 3.2 Production Bill Registry (20 Bills)

| # | Bill ID | Title | Intro Date | Ministry | Status |
|---|---------|-------|-----------|----------|--------|
| 1 | `the-banking-laws-amendment-bill-2024` | The Banking Laws (Amendment) Bill, 2024 | 2024-08-09 | Finance | passed_both |
| 2 | `the-bharatiya-vayuyan-vidheyak-2024` | The Bharatiya Vayuyan Vidheyak, 2024 | 2024-07-22 | Civil Aviation | passed_both |
| 3 | `the-bills-of-lading-bill-2024` | The Bills of Lading Bill, 2024 | 2024-08-09 | Shipping | passed_both |
| 4 | `the-boilers-bill-2024` | The Boilers Bill, 2024 | 2024-08-09 | Commerce & Industry | passed_both |
| 5 | `the-carriage-of-goods-by-sea-bill-2024` | The Carriage of Goods by Sea Bill, 2024 | 2024-08-09 | Shipping | passed_both |
| 6 | `the-coastal-shipping-bill-2024` | The Coastal Shipping Bill, 2024 | 2024-08-09 | Shipping | passed_both |
| 7 | `the-constitution-129th-amendment-bill-2024-...` | The Constitution (129th Amendment) Bill, 2024 [One Nation One Election] | 2024-07-22 | Law and Justice | in_committee |
| 8 | `the-constitution-scheduled-castes-and-...` | The Constitution (SC and ST Orders Amendment) Bill, 2024 | 2024-08-05 | Tribal Affairs | passed_both |
| 9 | `the-constitution-scheduled-tribes-order-amendment-bill-2024` | The Constitution (Scheduled Tribes Order Amendment) Bill, 2024 | 2024-08-05 | Tribal Affairs | passed_both |
| 10 | `the-disaster-management-amendment-bill-2024` | The Disaster Management (Amendment) Bill, 2024 | 2024-08-01 | Home Affairs | passed_both |
| 11 | `the-jammu-and-kashmir-local-bodies-laws-amendment-bill-2024` | The J&K Local Bodies Laws Amendment Bill, 2024 | 2024-08-05 | Home Affairs | passed_both |
| 12 | `the-merchant-shipping-bill-2024` | The Merchant Shipping Bill, 2024 | 2024-08-09 | Shipping | passed_both |
| 13 | `the-mussalman-wakf-repeal-bill-2024` | The Mussalman Wakf (Repeal) Bill, 2024 | 2024-08-05 | Minority Affairs | passed_both |
| 14 | `the-oilfields-regulation-and-development-amendment-bill-2024` | The Oilfields (Regulation and Development) Amendment Bill, 2024 | 2024-08-05 | Petroleum and Natural Gas | passed_both |
| 15 | `the-public-examinations-prevention-of-unfair-means-bill-2024` | The Public Examinations (Prevention of Unfair Means) Bill, 2024 | 2024-02-05 | Personnel | passed_both |
| 16 | `the-railways-amendment-bill-2024` | The Railways (Amendment) Bill, 2024 | 2024-08-09 | Railways | passed_both |
| 17 | `the-readjustment-of-representation-of-...` | The Readjustment of Representation of Scheduled Tribes in Assembly Constituencies of Goa Bill, 2024 | 2024-08-05 | Law and Justice | passed_both |
| 18 | `the-union-territories-laws-amendment-bill-2024-...` | The Union Territories Laws (Amendment) Bill, 2024 [One Nation One Election] | 2024-07-22 | Law and Justice | in_committee |
| 19 | `the-waqf-amendment-bill-2024` | The Waqf (Amendment) Bill, 2024 | 2024-07-22 | Minority Affairs | passed_both |
| 20 | `the-water-prevention-and-control-of-pollution-amendment-bill-2024` | The Water (Prevention and Control of Pollution) Amendment Bill, 2024 | 2024-02-05 | Environment | passed_both |

> **Note on House field:** The `house` field is recorded as `unknown` for 19 of 20 bills in the metadata store (only `the-banking-laws-amendment-bill-2024` records `lok_sabha`). This is a known metadata gap from the PRS scraper and does not affect any downstream prediction, decision, or reporting logic.

### 3.3 Auxiliary / Stub Records (excluded from production)

| File | Bill ID | Reason for Exclusion |
|------|---------|---------------------|
| `key-issues-and-analysis.json` | `key-issues-and-analysis` | PRS commentary/analysis document, not a parliamentary bill. `introduction_date = null`, `house = unknown`, `status = draft`, URL points to 2024 draft telecom rules commentary. Category: C (Auxiliary) |
| `service-bill.json` | `service-bill` | Synthetic system-test placeholder. `title = "Service Bill 2026"` (2026 is outside production scope), `introduction_date = null`, `source = unknown`, `url = https://example.com/bill`. Category: E (Non-production) |

---

## 4. Bill Text/PDF

| Property | Value |
|----------|-------|
| **Storage Location** | `data/bills/documents/2024/<bill-id>.pdf` |
| **Format** | PDF (original PRS / Lok Sabha download) |
| **Download Status** | All 20 production bills: `download_status = success` |
| **Text Extraction** | `text_status = success` for all 20 production bills |
| **Corpus Storage** | `data/bills/corpus/` (processed text) |
| **Knowledge Extraction** | `data/bills/knowledge/<bill-id>.json` (22 files: 20 production + 2 stubs) |

One additional PDF in `data/bills/pdfs/`: `code-on-wages-central-rules-2026.pdf` - reference document, not part of the 20 production bills.

---

## 5. Company Universe

### 5.1 Source

| Property | Value |
|----------|-------|
| **Storage** | `data/companies/companies.json` |
| **Total records** | 50 (47 production + 3 excluded) |
| **Exchange** | NSE (National Stock Exchange of India) and BSE |
| **Index Universe** | Nifty 50 and related large/mid-cap liquid securities |
| **Eligibility Criterion** | Continuous price data covering the full estimation window |

### 5.2 Production Company Universe (47 companies)

| ISIN | Company Name | Sector |
|------|-------------|--------|
| INE002A01018 | Reliance Industries Limited | Energy |
| INE003A01024 | Siemens Limited | Manufacturing |
| INE009A01021 | Infosys Limited | Technology |
| INE00LIC01010 | Life Insurance Corporation of India | Banking and Financial Services |
| INE018A01030 | Larsen and Toubro Limited | Infrastructure |
| INE019A01030 | JSW Steel Limited | Metals and Mining |
| INE021A01026 | Asian Paints Limited | Consumer Goods and FMCG |
| INE030A01027 | Hindustan Unilever Limited | Consumer Goods and FMCG |
| INE038A01020 | Hindalco Industries Limited | Metals and Mining |
| INE044A01045 | Sun Pharmaceutical Industries Limited | Healthcare and Pharmaceuticals |
| INE047A01021 | Grasim Industries Limited | Manufacturing |
| INE059A01026 | Cipla Limited | Healthcare and Pharmaceuticals |
| INE062A01020 | State Bank of India | Banking and Financial Services |
| INE066A01021 | Eicher Motors Limited | Manufacturing |
| INE075A01022 | Wipro Limited | Technology |
| INE081A01020 | Tata Steel Limited | Metals and Mining |
| INE089A01023 | Dr. Reddy's Laboratories Limited | Healthcare and Pharmaceuticals |
| INE090A01021 | ICICI Bank Limited | Banking and Financial Services |
| INE101A01026 | Mahindra and Mahindra Limited | Manufacturing |
| INE117A01022 | ABB India Limited | Manufacturing |
| INE123W01016 | SBI Life Insurance Company Limited | Banking and Financial Services |
| INE154A01025 | ITC Limited | Consumer Goods and FMCG |
| INE158A01026 | Hero Motocorp Limited | Manufacturing |
| INE192A01025 | Tata Consumer Products Limited | Consumer Goods and FMCG |
| INE213A01029 | Oil and Natural Gas Corporation Limited | Energy |
| INE216A01030 | Britannia Industries Limited | Consumer Goods and FMCG |
| INE237A01028 | Kotak Mahindra Bank Limited | Banking and Financial Services |
| INE238A01034 | Axis Bank Limited | Banking and Financial Services |
| INE239A01016 | Nestle India Limited | Consumer Goods and FMCG |
| INE245A01021 | Tata Power Company Limited | Energy |
| INE296A01024 | Bajaj Finance Limited | Banking and Financial Services |
| INE364U01010 | Adani Green Energy Limited | Energy |
| INE397D01024 | Bharti Airtel Limited | Telecommunications |
| INE423A01024 | Adani Enterprises Limited | Infrastructure |
| INE437A01024 | Apollo Hospitals Enterprise Limited | Healthcare and Pharmaceuticals |
| INE467B01029 | Tata Consultancy Services Limited | Technology |
| INE481G01011 | Ultratech Cement Limited | Infrastructure |
| INE522F01014 | Coal India Limited | Metals and Mining |
| INE585B01010 | Maruti Suzuki India Limited | Manufacturing |
| INE669C01036 | Tech Mahindra Limited | Technology |
| INE733E01010 | NTPC Limited | Energy |
| INE752E01010 | Power Grid Corporation of India Limited | Energy |
| INE795G01014 | HDFC Life Insurance Company Limited | Banking and Financial Services |
| INE814H01011 | Adani Power Limited | Energy |
| INE860A01027 | HCL Technologies Limited | Technology |
| INE917I01010 | Bajaj Auto Limited | Manufacturing |
| INE918I01018 | Bajaj Finserv Limited | Banking and Financial Services |

### 5.3 Excluded Securities (3 companies)

| ISIN | Company | Reason |
|------|---------|--------|
| INE040A01034 | HDFC Bank Limited | Incomplete market data: `ticker_nse = ""`, `ticker_bse = ""`, `bse_code = ""`, `market_cap_cr = None`. Missing ticker prevents price history retrieval. |
| INE155A01022 | Tata Motors Limited | `listing_date = None` - insufficient continuous pre-event trading history for estimation window computation. |
| INE214G01026 | LTIMindtree Limited | `listing_date = None` - post-merger entity (L&T Infotech + Mindtree); insufficient continuous history for estimation window. |

All 3 excluded ISINs are `is_active = True` and `listing_status = Listed` but are excluded due to liquidity/trading-history ineligibility (the canonical exclusion rule applied uniformly).

---

## 6. Market Data

| Property | Value |
|----------|-------|
| **Source** | Yahoo Finance API (yfinance library) |
| **Benchmark** | Nifty 50 Index (^NSEI) |
| **Data Type** | Daily adjusted closing prices (OHLCV) |
| **Storage** | `data/market/` (raw), `data/market_models/` (OLS parameters) |
| **Frequency** | NSE trading days |

---

## 7. Event Study Data

| Property | Value |
|----------|-------|
| **Storage** | `data/event_studies/<bill-id>_<isin>_<window>.json` |
| **Count** | 4,700 (20 bills x 47 companies x 5 windows) |
| **Window Format in filename** | `m<pre>,p<post>` (e.g., `m1,p1` = [-1,+1]) |
| **Content** | Cumulative Abnormal Return (CAR), t-statistic, p-value, abnormal returns by day |
| **Market Model** | OLS estimation of alpha/beta from pre-event estimation window |
| **Benchmark** | Nifty 50 Index (^NSEI) |
| **Responsible Module** | `services/market_model_service.py`, `labeling/label_generator.py` |

---

## 8. NLP / Embedding Data

| Property | Value |
|----------|-------|
| **Storage** | `data/embeddings/` |
| **Knowledge Layer** | `data/bills/knowledge/<bill-id>.json` (22 files, 20 production) |
| **Legislative NLP** | Legal transformer embedding engine (`embeddings/`) |
| **Financial NLP** | FinBERT domain embedding engine (`embeddings/`) |
| **Feature Fusion** | `data/fused/` |
| **Text Input** | Extracted bill PDF text from `data/bills/corpus/` |

---

## 9. Ground Truth

### 9.1 Ground Truth Definition

Ground truth consists of realized market outcomes computed from actual post-event market price data via the event study pipeline.

Ground truth fields:

| Field | Type | Description |
|-------|------|-------------|
| `car` | float | Cumulative Abnormal Return over the event window |
| `p_value` | float | Statistical significance of CAR |
| `direction` | enum | POSITIVE / NEUTRAL / NEGATIVE |
| `market_moving` | bool | True if significant AND absolute CAR > threshold |
| `impact_strength` | enum | LOW / MEDIUM / HIGH / VERY_HIGH |
| `confidence` | enum | LOW / MEDIUM / HIGH |

### 9.2 Ground Truth Storage

| Property | Value |
|----------|-------|
| **Storage** | `data/labels/<bill-id>_<isin>_<window>.json` |
| **Count** | 4,700 label records |
| **Responsible Module** | `labeling/label_generator.py` |
| **Schema** | `schemas/label.py` |

### 9.3 Usage of Ground Truth

Ground truth IS used for:
- Model training (target variables for all 4 classifiers)
- Model evaluation and cross-validation (`evaluation/`)
- Walk-forward backtesting (`backtesting/`)

Ground truth IS NOT used as:
- Any input feature in live/forward prediction
- Any input to the prediction engine at inference time
- Any input to the decision support engine
- Any input to the anticipation analysis

Verification: Inspection of all 4,700 prediction records confirms the absence of ground truth fields (`car`, `realized_return`, `direction_label`, `market_moving` (as GT), `impact_strength` (as GT), `confidence_label`).

---

## 10. Feature Dataset

| Property | Value |
|----------|-------|
| **Storage** | `data/features/master_feature_dataset.parquet` (320 KB), `data/features/master_feature_dataset.csv` (4.16 MB), `data/features/index.json` (361 KB) |
| **Content** | Structured tabular features: bill characteristics, company financials, market statistics, pre-event market signals, NLP-derived scores |
| **Temporal Rule** | Only pre-event features are used in prediction (see Section 17) |
| **Responsible Module** | `features/` |

---

## 11. Prediction Artifacts

| Property | Value |
|----------|-------|
| **Storage** | `data/predictions/pred_<bill-id>_<isin>_<window>.json` |
| **Count** | 4,700 production records |
| **Audit Summary** | `data/predictions/runtime_audit_summary.json` (auxiliary, not a prediction record) |
| **Naming** | `pred_<bill-id>_<isin>_-<pre>_p<post>.json` |
| **Key Fields** | prediction_id, bill_id, company_isin, event_window, predicted_direction, direction_probability, predicted_market_moving, predicted_impact_strength, predicted_confidence, anticipation_score, model_name, model_version, feature_version, prediction_timestamp, data_quality_status |
| **Models** | LightGBM (direction, impact, confidence), Random Forest (market_moving) |
| **Model Version** | v1.0 (100% of records) |
| **Data Quality** | VALID for all 4,700 records; 0 imputed |
| **Duplicate IDs** | 0 |
| **Responsible Module** | `prediction/` |

---

## 12. Decision Support

| Property | Value |
|----------|-------|
| **Storage** | `data/decision_support/dec_<bill-id>_<isin>_<window>.json` |
| **Count** | 4,700 records |
| **Relationship** | One-to-one with predictions |
| **Decision ID** | `dec_<bill-id>_<isin>_-<pre>_p<post>` |
| **Key Fields** | decision_id, bill_id, company_isin, event_window, predicted_direction, confidence_score, anticipation_score, impact_score, risk_score, risk_category, pricing_in_risk, investor_summary, business_summary, public_summary, decision_reason, decision_version, generation_timestamp, data_quality_status |
| **Decision Version** | v1.0 |
| **Responsible Module** | `decision_support/` |

---

## 13. Anticipation

| Property | Value |
|----------|-------|
| **Storage** | `data/anticipation/scores/<bill-id>_<isin>.json` |
| **Count** | 940 records (20 bills x 47 companies; window-independent) |
| **Purpose** | Pre-event market signal detection; diagnostic analysis of possible information leakage |
| **Key Fields** | bill_id, company_isin, official_introduction_date, market_signal_score, information_signal_score, anticipation_score, classification, anticipation_flag, confidence, evidence_count, detected_signals, calculation_timestamp |
| **Pre-Event Windows Used** | [-30,-21], [-20,-11], [-10,-6], [-5,-3], [-2,-1], cumulative [-30,-1] |
| **Classification** | STRONG_EVIDENCE / MODERATE_EVIDENCE / WEAK_EVIDENCE / NO_EVIDENCE |
| **Ground Truth Independence** | Uses only pre-event market data; post-event outcomes not used |
| **Usage in Prediction** | anticipation_score and anticipation_class are pre-event features; compliant with temporal boundary |
| **Responsible Module** | `anticipation/` |

---

## 14. Stakeholder Reports

| Property | Value |
|----------|-------|
| **Storage** | `data/reports/investor/*.json` (4,700), `data/reports/business/*.json` (4,700), `data/reports/public/*.json` (4,700) |
| **Total Count** | 14,100 canonical stakeholder reports |
| **Validation Records** | `data/reports/validation/` (14,100 validation JSONs) |
| **Bill Summary Reports** | `data/reports/bill_reports/` (22 files) |
| **Company Summary Reports** | `data/reports/company_reports/` (47 files) |
| **Perspectives** | Investor, Business/Corporate, Public |
| **Relationship** | 3 reports per prediction/decision record |
| **Responsible Module** | `reporting/` |

---

## 15. Dashboard

| Property | Value |
|----------|-------|
| **Framework** | Streamlit |
| **Module** | `dashboard/` |
| **Data Sources** | All production artifacts in `data/` (read-only) |
| **Tests** | 138 dedicated dashboard tests (100% passed, Task 7.5 audit) |
| **Loading** | Cold-start: 7.18 ms (Task 7.5 benchmark) |

---

## 16. Identifier / Data Lineage

| Stage | Primary Identifier | Format |
|-------|------------------|--------|
| Bill | `bill_id` | slug string |
| Company | `isin` | 12-char ISIN |
| Event Study / Label | `bill_id` + `isin` + `event_window` | compound |
| Anticipation | `bill_id` + `isin` | compound (no window dimension) |
| Prediction | `prediction_id` | `pred_<bill-id>_<isin>_-<pre>_p<post>` |
| Decision | `decision_id` | `dec_<bill-id>_<isin>_-<pre>_p<post>` |
| Stakeholder Report | `report_id` | embedded in JSON record |

Full Lineage Trace:

```
bill_id
    -> data/bills/metadata/<bill-id>.json        [bill metadata]
    -> data/bills/documents/2024/<bill-id>.pdf   [full text PDF]
    -> data/bills/knowledge/<bill-id>.json       [knowledge layer]
    -> data/mappings/<bill-id>.json              [sector/company mapping]

bill_id x isin
    -> data/market/<isin>/                       [market price data]
    -> data/market_models/<bill-id>_<isin>.json  [OLS market model]
    -> data/anticipation/scores/<bill-id>_<isin>.json  [anticipation]

bill_id x isin x event_window
    -> data/event_studies/<bill-id>_<isin>_<window>.json  [event study]
    -> data/labels/<bill-id>_<isin>_<window>.json         [ground truth]
    -> data/features/master_feature_dataset.*             [feature matrix]
    -> data/predictions/pred_<bill-id>_<isin>_<window>.json  [prediction]
    -> data/decision_support/dec_<bill-id>_<isin>_<window>.json  [decision]
    -> data/reports/investor/<...>.json    [investor report]
    -> data/reports/business/<...>.json    [business report]
    -> data/reports/public/<...>.json      [public report]
```

---

## 17. Temporal Boundaries

### 17.1 Estimation Window

The market model (OLS alpha/beta) is estimated from pre-event trading data, ending before the event window begins.

| Component | Period |
|-----------|--------|
| Estimation window start | approximately T0 - 130 trading days |
| Estimation window end | T0 - 11 trading days (before longest event window) |
| Schema | `MarketModelRecord.estimation_window = {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}` |

### 17.2 Event Windows (5 canonical)

| Window | Pre-Event | Post-Event | Filename Suffix |
|--------|-----------|-----------|-----------------|
| [-1,+1] | 1 day before | 1 day after | `_-1_p1` |
| [-3,+3] | 3 days before | 3 days after | `_-3_p3` |
| [-5,+5] | 5 days before | 5 days after | `_-5_p5` |
| [-5,+10] | 5 days before | 10 days after | `_-5_p10` |
| [-10,+10] | 10 days before | 10 days after | `_-10_p10` |

### 17.3 Prediction Information Cutoff (T0)

Allowed features (pre-T0): Bill text features, pre-event market statistics, company financials, sector characteristics, anticipation scores (computed from pre-event [-30,-1] data), legislative knowledge layer.

Not allowed (post-T0): Post-event realized returns, CAR, ground truth labels.

Verification: Schema inspection of all 4,700 prediction records confirms absence of: `car`, `realized_return`, `direction_label`, ground-truth `market_moving`, ground-truth `impact_strength`, `confidence_label`.

### 17.4 Ground Truth Calculation Period

Ground truth labels are computed over the full event window (pre + post) and stored separately in `data/labels/`. They are never passed to prediction or decision engines.

### 17.5 Anticipation Analysis Temporal Boundary

Anticipation uses only the pre-event window [-30,-1] relative to T0:
- Sub-windows (per `settings.ANTICIPATION_WINDOWS`): [-30,-21], [-20,-11], [-10,-6], [-5,-3], [-2,-1]
- Cumulative window (per `settings.ANTICIPATION_CUMULATIVE_WINDOW`): [-30,-1]

---

## 18. Ground Truth Boundaries

### 18.1 Boundary Definition

```
+----------------------------------------------------------+
|                  GROUND TRUTH REGIME                     |
|  Historical: all 20 bills have realized market data     |
|                                                          |
|  data/labels/ -- 4,700 label records                    |
|  Used for: Training, Evaluation, Backtesting            |
|  NOT used for: Live prediction features                 |
+----------------------------------------------------------+
                          |
                    T0 (Event Date = Bill Introduction Date)
                          |
+----------------------------------------------------------+
|                PREDICTION REGIME                         |
|  Forward-looking: uses only pre-T0 information          |
|                                                          |
|  data/predictions/ -- 4,700 prediction records          |
|  NOT PRESENT in records: car, realized_return,          |
|  direction_label (GT), market_moving (GT),              |
|  impact_strength (GT), confidence_label                 |
+----------------------------------------------------------+
```

### 18.2 Anti-Leakage Compliance

- Ground truth fields are absent from all 4,700 prediction records (schema-verified)
- Prediction engine reads from `data/features/` and `data/anticipation/scores/`, not from `data/labels/`
- Decision support reads from `data/predictions/`, not from `data/labels/`
- Backtesting uses walk-forward temporal split (training folds chronologically precede test folds)

---

## 19. Production Scope

| Metric | Count | Status |
|--------|-------|--------|
| Central Government Bills | 20 | VERIFIED |
| Production Companies | 47 | VERIFIED |
| Bill-Company Pairs | 940 | VERIFIED |
| Event Windows | 5 | VERIFIED |
| Prediction Records | 4,700 | VERIFIED |
| Decision Support Records | 4,700 | VERIFIED |
| Anticipation Records | 940 | VERIFIED |
| Stakeholder Reports (3 x 4,700) | 14,100 | VERIFIED |
| Ground Truth Labels | 4,700 | VERIFIED |
| Event Study Records | 4,700 | VERIFIED |

---

## 20. Known Exclusions

### 20.1 Excluded Mapping/Metadata Records

| Record | Classification | Reason |
|--------|----------------|--------|
| `key-issues-and-analysis` | C (Auxiliary) | PRS commentary document; no introduction date; not a parliamentary bill |
| `service-bill` | E (Non-production) | System test placeholder; year 2026; no introduction date; synthetic URL |

### 20.2 Excluded Companies

| ISIN | Company | Classification | Reason |
|------|---------|----------------|--------|
| INE040A01034 | HDFC Bank Limited | E (Non-production) | Missing ticker/BSE code; no market cap data; insufficient trading history coverage |
| INE155A01022 | Tata Motors Limited | E (Non-production) | `listing_date = None`; insufficient continuous trading history for estimation window |
| INE214G01026 | LTIMindtree Limited | E (Non-production) | `listing_date = None`; post-merger entity; insufficient continuous history |

### 20.3 Extra File in Predictions Directory

| File | Classification | Reason |
|------|----------------|--------|
| `data/predictions/runtime_audit_summary.json` | C (Auxiliary) | System-generated audit summary file; not a prediction record. Its own `total_records_on_disk = 4700` confirms the production count. |

---

*Document generated: 2026-09-06 | Task 8.1 - Final Academic Validation Phase*
