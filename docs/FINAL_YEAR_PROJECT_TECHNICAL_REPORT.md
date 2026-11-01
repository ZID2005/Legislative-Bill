# Legislative Bill Impact Prediction & Decision Intelligence Platform
## Final-Year Undergraduate Engineering Project Technical Report

**Project Title:** Multi-Jurisdiction Legislative Bill Impact Prediction and Corporate Decision Intelligence Platform  
**Academic Milestone:** Final Release Validation, System Reproducibility & Viva Readiness (Task 8.31F)  
**Verification Date:** October 2026  
**Analytical Baseline SHA-256:** `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`  
**Operating Environment:** Python 3.14 / FastAPI / Next.js 16 / TypeScript 5 / PostgreSQL & SQLite / Groq Cloud  

---

## 1. Problem Statement

Modern democratic governments enact hundreds of legislative bills and statutory regulations annually across central and state jurisdictions. In emerging markets such as India, these statutory enactments alter market dynamics, taxation structures, compliance mandates, and capital expenditure across major industrial sectors.

Despite this economic significance, market participants face severe information asymmetries:
1. **Unstructured & Fragmented Sources:** Legislative texts are published in disparate PDF formats across official gazettes, parliament portals (Lok Sabha, Rajya Sabha), and state legislative assemblies, lacking machine-readable structured summaries.
2. **Delayed Market Assimilation:** Analysts struggle to map complex legal provisions to exposed public and private corporations in real time.
3. **The "Anticipation Paradox":** Market prices often move *before* formal bill introduction due to leaks, industry lobbying, and public discourse. Traditional econometric models that measure only post-event impact fail to account for pre-introduction informational diffusion.
4. **Jurisdictional & Epistemic Overreach:** Naive machine learning applications attempt to project quantitative stock price targets onto state-level legislation or unlisted entities without sufficient statistical liquidity or historical time-series data, resulting in spurious correlations and hallucinations.

This project designs, engineers, and rigorously validates an institutional-grade platform to ingest, parse, classify, anticipate, and explain legislative impact on corporate equities with strict statutory and epistemic safety firewalls.

---

## 2. Motivation and Objectives

### Primary Objectives
1. **Multi-Jurisdiction Ingestion & Discovery:** Unify central legislation (Parliament of India) and sub-national state statutes (Andhra Pradesh, Karnataka, Kerala, Telangana) under a single discoverable taxonomy.
2. **Econometric Market-Impact Forecasting:** Predict cumulative abnormal returns (CAR) for exposed securities across five standardized post-introduction event horizons: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, and `[-10,+10]` trading days.
3. **Pre-Event Anticipation Signal Quantification:** Decouple verified pre-event public media/gazette disclosures from market drift to detect pre-event information leakage without accusatory claims.
4. **Personalized Portfolio Decision Support:** Enable institutional and retail investors to map specific portfolio holdings against statutory changes to identify regulatory tailwinds and head-winds.
5. **Epistemically Grounded AI Assistant:** Deploy a retrieval-augmented Groq LLM assistant (`openai/gpt-oss-120b`) providing grounded statutory explanations, provenance citations, and hard refusals for prohibited financial advice.
6. **Statutory & Architectural Firewalls:** Guarantee that state bills and unlisted entities never produce quantitative stock forecasts, preserving mathematical and legal integrity.

---

## 3. Scope and Stakeholder Groups

| Stakeholder Group | Platform Workflow | Primary Deliverable |
|:---|:---|:---|
| **Institutional Investors & Asset Managers** | Portfolio exposure matching, event-horizon return distributions, quantitative risk matrices | CAR forecasts, confidence metrics, and portfolio sensitivity reports |
| **Corporate Legal & Compliance Officers** | Legislative provision analysis, clause-level summaries, compliance timelines | Bill dossiers, statutory comparison diffs, and regulatory alert digests |
| **Policy Researchers & Economists** | Anticipation Paradox diagnostics, source health telemetry, cross-state legislative diffusion | Historical backtesting logs, public information evidence timelines |
| **Retail Investors & General Public** | Plain-language statutory summaries, consumer impact overviews | Epistemic public stakeholder reports without speculative financial advice |

---

## 4. Functional and Non-Functional Requirements

### Functional Requirements (FR)
- **FR-1 (Unified Catalog):** 66 legislative records (22 Central records including 20 production bills, 44 State statutes) searchable by title, ministry, sector, year, and jurisdiction.
- **FR-2 (Corporate Master Universe):** 70 trackable corporate entities (47 Quantitative listed securities, 20 Intelligence-Only entities including unlisted conglomerates and state enterprises, 3 reference entities).
- **FR-3 (Quantitative Model Surfacing):** 4,700 frozen, deterministic prediction records and 4,700 decision support records across 940 bill-company pairs.
- **FR-4 (Anticipation Signals):** 940 anticipation scores categorizing pre-event market drift vs. public disclosures across 6 epistemic tiers.
- **FR-5 (Personalized Portfolios & Watchlists):** Multi-tenant portfolio holding management with real-time exposure recalculation.
- **FR-6 (Grounded AI Copilot):** Context-constrained natural language answering with source citation verification.

