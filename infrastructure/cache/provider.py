"""
infrastructure/cache/provider.py
================================
Distributed Infrastructure & Cache Provider Boundary (Task 8.20).

Provides a unified boundary for:
1. Distributed Caching (query acceleration, API responses)
2. Distributed Rate Limiting (sliding window token bucket)
3. Session & Token Revocation (instant logout across multiple API replicas)
4. Distributed Scheduler & Worker Locks (prevents concurrent duplicate jobs)
5. Background Task Coordination

Guarantees:
- CacheProvider: Base abstract class defining the distributed contract.
- DevelopmentCacheProvider: High-performance, thread-safe in-memory cache with TTL,
  locks, and rate limiting for local development and testing.
- ProductionCacheProvider: Production Redis adapter architecture.
- If real Redis instance is not reachable/configured: REDIS_STATUS = NOT_CONFIGURED.
  Never claim Redis is operational without verification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import threading
import time
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Base Cache Provider Contract
# ---------------------------------------------------------------------------


class CacheProvider(ABC):
    """
    Abstract interface for distributed caching, locking, and rate limiting.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the cache provider."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether external cache infrastructure is configured."""
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> str:
        """Authoritative status: 'READY', 'CONFIGURED', or 'NOT_CONFIGURED'."""
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Retrieve a cached string value. Returns None if key missing or expired."""
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Set a string value with optional TTL expiration in seconds."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check whether key exists and is unexpired."""
        raise NotImplementedError

    @abstractmethod
    def acquire_lock(self, lock_name: str, timeout_seconds: float = 5.0, expire_seconds: int = 60) -> bool:
        """
        Acquire a named distributed lock to prevent duplicate concurrent jobs.
        Returns True if lock acquired, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def release_lock(self, lock_name: str) -> bool:
        """Release a previously acquired distributed lock."""
        raise NotImplementedError

    @abstractmethod
    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        """
        Check and record rate limit usage for a client or tenant.
        Returns: (allowed: bool, remaining_requests: int, reset_in_seconds: int)
        """
        raise NotImplementedError

    @abstractmethod
    def is_token_revoked(self, token: str) -> bool:
        """Check if an auth token / session has been revoked."""
        raise NotImplementedError

    @abstractmethod
    def revoke_token(self, token: str, ttl_seconds: int = 86400) -> None:
        """Add an auth token to the revoked session blacklist."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Check status and latency of the cache infrastructure."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Development In-Memory Cache Provider
# ---------------------------------------------------------------------------


