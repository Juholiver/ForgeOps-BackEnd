from fastapi.testclient import TestClient


def test_update_monitor_not_found(client: TestClient):
    response = client.patch(
        "/monitors/00000000-0000-0000-0000-000000000000",
        json={"name": "Updated"},
    )
    assert response.status_code == 404


def test_toggle_monitor_not_found(client: TestClient):
    response = client.post("/monitors/00000000-0000-0000-0000-000000000000/toggle")
    assert response.status_code == 404


def test_delete_monitor_not_found(client: TestClient):
    response = client.delete("/monitors/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_create_monitor_invalid_method(client: TestClient):
    response = client.post(
        "/monitors",
        json={
            "name": "Test",
            "url": "https://example.com",
            "method": "INVALID",
        },
    )
    assert response.status_code == 422


def test_create_monitor_invalid_timeout(client: TestClient):
    response = client.post(
        "/monitors",
        json={
            "name": "Test",
            "url": "https://example.com",
            "timeout_seconds": 200,
        },
    )
    assert response.status_code == 422


def test_create_monitor_invalid_expected_status(client: TestClient):
    response = client.post(
        "/monitors",
        json={
            "name": "Test",
            "url": "https://example.com",
            "expected_status": 99,
        },
    )
    assert response.status_code == 422


def test_list_monitors_active_only(client: TestClient):
    response = client.get("/monitors?active_only=true")
    assert response.status_code == 200
    data = response.json()
    assert all(m["active"] for m in data["items"])
