# TASK 8.25 — Report Generation

## Feature Overview

Route: `/reports`

Report Center for generating, viewing, downloading, and managing legislative intelligence reports.

## Supported Report Types

| Type | Sections | Formats |
|------|----------|---------|
| BILL | Bill Identity, Summary, Procedural Journey, Key Provisions, Economic Impact, Corporate Exposure, Market Intelligence, Anticipation, Sources | PDF |
| COMPANY | Company Profile, Legislative Exposure, Sector Analysis, Modelled Impact, Risk Classification, Anticipation | PDF, CSV |
| INDUSTRY | Industry Overview, Legislative Exposure, Affected Companies, Risk Landscape | PDF, CSV |
| PORTFOLIO | Portfolio Summary, Holdings Analysis, Legislative Exposure Map, Risk Overview, Sector Distribution | PDF, XLSX |
| RISK | Risk Matrix, High-Risk Bills, Affected Companies, Methodology | PDF, CSV |
| ANTICIPATION | Anticipation Overview, Signal Analysis, Bill-Company Matrix, Methodology | PDF |
| LEGISLATIVE_EXPOSURE | Coverage Overview, Central Exposure, State Exposure, Company Mapping, Provenance | PDF, CSV, XLSX |

## Safety Requirements

1. Reports generated from the SAME backend data used by the UI
2. No second calculation engine
3. Reports NEVER invent: numbers, companies, bill statuses, dates, predictions, source URLs
4. Every piece of data labelled: FACT / OBSERVED / DERIVED / INTERPRETATION / PREDICTION
5. No Buy/Sell/Hold recommendations
6. All reports include: title, generation timestamp, data freshness, provenance, disclaimers, methodology summary

## Report Metadata

Every report includes:
- Generation timestamp
- Data freshness timestamp
- Source attribution
- Epistemic label legend
- Statutory disclaimer
- Methodology notes

## Report Center

Users can:
- View recently generated reports
- Download reports (PDF/CSV/XLSX)
- Regenerate reports (re-fetches current data)
- Delete user-generated reports
