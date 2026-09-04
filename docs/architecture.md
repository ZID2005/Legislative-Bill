# Architecture

## Overview

The Legislative Intelligence & Market Impact Prediction System follows a
**layered pipeline architecture**, managed by a centralized **Service Layer** that coordinates business logic and orchestrates workflows across underlying domains.

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation Layer  (main.py / dashboard.py)                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │  Requests
┌────────────────────────────────▼────────────────────────────────┐
│  Service Layer  (services/)                                     │
│  Orchestrates workflows & injects domain models / repositories │
└──────┬─────────────────────────┬─────────────────────────┬──────┘
       │ Ingestion Flows         │ Predictions             │ Explanations (LLM)
┌──────▼──────────────────┐┌─────▼───────────┐┌────────────▼──────┐
│ Ingestion Layer         ││ Inference Layer ││ Explanation Layer │
│ ingestion/              ││ models/         ││ services/         │
└──────┬──────────────────┘└─────┬───────────┘└────────────┬──────┘
       │ Reads/Writes            │ Reads/Writes            │ Reads/Writes
┌──────▼─────────────────────────▼─────────────────────────▼──────┐
│ Data / Persistence Layer (storage/ repositories)                │
└─────────────────────────────────────────────────────────────────┘
```

## Service Layer (Coordination Facade)

The root-level `services/` package defines the orchestration facade for the platform. By utilizing Dependency Injection and Loose Coupling, it ensures presentation layers (CLI, Streamlit dashboards) never reach directly into deep parser, connector, or feature-engineering implementations.

Key services defined:
1. **`IngestionService`**: A single point of coordination for parliament bills, company masters, and stock price histories. Delegates parliament workflows to `ParliamentIngestionService` and triggers validation and catalog indexing.
2. **`PredictionService`**: Handles feature extraction and triggers ML models (LightGBM/FinBERT) to evaluate market impact on public companies.
3. **`ExplanationService`**: Uses a pluggable abstract `LLMProvider` interface to generate plain-language bill summaries, market event explanations, and power conversational QA bots. This serves as the primary extension point where **Groq** will later integrate.
4. **`MarketModelService`**: Coordinates the estimation of expected stock returns using the classical OLS market model baseline parameters.
5. **`EventStudyService`**: Implements the Advanced Event Study Engine to compute expected returns, observed actual returns, Daily Abnormal Returns (AR), Running CAR, and Final CAR across multiple configurable event windows. Also calculates summary quality metrics.
6. **`StatisticalSignificanceService`**: Orchestrates hypothesis testing on Event Study CARs, calculating p-values, t-statistics, 95% confidence intervals, and effect sizes. Integrates with `StatisticalValidator` to ensure mathematical sanity and manages caching and incremental runs via `StatisticalRepository`.

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Each module does exactly one job |
| **Dependency Direction** | Data flows top → bottom; no layer imports a higher layer |
| **No Hardcoded Values** | All paths and secrets come from `config/settings.py` |
| **Schema Contracts** | Each layer's output has a defined schema |
| **Fail-Fast Validation** | Invalid data is rejected early (Layer 2) |
| **Observability** | All layers log via `config/logging_config.py` |
| **Testability** | All modules are independently importable and testable |

## How Ingestion Works
The Legislative Data Ingestion Service runs a robust, step-by-step pipeline:
1. **Discovery (`discovery.py`)**: Locates available bills from portal RSS feeds or HTML tables based on configured criteria (e.g. year, latest). Returns lightweight records (title, URL, status, year).
2. **Metadata Collection — Task 1A.2 (`parse_html_details()`)**: Visits each bill's detail page and extracts structured metadata: ministry, bill number, house, introduction date, session, sponsor, official summary, PDF URL (link only), related bills, related acts, and last-updated date. If a field is unavailable on the page, it is stored as NULL — values are never invented.
3. **Normalize (`normalizer.py`)**: Transforms the raw attribute dict to a canonical `Bill` schema model. Dates become `datetime.date` objects, house and status are mapped to typed enums, and new fields (session, sponsor, related_bills, related_acts, pdf_url, language, last_updated) are populated.
4. **Validate (`validation/validator.py`)**: Screens the normalized object for malformed URLs, out-of-range dates, missing required fields, or empty titles. Year and ministry are optional — their absence produces a warning, not an error. Produces a detailed `ValidationReport`.
5. **Duplicate Detection**: The service checks the repository to determine if the bill is a new insert, a modified record requiring an update, or a duplicate to skip.
6. **Persistence**: Saves verified bills to disk as JSON files under `data/bills/metadata/<bill_id>.json` via the `BillRepository`.
7. **Document Collection — Task 1A.3 (`downloader.py`)**: Initiated via the `download-docs` command. The downloader queries all saved metadata records with a valid `pdf_url`, fetches the binary PDF content using streaming HTTP chunk writing, performs semantic integrity checks, and updates document auditing attributes on the bill record.

## Document Collection Workflow (Task 1A.3)

### Checksum Strategy
To ensure data integrity and avoid duplicate downloads, every completed file is hashed using **SHA-256**. The checksum is stored in `document_checksum` on the `Bill` record. On subsequent synchronization passes, files existing on disk are re-hashed. If the computed hash matches the stored `document_checksum`, the download is skipped.

### Resume Strategy
To support large documents and tolerate network interruptions, the downloader enforces **HTTP Range requests**.
- If a download is interrupted, a partial file is left on disk.
- On the next execution, the downloader checks if a partial file exists and reads its size (`start_byte`).
- The downloader requests only the remaining bytes by setting the HTTP `Range: bytes={start_byte}-` header.
- If the server responds with status `206 Partial Content`, chunks are appended to the file. If it responds with status `200 OK`, it is overwritten from the beginning. If it responds with `416 Range Not Satisfiable`, the downloader resets and starts a fresh download.

### Validation Strategy
Every downloaded document must pass a multi-layer validation pipeline to ensure it is not corrupted and is indeed a legislative document:
1. **HTTP Status Check**: Ensure response status code is `200` or `206`.
2. **File Extension Check**: File suffix must be `.pdf`.
3. **Minimum File Size Check**: File size must exceed a configured minimum threshold (default: 100 bytes) to prevent empty files or short HTML error pages.
4. **Magic Byte Signature Check**: The first 4 bytes must match the PDF magic header `%PDF`.
5. **Structural Corruption Check**: The file is structurally loaded using `PyPDF2.PdfReader` to read the trailer and cross-reference table without performing text extraction. If any parse exception is thrown, the file is flagged as corrupted and deleted.

## How to Add a New Legislative Source
To add another source (e.g. Ministry press releases or Lok Sabha committee reports):
1. **Define a New Parser method** in `ingestion/parliament/parser.py` (e.g. `parse_lok_sabha_committee`).
2. **Extend `discover_bills`** in `ingestion/parliament/discovery.py` to support the new `source` identifier.
3. **Register new catalog targets** in `data/catalog/bill_catalog.json` under `datasets`.
4. **Re-run the ingestion** from the CLI specifying the new source: `python main.py ingest --source <new_source>`.

## How Repositories Interact
Repositories (e.g., `BillRepository`, `MarketModelRepository`, `EventStudyRepository`, `StatisticalRepository`) abstract file system interactions:
- They load configurations from `config.settings`.
- They read and write standardized schema objects (`Bill`, `Company`, `PriceRecord`, `MarketModelRecord`, `EventStudyRecord`, `StatisticalResult`), shielding ingestion, quantitative finance engines, and prediction pipeline modules from physical file formats and directory structures.
- Swapping to a database or cloud storage backend will only require changing the repository's internal save/load implementations without touching any business or service layer logic.

## How Schemas are Used
- Every file in the pipelines must adhere to standard data schemas under `schemas/`.
- Schemas hold standard enums (e.g., `BillStatus`, `BillHouse`, `ImpactLabel`) to ensure consistent values throughout data ingestion, feature builders, models, and UI dashboards.
- Serialisation roundtrips are handled by `to_dict` and `from_dict` methods.

### Bill Schema Fields (Task 1A.2 & 1A.3 additions)
| Field | Type | Source |
|-------|------|--------|
| `year` | `Optional[int]` | Discovery → detail page → None if unknown |
| `ministry` | `str` | Detail page (empty if unavailable) |
| `pdf_url` | `Optional[str]` | Detail page PDF link (URL only) |
| `session` | `str` | Detail page session field |
| `sponsor` | `str` | Detail page introduced-by field |
| `related_bills` | `list[str]` | Slugs of linked bills on detail page |
| `related_acts` | `list[str]` | Act links on detail page |
| `language` | `str` | HTML lang attribute (default: English) |
| `last_updated` | `Optional[date]` | Meta tag / detail page date field |
| `document_path` | `Optional[str]` | Absolute path to downloaded PDF document |
| `document_size` | `Optional[int]` | Size of the downloaded file in bytes |
| `document_checksum` | `Optional[str]` | SHA-256 checksum of the completed PDF |
| `download_timestamp` | `Optional[str]` | ISO-8601 timestamp when download succeeded |
| `download_status` | `Optional[str]` | Execution status (`success`, `failed`) |
| `text_path` | `Optional[str]` | Absolute path to the extracted `.txt` file |
| `text_checksum` | `Optional[str]` | PDF checksum at last successful extraction |
| `text_size` | `Optional[int]` | Size of the extracted `.txt` file in bytes |
| `text_status` | `Optional[str]` | Extraction status (`success`, `scanned_pdf`, `failed`) |
| `extraction_method` | `Optional[str]` | Library used (`pdfplumber`, `pypdf2`) |
| `extraction_timestamp` | `Optional[str]` | ISO-8601 timestamp when extraction finished |
| `page_count` | `Optional[int]` | Total page count extracted from the PDF |
| `quality_metrics` | `Optional[dict]` | Character count, word count, avg chars per page |


## Text Extraction & Corpus Generation Workflow (Task 1A.4)

### Extraction Engine Strategy
To convert official PDFs to structured text, the extractor utilizes a dual-engine strategy:
1. **pdfplumber (Primary)**: Focuses on preserving structural text flow and layout. It extracts tabular data and formats it as tab-separated values.
2. **PyPDF2 (Fallback)**: Used if `pdfplumber` fails or returns zero characters.

### Scanned PDF & OCR Detection
If the total character count extracted across all pages is under 50 characters, the PDF is flagged as a scanned image. The `text_status` is set to `scanned_pdf`, and the corpus file is not written to disk, ensuring only high-quality searchable text is populated in the corpus.

### Text Cleaning & Deduplication
- **Unicode NFKC Normalization**: Compatibility characters (e.g. ligatures) are mapped to standard canonical forms.
- **Header & Footer Removal**: Repeated headers/footers (lines appearing on more than 50% of the document pages) are detected and removed to ensure clean, continuous prose.
- **Page Number Stripping**: Standard page numbering sequences are programmatically stripped from the text.
- **Spacing Normalization**: Multiple consecutive blank lines are collapsed to preserve paragraph structures without excess padding.


## Legislative Knowledge Layer Workflow (Task 1A.5)

The Legislative Knowledge Layer converts raw legislative text and metadata into canonical domain knowledge using a deterministic Rule Engine. This layer abstracts away LLM dependencies, running at high speed and 100% determinism.

### Taxonomy Mappings and Rules
All rules are stored as editable CSV files under the `knowledge/` directory:
1. **`ministry_mappings.csv`**: Normalizes raw sponsoring ministry names to a set of standardized, canonical ministries.
2. **`sector_domain_mapping.csv`**: Maps economic sectors to policy domains, economic domains, regulatory authorities, and default stakeholder groups.
3. **`geographic_scope_rules.csv`**: Maps state names and region keywords to geographic scopes.
4. **`bill_type_rules.csv`**: Maps keywords inside the title to bill types (e.g., Amendment Bill, Ordinary Bill).
5. **`departments.csv`**: Resolves specific departments using the canonical ministry and primary sector, supporting wildcards.
6. **`taxonomy_hierarchy.csv`**: Defines parent-to-child relationships (e.g. Finance -> Banking -> NBFC) to enable top-down hierarchical taxonomy traversal.

### Rule Engine Processing Logic
1. **Ministry Normalization**: Sponsoring ministries are cleaned and mapped using `ministry_mappings.csv`.
2. **Primary Sector Resolution**: Categorizes the bill into a primary sector based on:
   - Sponsoring ministry defaults (resolved via `ministry_sector.csv`).
   - Sponsoring category keywords (resolved via `bill_categories.csv`).
   - Keyword frequency fallback (counting hits of sector-specific keywords with word boundary checks).
3. **Secondary Sector Activation**: Traverses the parent-to-child taxonomy hierarchy downstream from the canonical ministry and primary sector. Nodes are activated as secondary sectors if they are mentioned directly in the text, or if at least 3 of their sector keywords are present.
4. **Department Resolution**: Resolves the sponsoring department based on a combination of the canonical ministry and primary sector (falling back to wildcard sector mapping if a specific rule does not exist).
5. **Geographic Scope & Bill Type Resolution**: Matches keywords inside titles, summaries, and corpus texts to determine regional scope (e.g. State-specific vs. National) and bill type (e.g. Constitution Amendment vs. Ordinary Bill).
6. **Traceability Metadata**: Automatically records generating metadata, including the SHA-256 checksums of the original files, generation timestamps, and computed confidence scores.

### Knowledge Repository
The `KnowledgeRepository` handles CRUD operations on knowledge records. It stores each record as a JSON file under `data/bills/knowledge/<bill_id>.json` alongside the metadata and corpus, keeping the data segregated but traceable.

### Validation Rules
The validator screens generated `KnowledgeRecord` objects to ensure taxonomy integrity:
- **Unknown Sponsoring Ministry**: Rejects records with ministries not defined in the lookup files.
- **Unknown Policy Domain**: Rejects records with policy domains not defined in the lookup files.
- **Conflicting Mappings**: Validates that the resolved primary sector aligns with the allowed sectors for the sponsoring ministry.
- **Duplicate Keywords**: Warns if duplicate keywords are present.

---

## Company Intelligence Database (Tasks 2.1 & 2.2)

### Company Master Database Architecture
The Company Intelligence layer is centered around a dedicated **Company Repository (`CompanyRepository`)** which decouples the persistence format (currently structured JSON under `data/companies/companies.json`) from the ingestion and search domains.
- **Preserves Repository Pattern**: Handles CRUD (`save`, `save_many`, `upsert_many`) and query logic independently of the legislative databases.
- **Enriched Schemas**: Stores canonical `Company` models enriched with sub-industries, headquarters city/state, websites, and listing statuses.

### Ingestion & Normalization Strategy
The `CompanyLoader` manages the ingestion pipeline:
1. **Live Exchange Downloads**: Queries active equities from the official NSE/BSE master feeds.
2. **Offline Seed Fallback**: Automatically falls back to a curated, high-quality seed database of **50+ major Indian companies** across multiple sectors (NIFTY 50, NIFTY Next 50, and key sector leaders) if exchange websites are offline or unreachable, ensuring zero pipeline downtime.
3. **Data Normalization**:
   - **Corporate Name Normalization**: Cleans and strips raw exchange casing and standardizes abbreviations (e.g. `RELIANCE INDUSTRIES LTD` → `Reliance Industries Limited`, `INFOSYS CO.` → `Infosys Company`).
   - **Symbol & ISIN Normalization**: Trims and forces uppercase.
   - **State Name Normalization**: Resolves raw state and city inputs/abbreviations (e.g. `mah`, `mumbai`, `kar`, `bangalore`) to canonical Indian State/UT names (e.g. `Maharashtra`, `Karnataka`).

### Company Validation Rules
Validation checks are run at both individual record and database collection levels:
- **Missing Company Names / ISINs**: Critical validation errors.
- **Missing Sector**: Validation warning (non-blocking).
- **Invalid Websites**: Rejects websites that do not start with `http://` or `https://`.
- **Invalid States**: Rejects states not present in the official set of Indian States/UTs.
- **Duplicate Checks**: Collection-level check identifying duplicate NSE Symbols or duplicate ISINs.

