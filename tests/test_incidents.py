from unittest.mock import patch

from fastapi.testclient import TestClient

from app.domain.models import IncidentStatus
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
def test_incident_created_on_failure(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="down",
        http_status=None,
        response_time_ms=None,
        error_message="Connection refused",
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/incidents?monitor_id={monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == IncidentStatus.OPEN
    assert "Connection refused" in data["items"][0]["reason"]


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_no_duplicate_incidents(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="down",
        http_status=None,
        response_time_ms=None,
        error_message="Connection refused",
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/incidents?monitor_id={monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_incident_resolved_on_recovery(
    mock_check, client: TestClient, auth_headers: dict[str, str]
):
    monitor_id = create_monitor(client, auth_headers)

    mock_check.return_value = CheckResultData(
        status="down",
        http_status=None,
        response_time_ms=None,
        error_message="Connection refused",
    )
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/incidents?monitor_id={monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == IncidentStatus.RESOLVED
    assert data["items"][0]["resolved_at"] is not None


def test_list_incidents_empty(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/incidents", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_incidents_pagination(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/incidents?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_get_incident_not_found(client: TestClient, auth_headers: dict[str, str]):
    response = client.get(
        "/incidents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_update_incident_status(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="down",
        http_status=None,
        response_time_ms=None,
        error_message="Connection refused",
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    incidents_resp = client.get(f"/incidents?monitor_id={monitor_id}", headers=auth_headers)
    incident_id = incidents_resp.json()["items"][0]["id"]

    response = client.patch(
        f"/incidents/{incident_id}",
        json={"status": "investigating"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == IncidentStatus.INVESTIGATING


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_filter_incidents_by_status(mock_check, client: TestClient, auth_headers: dict[str, str]):
    mock_check.return_value = CheckResultData(
        status="down",
        http_status=None,
        response_time_ms=None,
        error_message="Connection refused",
    )

    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    response = client.get(f"/incidents?status={IncidentStatus.OPEN}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == IncidentStatus.OPEN
