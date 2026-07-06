"""
ingestion package
=================
Data acquisition layer for the Legislative Intelligence project.

This package handles all data ingestion from external sources.  It is
deliberately split into domain-specific sub-packages because the ingestion
strategies differ significantly across source types.

Sub-packages
------------
parliament : Legislative documents from Lok Sabha, Rajya Sabha, PRS, etc.
companies  : Company master data from BSE and NSE.
market     : Historical OHLCV price data from exchanges and market APIs.
external   : Supplementary data — news, Google Trends, GDELT, macro indicators.

Design Principle
----------------
Each sub-package is independently runnable and produces well-defined output
artefacts (JSON/CSV/Parquet) stored under ``data/``.  No sub-package imports
from another sub-package — they communicate only via the data layer.

Implementation Timeline
-----------------------
* parliament/  — Task 1
* companies/   — Task 2
* market/      — Task 2
* external/    — Task 3+
"""
