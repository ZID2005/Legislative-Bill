"""
infrastructure/cache/__init__.py
================================
Distributed Caching & Coordination Provider Abstraction for Task 8.20.
"""

from infrastructure.cache.provider import (
    CacheProvider,
    DevelopmentCacheProvider,
    ProductionCacheProvider,
    get_cache_provider,
    reset_cache_provider,
)

__all__ = [
    "CacheProvider",
    "DevelopmentCacheProvider",
    "ProductionCacheProvider",
    "get_cache_provider",
    "reset_cache_provider",
]