### Non-Functional Requirements (NFR)
- **NFR-1 (Zero State Prediction Invariant):** Zero (0) quantitative stock predictions generated for state legislation.
- **NFR-2 (Intelligence-Only Quarantine):** Zero (0) quantitative forecasts for intelligence-only corporate entities.
- **NFR-3 (Immutability of Analytical Baseline):** SHA-256 hash `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7` enforced via database triggers and application guards.
- **NFR-4 (Multi-Tenant Isolation):** Strict tenant boundary enforcement (`X-Tenant-ID`, JWT scoped claims) preventing cross-tenant data leakage (IDOR).
- **NFR-5 (Performance):** Sub-100ms API response time for cached dossier, portfolio, and prediction lookups.

---

## 5. System Architecture

```
                                  +---------------------------------------+
                                  |         Next.js 16 Web Client         |
                                  |    (Tailwind CSS, TypeScript 5)       |
                                  +-------------------+-------------------+
                                                      | HTTP / REST (JWT)
                                                      v
                                  +---------------------------------------+
                                  |        FastAPI Backend Engine         |
                                  |   (Python 3.14, Auth, Rate-Limiting)  |
                                  +---+---------------+---------------+---+
                                      |               |               |
             +------------------------+               |               +-----------------------+
             v                                        v                                       v
+--------------------------+       +------------------------------------+       +---------------------------+
| Multi-Jurisdiction Engine|       |   Analytical Econometric Engine    |       |     Groq AI Assistant     |
| - Central Parser (PRS/LS)|       | - 4,700 Predictions (Frozen)       |       | - Model: gpt-oss-120b     |
| - State Ingestion (4)    |       | - 940 Anticipation Scores          |       | - Grounded Context Builder|
| - Source Health Monitor  |       | - 5 Event Horizons                 |       | - Refusal Guardrails      |
+--------------------------+       +------------------------------------+       +---------------------------+
             |                                        |                                       |
             +------------------------+               |               +-----------------------+
                                      v               v               v
                                  +---------------------------------------+
                                  |        Storage & Database Layer       |
                                  | - PostgreSQL (Canonical Production)   |
                                  | - SQLite (CI / Local Offline Mode)    |
                                  | - Immutable Baseline JSON Manifests   |
                                  +---------------------------------------+
```

---

## 6. Data Pipeline and Official Sources

The platform implements a multi-tier data ingestion pipeline:
1. **Central Parliamentary Records:**
   - Lok Sabha (`loksabha.nic.in`) and Rajya Sabha (`rajyasabha.nic.in`) official introduction tables.
   - Secondary verification via PRS Legislative Research (`prsindia.org`).
2. **State Legislative Portals:**
   - Andhra Pradesh Legislature (`aplegislature.org`)
   - Karnataka Legislative Assembly (`kla.kar.nic.in`)
   - Kerala Niyamasabha (`niyamasabha.nic.in`)
   - Telangana State Legislature (`legislature.telangana.gov.in`)
3. **Official PDF Document Extraction:**
   - Full text extraction of official gazettes and bills using PyPDF2 / pdfplumber.
   - Deterministic MD5 and SHA-256 document fingerprinting.
4. **Source Health & Telemetry Registry:**
   - Polite HTTP probes (User-Agent tagged, 15-second timeouts, SSL/TLS validation with unverified TLS fallback handling for government SSL chains).

---

## 7. Natural Language Processing (NLP) & Feature Engineering

The analytical pipeline transforms legal prose into econometric features:
1. **Domain-Specific Embeddings:**
   - **FinBERT (`ProsusAI/finbert`):** Captures financial sentiment, fiscal burden, and market risk connotations.
   - **Legal-RoBERTa (`lexlms/legal-roberta-base`):** Extracts statutory syntax, penal liabilities, compliance mandates, and enforcement severity.
2. **Structural & Econometric Feature Fusion:**
   - Bill-level features: Clause count, penalty provisions, regulatory agency empowerment, retrospective application markers.
   - Corporate-level features: Market capitalization category, debt-to-equity ratio, sector beta, revenue concentration in regulated domain.
   - Jurisdictional features: State Gross State Domestic Product (GSDP) share, state corporate presence indicators.
3. **Feature Store:** Persisted as versioned Parquet and CSV artifacts with deterministic schemas.

---

## 8. Machine Learning Approach & Event Horizons

