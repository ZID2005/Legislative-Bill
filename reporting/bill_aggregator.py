"""
reporting/bill_aggregator.py
=============================
Bill-level aggregation of DecisionSupportRecords (Task 7.3).

Produces a BillLevelReport summarising all companies affected by a single bill.

Aggregation Formulas (Documented)
----------------------------------
- total_companies     : count of unique company ISINs in the input records
- positive_count      : count where predicted_direction == "POSITIVE"
- negative_count      : count where predicted_direction == "NEGATIVE"
- neutral_count       : count where predicted_direction == "NEUTRAL"
- market_moving_count : count where market_moving_probability >= 0.50
- high_impact_count   : count where impact_category in {"HIGH", "VERY_HIGH"}
- avg_impact_score    : arithmetic mean of impact_score values
                        Formula: sum(impact_score for r in records) / len(records)
                        Note: NOT a probability average — this is an arithmetic mean
                        of the composite impact scores [0.0, 1.0].
- avg_risk_score      : arithmetic mean of risk_score values
                        Formula: sum(risk_score for r in records) / len(records)
                        Note: NOT a probability average.
- anticipation_distribution : {anticipation_class: count} frequency table
- risk_distribution         : {risk_category: count} frequency table
- sectors_affected          : sorted(list(set(record.sector for record in records if record.sector)))

Anti-aggregation Rules
-----------------------
- Probabilities (direction_probability, confidence_probability, etc.) are NOT
  averaged across records — averaging probability distributions yields
  statistically misleading results.
- Only scalar composite scores (impact_score, risk_score) and categorical
  counts are aggregated here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.decision import DecisionSupportRecord
from schemas.report import (
    REPORT_DISCLAIMER,
    REPORT_METHODOLOGY_NOTE,
    REPORT_VERSION,
    BillLevelReport,
    make_bill_report_id,
)

logger = get_logger(__name__)

_HIGH_IMPACT_CATEGORIES = frozenset({"HIGH", "VERY_HIGH"})
_MARKET_MOVING_THRESHOLD = 0.50


class BillAggregator:
    """
    Aggregates multiple DecisionSupportRecords for a single bill into a
    BillLevelReport.

    Parameters
    ----------
    report_version : str
    """

    def __init__(self, report_version: str = REPORT_VERSION) -> None:
        self._report_version = report_version

    def build(
        self,
        bill_id: str,
        records: list[DecisionSupportRecord],
        bill: Optional[Bill] = None,
        event_window: str = "",
    ) -> BillLevelReport:
        """
        Build a BillLevelReport from a list of DecisionSupportRecords
        for a single bill.

        Parameters
        ----------
        bill_id : str
        records : list[DecisionSupportRecord]
            All decision records for this bill (across companies).
        bill : Bill, optional
        event_window : str, optional
            If provided, filters records to this event window; if empty,
            uses the most frequent event window in records.

        Returns
        -------
        BillLevelReport
        """
        if not records:
            logger.warning("BillAggregator.build called with empty records for bill_id=%s", bill_id)
            return self._empty_report(bill_id, bill, event_window)

        # If event_window filter specified, apply it
        if event_window:
            filtered = [r for r in records if r.event_window == event_window]
            if not filtered:
                logger.warning(
                    "No records match event_window=%s for bill_id=%s; using all records.",
                    event_window, bill_id,
                )
                filtered = records
        else:
            # Use the most frequent event window
            window_counts: dict[str, int] = {}
            for r in records:
                window_counts[r.event_window] = window_counts.get(r.event_window, 0) + 1
            event_window = max(window_counts, key=window_counts.__getitem__)
            filtered = [r for r in records if r.event_window == event_window]

        # --- Aggregation formulas ---
        unique_isins = list(dict.fromkeys(r.company_isin for r in filtered))
        total_companies = len(unique_isins)

        # Direction counts
        positive_count = sum(1 for r in filtered if r.predicted_direction.upper() == "POSITIVE")
        negative_count = sum(1 for r in filtered if r.predicted_direction.upper() == "NEGATIVE")
        neutral_count = sum(1 for r in filtered if r.predicted_direction.upper() == "NEUTRAL")

        # Market-moving count: market_moving_probability >= 0.50
        market_moving_count = sum(
            1 for r in filtered if r.market_moving_probability >= _MARKET_MOVING_THRESHOLD
        )

        # High impact count: impact_category in {"HIGH", "VERY_HIGH"}
        high_impact_count = sum(
            1 for r in filtered
            if r.impact_category.upper() in _HIGH_IMPACT_CATEGORIES
        )

        # Arithmetic mean of scalar composite scores (NOT probability averages)
        n = len(filtered)
        avg_impact_score = sum(r.impact_score for r in filtered) / n
        avg_risk_score = sum(r.risk_score for r in filtered) / n

        # Frequency distributions
        anticipation_distribution: dict[str, int] = {}
        for r in filtered:
            key = r.anticipation_class
            anticipation_distribution[key] = anticipation_distribution.get(key, 0) + 1

        risk_distribution: dict[str, int] = {}
        for r in filtered:
            key = r.risk_category
            risk_distribution[key] = risk_distribution.get(key, 0) + 1

        # Sectors: sorted unique list of non-empty sector values
        sectors_affected = sorted(
            {r.sector for r in filtered if r.sector and r.sector.strip()}
        )

        # Per-company summary rows
        company_summaries = self._build_company_summaries(filtered)

        # Bill metadata
        bill_title = (bill.title if bill else None) or bill_id
        bill_ministry = (bill.ministry if bill else None) or ""
        bill_year = (bill.year if bill else None)

        return BillLevelReport(
            report_id=make_bill_report_id(bill_id),
            bill_id=bill_id,
            bill_title=bill_title,
            bill_ministry=bill_ministry,
            bill_year=bill_year,
            event_window=event_window,
            generated_timestamp=datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            report_version=self._report_version,
            total_companies=total_companies,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            market_moving_count=market_moving_count,
            high_impact_count=high_impact_count,
            avg_impact_score=avg_impact_score,
            avg_risk_score=avg_risk_score,
            anticipation_distribution=anticipation_distribution,
            risk_distribution=risk_distribution,
            sectors_affected=sectors_affected,
            company_summaries=company_summaries,
            methodology_note=REPORT_METHODOLOGY_NOTE,
            disclaimer=REPORT_DISCLAIMER,
        )

    def _build_company_summaries(
        self, records: list[DecisionSupportRecord]
    ) -> list[dict[str, Any]]:
        """Build per-company summary rows for the bill-level report."""
        summaries = []
        for r in records:
            summaries.append(
                {
                    "company_isin": r.company_isin,
                    "company_name": r.company_name or r.company_isin,
                    "company_symbol": r.company_symbol or "",
                    "sector": r.sector or "",
                    "predicted_direction": r.predicted_direction,
                    "direction_probability": r.direction_probability.get(
                        r.predicted_direction.upper(), 0.0
                    ),
                    "market_moving_probability": r.market_moving_probability,
                    "impact_score": round(r.impact_score, 4),
                    "impact_category": r.impact_category,
                    "risk_score": round(r.risk_score, 4),
                    "risk_category": r.risk_category,
                    "anticipation_class": r.anticipation_class,
                    "anticipation_score": round(r.anticipation_score, 4),
                    "confidence_level": r.predicted_confidence,
                }
            )
        return summaries

    def _empty_report(
        self, bill_id: str, bill: Optional[Bill], event_window: str
    ) -> BillLevelReport:
        """Return a zero-count BillLevelReport when no records are available."""
        return BillLevelReport(
            report_id=make_bill_report_id(bill_id),
            bill_id=bill_id,
            bill_title=(bill.title if bill else None) or bill_id,
            bill_ministry=(bill.ministry if bill else None) or "",
            bill_year=(bill.year if bill else None),
            event_window=event_window,
            generated_timestamp=datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            report_version=self._report_version,
            total_companies=0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            market_moving_count=0,
            high_impact_count=0,
            avg_impact_score=0.0,
            avg_risk_score=0.0,
            anticipation_distribution={},
            risk_distribution={},
            sectors_affected=[],
            company_summaries=[],
            methodology_note=REPORT_METHODOLOGY_NOTE,
            disclaimer=REPORT_DISCLAIMER,
        )
