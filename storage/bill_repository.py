"""
storage/bill_repository.py
==========================
Repository for legislative bill data.

This module is the **single access point** for reading and writing bill
records. All other modules must use this repository; they must not touch
the ``data/bills/`` directory directly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


class BillRepository:
    """
    Repository for bill metadata and full text.
    """

    def __init__(self) -> None:
        from config.settings import settings

        self._metadata_dir = settings.BILLS_DIR / "metadata"
        self._pdfs_dir = settings.BILLS_DIR / "pdfs"
        ensure_dir(self._metadata_dir)
        ensure_dir(self._pdfs_dir)
        logger.debug("BillRepository initialised | metadata_dir=%s", self._metadata_dir)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, bill: Bill) -> None:
        """
        Persist a bill record as a JSON file.

        Parameters
        ----------
        bill : Bill
            A validated ``schemas.bill.Bill`` object.
        """
        dest_path = self._metadata_dir / f"{bill.bill_id}.json"
        save_json(bill.to_dict(), dest_path)
        logger.info("Saved bill to repository: %s", bill.bill_id)

    def save_many(self, bills: list[Bill]) -> None:
        """
        Persist multiple bill records.

        Parameters
        ----------
        bills : list[Bill]
            List of ``Bill`` objects to persist.
        """
        for bill in bills:
            self.save(bill)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str) -> Optional[Bill]:
        """
        Retrieve a single bill by its unique ID.

        Returns ``None`` if not found (does not raise).
        """
        src_path = self._metadata_dir / f"{bill_id}.json"
        if not file_exists(src_path):
            logger.debug("Bill file not found: %s", src_path)
            return None
        try:
            data = load_json(src_path)
            return Bill.from_dict(data)
        except Exception as e:
            logger.error("Failed to load bill '%s': %s", bill_id, e)
            return None

    def get_all(self) -> list[Bill]:
        """Return all stored bill records."""
        bills = []
        try:
            files = list_files(self._metadata_dir, "*.json")
            for f in files:
                bill_id = f.stem
                bill = self.get(bill_id)
                if bill:
                    bills.append(bill)
        except Exception as e:
            logger.error("Failed to list bills: %s", e)
        return bills

    def get_by_year(self, year: int) -> list[Bill]:
        """Return all bills introduced in a given year."""
        return [b for b in self.get_all() if b.year == year]

    def get_by_ministry(self, ministry: str) -> list[Bill]:
        """Return bills sponsored by a given ministry (case-insensitive search)."""
        m_lower = ministry.strip().lower()
        return [b for b in self.get_all() if b.ministry.strip().lower() == m_lower]

    def get_by_status(self, status: str) -> list[Bill]:
        """Return bills filtered by status."""
        return [b for b in self.get_all() if b.status.value == status or b.status == status]

    def get_by_sector(self, sector: str) -> list[Bill]:
        """Return bills mapped to a given economic sector."""
        s_lower = sector.strip().lower()
        return [b for b in self.get_all() if any(s.strip().lower() == s_lower for s in b.sectors)]

    def get_all_ids(self) -> list[str]:
        """Return a list of all stored bill IDs."""
        try:
            files = list_files(self._metadata_dir, "*.json")
            return [f.stem for f in files]
        except Exception as e:
            logger.error("Failed to list bill IDs: %s", e)
            return []

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(self, bill_id: str) -> bool:
        """Return True if a bill with the given ID is already stored."""
        src_path = self._metadata_dir / f"{bill_id}.json"
        return file_exists(src_path)

    def delete(self, bill_id: str) -> None:
        """Remove a bill record and its associated PDF if present."""
        bill = self.get(bill_id)
        src_path = self._metadata_dir / f"{bill_id}.json"
        if file_exists(src_path):
            os.remove(src_path)
            logger.info("Deleted bill metadata: %s", bill_id)

        if bill and bill.pdf_path:
            pdf_path = Path(bill.pdf_path)
            if pdf_path.is_file():
                os.remove(pdf_path)
                logger.info("Deleted bill PDF: %s", pdf_path)

    def count(self) -> int:
        """Return the total number of stored bills."""
        return len(self.get_all_ids())

    def __repr__(self) -> str:
        return f"<BillRepository metadata_dir={self._metadata_dir!r}>"
