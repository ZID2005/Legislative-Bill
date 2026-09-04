# Methodology

## Overview

The prediction pipeline uses a multi-stage methodology that combines
**natural language processing** of legislative text with **quantitative
finance** techniques to produce market impact predictions.

---

## Stage 1: Ingest, Validate, and Extract (Corpus Generation)

Before performing NLP, raw documents are parsed and validated:
1. **Document Download**: Streaming chunked retrieval with Range Request support for partial-file resume.
2. **Multi-Engine Extraction**: Converts PDFs using `pdfplumber` layout-preservation algorithms as primary, with a `PyPDF2` parser fallback.
3. **Quality Filtering**: Blocks low-quality scanned image PDFs (<50 characters) to prevent database noise.
4. **Text Normalization & Deduplication**:
   - standardizes character encodings to NFKC.
   - removes page numbers and headers/footers repeated on $>50\%$ of pages.

## Stage 2: Bill Text Understanding (NLP)

### Approach
We treat each bill as a structured legal document and extract:
1. **Key provisions** — clauses most likely to have economic impact
2. **Entities** — sectors, companies, commodities, and regulatory bodies mentioned
3. **Sentiment** — whether provisions create obligations, relaxations, or restrictions
4. **Scope** — which industries and activities are covered

### Models
- **Primary**: Legal-RoBERTa (fine-tuned on Indian legal text)
- **Supplementary**: Fine-tuned FinBERT (sentiment)
- **Summarisation**: Mistral 7B / Llama 3 / abstract LLM interface (Groq)

---

## Stage 2: Sector & Company Mapping

### Phase A — Rule-Based Knowledge Generation (Task 1A.5)
A deterministic rule engine converts legislative texts into structured domain knowledge.
1. **Ministry and Category Lookups**: Canonical sponsoring ministry names and primary sector mappings are resolved using standard mapping catalogs (`ministry_mappings.csv` and `ministry_sector.csv`).
2. **Hierarchy-Based Taxonomy Traversal**: Uses the parent-to-child relations defined in `taxonomy_hierarchy.csv` to traverse downstream from canonical ministry/primary sector nodes.
3. **Word Boundary Keyword Frequency Checks**: Counts exact word occurrences (avoiding substring match errors like matching "oil" inside "boilers") to activate secondary sectors and policy/economic domains.
4. **Geographic Scope and Bill Type Categorization**: Extracts scopes (e.g. State-specific vs. National) and bill types based on regex/keyword lookups.
5. **Confidence Score Calculation**: Assigns confidence points programmatically based on the strength and provenance of mappings (e.g., raw ministry matching, category matching, keyword frequency, regulatory authority presence).

### Phase B — Deterministic Bill-to-Company Mapping (Task 2.3)
Once the knowledge record has been generated for a bill, the mapping engine maps the bill to listed companies in the Company Intelligence database using a scoring system:
1. **Base Sector Match**:
   - **Primary Sector**: `0.50` base confidence if the company's sector matches the bill's primary sector.
   - **Secondary Sector**: `0.30` base confidence if the company's sector matches one of the bill's secondary sectors.
2. **Deterministic Confidence Boosts**:
   - **Industry Match (`+0.20`)**: Applied if the company's industry matches or is mentioned inside the bill title, summary, or corpus text, or is present in the bill's keywords. The match is plural-tolerant.
   - **Sub-industry Match (`+0.10`)**: Applied if the industry did not match, but the company's sub-industry matches or is mentioned inside the bill's texts/keywords.
   - **Sponsoring Ministry Mappings (`+0.20`)**: Applied if the company's sector is regulated by the sponsoring ministry (using `knowledge/ministry_sector.csv` mapping).
   - **Direct Company Name/Alias Mention (`+0.10`)**: Applied if the company's normalized name (excluding suffixes like "Limited", "Ltd", etc.) or any of its aliases are explicitly mentioned in the bill text.
3. **Capping & Rounding**:
   - Total mapping confidence is capped at `1.0` and rounded to two decimal places.
   - Candidate companies are sorted by confidence descending, then by name ascending.

### Phase C — Embedding-Based Mapping (Future Stage)
Bill clause embeddings will be compared against sector-description and company-profile embeddings using cosine similarity to capture semantic similarity beyond exact keywords and taxonomy lookups.


---

## Stage 3: Ground-Truth Label Generation (Event Study)

The **market model event study** methodology (MacKinlay, 1997) is used to
compute abnormal returns around bill introduction dates.

### Return Calculations
To capture asset price dynamics robustly, the engine computes both:
1. **Daily Log Return**: $R_{i,t} = \ln(Close_{i,t} / Close_{i,t-1})$
2. **Simple Return**: $R^s_{i,t} = (Close_{i,t} - Close_{i,t-1}) / Close_{i,t-1}$

All returns are computed using a 45-day leading date buffer (to ensure returns are populated from the very first day of the window).

### Estimation Window
The estimation window boundaries are configurable and default to:
- **Start**: $T = -120$ trading days relative to the bill introduction date.
- **End**: $T = -10$ trading days relative to the bill introduction date.

The window count resolves actual trading days of the benchmark calendar, bypassing non-trading holidays and weekends.

#### Advantages of Expanded Historical Coverage (2014 - Present)
Expanding the historical stock price database back to **01 January 2014** provides two key methodological enhancements:
1. **Unbiased Estimation for Early Events**: For bills introduced in the early years of the dataset (e.g., 2014 to 2016), having a price history starting in 2014 ensures that the full pre-event estimation window ($T = -120$ to $T = -10$ trading days) is completely populated. Without this history, early bills would fail the validator check requiring at least 60 overlapping trading observations, leading to data deletion or parameter bias.
2. **Backtesting Validity & Out-of-Sample Performance**: Longitudinal backtests across multiple macro-economic cycles (2014–2026) are made possible. Quantitative models can be trained on earlier events (e.g., 2014–2020) and tested out-of-sample on later events (e.g., 2021–2026) with correct market model expected returns baselines.

### Ordinary Least Squares (OLS) Regression
We estimate the parameters of the classical linear market model:

```
R_it = α_i + β_i × R_mt + ε_it
```

Where:
- `R_it` = return of stock `i` on day `t`
- `R_mt` = return of market index (Nifty 50) on day `t`
- `α_i`, `β_i` = estimated parameters from the estimation window
- `ε_it` = residual error term on day `t`

The following metrics are computed and persisted:
- **Beta ($\beta$)**: Covariance of asset and benchmark returns divided by benchmark variance: $\beta = \frac{\text{Cov}(R_i, R_m)}{\text{Var}(R_m)}$.
- **Alpha ($\alpha$)**: Asset return intercept: $\alpha = \bar{R}_i - \beta \bar{R}_m$.
- **Residual Variance ($\sigma_\varepsilon^2$)**: Computed using $N-2$ degrees of freedom to adjust for parameter estimation bias.
- **R-squared ($R^2$)**: Coefficient of determination measuring model goodness-of-fit.
- **Standard Error of Regression ($\sigma_\varepsilon$)**: Residual standard deviation.
- **Beta Standard Error ($\text{SE}(\beta)$)**: $\sqrt{\sigma_\varepsilon^2 / \sum (R_{m,t} - \bar{R}_m)^2}$.
- **Alpha Standard Error ($\text{SE}(\alpha)$)**: $\sigma_\varepsilon \sqrt{1/N + \bar{R}_m^2 / \sum (R_{m,t} - \bar{R}_m)^2}$.
- **Observations ($N$)**: The number of overlapping trading days used.

### Ingestion Validation Rules
To prevent regression bias and numerical instability, the engine rejects the estimation if:
1. **Fewer than 60 observations** exist in the overlapping window.
2. **Benchmark return variance is near-zero** (< $10^{-9}$), which makes OLS regression mathematically singular.
3. **Company or benchmark price data is missing** or empty.
4. **The bill lacks an introduction date**.

### Event Study Engine calculations

The **Advanced Event Study Engine** computes event-study metrics for each Bill–Company pair across multiple configurable event windows.

#### Expected Return
The expected stock return is calculated for each trading day in the event window using the OLS Market Model parameters:
$$E(R_{i,t}) = \alpha_i + \beta_i R_{m,t}$$

Where:
- $\alpha_i$ and $\beta_i$ are the baseline OLS parameters retrieved from the `MarketModelRepository`.
- $R_{m,t}$ is the observed benchmark daily log-return (NIFTY 50) on day $t$.

#### Actual Return
The observed daily stock log-return $R_{i,t}$ is loaded from the `MarketRepository` for each trading day $t$ in the event window.

#### Abnormal Return (AR)
For each trading day in the event window, the abnormal return is the difference between the actual and expected return:
$$AR_{i,t} = R_{i,t} - E(R_{i,t})$$

#### Cumulative Abnormal Return (CAR)
- **Running CAR**: The cumulative abnormal return at day $t$ in the event window, computed as:
  $$CAR_{i,t} = \sum_{j=\text{start\_idx}}^{t} AR_{i,j}$$
- **Final CAR**: The total cumulative abnormal return at the end of the window.

