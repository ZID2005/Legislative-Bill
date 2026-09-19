"""
storage/state_bill_repository.py
================================
Repository for Indian State legislative bill data.

Manages persistence and retrieval of State bills strictly isolated
from Central Government production bill records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.bill import Bill, BillJurisdiction
from storage.bill_repository import BillRepository

logger = get_logger(__name__)


class StateBillRepository(BillRepository):
    """
    Repository dedicated to State Government legislative bill records.

    Default storage is rooted at ``settings.STATE_BILLS_DIR`` rather than
    the frozen Central ``settings.BILLS_DIR``.
    """

    def __init__(
        self,
        bills_dir: Optional[Path] = None,
        metadata_dir: Optional[Path] = None,
        pdfs_dir: Optional[Path] = None,
    ) -> None:
        from config.settings import settings

        target_bills_dir = Path(bills_dir) if bills_dir else settings.STATE_BILLS_DIR
        super().__init__(
            bills_dir=target_bills_dir,
            metadata_dir=metadata_dir,
            pdfs_dir=pdfs_dir,
        )
        logger.debug("StateBillRepository initialized | metadata_dir=%s", self._metadata_dir)

    def get_states_represented(self) -> list[str]:
        """Return a sorted list of unique State names present in this repository."""
        states = {b.state for b in self.get_all() if b.state}
        return sorted(states)

    def count_by_state(self, state: str) -> int:
        """Return the count of bills for a given state."""
        return len(self.get_by_state(state))

    def __repr__(self) -> str:
        return f"<StateBillRepository metadata_dir={self._metadata_dir!r} count={self.count()}>"
