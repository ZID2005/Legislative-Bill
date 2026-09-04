# Roadmap

## Version 1 — MVP (Central Government Bills)

### Phase 1: Foundation
- [x] **Task 0** — Project scaffold, config, logging, utils

### Phase 2: Data Acquisition
- [x] **Task 1** — Bill ingestion from PRS / Lok Sabha / Rajya Sabha
- [x] **Task 2** — Company master (BSE/NSE) + historical market prices

### Phase 3: Data Quality
- [x] **Task 3** — Validation layer (pydantic schemas, data quality checks)

### Phase 4: NLP Intelligence & Text Processing
- [x] **Task 4.1** — Document downloading & management
- [x] **Task 4.2** — Text extraction & corpus construction

### Phase 5: Knowledge Layer & Domain Mapping
- [x] **Task 5.1** — Legislative Knowledge Layer Engine
- [x] **Task 5.2** — Company Intelligence & Master Dataset
- [x] **Task 5.3** — Bill to Company Mapping Engine

### Phase 6: Market Modeling & Label Generation
- [x] **Task 6.1** — Market Data Pipeline (OHLCV & Index)
- [x] **Task 6.2** — Market Model Estimation Engine
- [x] **Task 6.3** — Event Study Engine
- [x] **Task 6.4** — Statistical Significance Engine
- [x] **Task 6.5** — Label Generation Engine

### Phase 7: Feature Engineering & Fusion
- [x] **Task 7.1** — Feature Engineering Engine
- [x] **Task 7.2** — NLP Text Embedding Engine (FinBERT & Legal-RoBERTa)
- [x] **Task 7.3** — Feature Fusion Engine
- [x] **Task 7.4** — Feature Selection Engine

### Phase 8: Machine Learning & Modeling
- [x] **Task 8.1** — ML Training Engine (Task 6.1)
- [x] **Task 8.2** — Model Evaluation Engine (Task 6.2)
- [x] **Task 8.3** — Explainability Engine (SHAP) (Task 6.3)
- [x] **Task 8.4** — Historical Backtesting Engine (Task 6.4)
- [x] **Task 6.5** — Anticipation Bias / Pre-Event Information Analysis Engine
- [x] **Task 7.1** — Final Prediction & Decision Engine (Forward-Looking Multi-Target Inference & Decision Support)
- [x] **Task 7.2** — Decision Support & Risk Scoring Engine (Multi-Stakeholder Qualitative Perspectives & Composite Risk Scoring)
- [x] **Task 7.3** — Stakeholder Reporting & Presentation Layer (Investor / Business / Public structured reports, bill/company aggregation, JSON/Markdown/CSV output)
- [x] **Task 7.4** — Interactive Decision-Support Dashboard (Streamlit & Plotly Multi-Lens Knowledge Interface)

### Phase 9: Real-Time Inference API (Future Scope)
- [ ] **Task 9** — Real-Time Prediction API (FastAPI)

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
- Automated portfolio rebalancing on legislative signals
- Regulatory compliance monitoring