#### Configurable Event Windows
The engine computes returns for multiple configurable windows:
- **`[-1,+1]`**: Immediate announcement effect.
- **`[-3,+3]`**: Extended announcement window.
- **`[-5,+5]`**: Medium short-term window.
- **`[-5,+10]`**: Post-announcement drift monitoring.
- **`[-10,+10]`**: Broad-term event window.

#### Quality Metrics
For each event study calculation, the following metrics are compiled:
- **Average AR**: Mean Daily Abnormal Return across the event window.
- **Maximum AR / Minimum AR**: The highest and lowest Daily Abnormal Returns observed.
- **Peak AR Day**: The relative trading day offset (e.g., `-1`, `0`, `+3`) where Daily AR is maximized.
- **Peak CAR Day**: The relative trading day offset where the running CAR peaks.
- **Observation Count**: The count of valid trading days successfully analyzed in the window.

#### Validation Rules
Event studies are rejected (generating `ValidationReport` objects and skipped/failed statistics) if:
- **Market Model missing**: No estimation record exists for the Bill–Company pair.
- **Company prices missing**: No historical daily price records exist for the company's resolved ticker.
- **Benchmark prices missing**: No benchmark history is available.
- **Event window incomplete**: The window boundaries lie outside the available trading history.
- **Less than required observations**: The company has fewer active trading days in the window than the expected window size (indicating trading halts or missing data).

### Stage 3B: Statistical Significance Testing

The **Statistical Significance Engine** evaluates whether the Cumulative Abnormal Returns (CAR) generated during the event window are statistically different from zero. This serves as the authoritative gate for downstream labeling and machine learning tasks.

#### Hypothesis Testing
- **Null Hypothesis ($H_0$)**: $CAR = 0$ (The legislative event has no abnormal impact on stock returns).
- **Alternative Hypothesis ($H_1$)**: $CAR \neq 0$ (The legislative event has a statistically significant abnormal impact on stock returns).

#### Statistical Metrics
1. **CAR Variance ($Var(CAR)$)**: Calculated under the assumption of independent daily abnormal returns:
   $$Var(CAR) = N \cdot \sigma^2_\epsilon$$
   Where $N$ is the number of trading days in the event window (`observation_count`) and $\sigma^2_\epsilon$ is the baseline market model's `residual_variance`.
2. **CAR Standard Error ($SE(CAR)$)**: The standard deviation of the CAR:
   $$SE(CAR) = \sqrt{Var(CAR)} = \sqrt{N} \cdot \sigma_\epsilon$$
   Where $\sigma_\epsilon$ is the standard error of the OLS regression.
3. **t-statistic**: Standardized score of the abnormal return:
   $$t = \frac{CAR}{SE(CAR)}$$
4. **Two-Tailed p-value**: Calculated using the Student's t-distribution:
   $$p = 2 \cdot (1 - F(|t|))$$
   Where $F$ is the CDF of Student's t-distribution with $df = M - 2$ degrees of freedom ($M$ being the `n_observations` in the estimation window).
5. **95% Confidence Interval**:
   $$[CAR - t_{crit} \cdot SE(CAR), CAR + t_{crit} \cdot SE(CAR)]$$
   Where $t_{crit}$ is the critical t-value for a two-tailed test at $\alpha = 0.05$ with $df$ degrees of freedom.

#### Decision Rules & Significance Levels
A result is flagged as **Significant** if:
- $|t| > t_{threshold}$ (default: $1.96$)
- $p < \alpha_{threshold}$ (default: $0.05$)

Significance levels are categorized as:
- **1% Level**: $p < 0.01$
- **5% Level**: $p < 0.05$
- **10% Level**: $p < 0.10$
- **Not Significant**: $p \ge 0.10$

#### Effect Size
Classifies the magnitude of the market impact using configurable CAR thresholds:
- **Large**: $|CAR| \ge \text{Large Threshold}$ (default: $0.05$ or 5%)
- **Medium**: $\text{Medium Threshold} \le |CAR| < \text{Large Threshold}$ (default: $0.02$ or 2%)
- **Small**: $|CAR| < \text{Medium Threshold}$ (default: $0.02$)

#### Validation Rules
Statistical calculations are rejected (generating `ValidationReport` objects) if:
- **CAR missing**: CAR value is None or NaN.
- **Variance invalid**: Variance is negative, NaN, or infinite.
- **Standard Error equals zero**: Standard error is zero or negative (prevents division by zero).
- **Degrees of freedom invalid**: $df \le 0$ (requires at least 3 estimation window observations).

---

## Stage 4: Feature Engineering

Features are split into four groups:

1. **Text features**: FinBERT/Legal-RoBERTa embeddings (768-dim)
2. **Bill features**: type, house, government majority, age
3. **Market context**: index return, sector return, VIX at event date
4. **Company features**: log market cap, beta, sector one-hot

---

## Stage 5: Model Training

### Architecture
- **Primary model**: LightGBM (gradient-boosted trees)
  - Handles mixed feature types well
  - Robust to irrelevant features
  - Fast inference (< 10ms per prediction)
- **Text model**: Fine-tuned FinBERT (text-only baseline)
- **Ensemble**: Weighted average of LightGBM and FinBERT outputs

### Evaluation

All models are evaluated using **time-based cross-validation** to prevent
data leakage (future bills must not be in the training set).

| Metric | Task |
|--------|------|
| AUROC, F1-macro | Classification (positive/negative/neutral) |
| MAE, RMSE, Pearson ρ | Regression (CAR prediction) |

---

## Stage 5: Label Generation (Task 4.4)

### Ground Truth Philosophy

Ground-truth labels are derived exclusively from **statistically validated
historical market reactions** — not analyst opinions, sentiment scores, or
ML predictions.  This guarantees:

- **Objectivity**: Labels are fully quantitative and free from subjectivity
- **Reproducibility**: Given identical inputs, labels are always identical
- **Auditability**: Every label carries a `decision_reason` and `calculation_timestamp`

### Label Derivation

Each `StatisticalResult` (Task 4.3) generates **four labels** simultaneously:

#### 1. Direction Label — `DirectionLabel`
Derived from CAR sign and statistical significance:

| Label | Condition |
|-------|-----------|
| `POSITIVE` | CAR > +threshold **AND** significant |
| `NEGATIVE` | CAR < −threshold **AND** significant |
| `NEUTRAL`  | Anything else (insignificant or small |CAR|) |

*Default threshold: ±2% (configurable via `LABEL_POSITIVE_CAR_THRESHOLD`,
`LABEL_NEGATIVE_CAR_THRESHOLD`).*

The significance gate (`significant == True`) ensures the label reflects
a genuine market reaction, not noise.  This avoids assigning POSITIVE/NEGATIVE
labels to random price fluctuations.

#### 2. Market-Moving Label — `market_moving`
Binary flag derived from significance AND magnitude:

```
market_moving = significant AND |CAR| > LABEL_MARKET_MOVING_CAR_THRESHOLD
```

*Default threshold: 2% absolute CAR.*

This flag identifies events with both statistical credibility **and** economic
materiality — the subset most relevant for investor and corporate decision-making.

#### 3. Impact Strength — `ImpactStrength`
Ordinal magnitude label based solely on |CAR| (direction-agnostic):

| Strength | Condition | Rationale |
|----------|-----------|-----------|
| `LOW` | `|CAR| < 1%` | Below typical daily noise floor |
| `MEDIUM` | `1% ≤ |CAR| < 3%` | Economically meaningful but moderate |
| `HIGH` | `3% ≤ |CAR| < 6%` | Strong legislative market reaction |
| `VERY_HIGH` | `|CAR| ≥ 6%` | Exceptional, event-study-confirming reaction |

*All boundaries are configurable via settings.*

#### 4. Confidence Label — `ConfidenceLabel`
Composite label combining p-value precision and Cohen's d effect size:

| Confidence | Condition |
|------------|-----------|
| `HIGH` | `p_value ≤ 0.01` **AND** `effect_size == "Large"` |
| `MEDIUM` | `p_value ≤ 0.05` **OR** `effect_size ∈ {Medium, Large}` |
| `LOW` | Neither condition met |

The composite design rewards convergent evidence: a small p-value alone may
arise from large sample sizes with trivial effects; a large effect size alone
may be underpowered.  Only when both dimensions agree do we assign `HIGH` confidence.

### Validation and Rejection

Labels are rejected (producing a `LabelValidationReport`) when:
1. The source `StatisticalResult` is unavailable
2. CAR is `NaN`, `+Inf`, or `−Inf`
3. p-value is `NaN`, `+Inf`, or `−Inf`

Rejected records are **logged and returned to the caller** but never persisted
as `LabelRecord` objects, preserving the integrity of the ground-truth dataset.

### Incremental Execution

The label generation pipeline supports **incremental runs**:
- Default mode skips any `(bill, company, window)` triple already present
  in the `LabelRepository`
- `--force-refresh` mode regenerates all labels, overwriting existing records
- This allows efficient incremental updates as new bills are processed

---

## References

