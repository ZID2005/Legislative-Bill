# Roadmap

## Version 1 — MVP (Central Government Bills)

### Phase 1: Foundation
- [x] **Task 0** — Project scaffold, config, logging, utils

### Phase 2: Data Acquisition
- [x] **Task 1** — Bill ingestion from PRS / Lok Sabha / Rajya Sabha
- [ ] **Task 2** — Company master (BSE/NSE) + historical market prices

### Phase 3: Data Quality
- [ ] **Task 3** — Validation layer (pydantic schemas, data quality checks)

### Phase 4: NLP Intelligence
- [ ] **Task 4** — Legal text NLP pipeline
  - PDF text extraction (pdfplumber)
  - Sentence segmentation
  - Bill clause extraction
  - Zero-shot sector classification (Legal-RoBERTa)
  - Bill summarisation (GPT-4 / open-source LLM)

### Phase 5: Domain Mapping
- [ ] **Task 5** — Sector and company mapping
  - Keyword-based mapping (Phase A)
  - Embedding-based mapping (Phase B)

### Phase 6: Label Generation
- [ ] **Task 6** — Event-study labels
  - Market model estimation
  - CAR computation
  - Statistical significance testing

### Phase 7: Feature Engineering
- [ ] **Task 7** — Feature matrix construction
  - Text features (FinBERT embeddings)
  - Bill metadata features
  - Market context features
  - Company/sector features

### Phase 8: Modelling
- [ ] **Task 8** — Model training & evaluation
  - Baseline: Logistic Regression, Random Forest
  - Primary: LightGBM + Optuna
  - Advanced: FinBERT fine-tune

### Phase 9: Inference API
- [ ] **Task 9** — Prediction API (FastAPI)
  - `/predict` endpoint
  - SHAP explanations
  - Response caching

### Phase 10: Dashboard
- [ ] **Task 10** — Knowledge platform UI
  - Bill explorer
  - Historical impact view
  - AI prediction view
  - Knowledge centre

---

## Version 2 — Expansion (Future)

| Feature | Description |
|---------|-------------|
| State bills | Extend to state-level legislative bills |
| Real-time | Live alerts on new bill introductions |
| Portfolio analysis | Personal portfolio impact assessment |
| Regulatory tracker | Track implementation via gazette notifications |
| Investor alerts | Email/SMS notifications for watched sectors |
| Multi-lingual | Hindi and regional language bill support |

---

## Version 3 — Enterprise (Long-term)

- White-label API for institutional clients
- Integration with Bloomberg / Reuters data feeds
- Backtesting framework for investment strategies
- Regulatory compliance monitoring
