"""
reporting/engine.py
====================
Master orchestrator for the Stakeholder Reporting & Presentation Layer (Task 7.3).

Coordinates:
1. Retrieval of DecisionSupportRecord outputs from DecisionRepository.
2. Optional enrichment from BillRepository, CompanyRepository, MappingRepository,
   and ExplainabilityRepository.
3. Construction of StakeholderReport via InvestorReporter, BusinessReporter,
   or PublicReporter.
4. Aggregation via BillAggregator and CompanyAggregator.
5. Validation via ReportValidator.
6. Persistence via ReportRepository.
7. Incremental execution: skips regeneration if decision_version unchanged
   unless force_refresh is True.

Zero-Modification Guarantee
----------------------------
This engine reads DecisionSupportRecord outputs only.
It does NOT:
- Modify predictions
- Recompute risk scores
- Retrain models
- Generate new event studies
- Access post-event market prices
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from reporting.bill_aggregator import BillAggregator
from reporting.business_reporter import BusinessReporter
from reporting.company_aggregator import CompanyAggregator
from reporting.formatter import ReportFormatter
from reporting.investor_reporter import InvestorReporter
from reporting.public_reporter import PublicReporter
from reporting.validator import ReportValidator
from schemas.bill import Bill
from schemas.company import Company
from schemas.decision import DecisionSupportRecord
from schemas.report import (
    REPORT_VERSION,
    BillLevelReport,
    CompanyLevelReport,
    ReportFormat,
    StakeholderReport,
    StakeholderType,
)
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.decision_repository import DecisionRepository
from storage.mapping_repository import MappingRepository
from storage.report_repository import ReportRepository

logger = get_logger(__name__)


class ReportingEngine:
    """
    Master orchestrator for the Stakeholder Reporting & Presentation Layer.

    Parameters
    ----------
    decision_repo : DecisionRepository, optional
    bill_repo : BillRepository, optional
    company_repo : CompanyRepository, optional
    mapping_repo : MappingRepository, optional
    report_repo : ReportRepository, optional
    explainability_repo : ExplainabilityRepository, optional
        If provided, top SHAP features are used for investor key_factors.
    report_version : str
    """

    def __init__(
        self,
        decision_repo: Optional[DecisionRepository] = None,
        bill_repo: Optional[BillRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        mapping_repo: Optional[MappingRepository] = None,
        report_repo: Optional[ReportRepository] = None,
        explainability_repo: Any = None,
        report_version: str = REPORT_VERSION,
    ) -> None:
        self.decision_repo = decision_repo or DecisionRepository()
        self.bill_repo = bill_repo or BillRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.mapping_repo = mapping_repo or MappingRepository()
        self.report_repo = report_repo or ReportRepository()
        self.explainability_repo = explainability_repo  # Optional; may be None

        self._report_version = report_version
        self._investor_reporter = InvestorReporter(report_version)
        self._business_reporter = BusinessReporter(report_version)
        self._public_reporter = PublicReporter(report_version)
        self._bill_aggregator = BillAggregator(report_version)
        self._company_aggregator = CompanyAggregator(report_version)
        self._validator = ReportValidator(report_version)
        self._formatter = ReportFormatter()

        logger.debug("ReportingEngine initialised (version=%s).", report_version)

    # ------------------------------------------------------------------
    # Public API: bulk generation
    # ------------------------------------------------------------------

    def generate_all(
        self,
        bill_id_filter: Optional[str] = None,
        company_isin_filter: Optional[str] = None,
        stakeholder_filter: Optional[str] = None,
        event_window_filter: Optional[str] = None,
        output_format: str = ReportFormat.JSON.value,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Generate reports for all matching DecisionSupportRecords.

        Parameters
        ----------
        bill_id_filter : str, optional
        company_isin_filter : str, optional
        stakeholder_filter : str, optional
            One of INVESTOR / BUSINESS / PUBLIC. If None, generates all three.
        event_window_filter : str, optional
        output_format : str
        force_refresh : bool

        Returns
        -------
        dict with stats and list of generated StakeholderReport objects.
        """
        # Load all decision records
        all_decisions = self.decision_repo.load_all()
        logger.info("Loaded %d decision records.", len(all_decisions))

        # Apply filters
        candidates = self._filter_decisions(
            all_decisions,
            bill_id_filter,
            company_isin_filter,
            event_window_filter,
        )
        logger.info("Filtered to %d candidate decision records.", len(candidates))

        # Determine which stakeholder types to generate
        stakeholder_types = self._resolve_stakeholder_types(stakeholder_filter)

        stats: dict[str, Any] = {
            "total_candidates": len(candidates),
            "stakeholder_types": [s.value for s in stakeholder_types],
            "reports_generated": 0,
            "reports_skipped": 0,
            "reports_failed": 0,
            "validation_failures": 0,
            "reports": [],
        }

        # Metadata caches
        bill_cache: dict[str, Optional[Bill]] = {}
        company_cache: dict[str, Optional[Company]] = {}
        top_factors_cache: dict[str, list[str]] = {}

        for idx, decision in enumerate(candidates, start=1):
            # Load metadata (cached)
            bill = self._get_bill(decision.bill_id, bill_cache)
            company = self._get_company(decision.company_isin, company_cache)
            top_factors = self._get_top_factors(
                decision.company_isin, top_factors_cache
            )

            for stype in stakeholder_types:
                result = self._generate_single(
                    decision=decision,
                    stakeholder_type=stype,
                    bill=bill,
                    company=company,
                    top_factors=top_factors,
                    output_format=output_format,
                    force_refresh=force_refresh,
                )
                if result == "SKIPPED":
                    stats["reports_skipped"] += 1
                elif result is None:
                    stats["reports_failed"] += 1
                    stats["validation_failures"] += 1
                else:
                    stats["reports_generated"] += 1
                    stats["reports"].append(result)

            if idx % 50 == 0 or idx == len(candidates):
                logger.info("Processed report candidate %d/%d.", idx, len(candidates))

        logger.info(
            "ReportingEngine.generate_all complete: generated=%d skipped=%d failed=%d",
            stats["reports_generated"],
            stats["reports_skipped"],
            stats["reports_failed"],
        )
        return stats

    # ------------------------------------------------------------------
    # Public API: single report
    # ------------------------------------------------------------------

    def generate_for_decision(
        self,
        decision: DecisionSupportRecord,
        stakeholder_type: StakeholderType,
        output_format: str = ReportFormat.JSON.value,
        force_refresh: bool = False,
    ) -> Optional[StakeholderReport]:
        """
        Generate a single StakeholderReport for a given decision record.

        Returns the report if generated, or None on validation failure.
        """
        bill = self._get_bill(decision.bill_id, {})
        company = self._get_company(decision.company_isin, {})
        top_factors = self._get_top_factors(decision.company_isin, {})
        result = self._generate_single(
            decision, stakeholder_type, bill, company, top_factors,
            output_format, force_refresh
        )
        if isinstance(result, StakeholderReport):
            return result
        return None

    # ------------------------------------------------------------------
    # Public API: bill-level aggregate
    # ------------------------------------------------------------------

    def generate_bill_report(
        self,
        bill_id: str,
        event_window: str = "",
        output_format: str = ReportFormat.JSON.value,
    ) -> BillLevelReport:
        """
        Generate a BillLevelReport aggregating all companies for a bill.
        """
        records = self.decision_repo.get_by_bill(bill_id)
        bill = self._get_bill(bill_id, {})
        report = self._bill_aggregator.build(bill_id, records, bill, event_window)
        self.report_repo.save_bill_report(report)
        logger.info(
            "Generated BillLevelReport for bill_id=%s (%d companies).",
            bill_id, report.total_companies
        )
        return report

    # ------------------------------------------------------------------
    # Public API: company-level aggregate
    # ------------------------------------------------------------------

    def generate_company_report(
        self,
        company_isin: str,
        output_format: str = ReportFormat.JSON.value,
    ) -> CompanyLevelReport:
        """
        Generate a CompanyLevelReport aggregating all bills for a company.
        """
        records = self.decision_repo.get_by_company(company_isin)
        company = self._get_company(company_isin, {})
        report = self._company_aggregator.build(company_isin, records, company)
        self.report_repo.save_company_report(report)
        logger.info(
            "Generated CompanyLevelReport for company_isin=%s (%d bills).",
            company_isin, report.total_bills
        )
        return report

    # ------------------------------------------------------------------
    # Format helpers
    # ------------------------------------------------------------------

    def format_report(self, report: Any, output_format: str) -> str:
        """Format a report object to the requested string format."""
        fmt = output_format.upper()
        if fmt == ReportFormat.JSON.value:
            return self._formatter.to_json(report)
        elif fmt == ReportFormat.MARKDOWN.value:
            return self._formatter.to_markdown(report)
        elif fmt == ReportFormat.CSV.value:
            return self._formatter.to_csv_summary([report])
        else:
            logger.warning("Unknown format '%s', falling back to JSON.", output_format)
            return self._formatter.to_json(report)

    # ------------------------------------------------------------------
    # Internal: single report generation
    # ------------------------------------------------------------------

    def _generate_single(
        self,
        decision: DecisionSupportRecord,
        stakeholder_type: StakeholderType,
        bill: Optional[Bill],
        company: Optional[Company],
        top_factors: Optional[list[str]],
        output_format: str,
        force_refresh: bool,
    ) -> Any:
        """
        Generate one StakeholderReport. Returns:
        - StakeholderReport  on success
        - "SKIPPED"          if incremental check passes (decision_version unchanged)
        - None               on validation failure
        """
        # Incremental check
        if not force_refresh and self.report_repo.exists(
            decision.bill_id, decision.company_isin,
            decision.event_window, stakeholder_type.value
        ):
            existing = self.report_repo.get_by_key(
                decision.bill_id, decision.company_isin,
                decision.event_window, stakeholder_type.value
            )
            if existing is not None and existing.decision_version == decision.decision_version:
                logger.debug(
                    "Skipping %s report for (%s, %s) — decision_version unchanged.",
                    stakeholder_type.value, decision.bill_id, decision.company_isin,
                )
                return "SKIPPED"

        # Build report
        try:
            if stakeholder_type == StakeholderType.INVESTOR:
                mapping = self._get_mapping(decision.bill_id)
                report = self._investor_reporter.build(
                    decision, bill, company, top_factors
                )
            elif stakeholder_type == StakeholderType.BUSINESS:
                mapping = self._get_mapping(decision.bill_id)
                report = self._business_reporter.build(
                    decision, bill, company, mapping
                )
            else:  # PUBLIC
                report = self._public_reporter.build(decision, bill, company)
        except Exception as exc:
            logger.error(
                "Failed to build %s report for (%s, %s): %s",
                stakeholder_type.value, decision.bill_id, decision.company_isin, exc,
                exc_info=True,
            )
            return None

        # Validate
        val_report = self._validator.validate(report)
        self.report_repo.save_validation_report(val_report)

        if not val_report.is_valid:
            logger.warning(
                "Validation failed for %s report (%s, %s): %s",
                stakeholder_type.value, decision.bill_id, decision.company_isin,
                val_report.errors,
            )
            return None

        # Persist
        self.report_repo.save(report)
        return report

    # ------------------------------------------------------------------
    # Internal: metadata helpers
    # ------------------------------------------------------------------

    def _filter_decisions(
        self,
        decisions: list[DecisionSupportRecord],
        bill_id_filter: Optional[str],
        company_isin_filter: Optional[str],
        event_window_filter: Optional[str],
    ) -> list[DecisionSupportRecord]:
        result = []
        for d in decisions:
            if bill_id_filter and d.bill_id != bill_id_filter:
                continue
            if company_isin_filter and d.company_isin != company_isin_filter:
                continue
            if event_window_filter and d.event_window != event_window_filter:
                continue
            result.append(d)
        return result

    def _resolve_stakeholder_types(
        self, stakeholder_filter: Optional[str]
    ) -> list[StakeholderType]:
        if stakeholder_filter:
            try:
                return [StakeholderType(stakeholder_filter.upper())]
            except ValueError:
                logger.warning(
                    "Unknown stakeholder_filter '%s'; generating all types.",
                    stakeholder_filter,
                )
        return list(StakeholderType)

    def _get_bill(
        self, bill_id: str, cache: dict[str, Optional[Bill]]
    ) -> Optional[Bill]:
        if bill_id not in cache:
            try:
                cache[bill_id] = self.bill_repo.get(bill_id)
            except Exception as exc:
                logger.warning("Could not load bill %s: %s", bill_id, exc)
                cache[bill_id] = None
        return cache[bill_id]

    def _get_company(
        self, company_isin: str, cache: dict[str, Optional[Company]]
    ) -> Optional[Company]:
        if company_isin not in cache:
            try:
                if hasattr(self.company_repo, "get_by_isin"):
                    cache[company_isin] = self.company_repo.get_by_isin(company_isin)
                else:
                    cache[company_isin] = getattr(
                        self.company_repo, "get", lambda _: None
                    )(company_isin)
            except Exception as exc:
                logger.warning("Could not load company %s: %s", company_isin, exc)
                cache[company_isin] = None
        return cache[company_isin]

    def _get_mapping(self, bill_id: str) -> Any:
        try:
            return self.mapping_repo.get(bill_id)
        except Exception as exc:
            logger.debug("Could not load mapping for %s: %s", bill_id, exc)
            return None

    def _get_top_factors(
        self, company_isin: str, cache: dict[str, list[str]]
    ) -> Optional[list[str]]:
        """Attempt to load top SHAP features from ExplainabilityRepository."""
        if self.explainability_repo is None:
            return None
        if company_isin in cache:
            return cache[company_isin]

        try:
            summary = self.explainability_repo.load_global_summary()
            top_features = [
                entry.get("feature", "")
                for entry in summary.get("top_features", [])[:10]
                if entry.get("feature")
            ]
            cache[company_isin] = top_features or None
            return cache[company_isin]
        except Exception:
            cache[company_isin] = None
            return None
