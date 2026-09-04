"""
storage/embedding_repository.py
================================
Repository for persisting and querying legislative bill embeddings (Task 5.2).

Saves embeddings in two formats:
1. Columnar Parquet under ``data/embeddings/{model_name}/embeddings.parquet``
   containing complete records (metadata + vectors).
2. Dense NumPy matrix under ``data/embeddings/{model_name}/embeddings.npy``
   containing the raw embedding matrix (aligned by bill_id).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.embedding_record import EmbeddingRecord
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


class EmbeddingRepository:
    """
    Repository for persisting and querying legislative bill embeddings.

    Parameters
    ----------
    embeddings_dir : Path, optional
        Root directory for embedding artefacts. Defaults to settings.EMBEDDINGS_DIR.
    model_name : str, optional
        The user-friendly name of the embedding model. Defaults to settings.DEFAULT_EMBEDDING_MODEL.
    """

    _INDEX_FILENAME = "index.json"

    def __init__(
        self,
        embeddings_dir: Optional[Path] = None,
        model_name: Optional[str] = None,
    ) -> None:
        from config.settings import settings

        self._embeddings_dir: Path = embeddings_dir or settings.EMBEDDINGS_DIR
        self._model_name: str = (model_name or settings.DEFAULT_EMBEDDING_MODEL).strip().lower()
        self._model_dir = self._embeddings_dir / self._model_name
        ensure_dir(self._model_dir)

        self._parquet_path = self._model_dir / "embeddings.parquet"
        self._npy_path = self._model_dir / "embeddings.npy"
        self._index_path = self._model_dir / self._INDEX_FILENAME

        # In-memory set of existing bill IDs (lazy-loaded)
        self._index: Optional[set[str]] = None

        logger.debug(
            "EmbeddingRepository initialised | dir=%s model=%s",
            self._model_dir,
            self._model_name,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_index(self) -> set[str]:
        """Load (or initialise) the in-memory bill-ID index."""
        if self._index is not None:
            return self._index
        if self._index_path.is_file():
            try:
                with self._index_path.open("r", encoding="utf-8") as fh:
                    self._index = set(json.load(fh))
            except Exception as exc:
                logger.warning("Could not load embedding index: %s — rebuilding.", exc)
                self._index = set()
        else:
            self._index = set()
        return self._index

    def _save_index(self) -> None:
        """Persist the in-memory bill-ID index to disk."""
        idx = self._load_index()
        try:
            with self._index_path.open("w", encoding="utf-8") as fh:
                json.dump(sorted(idx), fh)
        except Exception as exc:
            logger.error("Failed to persist embedding index: %s", exc)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_many(self, records: list[EmbeddingRecord]) -> int:
        """
        Persist a list of EmbeddingRecords.

        Merges new records with existing records (deduplicating by bill_id).
        Sorts the merged dataset alphabetically by bill_id to maintain a strict
        1-to-1 alignment with the rows in the NumPy .npy file.

        Parameters
        ----------
        records : list[EmbeddingRecord]
            List of new/updated EmbeddingRecord objects to save.

        Returns
        -------
        int
            Total number of records in the repository.
        """
        import numpy as np
        import pandas as pd

        if not records:
            logger.info("EmbeddingRepository.save_many: no records to save.")
            return self.count()

        # Group new records by bill_id (take last if duplicates passed in)
        new_records_map = {r.bill_id: r for r in records}

        # Load existing records
        existing_records = self.load_all()
        existing_records_map = {r.bill_id: r for r in existing_records}

        # Merge
        existing_records_map.update(new_records_map)
        merged_records = list(existing_records_map.values())

        # Sort alphabetically by bill_id
        merged_records.sort(key=lambda r: r.bill_id)

        # 1. Save to Parquet
        rows = [r.to_dict() for r in merged_records]
        df = pd.DataFrame(rows)
        try:
            df.to_parquet(self._parquet_path, index=False)
        except Exception as exc:
            logger.error("Failed to write Parquet embeddings: %s", exc)
            raise

        # 2. Save vectors to NumPy (.npy)
        vectors = [r.embedding_vector for r in merged_records]
        if vectors:
            try:
                np_matrix = np.array(vectors, dtype=np.float32)
                np.save(self._npy_path, np_matrix)
            except Exception as exc:
                logger.error("Failed to write NumPy embedding matrix: %s", exc)
                raise
        else:
            if self._npy_path.is_file():
                self._npy_path.unlink()

        # 3. Refresh and save index
        self._index = {r.bill_id for r in merged_records}
        self._save_index()

        logger.info(
            "EmbeddingRepository.save_many: wrote %d records (delta=%d) to %s",
            len(merged_records),
            len(records),
            self._model_dir,
        )
        return len(merged_records)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str) -> Optional[EmbeddingRecord]:
        """Retrieve the EmbeddingRecord for a specific bill."""
        if not self.exists(bill_id):
            return None
        # We can read the Parquet file and filter
        import pandas as pd
        try:
            df = pd.read_parquet(self._parquet_path)
            row = df[df["bill_id"] == bill_id]
            if row.empty:
                return None
            return EmbeddingRecord.from_dict(row.iloc[0].to_dict())
        except Exception as exc:
            logger.error("Failed to read bill '%s' from embedding Parquet: %s", bill_id, exc)
            return None

    def load_all(self) -> list[EmbeddingRecord]:
        """Load and return all EmbeddingRecords in alphabetical order of bill_id."""
        if not self._parquet_path.is_file():
            return []
        import pandas as pd
        try:
            df = pd.read_parquet(self._parquet_path)
            records = []
            for _, row in df.iterrows():
                records.append(EmbeddingRecord.from_dict(row.to_dict()))
            # Ensure return is sorted
            records.sort(key=lambda r: r.bill_id)
            return records
        except Exception as exc:
            logger.error("Failed to load all embeddings from Parquet: %s", exc)
            return []

    def load_dataframe(self) -> pd.DataFrame:
        """Load all embeddings as a pandas DataFrame."""
        import pandas as pd
        if not self._parquet_path.is_file():
            return pd.DataFrame()
        try:
            return pd.read_parquet(self._parquet_path)
        except Exception as exc:
            logger.error("Failed to load embedding DataFrame: %s", exc)
            return pd.DataFrame()

    def load_numpy(self) -> Optional[np.ndarray]:
        """Load all embedding vectors as a 2D NumPy array."""
        import numpy as np
        if not self._npy_path.is_file():
            return None
        try:
            return np.load(self._npy_path)
        except Exception as exc:
            logger.error("Failed to load NumPy embedding matrix: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Existence / Utility
    # ------------------------------------------------------------------

    def exists(self, bill_id: str) -> bool:
        """Return True if the bill already has a saved embedding."""
        return bill_id in self._load_index()

    def count(self) -> int:
        """Return the total number of saved embeddings."""
        return len(self._load_index())

    def get_existing_bill_ids(self) -> set[str]:
        """Return the set of all bill IDs currently saved."""
        return set(self._load_index())

    def clear(self) -> None:
        """Delete all repository files for this model."""
        for path in [self._parquet_path, self._npy_path, self._index_path]:
            if path.is_file():
                try:
                    path.unlink()
                    logger.info("Deleted embedding file: %s", path)
                except Exception as exc:
                    logger.error("Failed to delete embedding file %s: %s", path, exc)
        self._index = set()

    @property
    def model_dir(self) -> Path:
        """Path to the model subdirectory."""
        return self._model_dir

    @property
    def parquet_path(self) -> Path:
        """Path to the Parquet file."""
        return self._parquet_path

    @property
    def npy_path(self) -> Path:
        """Path to the NumPy .npy file."""
        return self._npy_path

    def __repr__(self) -> str:
        return (
            f"<EmbeddingRepository model={self._model_name!r} "
            f"records={self.count()}>"
        )
