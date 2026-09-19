# Legislative Intelligence Dashboard

A professional Streamlit dashboard for the **Legislative Intelligence & Market Impact Prediction System** — India 2024.

## Quick Start

```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`

## Features

| Page | Description |
|---|---|
| 🏠 Overview & New Bills | **[Task 7.4.1]** Newly Introduced Bills feed + KPI cards + Company exposure |
| 🌐 Global Overview | Production scope, system summary, executive overview |
| 📜 Bill Explorer | Per-bill deep dives with impact distributions |
| 🏢 Company Explorer | Corporate exposure profiles and decision scores |
| 📈 Investor View | Probabilistic direction, market-moving probability, pricing-in |
| 💼 Business View | Regulatory exposure, compliance implications |
| 🌍 Public View | Plain-English legislative summaries |
| ⚡ Risk Overview | Risk distributions and 2D risk matrices |
| 🛡️ Anticipation Overview | Pre-event market activity analysis |
| 🧠 Model Explainability | SHAP global feature importances |
| 📊 Backtesting Summary | Walk-forward temporal backtests |
| 📐 Methodology | Mathematical foundations and architecture |

## Task 7.4.1 — New Components

| File | Purpose |
|---|---|
| `dashboard/pages/overview.py` | Main overview page with Newly Arrived Bills |
| `dashboard/services/dashboard_service.py` | Production data access service |
| `dashboard/components/bill_cards.py` | Bill card UI components |
| `dashboard/components/cards.py` | KPI summary metric cards |
| `dashboard/components/filters.py` | Enhanced filter panel for bill feed |
| `dashboard/components/tables.py` | Company exposure and bills summary tables |
| `tests/test_dashboard_service.py` | DashboardService unit tests |
| `tests/test_dashboard_components.py` | Component unit tests |
| `docs/dashboard.md` | Complete documentation |

## Production Scope (Task 7.4.1 Verified)

| Metric | Value |
|---|---|
| Production Bills | 20 (2024 parliamentary session) |
| Production Companies | 47 (BSE/NSE-listed) |
| Decision Records | 4,700 (20 × 47 × 5 windows) |
| Stakeholder Reports | 14,100 |
| Anticipation Scores | 940 |

## Research Integrity

- ✅ Read-only: Dashboard never modifies predictions, risk scores, or anticipation scores
- ✅ No retraining: Dashboard never triggers ML retraining
- ✅ Correct dates: Bill recency uses `introduction_date` (legislative tabling date) only
- ✅ No fabrication: Missing data shown as "Not available"
- ✅ No future leakage: Post-event data excluded from prediction display

## Running Tests

```bash
# Task 7.4.1 tests
pytest tests/test_dashboard_service.py -v
pytest tests/test_dashboard_components.py -v

# Full regression
pytest tests/ -v
```

## Documentation

See [`docs/dashboard.md`](../docs/dashboard.md) for full architecture and data source documentation.
