"""
tests/test_prediction_repository.py
===================================
Unit tests for Task 7.1 PredictionRepository persistence layer.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from schemas.prediction import (
    PredictionRecord,
    PredictionValidationReport,
    make_prediction_id,
)
from storage.prediction_repository import PredictionRepository


@pytest.fixture
def temp_pred_repo(tmp_path: Path) -> PredictionRepository:
    return PredictionRepository(predictions_dir=tmp_path / "predictions")


@pytest.fixture
def sample_prediction() -> PredictionRecord:
    return PredictionRecord(
        prediction_id="",
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


class TestPredictionRepository:
    def test_save_and_get(
        self, temp_pred_repo: PredictionRepository, sample_prediction: PredictionRecord
    ) -> None:
        path = temp_pred_repo.save(sample_prediction)
        assert path.exists()

        loaded = temp_pred_repo.get(sample_prediction.prediction_id)
        assert loaded is not None
        assert loaded.bill_id == sample_prediction.bill_id
        assert loaded.company_isin == sample_prediction.company_isin
        assert loaded.predicted_direction == "POSITIVE"

    def test_get_by_key_and_exists(
        self, temp_pred_repo: PredictionRepository, sample_prediction: PredictionRecord
    ) -> None:
        assert not temp_pred_repo.exists("finance-act-2024", "INE002A01018", "[-20,+20]")
        temp_pred_repo.save(sample_prediction)
        assert temp_pred_repo.exists("finance-act-2024", "INE002A01018", "[-20,+20]")

        retrieved = temp_pred_repo.get_by_key("finance-act-2024", "INE002A01018", "[-20,+20]")
        assert retrieved is not None
        assert retrieved.prediction_id == sample_prediction.prediction_id

    def test_save_many_and_load_all(
        self, temp_pred_repo: PredictionRepository, sample_prediction: PredictionRecord
    ) -> None:
        p2 = PredictionRecord(
            prediction_id="",
            bill_id="finance-act-2024",
            company_isin="INE009A01021",
            company_name="Infosys",
            company_symbol="INFY",
            event_window="[-20,+20]",
            predicted_direction="NEUTRAL",
            direction_probability={"NEUTRAL": 0.9},
            predicted_market_moving=False,
            market_moving_probability=0.1,
            predicted_impact_strength="LOW",
            impact_probabilities={"LOW": 0.9},
            predicted_confidence="HIGH",
            confidence_probability={"HIGH": 0.9},
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.05,
            model_name={"direction": "lgbm"},
            model_version="v1.0",
            feature_version="v1.0",
            prediction_timestamp="2026-08-16T12:00:00Z",
            decision_reason="Neutral impact.",
        )

        p3 = PredictionRecord(
            prediction_id="",
            bill_id="telecom-bill-2023",
            company_isin="INE002A01018",
            company_name="Reliance Industries",
            company_symbol="RELIANCE",
            event_window="[-20,+20]",
            predicted_direction="NEGATIVE",
            direction_probability={"NEGATIVE": 0.8},
            predicted_market_moving=True,
            market_moving_probability=0.8,
            predicted_impact_strength="MEDIUM",
            impact_probabilities={"MEDIUM": 0.8},
            predicted_confidence="MEDIUM",
            confidence_probability={"MEDIUM": 0.8},
            anticipation_class="MODERATE_EVIDENCE",
            anticipation_score=0.6,
            model_name={"direction": "lgbm"},
            model_version="v1.0",
            feature_version="v1.0",
            prediction_timestamp="2026-08-16T12:00:00Z",
            decision_reason="Negative impact.",
        )

        saved = temp_pred_repo.save_many([sample_prediction, p2, p3])
        assert len(saved) == 3

        all_records = temp_pred_repo.load_all()
        assert len(all_records) == 3

        bill_records = temp_pred_repo.get_by_bill("finance-act-2024")
        assert len(bill_records) == 2

        comp_records = temp_pred_repo.get_by_company("INE002A01018")
        assert len(comp_records) == 2

    def test_validation_reports_persistence(
        self, temp_pred_repo: PredictionRepository
    ) -> None:
        rep = PredictionValidationReport(
            report_id="",
            bill_id="bill-1",
            company_isin="INE111",
            event_window="[-20,+20]",
            is_valid=False,
            errors=["Missing model for market_moving"],
            warnings=["High variance"],
            checks_performed={"model_avail": False},
        )
        saved_path = temp_pred_repo.save_validation_report(rep)
        assert saved_path.exists()

        all_reps = temp_pred_repo.load_validation_reports()
        assert len(all_reps) == 1
        assert all_reps[0].bill_id == "bill-1"
        assert all_reps[0].is_valid is False

    def test_clear(
        self, temp_pred_repo: PredictionRepository, sample_prediction: PredictionRecord
    ) -> None:
        temp_pred_repo.save(sample_prediction)
        rep = PredictionValidationReport(
            report_id="val_test",
            bill_id="bill-1",
            company_isin="INE111",
            event_window="[-20,+20]",
            is_valid=True,
        )
        temp_pred_repo.save_validation_report(rep)

        assert len(temp_pred_repo.load_all()) == 1
        assert len(temp_pred_repo.load_validation_reports()) == 1

        temp_pred_repo.clear()
        assert len(temp_pred_repo.load_all()) == 0
        assert len(temp_pred_repo.load_validation_reports()) == 0

    def test_corrupted_file_handling(
        self, temp_pred_repo: PredictionRepository
    ) -> None:
        bad_file = temp_pred_repo._root / "pred_corrupt.json"
        bad_file.write_text("invalid json content")

        # load_all should gracefully skip
        records = temp_pred_repo.load_all()
        assert len(records) == 0

        # get on corrupt file should return None
        assert temp_pred_repo.get("pred_corrupt") is None

    def test_get_nonexistent(
        self, temp_pred_repo: PredictionRepository
    ) -> None:
        assert temp_pred_repo.get("nonexistent_id") is None

    def test_save_prediction_raises_on_io_error(
        self, temp_pred_repo: PredictionRepository, sample_prediction: PredictionRecord
    ) -> None:
        with pytest.raises(Exception):
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr("storage.prediction_repository.save_json", lambda data, path: (_ for _ in ()).throw(IOError("Disk write failed")))
                temp_pred_repo.save(sample_prediction)

    def test_save_validation_report_raises_on_io_error(
        self, temp_pred_repo: PredictionRepository
    ) -> None:
        rep = PredictionValidationReport(
            report_id="val_err",
            bill_id="b1",
            company_isin="c1",
            event_window="[-20,+20]",
        )
        with pytest.raises(Exception):
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr("storage.prediction_repository.save_json", lambda data, path: (_ for _ in ()).throw(IOError("Disk write failed")))
                temp_pred_repo.save_validation_report(rep)

    def test_load_validation_reports_corrupt_file_handling(
        self, temp_pred_repo: PredictionRepository
    ) -> None:
        bad_report = temp_pred_repo._reports_dir / "val_corrupt.json"
        bad_report.write_text("invalid json")
        reports = temp_pred_repo.load_validation_reports()
        assert len(reports) == 0

    def test_clear_handles_unlink_exception(
        self, temp_pred_repo: PredictionRepository, sample_prediction: PredictionRecord
    ) -> None:
        temp_pred_repo.save(sample_prediction)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(Path, "unlink", lambda self: (_ for _ in ()).throw(PermissionError("Locked")))
            temp_pred_repo.clear()
