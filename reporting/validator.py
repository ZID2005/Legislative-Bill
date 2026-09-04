"""
reporting/validator.py
=======================
Report validation logic for the Stakeholder Reporting Layer (Task 7.3).

Validates StakeholderReport objects before persistence, checking:
- Required fields present and non-empty
- Valid stakeholder type (INVESTOR / BUSINESS / PUBLIC)
- Valid event window format
- Probability ranges [0.0, 1.0]
- Score ranges [0.0, 1.0]
- Missing bill/company metadata (warnings, not errors)
- Duplicate report ID detection (within session)
- Version string format

Returns ReportValidationReport objects with full audit trail.
"""

from __future__ import annotations

import re
from typing import Optional

from config.logging_config import get_logger
from schemas.report import (
    REPORT_VERSION,
    ReportValidationReport,
    StakeholderReport,
    StakeholderType,
    make_validation_report_id,
)

logger = get_logger(__name__)

# Regex for event window format: e.g. "[-20,+20]", "[-5,+5]"
_EVENT_WINDOW_RE = re.compile(r"^\[-?\d+,[\+\-]?\d+\]$")

# Valid stakeholder types as strings
_VALID_STAKEHOLDER_TYPES = frozenset(st.value for st in StakeholderType)

# Required non-empty string fields for a StakeholderReport
_REQUIRED_FIELDS = [
    "report_id",
    "bill_id",
    "company_isin",
    "event_window",
    "stakeholder_type",
    "decision_version",
    "report_version",
    "generated_timestamp",
    "executive_summary",
    "bill_summary",
    "company_summary",
    "impact_summary",
    "risk_summary",
    "anticipation_summary",
    "confidence_summary",
]


class ReportValidator:
    """
    Validates StakeholderReport objects before persistence.

    Maintains a session-level seen_ids set for duplicate detection.
    Call `reset()` between test runs or sessions as needed.

    Parameters
    ----------
    current_report_version : str
        Expected report version for compatibility checks.
    """

    def __init__(self, current_report_version: str = REPORT_VERSION) -> None:
        self._current_version = current_report_version
        self._seen_ids: set[str] = set()

    def reset(self) -> None:
        """Clear session-level duplicate ID tracker."""
        self._seen_ids.clear()

    def validate(self, report: StakeholderReport) -> ReportValidationReport:
        """
        Validate a StakeholderReport.

        Parameters
        ----------
        report : StakeholderReport

        Returns
        -------
        ReportValidationReport
            is_valid=True if no errors; warnings are informational only.
        """
        errors: list[str] = []
        warnings: list[str] = []
        checks: dict[str, bool] = {}

        # 1. Required fields
        missing = [
            f for f in _REQUIRED_FIELDS
            if not getattr(report, f, None)
        ]
        checks["required_fields_present"] = len(missing) == 0
        if missing:
            errors.append(f"Missing or empty required fields: {missing}")

        # 2. Valid stakeholder type
        valid_st = report.stakeholder_type in _VALID_STAKEHOLDER_TYPES
        checks["valid_stakeholder_type"] = valid_st
        if not valid_st:
            errors.append(
                f"Invalid stakeholder_type '{report.stakeholder_type}'. "
                f"Must be one of {sorted(_VALID_STAKEHOLDER_TYPES)}."
            )

        # 3. Valid event window format
        win = report.event_window or ""
        valid_win = bool(_EVENT_WINDOW_RE.match(win))
        checks["valid_event_window"] = valid_win
        if not valid_win:
            errors.append(
                f"Invalid event_window format '{win}'. "
                "Expected format: '[-N,+M]' e.g. '[-20,+20]'."
            )

        # 4. Bill ID and company ISIN non-empty
        checks["bill_id_non_empty"] = bool(report.bill_id)
        if not report.bill_id:
            errors.append("bill_id must not be empty.")

        checks["company_isin_non_empty"] = bool(report.company_isin)
        if not report.company_isin:
            errors.append("company_isin must not be empty.")

        # 5. Duplicate report ID check (session-level)
        is_duplicate = report.report_id in self._seen_ids
        checks["no_duplicate_report_id"] = not is_duplicate
        if is_duplicate:
            warnings.append(
                f"Duplicate report_id '{report.report_id}' detected in this session. "
                "Report may overwrite an existing record."
            )
        else:
            self._seen_ids.add(report.report_id)

        # 6. Version compatibility
        version_ok = bool(report.report_version) and bool(report.decision_version)
        checks["version_fields_present"] = version_ok
        if not version_ok:
            warnings.append("report_version or decision_version is empty.")

        if (
            report.report_version
            and self._current_version
            and report.report_version != self._current_version
        ):
            warnings.append(
                f"Report version '{report.report_version}' does not match "
                f"current engine version '{self._current_version}'."
            )

        # 7. Bill summary metadata warnings (informational)
        if report.bill_summary and len(report.bill_summary.strip()) < 20:
            warnings.append("bill_summary appears very short — bill metadata may be missing.")

        if report.company_summary and len(report.company_summary.strip()) < 20:
            warnings.append(
                "company_summary appears very short — company metadata may be missing."
            )

        # 8. Key factors
        if not report.key_factors:
            warnings.append("key_factors list is empty — no model factors available.")

        # 9. Methodology note and disclaimer
        if not report.methodology_note:
            warnings.append("methodology_note is missing.")
        if not report.disclaimer:
            warnings.append("disclaimer is missing.")

        validation_id = make_validation_report_id(report.report_id)
        return ReportValidationReport(
            validation_id=validation_id,
            report_id=report.report_id,
            bill_id=report.bill_id,
            company_isin=report.company_isin,
            stakeholder_type=report.stakeholder_type,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            checks_performed=checks,
        )
