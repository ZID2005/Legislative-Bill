"""
tests/test_statistical_significance.py
======================================
Unit tests for the Statistical Significance Engine.
"""

from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import MagicMock, patch
import scipy.stats as stats
import pytest

from schemas.event_study import EventStudyRecord
from schemas.market_model import MarketModelRecord
from schemas.statistical_result import StatisticalResult
from storage.statistical_repository import StatisticalRepository, sanitize_window
from validation.statistical_validator import StatisticalValidator
from services.statistical_service import StatisticalSignificanceService


@pytest.fixture
def temp_result_dir(tmp_path: Path) -> Path:
    """Fixture for isolated statistical results directory."""
    d = tmp_path / "statistical_results"
    d.mkdir()
    return d


@pytest.fixture
def statistical_repo(temp_result_dir: Path) -> StatisticalRepository:
    """Fixture for StatisticalRepository."""
    return StatisticalRepository(result_dir=temp_result_dir)


def test_sanitize_window():
    """Verify window label sanitization."""
    assert sanitize_window("[-5,+5]") == "m5,p5"
    assert sanitize_window("[-10,+10]") == "m10,p10"
    assert sanitize_window("[0,+1]") == "0,p1"


def test_statistical_result_serialization():
    """Verify StatisticalResult to_dict and from_dict roundtrip."""
    res = StatisticalResult(
        bill_id="test-bill",
        company="INE002A01018",
        company_symbol="RELIANCE",
        event_window="[-5,+5]",
        car=0.055,
        variance=0.002,
        standard_error=0.0447,
        t_statistic=1.23,
        p_value=0.22,
        confidence_interval=[-0.0326, 0.1426],
        significant=False,
        confidence_level="Not Significant",
        effect_size="Medium",
        decision_reason="Not significant because p=0.2200 and |t|=1.23",
        calculation_timestamp="2026-07-10T12:00:00Z",
    )
    data = res.to_dict()
    assert data["bill_id"] == "test-bill"
    assert data["confidence_interval"] == [-0.0326, 0.1426]

    res2 = StatisticalResult.from_dict(data)
    assert res2.bill_id == res.bill_id
    assert res2.company == res.company
    assert res2.car == res.car
    assert res2.significant == res.significant
    assert res2.confidence_interval == res.confidence_interval
    assert repr(res) == (
        "<StatisticalResult bill='test-bill' company='INE002A01018' "
        "window='[-5,+5]' car=0.0550 significant=False>"
    )


def test_repository_crud(statistical_repo):
    """Verify CRUD operations of StatisticalRepository."""
    res = StatisticalResult(
        bill_id="test-bill-1",
        company="INE123",
        company_symbol="TICK1",
        event_window="[-5,+5]",
        car=0.04,
        variance=0.001,
        standard_error=0.0316,
        t_statistic=1.26,
        p_value=0.21,
        confidence_interval=[-0.022, 0.102],
        significant=False,
        confidence_level="Not Significant",
        effect_size="Medium",
        decision_reason="Not significant",
        calculation_timestamp="2026-07-10T12:00:00Z",
    )

    # Save
    statistical_repo.save(res)
    assert statistical_repo.exists("test-bill-1", "INE123", "[-5,+5]")

    # Get
    retrieved = statistical_repo.get("test-bill-1", "INE123", "[-5,+5]")
    assert retrieved is not None
    assert retrieved.bill_id == "test-bill-1"
    assert retrieved.car == 0.04

    # Count
    assert statistical_repo.count() == 1

    # Get All
    all_results = statistical_repo.get_all()
    assert len(all_results) == 1
    assert all_results[0].bill_id == "test-bill-1"

    # Get By Bill
    by_bill = statistical_repo.get_by_bill("test-bill-1")
    assert len(by_bill) == 1

    # Get By Company
    by_comp = statistical_repo.get_by_company("INE123")
    assert len(by_comp) == 1

    # Delete
    statistical_repo.delete("test-bill-1", "INE123", "[-5,+5]")
    assert not statistical_repo.exists("test-bill-1", "INE123", "[-5,+5]")
    assert statistical_repo.count() == 0


