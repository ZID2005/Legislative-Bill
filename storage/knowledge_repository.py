"""
storage/knowledge_repository.py
================================
Repository for legislative bill knowledge records.

This module is the single access point for reading and writing knowledge records.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.knowledge_record import KnowledgeRecord
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


class KnowledgeRepository:
    """
    Repository for storing and querying KnowledgeRecord metadata.
    """

    def __init__(self) -> None:
        from config.settings import settings

        self._knowledge_dir = settings.BILLS_DIR / "knowledge"
        ensure_dir(self._knowledge_dir)
        logger.debug("KnowledgeRepository initialised | knowledge_dir=%s", self._knowledge_dir)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: KnowledgeRecord) -> None:
        """
        Persist a knowledge record as a JSON file.

        Parameters
        ----------
        record : KnowledgeRecord
            A validated schemas.knowledge_record.KnowledgeRecord object.
        """
        dest_path = self._knowledge_dir / f"{record.bill_id}.json"
        save_json(record.to_dict(), dest_path)
        logger.info("Saved knowledge record to repository: %s", record.bill_id)

    def save_many(self, records: list[KnowledgeRecord]) -> None:
        """
        Persist multiple knowledge records.

        Parameters
        ----------
        records : list[KnowledgeRecord]
            List of KnowledgeRecord objects to persist.
        """
        for record in records:
            self.save(record)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str) -> Optional[KnowledgeRecord]:
        """
        Retrieve a single knowledge record by its unique ID.

        Returns None if not found (does not raise).
        """
        src_path = self._knowledge_dir / f"{bill_id}.json"
        if not file_exists(src_path):
            logger.debug("Knowledge record file not found: %s", src_path)
            return None
        try:
            data = load_json(src_path)
            return KnowledgeRecord.from_dict(data)
        except Exception as e:
            logger.error("Failed to load knowledge record '%s': %s", bill_id, e)
            return None

    def get_all(self) -> list[KnowledgeRecord]:
        """Return all stored knowledge records."""
        records = []
        try:
            files = list_files(self._knowledge_dir, "*.json")
            for f in files:
                bill_id = f.stem
                record = self.get(bill_id)
                if record:
                    records.append(record)
        except Exception as e:
            logger.error("Failed to list knowledge records: %s", e)
        return records

    def get_by_ministry(self, ministry: str) -> list[KnowledgeRecord]:
        """Return knowledge records filtered by ministry (case-insensitive)."""
        m_lower = ministry.strip().lower()
        return [r for r in self.get_all() if r.ministry.strip().lower() == m_lower]

    def get_by_sector(self, sector: str) -> list[KnowledgeRecord]:
        """Return knowledge records where sector is primary or in secondary sectors (case-insensitive)."""
        s_lower = sector.strip().lower()
        return [
            r
            for r in self.get_all()
            if r.primary_sector.strip().lower() == s_lower
            or any(s.strip().lower() == s_lower for s in r.secondary_sectors)
        ]

    def get_by_policy_domain(self, policy_domain: str) -> list[KnowledgeRecord]:
        """Return knowledge records filtered by policy domain (case-insensitive)."""
        pd_lower = policy_domain.strip().lower()
        return [r for r in self.get_all() if r.policy_domain.strip().lower() == pd_lower]

    def get_by_tag(self, tag: str) -> list[KnowledgeRecord]:
        """Return knowledge records matching a searchable tag (e.g. 'status:passed_both')."""
        t_lower = tag.strip().lower()
        return [r for r in self.get_all() if any(t.lower() == t_lower for t in r.searchable_tags)]

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(self, bill_id: str) -> bool:
        """Return True if a knowledge record with the given ID is already stored."""
        src_path = self._knowledge_dir / f"{bill_id}.json"
        return file_exists(src_path)

    def delete(self, bill_id: str) -> None:
        """Remove a knowledge record."""
        src_path = self._knowledge_dir / f"{bill_id}.json"
        if file_exists(src_path):
            os.remove(src_path)
            logger.info("Deleted knowledge record: %s", bill_id)

    def count(self) -> int:
        """Return the total number of stored knowledge records."""
        try:
            files = list_files(self._knowledge_dir, "*.json")
            return len(files)
        except Exception as e:
            logger.error("Failed to count knowledge records: %s", e)
            return 0

    def __repr__(self) -> str:
        return f"<KnowledgeRepository knowledge_dir={self._knowledge_dir!r}>"
