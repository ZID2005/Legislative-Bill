"""
dashboard package
=================
Legislative Intelligence & Market Impact Decision-Support Dashboard.

Task 7.4.1: Added DashboardService, BillSummary, ProductionScope for the
Newly Arrived Bills feed and production-scope foundation.

Provides an institutional, interactive multi-stakeholder interface for
legislative impact analysis, model explainability, and historical backtest verification.
"""

from __future__ import annotations

from dashboard.dashboard import run_dashboard
from dashboard.filters.filter_engine import FilterEngine
from dashboard.services.dashboard_service import BillSummary, DashboardService, ProductionScope
from dashboard.services.data_service import DashboardDataService
from dashboard.services.scope_service import ScopeDiagnostic, ScopeService

__all__ = [
    "BillSummary",
    "DashboardDataService",
    "DashboardService",
    "FilterEngine",
    "ProductionScope",
    "ScopeDiagnostic",
    "ScopeService",
    "run_dashboard",
]
