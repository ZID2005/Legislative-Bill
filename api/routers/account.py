"""
api/routers/account.py
======================
Account and organization lifecycle, member management, data export, and deletion (Task 8.19).

Enforces:
1. Strict tenant boundary isolation.
2. RBAC enforcement:
   - Organization deletion and role changes restricted to OWNER.
   - Member invites and data exports restricted to OWNER or ADMIN.
3. Safe tenant deletion preserves frozen analytical and public legislative datasets.
4. Outbound invitations clearly marked as NOT_CONFIGURED.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from api.auth.provider import CurrentUser
from api.dependencies import (
    get_account_service,
    get_current_user,
    get_tenant_repository,
    get_user_repository,
    require_admin,
    require_owner,
)
from api.errors import BadRequestError, ForbiddenError, NotFoundError
from schemas.tenant import Tenant
from schemas.user import User
from services.account_service import AccountService
from storage.tenant_repository import TenantRepository
from storage.user_repository import UserRepository

router = APIRouter(prefix="/account", tags=["Account & Organization"])


class RegisterTenantRequest(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=100)
    owner_email: str = Field(..., min_length=5, max_length=100)
    owner_name: str = Field(..., min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    tenant_id: Optional[str] = None


class RegisterTenantResponse(BaseModel):
    tenant_id: str
    organization_name: str
    owner_user_id: str
    owner_email: str
    plan_tier: str
    billing_status: str


class OrganizationResponse(BaseModel):
    tenant_id: str
    name: str
    status: str
    plan_tier: str
    billing_status: str
    owner_user_id: str
    created_at: str
    updated_at: str
    member_count: int


class UpdateOrgRequest(BaseModel):
    name: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class InviteMemberRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    role: str = Field("MEMBER", description="Role to assign: ADMIN, MEMBER, VIEWER")
    display_name: Optional[str] = None


class ChangeRoleRequest(BaseModel):
    role: str = Field(..., description="New role: OWNER, ADMIN, MEMBER, VIEWER")


@router.post(
    "/register",
    response_model=RegisterTenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Organization & Owner",
    description="Provision a new tenant organization and initial OWNER account.",
)
def register_tenant(
    req: RegisterTenantRequest,
    account_service: AccountService = Depends(get_account_service),
) -> RegisterTenantResponse:
    try:
        tenant, user = account_service.register_tenant_and_owner(
            org_name=req.organization_name,
            owner_email=req.owner_email,
            owner_name=req.owner_name,
            password=req.password,
            tenant_id=req.tenant_id,
        )
        return RegisterTenantResponse(
            tenant_id=tenant.tenant_id,
            organization_name=tenant.name,
            owner_user_id=user.user_id,
            owner_email=user.email or req.owner_email,
            plan_tier=tenant.plan_tier,
            billing_status=tenant.billing_status,
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))


@router.get(
    "/organization",
    response_model=OrganizationResponse,
    summary="Get Organization Details",
    description="Retrieve metadata, tier placeholder, and member count for the caller's organization.",
)
def get_organization(
    current_user: CurrentUser = Depends(get_current_user),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> OrganizationResponse:
    tenant = tenant_repo.get(current_user.tenant_id)
    if not tenant:
        # Fallback default tenant object
        tenant = Tenant(tenant_id=current_user.tenant_id, name="Default Organization")

    members = user_repo.list(tenant_id=current_user.tenant_id)
    return OrganizationResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        status=tenant.status,
        plan_tier=tenant.plan_tier,
        billing_status=tenant.billing_status,
        owner_user_id=tenant.owner_user_id,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        member_count=len(members),
    )


@router.patch(
    "/organization",
    response_model=OrganizationResponse,
    summary="Update Organization",
    description="Update organization name and configuration metadata (OWNER/ADMIN only).",
)
def update_organization(
    req: UpdateOrgRequest,
    current_user: CurrentUser = Depends(require_admin),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> OrganizationResponse:
    tenant = tenant_repo.get(current_user.tenant_id)
    if not tenant:
        raise NotFoundError(message=f"Tenant '{current_user.tenant_id}' not found.")

    if req.name:
        tenant.name = req.name.strip()
    if req.metadata:
        tenant.metadata.update(req.metadata)

    updated = tenant_repo.update(tenant)
    members = user_repo.list(tenant_id=current_user.tenant_id)

    return OrganizationResponse(
        tenant_id=updated.tenant_id,
        name=updated.name,
        status=updated.status,
        plan_tier=updated.plan_tier,
        billing_status=updated.billing_status,
        owner_user_id=updated.owner_user_id,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        member_count=len(members),
    )


@router.get(
    "/members",
    summary="List Organization Members",
    description="List all registered and invited users belonging to the caller's tenant.",
)
def list_members(
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, Any]:
    members = user_repo.list(tenant_id=current_user.tenant_id)
    return {
        "tenant_id": current_user.tenant_id,
        "total_members": len(members),
        "items": [u.to_dict(include_sensitive=False) for u in members],
    }


@router.post(
    "/invite",
    status_code=status.HTTP_201_CREATED,
    summary="Invite Member",
    description="Invite a new member to the organization (OWNER/ADMIN only). Email delivery is marked NOT_CONFIGURED.",
)
def invite_member(
    req: InviteMemberRequest,
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, Any]:
    actor = user_repo.get(current_user.user_id, current_user.tenant_id) or User(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        role=current_user.role,
    )
    try:
        return account_service.invite_member(
            inviter_user=actor,
            email=req.email,
            role=req.role,
            display_name=req.display_name or "",
        )
    except PermissionError as pe:
        raise ForbiddenError(message=str(pe))
    except ValueError as ve:
        raise BadRequestError(message=str(ve))


@router.patch(
    "/members/{target_user_id}/role",
    summary="Change Member Role",
    description="Modify a member's role (OWNER only).",
)
def change_role(
    target_user_id: str,
    req: ChangeRoleRequest,
    current_user: CurrentUser = Depends(require_owner),
    account_service: AccountService = Depends(get_account_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, Any]:
    actor = user_repo.get(current_user.user_id, current_user.tenant_id) or User(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        role="OWNER",
    )
    try:
        updated = account_service.change_member_role(
            actor=actor,
            target_user_id=target_user_id,
            new_role=req.role,
        )
        return {
            "status": "success",
            "user_id": updated.user_id,
            "role": updated.role,
            "message": f"Role updated to {updated.role}",
        }
    except KeyError as ke:
        raise NotFoundError(message=str(ke))
    except PermissionError as pe:
        raise ForbiddenError(message=str(pe))
    except ValueError as ve:
        raise BadRequestError(message=str(ve))


@router.delete(
    "/members/{target_user_id}",
    summary="Remove Member",
    description="Deactivate a member from the organization (OWNER/ADMIN only).",
)
def remove_member(
    target_user_id: str,
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, Any]:
    actor = user_repo.get(current_user.user_id, current_user.tenant_id) or User(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        role=current_user.role,
    )
    try:
        success = account_service.remove_member(actor=actor, target_user_id=target_user_id)
        if not success:
            raise NotFoundError(message=f"Member '{target_user_id}' not found.")
        return {"status": "success", "message": f"Member '{target_user_id}' removed."}
    except KeyError as ke:
        raise NotFoundError(message=str(ke))
    except PermissionError as pe:
        raise ForbiddenError(message=str(pe))
    except ValueError as ve:
        raise BadRequestError(message=str(ve))


@router.get(
    "/export",
    summary="Export Tenant Data",
    description="Generate a complete archive of tenant-owned watchlists, alert rules, and preferences (OWNER/ADMIN only).",
)
@router.post(
    "/export",
    summary="Export Tenant Data",
    description="Generate a complete archive of tenant-owned watchlists, alert rules, and preferences (OWNER/ADMIN only).",
)
def export_data(
    current_user: CurrentUser = Depends(require_admin),
    account_service: AccountService = Depends(get_account_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, Any]:
    actor = user_repo.get(current_user.user_id, current_user.tenant_id) or User(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        role=current_user.role,
    )
    return account_service.export_tenant_data(actor)


@router.delete(
    "/tenant",
    summary="Soft-Delete Organization",
    description="Soft-delete the tenant organization (OWNER only). Never deletes public legislative records or frozen analytical baselines.",
)
def delete_tenant(
    current_user: CurrentUser = Depends(require_owner),
    account_service: AccountService = Depends(get_account_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict[str, Any]:
    actor = user_repo.get(current_user.user_id, current_user.tenant_id) or User(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        role="OWNER",
    )
    try:
        success = account_service.soft_delete_tenant(actor)
        if not success:
            raise NotFoundError(message=f"Tenant '{current_user.tenant_id}' not found.")
        return {
            "status": "DELETED",
            "tenant_id": current_user.tenant_id,
            "message": "Organization soft-deleted safely. Public legislative and frozen datasets remain intact.",
        }
    except PermissionError as pe:
        raise ForbiddenError(message=str(pe))
