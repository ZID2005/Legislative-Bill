"""
services/anticipation_evidence/evidence_repository.py
=====================================================
Dedicated repository for persisting and querying PublicInformationEvidence records
and AnticipationEvidenceContext artifacts.

Phase 24: Caching layer for external evidence retrieval.
Tenant isolation and provenance support.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.anticipation_evidence import (
    AnticipationEvidenceContext,
    PublicInformationEvidence,
    SearchTrendEvidence,
)
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


def _sanitize(identifier: str) -> str:
    return identifier.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_")


class AnticipationEvidenceRepository:
    """
    Persistence and caching layer for public-information evidence and combined contexts.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        read_only: bool = False,
    ) -> None:
        self._base_dir = base_dir or settings.ANTICIPATION_EVIDENCE_DIR
        self._evidence_dir = self._base_dir / "evidence"
        self._contexts_dir = self._base_dir / "contexts"
        self._trends_dir = self._base_dir / "trends"
        self._cache_dir = self._base_dir / "cache"
        self._read_only = read_only
        self._lock = threading.Lock()

        for d in [self._base_dir, self._evidence_dir, self._contexts_dir, self._trends_dir, self._cache_dir]:
            ensure_dir(d)

        # In-memory query cache for high-throughput responses
        self._memory_cache: dict[str, dict[str, Any]] = {}

    @property
    def is_read_only(self) -> bool:
        return self._read_only

    # ------------------------------------------------------------------
    # Evidence Items CRUD
    # ------------------------------------------------------------------

    def save_evidence(self, evidence: PublicInformationEvidence) -> None:
        """Persist a single PublicInformationEvidence record."""
        with self._lock:
            sanitized_id = _sanitize(evidence.evidence_id)
            dest = self._evidence_dir / f"{sanitized_id}.json"
            save_json(evidence.to_dict(), dest)
            logger.debug("Saved public information evidence %s", evidence.evidence_id)

    def save_evidence_batch(self, items: list[PublicInformationEvidence]) -> None:
        """Persist multiple PublicInformationEvidence records."""
        for item in items:
            self.save_evidence(item)

    def get_evidence_by_id(self, evidence_id: str) -> Optional[PublicInformationEvidence]:
        """Retrieve a PublicInformationEvidence record by ID."""
        sanitized_id = _sanitize(evidence_id)
        path = self._evidence_dir / f"{sanitized_id}.json"
        if not file_exists(path):
            return None
        try:
            data = load_json(path)
            return PublicInformationEvidence.from_dict(data)
        except Exception as e:
            logger.error("Failed to load evidence record %s: %s", evidence_id, e)
            return None

    def get_evidence_by_bill(self, bill_id: str) -> list[PublicInformationEvidence]:
        """Retrieve all evidence associated with a bill."""
        results: list[PublicInformationEvidence] = []
        try:
            files = list_files(self._evidence_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    if data.get("bill_id") == bill_id:
                        results.append(PublicInformationEvidence.from_dict(data))
                except Exception:
                    continue
        except Exception as exc:
            logger.error("Error querying evidence for bill %s: %s", bill_id, exc)
        return results

    def get_evidence_by_company(self, company_isin: str) -> list[PublicInformationEvidence]:
        """Retrieve all evidence records matching a company ISIN or ticker."""
        results: list[PublicInformationEvidence] = []
        isin_upper = company_isin.upper()
        try:
            files = list_files(self._evidence_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    matches = [m.upper() for m in data.get("entity_matches", [])]
                    if isin_upper in matches:
                        results.append(PublicInformationEvidence.from_dict(data))
                except Exception:
                    continue
        except Exception as exc:
            logger.error("Error querying evidence for company %s: %s", company_isin, exc)
        return results

    def get_all_evidence(self) -> list[PublicInformationEvidence]:
        """Retrieve all stored evidence items."""
        results: list[PublicInformationEvidence] = []
        try:
            files = list_files(self._evidence_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    results.append(PublicInformationEvidence.from_dict(data))
                except Exception:
                    continue
        except Exception as exc:
            logger.error("Error retrieving all evidence: %s", exc)
        return results

    # ------------------------------------------------------------------
    # Contexts CRUD
    # ------------------------------------------------------------------

    def save_context(self, context: AnticipationEvidenceContext) -> None:
        """Persist an AnticipationEvidenceContext record."""
        with self._lock:
            key = f"{_sanitize(context.bill_id)}_{_sanitize(context.company_isin or 'summary')}"
            dest = self._contexts_dir / f"{key}.json"
            save_json(context.to_dict(), dest)
            logger.debug("Saved anticipation evidence context for %s", key)

    def get_context(self, bill_id: str, company_isin: Optional[str] = None) -> Optional[AnticipationEvidenceContext]:
        """Retrieve an AnticipationEvidenceContext record."""
        key = f"{_sanitize(bill_id)}_{_sanitize(company_isin or 'summary')}"
        path = self._contexts_dir / f"{key}.json"
        if not file_exists(path):
            return None
        try:
            data = load_json(path)
            return AnticipationEvidenceContext.from_dict(data)
        except Exception as e:
            logger.error("Failed to load context for %s: %s", key, e)
            return None

    def get_all_contexts(self) -> list[AnticipationEvidenceContext]:
        """Retrieve all stored AnticipationEvidenceContext records."""
        results: list[AnticipationEvidenceContext] = []
        try:
            files = list_files(self._contexts_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    results.append(AnticipationEvidenceContext.from_dict(data))
                except Exception:
                    continue
        except Exception as exc:
            logger.error("Error retrieving all contexts: %s", exc)
        return results

    # ------------------------------------------------------------------
    # Search Trends CRUD
    # ------------------------------------------------------------------

    def save_trend(self, bill_id: str, trend: SearchTrendEvidence) -> None:
        """Persist a SearchTrendEvidence record."""
        with self._lock:
            sanitized_bill = _sanitize(bill_id)
            ts_str = _sanitize(trend.timestamp[:10])
            dest = self._trends_dir / f"{sanitized_bill}_{ts_str}.json"
            save_json(trend.to_dict(), dest)

    def get_trends_by_bill(self, bill_id: str) -> list[SearchTrendEvidence]:
        """Retrieve all search trend signals for a bill."""
        sanitized_bill = _sanitize(bill_id)
        results: list[SearchTrendEvidence] = []
        try:
            files = list_files(self._trends_dir, f"{sanitized_bill}_*.json")
            for f in files:
                try:
                    data = load_json(f)
                    results.append(SearchTrendEvidence.from_dict(data))
                except Exception:
                    continue
        except Exception as exc:
            logger.error("Error querying trends for bill %s: %s", bill_id, exc)
        return results

    # ------------------------------------------------------------------
    # Caching Layer (Phase 24)
    # ------------------------------------------------------------------

    def get_cached_response(
        self,
        source: str,
        query: str,
        time_window: str,
        jurisdiction: str,
    ) -> Optional[list[dict[str, Any]]]:
        """
        Check cache for external evidence query.
        Cache key composed of: source, query, time window, jurisdiction.
        """
        cache_key = f"{source.strip().lower()}:{query.strip().lower()}:{time_window.strip().lower()}:{jurisdiction.strip().lower()}"
        with self._lock:
            # Check in-memory first
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                return entry.get("data")

            # Check disk cache
            cache_file = self._cache_dir / f"{_sanitize(cache_key)}.json"
            if file_exists(cache_file):
                try:
                    data = load_json(cache_file)
                    self._memory_cache[cache_key] = data
                    return data.get("data")
                except Exception:
                    pass
        return None

    def set_cached_response(
        self,
        source: str,
        query: str,
        time_window: str,
        jurisdiction: str,
        data: list[dict[str, Any]],
    ) -> None:
        """Store external evidence query result in cache."""
        cache_key = f"{source.strip().lower()}:{query.strip().lower()}:{time_window.strip().lower()}:{jurisdiction.strip().lower()}"
        entry = {
            "cache_key": cache_key,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        with self._lock:
            self._memory_cache[cache_key] = entry
            cache_file = self._cache_dir / f"{_sanitize(cache_key)}.json"
            try:
                save_json(entry, cache_file)
            except Exception as e:
                logger.warning("Failed to write cache file: %s", e)
