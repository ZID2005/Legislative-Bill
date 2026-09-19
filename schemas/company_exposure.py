"""
schemas/company_exposure.py
===========================
Unified data models for Evidence-Based Company Exposure Intelligence across
Central Government and Indian State legislative bills.

Re-exports core classes from schemas.state_corporate_exposure while providing
jurisdiction-agnostic naming and utilities for corporate exposure analysis.
"""

from __future__ import annotations

from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StatePresenceRecord,
    StateCorporateExposure,
    CompanyExposureRecord,
    _FORBIDDEN_PREDICTIVE_TERMS,
)

__all__ = [
    "CorporateExposureEvidence",
    "StatePresenceRecord",
    "StateCorporateExposure",
    "CompanyExposureRecord",
    "_FORBIDDEN_PREDICTIVE_TERMS",
]