1. MacKinlay, A.C. (1997). *Event Studies in Economics and Finance*.
   Journal of Economic Literature, 35(1), 13–39.
2. Huang, A. et al. (2022). *FinBERT: A Large Language Model for Extracting
   Information from Financial Text*. Contemporary Accounting Research.
3. Chalkidis, I. et al. (2020). *Legal-BERT: The Muppets straight out of Law School*.
   EMNLP Findings.

---

## Stage 4B: Feature Engineering (Task 5.1)

### Objective

Convert all structured research outputs (bill metadata, company data, market model parameters, event study metrics, statistical tests, and ground-truth labels) into a single **unified ML feature table** stored in Apache Parquet.

### Design Principles

| Principle | Implementation |
|---|---|
| **Label-anchored enumeration** | Label repository is the authoritative join key source; every row is guaranteed to have ground-truth labels |
| **Fault tolerance** | Missing upstream records produce WARNING-level validation reports; the record is retained with partial features |
| **Strict rejection** | NaN numeric values or missing labels cause ERROR-level rejection; the row is excluded |
| **Incremental rebuild** | O(1) existence check via `index.json`; unchanged rows skipped on re-runs |
| **Schema versioning** | Every row carries `feature_version = "1.0"` for future drift detection |

### Feature Categories

#### Legislative Features
Sourced from `Bill` and `KnowledgeRecord` repositories.

| Feature | Type | Description |
|---|---|---|
| `bill_id` | str | Unique slug identifier |
| `bill_title` | str | Official full title |
| `bill_type` | str | e.g. "Finance Bill", "Ordinary Bill" |
| `ministry` | str | Sponsoring ministry |
| `department` | str | Responsible department |
| `policy_domain` | str | e.g. "Fiscal Policy", "Banking Regulation" |
| `economic_domain` | str | e.g. "Finance", "Agriculture" |
| `primary_sector` | str | Primary NSE sector affected |
| `secondary_sectors` | list[str] | Additional sectors (stored as JSON in Parquet) |
| `regulatory_authority` | str | e.g. "RBI", "SEBI", "IRDAI" |
| `geographic_scope` | str | "National", "State", or specific region |
| `introduction_date` | str | ISO-8601 date of bill introduction |

#### Company Features
Sourced from `Company` repository (NSE/BSE master).

| Feature | Type | Description |
|---|---|---|
| `company_name` | str | Official registered name |
| `nse_symbol` | str | NSE ticker (e.g. "HDFCBANK") |
| `isin` | str | International Securities Identification Number |
| `company_sector` | str | NSE/SEBI sector classification |
| `industry` | str | Industry group |
| `sub_industry` | str | Sub-industry classification |
| `market_cap_category` | str | "large_cap" / "mid_cap" / "small_cap" |
| `hq_state` | str | State of registered headquarters |

#### Financial Features (Market Model)
Sourced from `MarketModelRecord`. Represent the OLS regression parameters from the estimation window (pre-event baseline).

| Feature | Type | Description |
|---|---|---|
| `alpha` | float | Intercept — stock-specific drift |
| `beta` | float | Market sensitivity (CAPM beta) |
| `r_squared` | float | Regression fit quality |
| `residual_variance` | float | Unexplained variance (idiosyncratic risk) |
| `observation_count` | int | Number of trading days in estimation window |

#### Event Study Features
Sourced from `EventStudyRecord`. Represent the stock's response to the legislative event.

| Feature | Type | Description |
|---|---|---|
| `event_window` | str | Window specification e.g. "[-5,+5]" |
| `final_car` | float | Cumulative Abnormal Return at end of window |
| `avg_ar` | float | Mean daily Abnormal Return |
| `max_ar` | float | Peak positive daily AR |
| `min_ar` | float | Trough negative daily AR |
| `peak_ar_day` | int | Relative offset day of maximum AR |
| `peak_car_day` | int | Relative offset day of maximum running CAR |

#### Statistical Features
Sourced from `StatisticalResult`. Represent hypothesis-test outputs.

