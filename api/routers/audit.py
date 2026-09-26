"""
api/routers/audit.py
====================
Audit log retrieval endpoints for tenant administrators (Task 8.19).

Enforces:
1. Strict tenant boundary isolation — caller can only view audit trails for their own tenant.
2. RBAC: Restricted to OWNER and ADMIN roles.
3. Redaction: Zero sensitive payload/credential leakage.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.auth.provider import CurrentUser
from api.dependencies import get_audit_log_repository, require_admin
from storage.audit_log_repository import AuditLogRepository

router = APIRouter(prefix="/audit", tags=["Security & Audit"])


@router.get(
    "/logs",
    summary="List Tenant Audit Logs",
    description="Retrieve chronological security and administrative audit entries for the caller's tenant (OWNER/ADMIN only).",
)
def list_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action verb"),
    resource: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: CurrentUser = Depends(require_admin),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> dict[str, Any]:
    entries = audit_repo.list_entries(
        tenant_id=current_user.tenant_id,
        user_id=user_id,
        action=action,
        resource=resource,
        limit=limit,
        offset=offset,
    )

    return {
        "tenant_id": current_user.tenant_id,
        "count": len(entries),
        "limit": limit,
        "offset": offset,
        "items": [e.to_dict() for e in entries],
    }
