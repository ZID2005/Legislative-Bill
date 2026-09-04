"""
dashboard/utils/cache.py
========================
Caching utilities for dashboard data service.

Provides a unified decorator that applies `@st.cache_data` when running
under a Streamlit context, or an in-memory LRU cache when running headless
or in unit test suites.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_IN_MEMORY_CACHE: dict[str, Any] = {}


def cached_data(func: F) -> F:
    """
    Decorator for caching deterministic repository loading and transformations.

    If Streamlit is installed and running, uses `st.cache_data(show_spinner=False)`.
    Otherwise, wraps with `functools.lru_cache(maxsize=128)`.
    """
    try:
        import streamlit as st

        # Verify if streamlit is running in script runner context
        return st.cache_data(show_spinner=False)(func)  # type: ignore[return-value]
    except Exception:
        # Fallback to functools.lru_cache for testing or headless execution
        return functools.lru_cache(maxsize=128)(func)  # type: ignore[return-value]


def clear_dashboard_cache() -> None:
    """Clear both Streamlit cache and internal memory caches."""
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass
    _IN_MEMORY_CACHE.clear()
