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
| NSE India | Equity symbol list | CSV download | [NSE Live Feed](https://archives.nseindia.com/content/equities/EQUITY_L_CO_ME.csv) - parsed dynamically via `CompanyLoader` |
| Local Seed Database | Enrichment metadata | In-memory JSON | Fallback seed list containing 50+ major companies across NIFTY 50, NIFTY Next 50, and key sector leaders to enrich symbols with sectors, industries, websites, and HQ locations. |
| MCA (Ministry of Corporate Affairs) | Company registration data | Web | Can supplement with CIN numbers |

## Market Price Data

| Source | Type | Access | Notes |
|--------|------|--------|-------|
| Yahoo Finance (`yfinance`) | OHLCV, adjusted prices | Free API | Integrated dynamically via `MarketLoader`. Resolves NSE equities to `<symbol>.NS` and BSE to `<symbol>.BO` |
| NSE historical data | OHLCV | Bulk CSV downloads | Official but manual |
| Quandl / Nasdaq Data Link | Clean historical data | Paid API | Best quality; requires subscription |
| Alpha Vantage | OHLCV, fundamentals | Freemium API | Limited calls on free tier |

## Macroeconomic / Index Data

Supported indices via Yahoo Finance:

| Index Name | Yahoo Ticker | Description |
|------------|--------------|-------------|
| **NIFTY 50** | `^NSEI` | Benchmark index |
| **NIFTY Bank** | `^NSEBANK` | Banking index |
| **NIFTY IT** | `^CNXIT` | Information Technology index |
| **NIFTY Pharma** | `^CNXPHARMA` | Pharmaceutical index |
| **NIFTY Auto** | `^CNXAUTO` | Automobile index |
| **NIFTY FMCG** | `^CNXFMCG` | Fast-Moving Consumer Goods index |
| **NIFTY Energy** | `^CNXENERGY` | Energy and power utilities index |
| **NIFTY Infrastructure** | `^CNXINFRA` | Infrastructure and construction index |


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

---

## Document Storage Layout

Official bill PDFs are organized by the introduction year of the bill to avoid single-directory congestion. The layout is managed inside the project `data/` directory:

```
data/
└── bills/
    └── documents/
        ├── 2024/
        │   ├── the-finance-bill-2024.pdf
        │   └── digital-personal-data-protection-bill-2024.pdf
        └── unknown/
            └── some-undated-bill.pdf
```

