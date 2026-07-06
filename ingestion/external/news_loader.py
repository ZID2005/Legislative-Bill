"""
ingestion/external/news_loader.py
==================================
Financial news ingestion — **Task 3+ placeholder**.

Future Responsibility
---------------------
Fetch, store, and update financial news headlines relevant to Indian
legislative events from multiple sources:

*  NewsAPI (https://newsapi.org) — structured headline + sentiment
*  Google News RSS            — broad coverage
*  Economic Times RSS         — Indian business focus
*  Business Standard RSS      — Indian policy & market focus

Output schema (per article)::

    {
        "article_id": "et-20240201-0042",
        "source": "Economic Times",
        "title": "Finance Bill 2024 to impact insurance sector",
        "published_at": "2024-02-01T08:30:00Z",
        "url": "https://...",
        "snippet": "...",
        "sentiment_score": 0.32,
        "related_bill_ids": ["finance-bill-2024"],
        "related_sectors": ["Insurance", "Banking"]
    }

Dependencies (to be added)
---------------------------
*  newsapi-python
*  feedparser (RSS)
*  transformers / vaderSentiment (sentiment scoring)
"""

# TODO (Task 3+): Implement NewsLoader.


class NewsLoader:
    """Placeholder for financial news ingestion. Implemented in Task 3+."""

    def __init__(self) -> None:
        raise NotImplementedError("NewsLoader is not yet implemented.")
