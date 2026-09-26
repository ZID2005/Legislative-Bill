"""
tests/test_security_headers_ratelimit.py
========================================
Unit tests for Task 8.17 Security Headers and Rate Limiting.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.middleware.rate_limiter import _global_rate_limiter
from config.settings import settings

client = TestClient(app)


def test_security_headers_applied() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in resp.headers.get("Permissions-Policy", "")


def test_rate_limiter_allows_under_limit() -> None:
    _global_rate_limiter.reset_for_testing()
    allowed, remaining, retry_after = _global_rate_limiter.is_allowed("test_client", 5)
    assert allowed is True
    assert remaining == 4
    assert retry_after == 0


def test_rate_limiter_blocks_over_limit() -> None:
    _global_rate_limiter.reset_for_testing()
    limit = 3
    for _ in range(limit):
        allowed, _, _ = _global_rate_limiter.is_allowed("test_client_blocked", limit)
        assert allowed is True

    # Next request should be blocked
    allowed, remaining, retry_after = _global_rate_limiter.is_allowed("test_client_blocked", limit)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


def test_rate_limit_middleware_with_enabled_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    _global_rate_limiter.reset_for_testing()
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_AI_RPM", 2)

    headers = {"X-Tenant-ID": "rate_limit_test_tenant"}

    # Request 1: allowed
    r1 = client.post(
        "/api/v1/ai/ask",
        json={"question": "test", "context_type": "bill", "context_id": "test"},
        headers=headers,
    )
    assert r1.status_code != 429

    # Request 2: allowed
    r2 = client.post(
        "/api/v1/ai/ask",
        json={"question": "test", "context_type": "bill", "context_id": "test"},
        headers=headers,
    )
    assert r2.status_code != 429

    # Request 3: blocked with 429
    r3 = client.post(
        "/api/v1/ai/ask",
        json={"question": "test", "context_type": "bill", "context_id": "test"},
        headers=headers,
    )
    assert r3.status_code == 429
    assert r3.json()["error"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in r3.headers

    # Cleanup
    _global_rate_limiter.reset_for_testing()