### Performance & Scalability
With the expanded universe of 50 major companies:
- **Mass Persist Ops**: `save_many` operations complete in **< 10ms** (well below the 100ms threshold).
- **Search Latencies**: Query lookups across name, symbol, sector, industry, and state complete in **< 1ms** (well below the 50ms threshold), ensuring high responsiveness as the company network grows.


---

## Bill → Company Mapping Engine (Task 2.3)

The Bill-to-Company Mapping Engine maps legislative bills to potentially affected listed companies using the Legislative Knowledge Layer and the Company Intelligence Database with zero machine learning, LLMs, or prediction.

### Deterministic Mapping Rules & Scoring
The mapping engine (`SectorMapper`) evaluates active companies against each bill's metadata and knowledge records using a scoring system:
1. **Base Sector Matches**:
   - **Primary Sector Match**: Base confidence `0.50` if the company's sector matches the bill's primary sector.
   - **Secondary Sector Match**: Base confidence `0.30` if the company's sector matches one of the bill's secondary sectors.
2. **Deterministic Confidence Boosts**:
   - **Industry / Sub-industry Mentions**: Boost of `+0.20` (industry) or `+0.10` (sub-industry) if the industry name (or sub-industry name) is mentioned inside the bill title, summary, or corpus text, or is present in the bill's keywords. The matching is plural-tolerant (e.g. matching "private sector banks" with "private sector bank").
   - **Sponsoring Ministry Alignment**: Boost of `+0.20` if the company's sector is regulated by the sponsoring ministry (using `knowledge/ministry_sector.csv`).
   - **Company Name/Alias Direct Mention**: Boost of `+0.10` if the company's normalized name (excluding suffixes like "Limited", "Ltd") or any of its alias keywords are explicitly mentioned in the bill text.
