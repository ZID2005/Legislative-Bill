"""
storage/report_repository.py
=============================
ReportRepository — persistence layer for stakeholder reports (Task 7.3).

Manages storage, retrieval, and querying of StakeholderReport,
BillLevelReport, CompanyLevelReport, and ReportValidationReport
artefacts within ``data/reports/``.

Storage Structure
-----------------
::

    data/reports/
        investor/
            rpt_<bill>_<isin>_<window>_investor.json
        business/
            rpt_<bill>_<isin>_<window>_business.json
        public/
            rpt_<bill>_<isin>_<window>_public.json
        bill_reports/
            bill_rpt_<bill_id>.json
        company_reports/
            co_rpt_<isin>.json
        validation/
            val_rpt_<report_id>.json

Deterministic Filenames & IDs
------------------------------
Report IDs and filenames are generated deterministically from
(bill_id, company_isin, event_window, stakeholder_type) using
``make_report_id()`` from ``schemas.report``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.report import (
    BillLevelReport,
    CompanyLevelReport,
    ReportValidationReport,
    StakeholderReport,
    StakeholderType,
    make_report_id,
)
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)

# Stakeholder type → subdirectory name
_STAKEHOLDER_SUBDIRS: dict[str, str] = {
    StakeholderType.INVESTOR.value: "investor",
    StakeholderType.BUSINESS.value: "business",
    StakeholderType.PUBLIC.value: "public",
}


class ReportRepository:
    """
    Persistence layer for stakeholder reports.

    Parameters
    ----------
    reports_dir : Path, optional
        Root directory for reports. Defaults to ``settings.REPORTS_DIR``.
    """

    def __init__(self, reports_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._root: Path = reports_dir or settings.REPORTS_DIR

        # Sub-directories
        self._investor_dir: Path = self._root / "investor"
        self._business_dir: Path = self._root / "business"
        self._public_dir: Path = self._root / "public"
        self._bill_reports_dir: Path = self._root / "bill_reports"
        self._company_reports_dir: Path = self._root / "company_reports"
        self._validation_dir: Path = self._root / "validation"

        for d in [
            self._root,
            self._investor_dir,
            self._business_dir,
            self._public_dir,
            self._bill_reports_dir,
            self._company_reports_dir,
            self._validation_dir,
        ]:
            ensure_dir(d)

        logger.debug("ReportRepository initialised | root=%s", self._root)

    # ------------------------------------------------------------------
    # Path resolution
    # ------------------------------------------------------------------

    def _stakeholder_dir(self, stakeholder_type: str) -> Path:
        """Return the correct sub-directory for a stakeholder type."""
        subdir = _STAKEHOLDER_SUBDIRS.get(stakeholder_type.upper(), "unknown")
        return self._root / subdir

    def _report_path(self, report_id: str, stakeholder_type: str) -> Path:
        """Return the JSON filepath for a given report ID."""
        d = self._stakeholder_dir(stakeholder_type)
        return d / f"{report_id}.json"

    def _bill_report_path(self, report_id: str) -> Path:
        return self._bill_reports_dir / f"{report_id}.json"

    def _company_report_path(self, report_id: str) -> Path:
        return self._company_reports_dir / f"{report_id}.json"

    def _validation_path(self, validation_id: str) -> Path:
        return self._validation_dir / f"{validation_id}.json"

    # ------------------------------------------------------------------
    # CRUD: StakeholderReport
    # ------------------------------------------------------------------

    def save(self, report: StakeholderReport) -> Path:
        """
        Persist a StakeholderReport to disk.

        Returns
        -------
        Path
            Absolute path to the saved JSON file.
        """
        path = self._report_path(report.report_id, report.stakeholder_type)
        try:
            save_json(report.to_dict(), path)
            logger.debug("Saved StakeholderReport: %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to save report %s: %s", report.report_id, exc)
            raise

    def save_many(self, reports: list[StakeholderReport]) -> list[Path]:
        """Persist a list of StakeholderReport objects."""
        saved: list[Path] = []
        for r in reports:
            saved.append(self.save(r))
        logger.info("Saved %d StakeholderReports to %s", len(saved), self._root)
        return saved

    def get(self, report_id: str, stakeholder_type: str) -> Optional[StakeholderReport]:
        """Retrieve a StakeholderReport by ID and stakeholder type."""
        path = self._report_path(report_id, stakeholder_type)
        if not file_exists(path):
            return None
        try:
            data = load_json(path)
            return StakeholderReport.from_dict(data)
        except Exception as exc:
            logger.warning("Error loading report %s: %s", path, exc)
            return None

    def get_by_key(
        self,
        bill_id: str,
        company_isin: str,
        event_window: str,
        stakeholder_type: str,
    ) -> Optional[StakeholderReport]:
        """Retrieve a StakeholderReport by composite key."""
        report_id = make_report_id(bill_id, company_isin, event_window, stakeholder_type)
        return self.get(report_id, stakeholder_type)

    def exists(
        self,
        bill_id: str,
        company_isin: str,
        event_window: str,
        stakeholder_type: str,
    ) -> bool:
        """Check whether a report exists for the given composite key."""
        report_id = make_report_id(bill_id, company_isin, event_window, stakeholder_type)
        return file_exists(self._report_path(report_id, stakeholder_type))

    def get_by_bill(
        self, bill_id: str, stakeholder_type: Optional[str] = None
    ) -> list[StakeholderReport]:
        """
        Retrieve all StakeholderReports for a specific bill_id.

        Optionally filter by stakeholder_type.
        """
        all_reports = self.load_all(stakeholder_type=stakeholder_type)
        return [r for r in all_reports if r.bill_id == bill_id]

    def get_by_company(
        self, company_isin: str, stakeholder_type: Optional[str] = None
    ) -> list[StakeholderReport]:
        """
        Retrieve all StakeholderReports for a specific company ISIN.

        Optionally filter by stakeholder_type.
        """
        all_reports = self.load_all(stakeholder_type=stakeholder_type)
        return [r for r in all_reports if r.company_isin == company_isin]

    def load_all(
        self, stakeholder_type: Optional[str] = None
    ) -> list[StakeholderReport]:
        """
        Load all stored StakeholderReport objects.

        Parameters
        ----------
        stakeholder_type : str, optional
            If provided, load only from that stakeholder sub-directory.
        """
        reports: list[StakeholderReport] = []

        if stakeholder_type:
            dirs_to_scan = [self._stakeholder_dir(stakeholder_type)]
        else:
            dirs_to_scan = [
                self._investor_dir,
                self._business_dir,
                self._public_dir,
            ]

        for d in dirs_to_scan:
            if not d.is_dir():
                continue
            for filepath in list_files(d, pattern="rpt_*.json"):
                try:
                    data = load_json(filepath)
                    reports.append(StakeholderReport.from_dict(data))
                except Exception as exc:
                    logger.warning("Failed to load report %s: %s", filepath, exc)

        return reports

    # ------------------------------------------------------------------
    # CRUD: BillLevelReport
    # ------------------------------------------------------------------

    def save_bill_report(self, report: BillLevelReport) -> Path:
        """Persist a BillLevelReport."""
        path = self._bill_report_path(report.report_id)
        try:
            save_json(report.to_dict(), path)
            logger.debug("Saved BillLevelReport: %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to save bill report %s: %s", report.report_id, exc)
            raise

    def get_bill_report(self, report_id: str) -> Optional[BillLevelReport]:
        """Retrieve a BillLevelReport by report_id."""
        path = self._bill_report_path(report_id)
        if not file_exists(path):
            return None
        try:
            data = load_json(path)
            return BillLevelReport.from_dict(data)
        except Exception as exc:
            logger.warning("Error loading bill report %s: %s", path, exc)
            return None

    def load_all_bill_reports(self) -> list[BillLevelReport]:
        """Load all stored BillLevelReport objects."""
        reports: list[BillLevelReport] = []
        for filepath in list_files(self._bill_reports_dir, pattern="bill_rpt_*.json"):
            try:
                data = load_json(filepath)
                reports.append(BillLevelReport.from_dict(data))
            except Exception as exc:
                logger.warning("Failed to load bill report %s: %s", filepath, exc)
        return reports

    # ------------------------------------------------------------------
    # CRUD: CompanyLevelReport
    # ------------------------------------------------------------------

    def save_company_report(self, report: CompanyLevelReport) -> Path:
        """Persist a CompanyLevelReport."""
        path = self._company_report_path(report.report_id)
        try:
            save_json(report.to_dict(), path)
            logger.debug("Saved CompanyLevelReport: %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to save company report %s: %s", report.report_id, exc)
            raise

    def get_company_report(self, report_id: str) -> Optional[CompanyLevelReport]:
        """Retrieve a CompanyLevelReport by report_id."""
        path = self._company_report_path(report_id)
        if not file_exists(path):
            return None
        try:
            data = load_json(path)
            return CompanyLevelReport.from_dict(data)
        except Exception as exc:
            logger.warning("Error loading company report %s: %s", path, exc)
            return None

    def load_all_company_reports(self) -> list[CompanyLevelReport]:
        """Load all stored CompanyLevelReport objects."""
        reports: list[CompanyLevelReport] = []
        for filepath in list_files(self._company_reports_dir, pattern="co_rpt_*.json"):
            try:
                data = load_json(filepath)
                reports.append(CompanyLevelReport.from_dict(data))
            except Exception as exc:
                logger.warning("Failed to load company report %s: %s", filepath, exc)
        return reports

    # ------------------------------------------------------------------
    # CRUD: ReportValidationReport
    # ------------------------------------------------------------------

    def save_validation_report(self, report: ReportValidationReport) -> Path:
        """Persist a ReportValidationReport."""
        path = self._validation_path(report.validation_id)
        try:
            save_json(report.to_dict(), path)
            logger.debug("Saved ReportValidationReport: %s", path)
            return path
        except Exception as exc:
            logger.error(
                "Failed to save validation report %s: %s", report.validation_id, exc
            )
            raise

    def load_all_validation_reports(self) -> list[ReportValidationReport]:
        """Load all stored ReportValidationReport objects."""
        reports: list[ReportValidationReport] = []
        for filepath in list_files(self._validation_dir, pattern="val_*.json"):
            try:
                data = load_json(filepath)
                reports.append(ReportValidationReport.from_dict(data))
            except Exception as exc:
                logger.warning("Failed to load validation report %s: %s", filepath, exc)
        return reports
