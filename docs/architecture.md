# Architecture

## Overview

The Legislative Intelligence & Market Impact Prediction System follows a
**layered pipeline architecture**, managed by a centralized **Service Layer** that coordinates business logic and orchestrates workflows across underlying domains.

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation Layer  (main.py / dashboard.py)                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │  Requests
┌────────────────────────────────▼────────────────────────────────┐
│  Service Layer  (services/)                                     │
│  Orchestrates workflows & injects domain models / repositories │
└──────┬─────────────────────────┬─────────────────────────┬──────┘
       │ Ingestion Flows         │ Predictions             │ Explanations (LLM)
┌──────▼──────────────────┐┌─────▼───────────┐┌────────────▼──────┐
│ Ingestion Layer         ││ Inference Layer ││ Explanation Layer │
│ ingestion/              ││ models/         ││ services/         │
└──────┬──────────────────┘└─────┬───────────┘└────────────┬──────┘
       │ Reads/Writes            │ Reads/Writes            │ Reads/Writes
┌──────▼─────────────────────────▼─────────────────────────▼──────┐
│ Data / Persistence Layer (storage/ repositories)                │
└─────────────────────────────────────────────────────────────────┘
```

## Service Layer (Coordination Facade)

The root-level `services/` package defines the orchestration facade for the platform. By utilizing Dependency Injection and Loose Coupling, it ensures presentation layers (CLI, Streamlit dashboards) never reach directly into deep parser, connector, or feature-engineering implementations.

Key services defined:
1. **`IngestionService`**: A single point of coordination for parliament bills, company masters, and stock price histories. Delegates parliament workflows to `ParliamentIngestionService` and triggers validation and catalog indexing.
2. **`PredictionService`**: Handles feature extraction and triggers ML models (LightGBM/FinBERT) to evaluate market impact on public companies.
3. **`ExplanationService`**: Uses a pluggable abstract `LLMProvider` interface to generate plain-language bill summaries, market event explanations, and power conversational QA bots. This serves as the primary extension point where **Groq** will later integrate.

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Single Responsibility** | Each module does exactly one job |
| **Dependency Direction** | Data flows top → bottom; no layer imports a higher layer |
| **No Hardcoded Values** | All paths and secrets come from `config/settings.py` |
| **Schema Contracts** | Each layer's output has a defined schema |
| **Fail-Fast Validation** | Invalid data is rejected early (Layer 2) |
| **Observability** | All layers log via `config/logging_config.py` |
| **Testability** | All modules are independently importable and testable |

## How Ingestion Works
The Legislative Data Ingestion Service runs a robust, step-by-step pipeline:
1. **Discovery (`discovery.py`)**: Locates available bills from portal RSS feeds or HTML tables based on configured criteria (e.g. year, latest).
2. **Fetch Detail Page**: Hits the specific detail URL for each discovered bill to scrape summary text and identify official PDF document links.
3. **Download PDF (`downloader.py`)**: Downloads the binary document safely, saves it to `data/bills/pdfs/`, computes an MD5 checksum, and extracts text content via `pdfplumber` or `PyPDF2`.
4. **Normalize (`normalizer.py`)**: Transforms the raw attributes to a canonical `Bill` schema model, converting date strings to dates and mapping house/status strings to typed enums.
5. **Validate (`validation/validator.py`)**: Screens the Normalized object for malformed URLs, out-of-range dates, missing fields, or empty texts, outputting a detailed `ValidationReport`.
6. **Duplicate Detection**: The service checks the repository to determine if the bill is a new insert, a modified record requiring an update, or a duplicate to skip.
7. **Persistence**: Saves verified bills to disk as JSON files under `data/bills/metadata/<bill_id>.json` via the `BillRepository`.
8. **Catalog Registry**: Registers results in `data/catalog/bill_catalog.json`.

## How to Add a New Legislative Source
To add another source (e.g. Ministry press releases or Lok Sabha committee reports):
1. **Define a New Parser method** in `ingestion/parliament/parser.py` (e.g. `parse_lok_sabha_committee`).
2. **Extend `discover_bills`** in `ingestion/parliament/discovery.py` to support the new `source` identifier.
3. **Register new catalog targets** in `data/catalog/bill_catalog.json` under `datasets`.
4. **Re-run the ingestion** from the CLI specifying the new source: `python main.py ingest --source <new_source>`.

## How Repositories Interact
Repositories (e.g., `BillRepository`) abstract file system interactions:
- They load configurations from `config.settings`.
- They read and write standardized schema objects (`Bill`, `Company`, `PriceRecord`), shielding ingestion and NLP pipeline modules from physical file formats and directory structures.
- Swapping to a relational database backend in Task 3 will only require changing the repository's internal save/load implementations without touching any ingestion logic.

## How Schemas are Used
- Every file in the pipelines must adhere to standard data schemas under `schemas/`.
- Schemas hold standard enums (e.g., `BillStatus`, `BillHouse`, `ImpactLabel`) to ensure consistent values throughout data ingestion, feature builders, models, and UI dashboards.
- Serialisation roundtrips are handled by `to_dict` and `from_dict` methods.