3. **Capping & Sorting**:
   - Total mapping confidence is capped at `1.0` and rounded to two decimal places.
   - Candidate companies are sorted by confidence descending, then by company name ascending.

### Mapping Repository
The `MappingRepository` is responsible for storage operations on mapping records:
- Saves mapping records as JSON files under `data/mappings/<bill_id>.json`.
- Implements optimized in-memory lookup indices to enable high-speed lookups by:
  - **Bill ID**
  - **Company ID** (ISIN, NSE Ticker, or name substring)
  - **Sector**
  - **Ministry**
  - **Policy Domain**

### Mapping Validation & Integrity Rules
The validator enforces data integrity constraints on generated mapping records:
- **Unknown Sectors**: Rejects mappings where the primary or secondary sectors are not known in the system.
- **Duplicate Companies**: Rejects mappings where the same company ISIN is mapped twice in a single bill's candidate list.
- **Missing Companies**: Raises a warning if a bill regulates a sector that has active companies in the company database, but the candidate company list is empty.
- **Conflicting Mappings**: Rejects mappings if a company is mapped to a bill whose sectors do not match the company's sector (with support for compatible sector prefix/substring matching).
- **Ministry-Sector Mismatch**: Raises a warning if a company's sector is not regulated by the bill's sponsoring ministry.

---

## Historical Market Data Ingestion Service (Task 3.1)

The Historical Market Data Ingestion Service handles downloading, normalizing, validating, and persisting historical daily stock/index prices required for downstream event-study and market impact modeling.

### Market Repository (`MarketRepository`)
The `MarketRepository` is the single access point for reading and writing OHLCV market price data, index data, and daily returns.
- **Parquet Storage Format**: Stores historical prices as Parquet files partitioned by symbol and year under `data/market/<symbol>/<year>.parquet`. This format ensures high compression (~10–20× over CSV) and fast single-symbol queries without full dataset scans.
- **Index Ticker Mapping**: Automatically maps human-friendly index references (e.g. `NIFTY 50`, `NIFTY Bank`, `NIFTY IT`) to Yahoo Finance ticker equivalents (e.g. `^NSEI`, `^NSEBANK`, `^CNXIT`).
- **Log Returns Computation**: Dynamically calculates and slices daily log-returns: $R_t = \ln(Close_t / Close_{t-1})$ with custom buffer windows to ensure the first query date's return is calculated correctly.

### Market Data Ingestion (`MarketLoader`)
The `MarketLoader` class orchestrates the download and incremental syncing of market data:
1. **Asset Universe Resolution**: Syncs all 8 supported benchmark and sectoral indices and active listed companies. Resolves company tickers to yfinance identifiers (appending `.NS` for NSE and `.BO` for BSE).
2. **Yahoo Finance Scraper**: Pulls daily OHLCV and Adjusted Close history using `yfinance`.
3. **Price Normalization**:
   - Resets index and standardizes date formats to `YYYY-MM-DD`.
   - Maps yfinance columns to a canonical schema: `Date`, `Open`, `High`, `Low`, `Close`, `Adjusted Close`, `Volume`.
   - Clears missing records and ignores non-trading holiday intervals.
4. **Incremental & Bidirectional Synchronization**: Automatically reads existing date ranges in the repository. If the target start date is earlier than the locally stored minimum date, it performs a backward sync (downloading only the missing earlier periods up to `min_date - 1 day`). If the target end date is after the locally stored maximum date, it performs a forward sync (downloading from `max_date + 1 day` to the target end date). If the target range is already covered, it skips the download. This bidirectional capability preserves all existing data while expanding coverage.
5. **Earliest Sync Cache**: Uses a local, non-invasive `.earliest_sync` marker file in the symbol's directory to record the earliest attempted synchronization date. This prevents redundant backward sync attempts and yfinance API queries for companies listed after the target start date (which would otherwise return empty data).
6. **Rate Limiting & Throttle Control**: Introduces a deterministic 0.5-second sleep delay between successive asset downloads to respect Yahoo Finance's rate limits and prevent API throttling.

