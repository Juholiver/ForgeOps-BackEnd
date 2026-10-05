from unittest.mock import patch

from fastapi.testclient import TestClient

from app.infrastructure.health_check_client import CheckResultData


def create_monitor(client: TestClient, headers: dict[str, str], name: str = "Test Monitor") -> str:
    response = client.post(
        "/monitors",
        json={
            "name": name,
            "url": "https://example.com",
            "method": "GET",
            "interval_seconds": 60,
            "timeout_seconds": 30,
            "expected_status": 200,
        },
        headers=headers,
    )
    return response.json()["id"]


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_dashboard_summary(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )

    create_monitor(client, auth_headers)
    response = client.get("/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_monitors"] >= 1
    assert data["active_monitors"] >= 1
    assert "avg_uptime" in data
    assert "avg_latency_ms" in data


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_dashboard_uptime(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/dashboard/uptime/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["monitor_id"] == monitor_id
    assert data["uptime_percentage"] == 100.0
    assert data["total_checks"] >= 1


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_dashboard_latency(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=150.0,
        error_message=None,
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/dashboard/latency/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["monitor_id"] == monitor_id
    assert data["avg_latency_ms"] == 150.0
    assert data["p95_latency_ms"] == 150.0
    assert data["p99_latency_ms"] == 150.0


def test_dashboard_incident_summary(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/dashboard/incidents", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "open" in data
    assert "investigating" in data
    assert "resolved" in data


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_dashboard_availability(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/dashboard/availability/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["monitor_id"] == monitor_id
    assert data["availability_percentage"] == 100.0


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_dashboard_check_history(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/dashboard/history/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["monitor_id"] == monitor_id
    assert data["total"] >= 1
    assert len(data["checks"]) >= 1
