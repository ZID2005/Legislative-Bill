# Final-Year Engineering Project Viva Defense Notes
## Comprehensive Technical & Theoretical Oral Examination Cheat-Sheet

**Project:** Legislative Bill Impact Prediction & Decision Intelligence Platform  
**Academic Target:** External Examiner / Viva Voce Committee Defense  
**Platform Baseline SHA-256:** `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`  

---

## 1. System Architecture & Component Interaction

- **Layer 1: Ingestion & Scraping Engine:** Asynchronous scrapers target official parliamentary tables and state gazettes with polite request throttling (1.5s delay, 15s timeout, custom User-Agent). PDF text extraction utilizes pdfplumber with MD5/SHA-256 integrity verification.
- **Layer 2: NLP Representation Pipeline:** Bill text is cleaned, tokenized, and embedded via domain-specific Transformers (FinBERT & Legal-RoBERTa). 
- **Layer 3: Feature Engineering & Store:** Embeddings are pooled (mean-pooling over dense layers) and concatenated with structured company metadata, sector betas, and statutory markers into versioned Parquet tables.
- **Layer 4: Predictive Econometric Engine:** Gradient boosted decision trees project cumulative abnormal returns (CAR) across 5 standard event horizons.
- **Layer 5: Decision Intelligence & Anti-Leakage Layer:** Anticipation evidence scores decouple pre-event price action from public media disclosures.
- **Layer 6: Persistence & API Services:** FastAPI REST engine with JWT bearer auth, tenant isolation, and PostgreSQL/SQLite dual-provider persistence.
- **Layer 7: Presentation & AI Copilot:** Next.js 16 (React 19, TypeScript 5) web interface with Groq-accelerated RAG copilot.

---

## 2. Why Combine Natural Language Processing (NLP) with Machine Learning?

- **The Limitation of Pure NLP:** Language models can summarize statutory clauses or detect sentiment, but they cannot evaluate financial market dynamics, portfolio beta, or company balance sheet resilience.
- **The Limitation of Pure Quantitative ML:** Time-series models or regression trees lack understanding of statutory mandates, penalties, regulatory agency empowerment, or compliance deadlines.
- **The Hybrid Synthesis:** Combining dense legal-semantic embeddings with structured financial features (market cap, sector, debt ratio) allows tree-based models to learn non-linear interactions: *e.g., how a 5% carbon compliance penalty specifically impairs high-debt utilities compared to asset-light technology firms.*

---

## 3. Why Domain-Specific Language Representations (FinBERT vs. Legal-RoBERTa)?

- **General LLMs/BERT:** Pre-trained on Wikipedia/general news; treat terms like "liability", "charge", "default", "relief", or "instrument" with colloquial meanings.
- **ProsusAI/FinBERT:** Specifically trained on financial disclosures and analyst transcripts; accurately quantifies financial sentiment, fiscal drag, and market risk sentiment.
- **Legal-RoBERTa:** Pre-trained on judicial decisions and legislative statutes; understands formal statutory syntax, statutory definitions, amendments, penalty clauses, and jurisdictional scopes.
- **Two-Tower Embedding:** Combining both captures both legal severity and financial market sentiment.

---

## 4. Why LightGBM / XGBoost for Structured Econometric Forecasting?

- **Tabular Data Superiority:** Deep neural networks consistently underperform gradient boosted decision trees (GBDT) on heterogeneous tabular datasets with correlated numerical features and categorical indicators.
- **Non-Linear Thresholding:** Tree algorithms naturally discover critical statutory thresholds (e.g., companies exceeding a specific turnover or leverage threshold face abrupt regulatory burdens).
- **Interpretability:** Feature importance scores (Gain, Split) and SHAP values enable rigorous model auditability required in institutional and academic settings.
- **Robustness to Extreme Outliers:** Robust against market anomalies and skewed distribution tails without fragile normalization requirements.

---

## 5. Backtesting Methodology and Eliminating Temporal Leakage

- **Lookahead Bias Definition:** Occurs when information that became known *after* the event date $T_0$ is inadvertently used in model training or feature generation.
- **Platform Countermeasures:**
  1. Strict temporal cutoff: Features are computed using only data available strictly on or before the introduction date.
  2. Walk-forward cross-validation: 5 expanding-window folds; models trained on years $1..k$ are tested strictly on year $k+1$.
  3. No synthetic normalization across the full dataset: Means, variances, and scalers are fitted exclusively on the training split.
  4. 61 automated tests verifying zero temporal leakage across all 940 pairs.

---

## 6. The Anticipation Paradox Explained