### Expanded Historical Coverage (01 January 2014 onwards)
To support robust event studies and long-term backtesting, the market ingestion pipeline has been expanded to download and sync historical data starting from **01 January 2014** (or the earliest listing date for more recently listed assets).
- **Estimation Window Robustness**: Downstream Event Study estimation windows require stable baseline returns parameter estimation (typically -120 to -10 trading days relative to a bill's introduction). Expanding the price series back to 2014 guarantees that bills introduced in 2014–2016 have adequate, non-overlapping historical data to calculate alpha and beta parameters.
- **Backtesting and Out-of-Sample Validation**: Provides a 12-year historical testing canvas to backtest market-impact prediction algorithms, run out-of-sample statistical tests, and validate expected returns models across multiple economic cycles.

### Market Data Validation Rules
Validator logic (`validate_market_df`) executes before any persistence operation to screen data quality:
- **Missing Required Fields**: Rejects DataFrames missing key OHLCV columns.
- **Duplicate Rows**: Rejects records containing duplicate dates for the same symbol.
- **Invalid Prices**: Rejects rows containing non-numeric values or negative/zero prices.
- **Negative Volume**: Rejects rows containing negative trading volume.
- **Trading Day Gaps**: Warns if consecutive calendar day gaps exceed 5 days (excluding weekends), detecting potential historical data omissions.


## Market Model Engine (Task 4.1)

The Market Model Engine manages the Ordinary Least Squares (OLS) estimation of expected asset returns against the NIFTY 50 index benchmark. This forms the mathematical basis for future event studies.

### Market Model Repository (`MarketModelRepository`)
The `MarketModelRepository` provides a decoupled access layer for reading, writing, and checking the existence of OLS regression results.
- **JSON File Storage**: Stores records under `data/market_models/` using the unique naming convention `{bill_slug}_{company_isin}.json` to guarantee no collisions.
- **Single and Batch Queries**: Implements CRUD methods along with specialized filtering (`get_by_bill`, `get_by_company`).

### Market Model Validator (`MarketModelValidator`)
A strict validation gate that ensures statistical significance and numerical safety:
- **Input Validation**: Rejects runs with missing bills, companies, or price series.
- **Overlap Validation**: Rejects estimations with fewer than 60 overlapping trading observations.
- **Variance Check**: Rejects regressions where the benchmark returns variance is near-zero (< $10^{-9}$), avoiding singular/undefined slopes.

### Market Model Service (`MarketModelService`)
Coordinates the estimation pipeline:
1. **Event Day Calendar Resolution**: Maps the bill introduction date to the actual trading calendar of the benchmark index (NIFTY 50/`^NSEI`). Resolves non-trading event days to the next active trading session.
2. **Estimation Window Alignment**: Dynamically computes the index bounds for the configurable estimation window (default: $T = -120$ to $T = -10$ trading days relative to the event).
3. **Benchmark Returns Caching**: Caches full benchmark daily log returns in memory to bypass redundant Parquet read operations during batch runs.
4. **OLS Engine**: Triggers the OLS regression and persists the output.
5. **Incremental Synced Execution**: Skips already estimated bill-company pairs unless a force-refresh is requested.

---

## Label Generation Engine (Task 4.4)

The Label Generation Engine converts completed ``StatisticalResult`` records (from Task 4.3) into authoritative ground-truth labels for supervised machine learning.  No ML training is performed in this layer — it is a pure data-transformation pipeline.

### Label Types

Four labels are computed per (bill × company × event-window) triple:

| Label | Type | Values |
|-------|------|--------|
| `direction` | Categorical | `POSITIVE`, `NEGATIVE`, `NEUTRAL` |
| `market_moving` | Binary | `True`, `False` |
| `impact_strength` | Ordinal | `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH` |
| `confidence` | Ordinal | `HIGH`, `MEDIUM`, `LOW` |

### Classification Rules

**Direction Label** (configurable via `LABEL_POSITIVE_CAR_THRESHOLD`, `LABEL_NEGATIVE_CAR_THRESHOLD`):
- `POSITIVE`: CAR > +threshold **AND** `significant == True`
- `NEGATIVE`: CAR < −threshold **AND** `significant == True`
- `NEUTRAL`: all other cases (insignificant result, or |CAR| below threshold)

**Market-Moving Label** (configurable via `LABEL_MARKET_MOVING_CAR_THRESHOLD`):
- `True` if `significant == True` AND `|CAR| > threshold`

**Impact Strength** (configurable via `LABEL_STRENGTH_LOW_MAX`, `LABEL_STRENGTH_MEDIUM_MAX`, `LABEL_STRENGTH_HIGH_MAX`):

| Strength | Condition |
|----------|-----------|
| `LOW` | `|CAR| < 1%` (default) |
| `MEDIUM` | `1% ≤ |CAR| < 3%` |
| `HIGH` | `3% ≤ |CAR| < 6%` |
| `VERY_HIGH` | `|CAR| ≥ 6%` |

**Confidence Label** (composite of p-value and effect size):

| Confidence | Condition |
|------------|-----------|
| `HIGH` | `p_value ≤ 0.01` **AND** `effect_size == "Large"` |
| `MEDIUM` | `p_value ≤ 0.05` **OR** `effect_size ∈ {Medium, Large}` |
| `LOW` | everything else |

### Validation

A label is **rejected** and replaced by a `LabelValidationReport` if:
- The source `StatisticalResult` is `None`
- The CAR value is `NaN` or `±Inf`
- The p-value is `NaN` or `±Inf`

### Label Repository (`LabelRepository`)
- JSON file storage under `data/labels/` (configurable via `settings.LABELS_DIR`)
- Naming convention: `{bill_id}_{company_isin}_{sanitized_window}.json`
- Implements the same Repository Pattern as `StatisticalRepository`
- Supports full CRUD plus `get_by_bill` and `get_by_company` filtered queries

### Label Generation Service (`LabelGenerationService`)
Orchestrates the full pipeline:
1. **Load**: Reads all `StatisticalResult` records from `StatisticalRepository`
2. **Filter**: Applies optional bill ID, year, and event-window filters
3. **Incremental Skip**: Skips already-labelled records (unless `force_refresh=True`)
4. **Generate**: Delegates to `LabelGenerator` for all four label computations
5. **Persist**: Saves valid `LabelRecord` objects to `LabelRepository`
6. **Audit**: Collects `LabelValidationReport` objects for rejected records
7. **Summarise**: Returns a dict with `processed`, `generated`, `skipped`, `rejected` counts

### Ground Truth Strategy

Labels produced by this engine are derived exclusively from **observed historical market data** and **statistically validated event-study results**.  This ensures:
- **Objectivity**: No analyst judgement or heuristics are used
- **Reproducibility**: Labels regenerate deterministically from the same inputs
- **Auditability**: Every label carries a `decision_reason` and `calculation_timestamp`
- **Configurability**: All thresholds are environment-variable-driven

---

## Feature Engineering Engine (Task 5.1)

The Feature Engineering Engine is the **integration layer** of the Research Pipeline.  It combines every upstream repository into a single structured feature table — the master ML dataset.

### Purpose

| What it does | Why it matters |
|---|---|
| Merges 8 upstream repositories into one flat table | Gives ML models a single, versioned input |
| Anchors joins on Label records | Guarantees every row has ground-truth labels |
| Validates numerics and label completeness | Prevents silent NaN or missing-label errors in training |
| Persists to Parquet (primary) + CSV (export) | Columnar storage for fast dataset loading |
| Supports incremental rebuild | Avoids recomputing unchanged rows |

### Data Flow

```
Label Repository          ──► record key enumeration
   │
   ├── Bill Repository        ──► bill_title, introduction_date
   ├── Knowledge Repository   ──► bill_type, ministry, department,
   │                               policy_domain, economic_domain,
   │                               primary_sector, secondary_sectors,
   │                               regulatory_authority, geographic_scope
   ├── Company Repository     ──► company_name, nse_symbol, sector,
   │                               industry, market_cap_category, hq_state
   ├── Market Model Repository ─► alpha, beta, r_squared,
   │                               residual_variance, observation_count
   ├── Event Study Repository  ─► final_car, avg_ar, max_ar, min_ar,
   │                               peak_ar_day, peak_car_day
   ├── Statistical Repository  ─► t_statistic, p_value,
   │                               confidence_interval, significant_flag,
   │                               significance_level, effect_size
   └── Label Repository        ─► direction, market_moving,
                                   impact_strength, confidence_label
                                         │
                                         ▼
                              FeatureRecord (one per Bill × Company × Window)
                                         │
                                         ▼
                              FeatureRepository
                              data/features/master_feature_dataset.parquet
                              data/features/master_feature_dataset.csv
```

### Key Classes

| Class | Location | Role |
|---|---|---|
| `FeatureRecord` | `schemas/feature_record.py` | Canonical dataclass for one row |
| `FeatureValidationReport` | `schemas/feature_validation_report.py` | Audit record for rejected rows |
| `FeatureEngineeringEngine` | `features/feature_engine.py` | Core merge + validate + persist logic |
| `FeatureBuilder` | `features/feature_builder.py` | Public entry-point (stable API wrapper) |
| `FeatureRepository` | `storage/feature_repository.py` | Parquet/CSV I/O + incremental index |
| `FeatureBuildResult` | `features/feature_engine.py` | Build summary dataclass |

### Feature Groups

| Group | Source Repository | Fields |
|---|---|---|
| Legislative | Bill + KnowledgeRecord | bill_title, bill_type, ministry, department, policy_domain, economic_domain, primary_sector, secondary_sectors, regulatory_authority, geographic_scope, introduction_date |
| Company | Company | company_name, nse_symbol, isin, company_sector, industry, sub_industry, market_cap_category, hq_state |
| Financial | MarketModelRecord | alpha, beta, r_squared, residual_variance, observation_count |
| Event Study | EventStudyRecord | final_car, avg_ar, max_ar, min_ar, peak_ar_day, peak_car_day |
| Statistical | StatisticalResult | t_statistic, p_value, confidence_interval (lower/upper), significance_level, significant_flag, effect_size |
| Target Labels | LabelRecord | direction, market_moving, impact_strength, confidence_label |

### Validation Rules

| Rule | Severity | Condition |
|---|---|---|
| All four labels present | ERROR | Any of direction / market_moving / impact_strength / confidence_label is None |
| No NaN numerics | ERROR | alpha, beta, r_squared, t_statistic, p_value, or final_car is `float('nan')` |
| Missing upstream data | WARNING | Bill, KnowledgeRecord, Company, MarketModel, EventStudy, or StatisticalResult not found |

Records with `ERROR` severity are excluded from the dataset.  Records with `WARNING` severity are retained with partial features.

### Storage Layout

```
data/features/
    master_feature_dataset.parquet   ← primary (columnar, fast read)
    master_feature_dataset.csv       ← optional human-readable export
    index.json                       ← O(1) record-ID existence check
```

### Incremental Rebuild

The engine records every `record_id` (`{bill_id}|{company_isin}|{event_window}`) in `index.json`.  On subsequent `build(incremental=True)` calls, existing IDs are skipped.  Use `build(incremental=False)` or `rebuild()` to force a full recompute.

### Configuration

| Setting | Default | Purpose |
|---|---|---|
| `FEATURES_DIR` | `data/features/` | Root directory for feature artefacts |
| `FEATURE_DATASET_NAME` | `master_feature_dataset` | Parquet/CSV file stem name |

---

## NLP Embedding Engine (Task 5.2)

The **NLP Embedding Engine** generates reusable semantic text embeddings for every Indian legislative bill. These embeddings capture legal concepts, regulatory scope, and policy tone, and are stored in a form that can be fused with structured features for downstream machine learning.

### Design Principles & Workflow

```
1. Input: master_feature_dataset.parquet (extracts unique bill IDs)
2. For each unique bill_id:
    a. Locate text source (Bill Corpus -> Full Bill Text -> Bill Summary)
    b. Check embedding cache (cache hit -> return cached vector)
    c. Tokenize text chunking to model max length (512 tokens)
    d. Forward pass through HF Transformer model (FinBERT / Legal-RoBERTa)
    e. Apply pooling strategy (CLS or Mean Pooling)
    f. Validate vector dimensions, NaN/Inf values, non-empty
3. Persist new records to repository (index.json + Parquet metadata + NumPy matrix)
```

### Key Classes

| Class | Location | Role |
|---|---|---|
| `EmbeddingRecord` | `schemas/embedding_record.py` | Canonical model representation of a generated bill embedding |
| `EmbeddingValidationReport` | `schemas/embedding_record.py` | Audit record of bills rejected during embedding generation |
| `EmbeddingRepository` | `storage/embedding_repository.py` | Abstract I/O layer for saving and loading Parquet data and NumPy matrices |
| `EmbeddingEngine` | `models/embeddings/embedding_engine.py` | Main orchestration class for model loading, pooling, and batch execution |

### Text Selection Prioritization

To handle varying availability of text sources across different bill records, the engine selects the highest-quality text source using the following priority order:
1. **Bill Corpus (`text_path`)**: The full preprocessed NFKC normalized text file generated from the bill PDF.
2. **Full Bill Text (`full_text`)**: The plain text representation stored directly in the metadata.
3. **Bill Summary (`summary`)**: The official summary of the bill (fallback).

If none of these are available or if they are empty, the bill is rejected and logged in the validation report.

### Supported Models & Pooling Strategies

The engine supports two pre-trained Hugging Face transformer models, configured via `config/settings.py` or CLI arguments:
- **FinBERT** (`ProsusAI/finbert`): Specialized in financial sentiment and economic classification (768 dimensions).
- **Legal-RoBERTa** (`lexlms/legal-roberta-base`): Pre-trained on legal texts, capturing complex legal and regulatory terminology (768 dimensions).

Available pooling strategies:
- **`mean`**: Mean Pooling. Calculates the element-wise average of word token embeddings across the sequence length, weighted by the attention mask. This is the default strategy.
- **`cls`**: CLS Token Pooling. Extracts the embedding of the special `[CLS]` token (representing sentence-level context).

### Validation Constraints

Every generated embedding vector must pass the following rules:
- **Non-empty**: The vector must contain values.
- **Dimensionality Match**: Must match the model's standard dimension (768 for both FinBERT and Legal-RoBERTa).
- **No NaN or Inf**: Must not contain any `float('nan')` or `float('inf')` values.

Vectors that fail these checks are discarded, and an error report is appended to the validation results.

### Storage Layout & Caching

Embeddings are saved inside subdirectories named after the specific model under `data/embeddings/` to support concurrent multi-model experimentation:
```
data/embeddings/{model_name}/
    index.json                       ← O(1) existence check for bill caching
    embeddings_metadata.parquet       ← Columns: bill_id, embedding_model, embedding_dimension, model_version, generation_timestamp, token_count
    embeddings_matrix.npy            ← Raw N × D float32 matrix matching the sorted order of parquet rows
```

The NumPy matrix matches the row-order of the Parquet metadata file, making loading the embeddings as feature inputs for ML models extremely fast:
```python
import numpy as np
import pandas as pd

df_meta = pd.read_parquet("data/embeddings/finbert/embeddings_metadata.parquet")
embeddings = np.load("data/embeddings/finbert/embeddings_matrix.npy")
```

### CLI Command Options

Generate or refresh embeddings using:
```bash
python main.py generate-embeddings --model finbert --pooling mean --batch-size 16
```
Use `--force-refresh` to ignore the cache and rebuild all embeddings.

---

## Feature Fusion Engine (Task 5.3)

The **Feature Fusion Engine** compiles and merges structured features (from `master_feature_dataset.parquet`) with dense text embeddings (from FinBERT and Legal-RoBERTa repositories) into unified, machine-learning-ready datasets. 

### Key Classes

| Class | Location | Role |
|---|---|---|
| `FusionValidationReport` | `schemas/fusion_validation_report.py` | Audits dataset-level metrics (duplicate checks, NaN keys, missing embeddings) |
| `FusionRepository` | `storage/fusion_repository.py` | Reads and writes fused Parquet tables and companion JSON validation reports |
| `FeatureFusionEngine` | `features/fusion_engine.py` | Orchestrates the joining, vector expansion, and verification of fused records |

### Supported Fusion Modes

The system supports six distinct fusion modes to enable research comparison and future SaaS deployment:

1. **`structured`**: Structured Features Only (`structured_dataset.parquet`)
2. **`finbert`**: FinBERT Embeddings Only (`finbert_dataset.parquet`)
3. **`legal`**: Legal Transformer Embeddings Only (`legal_dataset.parquet`)
4. **`structured-finbert`**: Structured Features + FinBERT (`structured_finbert_dataset.parquet`)
5. **`structured-legal`**: Structured Features + Legal Embeddings (`structured_legal_dataset.parquet`)
6. **`hybrid`**: Structured Features + FinBERT + Legal Embeddings (`hybrid_dataset.parquet`)

### Embedding Column Expansion

To make dense vectors immediately consumable by tabular ML frameworks (e.g. LightGBM, XGBoost, Scikit-learn), the engine automatically flattens/expands the 768-dimension list-typed embedding columns into individual, float-valued columns:
- **FinBERT columns**: `finbert_emb_0` through `finbert_emb_767`
- **Legal columns**: `legal_emb_0` through `legal_emb_767`

### Storage Layout

All outputs are stored in `data/fused/` with companion JSON reports to ensure full traceability and data quality diagnostics:
```
data/fused/
    structured_dataset.parquet
    validation_report_structured.json
    finbert_dataset.parquet
    validation_report_finbert.json
    legal_dataset.parquet
    validation_report_legal.json
    structured_finbert_dataset.parquet
    validation_report_structured-finbert.json
    structured_legal_dataset.parquet
    validation_report_structured-legal.json
    hybrid_dataset.parquet
    validation_report_hybrid.json
```

### CLI Command Options

Build or refresh fused datasets using:
```bash
# Build a specific mode
python main.py build-fusion --mode hybrid

# Build all modes in sequence
python main.py build-fusion --all
```
Use `--rebuild` to force a complete rebuild of the datasets, ignoring existing records.

## Model Evaluation Engine (Task 6.2)

### Overview
The Model Evaluation Engine evaluates every trained classifier from the models/ directory using the unified training dataset. It is decoupled from the training loop, ensuring zero retraining is executed during evaluation.

### Components
1. **ModelEvaluator (models/evaluation/evaluator.py)**: Coordinates model loading via ModelRepository, triggers feature-label extraction via DatasetBuilder, executes inference pipeline transforms, generates predictions and probabilities, and conducts comparative ranking and detailed error analysis.
2. **metrics.py (models/evaluation/metrics.py)**: Unified API to calculate multi-class and binary evaluation metrics (Accuracy, Balanced Accuracy, Matthews Correlation Coefficient, Precision, Recall, Macro/Weighted F1, Log Loss, and ROC-AUC).
3. **EvaluationRepository (storage/evaluation_repository.py)**: Persistence layer for outputs in the evaluation/ directory:
   - metrics.json: Consolidated targets and algorithms performance stats.
   - confusion_matrix.csv: Flat table mapping target/model combinations to true vs predicted counts.
   - classification_report.json: Per-class precision, recall, f1, and support statistics.
   - comparison_report.json: Ranked model listings, Best vs Worst models, and average target baseline performance.

---

## Historical Backtesting Engine (Task 6.4)

### Overview
The Historical Backtesting Engine evaluates whether the trained prediction system produces useful predictions and investment signals using information that was strictly available on or before each historical bill introduction event.

### Key Architecture Components
1. **Strict Anti-Leakage Protocol**: Strips all post-event variables (CAR, AR, peak day, t-stats, p-values, future prices/labels) from prediction inputs.
2. **Temporal Walk-Forward Execution (`backtesting/engine.py`)**: Iterates chronologically through historical bill events. For every step, model preprocessors and classifiers are fit strictly on observations prior to the prediction timestamp.
3. **Strategy & Transaction Costs (`backtesting/strategy.py`)**: Translates predictions to quantitative trade signals (Positive $\rightarrow$ Long, Negative $\rightarrow$ Short, Neutral $\rightarrow$ 0). Subtracts configurable brokerage, slippage, and fee costs (`TransactionCostModel`). Compares against Buy-and-Hold and NIFTY 50 market benchmarks.
4. **Metrics Calculators (`backtesting/metrics.py`)**: Computes statistical classification metrics (Accuracy, Precision, Recall, Macro/Weighted F1, Balanced Accuracy, MCC, ROC-AUC, Brier Score, ECE) and financial strategy performance metrics (Cumulative Return, Sharpe Ratio, Max Drawdown, Volatility, Hit Ratio).
5. **Visualizer (`backtesting/visualizer.py`)**: Generates high-resolution PNG plots: `equity_curve.png`, `drawdown_curve.png`, `prediction_vs_actual.png`, `model_comparison.png`.
6. **Persistence & Reports (`storage/backtest_repository.py` & `backtesting/report_generator.py`)**: Stores runs under `data/backtests/<run_id>/` containing `backtest_report.json`, `model_comparison.json`, `strategy_metrics.json`, `leakage_report.json`, and `prediction_results.parquet`.
7. **Validation (`validation/backtest_validator.py`)**: Audits execution for look-ahead leakage, training cutoff violations, duplicate predictions, missing data, and invalid returns.

---

## Anticipation Bias / Pre-Event Information Analysis Engine (Task 6.5)

### Overview
The Anticipation Bias Analysis Engine is a research-grade quantitative diagnostic component that determines whether market participants received information about a legislative bill before its official parliamentary introduction date ($T_0$).

### Key Architecture Components
1. **Multi-Window Market Analyzer (`anticipation/market_analyzer.py`)**:
   - Calculates abnormal returns across trading-day aligned windows `[-30,-21]`, `[-20,-11]`, `[-10,-6]`, `[-5,-3]`, `[-2,-1]`, and cumulative `[-30,-1]`.
   - Computes MAR, CAR, volatility, AR z-scores, and p-values based on OLS market model residuals.
2. **Deterministic Signal Detector (`anticipation/signal_detector.py`)**:
   - Evaluates statistical significance ($|z| \ge 1.96$), return magnitude ($|CAR| \ge 2.0\%$), sustained direction ($\ge 70\%$), immediate concentration (`[-5,-3]`, `[-2,-1]`), and multi-window sign persistence.
3. **Scorer & Classifier (`anticipation/scorer.py`)**:
   - Blends market signal score and exponential-decayed pre-event information evidence into a normalized composite anticipation score $[0.0, 1.0]$.
   - Classifies pairs and bills into `NO_EVIDENCE`, `WEAK_EVIDENCE`, `MODERATE_EVIDENCE`, `STRONG_EVIDENCE`.
4. **Strict Anti-Leakage Validator (`validation/anticipation_validator.py`)**:
   - Audits evidence timestamps to strictly enforce $t_{\text{pub}} < T_0$. Rejects post-$T_0$ items and logs details in `AnticipationValidationReport`.
5. **Storage Layer (`storage/anticipation_repository.py`)**:
   - Manages persistence in `data/anticipation/`: `scores/`, `bill_scores/`, `market_stats/`, `evidence/`, `reports/`.
6. **Service & CLI (`services/anticipation_service.py` & `main.py`)**:
   - `python main.py analyze-anticipation` supports year/bill/company filters, incremental cached runs (`skip_existing`), and `--force-refresh`.

---

## Final Prediction & Decision Engine (Task 7.1)

### Overview
The Final Prediction & Decision Engine serves as the core forward-looking inference and contextual decision-support system. It loads existing trained machine learning estimators and preprocessors from `models/`, applies rigorous pre-inference validation, extracts calibrated multi-target probability distributions, and synthesizes qualitative decision support blending diagnostic pre-event anticipation evidence.

### Architecture Subsystems

```
                                  Input Candidate
                           (Bill-Company-Window Feature Row)
                                         │
                                         ▼
                            ┌────────────────────────┐
                            │  PredictionValidator   │
                            │ (Pre-inference checks) │
                            └────────────┬───────────┘
                                         │ Validated Features
                                         ▼
                            ┌────────────────────────┐
                            │     ModelSelector      │
                            │ (Evaluation rankings)  │
                            └────────────┬───────────┘
                                         │ Best Models for:
                                         │ • direction
                                         │ • market_moving
                                         │ • impact_strength
                                         │ • confidence
                                         ▼
                            ┌────────────────────────┐
                            │ FinalPredictionEngine  │
                            │ (Pure Forward Infer)   │
                            └────────────┬───────────┘
                                         │ Raw Class Probs
                                         ▼
 ┌──────────────────────┐   ┌────────────────────────┐
 │ Anticipation Score   ├──►│     DecisionEngine     │
 │ (Diagnostic Layer)   │   │ (Contextual Reasoning) │
 └──────────────────────┘   └────────────┬───────────┘
                                         │ Structured PredictionRecord
                                         ▼
                            ┌────────────────────────┐
                            │  PredictionRepository  │
                            │   (data/predictions/)  │
                            └────────────────────────┘
```

### Key Components
1. **ModelSelector (`prediction/model_selector.py`)**:
   - Queries `EvaluationRepository` (`comparison_report.json` and `metrics.json`) to select the highest-performing model per prediction target using Macro F1, Balanced Accuracy, MCC, ROC-AUC, and calibration error.
2. **PredictionValidator (`prediction/validator.py`)**:
   - Strictly validates feature inputs, required column presence, NaN/Inf absence, dimension alignment, and categorical data types prior to inference.
   - Generates persistent `PredictionValidationReport` records under `data/predictions/reports/`.
3. **DecisionEngine (`prediction/decision_engine.py`)**:
   - Strictly decouples statistical model predictions from contextual qualitative interpretations.
   - Integrates Task 6.5 anticipation classifications to flag potential priced-in market reactions without claiming insider leakage.
   - Synthesizes risk indicators, expected abnormal return magnitude estimates, and mandatory compliance disclaimers.
4. **FinalPredictionEngine (`prediction/engine.py`)**:
   - Master orchestrator with zero retraining.
   - Implements version-based incremental caching (`model_version` + `feature_version`) and `--force-refresh` overrides.
5. **PredictionRepository (`storage/prediction_repository.py`)**:
   - Persists deterministic records (`pred_<bill_id>_<company_isin>_<window>.json`) and validation reports under `data/predictions/`.
6. **PredictionService & CLI (`services/prediction.py` & `main.py`)**:
   - `python main.py generate-predictions` with granular filters (`--year`, `--bill-id`, `--company-isin`, `--event-window`, `--force-refresh`).

---

## Decision Support & Risk Scoring Engine (Task 7.2)

### Overview
The Decision Support & Risk Scoring Engine translates raw multi-target prediction outputs (`PredictionRecord`) and diagnostic pre-event anticipation metrics (`AnticipationScore`) into tailored, qualitative perspectives for distinct stakeholders alongside deterministic composite risk scores.

### Architectural Workflow

```
                                  Task 7.1 Prediction
                                   (PredictionRecord)
                                          │
                                          ▼
                             ┌────────────────────────┐
                             │ DecisionSupportValidator│
                             │ (Input & Entity Audit) │
                             └────────────┬───────────┘
                                          │ Validated Inputs
                                          ▼
        ┌─────────────────────────────────┴─────────────────────────────────┐
        │                                                                   │
        ▼                                                                   ▼
┌────────────────────────┐                                     ┌─────────────────────────┐
│       RiskScorer       │                                     │  StakeholderSynthesizer │
│ (Deterministic Formulas│                                     │ (Multi-Perspective View)│
│  & Clamped Aggregators)│                                     └────────────┬────────────┘
└───────────┬────────────┘                                                  │
            │                                                               │
            │ • Direction Impact Score                                      │ • Investor Perspective
            │ • Composite Risk Score                                        │ • Business Perspective
            │ • Pricing-In Category                                         │ • General Public Perspective
            │                                                               │
            └─────────────────────────────┬─────────────────────────────────┘
                                          ▼
                             ┌────────────────────────┐
                             │ DecisionSupportRecord  │
                             │ (Canonical Data Model) │
                             └────────────┬───────────┘
                                          │
                                          ▼
                             ┌────────────────────────┐
                             │   DecisionRepository   │
                             │(data/decision_support/)│
                             └────────────────────────┘
```

### Core Subsystems
1. **Deterministic Risk & Impact Scoring (`decision_support/risk_scorer.py`)**:
   - **Direction Impact Score**: Blends directional polarity probability, market-moving likelihood, impact magnitude probability, and model confidence, attenuated by pre-event anticipation:
     $$\text{ImpactScore} = \left( w_{\text{dir}} \cdot P(\text{Dir}) + w_{\text{strength}} \cdot \sum P(\text{Level}) \cdot v_{\text{Level}} \right) \cdot P(\text{MM}) \cdot C_{\text{scalar}} \cdot (1 - \delta \cdot A_{\text{score}})$$
   - **Composite Decision Risk Score**: Measures uncertainty, pre-event pricing-in risk, tail risk, and directional ambiguity:
     $$\text{RiskScore} = w_{\text{uncert}}(1 - C_{\text{scalar}}) + w_{\text{anticip}} A_{\text{score}} + w_{\text{tail}} P(\text{Tail}) \cdot P(\text{MM}) + w_{\text{conf}} (1 - |P(\text{Pos}) - P(\text{Neg})|)$$
   - **Categorization**: Deterministically bins impact and risk scores into `VERY_LOW`, `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`.

2. **Multi-Perspective Synthesis (`decision_support/stakeholder_synthesizer.py`)**:
   - **Investor View**: Directional probability distribution, market-moving likelihood tier, magnitude expectation, and pricing-in interpretation (*"potential positive impact"*, *"elevated market-moving probability"*).
   - **Business View**: Company sector/industry context, sponsoring ministry, knowledge-layer mapping alignment score, and strategic operational implications.
   - **General Public View**: Plain-English, jargon-free bill objectives explaining societal and regulatory intent.
   - **Compliance & Vocabulary Safety**: Strictly avoids deterministic certainty guarantees (*"will rise/fall"*) or illegal phrasing (*"insider trading"*). Integrates standard quantitative research disclaimers.

3. **Validation & Persistence (`decision_support/validator.py` & `storage/decision_repository.py`)**:
   - **DecisionValidationReport**: Persistent audit log under `data/decision_support/reports/`.
   - **DecisionSupportRecord**: Stored under `data/decision_support/dec_<bill_id>_<company_isin>_<event_window>.json`.
   - **Incremental Execution**: Skips records when `model_version`, `feature_version`, and `decision_version` match disk cache unless `--force-refresh` is active.

4. **Service & CLI (`services/decision_service.py` & `main.py`)**:
   - CLI: `python main.py generate-decision-support --year <YYYY> --bill-id <ID> --company-isin <ISIN> --event-window <WIN> [--force-refresh]`.

---

## Stakeholder Reporting & Presentation Layer (Task 7.3)

### Overview
The Stakeholder Reporting & Presentation Layer transforms the verified `DecisionSupportRecord` artefacts (Task 7.2) into structured, readable reports for three distinct audiences: **Investors**, **Businesses / Corporates**, and the **General Public**. It is a pure presentation layer that enforces compliance safety and provides multi-format serialisation (JSON, Markdown, CSV) and bill/company aggregation.

### Architectural Workflow

```
                               DecisionSupportRecord
                               (Task 7.2 Artefact)
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │     ReportValidator     │
                          │(Format & Integrity Audit│
                          └────────────┬────────────┘
                                       │ Validated Records
                                       ▼
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│    InvestorReporter     │ │    BusinessReporter     │ │     PublicReporter      │
│(Probabilistic, Pricing- │ │(Regulatory, Compliance, │ │(Plain-English, Jargon-  │
│ in, Model Factors View) │ │ & Operational Context)  │ │ Free Explanations View) │
└────────────┬────────────┘ └────────────┬────────────┘ └────────────┬────────────┘
             │                           │                           │
             └───────────────────────────┼───────────────────────────┘
                                         ▼
                               ┌───────────────────┐
                               │ StakeholderReport │
                               └─────────┬─────────┘
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        │                                                                 │
        ▼                                                                 ▼
┌─────────────────────────┐                                     ┌─────────────────────────┐
│     BillAggregator      │                                     │    CompanyAggregator    │
│(Bill → Companies View)  │                                     │(Company → Bills View)   │
└────────────┬────────────┘                                     └────────────┬────────────┘
             │                                                               │
             ▼                                                               ▼
┌─────────────────────────┐                                     ┌─────────────────────────┐
│     BillLevelReport     │                                     │   CompanyLevelReport    │
└────────────┬────────────┘                                     └────────────┬────────────┘
             │                                                               │
             └───────────────────────────┬───────────────────────────────────┘
                                         ▼
                               ┌───────────────────┐
                               │  ReportFormatter  │
                               │(JSON/Markdown/CSV)│
                               └─────────┬─────────┘
                                         │
                                         ▼
                               ┌───────────────────┐
                               │ ReportRepository  │
                               │  (data/reports/)  │
                               └───────────────────┘
```

### Core Subsystems
1. **Audience-Tailored Report Builders**:
   - **`InvestorReporter`**: Generates probabilistic summaries (*"potential positive impact"*, *"82% directional probability"*, *"75% market-moving likelihood"*), model factors (SHAP features), pricing-in analysis, confidence distribution, and quantitative research disclaimers.
   - **`BusinessReporter`**: Focuses on regulatory domains, operational headwinds/tailwinds, administrative burdens, compliance exposure, and market awareness.
   - **`PublicReporter`**: Generates plain-English summaries (*"what the bill does"*, *"why it matters"*, accessible confidence explanations) free of statistical or ML jargon.

2. **Aggregation Engines**:
   - **`BillAggregator`**: Computes deterministic bill-level statistics across all mapped companies: total companies, direction counts, market-moving count ($\ge 50\%$), high-impact count, arithmetic mean impact score, arithmetic mean risk score, anticipation distribution, and unique affected sectors. Avoids averaging raw probability distributions.
   - **`CompanyAggregator`**: Summarises all legislative exposures for a single company across multiple bills (Company $\rightarrow$ Bills view).

3. **Validation & Persistence (`ReportValidator` & `ReportRepository`)**:
   - Stores artefacts deterministically under `data/reports/`:
     - `investor/`: `rpt_<bill>_<isin>_<window>_investor.json`
     - `business/`: `rpt_<bill>_<isin>_<window>_business.json`
     - `public/`: `rpt_<bill>_<isin>_<window>_public.json`
     - `bill_reports/`: `bill_rpt_<bill_id>.json`
     - `company_reports/`: `co_rpt_<isin>.json`
     - `validation/`: `val_rpt_<report_id>.json`
   - Incremental execution skips regeneration if upstream `decision_version` is unchanged.

4. **Formatting & CLI (`ReportFormatter`, `ReportingService`, `main.py`)**:
   - Serialises to JSON, human-readable Markdown, or tabular CSV.
   - CLI: `python main.py generate-reports [--bill-id ID] [--company-isin ISIN] [--stakeholder {investor,business,public}] [--format {json,markdown,csv}] [--force-refresh] [--generate-bill-report] [--generate-company-report]`.

---

## Task 7.4 — Interactive Dashboard & Decision-Support Interface

### Overview
The **Interactive Dashboard** (`dashboard/`) is a read-only presentation and decision-support layer built with Streamlit and Plotly. It reads verified outputs from upstream tasks without recalculating predictions, retraining models, or altering storage datasets.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Interactive Dashboard Architecture                   │
│                               (Task 7.4)                               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌───────────────────────┐                               ┌───────────────────────┐
│     Scope Service     │                               │ DashboardDataService  │
│ (Reconcile Provenance)│                               │ (Cached Memory Store) │
└───────────┬───────────┘                               └───────────┬───────────┘
            │                                                       │
            │ Scope Diagnostic                                      │ Reads Repositories
            ▼                                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Multi-Criteria Filter Engine                       │
│     (Bill, Company, Sector, Ministry, Risk, Direction, Anticipation)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌─────────────────────────────────────────┐     ┌─────────────────────────────────────────┐
│           Exploratory Views             │     │         Verification Views              │
│  - Landing Page (Global KPIs)           │     │  - Risk Overview (Stats & Matrix)       │
│  - Bill Explorer (Dossier & Aggregates) │     │  - Anticipation (Diffusion Tiers)       │
│  - Company Explorer (Risk & Exposure)   │     │  - Explainability (Task 6.3 SHAP)       │
│  - Investor View (Compliant Research)   │     │  - Backtesting (Task 6.4 Curves & F1)   │
│  - Business View (Regulatory & Ops)     │     │  - Methodology (Architecture Blueprint) │
│  - Public View (Plain-English Context)  │     │                                         │
└─────────────────────────────────────────┘     └─────────────────────────────────────────┘
```

### Core Components
1. **Scope Reconciliation & Diagnostic (`ScopeService`)**:
   - Reconciles the production universe (20 bills $\times$ 47 companies $\times$ 5 windows = 4,700 decisions) against the 22 bills and 50 companies in the raw repository, documenting why PRS briefs (`key-issues-and-analysis`) and stubs (`service-bill`) as well as unmapped companies were excluded from ML training.
   - Explains that the Task 7.3 runtime observation of 50 decision records / 18 companies represented an intentional testing sample cohort, while production persistence maintains 100% full parity (4,700 records).

2. **Unified Data Service (`DashboardDataService`)**:
   - Central read-only interface querying `BillRepository`, `CompanyRepository`, `DecisionRepository`, `ReportRepository`, `ExplainabilityRepository`, and `BacktestRepository`.
   - Assembles an enriched Pandas DataFrame in memory once and caches it, enabling instant filtering (<1ms) without re-reading 4,700 files.

3. **Multi-Criteria Filter Engine (`FilterEngine`)**:
   - Supports composable filtering across 10 dimensions: bill, company, sector, ministry, policy domain, risk category, predicted direction, market-moving flag, anticipation tier, and event window.

4. **Institutional Compliance Invariants**:
   - Strict prohibition against trade-execution terms (*"buy"*, *"sell"*, *"guaranteed return"*, *"stock will rise"*, *"stock will fall"*).
   - Mandatory legal disclaimers stating that anticipation evidence does not establish insider trading, unlawful information leakage, or causality.
   - Strict separation between **Model Performance** (out-of-sample statistical metrics) and **Historical Strategy Performance** (hypothetical portfolio simulation).