def test_repository_empty_or_corrupt(statistical_repo, temp_result_dir):
    """Verify repository behavior with missing or corrupt files."""
    assert statistical_repo.get("non-existent", "comp", "[-1,+1]") is None

    # Write corrupt JSON file
    corrupt_file = temp_result_dir / "corrupt_file_m5_p5.json"
    with open(corrupt_file, "w") as f:
        f.write("{invalid json")

    # get_all should skip corrupt and log it
    assert len(statistical_repo.get_all()) == 0


def test_statistical_validator():
    """Verify StatisticalValidator checks and returns appropriate reports."""
    validator = StatisticalValidator()

    # 1. Valid case
    report = validator.validate_calculation(car=0.05, variance=0.001, standard_error=0.0316, df=100)
    assert report.is_valid

    # 2. Missing CAR
    report = validator.validate_calculation(car=None, variance=0.001, standard_error=0.0316, df=100)
    assert not report.is_valid
    assert "CAR is missing." in report.errors

    # 3. Invalid Variance
    report = validator.validate_calculation(car=0.05, variance=None, standard_error=0.0316, df=100)
    assert not report.is_valid
    assert "Variance is missing." in report.errors

    report = validator.validate_calculation(
        car=0.05, variance=-0.001, standard_error=0.0316, df=100
    )
    assert not report.is_valid
    assert any("Variance is invalid" in err for err in report.errors)

    report = validator.validate_calculation(
        car=0.05, variance=float("nan"), standard_error=0.0316, df=100
    )
    assert not report.is_valid
    assert any("Variance is invalid" in err for err in report.errors)

    # 4. Standard Error equals zero or invalid
    report = validator.validate_calculation(car=0.05, variance=0.001, standard_error=None, df=100)
    assert not report.is_valid
    assert "Standard Error is missing." in report.errors

    report = validator.validate_calculation(car=0.05, variance=0.001, standard_error=0.0, df=100)
    assert not report.is_valid
    assert "Standard Error equals zero." in report.errors

    report = validator.validate_calculation(car=0.05, variance=0.001, standard_error=-0.01, df=100)
    assert not report.is_valid
    assert any("Standard Error is invalid (negative):" in err for err in report.errors)

    report = validator.validate_calculation(
        car=0.05, variance=0.001, standard_error=float("inf"), df=100
    )
    assert not report.is_valid
    assert any("Standard Error is invalid:" in err for err in report.errors)

    # 5. Degrees of freedom invalid
    report = validator.validate_calculation(
        car=0.05, variance=0.001, standard_error=0.0316, df=None
    )
    assert not report.is_valid
    assert "Degrees of freedom is missing." in report.errors

    report = validator.validate_calculation(car=0.05, variance=0.001, standard_error=0.0316, df=0)
    assert not report.is_valid
    assert any("Degrees of freedom is invalid" in err for err in report.errors)

    report = validator.validate_calculation(car=0.05, variance=0.001, standard_error=0.0316, df=-5)
    assert not report.is_valid
    assert any("Degrees of freedom is invalid" in err for err in report.errors)


