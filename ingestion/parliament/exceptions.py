"""
ingestion/parliament/exceptions.py
==================================
Custom exception hierarchy for the Central Legislative Data Ingestion Service.
"""

from __future__ import annotations


class ParliamentIngestionError(Exception):
    """Base exception for all legislative ingestion pipeline failures."""
    pass


class ConnectorError(ParliamentIngestionError):
    """Raised when HTTP or networking operations fail, including rate limits and timeouts."""
    pass


class ParsingError(ParliamentIngestionError):
    """Raised when parsing of HTML, XML, or PDF contents fails due to unexpected formatting."""
    pass


class ValidationError(ParliamentIngestionError):
    """Raised when normalized bill data does not conform to validation schemas."""
    pass


class PDFDownloadError(ParliamentIngestionError):
    """Raised when downloading or processing a bill PDF document fails."""
    pass
