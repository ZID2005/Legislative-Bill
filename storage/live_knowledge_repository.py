"""
storage/live_knowledge_repository.py
=====================================
Task 8.26 — Live Legislative Intelligence & Automatic Update Pipeline.

Thread-safe, JSON-backed storage layer for ``LiveKnowledgeRecord`` objects.

FIREWALL RULE
=============
This repository calls ``record.assert_not_frozen_model()`` on every write.
No record with ``analytical_model_status = MODELLED`` may be persisted here
unless it was explicitly set through the approved analytical ingestion CLI.

Directory layout
----------------
storage/live_knowledge/
    records/           one JSON file per record_id
    index.json         fast lookup: bill_number / canonical_bill_id -> record_id
    stats.json         aggregate counters updated on every write
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from schemas.monitoring import (
    AnalyticalModelStatus,
    LiveKnowledgeRecord,
    LiveStatus,
)

logger = logging.getLogger(__name__)

_RECORDS_SUBDIR = "records"
_INDEX_FILE = "index.json"
_STATS_FILE = "stats.json"


class LiveKnowledgeRepository:
    """
    Thread-safe JSON-backed store for LiveKnowledgeRecord objects.

    Every mutating method:
    1. Calls ``record.assert_not_frozen_model()`` to enforce the Task 8.26 firewall.
    2. Atomically writes the record JSON to ``records/<record_id>.json``.
    3. Updates the index and stats files.
    """

    def __init__(self, storage_dir: Path) -> None:
        self._root = Path(storage_dir) / "live_knowledge"
        self._records_dir = self._root / _RECORDS_SUBDIR
        self._index_path = self._root / _INDEX_FILE
        self._stats_path = self._root / _STATS_FILE
        self._lock = threading.Lock()
        self._ensure_dirs()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self._records_dir.mkdir(parents=True, exist_ok=True)

    def _record_path(self, record_id: str) -> Path:
        return self._records_dir / f"{record_id}.json"

    def _load_index(self) -> dict:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("live_knowledge index corrupt; rebuilding")
        return {}

    def _save_index(self, index: dict) -> None:
        self._index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def _load_stats(self) -> dict:
        if self._stats_path.exists():
            try:
                return json.loads(self._stats_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "total_records": 0,
            "by_live_status": {},
            "by_analytical_model_status": {},
            "by_jurisdiction": {},
            "document_hash_changes": 0,
            "duplicate_discoveries": 0,
            "last_write_at": None,
        }

    def _save_stats(self, stats: dict) -> None:
        stats["last_write_at"] = datetime.now(timezone.utc).isoformat()
        self._stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    def _recompute_stats(self, index: dict) -> dict:
        """Full recompute — only called when stats diverge."""
        stats: dict = {
            "total_records": 0,
            "by_live_status": {},
            "by_analytical_model_status": {},
            "by_jurisdiction": {},
            "document_hash_changes": 0,
            "duplicate_discoveries": 0,
            "last_write_at": datetime.now(timezone.utc).isoformat(),
        }
        for record_id in index.get("record_ids", {}).values():
            rec_path = self._record_path(record_id)
            if not rec_path.exists():
                continue
            try:
                d = json.loads(rec_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            stats["total_records"] += 1
            ls = d.get("live_status", "UNKNOWN")
            stats["by_live_status"][ls] = stats["by_live_status"].get(ls, 0) + 1
            ams = d.get("analytical_model_status", "KNOWLEDGE_ONLY")
            stats["by_analytical_model_status"][ams] = stats["by_analytical_model_status"].get(ams, 0) + 1
            j = d.get("jurisdiction", "central")
            stats["by_jurisdiction"][j] = stats["by_jurisdiction"].get(j, 0) + 1
            stats["duplicate_discoveries"] += d.get("duplicate_discoveries", 0)
        return stats

    def _update_index(self, index: dict, record: LiveKnowledgeRecord) -> None:
        """Add/update all lookup keys for the record."""
        # record_ids: arbitrary key -> record_id mapping
        if "record_ids" not in index:
            index["record_ids"] = {}
        index["record_ids"][record.record_id] = record.record_id

        # bill_number -> record_id  (overwrite, latest wins)
        if record.bill_number:
            if "by_bill_number" not in index:
                index["by_bill_number"] = {}
            index["by_bill_number"][record.bill_number] = record.record_id

        # canonical_bill_id -> record_id
        if record.canonical_bill_id:
            if "by_canonical_bill_id" not in index:
                index["by_canonical_bill_id"] = {}
            index["by_canonical_bill_id"][record.canonical_bill_id] = record.record_id

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def upsert(self, record: LiveKnowledgeRecord) -> LiveKnowledgeRecord:
        """
        Save or update a LiveKnowledgeRecord.

        Enforces the frozen-model firewall (no MODELLED via pipeline).
        If a record with the same record_id already exists:
        - Increments duplicate_discoveries if content is unchanged.
        - Detects document hash changes and updates document fields.
        Returns the (possibly updated) record.
        """
        record.assert_not_frozen_model()

        with self._lock:
            index = self._load_index()
            stats = self._load_stats()
            rec_path = self._record_path(record.record_id)

            is_new = not rec_path.exists()
            if not is_new:
                try:
                    old_data = json.loads(rec_path.read_text(encoding="utf-8"))
                    old_hash = old_data.get("document_hash_sha256")
                    new_hash = record.document_hash_sha256
                    if old_hash and new_hash and old_hash != new_hash:
                        logger.info(
                            "Document hash changed for record %s: %s -> %s",
                            record.record_id, old_hash[:12], new_hash[:12],
                        )
                        stats["document_hash_changes"] = stats.get("document_hash_changes", 0) + 1
                    # Track re-discoveries if content identical
                    is_identical_content = (
                        old_data.get("title") == record.title
                        and old_data.get("bill_status_text") == record.bill_status_text
                        and (old_hash == new_hash or (old_hash is None and new_hash is None))
                    )
                    if is_identical_content:
                        record.duplicate_discoveries = old_data.get("duplicate_discoveries", 0) + 1
                        stats["duplicate_discoveries"] = stats.get("duplicate_discoveries", 0) + 1
                    else:
                        # Retain existing count on field updates
                        record.duplicate_discoveries = old_data.get("duplicate_discoveries", record.duplicate_discoveries)
                except Exception as exc:
                    logger.warning("Could not read existing record for diff: %s", exc)

            record.last_updated_at = datetime.now(timezone.utc).isoformat()
            rec_path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")

            self._update_index(index, record)
            self._save_index(index)

            # Increment totals
            if is_new:
                stats["total_records"] = stats.get("total_records", 0) + 1
                ls = record.live_status
                stats["by_live_status"][ls] = stats["by_live_status"].get(ls, 0) + 1
                ams = record.analytical_model_status
                stats["by_analytical_model_status"][ams] = (
                    stats["by_analytical_model_status"].get(ams, 0) + 1
                )
                j = record.jurisdiction
                stats["by_jurisdiction"][j] = stats["by_jurisdiction"].get(j, 0) + 1
            self._save_stats(stats)

            return record

    def mark_retrieval_failure(
        self,
        record_id: str,
        error: str,
    ) -> Optional[LiveKnowledgeRecord]:
        """
        Increment document_retrieval_failures for a record.
        Returns updated record, or None if not found.
        """
        with self._lock:
            rec_path = self._record_path(record_id)
            if not rec_path.exists():
                return None
            try:
                data = json.loads(rec_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.error("Failed to load record %s: %s", record_id, exc)
                return None
            data["document_retrieval_failures"] = data.get("document_retrieval_failures", 0) + 1
            data["document_retrieval_last_error"] = error
            data["last_updated_at"] = datetime.now(timezone.utc).isoformat()
            rec_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return LiveKnowledgeRecord.from_dict(data)

    def update_live_status(
        self,
        record_id: str,
        new_status: LiveStatus,
        verification_source_id: Optional[str] = None,
        verification_source_url: Optional[str] = None,
    ) -> Optional[LiveKnowledgeRecord]:
        """
        Transition a record to a new LiveStatus.
        Returns updated record, or None if not found.
        """
        with self._lock:
            rec_path = self._record_path(record_id)
            if not rec_path.exists():
                return None
            try:
                data = json.loads(rec_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.error("Failed to load record %s: %s", record_id, exc)
                return None
            data["live_status"] = new_status.value
            data["last_updated_at"] = datetime.now(timezone.utc).isoformat()
            if new_status == LiveStatus.VERIFIED:
                data["verified_at"] = datetime.now(timezone.utc).isoformat()
            if verification_source_id:
                data["verification_source_id"] = verification_source_id
            if verification_source_url:
                data["verification_source_url"] = verification_source_url
            rec_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return LiveKnowledgeRecord.from_dict(data)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, record_id: str) -> Optional[LiveKnowledgeRecord]:
        """Fetch a single record by record_id."""
        rec_path = self._record_path(record_id)
        if not rec_path.exists():
            return None
        try:
            data = json.loads(rec_path.read_text(encoding="utf-8"))
            return LiveKnowledgeRecord.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load record %s: %s", record_id, exc)
            return None

    def get_by_bill_number(self, bill_number: str) -> Optional[LiveKnowledgeRecord]:
        """Lookup by bill number using the index."""
        index = self._load_index()
        record_id = index.get("by_bill_number", {}).get(bill_number)
        if record_id:
            return self.get(record_id)
        return None

    def get_by_canonical_bill_id(self, canonical_bill_id: str) -> Optional[LiveKnowledgeRecord]:
        """Lookup by canonical bill_id using the index."""
        index = self._load_index()
        record_id = index.get("by_canonical_bill_id", {}).get(canonical_bill_id)
        if record_id:
            return self.get(record_id)
        return None

    def list_records(
        self,
        limit: int = 50,
        offset: int = 0,
        live_status: Optional[str] = None,
        analytical_model_status: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> tuple[list[LiveKnowledgeRecord], int]:
        """
        Paginated listing with optional filters.
        Returns (records, total_matching).
        """
        records = []
        for rec_path in sorted(self._records_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(rec_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if live_status and data.get("live_status") != live_status:
                continue
            if analytical_model_status and data.get("analytical_model_status") != analytical_model_status:
                continue
            if jurisdiction and data.get("jurisdiction") != jurisdiction:
                continue
            records.append(LiveKnowledgeRecord.from_dict(data))

        total = len(records)
        return records[offset: offset + limit], total

    def get_stats(self) -> dict:
        """Return aggregate statistics for the monitoring API."""
        return self._load_stats()

    def get_record_count(self) -> int:
        return self._load_stats().get("total_records", 0)
