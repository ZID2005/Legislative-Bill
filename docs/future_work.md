# Future Work

This document captures planned improvements, known limitations, and research
directions for future versions of the system.

---

## Version 2 Priorities

### State-Level Bills
- Extend data ingestion to cover all 28 state assemblies and 8 union territories
- Requires state-specific scraper adapters for each state legislature website
- Some states have well-maintained portals (e.g. Maharashtra, Tamil Nadu);
  others will need OCR-based extraction from PDFs

### Real-Time Bill Tracking
- Implement webhook or polling-based notifications for new bill introductions
- Trigger automated pipeline re-runs on new bill detection
- Push alerts (email, SMS, WhatsApp Business API) for subscribed users

### Portfolio-Level Impact
- Allow users to connect their portfolio (CSV upload or brokerage API)
- Aggregate bill impact predictions across all holdings
- Generate personalised "Legislative Risk Score" for a portfolio

### Regulatory Gazette Tracking
- Monitor the e-Gazette of India for notifications implementing passed bills
- Map gazette notifications back to the original bill
- Track implementation lag (days between passage and notification)

### Advanced Bill-to-Company Mapping
- **Embedding-Based Semantic Mapping**: Embed bill clauses using domain-specific legal models (e.g. Legal-RoBERTa) and calculate similarity against vector embeddings of company business descriptions, annual reports, and regulatory filings. This enables discovery of implicit dependencies beyond taxonomy keywords.
- **Supervised Confidence Calibration**: Leverage historical stock price reactions from event studies to train a machine learning model that automatically calibrates and weights mapping confidence, optimizing the decision boundary for mapping strength.

---

## Research Directions

### Improved Causal Identification
- Regression Discontinuity Design (RDD) around bill introduction dates
- Synthetic Control Methods for bills with limited affected companies
- Difference-in-Differences when control groups exist

### Multi-Modal Features
- Parliamentary debate transcripts (what was said about the bill?)
- Minister press conference text
- News media coverage volume and sentiment (Google News, NewsAPI)
- Social media sentiment (Twitter/X, StockTwits)

### Longer Horizon Predictions
- Currently focused on 3-month (CAR[0,+60]) prediction horizon
- Explore 6-month and 12-month impacts
- Study implementation effects (market reaction at notification date vs. introduction date)

### Cross-Country Comparison
- Compare Indian legislative market impact with similar bills in the US, UK, EU
- Learn from established FinReg literature

---

## Technical Debt & Known Limitations

| Issue | Priority | Notes |
|-------|----------|-------|
| Holiday calendar incomplete | Medium | Indian market holidays not yet populated |
| No state-level support | Low (V2) | Design is extensible |
| No real-time data | Low (V2) | yfinance is sufficient for MVP |
| LLM costs at scale | Medium | Open-source models preferred for self-hosting |
| Data recency bias | High | Model should be retrained quarterly |
| PDF extraction quality | High | Scanned PDFs need OCR fallback |

---

## Scalability Considerations

### Data Volume
- ~5,000 Central Government bills since independence
- ~5,000 listed companies
- 25+ years of daily price data
- → Estimated feature matrix: ~50,000 rows × 1,000 features

### Compute
- Training on a single GPU instance is sufficient for MVP
- Inference (FastAPI) should run on CPU with < 100ms latency
- Future: distributed training on multi-GPU for transformer fine-tuning

### Storage
- Parquet format for all tabular data (10–50x compression over CSV)
- Object storage (S3/GCS) for PDFs and model artefacts in production
- SQLite for MVP; migrate to PostgreSQL for V2

---

## Open Research Questions

1. Does the market react to bill *introduction* or bill *passage*? Or both?
2. How do markets react differently to bills with high vs. low passage probability?
3. Is there evidence of informed trading before bill introduction (insider trading signal)?
4. Does the sentiment of Parliamentary debate predict the final bill impact?
5. How does market microstructure (liquidity, spread) affect event study validity for small-cap stocks?