class DevelopmentCacheProvider(CacheProvider):
    """
    Thread-safe in-memory cache, distributed lock, and rate limiter emulator.
    Requires zero external infrastructure, ideal for development, CI, and testing.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, tuple[str, Optional[float]]] = {}  # key -> (value, expiry_timestamp)
        self._locks: dict[str, float] = {}  # lock_name -> expiry_timestamp
        self._rate_limits: dict[str, list[float]] = {}  # key -> list of request timestamps
        self._revoked_tokens: dict[str, float] = {}  # token -> expiry_timestamp

    @property
    def provider_name(self) -> str:
        return "DevelopmentCacheProvider (In-Memory)"

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def status(self) -> str:
        return "READY"

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._store.items() if exp is not None and exp < now]
        for k in expired_keys:
            del self._store[k]

        expired_locks = [k for k, exp in self._locks.items() if exp < now]
        for k in expired_locks:
            del self._locks[k]

        expired_revocations = [k for k, exp in self._revoked_tokens.items() if exp < now]
        for k in expired_revocations:
            del self._revoked_tokens[k]

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            self._cleanup_expired()
            if key not in self._store:
                return None
            val, exp = self._store[key]
            if exp is not None and exp < time.time():
                del self._store[key]
                return None
            return val

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        with self._lock:
            exp = (time.time() + ttl_seconds) if ttl_seconds else None
            self._store[key] = (str(value), exp)
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def acquire_lock(self, lock_name: str, timeout_seconds: float = 5.0, expire_seconds: int = 60) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() <= deadline:
            with self._lock:
                now = time.time()
                # Check if current lock expired
                if lock_name in self._locks and self._locks[lock_name] < now:
                    del self._locks[lock_name]

                if lock_name not in self._locks:
                    self._locks[lock_name] = now + expire_seconds
                    return True
            time.sleep(0.05)
        return False

    def release_lock(self, lock_name: str) -> bool:
        with self._lock:
            if lock_name in self._locks:
                del self._locks[lock_name]
                return True
            return False

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        now = time.time()
        window_start = now - window_seconds
        with self._lock:
            timestamps = self._rate_limits.get(key, [])
            # Filter timestamps outside window
            valid_timestamps = [t for t in timestamps if t >= window_start]
            if len(valid_timestamps) >= max_requests:
                oldest = valid_timestamps[0]
                reset_in = int(max(1, (oldest + window_seconds) - now))
                self._rate_limits[key] = valid_timestamps
                return False, 0, reset_in

            valid_timestamps.append(now)
            self._rate_limits[key] = valid_timestamps
            remaining = max(0, max_requests - len(valid_timestamps))
            return True, remaining, window_seconds

    def is_token_revoked(self, token: str) -> bool:
        clean = token.replace("Bearer ", "").strip()
        with self._lock:
            if clean in self._revoked_tokens:
                if self._revoked_tokens[clean] >= time.time():
                    return True
                del self._revoked_tokens[clean]
            return False

    def revoke_token(self, token: str, ttl_seconds: int = 86400) -> None:
        clean = token.replace("Bearer ", "").strip()
        if clean:
            with self._lock:
                self._revoked_tokens[clean] = time.time() + ttl_seconds
                logger.info("Revoked session token in cache: %s...", clean[:10])

    def health_check(self) -> dict[str, Any]:
        with self._lock:
            return {
                "provider": self.provider_name,
                "status": "HEALTHY",
                "connected": True,
                "cached_keys_count": len(self._store),
                "active_locks_count": len(self._locks),
                "revoked_tokens_count": len(self._revoked_tokens),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# ---------------------------------------------------------------------------
# Production Redis Cache Provider
# ---------------------------------------------------------------------------


class ProductionCacheProvider(CacheProvider):
    """
    Production Redis cache provider supporting distributed locks, sliding rate limiting,
    and cluster-wide session revocation.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: int = 0,
        timeout: float = 2.0,
    ) -> None:
        self._redis_url = redis_url or os.getenv("REDIS_URL", "").strip()
        self._host = host or os.getenv("REDIS_HOST", "").strip()
        self._port = port or int(os.getenv("REDIS_PORT", "6379"))
        self._password = password or os.getenv("REDIS_PASSWORD", "")
        self._db = db
        self._timeout = timeout
        self._client: Any = None

        # Determine if real Redis configuration exists
        self._is_configured = bool(
            self._redis_url
            and not "placeholder" in self._redis_url.lower()
            and not self._redis_url.startswith("redis://:pass@localhost")
        ) or bool(self._host and self._host not in ("localhost", "127.0.0.1", ""))

    @property
    def provider_name(self) -> str:
        return "ProductionCacheProvider (Redis)"

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    @property
    def status(self) -> str:
        return "CONFIGURED" if self._is_configured else "NOT_CONFIGURED"

    def _get_client(self) -> Any:
        if not self._is_configured:
            return None
        if self._client is None:
            try:
                import redis  # type: ignore
                if self._redis_url:
                    self._client = redis.Redis.from_url(
                        self._redis_url,
                        socket_timeout=self._timeout,
                        socket_connect_timeout=self._timeout,
                        decode_responses=True,
                    )
                else:
                    self._client = redis.Redis(
                        host=self._host,
                        port=self._port,
                        password=self._password or None,
                        db=self._db,
                        socket_timeout=self._timeout,
                        socket_connect_timeout=self._timeout,
                        decode_responses=True,
                    )
            except Exception as e:
                logger.error("Failed to initialize Redis client: %s", e)
                self._client = None
        return self._client

    def get(self, key: str) -> Optional[str]:
        client = self._get_client()
        if not client:
            return None
        try:
            return client.get(key)
        except Exception as e:
            logger.warning("Redis get error for %s: %s", key, e)
            return None

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            if ttl_seconds:
                return bool(client.setex(key, ttl_seconds, str(value)))
            return bool(client.set(key, str(value)))
        except Exception as e:
            logger.warning("Redis set error for %s: %s", key, e)
            return False

    def delete(self, key: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            return bool(client.delete(key))
        except Exception as e:
            logger.warning("Redis delete error for %s: %s", key, e)
            return False

    def exists(self, key: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            return bool(client.exists(key))
        except Exception as e:
            logger.warning("Redis exists error for %s: %s", key, e)
            return False

    def acquire_lock(self, lock_name: str, timeout_seconds: float = 5.0, expire_seconds: int = 60) -> bool:
        client = self._get_client()
        if not client:
            return False
        key = f"lock:{lock_name}"
        deadline = time.time() + timeout_seconds
        while time.time() <= deadline:
            try:
                # Redis atomic SET NX EX
                acquired = client.set(key, "1", nx=True, ex=expire_seconds)
                if acquired:
                    return True
            except Exception as e:
                logger.warning("Redis lock acquire error for %s: %s", lock_name, e)
                return False
            time.sleep(0.05)
        return False

    def release_lock(self, lock_name: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            return bool(client.delete(f"lock:{lock_name}"))
        except Exception as e:
            logger.warning("Redis lock release error for %s: %s", lock_name, e)
            return False

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        client = self._get_client()
        if not client:
            # Fallback to permissive in absence of cache
            return True, max_requests, window_seconds

        rl_key = f"ratelimit:{key}"
        now = time.time()
        clear_before = now - window_seconds
        try:
            pipe = client.pipeline()
            pipe.zremrangebyscore(rl_key, 0, clear_before)
            pipe.zcard(rl_key)
            pipe.zadd(rl_key, {str(now): now})
            pipe.expire(rl_key, window_seconds)
            _, current_count, _, _ = pipe.execute()

            if current_count >= max_requests:
                return False, 0, window_seconds
            remaining = max(0, max_requests - (current_count + 1))
            return True, remaining, window_seconds
        except Exception as e:
            logger.warning("Redis rate limit check error for %s: %s", key, e)
            return True, max_requests, window_seconds

    def is_token_revoked(self, token: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        clean = token.replace("Bearer ", "").strip()
        try:
            return bool(client.exists(f"revoked:{clean}"))
        except Exception as e:
            logger.warning("Redis token revocation check error: %s", e)
            return False

    def revoke_token(self, token: str, ttl_seconds: int = 86400) -> None:
        client = self._get_client()
        if not client:
            return
        clean = token.replace("Bearer ", "").strip()
        try:
            client.setex(f"revoked:{clean}", ttl_seconds, "1")
            logger.info("Revoked token in Redis blacklist: %s...", clean[:10])
        except Exception as e:
            logger.warning("Redis token revoke error: %s", e)

    def health_check(self) -> dict[str, Any]:
        if not self._is_configured:
            return {
                "provider": self.provider_name,
                "status": "NOT_CONFIGURED",
                "connected": False,
                "message": "REDIS_URL or REDIS_HOST is not configured.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        client = self._get_client()
        if not client:
            return {
                "provider": self.provider_name,
                "status": "UNAVAILABLE",
                "connected": False,
                "message": "Failed to create Redis connection client.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            t0 = time.perf_counter()
            client.ping()
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            return {
                "provider": self.provider_name,
                "status": "HEALTHY",
                "connected": True,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "UNREACHABLE",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# ---------------------------------------------------------------------------
# Provider Factory & Lifecycle
# ---------------------------------------------------------------------------

_cache_provider_instance: Optional[CacheProvider] = None


def get_cache_provider() -> CacheProvider:
    """Return the active cache provider singleton."""
    global _cache_provider_instance
    if _cache_provider_instance is None:
        is_production = settings.ENV.lower() == "production"
        has_redis_url = bool(os.getenv("REDIS_URL", "").strip() or os.getenv("REDIS_HOST", "").strip())

        if is_production or has_redis_url:
            _cache_provider_instance = ProductionCacheProvider()
            logger.info("Initialized %s | status=%s", _cache_provider_instance.provider_name, _cache_provider_instance.status)
        else:
            _cache_provider_instance = DevelopmentCacheProvider()
            logger.info("Initialized %s | status=%s", _cache_provider_instance.provider_name, _cache_provider_instance.status)

    return _cache_provider_instance


def reset_cache_provider(provider: Optional[CacheProvider] = None) -> None:
    """Reset cache provider singleton for testing."""
    global _cache_provider_instance
    _cache_provider_instance = provider
