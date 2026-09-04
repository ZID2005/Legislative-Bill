"""
services/anticipation_service.py
================================
Service layer orchestrator for Task 6.5 — Anticipation Bias / Pre-Event Information Analysis.
"""

from __future__ import annotations

from typing import Any, Optional
from config.logging_config import get_logger
from schemas.anticipation import AnticipationScore, BillAnticipationRecord
from anticipation.engine import AnticipationBiasEngine

logger = get_logger(__name__)


class AnticipationService:
    """
    Service coordinating execution of pre-event anticipation bias analysis.
    """

    def __init__(self, engine: Optional[AnticipationBiasEngine] = None) -> None:
        self.engine = engine or AnticipationBiasEngine()

    def run_analysis(
        self,
        year: Optional[int] = None,
        bill_id_filter: Optional[str] = None,
        company_isin_filter: Optional[str] = None,
        force_refresh: bool = False,
        skip_existing: bool = True,
    ) -> dict[str, Any]:
        """
        Execute anticipation bias analysis across matching models and bills.
        """
        logger.info(
            "AnticipationService executing analysis | year=%s bill=%s isin=%s force=%s",
            year,
            bill_id_filter,
            company_isin_filter,
            force_refresh,
        )
        return self.engine.run_all(
            year=year,
            bill_id_filter=bill_id_filter,
            company_isin_filter=company_isin_filter,
            force_refresh=force_refresh,
            skip_existing=skip_existing,
        )

    def get_bill_summary(self, bill_id: str) -> Optional[BillAnticipationRecord]:
        """
        Retrieve or compute bill-level anticipation record.
        """
        existing = self.engine.anticipation_repo.get_bill_score(bill_id)
        if existing:
            return existing
        bill_rec, rep = self.engine.analyze_bill(bill_id)
        return bill_rec