- **Concept:** In financial economics, when a bill is introduced to parliament, the market reaction is often negligible or paradoxical because the information was already leaked, debated in the press, or anticipated by industry insiders weeks prior.
- **Academic Formulation:** An event study looking only at post-introduction window $[0, +T]$ fails to capture the true statutory impact if the price drifted in $[-30, -1]$.
- **The Platform's Resolution:**
  - Quantifies pre-event market drift (CAR in $[-30, -1]$).
  - Searches verified pre-event public media (PIB, press).
  - Decouples market signals from public information:
    - Drift + No Media = `MARKET_SIGNAL_ONLY` (Potential private information diffusion).
    - Drift + Verified Media = `PUBLIC_INFORMATION_SUPPORTED` (Public price discovery).
  - Displays strict legal non-accusatory disclaimers.

---

## 7. The Five Event Horizons and Econometric Rationale

1. `[-1, +1]` **(Immediate):** Standard event-study window to isolate pure announcement effect while minimizing market noise.
2. `[-3, +3]` **(Short-Term):** Accommodates legislative news dissemination across trading weekends and delayed corporate disclosure.
3. `[-5, +5]` **(Standard):** Benchmark window for institutional portfolio rebalancing following policy tabling.
4. `[-5, +10]` **(Intermediate):** Captures parliamentary committee referrals, initial debate, and industry pushback.
5. `[-10, +10]` **(Extended):** Captures macroeconomic sector assimilation and systemic valuation adjustments.

---

## 8. Database Architecture: PostgreSQL Canonical vs. SQLite Fallback

- **PostgreSQL (Canonical Production):**
  - Schema enforced across 21 relational tables.
  - Native triggers block modifications to analytical tables.
  - Row-Level Security (RLS) ensures strict tenant data isolation.
  - Connection pooling via Supabase / pgvector readiness.
- **SQLite (Development / CI Fallback):**
  - Embedded zero-dependency engine enabling instant local reproduction on clean machines.
  - Uses file-level database constraints and application repositories to mirror production behavior.
- **Analytical Baseline:** 4,700 predictions, 4,700 decisions, 940 anticipation scores, and 14,100 stakeholder reports remain persisted as deterministic JSON files verified by SHA-256 `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`.

---

## 9. Groq Cloud AI Integration & Security Architecture

- **Selected Model:** `openai/gpt-oss-120b` via Groq LPU (Language Processing Unit) Cloud.
- **Zero Frontend Leakage:** The `GROQ_API_KEY` exists exclusively in backend environment variables. Frontend client requests proxy through `/api/v1/ai/ask`.
- **Latency Optimization:** Groq LPU inference averages 1.2–3.5s per comprehensive analysis, preventing frontend timeouts.
- **Error Handling:** Graceful degradation with honest status reporting when rate limits or provider downtime occur.

---

## 10. AI Grounding, Citations & Prompt Injection Defenses

- **Retrieval-Augmented Generation (RAG):** The model receives verified statutory provisions, official PDF links, and pre-calculated econometric predictions as bounded context.
- **Untrusted User Envelope:** User inputs are wrapped in explicit delimiter envelopes (`=== UNTRUSTED USER QUERY ===`) with instructions forbidding system prompt overrides.
- **Automated Refusals:**
  - Financial advice requests (e.g. "Should I buy SBI?") trigger instant refusals.
  - Price target requests trigger instant refusals.
- **Epistemic Tags:** Outputs enforce `[FACT]`, `[PREDICTION]`, and `[EVIDENCE]` tags to distinguish empirical data from statistical models.

---

## 11. The Two Non-Negotiable Safety Firewalls

### 1. State Bill Statutory Firewall
- **Rule:** State-level bills (Andhra Pradesh, Karnataka, Kerala, Telangana) must produce **strictly ZERO quantitative stock predictions**.
- **Rationale:** Sub-national legislation affects multi-state public firms unequally. Estimating national stock CAR for a state bill without granular state revenue segmentation is statistically invalid and legally misleading.

### 2. Intelligence-Only Company Firewall
- **Rule:** Unlisted entities (e.g. Swiggy unlisted, KSEB, APGENCO) must produce **strictly ZERO quantitative stock predictions**.
- **Rationale:** Equities without public exchange ticker feeds cannot have empirical abnormal return predictions.

---

## 12. Limitations & Critical Academic Self-Awareness

1. **Central Dataset Sample Size:** 20 production bills and 47 companies. While econometrically sound, expanding to the entire Indian statutory corpus requires automated historical event date verification.
2. **External Government Portal Uptime:** Indian government websites exhibit frequent DNS errors and downtime, necessitating local cached PDF mirrors.
3. **Liquidity Assumptions:** Event studies assume liquid market price discovery. Small-cap or thinly-traded securities may experience delayed price discovery.

---

## 13. Future Roadmap

1. Full coverage of all 28 Indian state legislative assemblies.
2. Audio speech-to-text ingestion of Sansad TV parliamentary debates.
3. Multi-agent debate consensus framework for qualitative compliance scoring.
4. Integration with simulated FIX institutional trading protocol.
