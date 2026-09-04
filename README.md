# 🏛️ Legislative Intelligence & Market Impact Prediction System

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Foundation%20%28Task%200%29-yellow)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-brightgreen)](https://pep8.org/)

---

## 📌 Project Overview

The **Legislative Intelligence & Market Impact Prediction System** is an AI-powered platform designed to:

1. **Understand** Indian Central Government legislative bills using advanced NLP.
2. **Predict** the potential economic impact of bills on:
   - Stock market sectors
   - Individual listed companies
   - Investors
   - Businesses
   - The general public
3. **Serve as a knowledge platform** where users can learn about existing bills, newly introduced bills, historical market reactions, and AI-predicted future impacts.

> **Version 1 (MVP)** focuses exclusively on **Central Government Bills**.  
> State-level bills are planned for a future release.

---

## 🎯 Objectives

| Objective | Description |
|-----------|-------------|
| Legislative Understanding | Parse, classify, and extract key provisions from Indian bills |
| Sector Mapping | Map bill provisions to affected SEBI-recognised sectors |
| Company Linking | Link bill impact to BSE/NSE listed companies |
| Market Impact Prediction | Predict short- and medium-term stock price movements |
| Knowledge Platform | Expose structured, searchable bill intelligence to end users |

---

## 🗂️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Data Ingestion                    │
│  bill_scraper  │  company_loader  │  market_loader   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                   Validation Layer                   │
│             validator  │  schema checks              │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              Enrichment & Mapping Layer              │
│      sector_mapper  │  label_generator               │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                  Feature Engineering                 │
│                    feature_builder                   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                   Modelling Layer                    │
│              trainer  │  predictor                   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                    Dashboard / API                   │
│                      dashboard                       │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Folder Structure

```
Legislative-bill/
│
├── config/                  # Centralised configuration
│   ├── __init__.py
│   ├── settings.py          # All project-level settings (env-driven)
│   └── logging_config.py    # Logging setup (console + rotating file)
│
├── data/                    # All data artefacts (git-ignored)
│   ├── raw/                 # Unmodified source data
│   ├── processed/           # Cleaned, transformed data
│   ├── bills/               # Downloaded bill PDFs and metadata
│   ├── companies/           # BSE/NSE company master data
│   ├── market/              # Historical market price data
│   └── external/            # Third-party supplementary data
│
├── scraper/                 # Data acquisition modules
│   ├── __init__.py
│   ├── bill_scraper.py      # [Task 1] Scrapes bills from PRS, Lok Sabha, Rajya Sabha
│   ├── company_loader.py    # [Task 2] BSE/NSE company master loader
│   └── market_loader.py     # [Task 2] Historical OHLCV price loader
│
├── validation/              # Data quality and schema validation
│   ├── __init__.py
│   └── validator.py         # [Task 3] pydantic-based schema validation
│
├── mapping/                 # Domain mapping logic
│   ├── __init__.py
│   └── sector_mapper.py     # [Task 5] Bill → sector / company mapping
│
├── labeling/                # Ground-truth label generation
│   ├── __init__.py
│   └── label_generator.py   # [Task 4.4] LabelGenerator — converts StatisticalResults to labels
│
├── models/                  # Model definitions and training
│   ├── __init__.py
│   ├── artefacts/           # Serialised model files (git-ignored)
│   ├── trainer.py           # [Task 8] Training pipeline (LightGBM + Optuna)
│   ├── predictor.py         # [Task 9] Inference engine
│   └── explainability/      # [Task 6.3] SHAP explainability engine
│
├── explainability/          # SHAP outputs (git-ignored)
│   ├── <target>/
│   │   └── <model_type>/
│   │       ├── shap_values.parquet
│   │       ├── feature_importance.csv
│   │       ├── local_explanations.json
│   │       ├── summary_plot.png
│   │       ├── bar_plot.png
│   │       └── dependence_plots/
│   ├── global_summary.json
│   ├── model_comparison.json
│   └── feature_comparison.png
│
├── features/                # Feature engineering pipelines
│   ├── __init__.py
│   ├── feature_builder.py   # [Task 5.1] FeatureBuilder — public entry-point
│   └── feature_engine.py    # [Task 5.1] FeatureEngineeringEngine — merge + validate + persist
│
├── dashboard/               # UI layer (Streamlit / FastAPI)
│   ├── __init__.py
│   └── dashboard.py         # [Task 10] Knowledge platform dashboard
│
├── utils/                   # Shared helper utilities
│   ├── __init__.py
│   ├── file_utils.py        # Atomic JSON/CSV I/O, directory helpers
│   ├── date_utils.py        # Date parsing, business-day logic
│   └── text_utils.py        # Text cleaning, slugify, truncate
│
├── notebooks/               # Exploratory analysis notebooks
│
├── tests/                   # Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py          # Shared pytest fixtures
│   └── test_placeholder.py  # Task 0 smoke tests
│
├── docs/                    # Project documentation
│   ├── architecture.md      # System architecture and design decisions
│   ├── roadmap.md           # Development roadmap
│   ├── data_sources.md      # Data source catalogue
│   ├── methodology.md       # NLP + event-study methodology
│   └── future_work.md       # Known limitations and future plans
│
├── logs/                    # Runtime logs (git-ignored)
│
├── .env.example             # Environment variable template
├── .gitignore
├── LICENSE                  # MIT
├── main.py                  # CLI entry point
├── pyproject.toml           # Tool configuration (pytest, black, mypy)
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.11+
- `pip`
- (Recommended) A virtual environment manager

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/legislative-bill.git
cd legislative-bill

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment variables
cp .env.example .env
# Edit .env with your actual values (API keys, DB URL, etc.)

# 5. Verify the setup
python main.py status
```

---

## 🚀 Running the Project

```bash
# Run the main entry point (defaults to status check)
python main.py

# Explicit status check
python main.py status

# Show all commands
python main.py --help

# Discover and ingest bill metadata (Task 1A.1 & 1A.2)
python main.py ingest --source prs --year 2024

# Download official PDF documents for ingested bills (Task 1A.3)
python main.py download-docs --year 2024

# Extract text and generate the legislative corpus (Task 1A.4)
python main.py extract-text --year 2024

# Build knowledge records from corpus (Task 1A.5 & 1A.5.1)
python main.py build-knowledge --year 2024

# Ingest and normalize company master records (Task 2.1 & 2.2)
python main.py ingest-companies

# Ingest and normalize historical market prices and indices back to 2014 (Task 3.1 & Enhancement)
# Downloads historical daily prices from 01 January 2014 through today for all indices and companies.
python main.py ingest-market --start-date 2014-01-01

# Build deterministic bill-company mappings (Task 2.3)
python main.py build-mappings --year 2024

# Estimate expected returns parameters using OLS market model (Task 4.1)
python main.py estimate-market-models --year 2024

# Compute abnormal returns and CARs via Advanced Event Study Engine (Task 4.2)
python main.py run-event-study --year 2024

# Compute statistical significance of event study CARs (Task 4.3)
python main.py run-statistical-significance --year 2024

# Generate ground-truth ML labels from statistical results (Task 4.4)
python main.py generate-labels --year 2024

# Regenerate all labels (overwrite existing)
python main.py generate-labels --year 2024 --force-refresh

# Build unified ML feature dataset — Parquet + optional CSV (Task 5.1)
python main.py build-features

# Full rebuild of feature dataset (ignore existing records)
python main.py build-features --rebuild

# Export feature dataset to CSV
python main.py build-features --export-csv

# Generate reusable NLP embeddings for bills (Task 5.2)
python main.py generate-embeddings --model finbert --pooling mean

# Regenerate embeddings (overwrite existing cache)
python main.py generate-embeddings --model finbert --force-refresh

# Perform feature fusion combining structured features and embeddings (Task 5.3)
# Supported modes: structured, finbert, legal, structured-finbert, structured-legal, hybrid
python main.py build-fusion --mode hybrid

# Build all six fusion modes in sequence
python main.py build-fusion --all

# Force full rebuild of fusion datasets, ignoring existing records
python main.py build-fusion --mode hybrid --rebuild

# Run feature selection to prune uninformative features (Task 5.4)
python main.py select-features --mode structured

# Train ML classifiers to predict legislative market impact (Task 6.1)
# Trains 4 targets × 3 models = 12 classifiers with chronological TimeSeriesSplit
python main.py train --mode structured

# Train a single target with a specific model
python main.py train --target direction --model-type lgbm

# Force rebuild of training datasets before training
python main.py train --rebuild-datasets

# Skip models already trained
python main.py train --skip-existing

# Evaluate every trained model and compare performance (Task 6.2)
python main.py evaluate-models --mode structured

# Rebuild datasets prior to running evaluation
python main.py evaluate-models --rebuild-dataset

# Generate SHAP global and local explanations for all trained models (Task 6.3)
python main.py explain-models --all

# Explain only the direction classifier with all model types
python main.py explain-models --target direction

# Explain only LightGBM models across all targets
python main.py explain-models --model lgbm

# Explain a single (target, model) combination
python main.py explain-models --target market_moving --model xgboost

# Run chronological walk-forward historical backtesting (Task 6.4)
python main.py backtest-models --all

# Run pre-event anticipation bias and information leakage analysis (Task 6.5)
python main.py analyze-anticipation

# Force refresh anticipation records
python main.py analyze-anticipation --force-refresh

# Generate final predictions (Task 7.1)
python main.py generate-predictions --year 2024

# Force re-infer and refresh cached predictions
python main.py generate-predictions --year 2024 --force-refresh

# Generate decision support and composite risk scoring (Task 7.2)
python main.py generate-decision-support --year 2024

# Force regenerate decision support interpretations
python main.py generate-decision-support --year 2024 --force-refresh

# Generate decision support for a specific bill and company
python main.py generate-decision-support --bill-id the-telecom-act-2024 --company-isin INE002A01018

# Generate stakeholder reports for Investors, Businesses, and the Public (Task 7.3)
python main.py generate-reports --stakeholder investor

# Generate reports for a specific bill in Markdown format
python main.py generate-reports --bill-id the-telecom-act-2024 --format markdown

# Generate business perspective for a specific company in CSV format
python main.py generate-reports --company-isin INE002A01018 --stakeholder business --format csv

# Generate aggregate bill-level report across all mapped companies
python main.py generate-reports --bill-id the-telecom-act-2024 --generate-bill-report

# Generate aggregate company legislative exposure report
python main.py generate-reports --company-isin INE002A01018 --generate-company-report

# Force full regeneration of stakeholder reports
python main.py generate-reports --force-refresh

# Run tests
pytest tests/ -v

# Run ML training tests specifically
python main.py test --cov=models/training --cov=storage/model_repository.py (placeholder, or pytest)
pytest tests/test_ml_training.py -v
pytest tests/test_model_evaluation.py -v --cov=models/evaluation --cov=storage/evaluation_repository.py

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# Check code style
flake8 . --max-line-length=100

# Format code
black .
```

---

## 🗺️ Development Roadmap

| Phase | Task | Status |
|-------|------|--------|
| **Task 0** | Project Foundation & Architecture | ✅ Complete |
| **Task 1** | Bill Data Ingestion (Scraping + Storage) | ✅ Complete |
| **Task 2** | Company & Market Data Acquisition | ✅ Complete |
| **Task 3** | Data Validation & Schema Enforcement | ✅ Complete |
| **Task 4** | NLP Pipeline (Legal Text Understanding) | ⚠️ In Progress |
| **Task 4.1** | Market Model Engine (OLS) | ✅ Complete |
| **Task 4.2** | Advanced Event Study Engine | ✅ Complete |
| **Task 4.3** | Statistical Significance Engine | ✅ Complete |
| **Task 4.4** | Label Generation Engine (Ground Truth) | ✅ Complete |
| **Task 5** | Sector & Company Mapping | ✅ Complete |
| **Task 5.1** | Unified Feature Engineering Engine | ✅ Complete |
| **Task 5.2** | NLP Embedding Engine | ✅ Complete |
| **Task 5.3** | Feature Fusion Engine | ✅ Complete |
| **Task 5.4** | Feature Selection Engine | ✅ Complete |
| **Task 6** | Ground-Truth Label Generation (Event Study) | ✅ Complete |
| **Task 6.1** | ML Training Engine (4 classifiers × 3 models) | ✅ Complete |
| **Task 6.2** | ML Evaluation Engine (Comparative Rankings + Errors) | ✅ Complete |
| **Task 6.3** | Explainability Engine (SHAP Global + Local Explanations) | ✅ Complete |
| **Task 6.4** | Historical Backtesting Engine (Walk-Forward, Anti-Leakage) | ✅ Complete |
| **Task 6.5** | Anticipation Bias / Pre-Event Information Analysis Engine | ✅ Complete |
| **Task 7.1** | Final Prediction & Decision Engine (Forward Inference) | ✅ Complete |
| **Task 7.2** | Decision Support & Risk Scoring Engine (Stakeholder Perspectives) | ✅ Complete |
| **Task 7.3** | Stakeholder Reporting Engine (Investor, Business, Public) | ✅ Complete |
| **Task 7.4** | Interactive Dashboard & Decision-Support Interface (Streamlit) | ✅ Complete |

See [docs/roadmap.md](docs/roadmap.md) for full details.

---

## 🖥️ Interactive Dashboard (Task 7.4)

Launch the multi-stakeholder Streamlit decision-support dashboard:

```bash
# Launch on default port 8501
python main.py serve

# Launch on custom port and host
python main.py serve --port 8080 --host 0.0.0.0

# Using alias
python main.py dashboard
```

### Dashboard Exploration Lenses
1. **Global Overview**: Portfolio KPIs, summary metrics, and scope reconciliation diagnostics.
2. **Bill Explorer**: Full legislative dossier, company exposures, and bill-level reports.
3. **Company Explorer**: Corporate risk profiles, relevant bills, and company-level reports.
4. **Investor View**: Probabilistic directional return, market-moving odds, and pricing-in discounts.
5. **Business View**: Operational risk, compliance implications, and ministerial oversight.
6. **Public View**: Plain-English societal significance and economic context.
7. **Risk Overview**: Statistical distributions, summary stats, and interactive 2D risk matrices.
8. **Anticipation Overview**: Pre-event information diffusion auditing and non-insider-trading legal notice.
9. **Model Explainability**: Pre-computed SHAP global feature importances and cross-model rankings.
10. **Backtesting Summary**: Walk-forward Sharpe ratios, drawdowns, and model vs strategy distinctions.
11. **Methodology**: 10-stage architecture flow and governance invariants.

---

## 🔒 Environment Variables

All secrets and environment-specific configuration are managed via `.env`.  
**Never commit `.env` to version control.**

See [`.env.example`](.env.example) for the full list of required variables.

---

## 📚 Documentation

Full project documentation lives in [`docs/`](docs/):

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Data Sources](docs/data_sources.md)
- [Methodology](docs/methodology.md)
- [Future Work](docs/future_work.md)

---

## 🧪 Testing

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/ -m unit -v

# Integration tests (requires network)
pytest tests/ -m integration -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 📐 Code Style

This project follows:
- **PEP 8** — Python style guide
- **Type hints** — all public functions are annotated
- **Docstrings** — all public modules, classes, and functions have docstrings
- **Black** — auto-formatter (100-char line length)
- **isort** — import sorting (black-compatible profile)

---

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes with tests
3. Run `pytest` and `flake8` before pushing
4. Open a pull request with a clear description

---

## 📄 License

[MIT](LICENSE) © 2024 Legislative Intelligence Project
