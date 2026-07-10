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

from pathlib import Path
from config.logging_config import get_logger
from schemas.company import Company

logger = get_logger(__name__)


class CompanyRepository:
    """
    Repository for BSE/NSE company master data.
    """

    def __init__(self, database_path: str | Path | None = None) -> None:
        from config.settings import settings

        self._companies_dir = settings.COMPANIES_DIR

        if database_path:
            self._db_file = Path(database_path)
        else:
            self._db_file = self._companies_dir / "companies.json"

        logger.debug("CompanyRepository initialised | file=%s", self._db_file)

    def _load_data(self) -> list[Company]:
        import json
        from schemas.company import Company

        if not self._db_file.is_file():
            return []
        try:
            with self._db_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return [Company.from_dict(item) for item in data]
        except Exception as e:
            logger.error("Failed to load company records: %s", e)
            return []

    def _save_data(self, companies: list[Company]) -> None:
        import json

        self._db_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._db_file.open("w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in companies], f, indent=2)
        except Exception as e:
            logger.error("Failed to save company records: %s", e)
            raise e

    def get_by_isin(self, isin: str) -> Company | None:
        """Return a company record by ISIN, or None if not found."""
        isin_upper = isin.strip().upper()
        for company in self._load_data():
            if company.isin.upper() == isin_upper:
                return company
        return None

    def get_by_ticker(self, ticker: str, exchange: str = "NSE") -> Company | None:
        """Return a company record by ticker symbol and exchange."""
        ticker_upper = ticker.strip().upper()
        exchange_upper = exchange.strip().upper()

        for company in self._load_data():
            if exchange_upper == "NSE" and company.ticker_nse.upper() == ticker_upper:
                return company
            elif exchange_upper == "BSE" and (
                company.ticker_bse.upper() == ticker_upper or company.bse_code == ticker_upper
            ):
                return company
        return None

    def get_all(self) -> list[Company]:
        """Return all company records."""
        return self._load_data()

    def get_by_sector(self, sector: str) -> list[Company]:
        """Return companies in a given SEBI/NSE sector."""
        sector_lower = sector.strip().lower()
        return [c for c in self._load_data() if c.sector.lower() == sector_lower]

    def get_by_market_cap_category(self, category: str) -> list[Company]:
        """Return companies by market cap category (large-cap/mid-cap/small-cap)."""
        category_lower = category.strip().lower().replace("-", "_")
        return [
            c for c in self._load_data() if c.market_cap_category.value.lower() == category_lower
        ]

    def search_by_name(self, query: str, top_k: int = 10) -> list[Company]:
        """Fuzzy-search companies by name using SequenceMatcher similarity."""
        from difflib import SequenceMatcher

        query_lower = query.strip().lower()
        if not query_lower:
            return []

        results = []
        for company in self._load_data():
            name_lower = company.company_name.lower()
            # Calculate similarity
            ratio = SequenceMatcher(None, query_lower, name_lower).ratio()
            # Also boost if query is substring
            if query_lower in name_lower:
                ratio += 0.3
            results.append((company, ratio))

        # Sort by similarity ratio descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in results[:top_k] if item[1] > 0.3]

    def search(
        self,
        nse_symbol: str | None = None,
        company_name: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        state: str | None = None,
    ) -> list[Company]:
        """
        Support lookup by: NSE Symbol, Company Name, Sector, Industry, State.
        """
        results = self._load_data()

        if nse_symbol:
            sym_upper = nse_symbol.strip().upper()
            results = [c for c in results if sym_upper in c.ticker_nse.upper()]

        if company_name:
            name_lower = company_name.strip().lower()
            results = [c for c in results if name_lower in c.company_name.lower()]

        if sector:
            sector_lower = sector.strip().lower()
            results = [c for c in results if sector_lower in c.sector.lower()]

        if industry:
            ind_lower = industry.strip().lower()
            results = [c for c in results if ind_lower in c.industry.lower()]

        if state:
            state_lower = state.strip().lower()
            results = [c for c in results if state_lower in c.hq_state.lower()]

        return results

    def save(self, company: Company) -> None:
        """Persist a single company record (inserts or updates)."""
        companies = self._load_data()
        isin_upper = company.isin.strip().upper()

        # Check if already exists by ISIN to update
        for idx, existing in enumerate(companies):
            if existing.isin.upper() == isin_upper:
                companies[idx] = company
                break
        else:
            companies.append(company)

        self._save_data(companies)

    def save_many(self, companies_list: list[Company]) -> None:
        """Persist multiple company records."""
        companies = self._load_data()

        for company in companies_list:
            isin_upper = company.isin.strip().upper()
            for idx, existing in enumerate(companies):
                if existing.isin.upper() == isin_upper:
                    companies[idx] = company
                    break
            else:
                companies.append(company)

        self._save_data(companies)

    def upsert_many(self, companies_list: list[Company]) -> int:
        """Insert or update company records; return count of upserted records."""
        before_count = self.count()
        self.save_many(companies_list)
        return len(companies_list)

    def count(self) -> int:
        """Return total number of stored company records."""
        return len(self._load_data())

    def exists(self, isin: str) -> bool:
        """Return True if a company with the given ISIN is stored."""
        isin_upper = isin.strip().upper()
        for company in self._load_data():
            if company.isin.upper() == isin_upper:
                return True
        return False

    def __repr__(self) -> str:
        return f"<CompanyRepository file={self._db_file!r}>"
