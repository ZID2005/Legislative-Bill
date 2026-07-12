"""
storage package
===============
Data access layer (Repository pattern) for the Legislative Intelligence project.

Motivation
----------
Without a dedicated storage layer, every module ends up doing::

    df = pd.read_csv("data/companies/master.csv")
    with open("data/bills/metadata/finance-bill-2024.json") as f:
        bill = json.load(f)

This creates three problems:

1.  **Coupling** — every module knows where data lives.
2.  **Fragility** — rename a file and you break many callers.
3.  **Lock-in** — moving from CSV to a database requires changes everywhere.

The Repository pattern solves this by providing a clean interface::

    from storage import bill_repo, company_repo, market_repo, catalog

    bill = bill_repo.get("finance-bill-2024")
    companies = company_repo.get_by_sector("Banking")
    prices = market_repo.get_prices("HDFCBANK", start="2024-01-01")

    # After ingestion, register the result in the catalog
    catalog.bills.update("bills_prs", record_count=4823, is_complete=True)

    # Before a pipeline run, check for staleness
    if catalog.bills.is_stale("bills_prs", max_age_days=7):
        logger.warning("Bill data may be stale")

The calling code doesn't know or care whether the data lives in a CSV,
Parquet file, SQLite database, or a cloud object store.

Components
----------
bill_repository    : Read/write bill metadata and full text.
company_repository : Read/write company master records.
market_repository  : Read/write historical OHLCV price data.
catalog            : Dataset registry — tracks freshness, record counts,
                     checksums, and ingestion timestamps for all datasets.

Note
----
In Task 0 repositories are stubs.  They will be wired to actual storage
backends incrementally as each data ingestion task is completed.
"""

from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.market_repository import MarketRepository
from storage.knowledge_repository import KnowledgeRepository
from storage.mapping_repository import MappingRepository
from storage.market_model_repository import MarketModelRepository
from storage.event_study_repository import EventStudyRepository
from storage.statistical_repository import StatisticalRepository
from storage.label_repository import LabelRepository
from storage.catalog import CatalogManager, DatasetEntry, compute_md5


# ---------------------------------------------------------------------------
# Repository singletons
# ---------------------------------------------------------------------------
bill_repo: BillRepository = BillRepository()
company_repo: CompanyRepository = CompanyRepository()
market_repo: MarketRepository = MarketRepository()
knowledge_repo: KnowledgeRepository = KnowledgeRepository()
mapping_repo: MappingRepository = MappingRepository()
market_model_repo: MarketModelRepository = MarketModelRepository()
event_study_repo: EventStudyRepository = EventStudyRepository()
statistical_repo: StatisticalRepository = StatisticalRepository()
label_repo: LabelRepository = LabelRepository()


# ---------------------------------------------------------------------------
# Catalog singletons — one per dataset group
# ---------------------------------------------------------------------------
class _Catalog:
    """Namespace holding catalog managers for each dataset group."""

    @property
    def bills(self) -> CatalogManager:
        """Catalog for the bills dataset group."""
        return CatalogManager("bills")

    @property
    def companies(self) -> CatalogManager:
        """Catalog for the companies dataset group."""
        return CatalogManager("companies")

    @property
    def market(self) -> CatalogManager:
        """Catalog for the market dataset group."""
        return CatalogManager("market")


catalog: _Catalog = _Catalog()


__all__ = [
    # Repositories
    "BillRepository",
    "CompanyRepository",
    "MarketRepository",
    "KnowledgeRepository",
    "MappingRepository",
    "MarketModelRepository",
    "EventStudyRepository",
    "StatisticalRepository",
    "LabelRepository",
    "bill_repo",
    "company_repo",
    "market_repo",
    "knowledge_repo",
    "mapping_repo",
    "market_model_repo",
    "event_study_repo",
    "statistical_repo",
    "label_repo",
    # Catalog
    "CatalogManager",
    "DatasetEntry",
    "compute_md5",
    "catalog",
]
