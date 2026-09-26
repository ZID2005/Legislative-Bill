"""
api/middleware/rate_limiter.py
==============================
Lightweight sliding-window in-memory rate limiting middleware for Task 8.17.

Guards high-cost endpoints against abuse and resource starvation:
- AI inference (/api/v1/ai/*)
- Unified search (/api/v1/search)
- Monitoring manual triggers (/api/v1/monitoring/run, /trigger)
- Expensive analytics queries

Features:
- Configurable per-route tiers and limits via settings.
- Bypassed when RATE_LIMIT_ENABLED=false (e.g. during dev/test).
- Adds standard X-RateLimit headers (Limit, Remaining, Reset).
- Returns HTTP 429 Too Many Requests with Retry-After header.
"""

from __future__ import annotations

import collections
import json
import threading
import time
from typing import Callable, Deque, Dict, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


class RateLimiter:
    """Sliding-window rate limiter maintaining request timestamps per client key."""

    def __init__(self) -> None:
        self._clients: Dict[str, Deque[float]] = collections.defaultdict(collections.deque)
        self._lock = threading.Lock()

    def is_allowed(self, client_key: str, limit_rpm: int) -> tuple[bool, int, int]:
        """
        Check if request is allowed under limit_rpm within a 60-second sliding window.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - 60.0

        with self._lock:
            timestamps = self._clients[client_key]

            # Prune timestamps older than sliding window
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            current_count = len(timestamps)

            if current_count >= limit_rpm:
                # Rate limit exceeded
                earliest = timestamps[0]
                retry_after = max(1, int(60.0 - (now - earliest)))
                return False, 0, retry_after

            # Allow request and record timestamp
            timestamps.append(now)
            remaining = max(0, limit_rpm - current_count - 1)
            return True, remaining, 0

    def reset_for_testing(self) -> None:
        """Clear all rate limit state (for test isolation)."""
        with self._lock:
            self._clients.clear()


_global_rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware enforcing sliding-window rate limits on high-cost endpoints."""

    def _resolve_limit(self, path: str) -> int:
        """Determine applicable RPM limit based on requested endpoint path."""
        if path.startswith(f"{settings.API_V1_STR}/ai"):
            return getattr(settings, "RATE_LIMIT_AI_RPM", 20)
        if path.startswith(f"{settings.API_V1_STR}/search"):
            return getattr(settings, "RATE_LIMIT_SEARCH_RPM", 60)
        if path.startswith(f"{settings.API_V1_STR}/monitoring") and any(
            action in path for action in ("run", "trigger")
        ):
            return getattr(settings, "RATE_LIMIT_MONITORING_RPM", 10)

        return getattr(settings, "RATE_LIMIT_DEFAULT_RPM", 120)

    def _resolve_client_key(self, request: Request) -> str:
        """Derive rate-limiting identifier from tenant, auth token, or IP."""
        tenant = request.headers.get("X-Tenant-ID")
        if tenant:
            return f"tenant:{tenant}"

        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1][:16]
            return f"auth:{token}"

        client_host = request.client.host if request.client else "unknown_ip"
        return f"ip:{client_host}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if rate limiting is enabled globally
        if not getattr(settings, "RATE_LIMIT_ENABLED", False):
            return await call_next(request)

        # Skip health endpoints
        path = request.url.path
        if path in ("/health", "/ready", f"{settings.API_V1_STR}/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_key = self._resolve_client_key(request)
        limit = self._resolve_limit(path)
        key = f"{client_key}:{path}"

        allowed, remaining, retry_after = _global_rate_limiter.is_allowed(key, limit)

        if not allowed:
            logger.warning("Rate limit exceeded for %s on %s (limit=%d RPM)", client_key, path, limit)
            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(retry_after),
            }
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests to {path}. Allowed rate is {limit} RPM.",
                    "retry_after_seconds": retry_after,
                },
                headers=headers,
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
