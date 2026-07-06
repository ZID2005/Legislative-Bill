"""
ingestion/external package
==========================
Supplementary and enrichment data ingestion from third-party sources.

Planned sources (each will become its own module):

news_loader.py
    Financial news headlines and sentiment from:
    *  NewsAPI (https://newsapi.org)
    *  Google News RSS feeds
    *  The Hindu, Economic Times, Business Standard RSS

trends_loader.py
    Google Trends data for bill-related keyword search volumes.
    Useful as a proxy for public awareness and media attention.
    Library: ``pytrends``

gdelt_loader.py
    GDELT Project (https://gdeltproject.org) for:
    *  Global media event data linked to Indian legislation
    *  Tone and coverage intensity scores

macro_loader.py
    Reserve Bank of India (RBI) macroeconomic indicators:
    *  Repo rate, reverse repo rate
    *  CPI / WPI inflation
    *  Money supply (M1, M2, M3)

All external sources are implemented in Task 3+.
"""