def test_calculations_math(statistical_repo):
    """Verify statistical calculations against exact scipy math."""
    es_record = EventStudyRecord(
        bill_id="test-bill-math",
        company_isin="INE001",
        company_symbol="SYM1",
        event_date="2026-07-10",
        benchmark_symbol="^NSEI",
        event_window="[-5,+5]",
        dates=[],
        offsets=[],
        expected_returns=[],
        actual_returns=[],
        daily_ar=[],
        running_car=[],
        final_car=0.06,  # 6% CAR
        avg_ar=0.0,
        max_ar=0.0,
        min_ar=0.0,
        peak_ar_day=0,
        peak_car_day=0,
        observation_count=11,  # 11 days in window [-5, +5]
        market_model_id="test-bill-math_INE001",
        calculation_timestamp="2026-07-10T12:00:00Z",
    )

    mm_record = MarketModelRecord(
        company_isin="INE001",
        company_symbol="SYM1",
        bill_id="test-bill-math",
        alpha=0.0001,
        beta=1.1,
        r_squared=0.45,
        residual_variance=0.0003,  # daily residual variance
        standard_error=math.sqrt(0.0003),
        beta_stderr=0.05,
        alpha_stderr=0.001,
        n_observations=122,  # 120 df
        estimation_window={},
        estimation_date="",
        benchmark_symbol="^NSEI",
    )

    mock_mm_repo = MagicMock()
    mock_mm_repo.get.return_value = mm_record

    service = StatisticalSignificanceService(
        event_study_repo=MagicMock(),
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        validator=StatisticalValidator(),
    )

    result, report = service.calculate_significance(es_record, force_refresh=True)

    assert report.is_valid
    assert result is not None

    # Variance: N * residual_variance = 11 * 0.0003 = 0.0033
    assert result.variance == pytest.approx(0.0033)
    # Standard Error: sqrt(variance) = sqrt(0.0033) = 0.0574456
    expected_se = math.sqrt(0.0033)
    assert result.standard_error == pytest.approx(expected_se)
    # t-statistic: CAR / SE = 0.06 / 0.0574456 = 1.044467
    expected_t = 0.06 / expected_se
    assert result.t_statistic == pytest.approx(expected_t)
    # df = 122 - 2 = 120
    # p-value: 2 * stats.t.sf(expected_t, 120) = 2 * (1 - t.cdf(expected_t, 120)) = 0.298379
    expected_p = float(2.0 * stats.t.sf(expected_t, 120))
    assert result.p_value == pytest.approx(expected_p)

    # 95% CI
    t_crit = float(stats.t.ppf(0.975, 120))
    expected_ci = [0.06 - t_crit * expected_se, 0.06 + t_crit * expected_se]
    assert result.confidence_interval == pytest.approx(expected_ci)

    # Significance and Confidence Level
    assert not result.significant
    assert result.confidence_level == "Not Significant"

    # Effect Size: absolute CAR = 0.06 >= 0.05 (Large)
    assert result.effect_size == "Large"
    assert "Not significant because" in result.decision_reason


def test_calculations_significant(statistical_repo):
    """Verify significance flags and levels are correctly determined."""
    es_record = EventStudyRecord(
        bill_id="test-bill-math-sig",
        company_isin="INE002",
        company_symbol="SYM2",
        event_date="2026-07-10",
        benchmark_symbol="^NSEI",
        event_window="[-1,+1]",
        dates=[],
        offsets=[],
        expected_returns=[],
        actual_returns=[],
        daily_ar=[],
        running_car=[],
        final_car=0.15,  # 15% CAR (extremely high)
        avg_ar=0.0,
        max_ar=0.0,
        min_ar=0.0,
        peak_ar_day=0,
        peak_car_day=0,
        observation_count=3,  # 3 days
        market_model_id="test-bill-math-sig_INE002",
        calculation_timestamp="2026-07-10T12:00:00Z",
    )

    mm_record = MarketModelRecord(
        company_isin="INE002",
        company_symbol="SYM2",
        bill_id="test-bill-math-sig",
        alpha=0.0001,
        beta=1.1,
        r_squared=0.45,
        residual_variance=0.0001,  # 0.01%
        standard_error=0.01,
        beta_stderr=0.05,
        alpha_stderr=0.001,
        n_observations=102,  # 100 df
        estimation_window={},
        estimation_date="",
        benchmark_symbol="^NSEI",
    )

    mock_mm_repo = MagicMock()
    mock_mm_repo.get.return_value = mm_record

    service = StatisticalSignificanceService(
        event_study_repo=MagicMock(),
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        validator=StatisticalValidator(),
    )

    # Calculate significance
    result, report = service.calculate_significance(es_record, force_refresh=True)
    assert report.is_valid
    assert result is not None
    assert result.significant
    # Variance = 3 * 0.0001 = 0.0003
    # SE = sqrt(0.0003) = 0.01732
    # t = 0.15 / 0.01732 = 8.66
    # p < 0.01 -> Confidence Level is "1%"
    assert result.confidence_level == "1%"
    assert result.effect_size == "Large"
    assert "Significant because" in result.decision_reason


