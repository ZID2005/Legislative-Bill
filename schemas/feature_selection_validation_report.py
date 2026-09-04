"""
schemas/feature_selection_validation_report.py
==============================================
Data model for validation reports produced by the Feature Selection Engine (Task 5.4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeatureSelectionValidationReport:
    """
    Audit record for validation checks performed on a selected features dataset.

    Attributes
    ----------
    mode : str
        The fusion mode (e.g. 'structured', 'hybrid').
    timestamp : str
        ISO-8601 UTC timestamp of validation.
    success : bool
        Whether validation passed (no errors).
    no_duplicate_columns : bool
        True if check passed (no duplicate features in selected columns).
    no_nan_only_columns : bool
        True if check passed (no columns containing only NaN).
    selected_features_exist : bool
        True if check passed (at least one feature column was selected).
    ranking_generated : bool
        True if check passed (feature importance ranking was generated successfully).
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
    no_duplicate_columns: bool = False
    no_nan_only_columns: bool = False
    selected_features_exist: bool = False
    ranking_generated: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the validation report to a JSON-compatible dictionary."""
        return {
            "mode": self.mode,
            "timestamp": self.timestamp,
            "success": self.success,
            "no_duplicate_columns": self.no_duplicate_columns,
            "no_nan_only_columns": self.no_nan_only_columns,
            "selected_features_exist": self.selected_features_exist,
            "ranking_generated": self.ranking_generated,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureSelectionValidationReport:
        """Deserialise the validation report from a dictionary."""
        return cls(
            mode=data["mode"],
            timestamp=data["timestamp"],
            success=data["success"],
            no_duplicate_columns=data.get("no_duplicate_columns", False),
            no_nan_only_columns=data.get("no_nan_only_columns", False),
            selected_features_exist=data.get("selected_features_exist", False),
            ranking_generated=data.get("ranking_generated", False),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            details=data.get("details", {}),
        )

    def __repr__(self) -> str:
        return (
            f"<FeatureSelectionValidationReport mode={self.mode!r} "
            f"success={self.success} "
            f"errors={len(self.errors)} "
            f"warnings={len(self.warnings)}>"
        )
