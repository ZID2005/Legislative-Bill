"""
ingestion/parliament/parser.py
==============================
Parsers for extracting bill metadata from HTML pages and RSS feeds.

Extracts titles, dates, ministries, houses of introduction, status, and PDF URLs
from PRS Legislative Research and Lok/Rajya Sabha structures.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from bs4 import BeautifulSoup

from config.logging_config import get_logger
from ingestion.parliament.exceptions import ParsingError

logger = get_logger(__name__)


class ParliamentParser:
    """
    Parser service for parsing legislative listings (HTML & RSS) and detail pages.
    """

    def _estimate_year(self, row_data: dict[str, Any], title: str, url: str) -> int | None:
        """
        Estimate the year of the bill using the following priority:
        1. Extract year from metadata (e.g. introduction_date or pub_date)
        2. Extract from URL (e.g. /2025/ or -2024)
        3. Extract from title (e.g. "Telecom Bill, 2023")
        4. Return None (NULL/Unknown) if not found.
        """
        # Priority 1: Extract year from metadata
        intro_date = row_data.get("introduction_date") or row_data.get("pub_date")
        if intro_date:
            match = re.search(r"\b(19|20)\d{2}\b", str(intro_date))
            if match:
                return int(match.group(0))

        # Priority 2: Extract from URL
        if url:
            match = re.search(r"\b(19|20)\d{2}\b", url)
            if match:
                return int(match.group(0))

        # Priority 3: Extract from title
        if title:
            match = re.search(r"\b(19|20)\d{2}\b", title)
            if match:
                return int(match.group(0))

        # Priority 4: NULL / Unknown
        return None

    def parse_rss(self, xml_content: str, source: str = "prs") -> list[dict[str, Any]]:
        """
        Parse RSS XML feed.

        Parameters
        ----------
        xml_content : str
            Raw XML content.
        source : str
            Identifier for the source.

        Returns
        -------
        list[dict]
            Parsed raw bill dictionaries.
        """
        bills = []
        try:
            root = ET.fromstring(xml_content.encode("utf-8"))
            channel = root.find("channel")
            if channel is None:
                raise ParsingError("Invalid RSS XML structure: <channel> tag not found.")

            items = channel.findall("item")
            for item in items:
                title_elem = item.find("title")
                link_elem = item.find("link")
                desc_elem = item.find("description")
                pub_date_elem = item.find("pubDate")

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                description = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
                pub_date_str = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else ""

                if not title:
                    logger.warning("Skipped RSS item with empty title.")
                    continue

                bill_meta = {
                    "title": title,
                    "url": link,
                    "source_url": link,
                    "description": description,
                    "pub_date": pub_date_str,
                    "source": source,
                }
                bill_meta["year"] = self._estimate_year(bill_meta, title, link)
                bills.append(bill_meta)

        except ET.ParseError as e:
            logger.error("Failed to parse RSS XML: %s", e)
            raise ParsingError(f"Failed to parse RSS XML: {e}") from e
        except Exception as e:
            logger.error("Error in parse_rss: %s", e)
            raise ParsingError(f"Error parsing RSS XML: {e}") from e

        return bills

    def parse_html_list(self, html_content: str, source: str = "prs") -> list[dict[str, Any]]:
        """
        Parse HTML bill list page. Supports PRS India bill table structures, Drupal Views, and general link lists.

        Parameters
        ----------
        html_content : str
            Raw HTML page content.
        source : str
            Identifier for the source.

        Returns
        -------
        list[dict]
            Parsed raw bill dictionaries.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        bills = []

        # Strategy 1: Find bill tables (existing logic)
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) <= 1:
                continue  # Empty or header-only table

            headers = [th.text.strip().lower() for th in rows[0].find_all(["th", "td"])]

            for row in rows[1:]:
                cols = row.find_all("td")
                if not cols:
                    continue

                row_data: dict[str, Any] = {"source": source}

                # Map columns by headers if present
                for idx, col in enumerate(cols):
                    if idx >= len(headers):
                        break
                    header = headers[idx]
                    col_text = col.text.strip()

                    if "title" in header or "bill" in header:
                        # Extract title and link
                        link = col.find("a")
                        row_data["title"] = col_text
                        if link and link.get("href"):
                            href = link["href"]
                            # Resolve relative URL if needed
                            if href.startswith("/"):
                                href = f"https://prsindia.org{href}"
                            row_data["url"] = href
                            row_data["source_url"] = href
                    elif "ministry" in header or "department" in header:
                        row_data["ministry"] = col_text
                    elif "date" in header or "introduction" in header:
                        row_data["introduction_date"] = col_text
                    elif "status" in header:
                        row_data["status"] = col_text
                    elif "house" in header:
                        row_data["house"] = col_text
                    elif "bill no" in header or "number" in header:
                        row_data["bill_number"] = col_text

                # Cleanup and validate minimum fields
                title = row_data.get("title", "").strip()
                if not title:
                    # Try fallback: first column as title if headers are missing/not matching
                    if len(cols) > 0:
                        first_col = cols[0]
                        title = first_col.text.strip()
                        row_data["title"] = title
                        link = first_col.find("a")
                        if link and link.get("href"):
                            href = link["href"]
                            if href.startswith("/"):
                                href = f"https://prsindia.org{href}"
                            row_data["url"] = href
                            row_data["source_url"] = href

                if not title:
                    continue

                row_data["year"] = self._estimate_year(row_data, title, row_data.get("url", ""))

                bills.append(row_data)

        # Strategy 2: Drupal Views rows (e.g. class="views-row")
        views_rows = soup.find_all(class_=re.compile(r"\bviews-row\b|\bviews-field-title-field\b"))
        for v_row in views_rows:
            # Find the title anchor link
            link = v_row.find("a", href=re.compile(r"/billtrack/|/bill/"))
            if not link:
                continue

            href = link.get("href", "")
            title = link.text.strip()
            if not title or not href:
                continue

            # Skip common links like category filter links or paginator/search
            if "category" in href or "search" in href or "billtrack" == title.lower():
                continue

            if href.startswith("/"):
                href = f"https://prsindia.org{href}"

            # Extract status from the row (either containing status class, or views-field-field-bill-status)
            status = "introduced"
            status_el = v_row.find(class_=re.compile(r"status|bill-status"))
            if status_el:
                status = status_el.text.strip()
            else:
                status_field = v_row.find(class_=re.compile(r"views-field-field-bill-status"))
                if status_field:
                    status = status_field.text.strip()

            row_data = {
                "source": source,
                "title": title,
                "url": href,
                "source_url": href,
                "status": status,
            }
            row_data["year"] = self._estimate_year(row_data, title, href)

            # Deduplicate against already parsed bills
            if not any(b["url"] == href for b in bills):
                bills.append(row_data)

        # Strategy 3: General link hunting fallback (if no bills found yet)
        if not bills:
            logger.info("No bills found via tables or views-rows. Applying general link fallback.")
            all_links = soup.find_all("a", href=re.compile(r"/billtrack/[^/]+$|/bill/[^/]+$"))
            for link in all_links:
                href = link.get("href", "")
                title = link.text.strip()
                if not title or not href or len(title) < 5:
                    continue
                # Skip pagination, home, and categories
                if "category" in href or "search" in href or "billtrack" in title.lower():
                    continue

                if href.startswith("/"):
                    href = f"https://prsindia.org{href}"

                row_data = {
                    "source": source,
                    "title": title,
                    "url": href,
                    "source_url": href,
                    "status": "introduced",
                }
                row_data["year"] = self._estimate_year(row_data, title, href)
                if not any(b["url"] == href for b in bills):
                    bills.append(row_data)

        logger.info("Successfully parsed %d bills from HTML.", len(bills))
        return bills

    def parse_html_details(self, html_content: str, bill_meta: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a bill's detail page to extract detailed fields like PDF links or summaries.

        Parameters
        ----------
        html_content : str
            Detail page HTML content.
        bill_meta : dict
            The existing metadata dict to be enriched.

        Returns
        -------
        dict
            Enriched metadata dict.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        enriched = bill_meta.copy()

        # Try to find a link to the PDF document
        # Common classes or text matching: e.g. "Bill Text", "Download", ".pdf"
        pdf_links = soup.find_all("a", href=re.compile(r"\.pdf$", re.IGNORECASE))
        for link in pdf_links:
            href = link["href"]
            link_text = link.text.strip().lower()
            if (
                "bill text" in link_text
                or "original bill" in link_text
                or "as introduced" in link_text
                or not enriched.get("document_url")
            ):
                if href.startswith("/"):
                    href = f"https://prsindia.org{href}"
                enriched["document_url"] = href
                logger.info("Found bill document PDF URL: %s", href)

        # Attempt to scrape detailed summary (e.g. paragraphs in a summary section)
        summary_div = soup.find("div", class_=re.compile(r"summary|description", re.IGNORECASE))
        if summary_div:
            summary_text = summary_div.text.strip()
            # Clean up double whitespace
            summary_text = re.sub(r"\s+", " ", summary_text)
            enriched["summary"] = summary_text[:1000]  # Limit size

        return enriched