| Feature | Type | Description |
|---|---|---|
| `t_statistic` | float | Student's t-statistic for CAR |
| `p_value` | float | Two-tailed p-value |
| `confidence_interval_lower` | float | Lower bound of 95% CI |
| `confidence_interval_upper` | float | Upper bound of 95% CI |
| `significance_level` | str | "1%", "5%", "10%", "Not Significant" |
| `significant_flag` | bool | True if statistically significant |
| `effect_size` | str | "Small", "Medium", "Large" (Cohen's d) |

#### Target Labels (Ground Truth)
Sourced from `LabelRecord`. These are the **supervised learning targets**.

| Label | Type | Values | Description |
|---|---|---|---|
| `direction` | str | POSITIVE / NEGATIVE / NEUTRAL | Directional market impact |
| `market_moving` | bool | True / False | Whether the event triggered measurable price impact |
| `impact_strength` | str | LOW / MEDIUM / HIGH / VERY_HIGH | Magnitude of price impact |
| `confidence_label` | str | HIGH / MEDIUM / LOW | Composite statistical confidence |

### Master Dataset Storage

The feature table is stored in **Apache Parquet** (columnar format) under `data/features/`.

```
data/features/
    master_feature_dataset.parquet   ← primary storage (compressed columnar)
    master_feature_dataset.csv       ← optional flat export for inspection
    index.json                       ← record ID list for O(1) existence checks
```

Parquet is chosen because:
- Columnar reads are 5–50× faster than CSV for ML workflows
- Schema enforcement prevents silent type corruption
- Downstream NLP / embedding pipelines load the full table into pandas DataFrames

### Composite Primary Key

Each row is uniquely identified by:

```
record_id = f"{bill_id}|{company_isin}|{event_window}"
```

This three-part key ensures the same (Bill, Company) pair can have multiple rows for different event windows (e.g., `[-5,+5]`, `[-2,+2]`, `[0,+20]`).

### Validation Pipeline

```
For each LabelRecord:
    1. Assemble FeatureRecord from all upstream repositories
    2. Check: all 4 labels present?          → ERROR if not
    3. Check: NaN in any numeric feature?    → ERROR if yes
    4. Check: upstream data gaps?            → WARNING (retained)
    5. Write to FeatureRepository or emit FeatureValidationReport
```

### Incremental Rebuild Guarantee

This guarantees that re-running the pipeline after adding new bills never creates duplicate rows and only processes genuinely new data.

---

## Stage 8: NLP Embedding Engine (Task 5.2)

To capture semantic nuances of legislative text (such as regulatory severity, industry-specific prohibitions, and structural policy changes), the system uses pre-trained transformer embeddings. These represent a dense, continuous vector representation of the bill text that can be joined with structured financial, metadata, and event study features for downstream machine learning.

### Model Selections & Target Domains

The engine implements two models to capture distinct linguistic patterns:
1. **FinBERT** (`ProsusAI/finbert`):
   - **Linguistic Focus**: Financial and economic sentiment.
   - **Methodology**: Fine-tuned on the Financial PhraseBank corpus. It excels at detecting whether provisions represent expansionary opportunities, fiscal restrictions, or market risks.
2. **Legal-RoBERTa** (`lexlms/legal-roberta-base`):
   - **Linguistic Focus**: Formal legal syntax, statutory mandates, and regulatory powers.
   - **Methodology**: Pre-trained on diverse multinational legal corpora (including LeXFiles consisting of legislation, regulations, court decisions, and contracts). It is highly sensitive to legislative syntax and regulatory licensing terminology.

### Mathematical Tokenization & Sequence Limits

Given the standard Transformer token sequence limit ($L = 512$ tokens including special markers `[CLS]` and `[SEP]`), legislative texts must be truncated:
- Text is tokenized using the Hugging Face `AutoTokenizer` configured with a maximum length of 512.
- Sequence padding is applied for short summaries, and truncation is applied at the tail of long bill texts to prevent out-of-memory errors on inference hardware.
- Both tokenizers use subword tokenization (WordPiece for FinBERT and Byte-Pair Encoding for Legal-RoBERTa).

### Vector Pooling Strategies

Raw Transformer models output sequence token representations of shape $B \times L \times D$ (where $B$ is the batch size, $L$ is sequence length 512, and $D = 768$ is the embedding dimension). To collapse this 3D tensor into a 2D feature matrix of shape $B \times D$ (one vector per bill), two mathematical pooling strategies are implemented:

#### 1. Mean Pooling (`mean`)
Mean pooling calculates the element-wise average of all non-padding token representation vectors:

$$
\mathbf{e}_{\text{mean}} = \frac{\sum_{t=1}^{L} \mathbf{h}_t \cdot \mathbf{m}_t}{\sum_{t=1}^{L} \mathbf{m}_t}
$$

Where:
- $\mathbf{h}_t \in \mathbb{R}^{768}$ is the hidden representation vector at sequence index $t$.
- $\mathbf{m}_t \in \{0, 1\}$ is the attention mask value at index $t$ (0 for padding tokens, 1 for active text tokens).

Mean pooling is the default strategy because it summarizes the semantic content of the entire sequence evenly, preventing individual outlier words from dominating the embedding.

#### 2. CLS Pooling (`cls`)
CLS pooling extracts the hidden representation of the special classification token at sequence index 0:

$$
\mathbf{e}_{\text{cls}} = \mathbf{h}_0
$$

The `[CLS]` token acts as a summary representation of the entire text sequence, which is trained during pre-training to perform classification tasks.

### Multi-Tiered Data Validation

To prevent corrupt or invalid features from degrading downstream ML models, all generated embedding vectors undergo three validation checks:
1. **Dimensionality Audit**: Ensures the length of the vector is exactly $D = 768$.
2. **Zero-Length Trap**: Rejects empty vectors (length 0).
3. **Numeric Sanity Check**: Screens every coordinate in the vector to ensure it is a finite float, rejecting any vector containing:
   - `NaN` (Not a Number) values resulting from dividing by zero in mean pooling.
   - `Inf` (Infinity) values resulting from numeric overflows.

Any bill failing validation is logged to a persistent validation report (`embeddings_validation_report.json`), and is omitted from the embeddings matrix.

### High-Speed Binary Storage Layout

Embeddings are saved in a decoupled layout to optimize for different retrieval operations:
- **`embeddings_metadata.parquet`**: Columnar metadata (bill ID, model parameters, timestamp, token counts) to support quick filtering and verification in pandas.
- **`embeddings_matrix.npy`**: A single, contiguous binary NumPy array containing the float32 coordinates of the embeddings.

Because the NumPy matrix rows are perfectly aligned with the Parquet metadata rows, loading the text embeddings as inputs for deep neural networks or LightGBM models requires no string matching or slow serialization:
```python
import numpy as np
import pandas as pd

# O(1) direct binary memory map loading
metadata_df = pd.read_parquet("data/embeddings/finbert/embeddings_metadata.parquet")
embedding_vectors = np.load("data/embeddings/finbert/embeddings_matrix.npy")
```
This reduces dataset loading times during training from minutes to milliseconds.

---

## Stage 9: Feature Fusion Engine (Task 5.3)

Feature fusion is the final pipeline stage before training. It implements a quantitative merging architecture to combine structured tabular features and unstructured dense transformer representations.

### Mathematical Join and Alignment

Given:
- A structured feature table $\mathbf{X}_{\text{struct}} \in \mathbb{R}^{N \times P}$, where $N$ is the number of (Bill, Company, Event-Window) observations, and $P$ is the number of structured features.
- An embedding matrix $\mathbf{E} \in \mathbb{R}^{B \times D}$, where $B$ is the number of unique bills, and $D = 768$ is the embedding dimension.

The engine performs a left-outer relational join mapping each unique `bill_id` in $\mathbf{X}_{\text{struct}}$ to its corresponding dense representation in $\mathbf{E}$:

$$
\mathbf{X}_{\text{fused}} = \mathbf{X}_{\text{struct}} \bowtie_{\text{bill\_id}} \mathbf{E}
$$

For a given observation $i \in \{1, \dots, N\}$, if its associated bill has a valid embedding $\mathbf{e}_{\text{bill}(i)} \in \mathbb{R}^{768}$, the fused row becomes:

$$
\mathbf{x}_{\text{fused}, i} = \left[ \mathbf{x}_{\text{struct}, i} \parallel \mathbf{e}_{\text{bill}(i)} \right] \in \mathbb{R}^{P + D}
$$

Where $\parallel$ represents the vector concatenation operator.

### Six Data Fusion Strategies

To support ablation studies and model selection, six dataset strategies are supported:
1. **Structured Only**: $\mathbf{X}_{\text{structured}} = \mathbf{X}_{\text{struct}}$
2. **FinBERT Only**: $\mathbf{X}_{\text{finbert}} = \mathbf{E}_{\text{finbert}}$
3. **Legal Only**: $\mathbf{X}_{\text{legal}} = \mathbf{E}_{\text{legal}}$
4. **Structured + FinBERT**: $\mathbf{X}_{\text{struct-finbert}} = \left[ \mathbf{X}_{\text{struct}} \parallel \mathbf{E}_{\text{finbert}} \right]$
5. **Structured + Legal**: $\mathbf{X}_{\text{struct-legal}} = \left[ \mathbf{X}_{\text{struct}} \parallel \mathbf{E}_{\text{legal}} \right]$
6. **Hybrid**: $\mathbf{X}_{\text{hybrid}} = \left[ \mathbf{X}_{\text{struct}} \parallel \mathbf{E}_{\text{finbert}} \parallel \mathbf{E}_{\text{legal}} \right] \in \mathbb{R}^{N \times (P + 768 + 768)}$

### Strict Validation Auditing

Every generated dataset is subjected to a mathematical audit before persistence:
1. **Uniqueness Check**: Rejects the dataset if the composite key `record_id` is duplicated.
2. **Completeness Check**: Verifies that no embedding columns contain `NaN` or `None`.
3. **Mismatched Dimensions Check**: Verifies that the number of embedding columns is exactly 768.
4. **Key Integrity Checks**: Verifies that all `bill_id`s and `company_isin`s in the fused table exist in the upstream master feature dataset.

---

## Stage 10: ML Training Engine (Task 6.1)

### Overview

The training engine trains four independent supervised classifiers predicting the market impact of newly introduced legislative bills. It operates exclusively on features known **before or at bill introduction** to prevent target leakage.

### Target Leakage Prevention

Two datasets are produced before training:

| Dataset | Contents | Use |
|---------|----------|-----|
| data/ml/training_dataset.parquet | Pre-event features only | Model training exclusively |
| data/ml/research_dataset.parquet | Complete feature set | Academic analysis, evaluation |

Columns automatically stripped from the training dataset include: car, inal_car, vg_ar, max_ar, min_ar, peak_ar_day, peak_car_day, 	_statistic, p_value, significance_level, significant_flag, confidence_interval_lower, confidence_interval_upper, effect_size, and all r_day_* / car_day_* running series columns.

### Four Classifiers

| Target | Classes |
|--------|---------|
| direction | POSITIVE / NEUTRAL / NEGATIVE |
| market_moving | True / False |
| impact_strength | LOW / MEDIUM / HIGH / VERY_HIGH |
| confidence | LOW / MEDIUM / HIGH |

### Three Algorithms per Classifier

| Algorithm | Role | Library |
|-----------|------|---------|
| LightGBM | Primary | lightgbm |
| XGBoost | Secondary | xgboost |
| Random Forest | Baseline | scikit-learn |

This produces **12 trained models** total (4 targets x 3 model types).

### Chronological Validation

All validation is chronological. Random train/test splitting is never used.

sklearn.model_selection.TimeSeriesSplit(n_splits=5) is used exclusively. Each fold validation window always comes temporally after its training window.

### Hyperparameter Selection

GridSearchCV with TimeSeriesSplit(n_splits=3) scoring is used with a compact search grid (2 values per parameter). After selection, the final model is refit on the entire training dataset.

### Model Repository

Each trained model is stored under models/<target>/<model_type>/ containing model.pkl, preprocessor.pkl, features.json, metadata.json, and training_report.json.

### CLI Usage

`ash
python main.py train --mode structured
python main.py train --target direction --model-type lgbm
python main.py train --rebuild-datasets
`

---

## Stage 11: Model Evaluation Engine (Task 6.2)

### Overview
The Model Evaluation Engine provides a standardized, multi-model, multi-target testing workflow to assess the performance of all 12 classifiers. Model evaluation runs on the unified training dataset without retraining, loading the refit estimators directly from the Model Repository.

### Statistical & Classification Metrics
The engine calculates standard and class-imbalance-aware metrics to evaluate prediction quality:

1. **Overall Performance**:
   - **Accuracy**: Fraction of correct predictions.
   - **Balanced Accuracy**: Macro-average of recall scores per class (essential for imbalanced targets like market_moving).
   - **Matthews Correlation Coefficient (MCC)**: High-quality metric for binary/multiclass settings (-1 to +1).

2. **Error / Precision Measures**:
   - **Precision (Macro & Weighted)**: Agreement of predictions with ground truth.
   - **Recall (Macro & Weighted)**: Coverage of positive instances.
   - **F1-Score (Macro & Weighted)**: Harmonic mean of precision and recall.

3. **Probability & Confidence Measures**:
   - **ROC-AUC**: Area under the ROC curve. Calculated using One-vs-Rest (OvR) macro-averaged strategy for multi-class and standard binary calculation for market_moving.
   - **Log Loss**: Multi-class cross-entropy loss based on predicted probability distributions (predict_proba).

### Model Comparative Ranking
Algorithms are ranked per target using the macro F1-score as the primary ranking metric. The evaluation repository persists comparison_report.json identifying:
- **Best model**: Highest macro F1.
- **Worst model**: Lowest macro F1.
- **Average Performance**: Arithmetic mean of accuracy and macro F1 across all trained estimators for the target.

### Error Analysis & Diagnosis
For every target and algorithm, a detailed error diagnostic report is compiled in classification_report.json:
- **Class Imbalance**: True label distribution percentage.
- **Hard Classes**: Automatically flags classes with an F1-score or recall below 0.60.
- **Most Common Misclassifications**: Ranks and outputs the top 3 pairs of (true_class, predicted_class) with the highest off-diagonal counts.
- **Prediction Confidence Distribution**: Aggregates distribution statistics (mean, std, min, max, median, 25th, and 75th percentiles) of the model's confidence (max(predict_proba)) to audit model overconfidence.

### CLI Usage
Run evaluation via the CLI:
` ash
# Evaluate structured mode models
python main.py evaluate-models --mode structured

# Rebuild datasets prior to evaluation
python main.py evaluate-models --rebuild-dataset
`

---

## Stage 12: Explainability Engine (Task 6.3)

### Overview

The **Explainability Engine** generates global and local SHAP-based explanations for every trained model. It operates without retraining — serialised model artefacts are loaded from `models/` and all explanation outputs are persisted to `explainability/`.

Explainability is essential for:
- **Regulatory compliance** — understanding what drives predictions
- **Model auditing** — detecting bias or unexpected feature reliance
- **Research utility** — identifying which bill features most reliably predict market movement

---

### SHAP (SHapley Additive exPlanations) Methodology

SHAP values are grounded in cooperative game theory (Shapley, 1953) and provide the unique attribution of a model's prediction to each input feature with the following guarantees:

| Property | Description |
|---|---|
| **Local accuracy** | SHAP values sum to the exact prediction minus the expected model output |
| **Consistency** | If a model relies more on a feature, its SHAP value cannot decrease |
| **Missingness** | Features absent from the data get a SHAP value of zero |
| **Efficiency** | Total attribution equals the output of the model |

For a prediction $f(x)$:

$$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i$$

Where:
- $\phi_0 = \mathbb{E}[f(x)]$ — the expected model output (baseline)
- $\phi_i$ — the SHAP value attributing feature $i$'s contribution
- $M$ — total number of features

**Reference**: Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. *NeurIPS*, 30.

---

### TreeExplainer Selection

All three trained model types (LightGBM, XGBoost, Random Forest) are tree-based ensembles. For these, `shap.TreeExplainer` provides **exact** Shapley values in $O(TLD^2)$ time where:
- $T$ = number of trees
- $L$ = maximum number of leaves per tree
- $D$ = maximum tree depth

This is significantly faster than the model-agnostic `KernelExplainer` and requires no approximation. A `KernelExplainer` fallback with k-means background summarization is available for edge cases.

---

### Global Explanations

#### 1. Feature Importance (Mean |SHAP|)

$$\hat{\phi}_i = \frac{1}{N} \sum_{j=1}^{N} |\phi_i^{(j)}|$$

The mean absolute SHAP value across all $N$ training samples produces a deterministic global ranking of feature importance.

Persisted as:
- `feature_importance.csv` — sorted descending table per (target, model_type)
- `global_summary.json` — top-20 features aggregated across all models by maximum mean |SHAP|

#### 2. Summary Plot (Beeswarm)

Each row shows one feature; each dot shows one sample. The x-axis shows the SHAP value (positive = pushes prediction higher). Colour shows the raw feature value (red = high, blue = low).

#### 3. Bar Plot

Horizontal bar chart of the top-20 features by mean |SHAP value|. Quick global reference for the most influential features.

#### 4. Dependence Plots

Scatter plot for each of the top-10 features showing the relationship between raw feature value (x-axis) and SHAP value (y-axis). Reveals non-linear effects and interaction patterns.

#### 5. Cross-Model Feature Comparison

Grouped bar chart comparing the top-20 features side-by-side across all three model types for each target. Features that rank highly across all models are the most robust predictors.

Persisted as:
- `feature_comparison.png` — grouped bar chart
- `model_comparison.json` — structured JSON for programmatic access

---

### Local Explanations

Per-sample SHAP explanations are generated for three strategically selected sample groups:

| Group | Selection Criterion | Purpose |
|---|---|---|
| **Correct** | `y_pred == y_true` AND `max(prob) >= 0.80` | Understand why the model succeeds |
| **Misclassified** | `y_pred != y_true` | Identify failure modes |
| **High-confidence** | `max(prob) >= 0.90` | Audit confident predictions |

Up to 10 samples per group with top-10 features by absolute SHAP value reported per sample.
Local explanations are persisted as `local_explanations.json` under each `explainability/<target>/<model_type>/`.

---

### Interpretation Guide

#### Reading SHAP Values

| SHAP value | Interpretation |
|---|---|
| **Positive** | Feature pushed prediction toward higher class label |
| **Negative** | Feature pushed prediction toward lower class label |
| **Near zero** | Feature had little effect on this prediction |
| **Large magnitude** | Strong influence regardless of direction |

#### Legislative-Specific Insights

| Feature | High SHAP | Low SHAP |
|---|---|---|
| `beta` | High market sensitivity → larger reaction | Low beta → muted reaction |
| `p_value` | Low p → high confidence in label | Insignificant → likely neutral |
| `effect_size` | Large Cohen's d → stronger impact | Small effect → neutral likely |
| `ministry` | Finance/Banking → POSITIVE likely | Agriculture → NEUTRAL likely |
| `market_cap_category` | Large-cap → dampened reaction | Small-cap → larger AR possible |

---

### Output Structure

```
explainability/
├── <target>/
│   └── <model_type>/
│       ├── shap_values.parquet
│       ├── feature_importance.csv
│       ├── local_explanations.json
│       ├── summary_plot.png
│       ├── bar_plot.png
│       └── dependence_plots/
│           └── <feature>_dependence.png (×10)
├── global_summary.json
├── model_comparison.json
Each trained model is stored under models/<target>/<model_type>/ containing model.pkl, preprocessor.pkl, features.json, metadata.json, and training_report.json.

### CLI Usage

` ash
python main.py train --mode structured
python main.py train --target direction --model-type lgbm
python main.py train --rebuild-datasets
`

---

## Stage 11: Model Evaluation Engine (Task 6.2)

### Overview
The Model Evaluation Engine provides a standardized, multi-model, multi-target testing workflow to assess the performance of all 12 classifiers. Model evaluation runs on the unified training dataset without retraining, loading the refit estimators directly from the Model Repository.

### Statistical & Classification Metrics
The engine calculates standard and class-imbalance-aware metrics to evaluate prediction quality:

1. **Overall Performance**:
   - **Accuracy**: Fraction of correct predictions.
   - **Balanced Accuracy**: Macro-average of recall scores per class (essential for imbalanced targets like market_moving).
   - **Matthews Correlation Coefficient (MCC)**: High-quality metric for binary/multiclass settings (-1 to +1).

2. **Error / Precision Measures**:
   - **Precision (Macro & Weighted)**: Agreement of predictions with ground truth.
   - **Recall (Macro & Weighted)**: Coverage of positive instances.
   - **F1-Score (Macro & Weighted)**: Harmonic mean of precision and recall.

3. **Probability & Confidence Measures**:
   - **ROC-AUC**: Area under the ROC curve. Calculated using One-vs-Rest (OvR) macro-averaged strategy for multi-class and standard binary calculation for market_moving.
   - **Log Loss**: Multi-class cross-entropy loss based on predicted probability distributions (predict_proba).

### Model Comparative Ranking
Algorithms are ranked per target using the macro F1-score as the primary ranking metric. The evaluation repository persists comparison_report.json identifying:
- **Best model**: Highest macro F1.
- **Worst model**: Lowest macro F1.
- **Average Performance**: Arithmetic mean of accuracy and macro F1 across all trained estimators for the target.

### Error Analysis & Diagnosis
For every target and algorithm, a detailed error diagnostic report is compiled in classification_report.json:
- **Class Imbalance**: True label distribution percentage.
- **Hard Classes**: Automatically flags classes with an F1-score or recall below 0.60.
- **Most Common Misclassifications**: Ranks and outputs the top 3 pairs of (true_class, predicted_class) with the highest off-diagonal counts.
- **Prediction Confidence Distribution**: Aggregates distribution statistics (mean, std, min, max, median, 25th, and 75th percentiles) of the model's confidence (max(predict_proba)) to audit model overconfidence.

### CLI Usage
Run evaluation via the CLI:
` ash
# Evaluate structured mode models
python main.py evaluate-models --mode structured

# Rebuild datasets prior to evaluation
python main.py evaluate-models --rebuild-dataset
`

---

## Stage 12: Explainability Engine (Task 6.3)

### Overview

The **Explainability Engine** generates global and local SHAP-based explanations for every trained model. It operates without retraining — serialised model artefacts are loaded from `models/` and all explanation outputs are persisted to `explainability/`.

Explainability is essential for:
- **Regulatory compliance** — understanding what drives predictions
- **Model auditing** — detecting bias or unexpected feature reliance
- **Research utility** — identifying which bill features most reliably predict market movement

---

### SHAP (SHapley Additive exPlanations) Methodology

SHAP values are grounded in cooperative game theory (Shapley, 1953) and provide the unique attribution of a model's prediction to each input feature with the following guarantees:

| Property | Description |
|---|---|
| **Local accuracy** | SHAP values sum to the exact prediction minus the expected model output |
| **Consistency** | If a model relies more on a feature, its SHAP value cannot decrease |
| **Missingness** | Features absent from the data get a SHAP value of zero |
| **Efficiency** | Total attribution equals the output of the model |

For a prediction $f(x)$:

$$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i$$

Where:
- $\phi_0 = \mathbb{E}[f(x)]$ — the expected model output (baseline)
- $\phi_i$ — the SHAP value attributing feature $i$'s contribution
- $M$ — total number of features

**Reference**: Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. *NeurIPS*, 30.

---

### TreeExplainer Selection

All three trained model types (LightGBM, XGBoost, Random Forest) are tree-based ensembles. For these, `shap.TreeExplainer` provides **exact** Shapley values in $O(TLD^2)$ time where:
- $T$ = number of trees
- $L$ = maximum number of leaves per tree
- $D$ = maximum tree depth

This is significantly faster than the model-agnostic `KernelExplainer` and requires no approximation. A `KernelExplainer` fallback with k-means background summarization is available for edge cases.

---

### Global Explanations

#### 1. Feature Importance (Mean |SHAP|)

$$\hat{\phi}_i = \frac{1}{N} \sum_{j=1}^{N} |\phi_i^{(j)}|$$

The mean absolute SHAP value across all $N$ training samples produces a deterministic global ranking of feature importance.

Persisted as:
- `feature_importance.csv` — sorted descending table per (target, model_type)
- `global_summary.json` — top-20 features aggregated across all models by maximum mean |SHAP|

#### 2. Summary Plot (Beeswarm)

Each row shows one feature; each dot shows one sample. The x-axis shows the SHAP value (positive = pushes prediction higher). Colour shows the raw feature value (red = high, blue = low).

#### 3. Bar Plot

Horizontal bar chart of the top-20 features by mean |SHAP value|. Quick global reference for the most influential features.

#### 4. Dependence Plots

Scatter plot for each of the top-10 features showing the relationship between raw feature value (x-axis) and SHAP value (y-axis). Reveals non-linear effects and interaction patterns.

#### 5. Cross-Model Feature Comparison

Grouped bar chart comparing the top-20 features side-by-side across all three model types for each target. Features that rank highly across all models are the most robust predictors.

Persisted as:
- `feature_comparison.png` — grouped bar chart
- `model_comparison.json` — structured JSON for programmatic access

---

### Local Explanations

Per-sample SHAP explanations are generated for three strategically selected sample groups:

| Group | Selection Criterion | Purpose |
|---|---|---|
| **Correct** | `y_pred == y_true` AND `max(prob) >= 0.80` | Understand why the model succeeds |
| **Misclassified** | `y_pred != y_true` | Identify failure modes |
| **High-confidence** | `max(prob) >= 0.90` | Audit confident predictions |

Up to 10 samples per group with top-10 features by absolute SHAP value reported per sample.
Local explanations are persisted as `local_explanations.json` under each `explainability/<target>/<model_type>/`.

---

### Interpretation Guide

#### Reading SHAP Values

| SHAP value | Interpretation |
|---|---|
| **Positive** | Feature pushed prediction toward higher class label |
| **Negative** | Feature pushed prediction toward lower class label |
| **Near zero** | Feature had little effect on this prediction |
| **Large magnitude** | Strong influence regardless of direction |

#### Legislative-Specific Insights

| Feature | High SHAP | Low SHAP |
|---|---|---|
| `beta` | High market sensitivity → larger reaction | Low beta → muted reaction |
| `p_value` | Low p → high confidence in label | Insignificant → likely neutral |
| `effect_size` | Large Cohen's d → stronger impact | Small effect → neutral likely |
| `ministry` | Finance/Banking → POSITIVE likely | Agriculture → NEUTRAL likely |
| `market_cap_category` | Large-cap → dampened reaction | Small-cap → larger AR possible |

---

### Output Structure

```
explainability/
├── <target>/
│   └── <model_type>/
│       ├── shap_values.parquet
│       ├── feature_importance.csv
│       ├── local_explanations.json
│       ├── summary_plot.png
│       ├── bar_plot.png
│       └── dependence_plots/
│           └── <feature>_dependence.png (×10)
├── global_summary.json
├── model_comparison.json
└── feature_comparison.png
```

### CLI Usage

```bash
# Explain all trained models
python main.py explain-models --all

# Explain only the direction classifier
python main.py explain-models --target direction

# Explain only LightGBM models
python main.py explain-models --model lgbm

# Use a specific feature-selection mode
python main.py explain-models --all --mode hybrid
```

---

## Stage 12: Historical Backtesting Methodology (Task 6.4)

### Purpose & Objective
The purpose of the **Historical Backtesting Engine** is to rigorously evaluate whether the trained prediction system produces useful investment signals using information that was strictly available on or before each historical bill introduction event.

### 1. Strict Anti-Leakage Protocol
At every historical bill event:
- Model preprocessors and estimators use **ONLY** pre-event feature variables known at or before the prediction cutoff date.
- All post-event variables (CAR, AR, peak day, t-statistic, p-value, effect size, post-event returns, future prices, future metadata, future labels) are stripped from prediction feature vectors.
- Actual event outcomes and abnormal returns (CAR) are joined **ONLY AFTER** prediction generation for strategy performance evaluation.

### 2. Prediction Timestamp & Anticipation Paradox
- **Prediction Timestamp**: Recorded explicitly for every backtest record (default: official bill introduction date).
- **Anticipation Window**: Configurable window (default `[-30, -1]` trading/calendar days before official introduction).
- **Anticipation Paradox Architecture**: The primary backtest runs at official introduction dates while documenting that historical anticipation-aware features (GDELT / Google Trends) are unavailable, using timestamp offsets to enable future media integration without engine redesign.

### 3. Chronological Walk-Forward Backtesting
- All historical bill events are ordered chronologically by `introduction_date`.
- **Expanding Training Window**: At step $t$, the model fits strictly on historical observations prior to date $t$, then generates predictions for test event(s) at date $t$.
- Observations are **never** shuffled, and random train/test splitting is strictly prohibited.

### 4. Strategy Signal Rules & Transaction Costs
- **Signal Generation**:
  - Predicted Positive / True $\rightarrow$ Long Position (+1.0)
  - Predicted Negative $\rightarrow$ Short Position (-1.0)
  - Predicted Neutral / False $\rightarrow$ No Position (0.0)
- **Transaction Costs**:
  - `Net Strategy Return = Signal * Actual CAR - Transaction Cost * |Signal|`
  - Configurable brokerage (default 5 bps), slippage (default 5 bps), and total transaction cost (default 10 bps). Also supports `transaction_cost = 0` for raw academic analysis.

### 5. Benchmark Comparison
- Strategy returns are evaluated against:
  - **Buy-and-Hold Benchmark**: Equal-weighted buy-and-hold position in target companies over event windows.
  - **Market Benchmark**: NIFTY 50 index return over corresponding periods.

### 6. Academic Distinction Requirement
The backtesting framework explicitly distinguishes:
1. **Predictive classification performance** (Accuracy, Precision, Recall, Macro F1, Weighted F1, Balanced Accuracy, MCC, ROC-AUC, Brier Score, ECE).
2. **Historical financial strategy performance** (Cumulative Return, Sharpe Ratio, Max Drawdown, Volatility, Hit Ratio).

*High classification accuracy does NOT guarantee strategy profitability due to transaction costs, asymmetrical return distributions, and market noise.*

### CLI Usage

```bash
# Backtest all targets
python main.py backtest-models --all

# Backtest specific target and model
python main.py backtest-models --target direction --model lgbm

# Backtest with zero transaction cost (academic raw analysis)
python main.py backtest-models --all --transaction-cost 0.0

# Backtest with 30-day anticipation window
python main.py backtest-models --all --anticipation-window 30
```

---

## Stage 8.5: Anticipation Bias / Pre-Event Information Analysis (Task 6.5)

### 1. Objective & Core Research Question
The Anticipation Bias Analysis Engine evaluates whether market participants may have received information about a legislative bill prior to its official parliamentary introduction date ($T_0$).
**Core Research Question**: *"For each production legislative bill: Was there measurable evidence that information related to this bill was publicly available or reflected in the market before the official introduction date?"*

### 2. Multi-Window Pre-Event Framework
Abnormal returns and cumulative abnormal returns are evaluated across trading-day aligned windows prior to $T_0$:
- `[-30, -21]`: Early anticipation / distant baseline
- `[-20, -11]`: Intermediate pre-event window
- `[-10, -6]`: Late pre-event window
- `[-5, -3]`: Immediate pre-announcement window
- `[-2, -1]`: Final pre-introduction window
- `[-30, -1]`: Cumulative full pre-event period

For each window $W = [t_1, t_2]$:
$$MAR_i(W) = \frac{1}{|W|} \sum_{t=t_1}^{t_2} AR_{i,t}, \quad CAR_i(W) = \sum_{t=t_1}^{t_2} AR_{i,t}$$
$$z = \frac{CAR_i(W)}{\sqrt{|W|} \cdot \hat{\sigma}_{\epsilon,i}}, \quad p = 2 \cdot (1 - \Phi(|z|))$$

### 3. Strict Anti-Leakage Rules
- **Rule**: For every external evidence item $e$: $t_{\text{publication}}(e) < T_{0,\text{official}}$ is strictly enforced.
- Any evidence with $t_{\text{pub}} \ge T_0$ is rejected, categorized with code `LOOK-AHEAD LEAKAGE`, and logged in `AnticipationValidationReport`.
- If external GDELT / Google Trends media data is not available, the engine explicitly sets `media_data_available = False` and derives diagnostic scores purely from pre-event market signals.

### 4. Deterministic Signal Detection
1. **STATISTICAL_SIGNIFICANCE_PRE_EVENT**: $|z| \ge 1.96$ ($p < 0.05$) in pre-event windows.
2. **HIGH_MAGNITUDE_PRE_EVENT_RETURN**: $|CAR| \ge 2.0\%$ (or $\ge 1.5\%$ in immediate windows).
3. **SUSTAINED_DIRECTIONAL_DRIFT**: $\ge 70\%$ positive or negative daily abnormal return days.
4. **IMMEDIATE_PRE_T0_ACCELERATION**: Elevated abnormal movement concentrated in `[-5,-3]` or `[-2,-1]`.
5. **MULTI_WINDOW_PERSISTENT_DRIFT**: $\ge 3$ consecutive sub-windows with consistent sign.

### 5. Classification & Diagnostic Scorer
Normalized composite anticipation score $S \in [0.0, 1.0]$:
- $S \ge 0.75 \implies \textbf{STRONG\_EVIDENCE}$
- $0.50 \le S < 0.75 \implies \textbf{MODERATE\_EVIDENCE}$
- $0.25 \le S < 0.50 \implies \textbf{WEAK\_EVIDENCE}$
- $S < 0.25 \implies \textbf{NO\_EVIDENCE}$

*Academic Distinction*: Pre-event abnormal returns indicate quantitative diagnostic patterns consistent with market anticipation, not proof of non-public insider information leakage.

### CLI Usage
```bash
# Analyze all bills and companies
python main.py analyze-anticipation

# Force refresh (recompute existing records)
python main.py analyze-anticipation --force-refresh

# Filter by year or specific bill
python main.py analyze-anticipation --year 2024
python main.py analyze-anticipation --bill-id the-banking-laws-amendment-bill-2024
```

---

## Stage 9: Final Prediction & Decision Engine (Task 7.1)

### 1. Objective & Design Philosophy
The Final Prediction & Decision Engine executes forward-looking inference over legislative bill-company pairs using existing trained machine learning estimators and fitted preprocessors from `models/`. It operates strictly under **Zero Retraining** constraints.

The engine strictly separates:
1. **Pure Machine Learning Estimations**: Deterministic classification labels and calibrated multi-class probability vectors across 4 prediction targets.
2. **Contextual Decision Support**: Qualitative narrative synthesis, risk factor identification, expected CAR impact range estimation, and incorporation of pre-event anticipation diagnostics.

### 2. Multi-Target Prediction Space

| Target | Classes / Range | Default Optimal Estimator | Selection Criterion |
|--------|----------------|---------------------------|---------------------|
| **Direction** | `POSITIVE`, `NEGATIVE`, `NEUTRAL` | LightGBM (`lgbm`) | Macro F1, Balanced Accuracy, MCC |
| **Market Moving** | `TRUE`, `FALSE` | Random Forest (`random_forest`) | Macro F1, ROC-AUC, Balanced Accuracy |
| **Impact Strength** | `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH` | LightGBM (`lgbm`) | Macro F1, Balanced Accuracy |
| **Confidence** | `LOW`, `MEDIUM`, `HIGH` | LightGBM (`lgbm`) | Macro F1, Calibration, Brier Score |

### 3. Pre-Inference Validation Pipeline (`PredictionValidator`)
Before any feature row is presented to a model estimator, the `PredictionValidator` performs fail-fast validation checks:
- **Identifier Sanity**: Validates that `bill_id`, `company_isin`, and `event_window` are non-empty strings.
- **Model Artifact Verification**: Verifies `model.pkl`, `preprocessor.pkl`, and `features.json` exist in `models/<target>/<model_type>/`.
- **Feature Alignment & Completeness**: Ensures all required features listed in `features.json` are present in the candidate dictionary.
- **Numerical Sanity**: Strictly detects and flags `NaN`, `+Inf`, and `-Inf` values in numeric fields.
- **Categorical Integrity**: Rejects non-scalar corrupt types (e.g., nested dicts or non-serializable objects).

Failed validations generate `PredictionValidationReport` artifacts saved under `data/predictions/reports/val_<bill_id>_<company_isin>_<window>.json`.

### 4. Contextual Decision Engine & Anticipation Blending (`DecisionEngine`)
The Decision Engine synthesizes a structured interpretation of the quantitative predictions:
- **Decision Narrative**: Formulates clear explanations summarizing predicted direction, probability strength, and confidence levels.
- **Anticipation Evidence Diagnostic**:
  - When `STRONG_EVIDENCE` / `MODERATE_EVIDENCE` anticipation is present: Flags that strong pre-event price discovery or abnormal run-up occurred and market impact may be **partially or fully priced in**.
  - When `NO_EVIDENCE` anticipation is present: Highlights that the legislative event is likely **novel to the market**.
- **Expected Impact Estimation**: Maps `(predicted_direction, predicted_impact_strength)` to abnormal return magnitude bands (e.g. $+3.0\%$ to $+6.0\%$ for `HIGH` positive impact).
- **Risk Indicators**: Highlights high volatility, extreme beta sensitivity ($\beta > 1.4$ or $\beta < 0.6$), low model confidence, and imputed data quality.
- **Compliance Disclaimer**: Appends mandatory disclaimer text:  
  *"[Probabilistic decision-support assessment for quantitative research purposes only. Does not constitute guaranteed price movements or investment advice.]"*

### 5. Incremental Execution & Caching Strategy
- Each prediction is uniquely identified by `pred_<bill_id>_<company_isin>_<window>`.
- The engine checks `PredictionRepository` for existing JSON records. If `model_version` and `feature_version` match current versions (`v1.0`), inference is skipped.
- CLI flag `--force-refresh` overrides the cache and recomputes all predictions.

### 6. CLI Usage

```bash
# Generate predictions for all candidates in 2024 bills
python main.py generate-predictions --year 2024

# Force re-infer and overwrite cached predictions
python main.py generate-predictions --year 2024 --force-refresh

# Generate predictions for a specific bill and company
python main.py generate-predictions --bill-id telecom-bill-2023 --company-isin INE002A01018

# Filter by event window
python main.py generate-predictions --event-window "[-20,+20]"
```

---

## Stage 15: Decision Support & Risk Scoring Engine (Task 7.2)

### 1. Objective & Philosophy
The Decision Support & Risk Scoring Engine transforms raw multi-target prediction outputs into structured, qualitative perspectives tailored for distinct stakeholder groups (Investors, Corporates, and the Public) while calculating deterministic composite risk scores.

### 2. Mathematical Formulation

#### Direction Impact Score ($I \in [0, 1]$)
Synthesizes directional confidence, market-moving likelihood, and magnitude tiers, attenuated by pre-event anticipation:
$$I = \left( w_{\text{dir}} \cdot P(\text{Dir}) + w_{\text{strength}} \cdot \sum_{k} P(\text{Level}_k) \cdot v_k \right) \cdot P(\text{MM}) \cdot C_{\text{scalar}} \cdot \left(1 - \delta \cdot A_{\text{score}}\right)$$

Where:
- $w_{\text{dir}} = 0.50$, $w_{\text{strength}} = 0.50$
- $v_{\text{Level}} \in \{ \text{LOW}: 0.25, \text{MEDIUM}: 0.50, \text{HIGH}: 0.75, \text{VERY\_HIGH}: 1.00 \}$
- $P(\text{MM})$ is the model's calibrated market-moving probability
- $C_{\text{scalar}}$ is the composite model confidence scalar $[0, 1]$
- $\delta = 0.30$ is the anticipation discount factor
- $A_{\text{score}} \in [0, 1]$ is the pre-event anticipation score

#### Composite Decision Risk Score ($R \in [0, 1]$)
Combines model uncertainty, pre-event pricing-in risk, tail magnitude risk, and directional ambiguity:
$$R = w_{\text{uncert}} \cdot (1 - C_{\text{scalar}}) + w_{\text{anticip}} \cdot A_{\text{score}} + w_{\text{tail}} \cdot P(\text{Tail}) \cdot P(\text{MM}) + w_{\text{conflict}} \cdot \left(1 - |P(\text{Pos}) - P(\text{Neg})|\right)$$

Where:
- $w_{\text{uncert}} = 0.30$, $w_{\text{anticip}} = 0.25$, $w_{\text{tail}} = 0.25$, $w_{\text{conflict}} = 0.20$
- $P(\text{Tail}) = P(\text{HIGH}) + P(\text{VERY\_HIGH})$
- $R$ is strictly clamped to $[0.0, 1.0]$

#### Scoring Categories
- $[0.00, 0.20)$: `VERY_LOW`
- $[0.20, 0.40)$: `LOW`
- $[0.40, 0.60)$: `MODERATE`
- $[0.60, 0.80)$: `HIGH`
- $[0.80, 1.00]$: `VERY_HIGH`

### 3. Stakeholder Perspectives

1. **Investor Perspective**:
   - Probabilistic assessment of abnormal return direction (*"potential positive impact"*, *"potential negative impact"*, *"neutral or subdued market reaction"*).
   - Magnitude expectation tier and market-moving probability.
   - Pricing-in risk evaluation (*"Substantial pre-event market activity suggests part or all of the expected reaction may already be priced in"*).

2. **Business / Corporate Perspective**:
   - Industry exposure and strategic intersection with the sponsoring ministry.
   - Knowledge-layer mapping alignment score and exposure type.
   - Qualitative operating implications (regulatory tailwinds, compliance overhead, capital expenditure requirements).

3. **General Public Perspective**:
   - Plain-English description free of financial jargon.
   - Explains legislative intent, societal objectives, and parliamentary context.

### 4. CLI Usage

```bash
# Generate decision support for all 2024 bills
python main.py generate-decision-support --year 2024

# Force refresh decisions and bypass cache
python main.py generate-decision-support --year 2024 --force-refresh

# Generate decision support for specific bill & company
python main.py generate-decision-support --bill-id the-telecom-act-2024 --company-isin INE002A01018
```

---

## Task 7.3: Stakeholder Reporting & Presentation Layer

### 1. Architectural Philosophy
The reporting layer is a **pure presentation and synthesis tier**. Invariant rules:
- It **never modifies** prediction targets, probabilities, composite risk scores, or underlying ML models.
- It translates quantitative signals into audience-tailored narrative artefacts formatted as **JSON**, **Markdown**, and **CSV**.
- It enforces strict compliance and legal guardrails across all narrative outputs.

### 2. Stakeholder Reporting Perspectives

#### A. Investor Report (`InvestorReporter`)
- **Tone**: Analytical, probabilistic, cautious, quantitative.
- **Vocabulary Safety**:
  - Allowed: *"Model indicates a potential positive impact"*, *"Elevated market-moving probability observed"*, *"Analysis suggests"*.
  - Forbidden: *"Stock will rise/fall"*, *"Guaranteed return"*, *"Buy/Sell this stock"*.
- **Key Sections**:
  - Executive Summary (probabilistic 2–3 sentence overview)
  - Bill & Company Identification
  - Market Impact & Directional Probability Distribution
  - Composite Decision Risk & Pricing-In Evaluation
  - Pre-Event Anticipation Analysis
  - Model Feature Importance (SHAP features from Task 6.3)
  - Legal & Academic Disclaimers

#### B. Business / Corporate Report (`BusinessReporter`)
- **Tone**: Strategic, operational, regulatory, non-trading.
- **Focus**:
  - Operational headwinds/tailwinds (incentives vs. regulatory constraints)
  - Compliance implications and administrative obligations
  - Knowledge-layer mapping alignment score
  - Industry and sub-industry structural exposure
  - Strategic market awareness

#### C. General Public Report (`PublicReporter`)
- **Tone**: Plain English, accessible, educational, jargon-free.
- **Focus**:
  - Simple explanation of what the bill does and why it was introduced
  - Clear overview of affected areas of the economy and everyday companies
  - Plain-language likelihood and confidence explanations
  - Free from statistical terms (*"SHAP"*, *"CAR"*, *"alpha"*, *"gradient boosting"*)

### 3. Aggregation Methodology

#### Bill-Level Aggregation (`BillAggregator`)
Synthesizes records across all companies affected by a single bill.

| Metric | Formulation / Calculation |
|---|---|
| `total_companies` | $\text{Count of unique company ISINs mapped to bill}$ |
| `positive_count` | $\sum \mathbb{I}(\text{predicted\_direction} = \text{POSITIVE})$ |
| `negative_count` | $\sum \mathbb{I}(\text{predicted\_direction} = \text{NEGATIVE})$ |
| `neutral_count` | $\sum \mathbb{I}(\text{predicted\_direction} = \text{NEUTRAL})$ |
| `market_moving_count` | $\sum \mathbb{I}(P(\text{Market-Moving}) \ge 0.50)$ |
| `high_impact_count` | $\sum \mathbb{I}(\text{impact\_category} \in \{\text{HIGH}, \text{VERY\_HIGH}\})$ |
| `avg_impact_score` | $\frac{1}{N} \sum_{i=1}^N \text{impact\_score}_i \quad (\text{Arithmetic mean of scalar scores; NOT probability average})$ |
| `avg_risk_score` | $\frac{1}{N} \sum_{i=1}^N \text{risk\_score}_i \quad (\text{Arithmetic mean of scalar scores; NOT probability average})$ |
| `sectors_affected` | $\text{Sorted unique list of all represented non-empty sectors}$ |
| `anticipation_distribution`| Frequency count table of anticipation classes |
| `risk_distribution` | Frequency count table of composite risk categories |

#### Company-Level Aggregation (`CompanyAggregator`)
Synthesizes all legislative exposures for a single company across multiple bills (Company $\rightarrow$ Bills view).

### 4. Mandatory Disclaimers & Methodology Statements

- **Investor & Business Disclaimer**:
  > *"IMPORTANT DISCLAIMER: This report is an academic decision-support output generated by a quantitative research system. It does not constitute personalised investment advice, financial advice, or a recommendation to buy, sell, or hold any security. Predictions are probabilistic and may be incorrect. Past model performance does not guarantee future results. This system is intended for research and educational purposes only. Always consult a qualified financial advisor before making investment decisions."*

- **General Public Disclaimer**:
  > *"NOTICE: This summary is for general information and educational purposes only. It is produced by an academic research system and does not constitute financial, legal, or investment advice. The analysis may be incorrect. Always seek professional advice before making financial decisions."*

### 5. CLI Usage

```bash
# Generate investor reports for all available decision records
python main.py generate-reports --stakeholder investor

# Generate Markdown reports for a specific bill across all companies
python main.py generate-reports --bill-id the-telecom-act-2024 --format markdown

# Generate business perspective for a specific company in CSV format
python main.py generate-reports --company-isin INE002A01018 --stakeholder business --format csv

# Generate aggregate bill-level report
python main.py generate-reports --bill-id the-telecom-act-2024 --generate-bill-report

# Generate aggregate company exposure report
python main.py generate-reports --company-isin INE002A01018 --generate-company-report

# Force full regeneration bypassing cache
python main.py generate-reports --force-refresh
```

---

## Stage 10: Task 7.4 — Interactive Dashboard & Decision-Support Interface

### 1. Presentation-Only Invariants
The dashboard layer operates strictly as a read-only presentation interface:
- **Zero Retraining**: Does not trigger training or fine-tuning runs.
- **Zero Model Modification**: Preserves all upstream probabilities, CARs, and SHAP vectors.
- **Zero Score Alteration**: Never recalculates composite risk scores ($R$) or directional impact scores ($I$).
- **Zero Future Information**: Enforces temporal isolation by visualizing only walk-forward evaluated horizons.
- **Immutable Repositories**: Reads verified JSON/Parquet artifacts from disk without in-place mutations.

### 2. Universe Reconciliation & Provenance Diagnostics
The dashboard includes an automated `ScopeService` providing transparency over the dataset universe:
- **Production Decision Universe**: Exactly $20 \text{ bills} \times 47 \text{ companies} \times 5 \text{ windows} = 4,700 \text{ records}$.
- **Repository Discrepancy Auditing**:
  - Explains the exclusion of 2 non-legislative records from `data/bills/metadata/` (`key-issues-and-analysis` which is a PRS brief and `service-bill` which is an empty test stub).
  - Explains the exclusion of 3 companies from `data/companies/` (`INE214G01026`, `INE155A01022`, `INE040A01034`) due to liquidity and market study fit.
  - Documents that the Task 7.3 runtime sample run of 50 decision records / 18 companies represented an intentional test batch, whereas the underlying persistence repository contains all 4,700 decision records with 100% parity.

### 3. Institutional Communication Standards
- **Non-Advisory Phrasing**: All financial commentary uses probabilistic framing (*"Model indicates a potential positive impact"*, *"Model assigns an elevated probability that the event may be market-moving"*). Prohibits words such as *"Buy"*, *"Sell"*, or *"Guaranteed Return"*.
- **Anticipation Framing**: Displays explicit legal notices declaring that pre-event statistical drift or abnormal volumes reflect public information diffusion and price discovery, and do not establish insider trading, unlawful leakage, or legal culpability.
- **Validation Separation**: Distinctly isolates machine learning classification performance (Macro F1, Balanced Accuracy, MCC, ROC-AUC) from hypothetical trading strategy simulations (Sharpe ratio, max drawdown, equity curves).




