"""
storage/company_repository.py
==============================
Repository for BSE/NSE company master data.

This module is the **single access point** for reading and writing company
records.  All other modules must use this repository; they must not read
``data/companies/`` directly.

Current Backend
---------------
Task 0: Stub (no backend yet)
Task 2: CSV / Parquet under ``data/companies/master.parquet``
Task 3+: SQLite (via SQLAlchemy)

Interface
---------
::

    repo = CompanyRepository()

    # Read single
    repo.get_by_isin(isin: str) -> Company | None
    repo.get_by_ticker(ticker: str, exchange: str = "NSE") -> Company | None

    # Read many
    repo.get_all() -> list[Company]
    repo.get_by_sector(sector: str) -> list[Company]
    repo.get_by_market_cap_category(category: str) -> list[Company]

    # Write
    repo.save(company: Company) -> None
    repo.save_many(companies: list[Company]) -> None
    repo.upsert_many(companies: list[Company]) -> int  # returns upsert count

    # Search
    repo.search_by_name(query: str, top_k: int = 10) -> list[Company]

    # Utility
    repo.count() -> int
    repo.exists(isin: str) -> bool
"""

from __future__ import annotations

from config.logging_config import get_logger

logger = get_logger(__name__)


class CompanyRepository:
    """
    Repository for BSE/NSE company master data.

    Full implementation in Task 2.
    """

    def __init__(self) -> None:
        from config.settings import settings
        self._companies_dir = settings.COMPANIES_DIR
        logger.debug("CompanyRepository initialised | dir=%s", self._companies_dir)

    def get_by_isin(self, isin: str) -> object | None:
        """Return a company record by ISIN, or None if not found."""
        raise NotImplementedError("CompanyRepository.get_by_isin() — implemented in Task 2.")

    def get_by_ticker(self, ticker: str, exchange: str = "NSE") -> object | None:
        """Return a company record by ticker symbol and exchange."""
        raise NotImplementedError("CompanyRepository.get_by_ticker() — implemented in Task 2.")

    def get_all(self) -> list:
        """Return all company records."""
        raise NotImplementedError("CompanyRepository.get_all() — implemented in Task 2.")

    def get_by_sector(self, sector: str) -> list:
        """Return companies in a given SEBI/NSE sector."""
        raise NotImplementedError("CompanyRepository.get_by_sector() — implemented in Task 2.")

    def get_by_market_cap_category(self, category: str) -> list:
        """Return companies by market cap category (large-cap/mid-cap/small-cap)."""
        raise NotImplementedError(
            "CompanyRepository.get_by_market_cap_category() — implemented in Task 2."
        )

    def search_by_name(self, query: str, top_k: int = 10) -> list:
        """
        Fuzzy-search companies by name.

        Uses rapidfuzz for approximate matching; useful for linking
        company names mentioned in bill text to master records.
        """
        raise NotImplementedError("CompanyRepository.search_by_name() — implemented in Task 5.")

    def save(self, company: object) -> None:
        """Persist a single company record."""
        raise NotImplementedError("CompanyRepository.save() — implemented in Task 2.")

    def save_many(self, companies: list) -> None:
        """Persist multiple company records."""
        raise NotImplementedError("CompanyRepository.save_many() — implemented in Task 2.")

    def upsert_many(self, companies: list) -> int:
        """Insert or update company records; return count of upserted records."""
        raise NotImplementedError("CompanyRepository.upsert_many() — implemented in Task 2.")

    def count(self) -> int:
        """Return total number of stored company records."""
        raise NotImplementedError("CompanyRepository.count() — implemented in Task 2.")

    def exists(self, isin: str) -> bool:
        """Return True if a company with the given ISIN is stored."""
        raise NotImplementedError("CompanyRepository.exists() — implemented in Task 2.")

    def __repr__(self) -> str:
        return f"<CompanyRepository dir={self._companies_dir!r}>"
