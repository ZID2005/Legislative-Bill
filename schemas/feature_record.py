"""
schemas/feature_record.py
=========================
Canonical data model for one row in the unified ML feature dataset.

Each ``FeatureRecord`` represents a single **Bill × Company × Event-Window**
observation and contains every feature group required for downstream NLP
embedding and machine-learning model training.

Feature Groups
--------------
1. Legislative Features  — from Bill + KnowledgeRecord
2. Company Features      — from Company
3. Financial Features    — from MarketModelRecord
4. Event Study Features  — from EventStudyRecord
5. Statistical Features  — from StatisticalResult
6. Target Labels         — from LabelRecord

Design
------
* Pure Python dataclass (no external dependencies) so it is importable
  everywhere without optional-dependency guards.
* ``to_dict()`` / ``from_dict()`` enable Parquet/CSV round-trips via pandas.
* ``record_id`` is the deterministic composite key:
  ``{bill_id}|{company_isin}|{event_window}``
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Composite key helper
# ---------------------------------------------------------------------------


def make_record_id(bill_id: str, company_isin: str, event_window: str) -> str:
    """Return the deterministic composite key for a FeatureRecord."""
    return f"{bill_id}|{company_isin}|{event_window}"


# ---------------------------------------------------------------------------
# FeatureRecord
# ---------------------------------------------------------------------------


@dataclass
class FeatureRecord:
    """
    Unified ML feature record for a (Bill × Company × Event-Window) triple.

    Attributes
    ----------
    record_id : str
        Composite primary key: ``{bill_id}|{company_isin}|{event_window}``.

    --- Legislative Features ---
    bill_id : str
    bill_title : str
    bill_type : str
    ministry : str
    department : str
    policy_domain : str
    economic_domain : str
    primary_sector : str
    secondary_sectors : list[str]
    regulatory_authority : str
    geographic_scope : str
    introduction_date : str | None   ISO-8601 date string or None

    --- Company Features ---
    company_name : str
    nse_symbol : str
    isin : str
    company_sector : str
    industry : str
    sub_industry : str
    market_cap_category : str
    hq_state : str

    --- Financial Features (Market Model) ---
    alpha : float | None
    beta : float | None
    r_squared : float | None
    residual_variance : float | None
    observation_count : int | None

    --- Event Study Features ---
    event_window : str
    final_car : float | None
    avg_ar : float | None
    max_ar : float | None
    min_ar : float | None
    peak_ar_day : int | None
    peak_car_day : int | None

    --- Statistical Features ---
    t_statistic : float | None
    p_value : float | None
    confidence_interval_lower : float | None
    confidence_interval_upper : float | None
    significance_level : str | None
    significant_flag : bool | None
    effect_size : str | None

    --- Target Labels ---
    direction : str | None             POSITIVE / NEGATIVE / NEUTRAL
    market_moving : bool | None
    impact_strength : str | None       LOW / MEDIUM / HIGH / VERY_HIGH
    confidence_label : str | None      HIGH / MEDIUM / LOW

    --- Provenance ---
    feature_version : str              Schema version for drift detection
    built_at : str                     ISO-8601 UTC timestamp of record creation
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    record_id: str
    bill_id: str
    company_isin: str  # also stored separately for easy access
    event_window: str

    # ------------------------------------------------------------------
    # Legislative Features
    # ------------------------------------------------------------------
    bill_title: str = ""
    bill_type: str = ""
    ministry: str = ""
    department: str = ""
    policy_domain: str = ""
    economic_domain: str = ""
    primary_sector: str = ""
    secondary_sectors: list[str] = field(default_factory=list)
    regulatory_authority: str = ""
    geographic_scope: str = ""
    introduction_date: Optional[str] = None  # ISO-8601 or None

    # ------------------------------------------------------------------
    # Company Features
    # ------------------------------------------------------------------
    company_name: str = ""
    nse_symbol: str = ""
    isin: str = ""
    company_sector: str = ""
    industry: str = ""
    sub_industry: str = ""
    market_cap_category: str = ""
    hq_state: str = ""

    # ------------------------------------------------------------------
    # Financial Features (from Market Model)
    # ------------------------------------------------------------------
    alpha: Optional[float] = None
    beta: Optional[float] = None
    r_squared: Optional[float] = None
    residual_variance: Optional[float] = None
    observation_count: Optional[int] = None

    # ------------------------------------------------------------------
    # Event Study Features
    # ------------------------------------------------------------------
    final_car: Optional[float] = None
    avg_ar: Optional[float] = None
    max_ar: Optional[float] = None
    min_ar: Optional[float] = None
    peak_ar_day: Optional[int] = None
    peak_car_day: Optional[int] = None

    # ------------------------------------------------------------------
    # Statistical Features
    # ------------------------------------------------------------------
    t_statistic: Optional[float] = None
    p_value: Optional[float] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    significance_level: Optional[str] = None
    significant_flag: Optional[bool] = None
    effect_size: Optional[str] = None

    # ------------------------------------------------------------------
    # Target Labels
    # ------------------------------------------------------------------
    direction: Optional[str] = None          # POSITIVE / NEGATIVE / NEUTRAL
    market_moving: Optional[bool] = None
    impact_strength: Optional[str] = None    # LOW / MEDIUM / HIGH / VERY_HIGH
    confidence_label: Optional[str] = None   # HIGH / MEDIUM / LOW

    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------
    feature_version: str = "1.0"
    built_at: str = ""

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON/Parquet-compatible flat dictionary."""
        return {
            "record_id": self.record_id,
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "event_window": self.event_window,
            # Legislative
            "bill_title": self.bill_title,
            "bill_type": self.bill_type,
            "ministry": self.ministry,
            "department": self.department,
            "policy_domain": self.policy_domain,
            "economic_domain": self.economic_domain,
            "primary_sector": self.primary_sector,
            "secondary_sectors": self.secondary_sectors,
            "regulatory_authority": self.regulatory_authority,
            "geographic_scope": self.geographic_scope,
            "introduction_date": self.introduction_date,
            # Company
            "company_name": self.company_name,
            "nse_symbol": self.nse_symbol,
            "isin": self.isin,
            "company_sector": self.company_sector,
            "industry": self.industry,
            "sub_industry": self.sub_industry,
            "market_cap_category": self.market_cap_category,
            "hq_state": self.hq_state,
            # Financial
            "alpha": self.alpha,
            "beta": self.beta,
            "r_squared": self.r_squared,
            "residual_variance": self.residual_variance,
            "observation_count": self.observation_count,
            # Event Study
            "final_car": self.final_car,
            "avg_ar": self.avg_ar,
            "max_ar": self.max_ar,
            "min_ar": self.min_ar,
            "peak_ar_day": self.peak_ar_day,
            "peak_car_day": self.peak_car_day,
            # Statistical
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "confidence_interval_lower": self.confidence_interval_lower,
            "confidence_interval_upper": self.confidence_interval_upper,
            "significance_level": self.significance_level,
            "significant_flag": self.significant_flag,
            "effect_size": self.effect_size,
            # Labels
            "direction": self.direction,
            "market_moving": self.market_moving,
            "impact_strength": self.impact_strength,
            "confidence_label": self.confidence_label,
            # Provenance
            "feature_version": self.feature_version,
            "built_at": self.built_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeatureRecord":
        """Deserialise a FeatureRecord from a flat dictionary."""

        def _opt_float(v: Any) -> Optional[float]:
            if v is None:
                return None
            try:
                f = float(v)
                import math
                return None if math.isnan(f) else f
            except (TypeError, ValueError):
                return None

        def _opt_int(v: Any) -> Optional[int]:
            if v is None:
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return None

        def _opt_bool(v: Any) -> Optional[bool]:
            if v is None:
                return None
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.strip().lower() in {"true", "1", "yes"}
            try:
                return bool(int(v))
            except (TypeError, ValueError):
                return None

        secondary_raw = data.get("secondary_sectors", [])
        if isinstance(secondary_raw, str):
            # Handle Parquet round-trip where lists become JSON strings
            import json
            try:
                secondary_raw = json.loads(secondary_raw)
            except Exception:
                secondary_raw = []

        return cls(
            record_id=data["record_id"],
            bill_id=data["bill_id"],
            company_isin=data["company_isin"],
            event_window=data["event_window"],
            # Legislative
            bill_title=data.get("bill_title", ""),
            bill_type=data.get("bill_type", ""),
            ministry=data.get("ministry", ""),
            department=data.get("department", ""),
            policy_domain=data.get("policy_domain", ""),
            economic_domain=data.get("economic_domain", ""),
            primary_sector=data.get("primary_sector", ""),
            secondary_sectors=secondary_raw if isinstance(secondary_raw, list) else [],
            regulatory_authority=data.get("regulatory_authority", ""),
            geographic_scope=data.get("geographic_scope", ""),
            introduction_date=data.get("introduction_date"),
            # Company
            company_name=data.get("company_name", ""),
            nse_symbol=data.get("nse_symbol", ""),
            isin=data.get("isin", ""),
            company_sector=data.get("company_sector", ""),
            industry=data.get("industry", ""),
            sub_industry=data.get("sub_industry", ""),
            market_cap_category=data.get("market_cap_category", ""),
            hq_state=data.get("hq_state", ""),
            # Financial
            alpha=_opt_float(data.get("alpha")),
            beta=_opt_float(data.get("beta")),
            r_squared=_opt_float(data.get("r_squared")),
            residual_variance=_opt_float(data.get("residual_variance")),
            observation_count=_opt_int(data.get("observation_count")),
            # Event Study
            final_car=_opt_float(data.get("final_car")),
            avg_ar=_opt_float(data.get("avg_ar")),
            max_ar=_opt_float(data.get("max_ar")),
            min_ar=_opt_float(data.get("min_ar")),
            peak_ar_day=_opt_int(data.get("peak_ar_day")),
            peak_car_day=_opt_int(data.get("peak_car_day")),
            # Statistical
            t_statistic=_opt_float(data.get("t_statistic")),
            p_value=_opt_float(data.get("p_value")),
            confidence_interval_lower=_opt_float(data.get("confidence_interval_lower")),
            confidence_interval_upper=_opt_float(data.get("confidence_interval_upper")),
            significance_level=data.get("significance_level"),
            significant_flag=_opt_bool(data.get("significant_flag")),
            effect_size=data.get("effect_size"),
            # Labels
            direction=data.get("direction"),
            market_moving=_opt_bool(data.get("market_moving")),
            impact_strength=data.get("impact_strength"),
            confidence_label=data.get("confidence_label"),
            # Provenance
            feature_version=data.get("feature_version", "1.0"),
            built_at=data.get("built_at", ""),
        )

    def has_labels(self) -> bool:
        """Return True if all four target labels are populated."""
        return all([
            self.direction is not None,
            self.market_moving is not None,
            self.impact_strength is not None,
            self.confidence_label is not None,
        ])

    def has_financial_features(self) -> bool:
        """Return True if market-model features are present."""
        return all([
            self.alpha is not None,
            self.beta is not None,
            self.r_squared is not None,
        ])

    def has_event_study_features(self) -> bool:
        """Return True if event-study features are present."""
        return self.final_car is not None

    def has_statistical_features(self) -> bool:
        """Return True if statistical significance features are present."""
        return all([
            self.t_statistic is not None,
            self.p_value is not None,
        ])

    def __repr__(self) -> str:
        return (
            f"<FeatureRecord bill={self.bill_id!r} "
            f"isin={self.company_isin!r} "
            f"window={self.event_window!r} "
            f"direction={self.direction!r}>"
        )
