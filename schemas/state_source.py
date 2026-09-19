"""
schemas/state_source.py
=======================
Schema definition for Indian State legislative bill data sources.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from schemas.bill import BillHouse
from utils.state_normalizer import normalize_state


@dataclass
class StateBillSource:
    """
    Configuration descriptor for an official State legislative bill source.

    Parameters
    ----------
    state : str
        Canonical name of the Indian State (e.g. 'Andhra Pradesh', 'Karnataka').
    legislature : str
        Official name of the legislature (e.g. 'Andhra Pradesh Legislative Assembly').
    source_name : str
        Unique identifier for the source adapter/configuration (e.g. 'andhra_pradesh_assembly').
    base_url : str
        Root domain/base URL of the official source portal.
    listing_url : str
        URL of the bill listings or index page.
    detail_url_pattern : str | None
        URL template or pattern for accessing individual bill details.
    document_url_pattern : str | None
        URL pattern for downloading official bill PDFs.
    source_type : str
        Category of data source ('html_table', 'session_list', 'portal', 'api').
    house : BillHouse
        Chamber associated with this source (VIDHAN_SABHA, VIDHAN_PARISHAD, or UNKNOWN).
    active : bool
        Whether this source is currently enabled for ingestion.
    notes : str | None
        Operational notes, access restrictions, or coverage details.
    """

    state: str
    legislature: str
    source_name: str
    base_url: str
    listing_url: str
    detail_url_pattern: Optional[str] = None
    document_url_pattern: Optional[str] = None
    source_type: str = "html_table"
    house: BillHouse = BillHouse.VIDHAN_SABHA
    active: bool = True
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        """Coerce enum and normalize state."""
        norm = normalize_state(self.state)
        if norm:
            self.state = norm
        if isinstance(self.house, str):
            try:
                self.house = BillHouse(self.house.strip().lower())
            except ValueError:
                self.house = BillHouse.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        """Serialize source config to dictionary."""
        d = asdict(self)
        d["house"] = self.house.value if isinstance(self.house, BillHouse) else str(self.house)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateBillSource:
        """Instantiate StateBillSource from dictionary."""
        d = dict(data)
        if "house" in d and isinstance(d["house"], str):
            try:
                d["house"] = BillHouse(d["house"].strip().lower())
            except ValueError:
                d["house"] = BillHouse.UNKNOWN
        return cls(**d)
