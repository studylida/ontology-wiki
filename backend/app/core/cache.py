"""Cache and Distributed Presence Lock Manager.

Supports Redis 7.2 with transparent in-memory TTL fallback.
"""
import time
import json
import logging
from typing import Optional, Any
from redis.asyncio import Redis, from_url

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages L2 cache and Presence Lock with graceful in-memory fallback."""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._in_memory_store: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._presence_locks: dict[str, tuple[str, float]] = {}  # lock_key -> (user_id, expire_at)

    async def init(self):
        """Initializes Redis connection if enabled and available."""
        if not settings.USE_IN_MEMORY_REDIS:
            try:
                self._redis = from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2.0
                )
                await self._redis.ping()
                logger.info("Connected to Redis 7.2 L2 Cache.")
            except Exception as e:
                logger.warning(f"Redis unavailable, falling back to In-Memory Cache: {e}")
                self._redis = None

    async def close(self):
        """Closes Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves cached value (JSON deserialized)."""
        if self._redis:
            try:
                val = await self._redis.get(key)
                return json.loads(val) if val else None
            except Exception as e:
                logger.warning(f"Redis get failed for {key}, checking in-memory fallback: {e}")

        # In-memory fallback
        item = self._in_memory_store.get(key)
        if item:
            val, expire_at = item
            if time.time() < expire_at:
                return val
            del self._in_memory_store[key]
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Stores value in cache with TTL."""
        val_str = json.dumps(value, ensure_ascii=False)
        if self._redis:
            try:
                await self._redis.set(key, val_str, ex=ttl_seconds)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed for {key}, using in-memory: {e}")

        self._in_memory_store[key] = (value, time.time() + ttl_seconds)
        return True

    async def delete(self, key: str) -> bool:
        """Invalidates cache key."""
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass
        self._in_memory_store.pop(key, None)
        return True

    # JSON convenience aliases
    get_json = get
    set_json = set

    # --------------------------------------------------------------------------
    # [Tab 3] Presence Lock (동시 편집 사전 차단 락)
    # --------------------------------------------------------------------------
    async def acquire_presence_lock(self, ticket_id: str, user_id: str, ttl_seconds: int = 30) -> bool:
        """Acquires non-blocking presence lock. Returns True if successfully locked."""
        key = f"presence:lock:ticket:{ticket_id}"
        if self._redis:
            try:
                # SETNX with TTL
                res = await self._redis.set(key, user_id, ex=ttl_seconds, nx=True)
                return bool(res)
            except Exception:
                pass

        # In-memory lock fallback
        now = time.time()
        lock = self._presence_locks.get(key)
        if lock:
            current_user, expire_at = lock
            if now < expire_at and current_user != user_id:
                return False  # Locked by someone else
        self._presence_locks[key] = (user_id, now + ttl_seconds)
        return True

    async def get_presence_holder(self, ticket_id: str) -> Optional[str]:
        """Gets current editor user_id if locked."""
        key = f"presence:lock:ticket:{ticket_id}"
        if self._redis:
            try:
                return await self._redis.get(key)
            except Exception:
                pass

        lock = self._presence_locks.get(key)
        if lock:
            user_id, expire_at = lock
            if time.time() < expire_at:
                return user_id
            del self._presence_locks[key]
        return None

    async def release_presence_lock(self, ticket_id: str, user_id: str) -> bool:
        """Releases presence lock if owned by user."""
        key = f"presence:lock:ticket:{ticket_id}"
        holder = await self.get_presence_holder(ticket_id)
        if holder == user_id:
            if self._redis:
                try:
                    await self._redis.delete(key)
                except Exception:
                    pass
            self._presence_locks.pop(key, None)
            return True
        return False

    async def check_health(self) -> bool:
        """Returns True if Redis is alive or in-memory mode is functioning."""
        if self._redis:
            try:
                await self._redis.ping()
                return True
            except Exception:
                return False
        return True  # In-memory is healthy


cache_manager = CacheManager()
