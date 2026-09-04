"""
reporting/__init__.py
=====================
Stakeholder Reporting & Presentation Layer (Task 7.3).

Exposes the primary public interface for generating, formatting,
validating, and persisting stakeholder reports from
DecisionSupportRecord outputs (Task 7.2).

No prediction logic, risk formulas, or ML models are present in this layer.
"""

from reporting.bill_aggregator import BillAggregator
from reporting.business_reporter import BusinessReporter
from reporting.company_aggregator import CompanyAggregator
from reporting.engine import ReportingEngine
from reporting.formatter import ReportFormatter
from reporting.investor_reporter import InvestorReporter
from reporting.public_reporter import PublicReporter
from reporting.validator import ReportValidator

__all__ = [
    "BillAggregator",
    "BusinessReporter",
    "CompanyAggregator",
    "ReportingEngine",
    "ReportFormatter",
    "InvestorReporter",
    "PublicReporter",
    "ReportValidator",
]
