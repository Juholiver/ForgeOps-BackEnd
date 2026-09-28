import pytest

from app.infrastructure.cache import DistributedLock, HealthCheckCache
from app.infrastructure.redis_client import RedisClient, redis_client


@pytest.fixture
def redis():
    return RedisClient()


@pytest.fixture
def cache():
    return HealthCheckCache(ttl=60)


@pytest.fixture
def lock():
    return DistributedLock(lock_timeout=60)


@pytest.mark.asyncio
async def test_redis_client_initial_state(redis):
    assert redis.is_available is False


@pytest.mark.asyncio
async def test_redis_client_connect_failure(redis):
    result = await redis.connect()
    assert result is False
    assert redis.is_available is False


@pytest.mark.asyncio
async def test_redis_get_returns_none_when_unavailable(redis):
    result = await redis.get("test-key")
    assert result is None


@pytest.mark.asyncio
async def test_redis_set_returns_false_when_unavailable(redis):
    result = await redis.set("test-key", {"data": "value"})
    assert result is False


@pytest.mark.asyncio
async def test_redis_delete_returns_false_when_unavailable(redis):
    result = await redis.delete("test-key")
    assert result is False


@pytest.mark.asyncio
async def test_redis_lock_acquire_succeeds_when_unavailable(redis):
    result = await redis.acquire_lock("test-lock")
    assert result is True


@pytest.mark.asyncio
async def test_redis_lock_release_succeeds_when_unavailable(redis):
    result = await redis.release_lock("test-lock")
    assert result is True


@pytest.mark.asyncio
async def test_redis_rate_limit_allows_when_unavailable(redis):
    allowed, count = await redis.check_rate_limit("test-key", 100, 60)
    assert allowed is True
    assert count == 0


@pytest.mark.asyncio
async def test_cache_get_returns_none_when_unavailable(cache):
    result = await cache.get("monitor-123")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_returns_false_when_unavailable(cache):
    result = await cache.set("monitor-123", {"status": "up"})
    assert result is False


@pytest.mark.asyncio
async def test_lock_acquire_succeeds_when_unavailable(lock):
    result = await lock.acquire("resource-123")
    assert result is True


@pytest.mark.asyncio
async def test_lock_release_succeeds_when_unavailable(lock):
    result = await lock.release("resource-123")
    assert result is True


def test_redis_client_singleton():
    assert redis_client is not None
