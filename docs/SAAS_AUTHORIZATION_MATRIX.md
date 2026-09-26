# SaaS Authorization Matrix: Role × Resource × Action

**Document Version:** 1.0.0  
**Status:** Canonical & Production Enforced  
**Platform Milestone:** TASK 8.19 — SaaS Launch Readiness  
**Target Roles:** `OWNER`, `ADMIN`, `MEMBER`, `VIEWER`  
**Identity Source Policy:** Backend Authoritative (Strict Rejection of Spoofed `X-Tenant-ID` / `X-User-ID` in Production Mode)

---

## 1. Overview & Principles

The Legislative Intelligence platform enforces strict multi-tenant authorization boundaries. All authorization decisions are made **authoritatively by backend security dependencies** (`require_authenticated_user`, `require_role`, `verify_tenant_access`). 

### Core Tenets:
1. **Tenant Isolation:** A tenant (`Tenant A`) can under no circumstances read, modify, or infer data belonging to another tenant (`Tenant B`).
2. **Public Platform Immutability:** Shared legislative records, company intelligence catalogs, economic indices, and frozen quantitative event-study models are read-only across all roles. No role (even `OWNER`) may mutate frozen baseline analytical outputs.
3. **Role Scoping:**
   - **`OWNER`**: Complete organizational control, user invitation, role management, tenant deletion, billing configuration placeholders, and full workspace/AI capabilities.
   - **`ADMIN`**: User management, workspace oversight, watchlist/alert management, analytics, and AI. Cannot delete the tenant or transfer ownership.
   - **`MEMBER`**: Active collaboration within the tenant workspace; can create, manage, and share personal/tenant watchlists, configure alert rules, trigger AI queries, and manage personal notification preferences.
   - **`VIEWER`**: Read-only stakeholder access to authorized tenant watchlists, alerts, notifications, and analytics snapshots. Mutation actions (`POST`, `PUT`, `PATCH`, `DELETE`) are strictly forbidden (returning `403 Forbidden`).

---

## 2. Master Permission Matrix

