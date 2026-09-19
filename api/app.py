"""
api/app.py
==========
Main FastAPI application entrypoint for the Indian Parliamentary Intelligence
& Market Impact Platform.

Exposes REST APIs for consumption by the SaaS frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.errors import register_error_handlers
from api.routers import (
    ai,
    alerts,
    bills,
    companies,
    coverage,
    monitoring,
    notifications,
    predictions,
    search,
    states,
    watchlists,
)
from api.schemas import HealthResponse
from config.settings import settings


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
    # CORS Middleware
    # -----------------------------------------------------------------------
    cors_origins = getattr(settings, "API_CORS_ORIGINS", ["*"])
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Exception Handlers
    # -----------------------------------------------------------------------
    register_error_handlers(application)

    # -----------------------------------------------------------------------
    # Health Endpoints
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
        return _health_payload()

    @application.get(f"{settings.API_V1_STR}/health", response_model=HealthResponse, tags=["Health"])
    def api_v1_health() -> HealthResponse:
        return _health_payload()

    # -----------------------------------------------------------------------
    # Mount Sub-Routers under /api/v1
    # -----------------------------------------------------------------------
    prefix = settings.API_V1_STR
    application.include_router(bills.router, prefix=prefix)
    application.include_router(companies.router, prefix=prefix)
    application.include_router(predictions.router, prefix=prefix)
    application.include_router(states.router, prefix=prefix)
    application.include_router(search.router, prefix=prefix)
    application.include_router(coverage.router, prefix=prefix)
    application.include_router(monitoring.router, prefix=prefix)
    application.include_router(watchlists.router, prefix=prefix)
    application.include_router(alerts.router, prefix=prefix)
    application.include_router(notifications.router, prefix=prefix)
    application.include_router(ai.router, prefix=prefix)

    return application


app = create_app()