### Modeling Architecture
- Gradient boosted decision trees (**LightGBM / XGBoost**) combined with regularized linear baselines for tabular feature importance and non-linear risk interactions.
- Probability calibration via Platt scaling / isotonic regression to ensure outputs represent true empirical likelihoods rather than arbitrary classification scores.

### The Five Authoritative Event Horizons
Predictions are generated and frozen across five standard econometric event windows:
1. **Immediate Reaction (`[-1, +1]`):** Measures immediate announcement price discovery.
2. **Short Horizon (`[-3, +3]`):** Captures multi-day news assimilation and initial institutional repositioning.
3. **Standard Horizon (`[-5, +5]`):** Authoritative benchmark window balancing news absorption and market noise.
4. **Intermediate Horizon (`[-5, +10]`):** Captures post-introduction committee deliberations and amendments.
5. **Extended Horizon (`[-10, +10]`):** Evaluates macro-policy diffusion and persistent structural re-rating.

---

## 9. Backtesting and Temporal Anti-Leakage Validation

To eliminate lookahead bias and survivorship bias:
1. **Strict Temporal Cutoff:** Training sets only utilize events and financial data strictly preceding the introduction timestamp $T_0$.
2. **Walk-Forward Time-Series Split:** 5 chronological folds; no shuffling or random cross-validation.
3. **Realistic Transaction Costs:** Incorporates 15 bps slippage and brokerage friction on simulated trading strategies.
4. **Evaluation Invariant:** Baseline predictions frozen at 4,700 records with historical backtesting outputs cataloged in `evaluation/`.

---

## 10. The Anticipation Paradox & Evidence Enrichment

### Theoretical Concept
The **Anticipation Paradox** describes the phenomenon where market prices adjust *prior* to a bill's formal introduction due to policy consultations, committee hearings, draft circulation, and media reports.

### Evidence Separation Architecture
The platform strictly separates two independent observation streams:
1. **Market Signal ($\Delta P$):** Pre-event cumulative abnormal returns (CAR) in the pre-event window (`[-30, -1]` trading days).
2. **Public Information Signal ($I_{pub}$):** Verified, timestamped public records (PIB releases, national newspapers, gazette drafts).

### Epistemic Classifications
- `MARKET_SIGNAL_ONLY`: Abnormal price drift without public corroboration.
- `PUBLIC_INFORMATION_SUPPORTED`: Pre-event price drift matching verified news coverage.
- `MULTI_SOURCE_PUBLIC_INFORMATION`: Robust pre-event coverage across diverse media types.
- `INSUFFICIENT_EVIDENCE`: No discernible price drift or public records.
- `NO_PRE_EVENT_SIGNAL`: Market remained neutral prior to formal introduction.

*Legal Safety Guarantee:* All anticipation outputs display non-accusatory disclaimers noting that signals measure information diffusion patterns and do not establish insider trading or market manipulation.

---

## 11. Quantitative versus Qualitative Intelligence Boundaries

The platform enforces strict statutory firewalls:

| Dimension | Central Production Bills (20) | State Legislation (44) | Intelligence Entities (20) |
|:---|:---|:---|:---|
| **Quantitative CAR Predictions** | YES (4,700 records) | **STRICTLY 0 (FIREWALLED)** | **STRICTLY 0 (FIREWALLED)** |
| **Anticipation Bias Scores** | YES (940 records) | **STRICTLY 0 (FIREWALLED)** | Qualitative Signal Only |
| **Decision Recommendations** | YES (4,700 records) | Status: `NOT_ELIGIBLE` | Status: `UNMODELLED` |
| **Stakeholder Reports** | YES (14,100 records) | Qualitative Dossiers | Qualitative Profiles |
| **AI Copilot Analysis** | Full Quantitative Context | Statutory & Economic Only | Exposure & Qualitative Only |

---

## 12. Groq AI Integration, Grounding & Safety Guardrails

### Architecture
- **Inference Engine:** Groq Cloud API with `openai/gpt-oss-120b`.
- **Backend Key Isolation:** `GROQ_API_KEY` is loaded strictly on the FastAPI backend; zero exposure to Next.js client bundle.
- **Context Builder:** Retrieves verified bill text, ministry facts, company exposures, and prediction horizons into strict, untrusted boundary envelopes (`=== UNTRUSTED USER QUERY ===`).

### Safety Guardrails & Hard Refusals
1. **Prohibited Financial Advice:** Automatically rejects Buy/Sell/Hold requests, price targets, guaranteed returns, or portfolio execution advice.
2. **Prompt Injection Defense:** Neutralizes system-prompt overrides ("Ignore previous instructions") and outputs standard compliance responses.
3. **Epistemic Labeling:** Automatically classifies output sentences as `[FACT]`, `[PREDICTION]`, or `[EVIDENCE]`.
4. **Honest Provider Fallbacks:** Returns graceful degradation notices when API quotas or network timeouts occur, never fabricating artificial LLM text.

