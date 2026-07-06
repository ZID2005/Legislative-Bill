"""
ingestion/parliament/discovery.py
=================================
Service for discovering legislative bills from central portals.

Hits listings or RSS feeds from PRS India, Lok Sabha, or Rajya Sabha base URLs.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from ingestion.parliament.connector import ParliamentConnector
from ingestion.parliament.parser import ParliamentParser

logger = get_logger(__name__)


class ParliamentDiscovery:
    """
    Discovers available Central Government bills from configured data sources.
    """

    def __init__(self, prs_base_url: Optional[str] = None) -> None:
        """
        Initialize the discovery service.

        Parameters
        ----------
        prs_base_url : str | None
            Base URL for PRS India. If None, read from settings.
        """
        if prs_base_url is None:
            from config.settings import settings
            self.prs_base_url = settings.PRS_BASE_URL
        else:
            self.prs_base_url = prs_base_url

        self.parser = ParliamentParser()

    async def discover_bills(
        self,
        connector: ParliamentConnector,
        source: str = "prs",
        year: Optional[int] = None,
        latest_only: bool = False,
        page: Optional[int] = None,
        page_size: int = 50,
        bill_id_filter: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query listing pages or RSS feeds to discover bills.

        Parameters
        ----------
        connector : ParliamentConnector
            Resilient HTTP connector.
        source : str
            The target platform ("prs", "lok_sabha", "rajya_sabha").
        year : int | None
            Filter bills to a specific year.
        latest_only : bool
            True to only fetch recently active bills.
        page : int | None
            Page index (1-based) to return. If None, returns all.
        page_size : int
            Number of records per page.
        bill_id_filter : str | None
            Filter by specific bill ID slug.

        Returns
        -------
        list[dict]
            Parsed lightweight bill metadata objects.
        """
        import re
        from datetime import date
        from bs4 import BeautifulSoup
        from utils.text_utils import slugify

        discovered = []

        if source == "prs":
            # PRS has an RSS feed or billtrack page. Let's support both.
            if latest_only:
                url = f"{self.prs_base_url}/bills/rss"
                logger.info("Discovering latest bills via PRS RSS feed: %s", url)
                try:
                    xml_content = await connector.fetch(url)
                    discovered = self.parser.parse_rss(xml_content, source="prs")
                except Exception as e:
                    logger.warning("Failed to parse PRS RSS: %s. Falling back to HTML list.", e)
                    url = f"{self.prs_base_url}/billtrack"
                    logger.info("Discovering bills via PRS HTML billtrack list: %s", url)
                    html_content = await connector.fetch(url)
                    discovered = self.parser.parse_html_list(html_content, source="prs")
            else:
                url = f"{self.prs_base_url}/billtrack"
                logger.info("Discovering historical bills via PRS HTML billtrack list: %s", url)
                html_content = await connector.fetch(url)
                discovered = self.parser.parse_html_list(html_content, source="prs")

        elif source == "lok_sabha" or source == "rajya_sabha":
            logger.info("Lok/Rajya Sabha requested. Fetching from PRS as central aggregator.")
            url = f"{self.prs_base_url}/billtrack"
            html_content = await connector.fetch(url)
            discovered = self.parser.parse_html_list(html_content, source=source)

        # 1. Clean, format as lightweight metadata, and perform duplicate prevention
        seen_ids = set()
        unique_discovered = []
        for bill in discovered:
            title = bill.get("title", "").strip()
            if not title:
                continue

            bid = slugify(title)
            if bid in seen_ids:
                continue
            seen_ids.add(bid)

            status = bill.get("status", "introduced")
            if isinstance(status, str):
                status = status.strip().lower()

            bill_year = bill.get("year")
            # Filter by year early if provided
            if year is not None and bill_year != year:
                continue

            metadata_item = {
                "bill_id": bid,
                "title": title,
                "year": bill_year,
                "source_url": bill.get("source_url") or bill.get("url"),
                "url": bill.get("source_url") or bill.get("url"),
                "status": status,
            }
            unique_discovered.append(metadata_item)

        # 2. Filter by specific bill ID
        if bill_id_filter:
            matched = [b for b in unique_discovered if b["bill_id"] == bill_id_filter]
            if matched:
                return matched

            # Fallback: query detail page directly if not found in table listing
            direct_url = f"{self.prs_base_url}/bill/{bill_id_filter}"
            logger.info("Direct bill ID query not in list. Fetching detail page directly: %s", direct_url)
            try:
                html_content = await connector.fetch(direct_url)
                soup = BeautifulSoup(html_content, "html.parser")
                title_el = soup.find(["h1", "h2"])
                title = title_el.text.strip() if title_el else bill_id_filter.replace("-", " ").title()

                year_val = date.today().year
                year_match = re.search(r"\b(19|20)\d{2}\b", title)
                if year_match:
                    year_val = int(year_match.group(0))

                return [{
                    "bill_id": bill_id_filter,
                    "title": title,
                    "year": year_val,
                    "source_url": direct_url,
                    "url": direct_url,
                    "status": "introduced",
                }]
            except Exception as e:
                logger.warning("Direct bill page fetch failed for ID %s: %s", bill_id_filter, e)
                return []

        # 3. Apply pagination
        if page is not None and page > 0:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            unique_discovered = unique_discovered[start_idx:end_idx]

        logger.info("Discovered %d bills matching filters.", len(unique_discovered))
        return unique_discovered
