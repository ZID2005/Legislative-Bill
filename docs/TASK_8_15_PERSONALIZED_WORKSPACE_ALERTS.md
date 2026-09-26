# Task 8.15 — Personalized Watchlist, Alert & Decision Workspace

**Status**: Completed  
**Type**: Additive Integration & Product Feature  
**Date**: September 2026  

---

## 1. Executive Summary

Task 8.15 delivers the production-quality Personalized User Workspace, Watchlist Portfolio Hub, Real-Time Alert Manager, In-App Notification Center, and Grounded AI Decision Assistant on top of India Legislative Bill Tracker's existing multi-tenant legislative intelligence, quantitative predictions, corporate exposure, and monitoring pipeline.

The implementation strictly honors all frozen institutional baselines, epistemic labels, and security firewalls:
- **Zero Retraining & Zero Re-estimation**: All 4,700 frozen Central predictions, 4,700 decisions, and 940 anticipation scores remain unchanged and byte-for-byte intact.
- **State Stock Prediction Firewall**: State stock predictions remain strictly **0** (`is_state_firewall_active: true`).
- **Intelligence Company Firewall**: Non-quant corporate entities are protected from quantitative return predictions (`is_intelligence_firewall_active: true`).
- **Institutional Neutrality**: Strictly objective terminology; zero Buy/Sell/Hold ratings or political scoring.
- **Epistemic Labeling**: Strict semantic tagging with `[OBSERVED]`, `[DERIVED]`, and `[PREDICTION]`.

---

## 2. System Architecture & Endpoints

### 2.1 Backend Workspace Router (`/api/v1/workspace`)

| Endpoint | Method | Description | Guardrails & Firewalls |
| :--- | :--- | :--- | :--- |
| `/summary` | `GET` | Attention metrics: unread notifications count, active alerts count, watched bills/companies/industries counts, recent change counts. | Multi-tenant user isolation via `X-Tenant-ID` and `X-User-ID`. |
| `/activity` | `GET` | Unified real-time activity stream combining monitoring events, alert records, and legislative status transitions. | Epistemic tagging (`[OBSERVED]`, `[DERIVED]`, `[PREDICTION]`), severity sorting, deep links. |
| `/watchlist-activity` | `GET` | Activity partitioned across user's watched Bills, Companies, Industries, and Jurisdictions. | Scoped to entities in user's active watchlists. |
| `/analytics-snapshot` | `GET` | Resolved decision analytics: sector concentration, risk categories, anticipation tiers, quant predictions for watched portfolio. | O(1) file lookups; enforces State Firewall (`stock_predictions: 0`) and Qualitative Firewall (`quant_predictions: 0`). |
| `/digests` | `GET` | Digest feed of aggregated alert digests (Daily/Weekly) for the user. | Multi-channel delivery records with audit timestamps. |

### 2.2 Alert & Preference Management (`/api/v1/alerts`)

- `GET /api/v1/alerts`: List user alerts with filtering by `watchlist_id`, `severity`, `status`, `alert_type`, and `limit`.
- `POST /api/v1/alerts/{alert_id}/read`: Mark single alert as read.
- `POST /api/v1/alerts/{alert_id}/archive`: Archive alert.
- `POST /api/v1/alerts/read-all`: Bulk mark all matching alerts as read.
- `GET /api/v1/alerts/preferences`: Retrieve user alert preferences (channels, quiet hours, digest frequency, minimum severity).
- `PUT /api/v1/alerts/preferences`: Update user alert preferences.

### 2.3 Notification Center (`/api/v1/notifications`)

- `GET /api/v1/notifications`: Paginated in-app notification feed.
- `GET /api/v1/notifications/summary`: Summary metrics (unread count, pending count, total active).
- `POST /api/v1/notifications/{notification_id}/read`: Mark notification as read.
- `POST /api/v1/notifications/{notification_id}/archive`: Archive notification.
- `POST /api/v1/notifications/read-all`: Mark all unread notifications as read.
- `GET /api/v1/notifications/digests`: Aggregated periodic digests.

### 2.4 Grounded Workspace AI Assistant (`/api/v1/ai/ask`)

- Parameter: `context_type: "workspace"`, `context_id: "workspace_home"` (or `watchlist_id`).
- Grounded context incorporates:
  - User's active watchlists and monitored entities.
  - Recent high-priority unread alerts and monitoring events.
  - Epistemic grounding disclaimer and model provenance (`Groq LLaMA 3.3 70B`).

---

## 3. Frontend Implementation & UI Surface

### 3.1 Sidebar Navigation (`frontend/components/layout/Sidebar.tsx`)
Added primary `WORKSPACE` group at the top of the sidebar hierarchy:
- 📊 **Workspace**: `/workspace` (Attention summary, activity feed, entity overview, decision snapshot, AI assistant)
- ⭐ **Watchlists**: `/watchlists` (Portfolio management, items list, trigger rule engine)
- 🔔 **Alerts**: `/alerts` (Active alert inbox, severity filter, read/archive actions)
- 📬 **Notifications**: `/notifications` (In-app delivery feed & periodic aggregated digests)

