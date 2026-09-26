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
from schemas.anticipation import AnticipationScore
from schemas.decision import DecisionSupportRecord
from schemas.prediction import PredictionRecord
from services.ai.ai_explanation_service import AIExplanationService
from services.company_intelligence_service import CompanyIntelligenceService
from services.industry_intelligence_service import IndustryIntelligenceService
from services.monitoring.monitoring_runner import MonitoringRunner
from services.monitoring.scheduler import LegislativeScheduler
from services.monitoring.source_registry import MonitoringSourceRegistry
from services.notification_center_service import NotificationCenterService
from services.state_knowledge_service import StateKnowledgeService
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from services.watchlist_service import WatchlistService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from services.alert_digest_service import AlertDigestService
from storage.anticipation_repository import AnticipationRepository
from storage.decision_repository import DecisionRepository
from storage.monitoring_repository import MonitoringRepository
from storage.prediction_repository import PredictionRepository
from storage.report_repository import ReportRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from storage.tenant_repository import TenantRepository
from storage.user_repository import UserRepository
from storage.audit_log_repository import AuditLogRepository
from services.ai_usage_service import AIUsageService
from services.entitlement_service import EntitlementService
from services.account_service import AccountService

logger = get_logger(__name__)


from api.auth.provider import CurrentUser, get_auth_provider


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> CurrentUser:
    """
    Dependency extracting current user and tenant identity via configured AuthProvider.

    Security & Architecture Rules:
    1. In production (or when AUTH_PROVIDER=jwt), a valid Bearer token is mandatory.
    2. In development / testing, allows X-Tenant-ID and X-User-ID headers to test
       multi-tenant boundary enforcement, falling back to ('default_user', 'default_tenant').
    3. Never accepts arbitrary tenant_id in query parameters for user-owned resources.
    """
    provider = get_auth_provider()
    return provider.authenticate(
        authorization=authorization,
        x_tenant_id=x_tenant_id,
        x_user_id=x_user_id,
    )


from fastapi import Depends
from api.errors import ForbiddenError


def require_role(allowed_roles: list[str]):
    """Enforce that the authenticated user possesses one of the allowed roles."""
    allowed_upper = [r.upper() for r in allowed_roles]

    def _role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_roles_upper = [r.upper() for r in current_user.roles]
        if not any(r in allowed_upper for r in user_roles_upper):
            raise ForbiddenError(
                code="INSUFFICIENT_PERMISSIONS",
                message=f"Action requires one of roles: {allowed_roles}. Current role: {current_user.role}",
                details={"required_roles": allowed_roles, "user_role": current_user.role},
            )
        return current_user

    return _role_checker


def require_owner(current_user: CurrentUser = Depends(require_role(["OWNER"]))) -> CurrentUser:
    return current_user


def require_admin(current_user: CurrentUser = Depends(require_role(["OWNER", "ADMIN"]))) -> CurrentUser:
    return current_user


def require_member(current_user: CurrentUser = Depends(require_role(["OWNER", "ADMIN", "MEMBER"]))) -> CurrentUser:
    return current_user


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
_monitoring_source_registry: Optional[MonitoringSourceRegistry] = None
_legislative_scheduler: Optional[LegislativeScheduler] = None
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


_alert_preference_repository: Optional[AlertPreferenceRepository] = None


def get_alert_preference_repository() -> AlertPreferenceRepository:
    global _alert_preference_repository
    if _alert_preference_repository is None:
        _alert_preference_repository = AlertPreferenceRepository()
    return _alert_preference_repository


_alert_digest_service: Optional[AlertDigestService] = None


def get_alert_digest_service() -> AlertDigestService:
    global _alert_digest_service
    if _alert_digest_service is None:
        _alert_digest_service = AlertDigestService()
    return _alert_digest_service


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


def get_monitoring_source_registry() -> MonitoringSourceRegistry:
    global _monitoring_source_registry
    if _monitoring_source_registry is None:
        _monitoring_source_registry = MonitoringSourceRegistry()
    return _monitoring_source_registry


def get_legislative_scheduler() -> LegislativeScheduler:
    global _legislative_scheduler
    if _legislative_scheduler is None:
        _legislative_scheduler = LegislativeScheduler()
    return _legislative_scheduler


def get_scheduler() -> LegislativeScheduler:
    """Return the singleton LegislativeScheduler for observability queries."""
    return get_legislative_scheduler()


_industry_intelligence_service: Optional[IndustryIntelligenceService] = None


def get_industry_intelligence_service() -> IndustryIntelligenceService:
    global _industry_intelligence_service
    if _industry_intelligence_service is None:
        _industry_intelligence_service = IndustryIntelligenceService()
    return _industry_intelligence_service


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


_cached_anticipation_scores: Optional[list[AnticipationScore]] = None


def get_cached_anticipation_scores() -> list[AnticipationScore]:
    """
    Return all 940 frozen Central anticipation scores indexed in memory.
    Avoids 940 filesystem reads on repeated API requests.
    """
    global _cached_anticipation_scores
    if _cached_anticipation_scores is None:
        repo = get_anticipation_repository()
        records = repo.get_all_scores()
        _cached_anticipation_scores = records
        logger.info("Indexed %d anticipation score records in API memory", len(records))
    return _cached_anticipation_scores


# ---------------------------------------------------------------------------
# SaaS Multi-Tenant Singletons (Task 8.19)
# ---------------------------------------------------------------------------

_tenant_repository: Optional[TenantRepository] = None
_user_repository: Optional[UserRepository] = None
_audit_log_repository: Optional[AuditLogRepository] = None
_ai_usage_service: Optional[AIUsageService] = None
_entitlement_service: Optional[EntitlementService] = None
_account_service: Optional[AccountService] = None


def get_tenant_repository() -> TenantRepository:
    global _tenant_repository
    if _tenant_repository is None:
        _tenant_repository = TenantRepository()
    return _tenant_repository


def get_user_repository() -> UserRepository:
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository


def get_audit_log_repository() -> AuditLogRepository:
    global _audit_log_repository
    if _audit_log_repository is None:
        _audit_log_repository = AuditLogRepository()
    return _audit_log_repository


def get_ai_usage_service() -> AIUsageService:
    global _ai_usage_service
    if _ai_usage_service is None:
        _ai_usage_service = AIUsageService()
    return _ai_usage_service


def get_entitlement_service() -> EntitlementService:
    global _entitlement_service
    if _entitlement_service is None:
        _entitlement_service = EntitlementService(tenant_repo=get_tenant_repository())
    return _entitlement_service


def get_account_service() -> AccountService:
    global _account_service
    if _account_service is None:
        wl_svc = get_watchlist_service()
        _account_service = AccountService(
            tenant_repo=get_tenant_repository(),
            user_repo=get_user_repository(),
            audit_repo=get_audit_log_repository(),
            watchlist_repo=wl_svc.watchlist_repo,
            alert_rule_repo=wl_svc.alert_rule_repo,
            alert_pref_repo=wl_svc.alert_pref_repo,
        )
    return _account_service

