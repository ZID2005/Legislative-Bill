"""
ingestion/market package
========================
Historical market price and index data ingestion.

Sources
-------
*  Yahoo Finance via ``yfinance`` (OHLCV, adjusted prices)
*  NSE bulk data downloads       (official historical data)
*  India VIX                     (NSE volatility index)
*  Quandl / Nasdaq Data Link     (future paid tier)

Modules
-------
market_loader : Fetches, caches, and stores OHLCV price data as Parquet files.

Implemented in Task 2.
"""
