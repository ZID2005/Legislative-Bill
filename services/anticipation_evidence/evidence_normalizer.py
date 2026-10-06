"""
services/anticipation_evidence/evidence_normalizer.py
=====================================================
Deterministic normalization and hashing utilities for public-information evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from config.logging_config import get_logger

logger = get_logger(__name__)

# Query parameters commonly used for tracking that should be removed from canonical URLs
_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "msclkid",
    "ref",
    "source",
    "sub_source",
    "sp_source",
    "session_id",
}


class EvidenceNormalizer:
    """
    Utility class for standardizing URLs, titles, and dates to ensure
    reproducible deduplication and hashing.
    """

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        """
        Normalize URL to canonical representation:
        - Strip whitespace
        - Lowercase scheme and netloc
        - Remove default ports (:80, :443)
        - Strip common tracking query params
        - Remove trailing slashes on path
        """
        if not raw_url:
            return ""

        url = raw_url.strip()
        parsed = urlparse(url)

        scheme = (parsed.scheme or "https").lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]

        # Strip tracking query params
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = [
            (k, v) for k, v in query_pairs if k.lower() not in _TRACKING_PARAMS
        ]
        clean_query = urlencode(sorted(filtered_query))

        path = parsed.path
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        canonical = urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
        return canonical

    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Normalize article title or headline for text similarity and deduplication:
        - Lowercase
        - Remove non-alphanumeric punctuation
        - Collapse multiple spaces into single space
        """
        if not title:
            return ""
        # Lowercase
        text = title.lower().strip()
        # Replace non-alphanumeric (except single spaces) with space
        text = re.sub(r"[^\w\s]", " ", text)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def parse_timestamp(ts_str: str) -> Optional[datetime]:
        """
        Parse flexible date/time strings into a timezone-aware UTC datetime.
        Returns None if parsing fails.
        """
        if not ts_str:
            return None

        clean_str = ts_str.strip()
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(clean_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt
            except ValueError:
                continue

        # Try fromisoformat as fallback
        try:
            dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            pass

        return None

    @staticmethod
    def format_iso_utc(dt: datetime) -> str:
        """Format datetime as UTC ISO-8601 string ending in 'Z'."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    @classmethod
    def compute_evidence_hash(
        cls,
        bill_id: str,
        source_url: str,
        headline: str,
        publication_timestamp: str,
    ) -> str:
        """
        Compute deterministic SHA-256 hash for evidence item.
        """
        can_url = cls.normalize_url(source_url)
        norm_title = cls.normalize_title(headline)
        payload = f"{bill_id.strip()}|{can_url}|{norm_title}|{publication_timestamp.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
