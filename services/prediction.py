"""
services/prediction.py
======================
Orchestration service for running model predictions and impact assessments.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from config.logging_config import get_logger
from schemas.prediction import ImpactLabel, Prediction, CompanyImpact
from storage.bill_repository import BillRepository

logger = get_logger(__name__)


class PredictionService:
    """
    Coordinates feature generation and runs model inference to predict bill market impact.
    """

    def __init__(self, bill_repository: Optional[BillRepository] = None) -> None:
        """
        Initialize the prediction service.
        """
        self.bill_repo = bill_repository or BillRepository()

    def predict_impact(self, bill_id: str, company_isin: str) -> Prediction:
        """
        Predict impact of a legislative bill on a specific listed company.

        Parameters
        ----------
        bill_id : str
            Unique bill ID slug.
        company_isin : str
            Target company ISIN code.

        Returns
        -------
        Prediction
            canonical Prediction schema object.
        """
        logger.info("PredictionService: predicting impact for bill=%s | company=%s", bill_id, company_isin)
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
