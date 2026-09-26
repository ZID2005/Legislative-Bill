"""
api/auth/__init__.py
====================
Authentication and multi-tenant authorization interfaces for Task 8.17.
"""

from api.auth.provider import (
    BaseAuthProvider,
    CurrentUser,
    DevelopmentAuthProvider,
    ProductionAuthProvider,
    get_auth_provider,
)

__all__ = [
    "BaseAuthProvider",
    "CurrentUser",
    "DevelopmentAuthProvider",
    "ProductionAuthProvider",
    "get_auth_provider",
]
