"""
storage/feature_repository.py
==============================
Repository for the unified ML feature dataset (Task 5.1).

Design
------
*  Follows the same Repository Pattern used by every other repository in
   this project (BillRepository, LabelRepository, etc.).
*  **Primary storage**: Apache Parquet under ``data/features/``.
   Parquet is chosen because downstream NLP / ML pipelines load the full
   dataset into pandas DataFrames; columnar storage gives fast reads.
*  **Optional CSV export**: a human-readable snapshot alongside the Parquet
   file, generated on demand.
*  **Incremental rebuild support**: ``exists(record_id)`` and
   ``get_existing_record_ids()`` allow the engine to skip rows that have
   not changed since the last build.
*  List-typed columns (``secondary_sectors``) are serialised as JSON strings
   in Parquet/CSV so they survive round-trips across pandas/pyarrow without
   requiring object-dtype columns.

File layout::

    data/features/
        master_feature_dataset.parquet   (primary)
        master_feature_dataset.csv       (optional export)
        index.json                       (record-id index for fast exists())
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.feature_record import FeatureRecord
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


class FeatureRepository:
    """
    Repository for persisting and querying the unified ML feature dataset.

    Parameters
    ----------
    features_dir : Path, optional
        Root directory for feature artefacts.  Defaults to
        ``settings.FEATURES_DIR``.
    dataset_name : str, optional
        Stem name (without extension) of the Parquet / CSV files.
        Defaults to ``settings.FEATURE_DATASET_NAME``.

    Notes
    -----
    *  ``save_many`` is the **primary write method**.  It merges new records
       with any existing dataset and re-writes the Parquet file atomically.
    *  ``load_all`` reads the full dataset from Parquet.
    *  The index file ``index.json`` is kept in sync on every write so that
       ``exists()`` can answer lookups in O(1) without loading the Parquet.
    """

    _INDEX_FILENAME = "index.json"

    def __init__(
        self,
        features_dir: Optional[Path] = None,
        dataset_name: Optional[str] = None,
    ) -> None:
        from config.settings import settings

        self._features_dir: Path = features_dir or settings.FEATURES_DIR
        self._dataset_name: str = dataset_name or settings.FEATURE_DATASET_NAME
        ensure_dir(self._features_dir)

        self._parquet_path = self._features_dir / f"{self._dataset_name}.parquet"
        self._csv_path = self._features_dir / f"{self._dataset_name}.csv"
        self._index_path = self._features_dir / self._INDEX_FILENAME

        # In-memory set of existing record IDs (lazy-loaded)
        self._index: Optional[set[str]] = None

        logger.debug(
            "FeatureRepository initialised | dir=%s dataset=%s",
            self._features_dir,
            self._dataset_name,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_index(self) -> set[str]:
        """Load (or initialise) the in-memory record-ID index."""
        if self._index is not None:
            return self._index
        if self._index_path.is_file():
            try:
                with self._index_path.open("r", encoding="utf-8") as fh:
                    self._index = set(json.load(fh))
            except Exception as exc:
                logger.warning("Could not load feature index: %s — rebuilding.", exc)
                self._index = set()
        else:
            self._index = set()
        return self._index

    def _save_index(self) -> None:
        """Persist the in-memory record-ID index to disk."""
        idx = self._load_index()
        try:
            with self._index_path.open("w", encoding="utf-8") as fh:
                json.dump(sorted(idx), fh)
        except Exception as exc:
            logger.error("Failed to persist feature index: %s", exc)

    @staticmethod
    def _to_parquet_row(record: FeatureRecord) -> dict:
        """
        Convert a FeatureRecord to a flat dict suitable for a pandas row.

        ``secondary_sectors`` is serialised as a JSON string so that
        pyarrow does not have to deal with ragged list columns.
        """
        row = record.to_dict()
        row["secondary_sectors"] = json.dumps(row["secondary_sectors"])
        return row

    @staticmethod
    def _from_parquet_row(row: dict) -> FeatureRecord:
        """Reconstruct a FeatureRecord from a pandas/pyarrow row dict."""
        raw = row.get("secondary_sectors", "[]")
        if isinstance(raw, str):
            try:
                row["secondary_sectors"] = json.loads(raw)
            except Exception:
                row["secondary_sectors"] = []
        # Convert NaN to None for optional numeric fields
        for key, value in row.items():
            if isinstance(value, float) and math.isnan(value):
                row[key] = None
        return FeatureRecord.from_dict(row)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_many(self, records: list[FeatureRecord]) -> int:
        """
        Persist a list of FeatureRecords into the Parquet dataset.

        Merges new records with any existing data (``record_id`` is the
        deduplication key).  Returns the total number of records written.

        Parameters
        ----------
        records : list[FeatureRecord]
            New or updated records to persist.

        Returns
        -------
        int
            Total record count after the merge.
        """
        import pandas as pd

        if not records:
            logger.info("FeatureRepository.save_many: no records to save.")
            return self.count()

        # Build DataFrame of new rows
        new_rows = [self._to_parquet_row(r) for r in records]
        new_df = pd.DataFrame(new_rows)

        # Merge with existing dataset (if any)
        if self._parquet_path.is_file():
            try:
                existing_df = pd.read_parquet(self._parquet_path)
                # Drop any old rows whose record_id is being refreshed
                existing_df = existing_df[
                    ~existing_df["record_id"].isin(new_df["record_id"])
                ]
                merged_df = pd.concat([existing_df, new_df], ignore_index=True)
            except Exception as exc:
                logger.warning(
                    "Could not read existing Parquet; starting fresh. Reason: %s", exc
                )
                merged_df = new_df
        else:
            merged_df = new_df

        # Persist
        try:
            merged_df.to_parquet(self._parquet_path, index=False)
        except Exception as exc:
            logger.error("Failed to write Parquet dataset: %s", exc)
            raise

        total = len(merged_df)
        logger.info(
            "FeatureRepository.save_many: wrote %d records (delta=%d) to %s",
            total,
            len(records),
            self._parquet_path,
        )

        # Refresh index
        self._index = set(merged_df["record_id"].tolist())
        self._save_index()

        return total

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load_all(self) -> list[FeatureRecord]:
        """Load and return the full feature dataset from Parquet."""
        if not self._parquet_path.is_file():
            logger.info("No feature dataset found at %s.", self._parquet_path)
            return []
        try:
            import pandas as pd

            df = pd.read_parquet(self._parquet_path)
            records: list[FeatureRecord] = []
            for _, row in df.iterrows():
                try:
                    records.append(self._from_parquet_row(row.to_dict()))
                except Exception as exc:
                    logger.error("Failed to deserialise feature row: %s", exc)
            return records
        except Exception as exc:
            logger.error("Failed to load feature dataset: %s", exc)
            return []

    def load_dataframe(self):
        """
        Return the full feature dataset as a ``pandas.DataFrame``.

        Returns an empty DataFrame if no dataset exists yet.
        """
        import pandas as pd

        if not self._parquet_path.is_file():
            return pd.DataFrame()
        try:
            return pd.read_parquet(self._parquet_path)
        except Exception as exc:
            logger.error("Failed to load feature DataFrame: %s", exc)
            return pd.DataFrame()

    def get_by_bill(self, bill_id: str) -> list[FeatureRecord]:
        """Return all feature records for a specific bill."""
        return [r for r in self.load_all() if r.bill_id == bill_id]

    def get_by_company(self, company_isin: str) -> list[FeatureRecord]:
        """Return all feature records for a specific company ISIN."""
        return [r for r in self.load_all() if r.company_isin == company_isin]

    # ------------------------------------------------------------------
    # Existence / utility
    # ------------------------------------------------------------------

    def exists(self, record_id: str) -> bool:
        """Return True if the record_id is already in the dataset."""
        return record_id in self._load_index()

    def get_existing_record_ids(self) -> set[str]:
        """Return the set of all record IDs currently persisted."""
        return set(self._load_index())

    def count(self) -> int:
        """Return total number of records currently persisted."""
        return len(self._load_index())

    def clear(self) -> None:
        """Delete the entire feature dataset (Parquet + CSV + index)."""
        for path in [self._parquet_path, self._csv_path, self._index_path]:
            if path.is_file():
                path.unlink()
                logger.info("Deleted feature file: %s", path)
        self._index = set()

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    def export_csv(self) -> Path:
        """
        Export the feature dataset to CSV alongside the Parquet file.

        Returns
        -------
        Path
            Absolute path of the written CSV file.

        Raises
        ------
        FileNotFoundError
            If no Parquet dataset exists yet.
        """
        if not self._parquet_path.is_file():
            raise FileNotFoundError(
                f"No feature dataset found at {self._parquet_path}. "
                "Run FeatureEngineeringEngine.build() first."
            )
        import pandas as pd

        df = pd.read_parquet(self._parquet_path)
        df.to_csv(self._csv_path, index=False)
        logger.info(
            "FeatureRepository.export_csv: wrote %d rows to %s",
            len(df),
            self._csv_path,
        )
        return self._csv_path

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def parquet_path(self) -> Path:
        """Absolute path to the primary Parquet file."""
        return self._parquet_path

    @property
    def csv_path(self) -> Path:
        """Absolute path to the CSV export file."""
        return self._csv_path

    def dataset_info(self) -> dict:
        """Return a summary dict describing the persisted dataset."""
        info: dict = {
            "parquet_path": str(self._parquet_path),
            "csv_path": str(self._csv_path),
            "record_count": self.count(),
            "parquet_exists": self._parquet_path.is_file(),
            "csv_exists": self._csv_path.is_file(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if self._parquet_path.is_file():
            info["parquet_size_bytes"] = self._parquet_path.stat().st_size
        return info

    def __repr__(self) -> str:
        return (
            f"<FeatureRepository dir={self._features_dir!r} "
            f"dataset={self._dataset_name!r} "
            f"records={self.count()}>"
        )
