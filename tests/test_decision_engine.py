"""
tests/test_decision_engine.py
=============================
Integration and unit tests for DecisionSupportEngine, DecisionSupportService, and CLI (Task 7.2).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from decision_support.engine import DecisionSupportEngine
from main import cmd_generate_decision_support
from schemas.anticipation import AnticipationClassification, AnticipationScore
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company, MarketCapCategory
from schemas.decision import DecisionSupportRecord
from schemas.mapping_record import BillCompanyMapping
from schemas.prediction import PredictionRecord
from services.decision_service import DecisionSupportService
from storage.anticipation_repository import AnticipationRepository
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.decision_repository import DecisionRepository
from storage.mapping_repository import MappingRepository
from storage.prediction_repository import PredictionRepository


@pytest.fixture
def mock_prediction_record() -> PredictionRecord:
    return PredictionRecord(
        prediction_id="pred_bill_1_INE002A01018_[-20,+20]",
        bill_id="the-telecom-act-2024",
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
        model_confidence=0.85,
        anticipation_class="STRONG_EVIDENCE",
        anticipation_score=0.80,
        model_name={"direction": "lgbm"},
        model_version="v1.0",
        feature_version="v1.0",
        prediction_timestamp="2026-08-16T12:00:00Z",
        decision_reason="Preliminary prediction narrative.",
    )


@pytest.fixture
def mock_bill() -> Bill:
    return Bill(
        bill_id="the-telecom-act-2024",
        title="The Telecommunications Act, 2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://prsindia.org/bills/the-telecom-act-2024",
        year=2024,
        ministry="Ministry of Communications",
        summary="A bill to overhaul telecommunications regulation.",
    )


@pytest.fixture
def mock_company() -> Company:
    return Company(
        isin="INE002A01018",
        company_name="Reliance Industries Limited",
        bse_code="500325",
        ticker_nse="RELIANCE",
        sector="Energy & Telecom",
        industry="Telecommunications",
        market_cap_category=MarketCapCategory.LARGE_CAP,
    )


@pytest.fixture
def mock_mapping() -> BillCompanyMapping:
    return BillCompanyMapping(
        bill_id="the-telecom-act-2024",
        bill_title="The Telecommunications Act, 2024",
        ministry="Ministry of Communications",
        policy_domain="Telecommunications",
        economic_domain="Infrastructure",
        primary_sector="Energy & Telecom",
        candidate_companies=[
            {
                "isin": "INE002A01018",
                "symbol": "RELIANCE",
                "confidence": 0.95,
                "exposure_type": "DIRECT",
                "reason": "Key telecom provider governed by spectrum laws.",
            }
        ],
        mapping_confidence=0.95,
        mapping_reason="Key telecom provider governed by spectrum laws.",
    )


class TestDecisionSupportEngine:
    def test_run_all_generates_decision_records(
        self,
        mock_prediction_record: PredictionRecord,
        mock_bill: Bill,
        mock_company: Company,
        mock_mapping: BillCompanyMapping,
        tmp_path: Path,
    ) -> None:
        pred_repo = MagicMock(spec=PredictionRepository)
        pred_repo.load_all.return_value = [mock_prediction_record]

        bill_repo = MagicMock(spec=BillRepository)
        bill_repo.get.return_value = mock_bill

        comp_repo = MagicMock(spec=CompanyRepository)
        comp_repo.get.return_value = mock_company
        comp_repo.get_by_isin.return_value = mock_company

        map_repo = MagicMock(spec=MappingRepository)
        map_repo.get.return_value = mock_mapping

        anticip_repo = MagicMock(spec=AnticipationRepository)
        anticip_repo.get_score.return_value = None

        dec_dir = tmp_path / "decision_support"
        dec_repo = DecisionRepository(decision_dir=dec_dir)

        engine = DecisionSupportEngine(
            prediction_repo=pred_repo,
            anticipation_repo=anticip_repo,
            decision_repo=dec_repo,
            bill_repo=bill_repo,
            company_repo=comp_repo,
            mapping_repo=map_repo,
        )

        stats = engine.run_all()
        assert stats["total_candidates"] == 1
        assert stats["decisions_generated"] == 1
        assert stats["decisions_skipped"] == 0
        assert stats["decisions_failed"] == 0
        assert len(stats["records"]) == 1

        rec = stats["records"][0]
        assert isinstance(rec, DecisionSupportRecord)
        assert rec.bill_id == "the-telecom-act-2024"
        assert rec.company_isin == "INE002A01018"
        assert rec.predicted_direction == "POSITIVE"
        assert rec.impact_score > 0.0
        assert rec.risk_score > 0.0
        assert rec.pricing_in_risk == "HIGH"
        assert "The Telecommunications Act, 2024" in rec.business_summary
        assert "potential positive impact" in rec.investor_summary

        # Verify disk persistence
        assert dec_repo.exists("the-telecom-act-2024", "INE002A01018", "[-20,+20]")
        loaded = dec_repo.get_by_key("the-telecom-act-2024", "INE002A01018", "[-20,+20]")
        assert loaded is not None
        assert loaded.decision_id == rec.decision_id

    def test_incremental_execution_skips_existing(
        self,
        mock_prediction_record: PredictionRecord,
        mock_bill: Bill,
        mock_company: Company,
        mock_mapping: BillCompanyMapping,
        tmp_path: Path,
    ) -> None:
        pred_repo = MagicMock(spec=PredictionRepository)
        pred_repo.load_all.return_value = [mock_prediction_record]

        bill_repo = MagicMock(spec=BillRepository)
        bill_repo.get.return_value = mock_bill

        comp_repo = MagicMock(spec=CompanyRepository)
        comp_repo.get.return_value = mock_company
        comp_repo.get_by_isin.return_value = mock_company

        map_repo = MagicMock(spec=MappingRepository)
        map_repo.get.return_value = mock_mapping

        dec_dir = tmp_path / "decision_support"
        dec_repo = DecisionRepository(decision_dir=dec_dir)

        engine = DecisionSupportEngine(
            prediction_repo=pred_repo,
            decision_repo=dec_repo,
            bill_repo=bill_repo,
            company_repo=comp_repo,
            mapping_repo=map_repo,
        )

        # Run 1: Generates
        stats1 = engine.run_all(force_refresh=False)
        assert stats1["decisions_generated"] == 1
        assert stats1["decisions_skipped"] == 0

        # Run 2: Skips because versions match
        stats2 = engine.run_all(force_refresh=False)
        assert stats2["decisions_generated"] == 0
        assert stats2["decisions_skipped"] == 1

        # Run 3: Force refresh regenerates
        stats3 = engine.run_all(force_refresh=True)
        assert stats3["decisions_generated"] == 1
        assert stats3["decisions_skipped"] == 0

    def test_candidate_filters(
        self,
        mock_prediction_record: PredictionRecord,
        mock_bill: Bill,
        tmp_path: Path,
    ) -> None:
        pred_repo = MagicMock(spec=PredictionRepository)
        pred_repo.load_all.return_value = [mock_prediction_record]

        bill_repo = MagicMock(spec=BillRepository)
        bill_repo.get.return_value = mock_bill

        dec_repo = DecisionRepository(decision_dir=tmp_path / "decision_support")

        engine = DecisionSupportEngine(
            prediction_repo=pred_repo,
            decision_repo=dec_repo,
            bill_repo=bill_repo,
        )

        # Non-matching bill_id filter
        stats = engine.run_all(bill_id_filter="different-bill")
        assert stats["total_candidates"] == 0

        # Non-matching company filter
        stats = engine.run_all(company_isin_filter="INE999999999")
        assert stats["total_candidates"] == 0

        # Non-matching year filter
        stats = engine.run_all(year_filter=2020)
        assert stats["total_candidates"] == 0


class TestDecisionSupportService:
    def test_service_delegates_to_engine_and_repo(self, tmp_path: Path) -> None:
        engine = MagicMock(spec=DecisionSupportEngine)
        engine.run_all.return_value = {"decisions_generated": 5}

        repo = MagicMock(spec=DecisionRepository)
        repo.get.return_value = "record_1"
        repo.get_by_bill.return_value = ["rec_bill"]
        repo.get_by_company.return_value = ["rec_comp"]
        repo.load_all.return_value = ["rec_all"]

        service = DecisionSupportService(engine=engine, repository=repo)

        res = service.generate_decision_support(bill_id="bill_1", force_refresh=True)
        assert res["decisions_generated"] == 5
        engine.run_all.assert_called_once_with(
            bill_id_filter="bill_1",
            company_isin_filter=None,
            year_filter=None,
            event_window_filter=None,
            force_refresh=True,
        )

        assert service.get_decision("dec_1") == "record_1"
        assert service.get_decisions_for_bill("bill_1") == ["rec_bill"]
        assert service.get_decisions_for_company("isin_1") == ["rec_comp"]
        assert service.get_all_decisions() == ["rec_all"]


class TestDecisionCLICommand:
    @patch("services.decision_service.DecisionSupportService.generate_decision_support")
    def test_cmd_generate_decision_support_success(self, mock_gen: MagicMock) -> None:
        mock_rec = MagicMock(spec=DecisionSupportRecord)
        mock_rec.bill_id = "the-telecom-act-2024"
        mock_rec.company_isin = "INE002A01018"
        mock_rec.company_symbol = "RELIANCE"
        mock_rec.predicted_direction = "POSITIVE"
        mock_rec.impact_score = 0.75
        mock_rec.risk_score = 0.40
        mock_rec.risk_category = "MODERATE"
        mock_rec.pricing_in_risk = "HIGH"

        mock_gen.return_value = {
            "total_candidates": 1,
            "decisions_generated": 1,
            "decisions_skipped": 0,
            "decisions_failed": 0,
            "risk_distribution": {"MODERATE": 1},
            "pricing_in_distribution": {"HIGH": 1},
            "records": [mock_rec],
        }

        args = argparse.Namespace(
            year=2024,
            bill_id=None,
            company_isin=None,
            event_window=None,
            force_refresh=True,
            rebuild=False,
        )

        exit_code = cmd_generate_decision_support(args)
        assert exit_code == 0
        mock_gen.assert_called_once_with(
            bill_id=None,
            company_isin=None,
            year=2024,
            event_window=None,
            force_refresh=True,
        )

    @patch("services.decision_service.DecisionSupportService.generate_decision_support")
    def test_cmd_generate_decision_support_error_handling(self, mock_gen: MagicMock) -> None:
        mock_gen.side_effect = RuntimeError("Storage corrupted")
        args = argparse.Namespace(
            year=None,
            bill_id=None,
            company_isin=None,
            event_window=None,
            force_refresh=False,
            rebuild=False,
        )
        exit_code = cmd_generate_decision_support(args)
        assert exit_code == 1
