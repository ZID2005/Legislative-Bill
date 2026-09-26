"""
api/app.py
==========
Main FastAPI application entrypoint for the Indian Parliamentary Intelligence
& Market Impact Platform.

Exposes REST APIs for consumption by the SaaS frontend.
Hardened for Task 8.17 Production Readiness:
- Structured logging middleware with X-Request-ID
- OWASP security headers middleware
- Configurable sliding-window rate limiter
- Liveness (/health) and Readiness (/ready) health probes
- Production-restricted CORS policy
- Central & State data freshness router (/api/v1/freshness)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from api.errors import register_error_handlers
from api.middleware.logging_middleware import LoggingMiddleware
from api.middleware.rate_limiter import RateLimitMiddleware
from api.middleware.security_headers import SecurityHeadersMiddleware
from api.routers import (
    account,
    ai,
    alerts,
    anticipation,
    audit,
    auth,
    bills,
    companies,
    coverage,
    freshness,
    industries,
    monitoring,
    notifications,
    predictions,
    risk,
    search,
    states,
    watchlists,
    workspace,
)
from api.schemas import HealthResponse
from config.settings import settings
from services.startup_validator import get_startup_validator


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    application = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=(
            "Production-facing REST API for the Indian Parliamentary Intelligence & "
            "Market Impact Platform. Serves Central/State legislative records, corporate "
            "exposure networks, backtested prediction engines, and multi-tenant watchlists & alerts."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # -----------------------------------------------------------------------
    # Middlewares (Ordered from innermost to outermost)
    # -----------------------------------------------------------------------
    # 1. Rate Limiting Middleware
    application.add_middleware(RateLimitMiddleware)

    # 2. Security Headers Middleware
    application.add_middleware(SecurityHeadersMiddleware)

    # 3. Access Logging & Request ID Middleware
    application.add_middleware(LoggingMiddleware)

    # 4. CORS Middleware
    cors_origins = list(getattr(settings, "API_CORS_ORIGINS", []))
    is_prod = settings.ENV.lower() == "production"

    # In production, reject '*' wildcard when credentials are enabled
    if is_prod and ("*" in cors_origins or not cors_origins):
        cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # -----------------------------------------------------------------------
    # Exception Handlers
    # -----------------------------------------------------------------------
    register_error_handlers(application)

    # -----------------------------------------------------------------------
    # Health & Readiness Endpoints
    # -----------------------------------------------------------------------
    def _health_payload() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            api_version=settings.API_VERSION,
            environment=settings.ENV,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @application.get("/health", response_model=HealthResponse, tags=["Health"])
    def root_health() -> HealthResponse:
        """Liveness probe: verifies process is running and responding."""
        return _health_payload()

    @application.get("/ready", tags=["Health"])
    @application.get("/health/ready", tags=["Health"])
    def readiness_probe(response: Response) -> dict[str, Any]:
        """
        Readiness probe: verifies essential storage, baseline contracts,
        and operational subsystems are ready to serve production traffic.
        """
        validator = get_startup_validator()
        report = validator.run_validation(strict=False)

        if not report.can_start:
            response.status_code = 503
            return {
                "status": "not_ready",
                "environment": settings.ENV,
                "critical_failures": report.critical_failures,
                "summary": report.status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return {
            "status": "ready",
            "environment": settings.ENV,
            "summary": report.status,
            "passed_checks": report.passed_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @application.get(f"{settings.API_V1_STR}/health", response_model=HealthResponse, tags=["Health"])
    def api_v1_health() -> HealthResponse:
        """API v1 Health check endpoint."""
        return _health_payload()

    # -----------------------------------------------------------------------
    # Mount Sub-Routers under /api/v1
    # -----------------------------------------------------------------------
    prefix = settings.API_V1_STR
    application.include_router(auth.router, prefix=prefix)
    application.include_router(account.router, prefix=prefix)
    application.include_router(audit.router, prefix=prefix)
    application.include_router(bills.router, prefix=prefix)
    application.include_router(companies.router, prefix=prefix)
    application.include_router(industries.router, prefix=prefix)
    application.include_router(predictions.router, prefix=prefix)
    application.include_router(states.router, prefix=prefix)
    application.include_router(search.router, prefix=prefix)
    application.include_router(coverage.router, prefix=prefix)
    application.include_router(monitoring.router, prefix=prefix)
    application.include_router(watchlists.router, prefix=prefix)
    application.include_router(alerts.router, prefix=prefix)
    application.include_router(notifications.router, prefix=prefix)
    application.include_router(ai.router, prefix=prefix)
    application.include_router(risk.router, prefix=prefix)
    application.include_router(anticipation.router, prefix=prefix)
    application.include_router(workspace.router, prefix=prefix)
    application.include_router(freshness.router, prefix=prefix)

    # -----------------------------------------------------------------------
    # Startup Lifecycle Hook
    # -----------------------------------------------------------------------
    @application.on_event("startup")
    def on_startup() -> None:
        validator = get_startup_validator()
        validator.run_validation(strict=False)

    return application


app = create_app()
