# Data Sources

## Legislative Data

| Source | Type | URL | Notes |
|--------|------|-----|-------|
| PRS Legislative Research | Bills, summaries, analysis | https://prsindia.org | Most comprehensive; has structured bill database |
| Lok Sabha | Official bills | https://loksabha.nic.in | Primary source for Lok Sabha bills and debates |
| Rajya Sabha | Official bills | https://rajyasabha.nic.in | Primary source for Rajya Sabha bills |
| India Code | Act full-texts | https://indiacode.nic.in | Final enacted legislation text |
| e-Gazette of India | Gazette notifications | https://egazette.gov.in | Official government notifications |
| Ministry of Finance | Budget documents | https://finmin.nic.in | Finance Act, Finance Bills, Budget PDFs |

## Company & Exchange Data

| Source | Type | Format | Notes |
|--------|------|--------|-------|
| BSE India | Company master, price data | CSV download | Free bulk downloads available |
| NSE India | Equity symbol list, price data | CSV download | `nseindia.com/market-data/securities-available-for-trading` |
| MCA (Ministry of Corporate Affairs) | Company registration data | Web | Can supplement with CIN numbers |

## Market Price Data

| Source | Type | Access | Notes |
|--------|------|--------|-------|
| Yahoo Finance (`yfinance`) | OHLCV, adjusted prices | Free API | Good historical coverage; may have gaps |
| NSE historical data | OHLCV | Bulk CSV downloads | Official but manual |
| Quandl / Nasdaq Data Link | Clean historical data | Paid API | Best quality; requires subscription |
| Alpha Vantage | OHLCV, fundamentals | Freemium API | Limited calls on free tier |

## Macroeconomic / Index Data

| Source | Description |
|--------|-------------|
| Nifty 50 (^NSEI) | Benchmark index via `yfinance` |
| India VIX | Volatility index via NSE |
| Sector indices | Nifty Bank, Nifty IT, Nifty Pharma, etc. |
| RBI data | Interest rates, inflation, money supply |

## Supplementary / Enrichment Data

| Source | Description |
|--------|-------------|
| Bombay Stock Exchange sector classification | Official sector/industry taxonomy |
| NSE sector indices | Sector-level benchmarks for abnormal return computation |
| OpenAI / open-source LLMs | Bill summarisation and zero-shot classification |
| Legal databases | For precedent analysis (future) |

---

## Data Licences & Terms of Use

> **Important**: Always verify terms of service before scraping or
> programmatically accessing any source.

*  PRS Legislative Research: Content is publicly available for non-commercial
   research use.
*  BSE/NSE: Bulk historical data is freely downloadable; real-time data
   requires a licensed datafeed.
*  Yahoo Finance via `yfinance`: Subject to Yahoo's terms; not for commercial
   redistribution.
*  `yfinance` is not affiliated with Yahoo Finance and is a community
   library — use responsibly.

---

## Data Freshness Requirements

| Data type | Required freshness | Update cadence |
|-----------|-------------------|----------------|
| Bill metadata | Daily | Incremental daily scrape |
| Bill PDFs | On new bills only | Event-triggered |
| Company master | Monthly | Monthly refresh |
| Price history | Daily | Nightly batch |
| Model artefacts | Quarterly | After each retraining cycle |
