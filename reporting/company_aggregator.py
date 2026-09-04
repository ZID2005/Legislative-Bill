"""
reporting/company_aggregator.py
================================
Company-level aggregation of DecisionSupportRecords (Task 7.3).

Produces CompanyLevelReport objects that show all legislation
potentially affecting a specific company.

Supports:
- Company → Bills view (all bills affecting a company ISIN)
- Bill → Company view (single company filtered from a bill's records)

Aggregation Formulas (Documented)
----------------------------------
- total_bills        : count of unique bill_ids in the input records
- positive_bill_count: count where predicted_direction == "POSITIVE"
- negative_bill_count: count where predicted_direction == "NEGATIVE"
- neutral_bill_count : count where predicted_direction == "NEUTRAL"
- avg_impact_score   : arithmetic mean of impact_score values
                       Formula: sum(r.impact_score for r) / len(records)
- avg_risk_score     : arithmetic mean of risk_score values
                       Formula: sum(r.risk_score for r) / len(records)
- high_impact_bills  : list of bill_ids where impact_category in {"HIGH", "VERY_HIGH"}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.company import Company
from schemas.decision import DecisionSupportRecord
from schemas.report import (
    REPORT_DISCLAIMER,
    REPORT_METHODOLOGY_NOTE,
    REPORT_VERSION,
    CompanyLevelReport,
    make_company_report_id,
)

logger = get_logger(__name__)

_HIGH_IMPACT_CATEGORIES = frozenset({"HIGH", "VERY_HIGH"})


class CompanyAggregator:
    """
    Aggregates multiple DecisionSupportRecords for a single company
    into a CompanyLevelReport.

    Parameters
    ----------
    report_version : str
    """

    def __init__(self, report_version: str = REPORT_VERSION) -> None:
        self._report_version = report_version

    def build(
        self,
        company_isin: str,
        records: list[DecisionSupportRecord],
        company: Optional[Company] = None,
    ) -> CompanyLevelReport:
        """
        Build a CompanyLevelReport from a list of DecisionSupportRecords
        for a single company ISIN.

        Parameters
        ----------
        company_isin : str
        records : list[DecisionSupportRecord]
            All decision records for this company (across bills).
        company : Company, optional

        Returns
        -------
        CompanyLevelReport
        """
        if not records:
            logger.warning(
                "CompanyAggregator.build called with empty records for company_isin=%s",
                company_isin,
            )
            return self._empty_report(company_isin, company)

        # Filter to this company (defensive)
        filtered = [r for r in records if r.company_isin == company_isin]
        if not filtered:
            filtered = records

        # --- Aggregation formulas ---
        unique_bills = list(dict.fromkeys(r.bill_id for r in filtered))
        total_bills = len(unique_bills)

        positive_bill_count = sum(
            1 for r in filtered if r.predicted_direction.upper() == "POSITIVE"
        )
        negative_bill_count = sum(
            1 for r in filtered if r.predicted_direction.upper() == "NEGATIVE"
        )
        neutral_bill_count = sum(
            1 for r in filtered if r.predicted_direction.upper() == "NEUTRAL"
        )

        n = len(filtered)
        avg_impact_score = sum(r.impact_score for r in filtered) / n
        avg_risk_score = sum(r.risk_score for r in filtered) / n

        high_impact_bills = sorted(
            {
                r.bill_id
                for r in filtered
                if r.impact_category.upper() in _HIGH_IMPACT_CATEGORIES
            }
        )

        # Per-bill summary rows
        bill_summaries = self._build_bill_summaries(filtered)

        # Company metadata
        company_name = (company.company_name if company else None) or ""
        company_sector = (company.sector if company else None) or ""

        return CompanyLevelReport(
            report_id=make_company_report_id(company_isin),
            company_isin=company_isin,
            company_name=company_name,
            company_sector=company_sector,
            generated_timestamp=datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            report_version=self._report_version,
            total_bills=total_bills,
            positive_bill_count=positive_bill_count,
            negative_bill_count=negative_bill_count,
            neutral_bill_count=neutral_bill_count,
            avg_impact_score=avg_impact_score,
            avg_risk_score=avg_risk_score,
            bill_summaries=bill_summaries,
            high_impact_bills=high_impact_bills,
            methodology_note=REPORT_METHODOLOGY_NOTE,
            disclaimer=REPORT_DISCLAIMER,
        )

    def _build_bill_summaries(
        self, records: list[DecisionSupportRecord]
    ) -> list[dict[str, Any]]:
        """Build per-bill summary rows for the company-level report."""
        summaries = []
        for r in records:
            summaries.append(
                {
                    "bill_id": r.bill_id,
                    "event_window": r.event_window,
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
                    "confidence_level": r.predicted_confidence,
                    "decision_version": r.decision_version,
                }
            )
        return summaries

    def _empty_report(
        self, company_isin: str, company: Optional[Company]
    ) -> CompanyLevelReport:
        """Return a zero-count CompanyLevelReport when no records are available."""
        return CompanyLevelReport(
            report_id=make_company_report_id(company_isin),
            company_isin=company_isin,
            company_name=(company.company_name if company else None) or "",
            company_sector=(company.sector if company else None) or "",
            generated_timestamp=datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            report_version=self._report_version,
            total_bills=0,
            positive_bill_count=0,
            negative_bill_count=0,
            neutral_bill_count=0,
            avg_impact_score=0.0,
            avg_risk_score=0.0,
            bill_summaries=[],
            high_impact_bills=[],
            methodology_note=REPORT_METHODOLOGY_NOTE,
            disclaimer=REPORT_DISCLAIMER,
        )
