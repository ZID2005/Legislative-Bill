"""
schemas package
===============
Typed data models for all core domain entities.

Motivation
----------
Without explicit schemas, data passes between modules as untyped dicts.
This causes:

*  Silent field renames breaking downstream code
*  Missing required fields only discovered at runtime
*  No IDE autocomplete or type-checker support
*  Inconsistent field naming across modules

This package defines the canonical schema for every entity in the system.
All code that reads or writes domain data must use these models.

Current Implementation
----------------------
Task 0: Python ``dataclasses`` with type hints.  Lightweight, zero
dependencies, compatible with the standard library.

Future Migration (Task 3)
--------------------------
Fields will be annotated with ``pydantic`` validators for:
*  Runtime type coercion (e.g. "2024-01-01" → datetime.date)
*  Value-range validation (e.g. year > 1947)
*  Custom error messages

Schemas
-------
bill        : Central Government legislative bill
company     : BSE/NSE listed company
market      : Market price record (OHLCV)
prediction  : Model prediction output for a (bill, company) pair
"""

from schemas.bill import Bill, BillStatus, BillHouse
from schemas.company import Company, MarketCapCategory
from schemas.market import PriceRecord
from schemas.prediction import Prediction, ImpactLabel
from schemas.knowledge_record import KnowledgeRecord
from schemas.mapping_record import BillCompanyMapping

__all__ = [
    # Bill
    "Bill",
    "BillStatus",
    "BillHouse",
    # Company
    "Company",
    "MarketCapCategory",
    # Market
    "PriceRecord",
    # Prediction
    "Prediction",
    "ImpactLabel",
    # Knowledge Record
    "KnowledgeRecord",
    # Mapping Record
    "BillCompanyMapping",
]
