# Methodology

## Overview

The prediction pipeline uses a multi-stage methodology that combines
**natural language processing** of legislative text with **quantitative
finance** techniques to produce market impact predictions.

---

## Stage 1: Bill Text Understanding (NLP)

### Approach
We treat each bill as a structured legal document and extract:
1. **Key provisions** — clauses most likely to have economic impact
2. **Entities** — sectors, companies, commodities, and regulatory bodies mentioned
3. **Sentiment** — whether provisions create obligations, relaxations, or restrictions
4. **Scope** — which industries and activities are covered

### Models
- **Primary**: Legal-RoBERTa (fine-tuned on Indian legal text)
- **Supplementary**: FinBERT (for financial sentiment within bill clauses)
- **Summarisation**: GPT-4 or open-source equivalent (Mistral 7B / Llama 3)

---

## Stage 2: Sector & Company Mapping

### Phase A — Keyword-Based (Baseline)
A curated keyword dictionary maps domain terms to sectors. Fast, interpretable,
but brittle to novel language.

### Phase B — Embedding-Based (Primary)
Bill clause embeddings are compared against sector-description embeddings using
cosine similarity. More robust to paraphrasing and novel provisions.

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
