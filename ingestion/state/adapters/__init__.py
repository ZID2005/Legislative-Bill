"""
ingestion/state/adapters package
================================
State-specific ingestion adapters for official Indian State legislature portals.
"""

from ingestion.state.adapters.andhra_pradesh import AndhraPradeshSourceAdapter
from ingestion.state.adapters.karnataka import KarnatakaSourceAdapter
from ingestion.state.adapters.kerala import KeralaSourceAdapter
from ingestion.state.adapters.telangana import TelanganaSourceAdapter

__all__ = [
    "AndhraPradeshSourceAdapter",
    "KarnatakaSourceAdapter",
    "KeralaSourceAdapter",
    "TelanganaSourceAdapter",
]