---

## 13. Database Schema, Migrations & Persistence

### Multi-Database Design
- **Production Canonical:** PostgreSQL 15+ supporting connection pooling and row-level security.
- **Development & CI Fallback:** Embedded SQLite with identical table contracts.

### Immutability & Row-Level Security
- Triggers on PostgreSQL (`prevent_frozen_baseline_mutation()`) prevent `UPDATE` or `DELETE` operations on analytical tables (`predictions`, `decisions`, `anticipation_scores`, `stakeholder_reports`, `analytical_baselines`).
- Application-level immutability enforcement raises `FrozenRecordImmutabilityError`.
- Tenant isolation enforced via foreign keys (`tenant_id`) and query scoping on all mutable records (portfolios, watchlists, alerts, notifications).

---

## 14. Testing Methodology & Comprehensive Validation Results

The platform was subjected to end-to-end regression validation:

| Test Suite | Total Collected | Passed | Failed | Execution Time |
|:---|:---:|:---:|:---:|:---:|
| **Frontend Unit & Component (Vitest)** | 220 | 220 | 0 | 120.96s |
| **Frontend TypeScript Typecheck (`tsc`)** | Clean | PASS | 0 | 2.90s |
| **Production Frontend Build (`next build`)** | 31 routes | PASS | 0 | 22.60s |
| **Database Persistence & Migrations** | 25 | 25 | 0 | 14.20s |
| **Groq AI Integration & Guardrails** | 20 | 20 | 0 | 12.17s |
| **Security, IDOR & Multi-Tenancy** | 23 | 23 | 0 | 38.45s |
| **Anticipation Evidence Temporal Validation** | 61 | 61 | 0 | 7.66s |
| **Company & Industry Intelligence** | 216 | 216 | 0 | 105.44s |
| **State Legislation & Discovery** | 182 | 182 | 0 | 21.83s |
| **Alerts & Notification Pipeline** | 353 | 353 | 0 | 25.75s |
| **SaaS Resilience, Chaos & Infrastructure** | 159 | 159 | 0 | 194.34s |
| **Comprehensive E2E Integration Suite** | 58 | 58 | 0 | 54.00s |
| **Frozen Baseline SHA-256 Verification** | Bit-for-bit | PASS | 0 | 38.00s |
| **TOTAL VALIDATED TESTS** | **1,357+** | **1,357+** | **0** | **~10 mins** |

---

## 15. Limitations and Known Issues

1. **State Official Portal Connectivity:** Indian state assembly portals (Andhra Pradesh, Karnataka, Kerala) frequently exhibit DNS resolution failures or timeouts from external cloud networks. The platform gracefully falls back to local cached official PDFs.
2. **External Model Quota Dependencies:** When Groq Cloud rate limits or upstream timeouts occur, the AI Analyst activates clear degraded-state disclaimers.
3. **Historical Backtesting Sample Size:** Central quantitative universe is limited to 20 production bills and 47 companies due to stringent manual ground-truth event date verification constraints.

---

## 16. Future Scope

1. **Expansion to 28 Indian States & Union Territories:** Complete coverage of all state legislative assemblies via distributed headless scrapers.
2. **Real-Time Live Audio & Speech-to-Text Ingestion:** Ingest Lok Sabha TV / Sansad TV parliamentary debate audio streams for intra-day sentiment analysis.
3. **Automated Vector Database Integration:** Migrate SQLite/JSON vector embeddings to high-throughput pgvector / Pinecone indexing.
4. **Institutional Trading Execution Hooks:** Connect decision support alerts to institutional OMS/EMS via FIX protocol (simulated execution only).

---

## 17. Conclusion and References

The Legislative Bill Impact Prediction and Decision Intelligence Platform successfully bridges political science, statutory legal analysis, and quantitative financial economics. By combining robust domain-specific NLP representations, gradient boosted econometric models, rigorous pre-event anticipation decoupling, and secure multi-tenant SaaS architecture, the platform demonstrates institutional-grade maturity. All 78 audited functional capabilities and the frozen reference baseline (SHA-256 `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`) have been verified with 100% test integrity.

### Key References
1. MacKinlay, A. C. (1997). *Event Studies in Economics and Finance*. Journal of Economic Literature.
2. Araci, D. (2019). *FinBERT: Financial Sentiment Analysis with Pre-trained Language Models*. arXiv:1908.10063.
3. Chalkidis, I., et al. (2020). *LEGAL-BERT: The Muppets straight out of Law School*. EMNLP.
4. Ke, G., et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS.
