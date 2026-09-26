"""
api/errors.py
=============
Standardized error models, exception classes, and exception handlers
for the FastAPI REST API layer.

Follows the mandatory error response contract:
{
  "error": {
    "code": "BILL_NOT_FOUND",
    "message": "...",
    "details": {}
  }
}
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Error Schemas
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional context or validation details"
    )


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Custom API Exceptions
# ---------------------------------------------------------------------------


class APIError(Exception):
    """Base API exception that maps directly to the standard error response."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An unexpected error occurred.",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class NotFoundError(APIError):
    def __init__(
        self,
        message: str = "Resource not found.",
        code: str = "NOT_FOUND",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            message=message,
            details=details,
        )


class BadRequestError(APIError):
    def __init__(
        self,
        message: str = "Invalid request.",
        code: str = "BAD_REQUEST",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=code,
            message=message,
            details=details,
        )


class UnauthorizedError(APIError):
    def __init__(
        self,
        message: str = "Authentication required.",
        code: str = "UNAUTHORIZED",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            message=message,
            details=details,
        )


class ForbiddenError(APIError):
    def __init__(
        self,
        message: str = "Access denied.",
        code: str = "FORBIDDEN",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code=code,
            message=message,
            details=details,
        )


class ConflictError(APIError):
    def __init__(
        self,
        message: str = "Resource conflict.",
        code: str = "CONFLICT",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=code,
            message=message,
            details=details,
        )


# ---------------------------------------------------------------------------
# Exception Handlers Registration
# ---------------------------------------------------------------------------


def register_error_handlers(app: FastAPI) -> None:
    """Register uniform JSON error handlers on the FastAPI application."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            500: "INTERNAL_SERVER_ERROR",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        from fastapi.encoders import jsonable_encoder
        clean_errors = jsonable_encoder(exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request body or query parameter validation failed.",
                    "details": {"errors": clean_errors},
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled API error: %s", exc, exc_info=True)
        # Redact internal details in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "details": {},
                }
            },
        )
