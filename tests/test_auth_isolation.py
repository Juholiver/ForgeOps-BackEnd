from unittest.mock import patch

from fastapi.testclient import TestClient

from app.infrastructure.health_check_client import CheckResultData


def create_monitor(client: TestClient, headers: dict[str, str], name: str = "A Monitor") -> str:
    response = client.post(
        "/monitors",
        json={"name": name, "url": "https://example.com"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_data_endpoints_require_auth(client: TestClient):
    monitor_id = "00000000-0000-0000-0000-000000000000"

    assert client.get("/monitors").status_code == 401
    assert client.get(f"/monitors/{monitor_id}").status_code == 401
    assert (
        client.post("/monitors", json={"name": "x", "url": "https://example.com"}).status_code
        == 401
    )
    assert client.get("/dashboard/summary").status_code == 401
    assert client.get(f"/dashboard/uptime/{monitor_id}").status_code == 401
    assert client.get("/dashboard/incidents").status_code == 401
    assert client.get("/incidents").status_code == 401
    assert client.post("/health-check/run-all").status_code == 401
    assert client.post(f"/health-check/{monitor_id}").status_code == 401
    assert client.get("/audit").status_code == 401


def test_monitor_isolation_between_users(
    client: TestClient, auth_headers: dict[str, str], other_headers: dict[str, str]
):
    monitor_id = create_monitor(client, auth_headers)

    own_list = client.get("/monitors", headers=auth_headers)
    assert own_list.status_code == 200
    assert own_list.json()["total"] == 1

    other_list = client.get("/monitors", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json()["total"] == 0
    assert other_list.json()["items"] == []

    assert client.get(f"/monitors/{monitor_id}", headers=auth_headers).status_code == 200
    assert client.get(f"/monitors/{monitor_id}", headers=other_headers).status_code == 404

    patch_resp = client.patch(
        f"/monitors/{monitor_id}", json={"name": "Hacked"}, headers=other_headers
    )
    assert patch_resp.status_code == 404

    toggle_resp = client.post(f"/monitors/{monitor_id}/toggle", headers=other_headers)
    assert toggle_resp.status_code == 404

    delete_resp = client.delete(f"/monitors/{monitor_id}", headers=other_headers)
    assert delete_resp.status_code == 404

    assert client.get(f"/monitors/{monitor_id}", headers=auth_headers).status_code == 200


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_check_and_dashboard_isolation(
    mock_check,
    client: TestClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
):
    mock_check.return_value = CheckResultData(
        status="up",
        http_status=200,
        response_time_ms=100.0,
        error_message=None,
    )
    monitor_id = create_monitor(client, auth_headers)

    forbidden = client.post(f"/health-check/{monitor_id}", headers=other_headers)
    assert forbidden.status_code == 404

    assert client.get(f"/dashboard/uptime/{monitor_id}", headers=other_headers).status_code == 404
    assert client.get(f"/dashboard/latency/{monitor_id}", headers=other_headers).status_code == 404
    assert (
        client.get(f"/dashboard/availability/{monitor_id}", headers=other_headers).status_code
        == 404
    )
    assert client.get(f"/dashboard/history/{monitor_id}", headers=other_headers).status_code == 404

    own_run = client.post("/health-check/run-all", headers=auth_headers)
    assert own_run.status_code == 200
    assert len(own_run.json()) == 1

    other_run = client.post("/health-check/run-all", headers=other_headers)
    assert other_run.status_code == 200
    assert other_run.json() == []

    own_summary = client.get("/dashboard/summary", headers=auth_headers)
    assert own_summary.json()["total_monitors"] == 1

    other_summary = client.get("/dashboard/summary", headers=other_headers)
    assert other_summary.status_code == 200
    assert other_summary.json()["total_monitors"] == 0
    assert other_summary.json()["total_checks"] == 0


@patch("app.application.health_check_service.HealthCheckClient.check")
def test_incident_isolation_between_users(
    mock_check,
    client: TestClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
):
    mock_check.return_value = CheckResultData(
        status="down",
        http_status=None,
        response_time_ms=None,
        error_message="Connection refused",
    )
    monitor_id = create_monitor(client, auth_headers)
    client.post(f"/health-check/{monitor_id}", headers=auth_headers)

    own_incidents = client.get("/incidents", headers=auth_headers)
    assert own_incidents.json()["total"] == 1
    incident_id = own_incidents.json()["items"][0]["id"]

    other_incidents = client.get("/incidents", headers=other_headers)
    assert other_incidents.status_code == 200
    assert other_incidents.json()["total"] == 0

    filtered = client.get(f"/incidents?monitor_id={monitor_id}", headers=other_headers)
    assert filtered.json()["total"] == 0

    assert client.get(f"/incidents/{incident_id}", headers=other_headers).status_code == 404
    assert (
        client.patch(
            f"/incidents/{incident_id}",
            json={"status": "investigating"},
            headers=other_headers,
        ).status_code
        == 404
    )

    assert client.get(f"/incidents/{incident_id}", headers=auth_headers).status_code == 200

    other_summary = client.get("/dashboard/incidents", headers=other_headers)
    assert other_summary.json()["total"] == 0

    own_summary = client.get("/dashboard/incidents", headers=auth_headers)
    assert own_summary.json()["total"] == 1


def test_audit_isolation_between_users(
    client: TestClient, auth_headers: dict[str, str], other_headers: dict[str, str]
):
    create_monitor(client, auth_headers)

    own_audit = client.get("/audit?action=monitor.create", headers=auth_headers)
    assert own_audit.status_code == 200
    assert own_audit.json()["total"] == 1

    other_audit = client.get("/audit?action=monitor.create", headers=other_headers)
    assert other_audit.status_code == 200
    assert other_audit.json()["total"] == 0