### 3.2 Workspace Hub (`frontend/app/workspace/page.tsx`)
- **Section A (Attention Telemetry Header)**: Badges for Unread Alerts, Active Triggers, Monitored Bills, Monitored Companies, Monitored Industries.
- **Section B (Grounded AI Assistant)**: Quick prompt chips ("What changed in my watchlists?", "Summarize my unread alerts", "Which bills affect my companies?"), persona selector, citation provenance.
- **Section C (Dual-Column Activity Feed & Watched Entities)**:
  - Left column: Unified activity timeline with epistemic badges (`[OBSERVED]`, `[DERIVED]`, `[PREDICTION]`), severity indicators, deep links.
  - Right column: Watched entity pills grouped into Bills, Companies, Industries, and Jurisdictions.
- **Section D (Analytics & Decision Snapshot)**: Sector concentration breakdown, risk tier distribution (HIGH, MEDIUM, LOW), anticipation tiers, quantitative prediction count (with State and Qualitative firewall verification notes).
- **Section E (Notification Digest Viewer)**: Digest cards showing aggregated notifications grouped by time window.
- **Section F (Quick Actions Modal)**: Shortcuts to create watchlists, browse bills/companies/industries, and jump to preferences.

### 3.3 Watchlist Manager (`frontend/app/watchlists/page.tsx` & `[watchlistId]/page.tsx`)
- Create, rename, delete watchlists.
- Entity management: Add/remove Bills, Companies, and Industries to watchlists.
- Alert rule management: Attach trigger rules (`BILL_STATUS_CHANGE`, `AMENDMENT_DETECTED`, `RISK_SCORE_CHANGE`, `ANTICIPATION_UPDATE`), toggle enabled status, set severity thresholds and channels.

### 3.4 Alerts Inbox (`frontend/app/alerts/page.tsx`)
- Filter by severity (HIGH, MEDIUM, LOW), status (NEW, READ, RESOLVED, ARCHIVED), and entity search.
- Inline "Mark Read", "Archive", and bulk "Mark All Read".

### 3.5 Notifications & Digests (`frontend/app/notifications/page.tsx`)
- Tabbed interface between **In-App Delivery Feed** and **Periodic Aggregated Digests**.
- Unread counter, bulk mark read, channel tagging (`IN_APP`, `EMAIL`, `WEBHOOK`).

### 3.6 Settings & Alert Preferences (`frontend/app/settings/page.tsx`)
- Preferences controls for allowed channels, minimum severity, digest frequency, and quiet hours schedule.

### 3.7 Industry Watchlist Integration
- `IndustryWatchlistModal.tsx` and "⭐ Add to Watchlist" button on `IndustryHeader.tsx` enable one-click watchlist addition from industry pages.

---

## 4. Verification & Testing

### 4.1 Backend Test Coverage (10/10 Passing)
- `tests/test_workspace_api.py`: Tests `/summary`, `/activity`, `/watchlist-activity`, `/analytics-snapshot`, `/digests`.
- `tests/test_alert_preferences_api.py`: Tests alert preference CRUD and validation.
- `tests/test_monitoring_alert_integration.py`: Tests end-to-end monitoring event dispatch into alert matching pipeline.

### 4.2 Frontend Test Coverage (14/14 Passing)
- `frontend/__tests__/pages/workspace.test.tsx`: Tests telemetry metrics, activity feed, epistemic tags, AI prompt submission, error states.
- `frontend/__tests__/pages/watchlists.test.tsx`: Tests watchlist card render, count display, create modal submission, empty state.
- `frontend/__tests__/pages/alerts.test.tsx`: Tests alert filtering, mark as read, bulk mark all as read.
- `frontend/__tests__/pages/notifications.test.tsx`: Tests notification feed, digest tab switching, mark all as read.

---

## 5. Frozen Baseline & Firewall Invariants

```
Central Bills: 20
Central Securities: 47
Central Pairs: 940
Central Predictions: 4,700 (Unchanged)
Central Decisions: 4,700 (Unchanged)
Central Anticipation Scores: 940 (Unchanged)
Central Stakeholder Reports: 14,100 (Unchanged)

State Bills: 44
State Official PDFs: 44
State Knowledge Records: 44
State Corporate Exposures: 86
State Stock Predictions: 0 (State Prediction Firewall: ENFORCED)

Unified Legislative Records: 66
Unified Corporate Exposures: 104
Unified Companies: 70 (47 quant, 20 qualitative intelligence, 3 reference)
Qualitative Intelligence Quant Predictions: 0 (Qualitative Firewall: ENFORCED)
```
