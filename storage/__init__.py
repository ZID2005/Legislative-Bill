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
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.market_repository import MarketRepository
from storage.knowledge_repository import KnowledgeRepository
from storage.mapping_repository import MappingRepository
from storage.market_model_repository import MarketModelRepository
from storage.event_study_repository import EventStudyRepository
from storage.statistical_repository import StatisticalRepository
from storage.label_repository import LabelRepository
from storage.feature_repository import FeatureRepository
from storage.fusion_repository import FusionRepository
from storage.feature_selection_repository import FeatureSelectionRepository
from storage.anticipation_repository import AnticipationRepository
from storage.prediction_repository import PredictionRepository
from storage.decision_repository import DecisionRepository
from storage.report_repository import ReportRepository
from storage.catalog import CatalogManager, DatasetEntry, compute_md5
from storage.user_repository import UserRepository
from storage.watchlist_repository import WatchlistRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.alert_event_repository import AlertEventRepository
from storage.notification_repository import NotificationRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_group_repository import AlertGroupRepository


# ---------------------------------------------------------------------------
# Repository singletons
# ---------------------------------------------------------------------------
bill_repo: BillRepository = BillRepository()
state_bill_repo: StateBillRepository = StateBillRepository()
state_knowledge_repo: StateKnowledgeRepository = StateKnowledgeRepository()
state_corporate_exposure_repo: StateCorporateExposureRepository = StateCorporateExposureRepository()
company_exposure_repo: CompanyExposureRepository = CompanyExposureRepository()
company_repo: CompanyRepository = CompanyRepository()
market_repo: MarketRepository = MarketRepository()
knowledge_repo: KnowledgeRepository = KnowledgeRepository()
mapping_repo: MappingRepository = MappingRepository()
market_model_repo: MarketModelRepository = MarketModelRepository()
event_study_repo: EventStudyRepository = EventStudyRepository()
statistical_repo: StatisticalRepository = StatisticalRepository()
label_repo: LabelRepository = LabelRepository()
feature_repo: FeatureRepository = FeatureRepository()
fusion_repo: FusionRepository = FusionRepository()
feature_selection_repo: FeatureSelectionRepository = FeatureSelectionRepository()
anticipation_repo: AnticipationRepository = AnticipationRepository()
prediction_repo: PredictionRepository = PredictionRepository()
decision_repo: DecisionRepository = DecisionRepository()
report_repo: ReportRepository = ReportRepository()
user_repo: UserRepository = UserRepository()
watchlist_repo: WatchlistRepository = WatchlistRepository()
alert_rule_repo: AlertRuleRepository = AlertRuleRepository()
alert_event_repo: AlertEventRepository = AlertEventRepository()
notification_repo: NotificationRepository = NotificationRepository()
alert_preference_repo: AlertPreferenceRepository = AlertPreferenceRepository()
alert_group_repo: AlertGroupRepository = AlertGroupRepository()


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
    "StateBillRepository",
    "StateKnowledgeRepository",
    "StateCorporateExposureRepository",
    "CompanyExposureRepository",
    "CompanyRepository",
    "MarketRepository",
    "KnowledgeRepository",
    "MappingRepository",
    "MarketModelRepository",
    "EventStudyRepository",
    "StatisticalRepository",
    "LabelRepository",
    "FeatureRepository",
    "FusionRepository",
    "FeatureSelectionRepository",
    "AnticipationRepository",
    "PredictionRepository",
    "DecisionRepository",
    "ReportRepository",
    "UserRepository",
    "WatchlistRepository",
    "AlertRuleRepository",
    "AlertEventRepository",
    "NotificationRepository",
    "AlertPreferenceRepository",
    "AlertGroupRepository",
    "bill_repo",
    "state_bill_repo",
    "state_knowledge_repo",
    "state_corporate_exposure_repo",
    "company_exposure_repo",
    "company_repo",
    "market_repo",
    "knowledge_repo",
    "mapping_repo",
    "market_model_repo",
    "event_study_repo",
    "statistical_repo",
    "label_repo",
    "feature_repo",
    "fusion_repo",
    "feature_selection_repo",
    "anticipation_repo",
    "prediction_repo",
    "decision_repo",
    "report_repo",
    "user_repo",
    "watchlist_repo",
    "alert_rule_repo",
    "alert_event_repo",
    "notification_repo",
    "alert_preference_repo",
    "alert_group_repo",
    # Catalog
    "CatalogManager",
    "DatasetEntry",
    "compute_md5",
    "catalog",
]
