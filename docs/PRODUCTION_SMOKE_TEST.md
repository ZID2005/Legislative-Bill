# PRODUCTION SMOKE TEST

**Platform**: India Legislative Intelligence & Market Impact Platform  
**Milestone**: Task 8.21  
**Scope**: Post-deployment verification of all critical application paths  
**Status**: NOT_RUN (requires live deployment — CLOUD_DEPLOYMENT = NOT_DEPLOYED)  

---

> [!IMPORTANT]
> This smoke test is documented for execution **after** live cloud deployment is completed.
> Current status: CLOUD_DEPLOYMENT = NOT_DEPLOYED
> 
> Equivalent functional verification has been conducted at staging/local level via:
> - `pytest tests/` (2,159 tests, 100% pass)
> - `scripts/smoke_test_all_routes.py`
> - Frontend: `npm run test` (180 tests, 100% pass)

---

## 1. Smoke Test Procedure

### Prerequisites

Before running the smoke test:
1. All 4 ECS services must show `RUNNING` status
2. `/health` → `{"status": "healthy"}`
3. `/ready` → `{"status": "ready", "state_predictions": 0}`
4. Baseline verification: `python scripts/verify_frozen_baseline_exact.py` exits 0

### Test Environment Setup

```bash
# Set production base URLs
export API_BASE=https://api.legis-intel.in
export FRONTEND_BASE=https://app.legis-intel.in

# Use test credentials (pre-configured test tenant, deleted after smoke test)
export SMOKE_TEST_EMAIL=smoke-test@legis-test.internal
export SMOKE_TEST_TENANT=smoke-test-tenant-alpha
```

---

## 2. Public Route Verification

| Route | Method | Expected | Description |
|:------|:-------|:---------|:-----------|
| `GET /` | Browser | 200 + Landing page | Marketing/landing page |
| `GET /login` | Browser | 200 + Login form | Authentication page |
| `GET /bills` | Browser | 200 + Bill list | Public bill discovery |
| `GET /companies` | Browser | 200 + Company list | Public company discovery |
| `GET /industries` | Browser | 200 + Industry list | Public industry discovery |

### API Health

```bash
# Public API health
curl -s $API_BASE/health | python -m json.tool
curl -s $API_BASE/ready | python -m json.tool

# Verify state_predictions = 0 in ready response
curl -s $API_BASE/ready | python -c "
import sys, json
data = json.load(sys.stdin)
assert data.get('state_predictions', -1) == 0, 'STATE PREDICTION FIREWALL BREACH'
print('✅ State predictions = 0 (FIREWALLED)')
"
```

---

## 3. Authentication Smoke Test

```bash
# 1. Create test account (tenant Alpha)
curl -s -X POST $API_BASE/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "smoke-alpha@test.internal", "password": "TestSmoke!123", "tenant_name": "Smoke-Tenant-Alpha"}'

# 2. Login
TOKEN=$(curl -s -X POST $API_BASE/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "smoke-alpha@test.internal", "password": "TestSmoke!123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Verify token
curl -s -H "Authorization: Bearer $TOKEN" $API_BASE/api/v1/auth/me | python -m json.tool

# 4. Verify workspace access
curl -s -H "Authorization: Bearer $TOKEN" $API_BASE/api/v1/workspace | python -m json.tool
```

---

## 4. Authenticated Route Verification

| Route | Auth | Expected | Description |
|:------|:-----|:---------|:-----------|
| `GET /workspace` | Required | 200 + workspace data | Personal workspace |
| `GET /watchlists` | Required | 200 + watchlist array | Watchlist management |
| `GET /alerts` | Required | 200 + alert array | Alert management |
| `GET /notifications` | Required | 200 + notification feed | Notification center |
| `GET /settings` | Required | 200 + settings page | User/tenant settings |
| `GET /ai-analyst` | Required | 200 + AI interface | AI analyst page |

```bash
# Test authenticated routes
for route in /api/v1/workspace /api/v1/watchlists /api/v1/alerts /api/v1/notifications; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" $API_BASE$route)
  echo "$route → HTTP $STATUS"
done
```

---

## 5. Analytical Route Verification

| Route | Expected | Baseline Check |
|:------|:---------|:--------------|
| `GET /api/v1/bills` | 200 + 66 records | legislative_records = 66 |
| `GET /api/v1/companies` | 200 + 70 companies | companies = 70 |
| `GET /api/v1/predictions` | 200 + 4700 predictions | predictions = 4700 |
| `GET /api/v1/risk` | 200 + risk dashboard | — |
| `GET /api/v1/anticipation` | 200 + 940 scores | anticipation = 940 |
| `GET /api/v1/states` | 200 + 4 states | state_predictions = 0 |

```bash
# Verify analytical baselines
curl -s -H "Authorization: Bearer $TOKEN" $API_BASE/api/v1/bills \
  | python -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Bills: {d[\"total\"]} (expected 66)')"

# Critical: verify state pages show 0 predictions
curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/api/v1/states/karnataka" \
  | python -c "
import sys, json
d = json.load(sys.stdin)
predictions = d.get('stock_predictions', [])
assert len(predictions) == 0, f'STATE PREDICTION BREACH: {len(predictions)} predictions found'
print('✅ Karnataka state page: 0 predictions (FIREWALLED)')
"
```

