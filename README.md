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
│   └── label_generator.py   # [Task 6] Event-study CAR computation
│
├── models/                  # Model definitions and training
│   ├── __init__.py
│   ├── artefacts/           # Serialised model files (git-ignored)
│   ├── trainer.py           # [Task 8] Training pipeline (LightGBM + Optuna)
│   └── predictor.py         # [Task 9] Inference engine
│
├── features/                # Feature engineering pipelines
│   ├── __init__.py
│   └── feature_builder.py   # [Task 7] Feature matrix construction
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

# Run tests
pytest tests/ -v

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
| **Task 2** | Company & Market Data Acquisition | 🔲 Planned |
| **Task 3** | Data Validation & Schema Enforcement | 🔲 Planned |
| **Task 4** | NLP Pipeline (Legal Text Understanding) | 🔲 Planned |
| **Task 5** | Sector & Company Mapping | 🔲 Planned |
| **Task 6** | Ground-Truth Label Generation (Event Study) | 🔲 Planned |
| **Task 7** | Feature Engineering | 🔲 Planned |
| **Task 8** | Model Training & Evaluation | 🔲 Planned |
| **Task 9** | Prediction API | 🔲 Planned |
| **Task 10** | Knowledge Dashboard | 🔲 Planned |

See [docs/roadmap.md](docs/roadmap.md) for full details.

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
