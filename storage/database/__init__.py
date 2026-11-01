"""
storage/database/__init__.py
============================
Production SaaS Database Abstraction & Multi-Tenant Persistence Boundary.
Task 8.31D.
"""

from storage.database.provider import (
    DataClassification,
    DatabaseError,
    DatabaseProvider,
    DatabaseUnavailableError,
    DevelopmentDatabaseProvider,
    FrozenRecordImmutabilityError,
    PermissionDeniedError,
    ProductionDatabaseProvider,
    RecordNotFoundError,
    TenantMismatchError,
    get_database_provider,
    reset_database_provider,
)

__all__ = [
    "DataClassification",
    "DatabaseError",
    "DatabaseProvider",
    "DatabaseUnavailableError",
    "DevelopmentDatabaseProvider",
    "FrozenRecordImmutabilityError",
    "PermissionDeniedError",
    "ProductionDatabaseProvider",
    "RecordNotFoundError",
    "TenantMismatchError",
    "get_database_provider",
    "reset_database_provider",
]