---

## 6. Multi-Tenant Isolation Smoke Test

```bash
# Create Tenant Beta
curl -s -X POST $API_BASE/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "smoke-beta@test.internal", "password": "TestSmoke!456", "tenant_name": "Smoke-Tenant-Beta"}'

TOKEN_BETA=$(curl -s -X POST $API_BASE/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "smoke-beta@test.internal", "password": "TestSmoke!456"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create watchlist in Tenant Alpha
WATCHLIST_ID=$(curl -s -X POST $API_BASE/api/v1/watchlists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alpha Private Watchlist"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Attempt cross-tenant access (Tenant Beta accessing Alpha's watchlist)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN_BETA" \
  "$API_BASE/api/v1/watchlists/$WATCHLIST_ID")

if [ "$STATUS" = "403" ] || [ "$STATUS" = "404" ]; then
  echo "✅ Cross-tenant isolation: HTTP $STATUS (CORRECT)"
else
  echo "❌ SECURITY FAILURE: Cross-tenant access returned HTTP $STATUS"
  exit 1
fi
```

---

## 7. AI Analyst Smoke Test

```bash
# Test AI analyst (must not generate predictions or recommendations)
curl -s -X POST $API_BASE/api/v1/ai/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key provisions of the Budget 2024 bill?", "context_type": "bill"}' \
  | python -c "
import sys, json
d = json.load(sys.stdin)
answer = d.get('answer', '')
# Verify answer contains epistemic tags
assert any(tag in answer for tag in ['[FACT]', '[OBSERVED]', '[DERIVED]', '[INTERPRETATION]']), \
    'AI response missing epistemic grounding tags'
print('✅ AI analyst response includes epistemic grounding')
# Verify no financial recommendations
forbidden = ['buy', 'sell', 'invest', 'recommend purchasing', 'recommend selling']
for word in forbidden:
    assert word.lower() not in answer.lower(), f'AI generated forbidden financial recommendation: {word}'
print('✅ AI analyst: no financial recommendations detected')
"
```

---

## 8. Performance Verification

Run performance benchmarks after deployment and compare with Task 8.20A staging baseline:

```bash
python scripts/benchmark_task_8_20_performance.py --base-url $API_BASE --token $TOKEN
```

| Endpoint | Task 8.20A Staging | Production Target |
|:---------|:-------------------|:------------------|
| `/auth/login` | 83.08 ms | ≤ 250 ms |
| `/auth/me` | 8.19 ms | ≤ 50 ms |
| `/workspace` | 8.37 ms | ≤ 50 ms |
| `/watchlists` | 7.15 ms | ≤ 50 ms |
| `/notifications` | 7.50 ms | ≤ 50 ms |
| `/search` | 693.78 ms | ≤ 2000 ms ⚠️ |
| `/ai/ask` | 95.96 ms | ≤ 500 ms |
| `/bills/{id}` | 6.14 ms | ≤ 50 ms |
| `/companies/{id}` | 39.22 ms | ≤ 200 ms |

> [!WARNING]
> `/search` at 693.78 ms in staging is already slow. Production with managed DB may differ.
> If search remains above 2000 ms in production, create a follow-up optimization task.
> Do **not** modify search semantics to improve latency.

---

## 9. Cleanup After Smoke Test

```bash
# Delete test tenant accounts (clean up smoke test data)
curl -s -X DELETE $API_BASE/api/v1/admin/tenants/smoke-test-tenant-alpha \
  -H "Authorization: Bearer $ADMIN_TOKEN"

curl -s -X DELETE $API_BASE/api/v1/admin/tenants/smoke-test-tenant-beta \
  -H "Authorization: Bearer $ADMIN_TOKEN"

echo "✅ Smoke test data cleaned up"
```

---

## 10. Smoke Test Pass Criteria

| Check | Expected | Pass Condition |
|:------|:---------|:--------------|
| Health endpoint | HTTP 200 | `status = "healthy"` |
| Ready endpoint | HTTP 200 | `status = "ready"` |
| State predictions | 0 | `state_predictions = 0` in /ready |
| Login flow | HTTP 200 | Valid JWT returned |
| Public pages | HTTP 200 | All 5 public routes respond |
| Authenticated routes | HTTP 200 | All 6 auth routes respond |
| Analytical baseline | 66 records, 70 companies | Counts match |
| Cross-tenant access | HTTP 403 or 404 | Zero data leakage |
| AI response | Grounded answer | Epistemic tags present |
| No financial recommendations | No buy/sell | Clean AI output |

**SMOKE_TEST_PASS** = All 10 checks pass with zero failures.

---

## 11. Current Status

```
PRODUCTION_SMOKE_TEST = NOT_RUN
Reason: CLOUD_DEPLOYMENT = NOT_DEPLOYED
Next step: Provision AWS ECS/Fargate environment and re-run this smoke test
```

Equivalent verification at local/staging level:
- Backend: 2,159 tests passed (100%)
- Frontend: 180 tests passed (100%)
- Security: 49 security tests passed (100%)
- Baseline: All values match authoritative frozen baseline exactly
