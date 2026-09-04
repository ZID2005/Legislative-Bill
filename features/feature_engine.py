"""
features/feature_engine.py
===========================
Unified Feature Engineering Engine — **Task 5.1**

Responsibility
--------------
Combine every upstream repository into one structured feature table:

  Bill Repository            → Legislative features
  Knowledge Repository       → Extended legislative features
  Company Repository         → Company features
  Mapping Repository         → Bill–Company pairs (driving join keys)
  Market Model Repository    → Financial features (alpha, beta, R², …)
  Event Study Repository     → Event-study features (CAR, AR, peaks, …)
  Statistical Repository     → Statistical features (t-stat, p-value, …)
  Label Repository           → Target labels (direction, market_moving, …)

Output
------
One ``FeatureRecord`` per (Bill × Company × Event-Window) triple, persisted
in Parquet via ``FeatureRepository``.

Key Design Decisions
--------------------
1.  **Label-anchored enumeration** — the Label repository is the authoritative
    source of (bill, company, window) keys.  This guarantees every assembled
    record has ground-truth labels.

2.  **Incremental rebuild** — ``build(incremental=True)`` skips any
    ``record_id`` already present in the feature index, avoiding redundant
    work when new data arrives for a subset of bills.

3.  **Fault tolerance** — individual lookup failures are caught and logged;
    they produce a ``FeatureValidationReport`` but do not stop the pipeline.

4.  **No ML / embeddings** — this module is strictly a structured data
    assembly pipeline.

Usage
-----
::

    from features.feature_engine import FeatureEngineeringEngine

    engine = FeatureEngineeringEngine()
    result = engine.build()

    print(f"Built {result.records_written} records")
    print(f"Validation errors: {len(result.validation_reports)}")
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from config.logging_config import get_logger
from schemas.feature_record import FeatureRecord, make_record_id
from schemas.feature_validation_report import FeatureValidationReport

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Build result
# ---------------------------------------------------------------------------


@dataclass
class FeatureBuildResult:
    """
    Summary of a single ``FeatureEngineeringEngine.build()`` run.

    Attributes
    ----------
    records_written : int
        Number of FeatureRecords successfully written in this run.
    records_skipped : int
        Records skipped because they already existed (incremental mode).
    records_rejected : int
        Records rejected by validation (missing labels, NaN numerics, …).
    total_in_dataset : int
        Total rows in the feature dataset after the build.
    validation_reports : list[FeatureValidationReport]
        One entry per rejected or warned record.
    build_duration_seconds : float
        Wall-clock time of the build run.
    """

    records_written: int = 0
    records_skipped: int = 0
    records_rejected: int = 0
    total_in_dataset: int = 0
    validation_reports: list[FeatureValidationReport] = field(default_factory=list)
    build_duration_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class FeatureEngineeringEngine:
    """
    Unified Feature Engineering Engine.

    Merges all upstream repositories into a master ML feature dataset
    and persists it via ``FeatureRepository``.

    Parameters
    ----------
    bill_repo : BillRepository, optional
    knowledge_repo : KnowledgeRepository, optional
    company_repo : CompanyRepository, optional
    mapping_repo : MappingRepository, optional
    market_model_repo : MarketModelRepository, optional
    event_study_repo : EventStudyRepository, optional
    statistical_repo : StatisticalRepository, optional
    label_repo : LabelRepository, optional
    feature_repo : FeatureRepository, optional
        Pass explicit instances for dependency injection / testing.
        When ``None`` the module-level singletons from ``storage`` are used.
    """

    def __init__(
        self,
        bill_repo=None,
        knowledge_repo=None,
        company_repo=None,
        mapping_repo=None,
        market_model_repo=None,
        event_study_repo=None,
        statistical_repo=None,
        label_repo=None,
        feature_repo=None,
    ) -> None:
        # Lazy import of singletons avoids circular-import issues and lets
        # tests inject mocks cleanly.
        if bill_repo is None:
            from storage import bill_repo as _br
            bill_repo = _br
        if knowledge_repo is None:
            from storage import knowledge_repo as _kr
            knowledge_repo = _kr
        if company_repo is None:
            from storage import company_repo as _cr
            company_repo = _cr
        if mapping_repo is None:
            from storage import mapping_repo as _mr
            mapping_repo = _mr
        if market_model_repo is None:
            from storage import market_model_repo as _mmr
            market_model_repo = _mmr
        if event_study_repo is None:
            from storage import event_study_repo as _esr
            event_study_repo = _esr
        if statistical_repo is None:
            from storage import statistical_repo as _sr
            statistical_repo = _sr
        if label_repo is None:
            from storage import label_repo as _lr
            label_repo = _lr
        if feature_repo is None:
            from storage import feature_repo as _fr
            feature_repo = _fr

        self._bill_repo = bill_repo
        self._knowledge_repo = knowledge_repo
        self._company_repo = company_repo
        self._mapping_repo = mapping_repo
        self._market_model_repo = market_model_repo
        self._event_study_repo = event_study_repo
        self._statistical_repo = statistical_repo
        self._label_repo = label_repo
        self._feature_repo = feature_repo

        logger.debug("FeatureEngineeringEngine initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, incremental: bool = True) -> FeatureBuildResult:
        """
        Build (or rebuild) the unified feature dataset.

        Parameters
        ----------
        incremental : bool
            If ``True`` (default), skip records whose ``record_id`` already
            exists in the feature repository (fast incremental update).
            If ``False``, rebuild every record from scratch.

        Returns
        -------
        FeatureBuildResult
            Summary of the build run.
        """
        start_ts = datetime.now(timezone.utc)
        result = FeatureBuildResult()

        logger.info(
            "FeatureEngineeringEngine.build() started | incremental=%s", incremental
        )

        # ------------------------------------------------------------------
        # Step 1 — load all label records (primary join key source)
        # ------------------------------------------------------------------
        label_records = self._label_repo.get_all()
        if not label_records:
            logger.warning(
                "No label records found — feature dataset will be empty."
            )
            result.build_duration_seconds = (
                datetime.now(timezone.utc) - start_ts
            ).total_seconds()
            return result

        logger.info("Loaded %d label records.", len(label_records))

        # ------------------------------------------------------------------
        # Step 2 — pre-load lookups (avoid N+1 queries)
        # ------------------------------------------------------------------
        existing_ids = self._feature_repo.get_existing_record_ids() if incremental else set()
        bills = {b.bill_id: b for b in self._bill_repo.get_all()}
        knowledge = {k.bill_id: k for k in self._knowledge_repo.get_all()}
        companies = {c.isin.upper(): c for c in self._company_repo.get_all()}

        logger.debug(
            "Pre-loaded: %d bills, %d knowledge records, %d companies",
            len(bills),
            len(knowledge),
            len(companies),
        )

        # ------------------------------------------------------------------
        # Step 3 — assemble one FeatureRecord per label
        # ------------------------------------------------------------------
        assembled: list[FeatureRecord] = []

        for label in label_records:
            record_id = make_record_id(
                label.bill_id, label.company, label.event_window
            )

            # Incremental skip
            if incremental and record_id in existing_ids:
                result.records_skipped += 1
                continue

            built_at = datetime.now(timezone.utc).isoformat()

            # Base record — start with the label fields
            rec = FeatureRecord(
                record_id=record_id,
                bill_id=label.bill_id,
                company_isin=label.company,
                event_window=label.event_window,
                isin=label.company,
                # Labels (always present by design — labels are the key source)
                direction=label.direction.value,
                market_moving=label.market_moving,
                impact_strength=label.impact_strength.value,
                confidence_label=label.confidence.value,
                built_at=built_at,
            )

            validation_errors: list[str] = []

            # ---- Legislative features (from Bill) ------------------------
            bill = bills.get(label.bill_id)
            if bill:
                rec.bill_title = bill.title
                rec.introduction_date = (
                    bill.introduction_date.isoformat()
                    if bill.introduction_date
                    else None
                )
                rec.ministry = bill.ministry
            else:
                logger.debug("Bill not found for label: %s", label.bill_id)
                validation_errors.append("missing_bill_record")

            # ---- Extended legislative features (from KnowledgeRecord) ---
            kr = knowledge.get(label.bill_id)
            if kr:
                rec.bill_type = kr.bill_type
                # Prefer KnowledgeRecord ministry if Bill has none
                if not rec.ministry:
                    rec.ministry = kr.ministry
                rec.department = kr.department
                rec.policy_domain = kr.policy_domain
                rec.economic_domain = kr.economic_domain
                rec.primary_sector = kr.primary_sector
                rec.secondary_sectors = list(kr.secondary_sectors)
                rec.regulatory_authority = kr.regulatory_authority
                rec.geographic_scope = kr.geographic_scope
            else:
                logger.debug("KnowledgeRecord not found for bill: %s", label.bill_id)
                validation_errors.append("missing_knowledge_record")

            # ---- Company features ----------------------------------------
            isin_upper = label.company.upper()
            company = companies.get(isin_upper)
            if company:
                rec.company_name = company.company_name
                rec.nse_symbol = company.ticker_nse
                rec.company_sector = company.sector
                rec.industry = company.industry
                rec.sub_industry = company.sub_industry
                rec.market_cap_category = company.market_cap_category.value
                rec.hq_state = company.hq_state
            else:
                logger.debug(
                    "Company not found for ISIN: %s", label.company
                )
                validation_errors.append("missing_company_record")

            # ---- Financial features (Market Model) -----------------------
            mm = self._market_model_repo.get(label.bill_id, label.company)
            if mm:
                rec.alpha = mm.alpha
                rec.beta = mm.beta
                rec.r_squared = mm.r_squared
                rec.residual_variance = mm.residual_variance
                rec.observation_count = mm.n_observations
            else:
                validation_errors.append("missing_market_model")

            # ---- Event Study features ------------------------------------
            es = self._event_study_repo.get(
                label.bill_id, label.company, label.event_window
            )
            if es:
                rec.final_car = es.final_car
                rec.avg_ar = es.avg_ar
                rec.max_ar = es.max_ar
                rec.min_ar = es.min_ar
                rec.peak_ar_day = es.peak_ar_day
                rec.peak_car_day = es.peak_car_day
            else:
                validation_errors.append("missing_event_study")

            # ---- Statistical features ------------------------------------
            stat = self._statistical_repo.get(
                label.bill_id, label.company, label.event_window
            )
            if stat:
                rec.t_statistic = stat.t_statistic
                rec.p_value = stat.p_value
                rec.significance_level = stat.confidence_level
                rec.significant_flag = stat.significant
                rec.effect_size = stat.effect_size
                if len(stat.confidence_interval) >= 2:
                    rec.confidence_interval_lower = stat.confidence_interval[0]
                    rec.confidence_interval_upper = stat.confidence_interval[1]
            else:
                validation_errors.append("missing_statistical_result")

            # ---- Validate the assembled record ---------------------------
            validation_report = self._validate(rec, validation_errors, built_at)

            if validation_report and validation_report.severity == "ERROR":
                result.records_rejected += 1
                result.validation_reports.append(validation_report)
                logger.warning(
                    "Rejected record %s: %s",
                    record_id,
                    validation_report.failed_checks,
                )
                continue

            if validation_report and validation_report.severity == "WARNING":
                result.validation_reports.append(validation_report)

            assembled.append(rec)

        # ------------------------------------------------------------------
        # Step 4 — persist to FeatureRepository
        # ------------------------------------------------------------------
        if assembled:
            total = self._feature_repo.save_many(assembled)
            result.records_written = len(assembled)
            result.total_in_dataset = total
        else:
            result.total_in_dataset = self._feature_repo.count()

        result.build_duration_seconds = (
            datetime.now(timezone.utc) - start_ts
        ).total_seconds()

        logger.info(
            "FeatureEngineeringEngine.build() complete | "
            "written=%d skipped=%d rejected=%d total=%d duration=%.2fs",
            result.records_written,
            result.records_skipped,
            result.records_rejected,
            result.total_in_dataset,
            result.build_duration_seconds,
        )

        return result

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(
        self,
        rec: FeatureRecord,
        upstream_errors: list[str],
        timestamp: str,
    ) -> Optional[FeatureValidationReport]:
        """
        Run all validation rules on an assembled FeatureRecord.

        Returns
        -------
        FeatureValidationReport or None
            ``None`` if the record passes all checks.
            A report with ``severity="ERROR"`` if it must be rejected.
            A report with ``severity="WARNING"`` if it is retained with caveats.
        """
        failed: list[str] = []

        # Rule 1 — Labels must be present (ERROR)
        if not rec.has_labels():
            if rec.direction is None:
                failed.append("missing_direction_label")
            if rec.market_moving is None:
                failed.append("missing_market_moving_label")
            if rec.impact_strength is None:
                failed.append("missing_impact_strength_label")
            if rec.confidence_label is None:
                failed.append("missing_confidence_label")

        # Rule 2 — NaN numerics in financial / stat fields (ERROR)
        numeric_fields = {
            "alpha": rec.alpha,
            "beta": rec.beta,
            "r_squared": rec.r_squared,
            "t_statistic": rec.t_statistic,
            "p_value": rec.p_value,
            "final_car": rec.final_car,
        }
        for name, val in numeric_fields.items():
            if val is not None and isinstance(val, float) and math.isnan(val):
                failed.append(f"nan_numeric_{name}")

        # Rule 3 — Upstream data gaps (WARNING — record still usable)
        warning_checks = [e for e in upstream_errors if e not in failed]
        if warning_checks:
            # Only escalate to ERROR if labels are also missing
            if failed:  # already has label errors → ERROR
                failed.extend(warning_checks)
            else:
                # warnings only → emit a WARNING report
                return FeatureValidationReport(
                    record_id=rec.record_id,
                    bill_id=rec.bill_id,
                    company_isin=rec.company_isin,
                    event_window=rec.event_window,
                    severity="WARNING",
                    failed_checks=warning_checks,
                    timestamp=timestamp,
                )

        if not failed:
            return None

        return FeatureValidationReport(
            record_id=rec.record_id,
            bill_id=rec.bill_id,
            company_isin=rec.company_isin,
            event_window=rec.event_window,
            severity="ERROR",
            failed_checks=failed,
            timestamp=timestamp,
        )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def rebuild(self) -> FeatureBuildResult:
        """Force a full rebuild (ignore existing records)."""
        return self.build(incremental=False)

    def export_csv(self):
        """Export the current feature dataset to CSV and return the path."""
        return self._feature_repo.export_csv()

    def dataset_info(self) -> dict:
        """Return metadata about the current feature dataset."""
        return self._feature_repo.dataset_info()
