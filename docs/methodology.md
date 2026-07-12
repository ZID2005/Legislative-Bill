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
