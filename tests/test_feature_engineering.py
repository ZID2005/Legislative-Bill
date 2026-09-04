"""
tests/test_feature_engineering.py
==================================
Comprehensive test suite for Task 5.1 — Unified Feature Engineering Engine.

Coverage targets
----------------
* FeatureRecord  schema (serialisation, helpers, edge cases)
* FeatureValidationReport schema
* FeatureRepository (save_many, load_all, load_dataframe, export_csv,
                     incremental index, exists, count, clear, get_by_*)
* FeatureEngineeringEngine (build, incremental rebuild, validation rules,
                            fault-tolerance, duplicate prevention)
* FeatureBuilder (thin wrapper API)

Design
------
All tests use temporary directories and mock / fake repositories so they
never touch production data.  No real pandas/parquet IO is skipped;
the tests exercise actual file writes to temp dirs.
"""

from __future__ import annotations

import json
import math
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers to build minimal fake domain objects
# ---------------------------------------------------------------------------


def _make_bill(bill_id: str = "test-bill-2024", title: str = "Test Bill"):
    """Return a minimal Bill object."""
    from schemas.bill import Bill, BillHouse, BillStatus
    return Bill(
        bill_id=bill_id,
        title=title,
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://example.com",
        ministry="Ministry of Finance",
        introduction_date=date(2024, 3, 1),
    )


def _make_knowledge(bill_id: str = "test-bill-2024"):
    """Return a minimal KnowledgeRecord."""
    from schemas.knowledge_record import KnowledgeRecord
    return KnowledgeRecord(
        bill_id=bill_id,
        ministry="Ministry of Finance",
        department="Department of Revenue",
        policy_domain="Fiscal Policy",
        economic_domain="Finance",
        primary_sector="BFSI",
        secondary_sectors=["Insurance", "Capital Markets"],
        regulatory_authority="SEBI",
        geographic_scope="National",
        bill_type="Finance Bill",
    )


def _make_company(isin: str = "INE001A01036", ticker: str = "HDFCBANK"):
    """Return a minimal Company."""
    from schemas.company import Company, MarketCapCategory
    return Company(
        isin=isin,
        company_name="HDFC Bank Limited",
        sector="Banking",
        ticker_nse=ticker,
        industry="Private Sector Bank",
        sub_industry="Retail Banking",
        market_cap_category=MarketCapCategory.LARGE_CAP,
        hq_state="Maharashtra",
    )


def _make_market_model(
    bill_id: str = "test-bill-2024", isin: str = "INE001A01036"
):
    """Return a minimal MarketModelRecord."""
    from schemas.market_model import MarketModelRecord
    return MarketModelRecord(
        company_isin=isin,
        company_symbol="HDFCBANK",
        bill_id=bill_id,
        alpha=0.0001,
        beta=1.05,
        r_squared=0.82,
        residual_variance=0.0002,
        standard_error=0.01,
        beta_stderr=0.05,
        alpha_stderr=0.0001,
        n_observations=120,
        estimation_window={"start_date": "2023-09-01", "end_date": "2024-02-28"},
        estimation_date="2024-03-01T00:00:00Z",
        benchmark_symbol="NIFTY50",
    )


def _make_event_study(
    bill_id: str = "test-bill-2024",
    isin: str = "INE001A01036",
    window: str = "[-5,+5]",
):
    """Return a minimal EventStudyRecord."""
    from schemas.event_study import EventStudyRecord
    return EventStudyRecord(
        bill_id=bill_id,
        company_isin=isin,
        company_symbol="HDFCBANK",
        event_date="2024-03-01",
        benchmark_symbol="NIFTY50",
        event_window=window,
        dates=["2024-02-24", "2024-02-25"],
        offsets=[-5, -4],
        expected_returns=[0.001, 0.001],
        actual_returns=[0.002, 0.001],
        daily_ar=[0.001, 0.000],
        running_car=[0.001, 0.001],
        final_car=0.035,
        avg_ar=0.003,
        max_ar=0.008,
        min_ar=-0.002,
        peak_ar_day=2,
        peak_car_day=3,
        observation_count=11,
        market_model_id=f"{bill_id}_{isin}",
        calculation_timestamp="2024-03-02T00:00:00Z",
    )


