from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.infrastructure.health_check_client import CheckResultData, HealthCheckClient


@pytest.fixture
def client():
    return HealthCheckClient()


@pytest.mark.asyncio
async def test_check_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.elapsed.total_seconds.return_value = 0.15

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await client.check("https://example.com", "GET", 30)

    assert result.status == "up"
    assert result.http_status == 200
    assert result.response_time_ms == 150.0
    assert result.error_message is None


@pytest.mark.asyncio
async def test_check_timeout(client):
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.TimeoutException("timeout")
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await client.check("https://example.com", "GET", 30)

    assert result.status == "timeout"
    assert result.http_status is None
    assert result.response_time_ms is None
    assert "timed out" in result.error_message


@pytest.mark.asyncio
async def test_check_connection_error(client):
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.ConnectError("refused")
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await client.check("https://example.com", "GET", 30)

    assert result.status == "error"
    assert result.http_status is None
    assert result.response_time_ms is None
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_check_http_status_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=mock_response
        )
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await client.check("https://example.com", "GET", 30)

    assert result.status == "error"
    assert result.http_status == 500


@pytest.mark.asyncio
async def test_check_unexpected_exception(client):
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.request.side_effect = Exception("unexpected")
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await client.check("https://example.com", "GET", 30)

    assert result.status == "error"
    assert "unexpected" in result.error_message


def test_check_result_data_defaults():
    data = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )
    assert data.status == "up"
    assert data.http_status == 200
    assert data.response_time_ms == 100.0
    assert data.error_message is None
