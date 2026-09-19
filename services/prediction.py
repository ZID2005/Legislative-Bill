"""
services/prediction.py
======================
Service layer orchestrator for Task 7.1 — Final Prediction & Decision Engine.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from prediction.engine import FinalPredictionEngine
from schemas.prediction import PredictionRecord, PredictionValidationReport
from storage.prediction_repository import PredictionRepository

logger = get_logger(__name__)


class PredictionService:
    """
    Service coordinating execution of forward-looking predictions and decision-support generation.
    """

    def __init__(
        self,
        engine: Optional[FinalPredictionEngine] = None,
        repository: Optional[PredictionRepository] = None,
        bill_repository: Optional[Any] = None,
    ) -> None:
        self._engine = engine
        self._repository = repository
        if bill_repository is not None:
            self.bill_repo = bill_repository
        else:
            from storage.bill_repository import BillRepository
            self.bill_repo = BillRepository()

    @property
    def engine(self) -> FinalPredictionEngine:
        if self._engine is None:
            self._engine = FinalPredictionEngine()
        return self._engine

    @property
    def repository(self) -> PredictionRepository:
        if self._repository is None:
            self._repository = PredictionRepository()
        return self._repository


    def predict_impact(self, bill_id: str, company_isin: str) -> Any:
        """
        Legacy method preserved for backward compatibility (Task 1 Service Layer).
        """
        from datetime import datetime, timezone
        from schemas.prediction import CompanyImpact, ImpactLabel, Prediction

        bill = self.bill_repo.get(bill_id)
        if not bill:
            raise ValueError(f"Bill not found in repository: {bill_id}")

        company_impact = CompanyImpact(
            isin=company_isin,
            ticker="MOCK",
            company_name="Mock Company",
            sector="Mock Sector",
            impact_label=ImpactLabel.NEUTRAL,
            confidence=0.5,
            car_predicted=0.0,
            top_features=["bill_length"],
        )

        return Prediction(
            bill_id=bill_id,
            model_version="1.0-stub",
            predicted_at=datetime.now(tz=timezone.utc),
            companies=[company_impact],
            overall_impact=ImpactLabel.NEUTRAL,
        )


    def generate_predictions(
        self,
        bill_id: Optional[str] = None,
        company_isin: Optional[str] = None,
        year: Optional[int] = None,
        event_window: Optional[str] = None,
        force_refresh: bool = False,
        mode: str = "structured",
    ) -> dict[str, Any]:
        """
        Execute prediction pipeline across matching bills and companies.

        Parameters
        ----------
        bill_id : str, optional
        company_isin : str, optional
        year : int, optional
        event_window : str, optional
        force_refresh : bool
        mode : str

        Returns
        -------
        dict[str, Any]
            Execution statistics and prediction records.
        """
        logger.info(
            "PredictionService: generating predictions | bill=%s isin=%s year=%s window=%s force=%s mode=%s",
            bill_id,
            company_isin,
            year,
            event_window,
            force_refresh,
            mode,
        )
        return self.engine.run_all(
            bill_id_filter=bill_id,
            company_isin_filter=company_isin,
            year_filter=year,
            event_window_filter=event_window,
            force_refresh=force_refresh,
            feature_mode=mode,
        )

    def predict_observation(
        self,
        feature_dict: dict[str, Any],
        force_refresh: bool = False,
    ) -> tuple[Optional[PredictionRecord], Optional[PredictionValidationReport]]:
        """
        Generate prediction for a single feature dictionary observation.
        """
        return self.engine.predict_observation(
            feature_dict=feature_dict,
            force_refresh=force_refresh,
        )

    def get_predictions_for_bill(self, bill_id: str) -> list[PredictionRecord]:
        """Retrieve all persisted predictions for a bill."""
        return self.repository.get_by_bill(bill_id)

    def get_predictions_for_company(self, company_isin: str) -> list[PredictionRecord]:
        """Retrieve all persisted predictions for a company."""
        return self.repository.get_by_company(company_isin)

    def get_all_predictions(self) -> list[PredictionRecord]:
        """Retrieve all stored predictions."""
        return self.repository.load_all()
