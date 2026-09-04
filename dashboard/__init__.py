"""
dashboard package
=================
Legislative Intelligence & Market Impact Decision-Support Dashboard — Task 7.4.

Provides an institutional, interactive multi-stakeholder interface (Investor,
Business, Public) for legislative impact analysis, model explainability,
and historical backtest verification.
"""

from __future__ import annotations

from dashboard.dashboard import run_dashboard
from dashboard.filters.filter_engine import FilterEngine
from dashboard.services.data_service import DashboardDataService
from dashboard.services.scope_service import ScopeDiagnostic, ScopeService

__all__ = [
    "DashboardDataService",
    "FilterEngine",
    "ScopeDiagnostic",
    "ScopeService",
    "run_dashboard",
]
