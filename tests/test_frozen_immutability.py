"""
tests/test_frozen_immutability.py
=================================
Unit tests for Task 8.17 Frozen Dataset Protection and Immutability Safeguards.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from schemas.anticipation import AnticipationScore
from schemas.decision import DecisionSupportRecord
from schemas.prediction import PredictionRecord
from schemas.report import StakeholderReport, StakeholderType
from storage.anticipation_repository import AnticipationRepository
from storage.decision_repository import DecisionRepository
from storage.exceptions import FrozenDatasetImmutableError
from storage.prediction_repository import PredictionRepository
from storage.report_repository import ReportRepository


@pytest.fixture
def sample_prediction() -> PredictionRecord:
    return PredictionRecord(
        prediction_id="pred_test",
        bill_id="finance-act-2024",
        company_isin="INE002A01018",
        company_name="Reliance Industries",
        company_symbol="RELIANCE",
        event_window="[-20,+20]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.85, "NEGATIVE": 0.05, "NEUTRAL": 0.10},
        predicted_market_moving=True,
        market_moving_probability=0.88,
        predicted_impact_strength="HIGH",
        impact_probabilities={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.70, "VERY_HIGH": 0.10},
        predicted_confidence="HIGH",
        confidence_probability={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80},
        anticipation_class="STRONG_EVIDENCE",
        anticipation_score=0.82,
        model_name={"direction": "lgbm", "market_moving": "random_forest"},
        model_version="v1.0",
        feature_version="v1.0",
        prediction_timestamp="2026-08-16T12:00:00Z",
        decision_reason="Positive impact with high confidence.",
        expected_impact_estimate="Expected positive return [+3%, +6%]",
        risk_indicators=["High pre-event market run-up"],
        model_confidence=0.82,
        data_quality_status="VALID",
    )


@pytest.fixture
def sample_decision() -> DecisionSupportRecord:
    return DecisionSupportRecord(
        decision_id="dec_test",
        bill_id="finance-act-2024",
        company_isin="INE002A01018",
        event_window="[-20,+20]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.85, "NEGATIVE": 0.05, "NEUTRAL": 0.10},
        market_moving_probability=0.88,
        predicted_impact_strength="HIGH",
        confidence_probability={"LOW": 0.1, "MEDIUM": 0.2, "HIGH": 0.7},
        anticipation_class="STRONG_EVIDENCE",
        anticipation_score=0.82,
        impact_score=0.85,
        risk_score=0.35,
        risk_category="MODERATE",
        pricing_in_risk="LOW",
        investor_summary="Summary",
        business_summary="Summary",
        public_summary="Summary",
        decision_reason="Rationale",
        model_version="v1.0",
        feature_version="v1.0",
    )


@pytest.fixture
def sample_anticipation() -> AnticipationScore:
    from config.settings import settings
    from utils.file_utils import load_json
    first_ant_file = next((settings.ANTICIPATION_DIR / "scores").glob("*.json"))
    return AnticipationScore.from_dict(load_json(first_ant_file))


@pytest.fixture
def sample_report() -> StakeholderReport:
    from config.settings import settings
    from utils.file_utils import load_json
    first_rep_file = next((settings.REPORTS_DIR / "investor").glob("*.json"))
    return StakeholderReport.from_dict(load_json(first_rep_file))


def test_prediction_repository_read_only_blocks_write(sample_prediction: PredictionRecord) -> None:
    repo = PredictionRepository(read_only=True)
    with pytest.raises(FrozenDatasetImmutableError):
        repo.save(sample_prediction)


def test_decision_repository_read_only_blocks_write(sample_decision: DecisionSupportRecord) -> None:
    repo = DecisionRepository(read_only=True)
    with pytest.raises(FrozenDatasetImmutableError):
        repo.save(sample_decision)


def test_anticipation_repository_read_only_blocks_write(sample_anticipation: AnticipationScore) -> None:
    repo = AnticipationRepository(read_only=True)
    with pytest.raises(FrozenDatasetImmutableError):
        repo.save_score(sample_anticipation)


def test_report_repository_read_only_blocks_write(sample_report: StakeholderReport) -> None:
    repo = ReportRepository(read_only=True)
    with pytest.raises(FrozenDatasetImmutableError):
        repo.save(sample_report)


def test_prediction_repository_writable_in_temp_dir(tmp_path: Path, sample_prediction: PredictionRecord) -> None:
    """Verify that test fixtures using custom temp directories can still write when read_only=False."""
    repo = PredictionRepository(predictions_dir=tmp_path, read_only=False)
    path = repo.save(sample_prediction)
    assert path.exists()
