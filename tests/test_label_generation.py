"""
tests/test_label_generation.py
===============================
Comprehensive unit tests for the Label Generation Engine (Task 4.4).

Coverage targets
----------------
*  Direction labels (POSITIVE / NEGATIVE / NEUTRAL)
*  Market-moving labels (True / False)
*  Impact-strength labels (LOW / MEDIUM / HIGH / VERY_HIGH)
*  Confidence labels (HIGH / MEDIUM / LOW)
*  LabelRecord serialisation (to_dict / from_dict roundtrip)
*  LabelValidationReport serialisation
*  LabelRepository CRUD and filtered queries
*  Incremental execution (skip existing, force refresh)
*  LabelGenerator.generate_many batch path
*  Input validation (None result, NaN CAR, NaN p-value)
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from labeling.label_generator import LabelConfig, LabelGenerator
from schemas.label_record import ConfidenceLabel, DirectionLabel, ImpactStrength, LabelRecord
from schemas.statistical_result import StatisticalResult
from schemas.validation_report import LabelValidationReport
from storage.label_repository import LabelRepository, _sanitize_window


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

# Fixed threshold config used across all tests
_CFG = LabelConfig(
    positive_car_threshold=0.02,
    negative_car_threshold=0.02,
    market_moving_car_threshold=0.02,
    strength_low_max=0.01,
    strength_medium_max=0.03,
    strength_high_max=0.06,
    confidence_high_pvalue=0.01,
    confidence_medium_pvalue=0.05,
)


def _make_stat_result(
    bill_id: str = "test-bill-2024",
    company: str = "INE001A01036",
    company_symbol: str = "RELIANCE",
    event_window: str = "[-5,+5]",
    car: float = 0.03,
    p_value: float = 0.03,
    significant: bool = True,
    effect_size: str = "Medium",
) -> StatisticalResult:
    """Construct a minimal StatisticalResult for testing."""
    return StatisticalResult(
        bill_id=bill_id,
        company=company,
        company_symbol=company_symbol,
        event_window=event_window,
        car=car,
        variance=0.001,
        standard_error=0.03162,
        t_statistic=0.95,
        p_value=p_value,
        confidence_interval=[-0.03, 0.09],
        significant=significant,
        confidence_level="5%" if significant else "Not Significant",
        effect_size=effect_size,
        decision_reason="test reason",
        calculation_timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _make_label_record(
    bill_id: str = "test-bill-2024",
    company: str = "INE001A01036",
    company_symbol: str = "RELIANCE",
    event_window: str = "[-5,+5]",
    car: float = 0.03,
    p_value: float = 0.03,
    direction: DirectionLabel = DirectionLabel.POSITIVE,
    market_moving: bool = True,
    impact_strength: ImpactStrength = ImpactStrength.MEDIUM,
    confidence: ConfidenceLabel = ConfidenceLabel.MEDIUM,
) -> LabelRecord:
    """Construct a minimal LabelRecord for testing."""
    return LabelRecord(
        bill_id=bill_id,
        company=company,
        company_symbol=company_symbol,
        event_window=event_window,
        car=car,
        p_value=p_value,
        direction=direction,
        market_moving=market_moving,
        impact_strength=impact_strength,
        confidence=confidence,
        decision_reason="test decision reason",
        calculation_timestamp=datetime.now(timezone.utc).isoformat(),
    )


@pytest.fixture
def generator() -> LabelGenerator:
    """Return a LabelGenerator with the fixed test config."""
    return LabelGenerator(config=_CFG)


@pytest.fixture
def temp_label_dir(tmp_path: Path) -> Path:
    """Isolated temporary directory for label storage."""
    d = tmp_path / "labels"
    d.mkdir()
    return d


@pytest.fixture
def label_repo(temp_label_dir: Path) -> LabelRepository:
    """LabelRepository backed by a temporary directory."""
    return LabelRepository(label_dir=temp_label_dir)


# ===========================================================================
# 1. Direction labels
# ===========================================================================


class TestDirectionLabel:
    """Tests for DirectionLabel computation."""

    def test_positive_label(self, generator: LabelGenerator) -> None:
        """CAR above +threshold AND significant → POSITIVE."""
        stat = _make_stat_result(car=0.05, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.POSITIVE

    def test_negative_label(self, generator: LabelGenerator) -> None:
        """CAR below −threshold AND significant → NEGATIVE."""
        stat = _make_stat_result(car=-0.05, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEGATIVE

    def test_neutral_insignificant(self, generator: LabelGenerator) -> None:
        """Large |CAR| but NOT significant → NEUTRAL."""
        stat = _make_stat_result(car=0.10, significant=False)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEUTRAL

    def test_neutral_small_car_positive(self, generator: LabelGenerator) -> None:
        """Significant but CAR barely above zero (below threshold) → NEUTRAL."""
        stat = _make_stat_result(car=0.005, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEUTRAL

    def test_neutral_small_car_negative(self, generator: LabelGenerator) -> None:
        """Significant but |CAR| below negative threshold → NEUTRAL."""
        stat = _make_stat_result(car=-0.005, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEUTRAL

    def test_exact_positive_threshold(self, generator: LabelGenerator) -> None:
        """CAR exactly at threshold is NOT strictly greater → NEUTRAL."""
        stat = _make_stat_result(car=0.02, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEUTRAL

    def test_exact_negative_threshold(self, generator: LabelGenerator) -> None:
        """CAR exactly at −threshold is not strictly less → NEUTRAL."""
        stat = _make_stat_result(car=-0.02, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEUTRAL

    def test_positive_just_above_threshold(self, generator: LabelGenerator) -> None:
        """CAR just above threshold + significant → POSITIVE."""
        stat = _make_stat_result(car=0.02001, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.POSITIVE

    def test_negative_just_below_threshold(self, generator: LabelGenerator) -> None:
        """CAR just below −threshold + significant → NEGATIVE."""
        stat = _make_stat_result(car=-0.02001, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEGATIVE


# ===========================================================================
# 2. Market-moving labels
# ===========================================================================


class TestMarketMovingLabel:
    """Tests for the market_moving binary label."""

    def test_market_moving_true(self, generator: LabelGenerator) -> None:
        """Significant AND |CAR| > threshold → True."""
        stat = _make_stat_result(car=0.05, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.market_moving is True

    def test_market_moving_false_insignificant(self, generator: LabelGenerator) -> None:
        """Not significant → False, even if |CAR| is large."""
        stat = _make_stat_result(car=0.10, significant=False)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.market_moving is False

    def test_market_moving_false_small_car(self, generator: LabelGenerator) -> None:
        """Significant but |CAR| below threshold → False."""
        stat = _make_stat_result(car=0.005, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.market_moving is False

    def test_market_moving_false_exactly_at_threshold(
        self, generator: LabelGenerator
    ) -> None:
        """Significant and |CAR| exactly at threshold → False (strict >)."""
        stat = _make_stat_result(car=0.02, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.market_moving is False

    def test_market_moving_true_negative_car(self, generator: LabelGenerator) -> None:
        """Significant AND |CAR| > threshold for negative CAR → True."""
        stat = _make_stat_result(car=-0.05, significant=True)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.market_moving is True


# ===========================================================================
# 3. Impact strength
# ===========================================================================


class TestImpactStrength:
    """Tests for the ImpactStrength ordinal label."""

    def test_low_strength(self, generator: LabelGenerator) -> None:
        """|CAR| < 1% → LOW."""
        stat = _make_stat_result(car=0.005)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.LOW

    def test_low_boundary(self, generator: LabelGenerator) -> None:
        """|CAR| == 0 → LOW."""
        stat = _make_stat_result(car=0.0)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.LOW

    def test_medium_strength_lower(self, generator: LabelGenerator) -> None:
        """|CAR| at 1% boundary → MEDIUM."""
        stat = _make_stat_result(car=0.01)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.MEDIUM

    def test_medium_strength_upper(self, generator: LabelGenerator) -> None:
        """|CAR| just below 3% → MEDIUM."""
        stat = _make_stat_result(car=0.029)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.MEDIUM

    def test_high_strength(self, generator: LabelGenerator) -> None:
        """|CAR| at 3% boundary → HIGH."""
        stat = _make_stat_result(car=0.03)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.HIGH

    def test_high_strength_upper(self, generator: LabelGenerator) -> None:
        """|CAR| just below 6% → HIGH."""
        stat = _make_stat_result(car=0.059)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.HIGH

    def test_very_high_strength(self, generator: LabelGenerator) -> None:
        """|CAR| >= 6% → VERY_HIGH."""
        stat = _make_stat_result(car=0.06)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.VERY_HIGH

    def test_very_high_strength_large(self, generator: LabelGenerator) -> None:
        """|CAR| >> 6% → VERY_HIGH."""
        stat = _make_stat_result(car=0.20)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.VERY_HIGH

    def test_impact_strength_uses_absolute_car(self, generator: LabelGenerator) -> None:
        """Negative CAR uses |CAR| for strength, so −8% → VERY_HIGH."""
        stat = _make_stat_result(car=-0.08)
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.impact_strength == ImpactStrength.VERY_HIGH


# ===========================================================================
# 4. Confidence labels
# ===========================================================================


class TestConfidenceLabel:
    """Tests for the ConfidenceLabel composite label."""

    def test_confidence_high(self, generator: LabelGenerator) -> None:
        """p_value ≤ 0.01 AND effect_size == Large → HIGH."""
        stat = _make_stat_result(p_value=0.005, effect_size="Large")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.HIGH

    def test_confidence_high_boundary_pvalue(self, generator: LabelGenerator) -> None:
        """p_value exactly 0.01 AND effect_size == Large → HIGH."""
        stat = _make_stat_result(p_value=0.01, effect_size="Large")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.HIGH

    def test_confidence_medium_small_pvalue_medium_effect(
        self, generator: LabelGenerator
    ) -> None:
        """p_value ≤ 0.05 AND effect_size == Medium → MEDIUM."""
        stat = _make_stat_result(p_value=0.03, effect_size="Medium")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.MEDIUM

    def test_confidence_medium_large_effect_high_pvalue(
        self, generator: LabelGenerator
    ) -> None:
        """Large effect_size alone → MEDIUM even if p_value > 0.05."""
        stat = _make_stat_result(p_value=0.15, effect_size="Large")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.MEDIUM

    def test_confidence_medium_boundary_pvalue(self, generator: LabelGenerator) -> None:
        """p_value exactly 0.05 AND small effect → MEDIUM."""
        stat = _make_stat_result(p_value=0.05, effect_size="Small")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.MEDIUM

    def test_confidence_low(self, generator: LabelGenerator) -> None:
        """p_value > 0.05 AND effect_size == Small → LOW."""
        stat = _make_stat_result(p_value=0.30, effect_size="Small")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.LOW

    def test_confidence_not_significant_low(self, generator: LabelGenerator) -> None:
        """p_value just above 0.05 AND Small effect → LOW."""
        stat = _make_stat_result(p_value=0.051, effect_size="Small")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.LOW

    def test_confidence_case_insensitive_effect_size(
        self, generator: LabelGenerator
    ) -> None:
        """Effect size matching is case-normalised ('large' → 'Large')."""
        stat = _make_stat_result(p_value=0.005, effect_size="large")
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.confidence == ConfidenceLabel.HIGH


# ===========================================================================
# 5. LabelRecord serialisation
# ===========================================================================


class TestLabelRecordSerialisation:
    """Tests for to_dict / from_dict roundtrip."""

    def test_serialise_roundtrip(self) -> None:
        """to_dict followed by from_dict returns identical record."""
        record = _make_label_record()
        data = record.to_dict()

        assert data["bill_id"] == "test-bill-2024"
        assert data["direction"] == "POSITIVE"
        assert data["market_moving"] is True
        assert data["impact_strength"] == "MEDIUM"
        assert data["confidence"] == "MEDIUM"

        restored = LabelRecord.from_dict(data)
        assert restored.bill_id == record.bill_id
        assert restored.company == record.company
        assert restored.car == record.car
        assert restored.direction == record.direction
        assert restored.market_moving == record.market_moving
        assert restored.impact_strength == record.impact_strength
        assert restored.confidence == record.confidence

    def test_repr_format(self) -> None:
        """__repr__ contains key fields."""
        record = _make_label_record()
        r = repr(record)
        assert "LabelRecord" in r
        assert "test-bill-2024" in r
        assert "POSITIVE" in r
        assert "MEDIUM" in r

    def test_enum_values_are_strings(self) -> None:
        """Enum values serialise as plain strings (not 'DirectionLabel.POSITIVE')."""
        record = _make_label_record()
        data = record.to_dict()
        assert isinstance(data["direction"], str)
        assert data["direction"] == "POSITIVE"
        assert isinstance(data["impact_strength"], str)
        assert isinstance(data["confidence"], str)


# ===========================================================================
# 6. LabelValidationReport serialisation
# ===========================================================================


class TestLabelValidationReportSerialisation:
    """Tests for LabelValidationReport to_dict / from_dict."""

    def test_roundtrip(self) -> None:
        """Serialise and deserialise a rejection report."""
        report = LabelValidationReport(
            bill_id="test-bill",
            company="INE001A01036",
            event_window="[-5,+5]",
            rejection_reason="CAR is NaN",
            timestamp="2026-07-12T00:00:00+00:00",
        )
        data = report.to_dict()
        restored = LabelValidationReport.from_dict(data)

        assert restored.bill_id == report.bill_id
        assert restored.company == report.company
        assert restored.event_window == report.event_window
        assert restored.rejection_reason == report.rejection_reason
        assert restored.timestamp == report.timestamp

    def test_repr_format(self) -> None:
        """__repr__ contains key rejection metadata."""
        report = LabelValidationReport(
            bill_id="test-bill",
            company="INE001A01036",
            event_window="[-5,+5]",
            rejection_reason="p-value is NaN",
            timestamp="2026-07-12T00:00:00+00:00",
        )
        r = repr(report)
        assert "LabelValidationReport" in r
        assert "test-bill" in r


# ===========================================================================
# 7. Validation — rejected labels
# ===========================================================================


class TestLabelValidation:
    """Tests for input validation and rejection logic."""

    def test_none_stat_result_rejected(self, generator: LabelGenerator) -> None:
        """None input → LabelValidationReport."""
        result = generator.generate(None)
        assert isinstance(result, LabelValidationReport)
        assert "None" in result.rejection_reason

    def test_nan_car_rejected(self, generator: LabelGenerator) -> None:
        """CAR == NaN → LabelValidationReport."""
        stat = _make_stat_result(car=float("nan"))
        result = generator.generate(stat)
        assert isinstance(result, LabelValidationReport)
        assert "CAR" in result.rejection_reason

    def test_inf_car_rejected(self, generator: LabelGenerator) -> None:
        """CAR == inf → LabelValidationReport."""
        stat = _make_stat_result(car=float("inf"))
        result = generator.generate(stat)
        assert isinstance(result, LabelValidationReport)
        assert "CAR" in result.rejection_reason

    def test_nan_pvalue_rejected(self, generator: LabelGenerator) -> None:
        """p_value == NaN → LabelValidationReport."""
        stat = _make_stat_result(p_value=float("nan"))
        result = generator.generate(stat)
        assert isinstance(result, LabelValidationReport)
        assert "p-value" in result.rejection_reason

    def test_rejection_report_has_timestamp(self, generator: LabelGenerator) -> None:
        """Rejection report carries a valid ISO-8601 timestamp."""
        result = generator.generate(None)
        assert isinstance(result, LabelValidationReport)
        assert result.timestamp  # non-empty
        # Basic ISO 8601 check: contains 'T' separator
        assert "T" in result.timestamp


# ===========================================================================
# 8. LabelRepository — CRUD
# ===========================================================================


class TestLabelRepository:
    """Tests for LabelRepository persistence operations."""

    def test_save_and_get(self, label_repo: LabelRepository) -> None:
        """Save a record then retrieve it by primary key."""
        record = _make_label_record()
        label_repo.save(record)

        retrieved = label_repo.get(
            record.bill_id, record.company, record.event_window
        )
        assert retrieved is not None
        assert retrieved.bill_id == record.bill_id
        assert retrieved.direction == record.direction
        assert retrieved.market_moving == record.market_moving

    def test_exists_true(self, label_repo: LabelRepository) -> None:
        """exists() returns True after saving."""
        record = _make_label_record()
        label_repo.save(record)
        assert label_repo.exists(record.bill_id, record.company, record.event_window)

    def test_exists_false(self, label_repo: LabelRepository) -> None:
        """exists() returns False when record not persisted."""
        assert not label_repo.exists("no-bill", "INE000000000", "[-1,+1]")

    def test_get_missing_returns_none(self, label_repo: LabelRepository) -> None:
        """get() returns None for a non-existent key."""
        result = label_repo.get("missing", "INE000000000", "[-1,+1]")
        assert result is None

    def test_count_zero_initially(self, label_repo: LabelRepository) -> None:
        """count() returns 0 when no records saved."""
        assert label_repo.count() == 0

    def test_count_after_saves(self, label_repo: LabelRepository) -> None:
        """count() increments correctly with each save."""
        for i in range(3):
            label_repo.save(
                _make_label_record(
                    bill_id=f"bill-{i}",
                    company="INE001A01036",
                    event_window="[-5,+5]",
                )
            )
        assert label_repo.count() == 3

    def test_save_many(self, label_repo: LabelRepository) -> None:
        """save_many persists all records."""
        records = [
            _make_label_record(
                bill_id=f"multi-bill-{i}",
                company="INE001A01036",
                event_window="[-5,+5]",
            )
            for i in range(5)
        ]
        label_repo.save_many(records)
        assert label_repo.count() == 5

    def test_get_all(self, label_repo: LabelRepository) -> None:
        """get_all() returns all saved records."""
        records = [
            _make_label_record(
                bill_id=f"all-bill-{i}",
                company="INE001A01036",
                event_window="[-5,+5]",
            )
            for i in range(4)
        ]
        label_repo.save_many(records)
        all_records = label_repo.get_all()
        assert len(all_records) == 4

    def test_delete(self, label_repo: LabelRepository) -> None:
        """delete() removes the record from disk."""
        record = _make_label_record()
        label_repo.save(record)
        assert label_repo.exists(record.bill_id, record.company, record.event_window)

        label_repo.delete(record.bill_id, record.company, record.event_window)
        assert not label_repo.exists(record.bill_id, record.company, record.event_window)

    def test_delete_nonexistent_is_safe(self, label_repo: LabelRepository) -> None:
        """delete() on a missing record does not raise."""
        label_repo.delete("ghost-bill", "INE000000000", "[-1,+1]")  # no exception

    def test_save_overwrites(self, label_repo: LabelRepository) -> None:
        """Saving twice with the same key overwrites the record."""
        record_v1 = _make_label_record(direction=DirectionLabel.POSITIVE)
        label_repo.save(record_v1)

        record_v2 = _make_label_record(direction=DirectionLabel.NEGATIVE)
        label_repo.save(record_v2)

        retrieved = label_repo.get(record_v2.bill_id, record_v2.company, record_v2.event_window)
        assert retrieved is not None
        assert retrieved.direction == DirectionLabel.NEGATIVE


# ===========================================================================
# 9. LabelRepository — filtered queries
# ===========================================================================


class TestLabelRepositoryFilters:
    """Tests for get_by_bill and get_by_company queries."""

    def test_get_by_bill(self, label_repo: LabelRepository) -> None:
        """get_by_bill() returns all records for a specific bill."""
        label_repo.save(_make_label_record(bill_id="alpha-2024", company="INE001A01036"))
        label_repo.save(_make_label_record(bill_id="alpha-2024", company="INE002A01018"))
        label_repo.save(_make_label_record(bill_id="beta-2024", company="INE001A01036"))

        results = label_repo.get_by_bill("alpha-2024")
        assert len(results) == 2
        assert all(r.bill_id == "alpha-2024" for r in results)

    def test_get_by_bill_empty(self, label_repo: LabelRepository) -> None:
        """get_by_bill() returns empty list for unknown bill."""
        results = label_repo.get_by_bill("no-such-bill")
        assert results == []

    def test_get_by_company(self, label_repo: LabelRepository) -> None:
        """get_by_company() returns all records for a specific ISIN."""
        isin_a = "INE001A01036"
        isin_b = "INE002A01018"
        label_repo.save(_make_label_record(bill_id="bill-1", company=isin_a))
        label_repo.save(_make_label_record(bill_id="bill-2", company=isin_a))
        label_repo.save(_make_label_record(bill_id="bill-3", company=isin_b))

        results = label_repo.get_by_company(isin_a)
        assert len(results) == 2
        assert all(r.company == isin_a for r in results)

    def test_get_by_company_empty(self, label_repo: LabelRepository) -> None:
        """get_by_company() returns empty list for unknown ISIN."""
        results = label_repo.get_by_company("INE999Z99999")
        assert results == []


# ===========================================================================
# 10. Incremental execution
# ===========================================================================


class TestIncrementalExecution:
    """Tests for skip-existing and force-refresh behaviour."""

    def test_skip_existing_label(
        self, generator: LabelGenerator, label_repo: LabelRepository
    ) -> None:
        """
        When skip_if_exists returns True, generate() is not re-run.
        Using generate_many to test the skip path.
        """
        stat = _make_stat_result()
        # First pass: generate and save
        result = generator.generate(stat)
        assert isinstance(result, LabelRecord)
        label_repo.save(result)

        # Second pass: skip_if_exists will return True
        valid, rejected = generator.generate_many(
            stat_results=[stat],
            skip_if_exists=label_repo.exists,
        )
        assert len(valid) == 0  # skipped
        assert len(rejected) == 0
        assert label_repo.count() == 1  # still just one record

    def test_force_refresh_regenerates(
        self, generator: LabelGenerator, label_repo: LabelRepository
    ) -> None:
        """
        When skip_if_exists=None (force refresh), all records are regenerated.
        """
        stats = [
            _make_stat_result(company="INE001A01036"),
            _make_stat_result(company="INE002A01018"),
        ]
        # First pass
        valid1, _ = generator.generate_many(stats)
        label_repo.save_many(valid1)
        assert label_repo.count() == 2

        # Force refresh — no skip callable
        valid2, _ = generator.generate_many(stats, skip_if_exists=None)
        label_repo.save_many(valid2)
        # Overwriting gives the same count
        assert label_repo.count() == 2

    def test_partial_skip(
        self, generator: LabelGenerator, label_repo: LabelRepository
    ) -> None:
        """Only already-existing records are skipped; new ones are generated."""
        existing = _make_stat_result(company="INE001A01036")
        new_record = _make_stat_result(company="INE002A01018")

        # Pre-save the first one
        label_repo.save(generator.generate(existing))  # type: ignore[arg-type]

        stats = [existing, new_record]
        valid, rejected = generator.generate_many(
            stat_results=stats,
            skip_if_exists=label_repo.exists,
        )
        # Only the new_record should be generated
        assert len(valid) == 1
        assert valid[0].company == "INE002A01018"
        assert len(rejected) == 0


# ===========================================================================
# 11. Batch generation
# ===========================================================================


class TestBatchGeneration:
    """Tests for generate_many."""

    def test_batch_mix_valid_rejected(self, generator: LabelGenerator) -> None:
        """generate_many correctly splits valid and rejected results."""
        valid_stat = _make_stat_result(car=0.05, significant=True)
        bad_stat = _make_stat_result(car=float("nan"))

        valid_labels, rejected_reports = generator.generate_many([valid_stat, bad_stat])

        assert len(valid_labels) == 1
        assert len(rejected_reports) == 1
        assert isinstance(valid_labels[0], LabelRecord)
        assert isinstance(rejected_reports[0], LabelValidationReport)

    def test_batch_empty_input(self, generator: LabelGenerator) -> None:
        """generate_many with empty list returns empty results."""
        valid, rejected = generator.generate_many([])
        assert valid == []
        assert rejected == []


# ===========================================================================
# 12. Sanitize window helper
# ===========================================================================


class TestSanitizeWindow:
    """Tests for the _sanitize_window path-safety helper."""

    def test_standard_window(self) -> None:
        assert _sanitize_window("[-5,+5]") == "m5,p5"

    def test_zero_start_window(self) -> None:
        assert _sanitize_window("[0,+20]") == "0,p20"

    def test_long_window(self) -> None:
        assert _sanitize_window("[-10,+10]") == "m10,p10"


# ===========================================================================
# 13. LabelConfig from_settings
# ===========================================================================


class TestLabelConfig:
    """Tests for LabelConfig instantiation from settings."""

    def test_from_settings_produces_valid_config(self) -> None:
        """from_settings() returns a LabelConfig with sensible defaults."""
        config = LabelConfig.from_settings()
        assert config.positive_car_threshold > 0
        assert config.negative_car_threshold > 0
        assert config.strength_low_max < config.strength_medium_max
        assert config.strength_medium_max < config.strength_high_max
        assert 0 < config.confidence_high_pvalue <= config.confidence_medium_pvalue

    def test_custom_config_override(self) -> None:
        """Custom LabelConfig is respected by LabelGenerator."""
        custom_cfg = LabelConfig(
            positive_car_threshold=0.10,  # very high threshold
            negative_car_threshold=0.10,
            market_moving_car_threshold=0.10,
            strength_low_max=0.05,
            strength_medium_max=0.10,
            strength_high_max=0.20,
            confidence_high_pvalue=0.01,
            confidence_medium_pvalue=0.05,
        )
        gen = LabelGenerator(config=custom_cfg)
        # CAR=0.05 is POSITIVE under default config, but NEUTRAL under custom (threshold=0.10)
        stat = _make_stat_result(car=0.05, significant=True)
        result = gen.generate(stat)
        assert isinstance(result, LabelRecord)
        assert result.direction == DirectionLabel.NEUTRAL