def _make_stat_result(
    bill_id: str = "test-bill-2024",
    isin: str = "INE001A01036",
    window: str = "[-5,+5]",
):
    """Return a minimal StatisticalResult."""
    from schemas.statistical_result import StatisticalResult
    return StatisticalResult(
        bill_id=bill_id,
        company=isin,
        company_symbol="HDFCBANK",
        event_window=window,
        car=0.035,
        variance=0.0001,
        standard_error=0.01,
        t_statistic=3.5,
        p_value=0.001,
        confidence_interval=[-0.01, 0.08],
        significant=True,
        confidence_level="1%",
        effect_size="Large",
        decision_reason="Significant",
        calculation_timestamp="2024-03-02T00:00:00Z",
    )


def _make_label(
    bill_id: str = "test-bill-2024",
    isin: str = "INE001A01036",
    window: str = "[-5,+5]",
):
    """Return a minimal LabelRecord."""
    from schemas.label_record import (
        ConfidenceLabel,
        DirectionLabel,
        ImpactStrength,
        LabelRecord,
    )
    return LabelRecord(
        bill_id=bill_id,
        company=isin,
        company_symbol="HDFCBANK",
        event_window=window,
        car=0.035,
        p_value=0.001,
        direction=DirectionLabel.POSITIVE,
        market_moving=True,
        impact_strength=ImpactStrength.HIGH,
        confidence=ConfidenceLabel.HIGH,
        decision_reason="Significant positive CAR",
        calculation_timestamp="2024-03-02T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# FeatureRecord schema tests
# ---------------------------------------------------------------------------


class TestFeatureRecord:
    """Tests for schemas/feature_record.py."""

    def test_make_record_id(self):
        from schemas.feature_record import make_record_id

        rid = make_record_id("bill-a", "INE001", "[-5,+5]")
        assert rid == "bill-a|INE001|[-5,+5]"

    def test_default_field_values(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        rec = FeatureRecord(record_id=rid, bill_id="b", company_isin="I", event_window="w")
        assert rec.bill_title == ""
        assert rec.secondary_sectors == []
        assert rec.alpha is None
        assert rec.direction is None
        assert rec.market_moving is None
        assert rec.feature_version == "1.0"

    def test_to_dict_round_trip(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("bill", "ISIN123", "[-5,+5]")
        rec = FeatureRecord(
            record_id=rid,
            bill_id="bill",
            company_isin="ISIN123",
            event_window="[-5,+5]",
            bill_title="Sample Bill",
            secondary_sectors=["Sector A", "Sector B"],
            alpha=0.0002,
            beta=1.1,
            final_car=0.04,
            t_statistic=2.5,
            p_value=0.012,
            direction="POSITIVE",
            market_moving=True,
            impact_strength="HIGH",
            confidence_label="MEDIUM",
            built_at="2024-03-01T00:00:00Z",
        )
        d = rec.to_dict()
        assert d["bill_id"] == "bill"
        assert d["secondary_sectors"] == ["Sector A", "Sector B"]
        assert d["beta"] == 1.1

        rec2 = FeatureRecord.from_dict(d)
        assert rec2.bill_id == rec.bill_id
        assert rec2.secondary_sectors == rec.secondary_sectors
        assert rec2.beta == pytest.approx(1.1)
        assert rec2.direction == "POSITIVE"
        assert rec2.market_moving is True

    def test_from_dict_json_encoded_secondary_sectors(self):
        """secondary_sectors survives Parquet round-trip as JSON string."""
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        d = {
            "record_id": rid, "bill_id": "b", "company_isin": "I", "event_window": "w",
            "secondary_sectors": '["A", "B"]',
        }
        rec = FeatureRecord.from_dict(d)
        assert rec.secondary_sectors == ["A", "B"]

    def test_from_dict_nan_becomes_none(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        d = {
            "record_id": rid, "bill_id": "b", "company_isin": "I", "event_window": "w",
            "alpha": float("nan"),
            "beta": float("nan"),
        }
        rec = FeatureRecord.from_dict(d)
        assert rec.alpha is None
        assert rec.beta is None

    def test_has_labels_true(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        rec = FeatureRecord(
            record_id=rid, bill_id="b", company_isin="I", event_window="w",
            direction="POSITIVE", market_moving=True,
            impact_strength="HIGH", confidence_label="HIGH",
        )
        assert rec.has_labels() is True

    def test_has_labels_false_when_partial(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        rec = FeatureRecord(
            record_id=rid, bill_id="b", company_isin="I", event_window="w",
            direction="POSITIVE",
            # missing market_moving, impact_strength, confidence_label
        )
        assert rec.has_labels() is False

    def test_has_financial_features(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        rec = FeatureRecord(
            record_id=rid, bill_id="b", company_isin="I", event_window="w",
            alpha=0.0, beta=1.0, r_squared=0.8,
        )
        assert rec.has_financial_features() is True

    def test_has_event_study_features(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        rec = FeatureRecord(
            record_id=rid, bill_id="b", company_isin="I", event_window="w",
            final_car=0.03,
        )
        assert rec.has_event_study_features() is True

    def test_repr(self):
        from schemas.feature_record import FeatureRecord, make_record_id

        rid = make_record_id("b", "I", "w")
        rec = FeatureRecord(record_id=rid, bill_id="b", company_isin="I", event_window="w")
        assert "FeatureRecord" in repr(rec)


# ---------------------------------------------------------------------------
# FeatureValidationReport schema tests
# ---------------------------------------------------------------------------


class TestFeatureValidationReport:
    def test_to_dict_round_trip(self):
        from schemas.feature_validation_report import FeatureValidationReport

        report = FeatureValidationReport(
            record_id="b|I|w",
            bill_id="b",
            company_isin="I",
            event_window="w",
            severity="ERROR",
            failed_checks=["missing_direction_label"],
            timestamp="2024-03-01T00:00:00Z",
        )
        d = report.to_dict()
        r2 = FeatureValidationReport.from_dict(d)
        assert r2.severity == "ERROR"
        assert r2.failed_checks == ["missing_direction_label"]

    def test_repr(self):
        from schemas.feature_validation_report import FeatureValidationReport

        report = FeatureValidationReport(
            record_id="b|I|w", bill_id="b", company_isin="I",
            event_window="w", severity="WARNING", failed_checks=["missing_bill_record"],
        )
        assert "FeatureValidationReport" in repr(report)


# ---------------------------------------------------------------------------
# FeatureRepository tests
# ---------------------------------------------------------------------------


class TestFeatureRepository:
    """Tests for storage/feature_repository.py."""

    def _make_repo(self, tmpdir: Path):
        from storage.feature_repository import FeatureRepository
        return FeatureRepository(features_dir=tmpdir, dataset_name="test_dataset")

    def _make_record(self, bill_id="b", isin="I", window="w"):
        from schemas.feature_record import FeatureRecord, make_record_id
        rid = make_record_id(bill_id, isin, window)
        return FeatureRecord(
            record_id=rid, bill_id=bill_id, company_isin=isin, event_window=window,
            direction="POSITIVE", market_moving=True,
            impact_strength="HIGH", confidence_label="HIGH",
            beta=1.05, alpha=0.0001, r_squared=0.82,
            final_car=0.035, t_statistic=3.5, p_value=0.001,
            secondary_sectors=["Banking"],
            built_at="2024-03-01T00:00:00Z",
        )

    def test_save_many_and_load_all(self, tmp_path):
        repo = self._make_repo(tmp_path)
        rec = self._make_record()
        total = repo.save_many([rec])
        assert total == 1

        loaded = repo.load_all()
        assert len(loaded) == 1
        assert loaded[0].bill_id == "b"

    def test_parquet_file_created(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record()])
        assert (tmp_path / "test_dataset.parquet").is_file()

    def test_index_file_created(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record()])
        idx_path = tmp_path / "index.json"
        assert idx_path.is_file()
        ids = json.loads(idx_path.read_text())
        assert "b|I|w" in ids

    def test_exists_true_after_save(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record()])
        assert repo.exists("b|I|w") is True

    def test_exists_false_before_save(self, tmp_path):
        repo = self._make_repo(tmp_path)
        assert repo.exists("nonexistent") is False

    def test_count(self, tmp_path):
        repo = self._make_repo(tmp_path)
        assert repo.count() == 0
        repo.save_many([self._make_record()])
        assert repo.count() == 1

    def test_duplicate_record_id_deduplication(self, tmp_path):
        """Saving same record_id twice must not create duplicate rows."""
        repo = self._make_repo(tmp_path)
        rec = self._make_record()
        repo.save_many([rec])
        repo.save_many([rec])  # second save of same record
        assert repo.count() == 1

    def test_incremental_merge(self, tmp_path):
        """New record IDs merge with existing dataset."""
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record("bill1", "ISIN1", "w")])
        repo.save_many([self._make_record("bill2", "ISIN2", "w")])
        assert repo.count() == 2

    def test_clear(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record()])
        repo.clear()
        assert repo.count() == 0
        assert not (tmp_path / "test_dataset.parquet").is_file()

    def test_load_dataframe(self, tmp_path):
        import pandas as pd

        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record()])
        df = repo.load_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "bill_id" in df.columns

    def test_load_dataframe_empty_when_no_data(self, tmp_path):
        import pandas as pd

        repo = self._make_repo(tmp_path)
        df = repo.load_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_export_csv(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record()])
        csv_path = repo.export_csv()
        assert csv_path.is_file()
        content = csv_path.read_text()
        assert "bill_id" in content
        assert ",b," in content  # bill_id value present

    def test_export_csv_raises_when_no_dataset(self, tmp_path):
        repo = self._make_repo(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.export_csv()

    def test_get_by_bill(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([
            self._make_record("bill1", "ISIN1", "w"),
            self._make_record("bill2", "ISIN2", "w"),
        ])
        result = repo.get_by_bill("bill1")
        assert len(result) == 1
        assert result[0].bill_id == "bill1"

    def test_get_by_company(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([
            self._make_record("bill1", "ISIN1", "w"),
            self._make_record("bill2", "ISIN2", "w"),
        ])
        result = repo.get_by_company("ISIN2")
        assert len(result) == 1
        assert result[0].company_isin == "ISIN2"

    def test_get_existing_record_ids(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record("b1", "I1", "w")])
        ids = repo.get_existing_record_ids()
        assert "b1|I1|w" in ids

    def test_dataset_info(self, tmp_path):
        repo = self._make_repo(tmp_path)
        repo.save_many([self._make_record()])
        info = repo.dataset_info()
        assert info["record_count"] == 1
        assert info["parquet_exists"] is True

    def test_repr(self, tmp_path):
        repo = self._make_repo(tmp_path)
        assert "FeatureRepository" in repr(repo)

    def test_secondary_sectors_json_roundtrip(self, tmp_path):
        """List fields survive Parquet→load_all round-trip."""
        repo = self._make_repo(tmp_path)
        rec = self._make_record()
        rec.secondary_sectors = ["Insurance", "Capital Markets"]
        repo.save_many([rec])
        loaded = repo.load_all()
        assert loaded[0].secondary_sectors == ["Insurance", "Capital Markets"]

    def test_load_all_empty_when_no_file(self, tmp_path):
        repo = self._make_repo(tmp_path)
        assert repo.load_all() == []


# ---------------------------------------------------------------------------
# Fake repository helpers for engine tests
# ---------------------------------------------------------------------------


class _FakeBillRepo:
    def __init__(self, bills=None):
        self._bills = bills or []

    def get_all(self):
        return self._bills


class _FakeKnowledgeRepo:
    def __init__(self, records=None):
        self._records = records or []

    def get_all(self):
        return self._records


class _FakeCompanyRepo:
    def __init__(self, companies=None):
        self._companies = companies or []

    def get_all(self):
        return self._companies


class _FakeMappingRepo:
    def __init__(self, mappings=None):
        self._mappings = mappings or []

    def get_all(self):
        return self._mappings


class _FakeMarketModelRepo:
    def __init__(self, models=None):
        self._models = {(m.bill_id, m.company_isin): m for m in (models or [])}

    def get(self, bill_id, company_isin):
        return self._models.get((bill_id, company_isin))


class _FakeEventStudyRepo:
    def __init__(self, studies=None):
        self._studies = {(s.bill_id, s.company_isin, s.event_window): s for s in (studies or [])}

    def get(self, bill_id, company_isin, event_window):
        return self._studies.get((bill_id, company_isin, event_window))


class _FakeStatRepo:
    def __init__(self, results=None):
        self._results = {(r.bill_id, r.company, r.event_window): r for r in (results or [])}

    def get(self, bill_id, company_isin, event_window):
        return self._results.get((bill_id, company_isin, event_window))


class _FakeLabelRepo:
    def __init__(self, labels=None):
        self._labels = labels or []

    def get_all(self):
        return self._labels


def _make_full_engine(tmp_path: Path):
    """
    Build a fully-wired FeatureEngineeringEngine using fake repositories
    pre-populated with one complete (bill, company, window) record.
    """
    from storage.feature_repository import FeatureRepository
    from features.feature_engine import FeatureEngineeringEngine

    bill = _make_bill()
    kr = _make_knowledge()
    company = _make_company()
    mm = _make_market_model()
    es = _make_event_study()
    stat = _make_stat_result()
    label = _make_label()
    feature_repo = FeatureRepository(features_dir=tmp_path / "features", dataset_name="test")

    engine = FeatureEngineeringEngine(
        bill_repo=_FakeBillRepo([bill]),
        knowledge_repo=_FakeKnowledgeRepo([kr]),
        company_repo=_FakeCompanyRepo([company]),
        mapping_repo=_FakeMappingRepo(),
        market_model_repo=_FakeMarketModelRepo([mm]),
        event_study_repo=_FakeEventStudyRepo([es]),
        statistical_repo=_FakeStatRepo([stat]),
        label_repo=_FakeLabelRepo([label]),
        feature_repo=feature_repo,
    )
    return engine, feature_repo


# ---------------------------------------------------------------------------
# FeatureEngineeringEngine tests
# ---------------------------------------------------------------------------


class TestFeatureEngineeringEngine:

    def test_build_full_record(self, tmp_path):
        """A complete pipeline record is assembled with all feature groups."""
        engine, repo = _make_full_engine(tmp_path)
        result = engine.build()

        assert result.records_written == 1
        assert result.records_rejected == 0
        assert result.total_in_dataset == 1

        records = repo.load_all()
        assert len(records) == 1
        r = records[0]

        # Legislative
        assert r.bill_id == "test-bill-2024"
        assert r.bill_title == "Test Bill"
        assert r.bill_type == "Finance Bill"
        assert r.ministry == "Ministry of Finance"
        assert r.department == "Department of Revenue"
        assert r.policy_domain == "Fiscal Policy"
        assert r.primary_sector == "BFSI"
        assert "Insurance" in r.secondary_sectors
        assert r.geographic_scope == "National"
        assert r.introduction_date == "2024-03-01"

        # Company
        assert r.nse_symbol == "HDFCBANK"
        assert r.company_name == "HDFC Bank Limited"
        assert r.company_sector == "Banking"
        assert r.market_cap_category == "large_cap"

        # Financial
        assert r.alpha == pytest.approx(0.0001)
        assert r.beta == pytest.approx(1.05)
        assert r.r_squared == pytest.approx(0.82)
        assert r.observation_count == 120

        # Event Study
        assert r.final_car == pytest.approx(0.035)
        assert r.avg_ar == pytest.approx(0.003)

        # Statistical
        assert r.t_statistic == pytest.approx(3.5)
        assert r.p_value == pytest.approx(0.001)
        assert r.significant_flag is True
        assert r.confidence_interval_lower == pytest.approx(-0.01)
        assert r.confidence_interval_upper == pytest.approx(0.08)

        # Labels
        assert r.direction == "POSITIVE"
        assert r.market_moving is True
        assert r.impact_strength == "HIGH"
        assert r.confidence_label == "HIGH"

    def test_build_empty_when_no_labels(self, tmp_path):
        """Engine returns zero records when label repo is empty."""
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo(),
            knowledge_repo=_FakeKnowledgeRepo(),
            company_repo=_FakeCompanyRepo(),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo(),
            event_study_repo=_FakeEventStudyRepo(),
            statistical_repo=_FakeStatRepo(),
            label_repo=_FakeLabelRepo([]),   # empty
            feature_repo=repo,
        )
        result = engine.build()
        assert result.records_written == 0
        assert result.total_in_dataset == 0

    def test_incremental_skips_existing(self, tmp_path):
        """Second build() call skips records already in the feature index."""
        engine, repo = _make_full_engine(tmp_path)
        r1 = engine.build(incremental=True)
        assert r1.records_written == 1

        r2 = engine.build(incremental=True)
        assert r2.records_written == 0
        assert r2.records_skipped == 1

    def test_rebuild_overwrites_existing(self, tmp_path):
        """rebuild() re-processes all records even if they already exist."""
        engine, repo = _make_full_engine(tmp_path)
        engine.build(incremental=True)
        result = engine.rebuild()
        assert result.records_written == 1
        assert result.records_skipped == 0

    def test_duplicate_prevention_in_parquet(self, tmp_path):
        """Two builds with same labels produce exactly one row, not two."""
        engine, repo = _make_full_engine(tmp_path)
        engine.rebuild()
        engine.rebuild()
        assert repo.count() == 1

    def test_missing_bill_generates_warning_not_error(self, tmp_path):
        """Records survive with WARNING when Bill repo has no data."""
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        label = _make_label()
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo([]),       # no bills
            knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
            company_repo=_FakeCompanyRepo([_make_company()]),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo([_make_market_model()]),
            event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
            statistical_repo=_FakeStatRepo([_make_stat_result()]),
            label_repo=_FakeLabelRepo([label]),
            feature_repo=repo,
        )
        result = engine.build()
        # Record should still be written (WARNING level only)
        assert result.records_written == 1
        assert result.records_rejected == 0
        assert len(result.validation_reports) == 1
        assert result.validation_reports[0].severity == "WARNING"

    def test_missing_company_generates_warning(self, tmp_path):
        """Records survive with WARNING when Company repo has no data."""
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        label = _make_label()
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo([_make_bill()]),
            knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
            company_repo=_FakeCompanyRepo([]),      # no companies
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo([_make_market_model()]),
            event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
            statistical_repo=_FakeStatRepo([_make_stat_result()]),
            label_repo=_FakeLabelRepo([label]),
            feature_repo=repo,
        )
        result = engine.build()
        assert result.records_written == 1
        assert result.records_rejected == 0

    def test_nan_in_market_model_triggers_error(self, tmp_path):
        """NaN numeric values in a market model record cause ERROR rejection."""
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        label = _make_label()

        # Build a market model with NaN alpha
        mm = _make_market_model()
        mm.alpha = float("nan")

        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo([_make_bill()]),
            knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
            company_repo=_FakeCompanyRepo([_make_company()]),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo([mm]),
            event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
            statistical_repo=_FakeStatRepo([_make_stat_result()]),
            label_repo=_FakeLabelRepo([label]),
            feature_repo=repo,
        )
        result = engine.build()
        assert result.records_rejected == 1
        assert result.records_written == 0
        report = result.validation_reports[0]
        assert report.severity == "ERROR"
        assert "nan_numeric_alpha" in report.failed_checks

    def test_multiple_bills_and_companies(self, tmp_path):
        """Engine handles multiple (bill, company, window) triples correctly."""
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        isin1, isin2 = "INE001A01036", "INE002A01036"
        bill_ids = ["bill-a", "bill-b"]

        bills = [_make_bill(bid, f"Title {bid}") for bid in bill_ids]
        knowledge = [_make_knowledge(bid) for bid in bill_ids]
        companies = [_make_company(isin1, "HDFCBANK"), _make_company(isin2, "ICICIBANK")]
        models = [_make_market_model(bid, isin) for bid in bill_ids for isin in [isin1, isin2]]
        studies = [_make_event_study(bid, isin) for bid in bill_ids for isin in [isin1, isin2]]
        stats = [_make_stat_result(bid, isin) for bid in bill_ids for isin in [isin1, isin2]]
        labels = [_make_label(bid, isin) for bid in bill_ids for isin in [isin1, isin2]]

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo(bills),
            knowledge_repo=_FakeKnowledgeRepo(knowledge),
            company_repo=_FakeCompanyRepo(companies),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo(models),
            event_study_repo=_FakeEventStudyRepo(studies),
            statistical_repo=_FakeStatRepo(stats),
            label_repo=_FakeLabelRepo(labels),
            feature_repo=repo,
        )
        result = engine.build()
        assert result.records_written == 4
        assert result.total_in_dataset == 4
        assert repo.count() == 4

    def test_build_duration_is_positive(self, tmp_path):
        engine, _ = _make_full_engine(tmp_path)
        result = engine.build()
        assert result.build_duration_seconds >= 0.0

    def test_dataset_info_keys(self, tmp_path):
        engine, _ = _make_full_engine(tmp_path)
        engine.build()
        info = engine.dataset_info()
        assert "record_count" in info
        assert "parquet_path" in info
        assert "parquet_exists" in info

    def test_export_csv_via_engine(self, tmp_path):
        engine, _ = _make_full_engine(tmp_path)
        engine.build()
        csv_path = engine.export_csv()
        assert csv_path.is_file()

    def test_no_duplicate_pairs_across_incremental_builds(self, tmp_path):
        """Multiple incremental builds never create duplicate record_ids."""
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        isin = "INE001A01036"
        label = _make_label()
        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")

        for _ in range(3):
            engine = FeatureEngineeringEngine(
                bill_repo=_FakeBillRepo([_make_bill()]),
                knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
                company_repo=_FakeCompanyRepo([_make_company()]),
                mapping_repo=_FakeMappingRepo(),
                market_model_repo=_FakeMarketModelRepo([_make_market_model()]),
                event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
                statistical_repo=_FakeStatRepo([_make_stat_result()]),
                label_repo=_FakeLabelRepo([label]),
                feature_repo=repo,
            )
            engine.build(incremental=True)

        assert repo.count() == 1

    def test_record_id_composite_key_format(self, tmp_path):
        """record_id must follow bill_id|company_isin|event_window format."""
        engine, repo = _make_full_engine(tmp_path)
        engine.build()
        records = repo.load_all()
        assert records[0].record_id == "test-bill-2024|INE001A01036|[-5,+5]"

    def test_rebuild_method(self, tmp_path):
        """rebuild() is an alias for build(incremental=False)."""
        engine, repo = _make_full_engine(tmp_path)
        engine.build(incremental=True)
        result = engine.rebuild()
        assert result.records_written == 1


