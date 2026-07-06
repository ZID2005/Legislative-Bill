"""
validation/validator.py
=======================
Data validation module.

Validates all incoming data records before they are persisted or processed
downstream. Validation is the first gate in the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from config.logging_config import get_logger
from schemas.bill import Bill, BillHouse, BillStatus

logger = get_logger(__name__)


@dataclass
class ValidationReport:
    """
    Accumulates errors and warnings discovered during data validation.

    Attributes
    ----------
    errors : list[str]
        List of critical failures that make the record invalid/unusable.
    warnings : list[str]
        List of non-blocking issues (e.g. missing optional fields).
    """
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if there are zero validation errors."""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """Add a critical validation error."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a non-blocking validation warning."""
        self.warnings.append(message)

    def merge(self, other: ValidationReport) -> None:
        """Merge another validation report into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class Validator:
    """
    Data validation service for legislative bills, companies, and market data.
    """

    def validate_bill(self, bill: Any) -> ValidationReport:
        """
        Validate a Bill instance or a raw dictionary representing a bill.

        Parameters
        ----------
        bill : Bill or dict
            The bill record to validate.

        Returns
        -------
        ValidationReport
            The validation report containing errors and warnings.
        """
        report = ValidationReport()

        if isinstance(bill, dict):
            # Dict validation helper
            self._validate_bill_dict(bill, report)
        elif isinstance(bill, Bill):
            self._validate_bill_object(bill, report)
        else:
            report.add_error(f"Invalid bill input type: {type(bill).__name__}. Expected Bill object or dict.")

        if not report.is_valid:
            logger.error("Validation failed for bill. Errors: %s", report.errors)
        elif report.warnings:
            logger.warning("Validation completed with warnings for bill. Warnings: %s", report.warnings)

        return report

    def _validate_bill_dict(self, data: dict[str, Any], report: ValidationReport) -> None:
        """Helper to validate raw bill dictionary."""
        required_fields = ["bill_id", "title", "year", "ministry", "house", "status", "url"]
        for field_name in required_fields:
            if field_name not in data or data[field_name] is None:
                report.add_error(f"Missing required field: '{field_name}'")
            elif isinstance(data[field_name], str) and not data[field_name].strip():
                report.add_error(f"Required field '{field_name}' is empty")

        # Year validation
        if "year" in data and data["year"] is not None:
            try:
                year_val = int(data["year"])
                current_year = date.today().year
                if not (1947 <= year_val <= current_year + 1):
                    report.add_error(f"Invalid year: {year_val}. Must be between 1947 and {current_year + 1}.")
            except (ValueError, TypeError):
                report.add_error(f"Field 'year' must be an integer: {data['year']}")

        # House validation
        if "house" in data and data["house"] is not None:
            house_val = data["house"]
            if house_val not in [h.value for h in BillHouse]:
                report.add_error(f"Invalid house: '{house_val}'. Must be one of {[h.value for h in BillHouse]}")

        # Status validation
        if "status" in data and data["status"] is not None:
            status_val = data["status"]
            if status_val not in [s.value for s in BillStatus]:
                report.add_error(f"Invalid status: '{status_val}'. Must be one of {[s.value for s in BillStatus]}")

        # URL validation
        if "url" in data and data["url"] is not None:
            url_val = str(data["url"])
            if not url_val.startswith("https://") and not url_val.startswith("http://"):
                report.add_error(f"Malformed URL: '{url_val}'. Must start with http:// or https://")

        # Warnings for missing optional but recommended fields
        if not data.get("bill_number"):
            report.add_warning("Missing recommended field: 'bill_number'")
        if not data.get("pdf_path"):
            report.add_warning("Missing optional field: 'pdf_path'")
        if not data.get("full_text"):
            report.add_warning("Missing optional field: 'full_text'")

    def _validate_bill_object(self, bill: Bill, report: ValidationReport) -> None:
        """Helper to validate a Bill domain object."""
        # Check required fields
        if not bill.bill_id or not bill.bill_id.strip():
            report.add_error("Required field 'bill_id' is empty")
        if not bill.title or not bill.title.strip():
            report.add_error("Required field 'title' is empty")
        if not bill.ministry or not bill.ministry.strip():
            report.add_error("Required field 'ministry' is empty")
        if not bill.url or not bill.url.strip():
            report.add_error("Required field 'url' is empty")
        else:
            if not bill.url.startswith("https://") and not bill.url.startswith("http://"):
                report.add_error(f"Malformed URL: '{bill.url}'. Must start with http:// or https://")

        # Year validation
        current_year = date.today().year
        if not (1947 <= bill.year <= current_year + 1):
            report.add_error(f"Invalid year: {bill.year}. Must be between 1947 and {current_year + 1}.")

        # Enums validation (since dataclass holds enum type, we verify types)
        if not isinstance(bill.house, BillHouse):
            report.add_error(f"Invalid house type: {type(bill.house).__name__}. Expected BillHouse Enum.")
        if not isinstance(bill.status, BillStatus):
            report.add_error(f"Invalid status type: {type(bill.status).__name__}. Expected BillStatus Enum.")

        # Date fields type checks
        for date_field in ["introduction_date", "assent_date", "gazette_date", "ingested_at"]:
            val = getattr(bill, date_field)
            if val is not None and not isinstance(val, date):
                report.add_error(f"Field '{date_field}' must be a datetime.date object. Got {type(val).__name__}.")

        # Warnings
        if not bill.bill_number:
            report.add_warning("Missing recommended field: 'bill_number'")
        if not bill.pdf_path:
            report.add_warning("Missing optional field: 'pdf_path'")
        if not bill.full_text:
            report.add_warning("Missing optional field: 'full_text'")

    def validate_company(self, record: dict) -> ValidationReport:
        """Placeholder for company validation."""
        # Implemented in Task 3. For now, basic placeholder.
        report = ValidationReport()
        if not record.get("isin"):
            report.add_error("Missing required company field: 'isin'")
        return report

    def validate_market_df(self, df: Any) -> ValidationReport:
        """Placeholder for market data validation."""
        # Implemented in Task 3. For now, basic placeholder.
        report = ValidationReport()
        return report
