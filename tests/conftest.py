"""
tests/conftest.py
=================
Shared pytest fixtures for the test suite.

Fixtures defined here are automatically available in all test files.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sample_bill_metadata() -> dict:
    """Return a sample bill metadata dict for testing validators and mappers."""
    return {
        "bill_id": "finance-bill-2024",
        "title": "The Finance Bill, 2024",
        "bill_number": "7/2024",
        "year": 2024,
        "ministry": "Ministry of Finance",
        "house": "Lok Sabha",
        "status": "passed",
        "introduction_date": "2024-02-01",
        "url": "https://prsindia.org/bills/finance-bill-2024",
        "sectors": ["Banking", "Insurance", "Capital Markets"],
    }


@pytest.fixture(scope="session")
def sample_company_record() -> dict:
    """Return a sample company master record for testing."""
    return {
        "isin": "INE009A01021",
        "ticker_nse": "INFY",
        "ticker_bse": "INFY",
        "company_name": "Infosys Limited",
        "sector": "Technology",
        "industry": "IT Services",
        "market_cap_cr": 620000,
        "listing_date": "1993-06-14",
    }
