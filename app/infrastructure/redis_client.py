import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


class RedisClient:
    def __init__(self) -> None:
        self._client: redis.Redis[Any] | None = None
        self._available = False

    async def connect(self) -> bool:
        try:
            self._client = redis.from_url(
                settings.redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=False,
            )
            await self._client.ping()
            self._available = True
            return True
        except Exception:
            self._available = False
            return False

    @property
    def is_available(self) -> bool:
        return self._available and self._client is not None

    async def get(self, key: str) -> Any | None:
        if not self.is_available or self._client is None:
            return None
        try:
            data = await self._client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            self._available = False
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self.is_available or self._client is None:
            return False
        try:
            await self._client.set(key, json.dumps(value), ex=ttl)
            return True
        except Exception:
            self._available = False
            return False

    async def delete(self, key: str) -> bool:
        if not self.is_available or self._client is None:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception:
            self._available = False
            return False

    async def acquire_lock(self, lock_key: str, ttl: int = 60) -> bool:
        if not self.is_available or self._client is None:
            return True
        try:
            acquired = await self._client.set(lock_key, "1", nx=True, ex=ttl)
            return acquired is not None
        except Exception:
            self._available = False
            return True

    async def release_lock(self, lock_key: str) -> bool:
        if not self.is_available or self._client is None:
            return True
        try:
            await self._client.delete(lock_key)
            return True
        except Exception:
            self._available = False
            return True

    async def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> tuple[bool, int]:
        if not self.is_available or self._client is None:
            return True, 0
        try:
            current = await self._client.get(key)
            current_count = int(current) if current else 0

            if current_count >= max_requests:
                return False, current_count

            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            await pipe.execute()
            return True, current_count + 1
        except Exception:
            self._available = False
            return True, 0

    async def close(self) -> None:
        if self._client:
            await self._client.close()


redis_client = RedisClient()
