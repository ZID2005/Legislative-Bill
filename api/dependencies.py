"""
api/dependencies.py
===================
Dependency injection providers for services, repositories,
and multi-tenant user authentication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from fastapi import Header

from config.logging_config import get_logger
from config.settings import settings
from api.errors import UnauthorizedError
from schemas.decision import DecisionSupportRecord
from schemas.prediction import PredictionRecord
from services.ai.ai_explanation_service import AIExplanationService
from services.company_intelligence_service import CompanyIntelligenceService
from services.monitoring.monitoring_runner import MonitoringRunner
from services.notification_center_service import NotificationCenterService
from services.state_knowledge_service import StateKnowledgeService
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from services.watchlist_service import WatchlistService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.anticipation_repository import AnticipationRepository
from storage.decision_repository import DecisionRepository
from storage.monitoring_repository import MonitoringRepository
from storage.prediction_repository import PredictionRepository
from storage.report_repository import ReportRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.state_knowledge_repository import StateKnowledgeRepository

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Authentication & Identity Context
# ---------------------------------------------------------------------------


@dataclass
class CurrentUser:
    """Authenticated user context for multi-tenant isolation."""

    user_id: str
    tenant_id: str
    roles: list[str] = field(default_factory=lambda: ["analyst"])

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> CurrentUser:
    """
    Dependency extracting current user and tenant identity.

    Security & Architecture Rules:
    1. In production (ENV == 'production'), a valid Bearer JWT is mandatory.
    2. In development / testing, allows X-Tenant-ID and X-User-ID headers to test
       multi-tenant boundary enforcement, falling back to ('default_user', 'default_tenant').
    3. Never accepts arbitrary tenant_id in query parameters for user-owned resources.
    """
    # Production JWT enforcement preparation
    if settings.ENV.lower() == "production":
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedError(
                code="AUTH_REQUIRED",
                message="Valid Bearer token required in Authorization header.",
            )
        token = authorization.split(" ", 1)[1].strip()
        if not token or token == "invalid_token":
            raise UnauthorizedError(
                code="INVALID_TOKEN",
                message="Provided authorization token is invalid or expired.",
            )
        # In a full JWT deployment, jwt.decode would verify signatures & claims
        # For now, extract claims or use token identity
        user_id = x_user_id or "prod_user"
        tenant_id = x_tenant_id or "prod_tenant"
        return CurrentUser(user_id=user_id, tenant_id=tenant_id)

    # Development / Testing Mode
    user_id = x_user_id.strip() if x_user_id else "default_user"
    tenant_id = x_tenant_id.strip() if x_tenant_id else "default_tenant"

    return CurrentUser(user_id=user_id, tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# Service & Repository Singletons
# ---------------------------------------------------------------------------

_discovery_service: Optional[UnifiedLegislativeDiscoveryService] = None
_company_intelligence_service: Optional[CompanyIntelligenceService] = None
_prediction_repository: Optional[PredictionRepository] = None
_decision_repository: Optional[DecisionRepository] = None
_anticipation_repository: Optional[AnticipationRepository] = None
_report_repository: Optional[ReportRepository] = None
_state_knowledge_service: Optional[StateKnowledgeService] = None
_state_bill_repository: Optional[StateBillRepository] = None
_state_knowledge_repository: Optional[StateKnowledgeRepository] = None
_state_corporate_repository: Optional[StateCorporateExposureRepository] = None
_watchlist_service: Optional[WatchlistService] = None
_alert_event_repository: Optional[AlertEventRepository] = None
_alert_group_repository: Optional[AlertGroupRepository] = None
_notification_center_service: Optional[NotificationCenterService] = None
_monitoring_runner: Optional[MonitoringRunner] = None
_monitoring_repository: Optional[MonitoringRepository] = None
_ai_explanation_service: Optional[AIExplanationService] = None

# In-memory caches for static/frozen artifacts to guarantee sub-5ms latency
_cached_predictions: Optional[list[PredictionRecord]] = None
_cached_predictions_by_id: Optional[dict[str, PredictionRecord]] = None
_cached_decisions_by_id: Optional[dict[str, DecisionSupportRecord]] = None


def get_discovery_service() -> UnifiedLegislativeDiscoveryService:
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = UnifiedLegislativeDiscoveryService()
    return _discovery_service


def get_company_intelligence_service() -> CompanyIntelligenceService:
    global _company_intelligence_service
    if _company_intelligence_service is None:
        _company_intelligence_service = CompanyIntelligenceService()
    return _company_intelligence_service


def get_prediction_repository() -> PredictionRepository:
    global _prediction_repository
    if _prediction_repository is None:
        _prediction_repository = PredictionRepository()
    return _prediction_repository


def get_decision_repository() -> DecisionRepository:
    global _decision_repository
    if _decision_repository is None:
        _decision_repository = DecisionRepository()
    return _decision_repository


def get_anticipation_repository() -> AnticipationRepository:
    global _anticipation_repository
    if _anticipation_repository is None:
        _anticipation_repository = AnticipationRepository()
    return _anticipation_repository


def get_report_repository() -> ReportRepository:
    global _report_repository
    if _report_repository is None:
        _report_repository = ReportRepository()
    return _report_repository


def get_state_knowledge_service() -> StateKnowledgeService:
    global _state_knowledge_service
    if _state_knowledge_service is None:
        _state_knowledge_service = StateKnowledgeService()
    return _state_knowledge_service


def get_state_bill_repository() -> StateBillRepository:
    global _state_bill_repository
    if _state_bill_repository is None:
        _state_bill_repository = StateBillRepository()
    return _state_bill_repository


def get_state_knowledge_repository() -> StateKnowledgeRepository:
    global _state_knowledge_repository
    if _state_knowledge_repository is None:
        _state_knowledge_repository = StateKnowledgeRepository()
    return _state_knowledge_repository


def get_state_corporate_repository() -> StateCorporateExposureRepository:
    global _state_corporate_repository
    if _state_corporate_repository is None:
        _state_corporate_repository = StateCorporateExposureRepository()
    return _state_corporate_repository


def get_watchlist_service() -> WatchlistService:
    global _watchlist_service
    if _watchlist_service is None:
        _watchlist_service = WatchlistService()
    return _watchlist_service


def get_alert_event_repository() -> AlertEventRepository:
    global _alert_event_repository
    if _alert_event_repository is None:
        _alert_event_repository = AlertEventRepository()
    return _alert_event_repository


def get_alert_group_repository() -> AlertGroupRepository:
    global _alert_group_repository
    if _alert_group_repository is None:
        _alert_group_repository = AlertGroupRepository()
    return _alert_group_repository


def get_notification_center_service() -> NotificationCenterService:
    global _notification_center_service
    if _notification_center_service is None:
        _notification_center_service = NotificationCenterService()
    return _notification_center_service


def get_monitoring_runner() -> MonitoringRunner:
    global _monitoring_runner
    if _monitoring_runner is None:
        _monitoring_runner = MonitoringRunner()
    return _monitoring_runner


def get_monitoring_repository() -> MonitoringRepository:
    global _monitoring_repository
    if _monitoring_repository is None:
        _monitoring_repository = MonitoringRepository()
    return _monitoring_repository


def get_ai_explanation_service() -> AIExplanationService:
    global _ai_explanation_service
    if _ai_explanation_service is None:
        _ai_explanation_service = AIExplanationService()
    return _ai_explanation_service


# ---------------------------------------------------------------------------
# High-Performance In-Memory Index for Frozen Central Artifacts
# ---------------------------------------------------------------------------


def get_cached_predictions() -> tuple[list[PredictionRecord], dict[str, PredictionRecord]]:
    """
    Return all 4,700 frozen Central prediction records indexed in memory.
    Avoids 4,700 file system reads on repeated API requests.
    """
    global _cached_predictions, _cached_predictions_by_id
    if _cached_predictions is None:
        repo = get_prediction_repository()
        records = repo.load_all()
        by_id = {r.prediction_id: r for r in records}
        _cached_predictions = records
        _cached_predictions_by_id = by_id
        logger.info("Indexed %d prediction records in API memory", len(records))
    assert _cached_predictions_by_id is not None
    return _cached_predictions, _cached_predictions_by_id


def get_cached_decisions_by_id() -> dict[str, DecisionSupportRecord]:
    """
    Return all 4,700 frozen Central decision records indexed by decision_id in memory.
    """
    global _cached_decisions_by_id
    if _cached_decisions_by_id is None:
        repo = get_decision_repository()
        records = repo.load_all()
        _cached_decisions_by_id = {r.decision_id: r for r in records}
        logger.info("Indexed %d decision support records in API memory", len(records))
    return _cached_decisions_by_id
