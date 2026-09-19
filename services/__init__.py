"""
services package
================
Service Layer (orchestration) for the Legislative Intelligence project.

Coordinates business workflows across ingestion, validation, models, and AI.
"""

from __future__ import annotations

from services.ingestion import IngestionService
from services.prediction import PredictionService
from services.explanation import ExplanationService, LLMProvider
from services.knowledge_service import KnowledgeService
from services.mapping_service import MappingService
from services.event_study_service import EventStudyService
from services.market_model_service import MarketModelService
from services.statistical_service import StatisticalSignificanceService
from services.label_service import LabelGenerationService
from services.anticipation_service import AnticipationService
from services.company_intelligence_service import (
    CompanyBillExposureView,
    CompanyExposureExplanation,
    CompanyIntelligenceService,
    CompanyProfileView,
)
from services.decision_service import DecisionSupportService
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from services.watchlist_index_service import (
    IndexValidationReport,
    WatchlistIndexService,
    WatchlistSubscriber,
)
from services.watchlist_service import WatchlistService
from services.alert_matching_service import AlertMatchingService
from services.alert_aggregation_service import AlertAggregationService
from services.alert_digest_service import AlertDigestService
from services.notification_dispatcher import NotificationDispatcher
from services.notification_providers import (
    EmailNotificationProvider,
    InAppNotificationProvider,
    MockEmailProvider,
    MockPushProvider,
    MockWebhookTransport,
    NotificationProvider,
    NotificationProviderRegistry,
    PushNotificationProvider,
    WebhookNotificationProvider,
    WebhookTransport,
    format_webhook_payload,
    generate_hmac_sha256_signature,
    validate_webhook_url,
)
from services.notification_service import NotificationService
from services.notification_center_service import (
    NotificationCenterService,
    NotificationCenterSummary,
)
from services.alert_pipeline_service import AlertPipelineService, PipelineResult

__all__ = [
    "IngestionService",
    "PredictionService",
    "DecisionSupportService",
    "ExplanationService",
    "LLMProvider",
    "KnowledgeService",
    "MappingService",
    "EventStudyService",
    "MarketModelService",
    "StatisticalSignificanceService",
    "LabelGenerationService",
    "AnticipationService",
    "UnifiedLegislativeDiscoveryService",
    "CompanyIntelligenceService",
    "CompanyProfileView",
    "CompanyBillExposureView",
    "CompanyExposureExplanation",
    "WatchlistService",
    "WatchlistIndexService",
    "WatchlistSubscriber",
    "IndexValidationReport",
    "AlertMatchingService",
    "AlertAggregationService",
    "AlertDigestService",
    "NotificationDispatcher",
    "NotificationService",
    "NotificationCenterService",
    "NotificationCenterSummary",
    "NotificationProvider",
    "InAppNotificationProvider",
    "EmailNotificationProvider",
    "PushNotificationProvider",
    "WebhookNotificationProvider",
    "MockEmailProvider",
    "MockPushProvider",
    "WebhookTransport",
    "MockWebhookTransport",
    "NotificationProviderRegistry",
    "format_webhook_payload",
    "generate_hmac_sha256_signature",
    "validate_webhook_url",
    "AlertPipelineService",
    "PipelineResult",
]
