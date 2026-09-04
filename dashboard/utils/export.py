"""
dashboard/utils/export.py
=========================
Export utilities for tabular decision data and reports (CSV, JSON).
"""

from __future__ import annotations

import json
from typing import Any, Optional
import pandas as pd


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a pandas DataFrame to CSV bytes for file download."""
    return df.to_csv(index=False).encode("utf-8")


def to_json_bytes(data: dict[str, Any] | list[Any]) -> bytes:
    """Convert a dictionary or list to formatted JSON bytes for download."""
    return json.dumps(data, indent=2, default=str).encode("utf-8")
