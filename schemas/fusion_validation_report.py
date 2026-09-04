"""
schemas/fusion_validation_report.py
====================================
Data model for validation reports produced by the Feature Fusion Engine (Task 5.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FusionValidationReport:
    """
    Audit record for validation checks performed on a fused dataset.

    Attributes
    ----------
    mode : str
        The fusion mode (e.g. 'structured', 'hybrid').
    timestamp : str
        ISO-8601 UTC timestamp of validation.
    success : bool
        Whether validation passed (no errors).
    duplicate_rows_count : int
        Number of duplicate bill-company-window rows.
    missing_embeddings_count : int
        Number of rows missing expected embeddings.
    nan_values_count : int
        Number of NaN/null values in key/embedding columns.
    mismatched_dimensions_count : int
        Number of rows with incorrect embedding size.
    mismatched_bill_ids_count : int
        Number of mismatched bills.
    mismatched_company_ids_count : int
        Number of mismatched companies.
    errors : list[str]
        List of validation error messages.
    warnings : list[str]
        List of non-blocking warnings.
    details : dict[str, Any]
        Optional detailed metrics or diagnostics.
    """

    mode: str
    timestamp: str
    success: bool
    duplicate_rows_count: int = 0
    missing_embeddings_count: int = 0
    nan_values_count: int = 0
    mismatched_dimensions_count: int = 0
    mismatched_bill_ids_count: int = 0
    mismatched_company_ids_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the validation report to a JSON-compatible dictionary."""
        return {
            "mode": self.mode,
            "timestamp": self.timestamp,
            "success": self.success,
            "duplicate_rows_count": self.duplicate_rows_count,
            "missing_embeddings_count": self.missing_embeddings_count,
            "nan_values_count": self.nan_values_count,
            "mismatched_dimensions_count": self.mismatched_dimensions_count,
            "mismatched_bill_ids_count": self.mismatched_bill_ids_count,
            "mismatched_company_ids_count": self.mismatched_company_ids_count,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FusionValidationReport:
        """Deserialise the validation report from a dictionary."""
        return cls(
            mode=data["mode"],
            timestamp=data["timestamp"],
            success=data["success"],
            duplicate_rows_count=data.get("duplicate_rows_count", 0),
            missing_embeddings_count=data.get("missing_embeddings_count", 0),
            nan_values_count=data.get("nan_values_count", 0),
            mismatched_dimensions_count=data.get("mismatched_dimensions_count", 0),
            mismatched_bill_ids_count=data.get("mismatched_bill_ids_count", 0),
            mismatched_company_ids_count=data.get("mismatched_company_ids_count", 0),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            details=data.get("details", {}),
        )

    def __repr__(self) -> str:
        return (
            f"<FusionValidationReport mode={self.mode!r} "
            f"success={self.success} "
            f"errors={len(self.errors)} "
            f"warnings={len(self.warnings)}>"
        )
