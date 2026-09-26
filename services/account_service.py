"""
services/account_service.py
===========================
Account lifecycle, member onboarding, data export, and deletion safety service (Task 8.19).

Enforces:
1. Strict tenant boundary isolation on all user mutations.
2. Invariant: Outbound invitation emails are documented as NOT_CONFIGURED
   rather than pretending email delivery succeeded.
3. Safe tenant deletion preserves frozen analytical and public legislative records.
4. Tenant data export packages only tenant-owned watchlists, alerts, and preferences.
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.audit_log import AuditLogEntry
from schemas.tenant import Tenant
from schemas.user import User, hash_password
from storage.audit_log_repository import AuditLogRepository
from storage.tenant_repository import TenantRepository
from storage.user_repository import UserRepository
from storage.watchlist_repository import WatchlistRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.alert_preference_repository import AlertPreferenceRepository

logger = get_logger(__name__)


class AccountService:
    """
    Coordinates tenant registration, membership, export, and soft deletion.
    """

    def __init__(
        self,
        tenant_repo: Optional[TenantRepository] = None,
        user_repo: Optional[UserRepository] = None,
        audit_repo: Optional[AuditLogRepository] = None,
        watchlist_repo: Optional[WatchlistRepository] = None,
        alert_rule_repo: Optional[AlertRuleRepository] = None,
        alert_pref_repo: Optional[AlertPreferenceRepository] = None,
    ) -> None:
        self.tenant_repo = tenant_repo or TenantRepository()
        self.user_repo = user_repo or UserRepository()
        self.audit_repo = audit_repo or AuditLogRepository()
        self.watchlist_repo = watchlist_repo or WatchlistRepository()
        self.alert_rule_repo = alert_rule_repo or AlertRuleRepository()
        self.alert_pref_repo = alert_pref_repo or AlertPreferenceRepository()

    def register_tenant_and_owner(
        self,
        org_name: str,
        owner_email: str,
        owner_name: str,
        password: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> tuple[Tenant, User]:
        """
        Create a new tenant organization and initial OWNER user.
        """
        if not tenant_id:
            slug = org_name.lower().replace(" ", "_")[:16]
            tenant_id = f"org_{slug}_{uuid.uuid4().hex[:6]}"

        user_id = f"usr_{uuid.uuid4().hex[:8]}"

        tenant = Tenant(
            tenant_id=tenant_id,
            name=org_name,
            owner_user_id=user_id,
            plan_tier="PLAN_NOT_CONFIGURED",
            billing_status="BILLING_NOT_CONNECTED",
        )
        self.tenant_repo.create(tenant)

        user = User(
            user_id=user_id,
            tenant_id=tenant_id,
            email=owner_email,
            display_name=owner_name,
            role="OWNER",
            status="ACTIVE",
            password_hash=hash_password(password) if password else None,
        )
        self.user_repo.create(user)

        self.audit_repo.log(
            AuditLogEntry(
                tenant_id=tenant_id,
                user_id=user_id,
                action="TENANT_REGISTERED",
                resource="tenant",
                resource_id=tenant_id,
                details={"org_name": org_name, "owner_email": owner_email},
            )
        )

        logger.info("Registered tenant '%s' with owner '%s'", tenant_id, user_id)
        return tenant, user

    def invite_member(
        self,
        inviter_user: User,
        email: str,
        role: str = "MEMBER",
        display_name: str = "",
    ) -> dict[str, Any]:
        """
        Invite a new member to the inviter's tenant.
        Explicitly notes email delivery status as NOT_CONFIGURED.
        """
        if not inviter_user.is_admin:
            raise PermissionError("Only OWNER or ADMIN may invite members.")

        tenant_id = inviter_user.tenant_id
        existing = self.user_repo.get_by_email(email, tenant_id)
        if existing:
            raise ValueError(f"User with email '{email}' already exists in this organization.")

        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        invited_user = User(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            display_name=display_name or email.split("@")[0],
            role=role.upper(),
            status="PENDING_INVITE",
            is_active=False,
        )
        self.user_repo.create(invited_user)

        self.audit_repo.log(
            AuditLogEntry(
                tenant_id=tenant_id,
                user_id=inviter_user.user_id,
                action="USER_INVITED",
                resource="user",
                resource_id=user_id,
                details={"invited_email": email, "role": role},
            )
        )

        return {
            "user_id": user_id,
            "email": email,
            "role": role,
            "status": "PENDING_INVITE",
            "outbound_email": "NOT_CONFIGURED",
            "invite_token": f"inv_{uuid.uuid4().hex}",
        }

    def change_member_role(
        self,
        actor: User,
        target_user_id: str,
        new_role: str,
    ) -> User:
        """Change a member's role. Only OWNER can reassign roles."""
        if not actor.is_owner:
            raise PermissionError("Only an OWNER can modify member roles.")

        target = self.user_repo.get(target_user_id, actor.tenant_id)
        if not target:
            raise KeyError(f"User '{target_user_id}' not found in tenant '{actor.tenant_id}'")

        old_role = target.role
        target.role = new_role.upper()
        updated = self.user_repo.update(target)

        self.audit_repo.log(
            AuditLogEntry(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                action="ROLE_CHANGED",
                resource="user",
                resource_id=target_user_id,
                details={"old_role": old_role, "new_role": target.role},
            )
        )
        return updated

    def remove_member(
        self,
        actor: User,
        target_user_id: str,
    ) -> bool:
        """Remove/deactivate a member. Prevent deleting the primary owner."""
        if not actor.is_admin:
            raise PermissionError("Only OWNER or ADMIN may remove members.")

        target = self.user_repo.get(target_user_id, actor.tenant_id)
        if not target:
            raise KeyError(f"User '{target_user_id}' not found in tenant '{actor.tenant_id}'")

        if target.is_owner:
            raise ValueError("The organization OWNER cannot be removed. Transfer ownership first.")

        success = self.user_repo.soft_delete(target_user_id, actor.tenant_id)

        self.audit_repo.log(
            AuditLogEntry(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                action="MEMBER_REMOVED",
                resource="user",
                resource_id=target_user_id,
                details={"removed_user": target_user_id},
            )
        )
        return success

    def export_tenant_data(self, actor: User) -> dict[str, Any]:
        """
        Aggregate all tenant-owned data into a secure export payload.
        Guarantees: Never exports another tenant's data or internal secrets.
        """
        tenant_id = actor.tenant_id
        watchlists = self.watchlist_repo.list_watchlists(tenant_id=tenant_id)
        alert_rules = self.alert_rule_repo.list_rules(tenant_id=tenant_id)
        prefs = self.alert_pref_repo.get(user_id=actor.user_id, tenant_id=tenant_id)
        members = self.user_repo.list(tenant_id=tenant_id)

        self.audit_repo.log(
            AuditLogEntry(
                tenant_id=tenant_id,
                user_id=actor.user_id,
                action="DATA_EXPORT_REQUESTED",
                resource="tenant",
                resource_id=tenant_id,
                details={"item_counts": {"watchlists": len(watchlists), "alerts": len(alert_rules)}},
            )
        )

        return {
            "export_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "export_status": "READY",
            "data": {
                "watchlists": [w.to_dict() for w in watchlists],
                "alert_rules": [r.to_dict() for r in alert_rules],
                "alert_preferences": prefs.to_dict() if prefs else None,
                "users": [u.to_dict(include_sensitive=False) for u in members],
            },
        }

    def soft_delete_tenant(self, actor: User) -> bool:
        """
        Soft-delete an entire tenant.
        Safe Invariant: Never deletes public legislative facts, state acts, or frozen predictions.
        """
        if not actor.is_owner:
            raise PermissionError("Only an OWNER can delete an organization.")

        tenant_id = actor.tenant_id
        success = self.tenant_repo.soft_delete(tenant_id)

        self.audit_repo.log(
            AuditLogEntry(
                tenant_id=tenant_id,
                user_id=actor.user_id,
                action="TENANT_DELETED",
                resource="tenant",
                resource_id=tenant_id,
                details={"deleted_by": actor.user_id},
            )
        )
        return success
