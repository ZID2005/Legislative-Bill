"""
scraper/company_loader.py
=========================
Company master data loader — **Task 2 placeholder**.

Future Responsibility
---------------------
This module will load and maintain the master list of companies listed on
BSE (Bombay Stock Exchange) and NSE (National Stock Exchange) of India.

Planned functionality:

1.  **Load company master** from BSE/NSE bulk data downloads:
    *  BSE scrip master CSV (available from bseindia.com)
    *  NSE equity symbol list (available from nseindia.com)

2.  **Persist** a unified, deduplicated company master as a structured CSV/
    Parquet file under ``data/companies/``.

3.  **Enrich** each company record with:
    *  ISIN (unique security identifier)
    *  NSE/BSE ticker symbols
    *  Sector (SEBI/NSE/BSE sector classification)
    *  Industry group
    *  Market cap category (large-cap, mid-cap, small-cap)
    *  Listing date

4.  **Incremental refresh** — detect changes in the exchange listings and
    update the local master accordingly.

Interface (stub)
----------------
::

    def load_company_master(exchange: str = "both") -> list[dict]:
        ...

    def get_company_by_isin(isin: str) -> dict | None:
        ...

    def get_companies_by_sector(sector: str) -> list[dict]:
        ...

Dependencies (to be added in Task 2)
--------------------------------------
*  pandas
*  requests / httpx
*  openpyxl (for Excel-format exchange files)
"""

# TODO (Task 2): Implement CompanyLoader class.


class CompanyLoader:
    """
    Placeholder for the BSE/NSE company master data loader.

    Full implementation planned for Task 2.
    """

    def __init__(self) -> None:
        raise NotImplementedError(
            "CompanyLoader is not yet implemented.  See Task 2."
        )
