"""
tests/test_decision_repository.py
=================================
Unit tests for DecisionRepository persistence and retrieval (Task 7.2).
"""

from __future__ import annotations

from pathlib import Path
import pytest

from schemas.decision import DecisionSupportRecord, DecisionValidationReport
from storage.decision_repository import DecisionRepository


@pytest.fixture
def temp_decision_dir(tmp_path: Path) -> Path:
    d = tmp_path / "decision_support"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def decision_repo(temp_decision_dir: Path) -> DecisionRepository:
    return DecisionRepository(decision_dir=temp_decision_dir)


@pytest.fixture
def sample_record() -> DecisionSupportRecord:
    return DecisionSupportRecord(
        decision_id="dec_bill_1_INE001A01036_[-20,+20]",
        bill_id="bill_1",
        company_isin="INE001A01036",
        company_name="HDFC Bank",
        company_symbol="HDFCBANK",
        sector="Financial Services",
        event_window="[-20,+20]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.85, "NEGATIVE": 0.05, "NEUTRAL": 0.10},
        market_moving_probability=0.88,
        predicted_impact_strength="HIGH",
        impact_probabilities={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.70, "VERY_HIGH": 0.10},
        predicted_confidence="HIGH",
        confidence_probability={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80},
        confidence_score=0.85,
        anticipation_class="STRONG_EVIDENCE",
        anticipation_score=0.82,
        impact_score=0.72,
        impact_category="HIGH",
        risk_score=0.48,
        risk_category="MODERATE",
        pricing_in_risk="HIGH",
        pricing_in_score=0.82,
        investor_summary="Investor summary text.",
        business_summary="Business summary text.",
        public_summary="Public summary text.",
        decision_reason="Decision reason text.",
        model_version="v1.0",
        feature_version="v1.0",
        decision_version="v1.0",
        generation_timestamp="2026-08-16T12:00:00Z",
    )


class TestDecisionRepository:
    def test_save_and_get(
        self, decision_repo: DecisionRepository, sample_record: DecisionSupportRecord
    ) -> None:
        path = decision_repo.save(sample_record)
        assert path.exists()
        assert "dec_bill_1_INE001A01036" in path.name

        loaded = decision_repo.get(sample_record.decision_id)
        assert loaded is not None
        assert loaded.decision_id == sample_record.decision_id
        assert loaded.bill_id == sample_record.bill_id
        assert loaded.company_isin == sample_record.company_isin
        assert loaded.impact_score == sample_record.impact_score
        assert loaded.risk_score == sample_record.risk_score

    def test_get_non_existent_returns_none(self, decision_repo: DecisionRepository) -> None:
        assert decision_repo.get("dec_non_existent") is None

    def test_exists_and_get_by_key(
        self, decision_repo: DecisionRepository, sample_record: DecisionSupportRecord
    ) -> None:
        assert not decision_repo.exists("bill_1", "INE001A01036", "[-20,+20]")
        decision_repo.save(sample_record)
        assert decision_repo.exists("bill_1", "INE001A01036", "[-20,+20]")

        by_key = decision_repo.get_by_key("bill_1", "INE001A01036", "[-20,+20]")
        assert by_key is not None
        assert by_key.decision_id == sample_record.decision_id

    def test_save_many_and_load_all(
        self, decision_repo: DecisionRepository, sample_record: DecisionSupportRecord
    ) -> None:
        rec2 = DecisionSupportRecord(
            decision_id="dec_bill_2_INE002A01018_[-20,+20]",
            bill_id="bill_2",
            company_isin="INE002A01018",
            company_name="Reliance Industries",
            company_symbol="RELIANCE",
            sector="Energy",
            event_window="[-20,+20]",
            predicted_direction="NEUTRAL",
            direction_probability={"POSITIVE": 0.1, "NEGATIVE": 0.1, "NEUTRAL": 0.8},
            market_moving_probability=0.15,
            predicted_impact_strength="LOW",
            confidence_probability={"LOW": 0.7, "MEDIUM": 0.2, "HIGH": 0.1},
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.1,
            impact_score=0.15,
            impact_category="VERY_LOW",
            risk_score=0.25,
            risk_category="LOW",
            pricing_in_risk="VERY_LOW",
            investor_summary="Neutral outlook.",
            business_summary="Limited operational impact.",
            public_summary="General governance update.",
            decision_reason="Subdued reaction expected.",
            model_version="v1.0",
            feature_version="v1.0",
            generation_timestamp="2026-08-16T12:00:00Z",
        )

        paths = decision_repo.save_many([sample_record, rec2])
        assert len(paths) == 2

        all_records = decision_repo.load_all()
        assert len(all_records) == 2

        by_bill = decision_repo.get_by_bill("bill_1")
        assert len(by_bill) == 1
        assert by_bill[0].bill_id == "bill_1"

        by_company = decision_repo.get_by_company("INE002A01018")
        assert len(by_company) == 1
        assert by_company[0].company_isin == "INE002A01018"

    def test_validation_reports_persistence(self, decision_repo: DecisionRepository) -> None:
        report = DecisionValidationReport(
            report_id="",
            bill_id="bill_1",
            company_isin="INE001A01036",
            event_window="[-20,+20]",
            is_valid=True,
            errors=[],
            warnings=[],
            checks_performed={"all_valid": True},
        )
        path = decision_repo.save_validation_report(report)
        assert path.exists()

        reports = decision_repo.load_validation_reports()
        assert len(reports) == 1
        assert reports[0].bill_id == "bill_1"

    def test_clear_repository(
        self, decision_repo: DecisionRepository, sample_record: DecisionSupportRecord
    ) -> None:
        decision_repo.save(sample_record)
        assert len(decision_repo.load_all()) == 1

        decision_repo.clear()
        assert len(decision_repo.load_all()) == 0

    def test_corrupted_json_file_handling(
        self, decision_repo: DecisionRepository, temp_decision_dir: Path
    ) -> None:
        corrupted = temp_decision_dir / "dec_bad_record.json"
        corrupted.write_text("{invalid_json: true", encoding="utf-8")

        all_recs = decision_repo.load_all()
        assert len(all_recs) == 0

        val_reports_dir = temp_decision_dir / "reports"
        val_reports_dir.mkdir(parents=True, exist_ok=True)
        bad_val = val_reports_dir / "val_dec_bad.json"
        bad_val.write_text("not json", encoding="utf-8")

        reports = decision_repo.load_validation_reports()
        assert len(reports) == 0

    def test_save_raises_on_unwritable_path(
        self, decision_repo: DecisionRepository, sample_record: DecisionSupportRecord, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def mock_write_raise(*args, **kwargs):
            raise IOError("Permission denied")

        monkeypatch.setattr("storage.decision_repository.save_json", mock_write_raise)
        with pytest.raises(IOError):
            decision_repo.save(sample_record)
