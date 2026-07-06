"""
storage/catalog.py
==================
Data catalog manager — dataset registry for the Legislative Intelligence project.

The catalog tracks **metadata about datasets**, not the datasets themselves:

*  When was this dataset last ingested?
*  How many records does it contain?
*  What was the checksum of the source file?
*  Is the local copy complete or truncated?
*  Is the local copy stale (older than a configured threshold)?

This pattern is common in production data systems (e.g. LinkedIn's DataHub,
Netflix's Metacat, dbt's manifest.json, Airflow's dataset versioning).

Usage
-----
    from storage.catalog import CatalogManager

    catalog = CatalogManager("bills")          # loads data/catalog/bill_catalog.json

    # After ingestion, update the catalog entry
    catalog.update(
        dataset_id="bills_prs",
        record_count=4823,
        is_complete=True,
        source_version="2024-06-01",
        notes="Full refresh from PRS website",
    )

    # Before a pipeline run, check if data is stale
    if catalog.is_stale("bills_prs", max_age_days=7):
        logger.warning("Bill data is stale — re-ingestion recommended")

    # Quick summary for all datasets in this group
    catalog.print_summary()

Catalog files
-------------
bill_catalog.json    : ``CatalogManager("bills")``
company_catalog.json : ``CatalogManager("companies")``
market_catalog.json  : ``CatalogManager("market")``
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_GROUPS = {"bills", "companies", "market"}
_CATALOG_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "catalog"

# Maps group name → catalog filename prefix (avoids brittle string slicing)
_GROUP_FILENAME: dict[str, str] = {
    "bills": "bill",
    "companies": "company",
    "market": "market",
}


# ---------------------------------------------------------------------------
# DatasetEntry — lightweight value object
# ---------------------------------------------------------------------------

class DatasetEntry:
    """
    A single dataset entry from the catalog.

    This is a thin wrapper around the raw dict stored in the JSON file.
    Provides typed property accessors for the most commonly used fields.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def dataset_id(self) -> str:
        return self._data.get("dataset_id", "")

    @property
    def description(self) -> str:
        return self._data.get("description", "")

    @property
    def source(self) -> str:
        return self._data.get("source", "")

    # ------------------------------------------------------------------
    # Freshness
    # ------------------------------------------------------------------

    @property
    def last_ingested_at(self) -> datetime | None:
        raw = self._data.get("last_ingested_at")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None

    @property
    def is_complete(self) -> bool:
        return bool(self._data.get("is_complete", False))

    @property
    def record_count(self) -> int:
        return int(self._data.get("record_count", 0))

    @property
    def checksum_md5(self) -> str | None:
        return self._data.get("checksum_md5")

    # ------------------------------------------------------------------
    # Staleness check
    # ------------------------------------------------------------------

    def age_days(self) -> float | None:
        """
        Return the age of the dataset in days since last ingestion.

        Returns ``None`` if the dataset has never been ingested.
        """
        ts = self.last_ingested_at
        if ts is None:
            return None
        now = datetime.now(tz=timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return (now - ts).total_seconds() / 86400

    def is_stale(self, max_age_days: float = 7.0) -> bool:
        """
        Return ``True`` if the dataset has never been ingested or is older
        than ``max_age_days``.

        Parameters
        ----------
        max_age_days : float
            Maximum acceptable age in days before the dataset is considered stale.

        Returns
        -------
        bool
        """
        age = self.age_days()
        if age is None:
            return True          # Never ingested → always stale
        return age > max_age_days

    def to_dict(self) -> dict[str, Any]:
        """Return the raw underlying dict."""
        return self._data.copy()

    def __repr__(self) -> str:
        age = self.age_days()
        age_str = f"{age:.1f}d" if age is not None else "never"
        return (
            f"<DatasetEntry id={self.dataset_id!r} "
            f"records={self.record_count} "
            f"complete={self.is_complete} "
            f"age={age_str}>"
        )


# ---------------------------------------------------------------------------
# CatalogManager
# ---------------------------------------------------------------------------

class CatalogManager:
    """
    Reads and writes a group catalog JSON file.

    One ``CatalogManager`` instance maps to one catalog file:

    *  ``CatalogManager("bills")``     → ``data/catalog/bill_catalog.json``
    *  ``CatalogManager("companies")`` → ``data/catalog/company_catalog.json``
    *  ``CatalogManager("market")``    → ``data/catalog/market_catalog.json``

    Parameters
    ----------
    group : str
        Dataset group name.  Must be one of: ``'bills'``, ``'companies'``,
        ``'market'``.
    catalog_dir : Path | None
        Override the default catalog directory (useful in tests).
    """

    def __init__(
        self,
        group: str,
        catalog_dir: Path | None = None,
    ) -> None:
        if group not in _VALID_GROUPS:
            raise ValueError(
                f"Unknown catalog group {group!r}.  "
                f"Must be one of: {sorted(_VALID_GROUPS)}"
            )
        self._group = group
        self._catalog_dir = catalog_dir or _CATALOG_DIR
        self._path = self._catalog_dir / f"{_GROUP_FILENAME[group]}_catalog.json"
        self._data: dict[str, Any] = self._load()

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        """Load the catalog JSON file; return empty skeleton if missing."""
        if not self._path.is_file():
            logger.warning("Catalog file not found: %s — starting with empty catalog", self._path)
            return {
                "catalog_version": "1.0",
                "dataset_group": self._group,
                "last_updated": None,
                "datasets": {},
            }
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug("Catalog loaded: %s (%d datasets)", self._path, len(data.get("datasets", {})))
        return data

    def _save(self) -> None:
        """Atomically write the catalog back to disk."""
        self._data["last_updated"] = datetime.now(tz=timezone.utc).isoformat()
        self._catalog_dir.mkdir(parents=True, exist_ok=True)

        tmp_path = self._path.with_suffix(".tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(self._path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        logger.debug("Catalog saved: %s", self._path)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, dataset_id: str) -> DatasetEntry | None:
        """
        Return a :class:`DatasetEntry` for the given dataset ID.

        Returns ``None`` if the dataset is not registered.
        """
        raw = self._data.get("datasets", {}).get(dataset_id)
        if raw is None:
            return None
        return DatasetEntry(raw)

    def get_all(self) -> dict[str, DatasetEntry]:
        """Return all registered datasets as a ``{dataset_id: DatasetEntry}`` dict."""
        return {
            k: DatasetEntry(v)
            for k, v in self._data.get("datasets", {}).items()
        }

    def list_ids(self) -> list[str]:
        """Return all registered dataset IDs."""
        return list(self._data.get("datasets", {}).keys())

    def is_stale(self, dataset_id: str, max_age_days: float = 7.0) -> bool:
        """
        Return ``True`` if the dataset has never been ingested or is older
        than ``max_age_days``.

        Parameters
        ----------
        dataset_id : str
        max_age_days : float

        Returns
        -------
        bool
        """
        entry = self.get(dataset_id)
        if entry is None:
            logger.warning("Dataset %r not found in catalog — treating as stale", dataset_id)
            return True
        return entry.is_stale(max_age_days)

    def is_complete(self, dataset_id: str) -> bool:
        """Return True if the dataset is marked as complete."""
        entry = self.get(dataset_id)
        return entry.is_complete if entry else False

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def update(
        self,
        dataset_id: str,
        record_count: int | None = None,
        is_complete: bool | None = None,
        source_version: str | None = None,
        checksum_md5: str | None = None,
        notes: str | None = None,
        coverage: dict | None = None,
        **extra_fields: Any,
    ) -> DatasetEntry:
        """
        Update catalog metadata for a dataset and persist to disk.

        Only the fields you pass will be updated; all others remain unchanged.
        Automatically sets ``last_ingested_at`` to the current UTC timestamp.

        Parameters
        ----------
        dataset_id : str
            ID of the dataset to update.
        record_count : int | None
            Total number of records in the dataset.
        is_complete : bool | None
            Whether the ingestion completed without errors or truncation.
        source_version : str | None
            Version string from the source (e.g. a date, hash, or release tag).
        checksum_md5 : str | None
            MD5 hex digest of the primary data file (for integrity checks).
        notes : str | None
            Free-text notes about this ingestion run.
        coverage : dict | None
            Updated coverage metadata (e.g. ``{"start_date": "2000-01-01"}``).
        **extra_fields
            Any additional fields to store in the entry.

        Returns
        -------
        DatasetEntry
            The updated entry.

        Raises
        ------
        KeyError
            If ``dataset_id`` is not registered in this catalog.
        """
        datasets = self._data.setdefault("datasets", {})
        if dataset_id not in datasets:
            raise KeyError(
                f"Dataset {dataset_id!r} is not registered in the {self._group!r} catalog.  "
                f"Add it to data/catalog/{self._group.rstrip('s')}_catalog.json first."
            )

        entry = datasets[dataset_id]
        now_iso = datetime.now(tz=timezone.utc).isoformat()
        entry["last_ingested_at"] = now_iso
        entry["last_checked_at"] = now_iso

        if record_count is not None:
            entry["record_count"] = record_count
        if is_complete is not None:
            entry["is_complete"] = is_complete
        if source_version is not None:
            entry["source_version"] = source_version
        if checksum_md5 is not None:
            entry["checksum_md5"] = checksum_md5
        if notes is not None:
            entry["notes"] = notes
        if coverage is not None:
            existing_coverage = entry.get("coverage", {})
            existing_coverage.update(coverage)
            entry["coverage"] = existing_coverage
        for k, v in extra_fields.items():
            entry[k] = v

        self._save()

        updated = DatasetEntry(entry)
        logger.info(
            "Catalog updated | group=%s dataset=%s records=%d complete=%s",
            self._group,
            dataset_id,
            updated.record_count,
            updated.is_complete,
        )
        return updated

    def touch(self, dataset_id: str) -> None:
        """
        Mark a dataset as checked now without changing other metadata.

        Useful at the start of a pipeline run to record a freshness check
        even when no new data was downloaded.
        """
        datasets = self._data.setdefault("datasets", {})
        if dataset_id in datasets:
            datasets[dataset_id]["last_checked_at"] = (
                datetime.now(tz=timezone.utc).isoformat()
            )
            self._save()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def print_summary(self) -> None:
        """Print a human-readable summary of all datasets to stdout."""
        entries = self.get_all()
        print(f"\n{'─' * 70}")
        print(f"  Catalog: {self._group}  ({len(entries)} datasets)")
        print(f"  File:    {self._path}")
        print(f"{'─' * 70}")
        for ds_id, entry in entries.items():
            age = entry.age_days()
            age_str = f"{age:.1f}d ago" if age is not None else "never ingested"
            stale_flag = " ⚠ STALE" if entry.is_stale() else ""
            print(
                f"  {ds_id:<35} "
                f"records={entry.record_count:<8} "
                f"complete={str(entry.is_complete):<6} "
                f"{age_str}{stale_flag}"
            )
        print(f"{'─' * 70}\n")

    def __repr__(self) -> str:
        return (
            f"<CatalogManager group={self._group!r} "
            f"datasets={len(self.list_ids())} "
            f"path={self._path!r}>"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_md5(path: str | os.PathLike, chunk_size: int = 65536) -> str:
    """
    Compute the MD5 hex digest of a file.

    Used to populate ``checksum_md5`` in catalog entries so you can detect
    if a source file has changed since last ingestion.

    Parameters
    ----------
    path : str | PathLike
        Path to the file.
    chunk_size : int
        Read buffer size in bytes.

    Returns
    -------
    str
        32-character lowercase hexadecimal MD5 digest.
    """
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()
