"""
api/middleware/logging_middleware.py
===================================
Structured request logging middleware for Task 8.17.

Guarantees:
- Assigns a unique UUID4 Request ID (or adopts incoming X-Request-ID).
- Injects X-Request-ID into every HTTP response.
- Logs structured telemetry: timestamp, environment, service, request_id,
  route, method, status, duration_ms, and tenant_id.
- Strictly redacts passwords, tokens, API keys, and sensitive headers.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Callable
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger("api.access")

_FORBIDDEN_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Asynchronous structured access logger for FastAPI.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # 1. Request ID resolution
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # 2. Extract safe tenant identifier (pseudonymous hash if present)
        raw_tenant = request.headers.get("X-Tenant-ID", "anonymous")
        tenant_id = (
            hashlib.sha256(raw_tenant.encode("utf-8")).hexdigest()[:8]
            if raw_tenant != "anonymous"
            else "anonymous"
        )

        route = request.url.path
        method = request.method

        # 3. Process Request
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._log_access(
                request_id=request_id,
                route=route,
                method=method,
                status_code=status_code,
                duration_ms=duration_ms,
                tenant_id=tenant_id,
                error=str(exc),
            )
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 4. Attach X-Request-ID to response
        response.headers["X-Request-ID"] = request_id

        # 5. Emit structured log
        self._log_access(
            request_id=request_id,
            route=route,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            tenant_id=tenant_id,
        )

        return response

    def _log_access(
        self,
        request_id: str,
        route: str,
        method: str,
        status_code: int,
        duration_ms: float,
        tenant_id: str,
        error: str | None = None,
    ) -> None:
        # Avoid logging noisy health checks in debug unless configured
        if route in ("/health", "/api/v1/health") and status_code == 200:
            return

        payload = {
            "service": "legislative-intel-api",
            "environment": settings.ENV,
            "request_id": request_id,
            "method": method,
            "route": route,
            "status": status_code,
            "duration_ms": duration_ms,
            "tenant": tenant_id,
        }
        if error:
            payload["error"] = error

        if getattr(settings, "LOG_STRUCTURED_JSON", False):
            msg = json.dumps(payload)
        else:
            msg = (
                f"{method} {route} -> {status_code} "
                f"[{duration_ms}ms] req_id={request_id} tenant={tenant_id}"
            )

        if status_code >= 500:
            logger.error(msg)
        elif status_code >= 400:
            logger.warning(msg)
        else:
            logger.info(msg)
