from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.redis_client import RedisClient


@pytest.fixture
def redis():
    return RedisClient()


@pytest.mark.asyncio
async def test_redis_get_with_data(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.get.return_value = b'{"key": "value"}'

    result = await redis.get("test-key")

    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_redis_get_no_data(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.get.return_value = None

    result = await redis.get("test-key")

    assert result is None


@pytest.mark.asyncio
async def test_redis_set_success(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.set.return_value = True

    result = await redis.set("test-key", {"data": "value"}, ttl=300)

    assert result is True


@pytest.mark.asyncio
async def test_redis_delete_success(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.delete.return_value = 1

    result = await redis.delete("test-key")

    assert result is True


@pytest.mark.asyncio
async def test_redis_acquire_lock_success(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.set.return_value = True

    result = await redis.acquire_lock("test-lock", ttl=60)

    assert result is True


@pytest.mark.asyncio
async def test_redis_acquire_lock_failure(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.set.return_value = None

    result = await redis.acquire_lock("test-lock", ttl=60)

    assert result is False


@pytest.mark.asyncio
async def test_redis_release_lock(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.delete.return_value = 1

    result = await redis.release_lock("test-lock")

    assert result is True


@pytest.mark.asyncio
async def test_redis_rate_limit_allows(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.get.return_value = None

    mock_pipe = AsyncMock()
    mock_pipe.incr = AsyncMock(return_value=1)
    mock_pipe.expire = AsyncMock(return_value=True)
    mock_pipe.execute = AsyncMock(return_value=[1, True])
    redis._client.pipeline = MagicMock(return_value=mock_pipe)

    allowed, count = await redis.check_rate_limit("test-key", 100, 60)

    assert allowed is True
    assert count == 1


@pytest.mark.asyncio
async def test_redis_rate_limit_blocks(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.get.return_value = b"150"

    allowed, count = await redis.check_rate_limit("test-key", 100, 60)

    assert allowed is False
    assert count == 150


@pytest.mark.asyncio
async def test_redis_close(redis):
    redis._client = AsyncMock()
    redis._available = True

    await redis.close()

    redis._client.close.assert_called_once()


@pytest.mark.asyncio
async def test_redis_get_with_invalid_json(redis):
    redis._client = AsyncMock()
    redis._available = True
    redis._client.get.return_value = b"invalid json"

    result = await redis.get("test-key")

    assert result is None
    assert redis._available is False