def test_calculations_levels_and_sizes(statistical_repo):
    """Verify different combinations of significance levels and effect sizes."""
    es_record = EventStudyRecord(
        bill_id="test-bill", company_isin="INE003", company_symbol="SYM3",
        event_date="2026-07-10", benchmark_symbol="^NSEI", event_window="[-1,+1]",
        dates=[], offsets=[], expected_returns=[], actual_returns=[], daily_ar=[], running_car=[],
        final_car=0.035, avg_ar=0.0, max_ar=0.0, min_ar=0.0, peak_ar_day=0, peak_car_day=0,
        observation_count=3, market_model_id="id", calculation_timestamp=""
    )

    # Let's adjust residual variance to get p-value around 0.03
    # (5% significance) and CAR is Medium (0.035)
    mm_record = MarketModelRecord(
        company_isin="INE003", company_symbol="SYM3", bill_id="test-bill",
        alpha=0.0, beta=1.0, r_squared=0.5, residual_variance=0.000075,
        standard_error=0.0086, beta_stderr=0.05, alpha_stderr=0.001,
        n_observations=102, estimation_window={}, estimation_date="", benchmark_symbol="^NSEI"
    )

    mock_mm_repo = MagicMock()
    mock_mm_repo.get.return_value = mm_record

    service = StatisticalSignificanceService(
        event_study_repo=MagicMock(),
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        validator=StatisticalValidator()
    )

    result, report = service.calculate_significance(es_record, force_refresh=True)
    assert report.is_valid
    assert result is not None
    # CAR = 0.035 -> Medium effect size (0.02 <= 0.035 < 0.05)
    assert result.effect_size == "Medium"

    # Check 10% significance level by increasing residual variance slightly
    mm_record.residual_variance = 0.00018
    result_10, _ = service.calculate_significance(es_record, force_refresh=True)
    assert result_10 is not None
    # t = 0.035 / sqrt(3 * 0.00018) = 0.035 / 0.0232 = 1.505
    # p = 2 * sf(1.505, 100) = 0.13 (Not significant at 5%, and actually not at 10% either here)

    # Check Small effect size: CAR = 0.01
    es_record.final_car = 0.01
    result_small, _ = service.calculate_significance(es_record, force_refresh=True)
    assert result_small is not None
    assert result_small.effect_size == "Small"


def test_service_run_calculations_filters(statistical_repo):
    """Verify incremental run_calculations with filters."""
    es1 = EventStudyRecord(
        bill_id="bill-1", company_isin="INE001", company_symbol="S1",
        event_date="2026-07-10", benchmark_symbol="^NSEI", event_window="[-5,+5]",
        dates=[], offsets=[], expected_returns=[], actual_returns=[], daily_ar=[], running_car=[],
        final_car=0.02, avg_ar=0.0, max_ar=0.0, min_ar=0.0, peak_ar_day=0, peak_car_day=0,
        observation_count=11, market_model_id="", calculation_timestamp=""
    )
    es2 = EventStudyRecord(
        bill_id="bill-2", company_isin="INE002", company_symbol="S2",
        event_date="2026-07-10", benchmark_symbol="^NSEI", event_window="[-5,+5]",
        dates=[], offsets=[], expected_returns=[], actual_returns=[], daily_ar=[], running_car=[],
        final_car=-0.04, avg_ar=0.0, max_ar=0.0, min_ar=0.0, peak_ar_day=0, peak_car_day=0,
        observation_count=11, market_model_id="", calculation_timestamp=""
    )

    mock_es_repo = MagicMock()
    mock_es_repo.get_all.return_value = [es1, es2]

    mm = MarketModelRecord(
        company_isin="INE001", company_symbol="S1", bill_id="bill-1",
        alpha=0.0, beta=1.0, r_squared=0.5, residual_variance=0.0001,
        standard_error=0.01, beta_stderr=0.05, alpha_stderr=0.001,
        n_observations=102, estimation_window={}, estimation_date="", benchmark_symbol="^NSEI"
    )
    mm2 = MarketModelRecord(
        company_isin="INE002", company_symbol="S2", bill_id="bill-2",
        alpha=0.0, beta=1.0, r_squared=0.5, residual_variance=0.00015,
        standard_error=0.012, beta_stderr=0.05, alpha_stderr=0.001,
        n_observations=102, estimation_window={}, estimation_date="", benchmark_symbol="^NSEI"
    )

    mock_mm_repo = MagicMock()
    # Mocking get to return the right market model record based on arguments

    def get_mm(bill_id, company_isin):
        if bill_id == "bill-1":
            return mm
        elif bill_id == "bill-2":
            return mm2
        return None
    mock_mm_repo.get.side_effect = get_mm

    mock_bill_repo = MagicMock()
    # Mocking bills to have specific years
    bill1 = MagicMock()
    bill1.year = 2024
    bill2 = MagicMock()
    bill2.year = 2025

    def get_bill(bill_id):
        if bill_id == "bill-1":
            return bill1
        elif bill_id == "bill-2":
            return bill2
        return None
    mock_bill_repo.get.side_effect = get_bill

    service = StatisticalSignificanceService(
        event_study_repo=mock_es_repo,
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        bill_repo=mock_bill_repo,
        validator=StatisticalValidator()
    )

    # 1. Run all calculations (no filters)
    summary = service.run_calculations(force_refresh=True)
    assert summary["processed"] == 2
    assert summary["succeeded"] == 2
    assert summary["failed"] == 0
    assert summary["skipped"] == 0

    # 2. Run again without force_refresh (incremental execution)
    summary = service.run_calculations(force_refresh=False)
    assert summary["processed"] == 2
    assert summary["skipped"] == 2
    assert summary["succeeded"] == 0

    # 3. Test filtering by bill_id
    summary = service.run_calculations(bill_id_filter="bill-1", force_refresh=True)
    assert summary["processed"] == 1
    assert summary["succeeded"] == 1

    # 4. Test filtering by company_isin
    summary = service.run_calculations(company_isin_filter="INE002", force_refresh=True)
    assert summary["processed"] == 1
    assert summary["succeeded"] == 1

    # 5. Test filtering by window
    summary = service.run_calculations(window_filter="[-1,+1]", force_refresh=True)
    assert summary["processed"] == 0

    # 6. Test filtering by year
    summary = service.run_calculations(year=2025, force_refresh=True)
    assert summary["processed"] == 1
    assert summary["succeeded"] == 1


