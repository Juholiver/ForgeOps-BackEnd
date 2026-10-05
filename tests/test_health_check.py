from unittest.mock import patch

from fastapi.testclient import TestClient

from app.infrastructure.health_check_client import CheckResultData


def create_test_monitor(
    client: TestClient, headers: dict[str, str], name: str = "Test Monitor"
) -> str:
    response = client.post(
        "/monitors",
        json={
            "name": name,
            "url": "https://httpbin.org/status/200",
            "method": "GET",
            "interval_seconds": 60,
            "timeout_seconds": 30,
            "expected_status": 200,
        },
        headers=headers,
    )
    return response.json()["id"]


@patch("app.application.health_check_service.HealthCheckClient.check")
async def test_execute_check_success(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=150.0,
        error_message=None,
    )

    monitor_id = create_test_monitor(client, auth_headers)
    response = client.post(f"/health-check/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["monitor_id"] == monitor_id
    assert data["status"] == "up"
    assert data["http_status"] == 200
    assert data["response_time_ms"] == 150.0


@patch("app.application.health_check_service.HealthCheckClient.check")
async def test_execute_check_unexpected_status(
    mock_check, client: TestClient, auth_headers: dict[str, str]
):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=500,
        response_time_ms=200.0,
        error_message=None,
    )

    monitor_id = create_test_monitor(client, auth_headers)
    response = client.post(f"/health-check/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Expected status 200" in data["error_message"]


@patch("app.application.health_check_service.HealthCheckClient.check")
async def test_execute_check_timeout(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="timeout",
        http_status=None,
        response_time_ms=None,
        error_message="Request timed out after 30s",
    )

    monitor_id = create_test_monitor(client, auth_headers)
    response = client.post(f"/health-check/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "timeout"
    assert "timed out" in data["error_message"]


def test_execute_check_monitor_not_found(client: TestClient, auth_headers: dict[str, str]):
    response = client.post(
        "/health-check/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_execute_all_checks(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )

    create_test_monitor(client, auth_headers, "Monitor 1")
    create_test_monitor(client, auth_headers, "Monitor 2")

    response = client.post("/health-check/run-all", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["status"] == "up" for item in data)
