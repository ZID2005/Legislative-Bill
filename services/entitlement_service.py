"""
services/entitlement_service.py
===============================
SaaS Feature Entitlement and Non-Functional Billing Boundary (Tasks 8.19).

Enforces:
1. Canonical tier levels: FREE, PRO, TEAM, ENTERPRISE.
2. Invariant: Does NOT implement fake payment gateways or process payment cards.
3. Explicit status: BILLING_NOT_CONNECTED / PLAN_NOT_CONFIGURED.
4. Clean boundary for quota and entitlement checks (watchlists, alerts, AI usage, exports).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from storage.tenant_repository import TenantRepository

logger = get_logger(__name__)


@dataclass(frozen=True)
class PlanEntitlement:
    """Entitlement thresholds and capabilities per subscription tier."""

    name: str
    max_watchlists: int
    max_alerts: int
    ai_requests_per_month: int
    data_export: bool
    webhook_delivery: bool
    status: str = "BILLING_NOT_CONNECTED"


TIER_ENTITLEMENTS: dict[str, PlanEntitlement] = {
    "FREE": PlanEntitlement(
        name="FREE",
        max_watchlists=3,
        max_alerts=5,
        ai_requests_per_month=50,
        data_export=False,
        webhook_delivery=False,
    ),
    "PRO": PlanEntitlement(
        name="PRO",
        max_watchlists=25,
        max_alerts=50,
        ai_requests_per_month=1000,
        data_export=True,
        webhook_delivery=True,
    ),
    "TEAM": PlanEntitlement(
        name="TEAM",
        max_watchlists=100,
        max_alerts=200,
        ai_requests_per_month=5000,
        data_export=True,
        webhook_delivery=True,
    ),
    "ENTERPRISE": PlanEntitlement(
        name="ENTERPRISE",
        max_watchlists=999999,
        max_alerts=999999,
        ai_requests_per_month=999999,
        data_export=True,
        webhook_delivery=True,
    ),
    "PLAN_NOT_CONFIGURED": PlanEntitlement(
        name="PLAN_NOT_CONFIGURED",
        max_watchlists=50,
        max_alerts=100,
        ai_requests_per_month=1000,
        data_export=True,
        webhook_delivery=True,
    ),
}


class EntitlementService:
    """
    Evaluates tenant feature permissions and resource quotas.
    """

    def __init__(self, tenant_repo: Optional[TenantRepository] = None) -> None:
        self._tenant_repo = tenant_repo or TenantRepository()

    def get_tenant_entitlements(self, tenant_id: str) -> PlanEntitlement:
        """Retrieve authoritative entitlements for a tenant."""
        tenant = self._tenant_repo.get(tenant_id)
        if not tenant:
            return TIER_ENTITLEMENTS["PLAN_NOT_CONFIGURED"]

        tier = tenant.plan_tier.upper() if tenant.plan_tier else "PLAN_NOT_CONFIGURED"
        return TIER_ENTITLEMENTS.get(tier, TIER_ENTITLEMENTS["PLAN_NOT_CONFIGURED"])

    def is_feature_allowed(self, tenant_id: str, feature: str) -> bool:
        """Check boolean permission for a capability (e.g. 'data_export')."""
        entitlements = self.get_tenant_entitlements(tenant_id)
        if feature == "data_export":
            return entitlements.data_export
        if feature == "webhook_delivery":
            return entitlements.webhook_delivery
        return True

    def check_quota(self, tenant_id: str, feature: str, current_count: int) -> bool:
        """
        Verify whether the tenant is within quota limits for a metered resource.
        """
        entitlements = self.get_tenant_entitlements(tenant_id)
        if feature == "watchlists":
            return current_count < entitlements.max_watchlists
        if feature == "alerts":
            return current_count < entitlements.max_alerts
        if feature == "ai_requests":
            return current_count < entitlements.ai_requests_per_month
        return True
