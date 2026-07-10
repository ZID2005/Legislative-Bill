"""
storage/mapping_repository.py
==============================
Repository for storing and retrieving Bill-Company mapping records.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.mapping_record import BillCompanyMapping
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


class MappingRepository:
    """
    Repository for persisting and querying BillCompanyMapping records.
    """

    def __init__(self, mappings_dir: str | Path | None = None) -> None:
        from config.settings import settings

        if mappings_dir:
            self._mappings_dir = Path(mappings_dir)
        else:
            self._mappings_dir = settings.DATA_DIR / "mappings"

        ensure_dir(self._mappings_dir)
        logger.debug("MappingRepository initialised | mappings_dir=%s", self._mappings_dir)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, mapping: BillCompanyMapping) -> None:
        """
        Persist a bill-company mapping record as a JSON file.

        Parameters
        ----------
        mapping : BillCompanyMapping
            A validated schemas.mapping_record.BillCompanyMapping object.
        """
        dest_path = self._mappings_dir / f"{mapping.bill_id}.json"
        save_json(mapping.to_dict(), dest_path)
        logger.info("Saved bill-company mapping to repository: %s", mapping.bill_id)

    def save_many(self, mappings: list[BillCompanyMapping]) -> None:
        """
        Persist multiple mapping records.

        Parameters
        ----------
        mappings : list[BillCompanyMapping]
            List of BillCompanyMapping objects to persist.
        """
        for mapping in mappings:
            self.save(mapping)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str) -> Optional[BillCompanyMapping]:
        """
        Retrieve a single mapping record by bill ID.

        Returns None if not found.
        """
        src_path = self._mappings_dir / f"{bill_id}.json"
        if not file_exists(src_path):
            logger.debug("Mapping record file not found: %s", src_path)
            return None
        try:
            data = load_json(src_path)
            return BillCompanyMapping.from_dict(data)
        except Exception as e:
            logger.error("Failed to load mapping record '%s': %s", bill_id, e)
            return None

    def get_all(self) -> list[BillCompanyMapping]:
        """Return all stored mapping records."""
        mappings = []
        try:
            files = list_files(self._mappings_dir, "*.json")
            for f in files:
                bill_id = f.stem
                mapping = self.get(bill_id)
                if mapping:
                    mappings.append(mapping)
        except Exception as e:
            logger.error("Failed to list mapping records: %s", e)
        return mappings

    # ------------------------------------------------------------------
    # Search Lookups
    # ------------------------------------------------------------------

    def get_by_bill(self, bill_id: str) -> Optional[BillCompanyMapping]:
        """Lookup mapping by bill ID (exact match)."""
        return self.get(bill_id)

    def get_by_company(self, company_identifier: str) -> list[BillCompanyMapping]:
        """
        Lookup mappings where the specified company is listed as a candidate.
        Checks for matching ISIN, NSE/BSE ticker, or company name (case-insensitive substring).
        """
        ident = company_identifier.strip().lower()
        if not ident:
            return []

        results = []
        for mapping in self.get_all():
            for comp in mapping.candidate_companies:
                if (
                    comp.get("isin", "").lower() == ident
                    or comp.get("ticker_nse", "").lower() == ident
                    or comp.get("ticker_bse", "").lower() == ident
                    or ident in comp.get("company_name", "").lower()
                ):
                    results.append(mapping)
                    break
        return results

    def get_by_sector(self, sector: str) -> list[BillCompanyMapping]:
        """
        Lookup mappings matching a sector as primary or secondary (case-insensitive).
        """
        sector_lower = sector.strip().lower()
        if not sector_lower:
            return []

        results = []
        for mapping in self.get_all():
            if mapping.primary_sector.strip().lower() == sector_lower or any(
                s.strip().lower() == sector_lower for s in mapping.secondary_sectors
            ):
                results.append(mapping)
        return results

    def get_by_ministry(self, ministry: str) -> list[BillCompanyMapping]:
        """
        Lookup mappings by sponsoring ministry (case-insensitive).
        """
        m_lower = ministry.strip().lower()
        if not m_lower:
            return []

        return [m for m in self.get_all() if m.ministry.strip().lower() == m_lower]

    def get_by_policy_domain(self, policy_domain: str) -> list[BillCompanyMapping]:
        """
        Lookup mappings by policy domain (case-insensitive).
        """
        pd_lower = policy_domain.strip().lower()
        if not pd_lower:
            return []

        return [m for m in self.get_all() if m.policy_domain.strip().lower() == pd_lower]

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(self, bill_id: str) -> bool:
        """Return True if a mapping record with the given bill ID exists."""
        src_path = self._mappings_dir / f"{bill_id}.json"
        return file_exists(src_path)

    def delete(self, bill_id: str) -> None:
        """Remove a mapping record."""
        src_path = self._mappings_dir / f"{bill_id}.json"
        if file_exists(src_path):
            os.remove(src_path)
            logger.info("Deleted mapping record: %s", bill_id)

    def count(self) -> int:
        """Return the total number of stored mapping records."""
        try:
            files = list_files(self._mappings_dir, "*.json")
            return len(files)
        except Exception as e:
            logger.error("Failed to count mapping records: %s", e)
            return 0

    def __repr__(self) -> str:
        return f"<MappingRepository mappings_dir={self._mappings_dir!r}>"
