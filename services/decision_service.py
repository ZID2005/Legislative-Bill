"""
services/decision_service.py
============================
Service layer orchestrator for Task 7.2 — Decision Support & Risk Scoring Engine.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from decision_support.engine import DecisionSupportEngine
from schemas.decision import DecisionSupportRecord, DecisionValidationReport
from storage.decision_repository import DecisionRepository

logger = get_logger(__name__)


class DecisionSupportService:
    """
    Service coordinating execution of decision-support and composite risk-scoring workflows.
    """

    def __init__(
        self,
        engine: Optional[DecisionSupportEngine] = None,
        repository: Optional[DecisionRepository] = None,
    ) -> None:
        self.engine = engine or DecisionSupportEngine()
        self.repository = repository or DecisionRepository()

    def generate_decision_support(
        self,
        bill_id: Optional[str] = None,
        company_isin: Optional[str] = None,
        year: Optional[int] = None,
        event_window: Optional[str] = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Execute decision-support generation across matching predictions.

        Parameters
        ----------
        bill_id : str, optional
        company_isin : str, optional
        year : int, optional
        event_window : str, optional
        force_refresh : bool

        Returns
        -------
        dict[str, Any]
            Execution statistics and decision support records.
        """
        logger.info(
            "DecisionSupportService: generating decision support | bill=%s isin=%s year=%s window=%s force=%s",
            bill_id,
            company_isin,
            year,
            event_window,
            force_refresh,
        )
        return self.engine.run_all(
            bill_id_filter=bill_id,
            company_isin_filter=company_isin,
            year_filter=year,
            event_window_filter=event_window,
            force_refresh=force_refresh,
        )

    def get_decision(self, decision_id: str) -> Optional[DecisionSupportRecord]:
        """Retrieve a specific decision support record by ID."""
        return self.repository.get(decision_id)

    def get_decisions_for_bill(self, bill_id: str) -> list[DecisionSupportRecord]:
        """Retrieve all persisted decision support records for a bill."""
        return self.repository.get_by_bill(bill_id)

    def get_decisions_for_company(self, company_isin: str) -> list[DecisionSupportRecord]:
        """Retrieve all persisted decision support records for a company."""
        return self.repository.get_by_company(company_isin)

    def get_all_decisions(self) -> list[DecisionSupportRecord]:
        """Retrieve all stored decision support records."""
        return self.repository.load_all()
