"""
knowledge/company_exposure_engine.py
====================================
Unified Evidence-Based Company Exposure Intelligence Engine.

Evaluates candidate corporate entities against Central and State legislative bills
following the canonical 10-step conceptual chain:
    Bill -> Legislative Domain / Sector -> Business Activity -> Geographic / State Presence
         -> Company -> Evidence -> Exposure Type -> Exposure Strength -> Economic Mechanism -> Market Relevance.

Strictly qualitative exposure interpretation; zero financial predictions, return forecasts, or trading signals.
"""

from __future__ import annotations

from knowledge.state_corporate_exposure_engine import (
    StateCorporateExposureEngine,
    CompanyExposureEngine,
)

__all__ = [
    "StateCorporateExposureEngine",
    "CompanyExposureEngine",
]
