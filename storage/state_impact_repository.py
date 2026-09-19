"""
storage/state_impact_repository.py
==================================
Repository for Indian State legislative bill economic and market impact assessment records.

Manages persistence, retrieval, and multi-attribute search for
`StateImpactAssessment` records in `data/state_bills/impact_assessments/`.
Maintains strict isolation from Central Government storage.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.state_impact_assessment import StateImpactAssessment
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


class StateImpactRepository:
    """
    Repository for storing, retrieving, and querying StateImpactAssessment records.
    """

    def __init__(self, impact_dir: Optional[Path] = None) -> None:
        """
        Initialize the State impact assessment repository.

        Parameters
        ----------
        impact_dir : Path | None
            Directory to store impact assessment records.
            Defaults to settings.STATE_BILLS_DIR / "impact_assessments".
        """
        from config.settings import settings

        if impact_dir is None:
            self._impact_dir = settings.STATE_BILLS_DIR / "impact_assessments"
        else:
            self._impact_dir = Path(impact_dir)

        ensure_dir(self._impact_dir)
        logger.debug("StateImpactRepository initialized | dir=%s", self._impact_dir)

    @property
    def impact_dir(self) -> Path:
        return self._impact_dir

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: StateImpactAssessment) -> None:
        """Persist a single StateImpactAssessment record as JSON."""
        dest_path = self._impact_dir / f"{record.bill_id}.json"
        save_json(record.to_dict(), dest_path)
        logger.info("Saved state impact assessment: %s", record.bill_id)

    def save_many(self, records: list[StateImpactAssessment]) -> None:
        """Persist multiple StateImpactAssessment records."""
        for r in records:
            self.save(r)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str) -> Optional[StateImpactAssessment]:
        """Retrieve a StateImpactAssessment record by bill_id."""
        src_path = self._impact_dir / f"{bill_id}.json"
        if not file_exists(src_path):
            logger.debug("State impact assessment record not found: %s", src_path)
            return None
        try:
            data = load_json(src_path)
            return StateImpactAssessment.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load state impact assessment '%s': %s", bill_id, exc)
            return None

    def get_all(self) -> list[StateImpactAssessment]:
        """Return all stored StateImpactAssessment records."""
        records: list[StateImpactAssessment] = []
        try:
            files = list_files(self._impact_dir, "*.json")
            for f in files:
                rec = self.get(f.stem)
                if rec:
                    records.append(rec)
        except Exception as exc:
            logger.error("Failed to list state impact assessment records: %s", exc)
        return records

    def get_by_state(self, state: str) -> list[StateImpactAssessment]:
        """Filter records by State name (case-insensitive, normalized)."""
        target_norm = normalize_state(state) or state.strip().lower()
        results = []
        for r in self.get_all():
            r_norm = normalize_state(r.state) or r.state.strip().lower()
            if r_norm.lower() == target_norm.lower():
                results.append(r)
        return results

    def get_by_eligibility(self, eligibility: str) -> list[StateImpactAssessment]:
        """Filter records by modeling eligibility (case-insensitive)."""
        target = eligibility.strip().upper()
        return [r for r in self.get_all() if r.modeling_eligibility.upper() == target]

    def get_by_relevance(self, relevance: str) -> list[StateImpactAssessment]:
        """Filter records by market relevance (case-insensitive)."""
        target = relevance.strip().upper()
        return [r for r in self.get_all() if r.market_relevance.upper() == target]

    def get_by_strength(self, strength: str) -> list[StateImpactAssessment]:
        """Filter records by economic impact strength (case-insensitive)."""
        target = strength.strip().upper()
        return [r for r in self.get_all() if r.economic_strength.upper() == target]

    def get_by_mechanism(self, mechanism: str) -> list[StateImpactAssessment]:
        """Filter records by economic mechanism."""
        target = mechanism.strip().lower()
        return [r for r in self.get_all() if any(target == m.lower() for m in r.economic_mechanisms)]

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(self, bill_id: str) -> bool:
        """Return True if an impact assessment for bill_id exists."""
        return file_exists(self._impact_dir / f"{bill_id}.json")

    def delete(self, bill_id: str) -> None:
        """Delete an impact assessment record."""
        p = self._impact_dir / f"{bill_id}.json"
        if file_exists(p):
            os.remove(p)
            logger.info("Deleted state impact assessment record: %s", bill_id)

    def count(self) -> int:
        """Return the count of stored state impact assessment records."""
        try:
            return len(list_files(self._impact_dir, "*.json"))
        except Exception:
            return 0

    def __repr__(self) -> str:
        return f"<StateImpactRepository dir={self._impact_dir!r} count={self.count()}>"