# ---------------------------------------------------------------------------
# FeatureBuilder tests
# ---------------------------------------------------------------------------


class TestFeatureBuilder:

    def test_build_delegates_to_engine(self, tmp_path):
        from features.feature_builder import FeatureBuilder
        from features.feature_engine import FeatureEngineeringEngine, FeatureBuildResult
        from storage.feature_repository import FeatureRepository

        # Use a real engine wired to fake repos
        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo([_make_bill()]),
            knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
            company_repo=_FakeCompanyRepo([_make_company()]),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo([_make_market_model()]),
            event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
            statistical_repo=_FakeStatRepo([_make_stat_result()]),
            label_repo=_FakeLabelRepo([_make_label()]),
            feature_repo=repo,
        )
        builder = FeatureBuilder(engine=engine)
        result = builder.build()
        assert isinstance(result, FeatureBuildResult)
        assert result.records_written == 1

    def test_rebuild_via_builder(self, tmp_path):
        from features.feature_builder import FeatureBuilder
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo([_make_bill()]),
            knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
            company_repo=_FakeCompanyRepo([_make_company()]),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo([_make_market_model()]),
            event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
            statistical_repo=_FakeStatRepo([_make_stat_result()]),
            label_repo=_FakeLabelRepo([_make_label()]),
            feature_repo=repo,
        )
        builder = FeatureBuilder(engine=engine)
        builder.build()
        result = builder.rebuild()
        assert result.records_written == 1

    def test_export_csv_via_builder(self, tmp_path):
        from features.feature_builder import FeatureBuilder
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo([_make_bill()]),
            knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
            company_repo=_FakeCompanyRepo([_make_company()]),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo([_make_market_model()]),
            event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
            statistical_repo=_FakeStatRepo([_make_stat_result()]),
            label_repo=_FakeLabelRepo([_make_label()]),
            feature_repo=repo,
        )
        builder = FeatureBuilder(engine=engine)
        builder.build()
        csv_path = builder.export_csv()
        assert csv_path.is_file()

    def test_dataset_info_via_builder(self, tmp_path):
        from features.feature_builder import FeatureBuilder
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo([_make_bill()]),
            knowledge_repo=_FakeKnowledgeRepo([_make_knowledge()]),
            company_repo=_FakeCompanyRepo([_make_company()]),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo([_make_market_model()]),
            event_study_repo=_FakeEventStudyRepo([_make_event_study()]),
            statistical_repo=_FakeStatRepo([_make_stat_result()]),
            label_repo=_FakeLabelRepo([_make_label()]),
            feature_repo=repo,
        )
        builder = FeatureBuilder(engine=engine)
        builder.build()
        info = builder.dataset_info()
        assert info["record_count"] == 1

    def test_repr(self, tmp_path):
        from features.feature_builder import FeatureBuilder
        from storage.feature_repository import FeatureRepository
        from features.feature_engine import FeatureEngineeringEngine

        repo = FeatureRepository(features_dir=tmp_path / "f", dataset_name="test")
        engine = FeatureEngineeringEngine(
            bill_repo=_FakeBillRepo(),
            knowledge_repo=_FakeKnowledgeRepo(),
            company_repo=_FakeCompanyRepo(),
            mapping_repo=_FakeMappingRepo(),
            market_model_repo=_FakeMarketModelRepo(),
            event_study_repo=_FakeEventStudyRepo(),
            statistical_repo=_FakeStatRepo(),
            label_repo=_FakeLabelRepo(),
            feature_repo=repo,
        )
        builder = FeatureBuilder(engine=engine)
        assert "FeatureBuilder" in repr(builder)
