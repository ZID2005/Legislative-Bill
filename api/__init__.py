"""
api package initialization.
Exposes the FastAPI application instance.
"""

from api.app import app, create_app

__all__ = ["app", "create_app"]
