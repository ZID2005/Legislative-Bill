"""
storage/market_model_repository.py
==================================
Repository for storing and retrieving Market Model estimation records.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.market_model import MarketModelRecord
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


class MarketModelRepository:
    """
    Repository for persisting and querying MarketModelRecord objects.
    """

    def __init__(self, model_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._model_dir = model_dir or settings.DATA_DIR / "market_models"
        ensure_dir(self._model_dir)
        logger.debug("MarketModelRepository initialised | model_dir=%s", self._model_dir)

    def _get_path(self, bill_id: str, company_isin: str) -> Path:
        # Sanitize name to avoid directory traversal
        sanitized_bill = bill_id.replace("/", "_").replace("\\", "_")
        return self._model_dir / f"{sanitized_bill}_{company_isin}.json"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: MarketModelRecord) -> None:
        """
        Persist a market model record as a JSON file.
        """
        dest_path = self._get_path(record.bill_id, record.company_isin)
        save_json(record.to_dict(), dest_path)
        logger.info(
            "Saved market model record for bill %s, company %s (%s)",
            record.bill_id,
            record.company_symbol,
            record.company_isin,
        )

    def save_many(self, records: list[MarketModelRecord]) -> None:
        """
        Persist multiple market model records.
        """
        for record in records:
            self.save(record)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str, company_isin: str) -> Optional[MarketModelRecord]:
        """
        Retrieve a market model record by bill ID and company ISIN.
        """
        src_path = self._get_path(bill_id, company_isin)
        if not file_exists(src_path):
            return None
        try:
            data = load_json(src_path)
            return MarketModelRecord.from_dict(data)
        except Exception as e:
            logger.error(
                "Failed to load market model record for bill %s, company %s: %s",
                bill_id,
                company_isin,
                e,
            )
            return None

    def get_all(self) -> list[MarketModelRecord]:
        """
        Return all stored market model records.
        """
        records = []
        try:
            files = list_files(self._model_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    records.append(MarketModelRecord.from_dict(data))
                except Exception as e:
                    logger.error("Failed to load market model file %s: %s", f.name, e)
        except Exception as e:
            logger.error("Failed to list market model records: %s", e)
        return records

    def get_by_bill(self, bill_id: str) -> list[MarketModelRecord]:
        """
        Return market model records filtered by bill ID.
        """
        return [r for r in self.get_all() if r.bill_id == bill_id]

    def get_by_company(self, company_isin: str) -> list[MarketModelRecord]:
        """
        Return market model records filtered by company ISIN.
        """
        return [r for r in self.get_all() if r.company_isin == company_isin]

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(self, bill_id: str, company_isin: str) -> bool:
        """
        Return True if a record exists for the given bill and company.
        """
        src_path = self._get_path(bill_id, company_isin)
        return file_exists(src_path)

    def delete(self, bill_id: str, company_isin: str) -> None:
        """
        Remove a market model record.
        """
        src_path = self._get_path(bill_id, company_isin)
        if file_exists(src_path):
            os.remove(src_path)
            logger.info("Deleted market model record: bill=%s, company=%s", bill_id, company_isin)

    def count(self) -> int:
        """
        Return the total number of stored market model records.
        """
        try:
            files = list_files(self._model_dir, "*.json")
            return len(files)
        except Exception as e:
            logger.error("Failed to count market model records: %s", e)
            return 0
