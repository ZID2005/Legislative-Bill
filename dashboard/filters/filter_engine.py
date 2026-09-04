"""
dashboard/filters/filter_engine.py
==================================
Multi-dimensional filtering engine for the Decision-Support Dashboard.

Provides pure Python filtering capabilities over decision dataframes,
supporting combined or individual filters across:
- Bill ID / Title
- Company ISIN / Name / Ticker
- Sector
- Ministry
- Policy Domain
- Risk Category
- Predicted Direction
- Market-Moving Status
- Anticipation Evidence Category
- Event Window
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd


class FilterEngine:
    """
    Filtering engine operating on decision DataFrames.
    """

    @staticmethod
    def apply_filters(
        df: pd.DataFrame,
        bill_id: Optional[str | list[str]] = None,
        company_isin: Optional[str | list[str]] = None,
        sector: Optional[str | list[str]] = None,
        ministry: Optional[str | list[str]] = None,
        policy_domain: Optional[str | list[str]] = None,
        risk_category: Optional[str | list[str]] = None,
        direction: Optional[str | list[str]] = None,
        market_moving_only: Optional[bool] = None,
        anticipation_category: Optional[str | list[str]] = None,
        event_window: Optional[str | list[str]] = None,
    ) -> pd.DataFrame:
        """
        Apply criteria to filter a decision DataFrame.
        """
        if df.empty:
            return df.copy()

        filtered = df.copy()

        def _match(series: pd.Series, val: Any) -> pd.Series:
            if val is None or val == "All" or val == ["All"]:
                return pd.Series(True, index=series.index)
            if isinstance(val, (list, set, tuple)):
                if not val:
                    return pd.Series(True, index=series.index)
                return series.isin(val)
            return series == val

        if bill_id is not None:
            filtered = filtered[_match(filtered["bill_id"], bill_id)]

        if company_isin is not None:
            filtered = filtered[_match(filtered["company_isin"], company_isin)]

        if sector is not None and "sector" in filtered.columns:
            filtered = filtered[_match(filtered["sector"], sector)]

        if ministry is not None and "ministry" in filtered.columns:
            filtered = filtered[_match(filtered["ministry"], ministry)]

        if policy_domain is not None and "policy_domain" in filtered.columns:
            filtered = filtered[_match(filtered["policy_domain"], policy_domain)]

        if risk_category is not None:
            filtered = filtered[_match(filtered["risk_category"], risk_category)]

        if direction is not None:
            filtered = filtered[_match(filtered["predicted_direction"], direction)]

        if market_moving_only is True:
            filtered = filtered[filtered["market_moving_probability"] >= 0.50]
        elif market_moving_only is False:
            filtered = filtered[filtered["market_moving_probability"] < 0.50]

        if anticipation_category is not None:
            filtered = filtered[_match(filtered["anticipation_evidence"], anticipation_category)]

        if event_window is not None:
            filtered = filtered[_match(filtered["event_window"], event_window)]

        return filtered

    @staticmethod
    def get_filter_options(df: pd.DataFrame) -> dict[str, list[str]]:
        """
        Extract unique values for all available filter dimensions from the dataset.
        """
        if df.empty:
            return {
                "bills": [],
                "companies": [],
                "sectors": [],
                "ministries": [],
                "policy_domains": [],
                "risk_categories": [],
                "directions": [],
                "anticipation_tiers": [],
                "event_windows": [],
            }

        def _sorted_unique(col: str) -> list[str]:
            if col in df.columns:
                return sorted([str(x) for x in df[col].dropna().unique() if str(x) != "nan" and str(x) != ""])
            return []

        return {
            "bills": _sorted_unique("bill_id"),
            "companies": _sorted_unique("company_isin"),
            "sectors": _sorted_unique("sector"),
            "ministries": _sorted_unique("ministry"),
            "policy_domains": _sorted_unique("policy_domain"),
            "risk_categories": _sorted_unique("risk_category"),
            "directions": _sorted_unique("predicted_direction"),
            "anticipation_tiers": _sorted_unique("anticipation_evidence"),
            "event_windows": _sorted_unique("event_window"),
        }