| Resource Category | Specific Resource / Action | OWNER | ADMIN | MEMBER | VIEWER | Endpoint Pattern |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Organization & Tenant** | View Organization Profile | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/account/organization` |
| | Update Organization Settings | ✅ | ✅ | ❌ (403) | ❌ (403) | `PATCH /api/v1/account/organization` |
| | View Plan / Billing Status | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/account/plan` |
| | View Audit Trail | ✅ | ✅ | ❌ (403) | ❌ (403) | `GET /api/v1/account/audit-logs` |
| | Soft-Delete Tenant | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | `DELETE /api/v1/account/organization` |
| **User Management** | List Tenant Users | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/account/users` |
| | Invite Member / Admin | ✅ | ✅ | ❌ (403) | ❌ (403) | `POST /api/v1/account/invite` |
| | Modify User Role | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | `PATCH /api/v1/account/users/{id}/role` |
| | Deactivate / Remove User | ✅ | ✅ (Non-Owners) | ❌ (403) | ❌ (403) | `DELETE /api/v1/account/users/{id}` |
| | Soft-Delete Own Account | ✅ | ✅ | ✅ | ✅ | `DELETE /api/v1/account/me` |
| **Workspace & Telemetry** | View Workspace Summary | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/workspace` |
| | View Attention & Activity Feed | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/workspace/activity` |
| | View Analytics Snapshot | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/workspace/analytics` |
| | Export Workspace / Tenant Data | ✅ | ✅ | ❌ (403) | ❌ (403) | `POST /api/v1/account/export` |
| **Watchlists** | List Tenant Watchlists | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/watchlists` |
| | View Single Watchlist | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/watchlists/{id}` |
| | Create Watchlist | ✅ | ✅ | ✅ | ❌ (403) | `POST /api/v1/watchlists` |
| | Update Watchlist Metadata | ✅ | ✅ | ✅ | ❌ (403) | `PUT /api/v1/watchlists/{id}` |
| | Delete Watchlist | ✅ | ✅ | ✅ (Creator) | ❌ (403) | `DELETE /api/v1/watchlists/{id}` |
| | Add Item to Watchlist | ✅ | ✅ | ✅ | ❌ (403) | `POST /api/v1/watchlists/{id}/items` |
| | Remove Item from Watchlist | ✅ | ✅ | ✅ | ❌ (403) | `DELETE /api/v1/watchlists/{id}/items/{item_id}` |
| **Alert Rules** | List Tenant Alert Rules | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/alerts/rules` |
| | View Alert Rule | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/alerts/rules/{id}` |
| | Create Alert Rule | ✅ | ✅ | ✅ | ❌ (403) | `POST /api/v1/alerts/rules` |
| | Update / Toggle Alert Rule | ✅ | ✅ | ✅ | ❌ (403) | `PUT /api/v1/alerts/rules/{id}` |
| | Delete Alert Rule | ✅ | ✅ | ✅ (Creator) | ❌ (403) | `DELETE /api/v1/alerts/rules/{id}` |
| **In-App Notifications** | View Notification Feed | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/notifications` |
| | Mark Single Notification Read | ✅ | ✅ | ✅ | ✅ | `POST /api/v1/notifications/{id}/read` |
| | Mark All Notifications Read | ✅ | ✅ | ✅ | ✅ | `POST /api/v1/alerts/events/read-all` |
| | Archive Notification | ✅ | ✅ | ✅ | ❌ (403) | `POST /api/v1/notifications/{id}/archive` |
| | List Notification Digests | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/notifications/digests` |
| **Notification Preferences**| View Alert / Channel Preferences | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/alerts/preferences` |
| | Update Preferences | ✅ | ✅ | ✅ | ❌ (403) | `PATCH /api/v1/alerts/preferences` |
| **Grounded AI Copilot** | Execute Grounded AI Query | ✅ | ✅ | ✅ | ❌ (403) | `POST /api/v1/ai/ask` |
| | View Personal / Tenant AI Usage | ✅ | ✅ | ✅ | ✅ | `GET /api/v1/ai/usage` |
| | View Cross-Tenant AI Usage | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (403) | Blocked by Isolation Boundary |
| **Public Platform Data** | Bills (Central & State) | ✅ (Read) | ✅ (Read) | ✅ (Read) | ✅ (Read) | `GET /api/v1/bills/*` (Immutable) |
| *(Shared Knowledge)* | Companies & Dossiers | ✅ (Read) | ✅ (Read) | ✅ (Read) | ✅ (Read) | `GET /api/v1/companies/*` (Immutable) |
| | Industry Intelligence | ✅ (Read) | ✅ (Read) | ✅ (Read) | ✅ (Read) | `GET /api/v1/industries/*` (Immutable) |
| | Central Quant Predictions | ✅ (Read) | ✅ (Read) | ✅ (Read) | ✅ (Read) | `GET /api/v1/predictions/*` (Immutable) |
| | State Exposure & Knowledge | ✅ (Read) | ✅ (Read) | ✅ (Read) | ✅ (Read) | `GET /api/v1/states/*` (Immutable) |

---

## 3. IDOR Defense & Error Handling Standards

When an authenticated user requests a resource that belongs to another tenant or attempts an action disallowed by their role, the platform enforces strict security responses:

1. **Cross-Tenant Resource Requests:**
   - Always return `404 Not Found` (or `403 Forbidden` if existence cannot be masked) to prevent resource existence enumeration.
   - Example: Tenant B attempting `GET /api/v1/watchlists/{tenant_a_watchlist_id}` receives `404 Not Found` with message `"Watchlist not found"`.
2. **Unauthorized Role Mutation (Privilege Escalation):**
   - Returns `403 Forbidden` with detail `"Insufficient permissions for this action"`.
   - Example: `VIEWER` attempting `POST /api/v1/watchlists` receives `403 Forbidden`.
3. **Audit Log Generation:**
   - All authorization failures and security-sensitive mutations log structured audit records tagged with `user_id`, `tenant_id`, `resource`, `action`, `status="FAILURE"`, and client IP.

---

## 4. Verification & Automated Test Coverage

The enforcement of this authorization matrix is continuously validated through automated suites:
- `tests/test_saas_auth_lifecycle.py`: Role enforcement, session expiry, token validation.
- `tests/test_security_idor.py`: Cross-tenant boundary verification across 9 resource vectors.
- `tests/test_saas_multitenant_e2e.py`: Parallel tenant isolation under active concurrent mutations.
- `tests/test_saas_onboarding_and_lifecycle.py`: Invitation and role transitions.