def test_calculations_validation_failure(statistical_repo):
    """Verify that calculations that fail validation are rejected and reported."""
    es_record = EventStudyRecord(
        bill_id="test-bill-fail",
        company_isin="INE999",
        company_symbol="SYM_FAIL",
        event_date="2026-07-10",
        benchmark_symbol="^NSEI",
        event_window="[-5,+5]",
        dates=[],
        offsets=[],
        expected_returns=[],
        actual_returns=[],
        daily_ar=[],
        running_car=[],
        final_car=float("nan"),  # Invalid CAR
        avg_ar=0.0,
        max_ar=0.0,
        min_ar=0.0,
        peak_ar_day=0,
        peak_car_day=0,
        observation_count=11,
        market_model_id="",
        calculation_timestamp="",
    )

    mm_record = MarketModelRecord(
        company_isin="INE999",
        company_symbol="SYM_FAIL",
        bill_id="test-bill-fail",
        alpha=0.0,
        beta=1.0,
        r_squared=0.5,
        residual_variance=-0.05,  # Invalid negative variance
        standard_error=0.0,  # Zero SE
        beta_stderr=0.05,
        alpha_stderr=0.001,
        n_observations=2,  # Invalid observations, df = 0
        estimation_window={},
        estimation_date="",
        benchmark_symbol="^NSEI",
    )

    mock_mm_repo = MagicMock()
    mock_mm_repo.get.return_value = mm_record

    service = StatisticalSignificanceService(
        event_study_repo=MagicMock(),
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        validator=StatisticalValidator(),
    )

    result, report = service.calculate_significance(es_record, force_refresh=True)
    assert result is None
    assert not report.is_valid
    # Errors should accumulate
    assert len(report.errors) > 0


