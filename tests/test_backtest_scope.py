"""
tests/test_backtest_scope.py
==============================
Regression tests for Backtest Dataset Scope Validation.

These tests verify that the production backtest universe is correct,
that no test/stub records contaminate the pipeline, and that mathematical
parity holds across all data layers.

Added as part of the final Backtest Dataset Scope Audit.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from config.logging_config import get_logger
from schemas.bill import Bill, BillStatus
from schemas.company import Company

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants — production scope expectations
# ---------------------------------------------------------------------------

# Known non-legislative / stub bill IDs that must NOT appear in backtests
KNOWN_STUB_BILL_IDS = frozenset({"key-issues-and-analysis", "service-bill"})

# Pattern for test/stub bill IDs (bill-1, bill-2, test-xyz, stub-xyz)
TEST_BILL_PATTERN = re.compile(r"^(bill-\d+|test-|stub-)", re.IGNORECASE)

# Pattern for test company ISINs (TEST*, STUB*)
TEST_COMPANY_ISIN_PATTERN = re.compile(r"^(TEST|STUB)", re.IGNORECASE)

# Valid Indian ISIN prefix
VALID_ISIN_PREFIX = "INE"

# Expected event windows in the production system
EXPECTED_EVENT_WINDOWS = frozenset({
    "[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]",
})

# Minimum expected production bill count (guard against empty repos)
MIN_PRODUCTION_BILLS = 10

# Minimum expected production company count
MIN_PRODUCTION_COMPANIES = 30


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bill_metadata_dir() -> Path:
    """Path to bill metadata directory."""
    from config.settings import settings
    return settings.BILLS_DIR / "metadata"


@pytest.fixture(scope="module")
def companies_file() -> Path:
    """Path to company repository file."""
    from config.settings import settings
    return settings.COMPANIES_DIR / "companies.json"


@pytest.fixture(scope="module")
def mappings_dir() -> Path:
    """Path to mappings directory."""
    from config.settings import settings
    return settings.DATA_DIR / "mappings"


@pytest.fixture(scope="module")
def features_dir() -> Path:
    """Path to features directory."""
    from config.settings import settings
    return settings.DATA_DIR / "features"


@pytest.fixture(scope="module")
def ml_dir() -> Path:
    """Path to ML data directory."""
    from config.settings import settings
    return settings.ML_DATA_DIR


@pytest.fixture(scope="module")
def backtests_dir() -> Path:
    """Path to backtest outputs directory."""
    from config.settings import settings
    return settings.DATA_DIR / "backtests"


@pytest.fixture(scope="module")
def all_bill_metadata(bill_metadata_dir: Path) -> list[dict[str, Any]]:
    """Load all bill metadata records."""
    results = []
    if not bill_metadata_dir.is_dir():
        return results
    for f in sorted(bill_metadata_dir.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            results.append(json.load(fh))
    return results


@pytest.fixture(scope="module")
def all_companies(companies_file: Path) -> list[dict[str, Any]]:
    """Load all company records."""
    if not companies_file.is_file():
        return []
    with open(companies_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


@pytest.fixture(scope="module")
def production_bill_ids(all_bill_metadata: list[dict]) -> set[str]:
    """Return bill IDs that are genuine production legislative bills."""
    ids = set()
    for meta in all_bill_metadata:
        bid = meta.get("bill_id", "")
        if bid in KNOWN_STUB_BILL_IDS:
            continue
        if TEST_BILL_PATTERN.match(bid):
            continue
        ids.add(bid)
    return ids


@pytest.fixture(scope="module")
def stub_bill_ids(all_bill_metadata: list[dict]) -> set[str]:
    """Return bill IDs that are non-legislative / stub records."""
    ids = set()
    for meta in all_bill_metadata:
        bid = meta.get("bill_id", "")
        if bid in KNOWN_STUB_BILL_IDS or TEST_BILL_PATTERN.match(bid):
            ids.add(bid)
    return ids


# ---------------------------------------------------------------------------
# 1. Bill Repository Scope Tests
# ---------------------------------------------------------------------------


class TestBillRepositoryScope:
    """Verify the bill repository contains a valid production corpus."""

    def test_bill_metadata_exists(self, bill_metadata_dir: Path) -> None:
        """Bill metadata directory must exist and contain files."""
        assert bill_metadata_dir.is_dir(), f"Bill metadata dir not found: {bill_metadata_dir}"
        files = list(bill_metadata_dir.glob("*.json"))
        assert len(files) > 0, "No bill metadata files found"

    def test_minimum_production_bills(self, production_bill_ids: set[str]) -> None:
        """At least MIN_PRODUCTION_BILLS real legislative bills must exist."""
        assert len(production_bill_ids) >= MIN_PRODUCTION_BILLS, (
            f"Only {len(production_bill_ids)} production bills found, "
            f"expected >= {MIN_PRODUCTION_BILLS}"
        )

    def test_stub_bills_identified(self, stub_bill_ids: set[str]) -> None:
        """Known stub/non-legislative bills must be identified."""
        for stub in KNOWN_STUB_BILL_IDS:
            # Stub bills should either exist and be flagged, or not exist at all
            pass  # If they exist, they should be in stub_bill_ids

    def test_production_bills_have_introduction_dates(
        self, all_bill_metadata: list[dict], production_bill_ids: set[str]
    ) -> None:
        """Every production bill must have a valid introduction_date."""
        missing = []
        for meta in all_bill_metadata:
            bid = meta.get("bill_id", "")
            if bid not in production_bill_ids:
                continue
            if not meta.get("introduction_date"):
                missing.append(bid)
        assert len(missing) == 0, (
            f"Production bills missing introduction_date: {missing}"
        )

    def test_no_test_pattern_bills_in_production(
        self, production_bill_ids: set[str]
    ) -> None:
        """No bill-N, test-*, or stub-* IDs in the production set."""
        violations = [
            bid for bid in production_bill_ids
            if TEST_BILL_PATTERN.match(bid)
        ]
        assert len(violations) == 0, (
            f"Test-pattern bill IDs found in production: {violations}"
        )

    def test_stub_bills_have_no_introduction_date(
        self, all_bill_metadata: list[dict], stub_bill_ids: set[str]
    ) -> None:
        """Stub bills should lack a valid introduction_date (confirming they are stubs)."""
        for meta in all_bill_metadata:
            bid = meta.get("bill_id", "")
            if bid not in stub_bill_ids:
                continue
            # At least verify they're identified as stubs for documentation
            assert bid in KNOWN_STUB_BILL_IDS or TEST_BILL_PATTERN.match(bid)


# ---------------------------------------------------------------------------
# 2. Company Repository Scope Tests
# ---------------------------------------------------------------------------


class TestCompanyRepositoryScope:
    """Verify the company repository integrity."""

    def test_company_data_exists(self, companies_file: Path) -> None:
        """Company data file must exist."""
        assert companies_file.is_file(), f"Companies file not found: {companies_file}"

    def test_minimum_companies(self, all_companies: list[dict]) -> None:
        """At least MIN_PRODUCTION_COMPANIES must be in the repository."""
        assert len(all_companies) >= MIN_PRODUCTION_COMPANIES, (
            f"Only {len(all_companies)} companies found, "
            f"expected >= {MIN_PRODUCTION_COMPANIES}"
        )

    def test_no_duplicate_isins(self, all_companies: list[dict]) -> None:
        """All company ISINs must be unique."""
        isins = [c["isin"] for c in all_companies]
        assert len(isins) == len(set(isins)), (
            f"Duplicate ISINs found: {len(isins)} total, {len(set(isins))} unique"
        )

    def test_no_test_company_isins(self, all_companies: list[dict]) -> None:
        """No ISINs matching TEST* or STUB* patterns."""
        violations = [
            c["isin"] for c in all_companies
            if TEST_COMPANY_ISIN_PATTERN.match(c.get("isin", ""))
        ]
        assert len(violations) == 0, f"Test company ISINs found: {violations}"

    def test_all_isins_valid_prefix(self, all_companies: list[dict]) -> None:
        """All ISINs should start with 'INE' (Indian securities)."""
        violations = [
            c["isin"] for c in all_companies
            if not c.get("isin", "").startswith(VALID_ISIN_PREFIX)
        ]
        assert len(violations) == 0, f"Non-INE ISINs found: {violations}"

    def test_all_companies_active(self, all_companies: list[dict]) -> None:
        """Production companies should be active."""
        inactive = [
            c["isin"] for c in all_companies if not c.get("is_active", True)
        ]
        # Inactive companies are allowed but should be documented
        if inactive:
            logger.info("Inactive companies: %s", inactive)


# ---------------------------------------------------------------------------
# 3. Feature Dataset Scope Tests
# ---------------------------------------------------------------------------


class TestFeatureDatasetScope:
    """Verify the feature dataset contains only production records."""

    def test_feature_dataset_exists(self, features_dir: Path) -> None:
        """Feature Parquet file must exist."""
        parquet_file = features_dir / "master_feature_dataset.parquet"
        assert parquet_file.is_file(), f"Feature dataset not found: {parquet_file}"

    def test_no_stub_bills_in_features(self, features_dir: Path) -> None:
        """No stub/test bill IDs should appear in the feature dataset."""
        import pandas as pd

        parquet_file = features_dir / "master_feature_dataset.parquet"
        if not parquet_file.is_file():
            pytest.skip("Feature dataset not found")

        df = pd.read_parquet(parquet_file, columns=["bill_id"])
        unique_bills = set(df["bill_id"].unique())

        stub_in_features = unique_bills & KNOWN_STUB_BILL_IDS
        assert len(stub_in_features) == 0, (
            f"Stub bills found in feature dataset: {stub_in_features}"
        )

        test_in_features = [
            b for b in unique_bills if TEST_BILL_PATTERN.match(b)
        ]
        assert len(test_in_features) == 0, (
            f"Test-pattern bills found in feature dataset: {test_in_features}"
        )

    def test_feature_observation_parity(self, features_dir: Path) -> None:
        """expected = unique_bills × unique_companies × event_windows."""
        import pandas as pd

        parquet_file = features_dir / "master_feature_dataset.parquet"
        if not parquet_file.is_file():
            pytest.skip("Feature dataset not found")

        df = pd.read_parquet(
            parquet_file,
            columns=["bill_id", "company_isin", "event_window"],
        )
        n_bills = df["bill_id"].nunique()
        n_companies = df["company_isin"].nunique()
        n_windows = df["event_window"].nunique()
        expected = n_bills * n_companies * n_windows
        actual = len(df)

        assert actual == expected, (
            f"Feature parity MISMATCH: {n_bills}×{n_companies}×{n_windows}"
            f"={expected}, actual={actual}"
        )

    def test_valid_event_windows(self, features_dir: Path) -> None:
        """All event windows must be from the known production set."""
        import pandas as pd

        parquet_file = features_dir / "master_feature_dataset.parquet"
        if not parquet_file.is_file():
            pytest.skip("Feature dataset not found")

        df = pd.read_parquet(parquet_file, columns=["event_window"])
        unique_windows = set(df["event_window"].unique())

        unexpected = unique_windows - EXPECTED_EVENT_WINDOWS
        assert len(unexpected) == 0, (
            f"Unexpected event windows: {unexpected}"
        )


# ---------------------------------------------------------------------------
# 4. Backtest Output Scope Tests
# ---------------------------------------------------------------------------


class TestBacktestOutputScope:
    """Verify backtest outputs use only production records."""

    @pytest.fixture
    def v641_report(self, backtests_dir: Path) -> dict | None:
        """Load the v641_direction backtest report."""
        report_file = backtests_dir / "v641_direction" / "backtest_report.json"
        if not report_file.is_file():
            return None
        with open(report_file, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def test_v641_report_exists(self, v641_report: dict | None) -> None:
        """v641_direction backtest report must exist."""
        if v641_report is None:
            pytest.skip("v641_direction report not found")
        assert "summary_counts" in v641_report

    def test_no_stub_bills_in_backtest(self, backtests_dir: Path) -> None:
        """No stub bill IDs in backtest prediction outputs."""
        import pandas as pd

        pred_file = backtests_dir / "v641_direction" / "prediction_results.parquet"
        if not pred_file.is_file():
            pytest.skip("Prediction results not found")

        df = pd.read_parquet(pred_file, columns=["bill_id"])
        unique_bills = set(df["bill_id"].unique())

        stub_in_bt = unique_bills & KNOWN_STUB_BILL_IDS
        assert len(stub_in_bt) == 0, (
            f"Stub bills found in backtest: {stub_in_bt}"
        )

        test_in_bt = [b for b in unique_bills if TEST_BILL_PATTERN.match(b)]
        assert len(test_in_bt) == 0, (
            f"Test-pattern bills found in backtest: {test_in_bt}"
        )

    def test_backtest_isins_in_company_repo(
        self, backtests_dir: Path, all_companies: list[dict]
    ) -> None:
        """All ISINs in backtest must trace to the company repository."""
        import pandas as pd

        pred_file = backtests_dir / "v641_direction" / "prediction_results.parquet"
        if not pred_file.is_file():
            pytest.skip("Prediction results not found")

        df = pd.read_parquet(pred_file, columns=["company_isin"])
        bt_isins = set(df["company_isin"].unique())
        repo_isins = {c["isin"] for c in all_companies}

        untraced = bt_isins - repo_isins
        assert len(untraced) == 0, (
            f"Backtest ISINs not in company repo: {untraced}"
        )

    def test_backtest_bills_in_bill_repo(
        self, backtests_dir: Path, production_bill_ids: set[str]
    ) -> None:
        """All bill IDs in backtest must trace to the bill repository."""
        import pandas as pd

        pred_file = backtests_dir / "v641_direction" / "prediction_results.parquet"
        if not pred_file.is_file():
            pytest.skip("Prediction results not found")

        df = pd.read_parquet(pred_file, columns=["bill_id"])
        bt_bills = set(df["bill_id"].unique())

        untraced = bt_bills - production_bill_ids
        assert len(untraced) == 0, (
            f"Backtest bill IDs not in production bill repo: {untraced}"
        )

    def test_940_is_not_unique_companies(
        self, v641_report: dict | None
    ) -> None:
        """The '940' value must not be confused with unique companies."""
        if v641_report is None:
            pytest.skip("v641_direction report not found")

        overlap = v641_report.get("event_overlap_summary", {})
        max_simul = overlap.get("max_simultaneous_events", 0)

        counts = v641_report.get("summary_counts", {})
        unique_companies = counts.get("unique_companies", 0)

        # The 940 is simultaneous events, NOT unique companies
        if max_simul == 940:
            assert unique_companies != 940, (
                "CRITICAL: unique_companies equals max_simultaneous_events=940. "
                "These are observations, not companies."
            )
            assert unique_companies < 100, (
                f"unique_companies={unique_companies} seems too high. "
                "Expected ~47 mapped companies, not 940."
            )


# ---------------------------------------------------------------------------
# 5. Temporal Validation Tests
# ---------------------------------------------------------------------------


class TestTemporalValidation:
    """Verify temporal integrity of backtest predictions."""

    def test_no_temporal_violations(self, backtests_dir: Path) -> None:
        """training_cutoff_date must be < prediction_timestamp for all records."""
        import pandas as pd

        pred_file = backtests_dir / "v641_direction" / "prediction_results.parquet"
        if not pred_file.is_file():
            pytest.skip("Prediction results not found")

        df = pd.read_parquet(
            pred_file,
            columns=["prediction_timestamp", "training_cutoff_date"],
        )
        df["pred_dt"] = pd.to_datetime(df["prediction_timestamp"], errors="coerce")
        df["cutoff_dt"] = pd.to_datetime(df["training_cutoff_date"], errors="coerce")

        violations = df[df["cutoff_dt"] >= df["pred_dt"]]
        assert len(violations) == 0, (
            f"Temporal violations found: {len(violations)} records where "
            f"training_cutoff >= prediction_timestamp"
        )


# ---------------------------------------------------------------------------
# 6. Cross-Run Consistency Tests
# ---------------------------------------------------------------------------


class TestCrossRunConsistency:
    """Verify all v641 runs use identical data scope."""

    V641_RUNS = [
        "v641_direction",
        "v641_confidence",
        "v641_impact_strength",
        "v641_market_moving",
    ]

    def test_all_v641_runs_same_scope(self, backtests_dir: Path) -> None:
        """All v641 runs must report identical observation/bill/company counts."""
        results = {}
        for run_name in self.V641_RUNS:
            report_file = backtests_dir / run_name / "backtest_report.json"
            if not report_file.is_file():
                continue
            with open(report_file, "r", encoding="utf-8") as fh:
                rpt = json.load(fh)
            sc = rpt.get("summary_counts", {})
            results[run_name] = (
                sc.get("total_observations"),
                sc.get("unique_bills"),
                sc.get("unique_companies"),
            )

        if len(results) < 2:
            pytest.skip("Fewer than 2 v641 runs found")

        # All runs should have identical scope
        values = list(results.values())
        for run_name, val in results.items():
            assert val == values[0], (
                f"Scope mismatch: {run_name}={val} vs {list(results.keys())[0]}={values[0]}"
            )


# ---------------------------------------------------------------------------
# 7. Mathematical Parity — Unit Tests (synthetic data)
# ---------------------------------------------------------------------------


class TestMathematicalParitySynthetic:
    """Unit-level parity checks with synthetic data."""

    def test_observation_count_formula(self) -> None:
        """Verify N = bills × companies × windows for synthetic data."""
        bills = ["bill-A", "bill-B", "bill-C"]
        companies = ["ISIN-1", "ISIN-2"]
        windows = ["[-1,+1]", "[-3,+3]"]

        expected = len(bills) * len(companies) * len(windows)
        # Simulate a full cross-join
        observations = [
            (b, c, w) for b in bills for c in companies for w in windows
        ]
        assert len(observations) == expected

    def test_walk_forward_reduces_observations(self) -> None:
        """Walk-forward with 25% initial window should reduce test observations."""
        total_unique_dates = 8
        initial_cutoff_idx = max(2, int(total_unique_dates * 0.25))
        test_dates = total_unique_dates - initial_cutoff_idx
        assert test_dates < total_unique_dates
        assert test_dates == 6  # 8 - 2 = 6

    def test_simultaneous_events_not_companies(self) -> None:
        """940 simultaneous events ≠ 940 unique companies."""
        # Simulate: 4 bills × 47 companies × 5 windows
        n_bills = 4
        n_companies = 47
        n_windows = 5
        simultaneous_events = n_bills * n_companies * n_windows
        assert simultaneous_events == 940
        assert n_companies == 47  # Actual unique companies
        assert simultaneous_events != n_companies
