"""
api/middleware/security_headers.py
==================================
Security headers middleware for Task 8.17.

Injects OWASP-recommended defensive HTTP headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: geolocation=(), camera=(), microphone=()
- Strict-Transport-Security: max-age=31536000; includeSubDomains (production)
"""

from __future__ import annotations

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies security headers to every outgoing HTTP response.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Apply standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # HSTS in production environments
        if settings.ENV.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
