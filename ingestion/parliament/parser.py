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
        Estimate the year of the bill delegating to the single authoritative
        year extraction logic.
        """
        from utils.text_utils import extract_bill_year

        return extract_bill_year(
            title=title,
            introduction_date=row_data.get("introduction_date"),
            metadata=row_data,
            url=url,
        )

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

                title = (
                    title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                )
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                description = (
                    desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
                )
                pub_date_str = (
                    pub_date_elem.text.strip()
                    if pub_date_elem is not None and pub_date_elem.text
                    else ""
                )

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
        Parse a bill's PRS detail page and extract all available structured metadata.

        Extracts (when available):
        - title, bill_number, ministry, house, status
        - introduction_date, last_updated
        - session, sponsor
        - official summary (first 2000 chars)
        - pdf_url (URL only — never downloads)
        - related_bills (slugs linked on the page)
        - related_acts (act names linked on the page)
        - language

        Parameters
        ----------
        html_content : str
            Detail page HTML content.
        bill_meta : dict
            Existing lightweight metadata dict from discovery (used as fallback).

        Returns
        -------
        dict
            Enriched metadata dict. Never raises — failures are logged and skipped.
        """
        enriched: dict[str, Any] = bill_meta.copy()
        if not html_content or not html_content.strip():
            logger.warning("Empty HTML content passed to parse_html_details.")
            return enriched

        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            logger.error("BeautifulSoup failed to parse detail HTML: %s", e)
            return enriched

        source_url = enriched.get("url", "")

        # ------------------------------------------------------------------
        # Helper: extract text from a labelled Drupal field or a <dt>/<dd> pair
        # ------------------------------------------------------------------
        def _field(css_class: str) -> str:
            """Return text content of the first element with the given CSS class."""
            el = soup.find(class_=re.compile(css_class, re.IGNORECASE))
            if el:
                return re.sub(r"\s+", " ", el.get_text(separator=" ")).strip()
            return ""

        def _label_value(label_text: str) -> str:
            """Find a <dt> or <th> matching label_text and return the paired <dd>/<td> text."""
            for tag in soup.find_all(["dt", "th", "td", "div", "span", "label"]):
                text = tag.get_text(strip=True)
                if label_text.lower() in text.lower() and len(text) < 60:
                    # Try next sibling first
                    sibling = tag.find_next_sibling(["dd", "td", "div", "span"])
                    if sibling:
                        val = sibling.get_text(strip=True)
                        if val and val.lower() != text.lower():
                            return re.sub(r"\s+", " ", val).strip()
            return ""

        # ------------------------------------------------------------------
        # Title — prefer <h1>, fall back to <h2>
        # ------------------------------------------------------------------
        h1 = soup.find("h1")
        if h1:
            title_text = re.sub(r"\s+", " ", h1.get_text()).strip()
            if title_text and len(title_text) > 5:
                enriched["title"] = title_text

        # ------------------------------------------------------------------
        # Ministry
        # ------------------------------------------------------------------
        ministry = (
            _field(r"field-name-field-ministry|field--name-field-ministry")
            or _field(r"ministry")
            or _label_value("Ministry")
            or _label_value("Department")
        )
        if ministry:
            # Strip any leading label text like "Ministry:" that may be included
            ministry = re.sub(
                r"^(Ministry|Department)\s*[:\-]\s*", "", ministry, flags=re.IGNORECASE
            ).strip()
            enriched["ministry"] = ministry

        # ------------------------------------------------------------------
        # Bill Number
        # ------------------------------------------------------------------
        bill_number = (
            _field(r"field-name-field-bill-number|field--name-field-bill-number")
            or _label_value("Bill No")
            or _label_value("Bill Number")
        )
        if bill_number:
            enriched["bill_number"] = bill_number

        # ------------------------------------------------------------------
        # House of Introduction
        # ------------------------------------------------------------------
        house_raw = (
            _field(r"field-name-field-house|field--name-field-house")
            or _label_value("House")
            or _label_value("Introduced in")
        )
        if house_raw:
            enriched["house"] = house_raw

        # ------------------------------------------------------------------
        # Status (detail page may have more accurate status than listing)
        # ------------------------------------------------------------------
        status_raw = (
            _field(r"field-name-field-bill-status|field--name-field-bill-status")
            or _field(r"status-tag|bill-status")
            or _label_value("Status")
        )
        if status_raw:
            enriched["status"] = status_raw

        # ------------------------------------------------------------------
        # Introduction Date
        # ------------------------------------------------------------------
        intro_date_raw = (
            _field(r"field-name-field-date-of-introduction|field--name-field-date-of-introduction")
            or _field(r"introduction-date|date-introduction")
            or _label_value("Date of Introduction")
            or _label_value("Introduction Date")
            or _label_value("Introduced")
        )
        if intro_date_raw and not enriched.get("introduction_date"):
            enriched["introduction_date"] = intro_date_raw

        # ------------------------------------------------------------------
        # Last Updated — from meta tags or date fields
        # ------------------------------------------------------------------
        last_updated_raw = ""
        meta_modified = soup.find(
            "meta", {"name": re.compile(r"modified|updated|last.modified", re.IGNORECASE)}
        )
        if meta_modified:
            last_updated_raw = meta_modified.get("content", "")
        if not last_updated_raw:
            last_updated_raw = (
                _field(r"field-name-field-last-updated|field--name-field-last-updated")
                or _label_value("Last Updated")
                or _label_value("Updated")
            )
        if last_updated_raw:
            enriched["last_updated"] = last_updated_raw

        # ------------------------------------------------------------------
        # Session
        # ------------------------------------------------------------------
        session = (
            _field(r"field-name-field-session|field--name-field-session")
            or _label_value("Session")
            or _label_value("Parliamentary Session")
        )
        if session:
            enriched["session"] = session

        # ------------------------------------------------------------------
        # Sponsor / Introduced By
        # ------------------------------------------------------------------
        sponsor = (
            _field(r"field-name-field-introduced-by|field--name-field-introduced-by")
            or _field(r"field-name-field-sponsor|field--name-field-sponsor")
            or _label_value("Introduced By")
            or _label_value("Sponsored By")
            or _label_value("Minister")
        )
        if sponsor:
            enriched["sponsor"] = sponsor

        # ------------------------------------------------------------------
        # Official Summary — from known Drupal body/summary containers
        # ------------------------------------------------------------------
        summary_div = (
            soup.find(class_=re.compile(r"field-name-body|field--name-body", re.IGNORECASE))
            or soup.find(
                class_=re.compile(r"bill-summary|summary-text|bill-description", re.IGNORECASE)
            )
            or soup.find("div", class_=re.compile(r"summary|description", re.IGNORECASE))
        )
        if summary_div and not enriched.get("summary"):
            text = re.sub(r"\s+", " ", summary_div.get_text(separator=" ")).strip()
            if len(text) > 20:
                enriched["summary"] = text[:2000]

        # ------------------------------------------------------------------
        # PDF URL — priority: "Bill Text / As Introduced" > any .pdf link
        # ------------------------------------------------------------------
        pdf_links = soup.find_all("a", href=re.compile(r"\.pdf", re.IGNORECASE))
        pdf_url: str = ""
        fallback_pdf_url: str = ""

        for link in pdf_links:
            href = str(link.get("href", "")).strip()
            if not href:
                continue
            link_text = link.get_text(strip=True).lower()

            if (
                "bill text" in link_text
                or "as introduced" in link_text
                or "original bill" in link_text
            ):
                pdf_url = href
                break  # highest priority; stop searching

            if not fallback_pdf_url:
                fallback_pdf_url = href  # record first available PDF as fallback

        if not pdf_url and fallback_pdf_url:
            pdf_url = fallback_pdf_url

        # Normalize and validate pdf_url
        final_pdf_url = None
        if pdf_url:
            import urllib.parse  # noqa: PLC0415

            # 1. Resolve relative and root-relative URLs using source_url as canonical base
            if source_url:
                resolved_url = urllib.parse.urljoin(source_url, pdf_url)
            else:
                resolved_url = pdf_url

            # 2. Normalize scheme to HTTPS and ensure absolute
            try:
                parsed = urllib.parse.urlparse(resolved_url)
                if parsed.scheme in ("http", "https"):
                    # Force HTTPS
                    normalized_url = urllib.parse.urlunparse(parsed._replace(scheme="https"))
                else:
                    if not parsed.scheme and parsed.netloc:
                        normalized_url = f"https://{resolved_url}"
                    else:
                        normalized_url = resolved_url

                # Validate final absolute canonical HTTPS URL
                parsed_final = urllib.parse.urlparse(normalized_url)
                if (
                    parsed_final.scheme == "https"
                    and parsed_final.netloc
                    and "." in parsed_final.netloc
                ):
                    final_pdf_url = normalized_url
                else:
                    logger.warning(
                        "PDF URL validation failed for: %s (scheme: %s, netloc: %s)",
                        normalized_url,
                        parsed_final.scheme,
                        parsed_final.netloc,
                    )
            except Exception as e:
                logger.warning("Error parsing resolved PDF URL %s: %s", resolved_url, e)

        if final_pdf_url:
            enriched["pdf_url"] = final_pdf_url
            logger.info("Found validated bill PDF URL: %s", final_pdf_url)
        else:
            enriched["pdf_url"] = None

        # ------------------------------------------------------------------
        # Related Bills — internal /billtrack/ links on the page
        # ------------------------------------------------------------------
        detail_area = (
            soup.find("main") or soup.find(id=re.compile(r"content|main", re.IGNORECASE)) or soup
        )
        related_slugs: list[str] = []
        current_slug = source_url.rstrip("/").rsplit("/", 1)[-1]
        for link in detail_area.find_all("a", href=re.compile(r"/billtrack/[^/]+$|/bill/[^/]+$")):
            href = str(link.get("href", ""))
            slug = href.rstrip("/").rsplit("/", 1)[-1]
            if slug and slug != current_slug and slug not in related_slugs:
                # Skip navigation, category or filter links
                if "category" not in href and "search" not in href:
                    related_slugs.append(slug)
        if related_slugs:
            enriched["related_bills"] = related_slugs[:10]  # cap at 10

        # ------------------------------------------------------------------
        # Related Acts — anchor text ending with "Act" in the content area
        # ------------------------------------------------------------------
        related_acts: list[str] = []
        act_pattern = re.compile(r"\bAct\b", re.IGNORECASE)
        for link in detail_area.find_all("a"):
            link_text = link.get_text(strip=True)
            href = str(link.get("href", ""))
            # Must look like an Act reference; exclude navigation links
            if act_pattern.search(link_text) and len(link_text) > 5 and len(link_text) < 120:
                if "/billtrack/" not in href and link_text not in related_acts:
                    related_acts.append(link_text)
        if related_acts:
            enriched["related_acts"] = related_acts[:15]  # cap at 15

        # ------------------------------------------------------------------
        # Language — default English unless detected otherwise
        # ------------------------------------------------------------------
        html_lang = soup.find("html")
        lang_attr = html_lang.get("lang", "en") if html_lang else "en"
        if lang_attr and not lang_attr.startswith("en"):
            enriched["language"] = lang_attr
        elif "language" not in enriched:
            enriched["language"] = "English"

        # ------------------------------------------------------------------
        # Year refinement from metadata now available
        # ------------------------------------------------------------------
        if not enriched.get("year"):
            from utils.text_utils import extract_bill_year

            enriched["year"] = extract_bill_year(
                title=enriched.get("title"),
                introduction_date=enriched.get("introduction_date"),
                metadata=enriched,
                url=enriched.get("url"),
            )

        logger.info(
            "Detail page parsed for bill '%s' | ministry=%r | pdf_url=%r | related_bills=%d",
            enriched.get("title", "?"),
            enriched.get("ministry", ""),
            enriched.get("pdf_url", ""),
            len(enriched.get("related_bills", [])),
        )
        return enriched
