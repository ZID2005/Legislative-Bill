# TASK 8.25 — Live Legislative Discovery

## Architecture

The Live Legislative Discovery system creates a **complete separation** between:

- **FROZEN ANALYTICAL DATASET** — the immutable quantitative model (20 Central bills, 4,700 predictions, etc.)
- **LIVE LEGISLATIVE DISCOVERY DATA** — newly discovered bills from authoritative sources

## Key Invariant

NEW CURRENT/RECENT LEGISLATIVE RECORDS are **NEVER** inserted into the frozen prediction dataset unless they independently pass the existing analytical eligibility and modelling pipeline in a future, explicitly versioned task.

## New Routes

| Route | Description |
|-------|-------------|
| `/live-discovery` | Full live discovery feed with filters |
| `/latest-bills` | Latest bills ordered by discovery timestamp |
| `/upcoming-legislation` | Scheduled/expected future events |

## Status Labels

| Status | Meaning |
|--------|---------|
| NEW | Discovered in last 48h |
| RECENT | Discovered in last 7 days |
| ACTIVE | Currently in legislative process |
| AMENDED | Bill has been formally amended |
| PASSED | Enacted/passed |
| ASSENT_PENDING | Awaiting presidential/gubernatorial assent |
| NOTIFIED | Published in official gazette |
| ARCHIVED | Historical record |
| UPCOMING | Scheduled for future consideration |
| SOURCE_UNVERIFIED | Provenance not independently confirmed |

## Provenance Requirements

Every live record exposes:
- `source` — source name
- `sourceUrl` — official URL (never fabricated)
- `sourceOrganization` — originating authority
- `discoveredAt` — ingestion timestamp
- `lastUpdated` — last detected change
- `provenance` — AUTHORITATIVE / SECONDARY / UNVERIFIED

## Safety Rules

1. A newly discovered bill MUST NOT appear to have a market prediction
2. `isInAnalyticalModel` field is always `false` for live discovery records
3. No future dates are fabricated for upcoming legislation
4. Date confidence is always labelled: Scheduled / Reported / Expected by source / Date not available
