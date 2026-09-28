from typing import Any

from app.infrastructure.redis_client import redis_client


class HealthCheckCache:
    def __init__(self, ttl: int = 60):
        self.ttl = ttl

    def _key(self, monitor_id: str) -> str:
        return f"health_check:{monitor_id}"

    async def get(self, monitor_id: str) -> dict[str, Any] | None:
        return await redis_client.get(self._key(monitor_id))

    async def set(self, monitor_id: str, data: dict[str, Any]) -> bool:
        return await redis_client.set(self._key(monitor_id), data, self.ttl)

    async def invalidate(self, monitor_id: str) -> bool:
        return await redis_client.delete(self._key(monitor_id))


class DistributedLock:
    def __init__(self, lock_timeout: int = 60):
        self.lock_timeout = lock_timeout

    def _key(self, resource: str) -> str:
        return f"lock:{resource}"

    async def acquire(self, resource: str) -> bool:
        return await redis_client.acquire_lock(
            self._key(resource), self.lock_timeout
        )

    async def release(self, resource: str) -> bool:
        return await redis_client.release_lock(self._key(resource))
