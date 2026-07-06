"""
ingestion/parliament package
============================
Ingestion of Indian Central Government legislative documents.

Sources
-------
*  PRS Legislative Research  (https://prsindia.org)
*  Lok Sabha                 (https://loksabha.nic.in)
*  Rajya Sabha               (https://rajyasabha.nic.in)
*  India Code                (https://indiacode.nic.in)
*  e-Gazette of India        (https://egazette.gov.in)
"""

from __future__ import annotations

from ingestion.parliament.connector import ParliamentConnector
from ingestion.parliament.discovery import ParliamentDiscovery
from ingestion.parliament.downloader import ParliamentDownloader
from ingestion.parliament.exceptions import (
    ConnectorError,
    ParsingError,
    ParliamentIngestionError,
    PDFDownloadError,
    ValidationError,
)
from ingestion.parliament.normalizer import ParliamentNormalizer
from ingestion.parliament.parser import ParliamentParser
from ingestion.parliament.service import ParliamentIngestionService

__all__ = [
    "ParliamentConnector",
    "ParliamentDiscovery",
    "ParliamentDownloader",
    "ParliamentNormalizer",
    "ParliamentParser",
    "ParliamentIngestionService",
    "ParliamentIngestionError",
    "ConnectorError",
    "ParsingError",
    "PDFDownloadError",
    "ValidationError",
]
