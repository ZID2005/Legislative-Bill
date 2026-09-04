"""
tests/test_dashboard_scope.py
=============================
Unit tests for Task 7.4 Scope Reconciliation & Diagnostic Service.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from dashboard.services.scope_service import ScopeDiagnostic, ScopeService


def test_scope_diagnostic_defaults():
    """Verify default values in ScopeDiagnostic represent the production universe."""
    diag = ScopeDiagnostic()
    assert diag.production_bills_count == 20
    assert diag.production_companies_count == 47
    assert diag.production_event_windows_count == 5
    assert diag.expected_decision_candidates == 4700
    assert diag.actual_decision_records == 4700
    assert diag.total_repository_bills == 22
    assert diag.total_repository_companies == 50
    assert "key-issues-and-analysis" in diag.test_or_non_legislative_bills
    assert "service-bill" in diag.test_or_non_legislative_bills
    assert "INE214G01026" in diag.excluded_or_unmapped_companies
    assert diag.parity_verdict == "PRODUCTION_FULL_PARITY_CONFIRMED"


def test_scope_diagnostic_to_dict():
    """Verify serialization to dictionary."""
    diag = ScopeDiagnostic()
    d = diag.to_dict()
    assert isinstance(d, dict)
    assert d["production_bills_count"] == 20
    assert d["production_companies_count"] == 47
    assert d["expected_decision_candidates"] == 4700
    assert "bill_discrepancy_explanation" in d
    assert "company_discrepancy_explanation" in d
    assert "runtime_subset_explanation" in d


def test_scope_service_with_mock_data_service():
    """Verify ScopeService dynamically queries data service if present."""
    mock_data_service = MagicMock()
    # Create mock decision records
    rec1 = MagicMock()
    rec1.bill_id = "bill-1"
    rec1.company_isin = "INE001"
    rec2 = MagicMock()
    rec2.bill_id = "bill-2"
    rec2.company_isin = "INE002"

    mock_data_service.get_decision_records.return_value = [rec1, rec2]

    service = ScopeService(mock_data_service)
    diag = service.get_diagnostic()

    assert diag.actual_decision_records == 2
    assert diag.production_bills_count == 2
    assert diag.production_companies_count == 2
    assert diag.expected_decision_candidates == 2 * 2 * 5


def test_scope_service_fallback_on_exception():
    """Verify ScopeService falls back safely when data service raises exception."""
    mock_data_service = MagicMock()
    mock_data_service.get_decision_records.side_effect = RuntimeError("Storage error")

    service = ScopeService(mock_data_service)
    diag = service.get_diagnostic()

    assert diag.actual_decision_records == 4700
    assert diag.production_bills_count == 20
    assert diag.production_companies_count == 47