def test_calculations_missing_market_model(statistical_repo):
    """Verify behavior when market model is missing."""
    es_record = EventStudyRecord(
        bill_id="test-bill-missing",
        company_isin="INE777",
        company_symbol="SYM_MISSING",
        event_date="2026-07-10",
        benchmark_symbol="^NSEI",
        event_window="[-5,+5]",
        dates=[],
        offsets=[],
        expected_returns=[],
        actual_returns=[],
        daily_ar=[],
        running_car=[],
        final_car=0.02,
        avg_ar=0.0,
        max_ar=0.0,
        min_ar=0.0,
        peak_ar_day=0,
        peak_car_day=0,
        observation_count=11,
        market_model_id="",
        calculation_timestamp="",
    )

    mock_mm_repo = MagicMock()
    mock_mm_repo.get.return_value = None  # Missing market model

    service = StatisticalSignificanceService(
        event_study_repo=MagicMock(),
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        validator=StatisticalValidator(),
    )

    result, report = service.calculate_significance(es_record, force_refresh=True)
    assert result is None
    assert not report.is_valid
    assert "Market model record not found" in report.errors[0]


def test_coverage_edge_cases(statistical_repo, temp_result_dir):
    """Test the remaining uncovered edge cases to achieve 100% coverage."""
    # 1. Cache hit branch in calculate_significance
    es_record = EventStudyRecord(
        bill_id="test-bill-cache", company_isin="INE111", company_symbol="SYM_C",
        event_date="2026-07-10", benchmark_symbol="^NSEI", event_window="[-5,+5]",
        dates=[], offsets=[], expected_returns=[], actual_returns=[], daily_ar=[], running_car=[],
        final_car=0.03, avg_ar=0.0, max_ar=0.0, min_ar=0.0, peak_ar_day=0, peak_car_day=0,
        observation_count=11, market_model_id="id", calculation_timestamp=""
    )
    mm_record = MarketModelRecord(
        company_isin="INE111", company_symbol="SYM_C", bill_id="test-bill-cache",
        alpha=0.0, beta=1.0, r_squared=0.5, residual_variance=0.0001,
        standard_error=0.01, beta_stderr=0.05, alpha_stderr=0.001,
        n_observations=102, estimation_window={}, estimation_date="", benchmark_symbol="^NSEI"
    )

    mock_mm_repo = MagicMock()
    mock_mm_repo.get.return_value = mm_record

    service = StatisticalSignificanceService(
        event_study_repo=MagicMock(),
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        validator=StatisticalValidator()
    )

    # Calculate and save
    res1, report1 = service.calculate_significance(es_record, force_refresh=True)
    assert report1.is_valid
    assert res1 is not None

    # Calculate again with force_refresh=False -> hits cache
    res2, report2 = service.calculate_significance(es_record, force_refresh=False)
    assert report2.is_valid
    assert res2 is not None
    assert res2.calculation_timestamp == res1.calculation_timestamp

    # 2. 10% Significance Level (p-value between 0.05 and 0.10)
    # Let's adjust CAR to get t-stat of ~1.7 -> p-val ~0.09
    # residual_variance = 0.0001 -> N = 11 -> variance = 0.0011 -> SE = 0.033166
    # To get t = 1.7, CAR = 1.7 * 0.033166 = 0.05638
    es_record.final_car = 0.05638
    res_10, _ = service.calculate_significance(es_record, force_refresh=True)
    assert res_10 is not None
    assert res_10.confidence_level == "10%"

    # 3. run_calculations with missing bill
    mock_es_repo = MagicMock()
    mock_es_repo.get_all.return_value = [es_record]
    mock_bill_repo = MagicMock()
    mock_bill_repo.get.return_value = None  # Bill missing

    service_missing_bill = StatisticalSignificanceService(
        event_study_repo=mock_es_repo,
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        bill_repo=mock_bill_repo,
        validator=StatisticalValidator()
    )
    # run with year filter
    summary = service_missing_bill.run_calculations(year=2024, force_refresh=True)
    assert summary["processed"] == 0
    # Should skip because bill is missing
    assert summary["succeeded"] == 0

    # 3b. run_calculations with bill year not matching filter
    mock_bill = MagicMock()
    mock_bill.year = 2020  # Doesn't match 2024
    mock_bill_repo2 = MagicMock()
    mock_bill_repo2.get.return_value = mock_bill

    service_wrong_year = StatisticalSignificanceService(
        event_study_repo=mock_es_repo,
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        bill_repo=mock_bill_repo2,
        validator=StatisticalValidator()
    )
    summary2 = service_wrong_year.run_calculations(year=2024, force_refresh=True)
    assert summary2["processed"] == 0

    # 3c. run_calculations with validation failure
    es_invalid = EventStudyRecord(
        bill_id="bill-invalid", company_isin="INE-INV", company_symbol="INV",
        event_date="2026-07-10", benchmark_symbol="^NSEI", event_window="[-5,+5]",
        dates=[], offsets=[], expected_returns=[], actual_returns=[], daily_ar=[], running_car=[],
        final_car=float("nan"), avg_ar=0.0, max_ar=0.0, min_ar=0.0, peak_ar_day=0, peak_car_day=0,
        observation_count=11, market_model_id="id", calculation_timestamp=""
    )
    mock_es_repo.get_all.return_value = [es_invalid]

    # We need a market model for it
    mm_invalid = MarketModelRecord(
        company_isin="INE-INV", company_symbol="INV", bill_id="bill-invalid",
        alpha=0.0, beta=1.0, r_squared=0.5, residual_variance=0.0001,
        standard_error=0.01, beta_stderr=0.05, alpha_stderr=0.001,
        n_observations=102, estimation_window={}, estimation_date="", benchmark_symbol="^NSEI"
    )

    def get_mm_invalid(bill_id, company_isin):
        if bill_id == "bill-invalid":
            return mm_invalid
        return None
    mock_mm_repo.get.side_effect = get_mm_invalid

    service_fail_val = StatisticalSignificanceService(
        event_study_repo=mock_es_repo,
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        bill_repo=mock_bill_repo,
        validator=StatisticalValidator()
    )
    summary_fail = service_fail_val.run_calculations(force_refresh=True)
    assert summary_fail["processed"] == 1
    assert summary_fail["failed"] == 1
    assert "bill-invalid_INE-INV_[-5,+5]" in summary_fail["errors"]

    # 3d. run_calculations raising an exception inside calculate_significance
    service_fail_exc = StatisticalSignificanceService(
        event_study_repo=mock_es_repo,
        market_model_repo=mock_mm_repo,
        statistical_repo=statistical_repo,
        bill_repo=mock_bill_repo,
        validator=StatisticalValidator()
    )
    service_fail_exc.calculate_significance = MagicMock(
        side_effect=Exception("forced test exception")
    )
    summary_exc = service_fail_exc.run_calculations(force_refresh=True)
    assert summary_exc["processed"] == 1
    assert summary_exc["failed"] == 1
    assert summary_exc["errors"]["bill-invalid_INE-INV_[-5,+5]"] == ["forced test exception"]

    # 4. Repository save_many
    res_a = StatisticalResult(
        bill_id="bill-a", company="INE-A", company_symbol="SA", event_window="[-1,+1]",
        car=0.01, variance=0.0001, standard_error=0.01, t_statistic=1.0, p_value=0.3,
        confidence_interval=[0.0, 0.02], significant=False, confidence_level="Not Significant",
        effect_size="Small", decision_reason="Reason", calculation_timestamp="2026"
    )
    res_b = StatisticalResult(
        bill_id="bill-b", company="INE-B", company_symbol="SB", event_window="[-1,+1]",
        car=0.02, variance=0.0001, standard_error=0.01, t_statistic=2.0, p_value=0.04,
        confidence_interval=[0.0, 0.04], significant=True, confidence_level="5%",
        effect_size="Small", decision_reason="Reason", calculation_timestamp="2026"
    )
    statistical_repo.save_many([res_a, res_b])
    assert statistical_repo.exists("bill-a", "INE-A", "[-1,+1]")
    assert statistical_repo.exists("bill-b", "INE-B", "[-1,+1]")

    # 5. get() on a corrupted file
    corrupt_file = temp_result_dir / "corrupt-get_INE_m5,p5.json"
    with open(corrupt_file, "w") as f:
        f.write("{corrupt")
    assert statistical_repo.get("corrupt-get", "INE", "[-5,+5]") is None

    # 6. Repository exceptions when listing/counting
    with patch(
        "storage.statistical_repository.list_files",
        side_effect=Exception("mocked list error"),
    ):
        assert len(statistical_repo.get_all()) == 0
        assert len(statistical_repo.get_by_bill("bill-a")) == 0
        assert len(statistical_repo.get_by_company("INE-A")) == 0
        assert statistical_repo.count() == 0
