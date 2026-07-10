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

### Market Model
Normal returns are estimated using OLS regression over an estimation window:

```
R_it = α_i + β_i × R_mt + ε_it
```

Where:
- `R_it` = return of stock `i` on day `t`
- `R_mt` = return of market index (Nifty 50) on day `t`
- `α_i`, `β_i` = estimated parameters from the estimation window

### Abnormal Return (AR)
```
AR_it = R_it − (α_i + β_i × R_mt)
```

### Cumulative Abnormal Return (CAR)
```
CAR_i[T1, T2] = Σ AR_it  for t = T1 to T2
```

### Event Windows

| Window | Range | Interpretation |
|--------|-------|----------------|
| Pre-event | T-120 to T-11 | Estimation window |
| Announcement | T-1, T=0, T+1 | Immediate reaction |
| Short-term | T=0 to T+5 | 1-week effect |
| Medium-term | T=0 to T+20 | 1-month effect |
| Long-term | T=0 to T+60 | 3-month effect |

### Statistical Significance
T-statistics are computed for each CAR. Predictions with |t| < 2.0 (p > 0.05)
are flagged as statistically insignificant.

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

## References

1. MacKinlay, A.C. (1997). *Event Studies in Economics and Finance*.
   Journal of Economic Literature, 35(1), 13–39.
2. Huang, A. et al. (2022). *FinBERT: A Large Language Model for Extracting
   Information from Financial Text*. Contemporary Accounting Research.
3. Chalkidis, I. et al. (2020). *Legal-BERT: The Muppets straight out of Law School*.
   EMNLP Findings.
