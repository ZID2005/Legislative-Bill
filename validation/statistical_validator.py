"""
validation/statistical_validator.py
===================================
Validator for verifying statistical significance calculations and inputs.
"""

from __future__ import annotations

import math
from typing import Optional

from validation.validator import ValidationReport


class StatisticalValidator:
    """
    Validation logic for checking statistical significance parameters.
    """

    def validate_calculation(
        self,
        car: Optional[float],
        variance: Optional[float],
        standard_error: Optional[float],
        df: Optional[int],
    ) -> ValidationReport:
        """
        Validate statistical significance inputs.
        Rejects calculation if CAR is missing, variance is invalid (negative, NaN, inf, or None),
        standard error is zero/negative, or degrees of freedom is <= 0.
        """
        report = ValidationReport()

        # 1. CAR missing
        if car is None:
            report.add_error("CAR is missing.")
        elif math.isnan(car) or math.isinf(car):
            report.add_error(f"CAR is invalid: {car}")

        # 2. Variance invalid
        if variance is None:
            report.add_error("Variance is missing.")
        elif math.isnan(variance) or math.isinf(variance) or variance < 0:
            report.add_error(f"Variance is invalid: {variance}")

        # 3. Standard Error equals zero
        if standard_error is None:
            report.add_error("Standard Error is missing.")
        elif math.isnan(standard_error) or math.isinf(standard_error):
            report.add_error(f"Standard Error is invalid: {standard_error}")
        elif standard_error == 0.0:
            report.add_error("Standard Error equals zero.")
        elif standard_error < 0.0:
            report.add_error(f"Standard Error is invalid (negative): {standard_error}")

        # 4. Degrees of freedom invalid
        if df is None:
            report.add_error("Degrees of freedom is missing.")
        elif df <= 0:
            report.add_error(f"Degrees of freedom is invalid: {df}. Must be greater than zero.")

        return report
