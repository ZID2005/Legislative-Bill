"""
services/reporting_service.py
==============================
Thin service façade over ReportingEngine (Task 7.3).

Provides a clean API surface for CLI commands and future integrations
without exposing internal engine wiring.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from reporting.engine import ReportingEngine
from schemas.report import BillLevelReport, CompanyLevelReport, ReportFormat, StakeholderReport

logger = get_logger(__name__)


class ReportingService:
    """
    Service layer wrapping ReportingEngine for stakeholder report generation.

    Parameters
    ----------
    engine : ReportingEngine, optional
        Pre-configured engine. Created automatically if not provided.
    """

    def __init__(self, engine: Optional[ReportingEngine] = None) -> None:
        self._engine = engine or ReportingEngine()
        logger.debug("ReportingService initialised.")

    def generate_reports(
        self,
        bill_id: Optional[str] = None,
        company_isin: Optional[str] = None,
        stakeholder: Optional[str] = None,
        event_window: Optional[str] = None,
        output_format: str = ReportFormat.JSON.value,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Generate stakeholder reports matching the given filters.

        Parameters
        ----------
        bill_id : str, optional
        company_isin : str, optional
        stakeholder : str, optional
            INVESTOR / BUSINESS / PUBLIC
        event_window : str, optional
        output_format : str
        force_refresh : bool

        Returns
        -------
        dict — execution statistics and list of generated reports
        """
        logger.info(
            "ReportingService.generate_reports: bill=%s company=%s stakeholder=%s format=%s",
            bill_id, company_isin, stakeholder, output_format,
        )
        return self._engine.generate_all(
            bill_id_filter=bill_id,
            company_isin_filter=company_isin,
            stakeholder_filter=stakeholder,
            event_window_filter=event_window,
            output_format=output_format,
            force_refresh=force_refresh,
        )

    def generate_bill_report(
        self,
        bill_id: str,
        event_window: str = "",
        output_format: str = ReportFormat.JSON.value,
    ) -> BillLevelReport:
        """Generate a bill-level aggregation report."""
        return self._engine.generate_bill_report(bill_id, event_window, output_format)

    def generate_company_report(
        self,
        company_isin: str,
        output_format: str = ReportFormat.JSON.value,
    ) -> CompanyLevelReport:
        """Generate a company-level aggregation report."""
        return self._engine.generate_company_report(company_isin, output_format)

    def format_report(self, report: Any, output_format: str) -> str:
        """Format any report object to string."""
        return self._engine.format_report(report, output_format)
