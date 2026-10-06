# TASK 8.25 — Portfolio Intelligence

## Feature Overview

Route: `/portfolio`

Personal portfolio creation, upload, and legislative exposure analysis.

## Data Model

### User-Provided Data (clearly labelled)
- Holdings (company, ticker, ISIN)
- Quantity
- Average purchase price
- Current value
- Portfolio name

### Platform-Derived Data (clearly labelled)
- Legislative exposure count
- Relevant bills (with MODELLED/INTELLIGENCE labels)
- Risk signals (LOW/MODERATE/HIGH/ELEVATED)
- Anticipation signals
- Sector distribution analysis

## Import Formats

- Manual addition (company search)
- CSV upload (company, ticker, isin, quantity, avg_purchase_price)
- XLSX upload

## Safety Rules

1. NO Buy/Sell/Hold recommendations
2. Decision-support language only:
   - "Exposure detected"
   - "Relevant legislative event"
   - "Modelled market impact"
   - "Additional monitoring may be useful"
3. No individualized financial advice
4. USER-PROVIDED vs PLATFORM-DERIVED data clearly distinguished

## Portfolio → Bill Connection

Company → Related Bills → Legislative Status → Sector → Modelled Market Impact → Risk → Anticipation → Source

## Watchlist Integration

Portfolio companies can be added to existing watchlists. No duplicate alert system created.

## StatePredictionFirewall

Portfolio analysis respects the StatePredictionFirewall:
- State bills show INTELLIGENCE ONLY label
- No State stock predictions
- No State anticipation scores
