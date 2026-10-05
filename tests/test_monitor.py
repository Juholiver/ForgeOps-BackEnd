from fastapi.testclient import TestClient


def test_create_monitor(client: TestClient, auth_headers: dict[str, str]):
    response = client.post(
        "/monitors",
        json={
            "name": "Google",
            "url": "https://www.google.com",
            "method": "GET",
            "interval_seconds": 60,
            "timeout_seconds": 30,
            "expected_status": 200,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Google"
    assert data["url"] == "https://www.google.com/"
    assert data["method"] == "GET"
    assert data["active"] is True
    assert "id" in data


def test_create_monitor_invalid_url(client: TestClient, auth_headers: dict[str, str]):
    response = client.post(
        "/monitors",
        json={
            "name": "Invalid",
            "url": "not-a-url",
            "interval_seconds": 60,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_monitor_invalid_interval(client: TestClient, auth_headers: dict[str, str]):
    response = client.post(
        "/monitors",
        json={
            "name": "Invalid",
            "url": "https://example.com",
            "interval_seconds": 5,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_monitors(client: TestClient, auth_headers: dict[str, str]):
    client.post(
        "/monitors",
        json={"name": "Test", "url": "https://example.com"},
        headers=auth_headers,
    )
    response = client.get("/monitors", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_list_monitors_pagination(client: TestClient, auth_headers: dict[str, str]):
    for i in range(3):
        client.post(
            "/monitors",
            json={"name": f"Test {i}", "url": f"https://example{i}.com"},
            headers=auth_headers,
        )
    response = client.get("/monitors?page=1&page_size=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_get_monitor(client: TestClient, auth_headers: dict[str, str]):
    create_response = client.post(
        "/monitors",
        json={"name": "Test", "url": "https://example.com"},
        headers=auth_headers,
    )
    monitor_id = create_response.json()["id"]

    response = client.get(f"/monitors/{monitor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == monitor_id
    assert data["name"] == "Test"


def test_get_monitor_not_found(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/monitors/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


def test_update_monitor(client: TestClient, auth_headers: dict[str, str]):
    create_response = client.post(
        "/monitors",
        json={"name": "Test", "url": "https://example.com"},
        headers=auth_headers,
    )
    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/monitors/{monitor_id}",
        json={"name": "Updated", "interval_seconds": 120},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["interval_seconds"] == 120


def test_toggle_monitor(client: TestClient, auth_headers: dict[str, str]):
    create_response = client.post(
        "/monitors",
        json={"name": "Test", "url": "https://example.com"},
        headers=auth_headers,
    )
    monitor_id = create_response.json()["id"]
    assert create_response.json()["active"] is True

    response = client.post(f"/monitors/{monitor_id}/toggle", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["active"] is False

    response = client.post(f"/monitors/{monitor_id}/toggle", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["active"] is True


def test_delete_monitor(client: TestClient, auth_headers: dict[str, str]):
    create_response = client.post(
        "/monitors",
        json={"name": "Test", "url": "https://example.com"},
        headers=auth_headers,
    )
    monitor_id = create_response.json()["id"]

    response = client.delete(f"/monitors/{monitor_id}", headers=auth_headers)
    assert response.status_code == 204

    response = client.get(f"/monitors/{monitor_id}", headers=auth_headers)
    assert response.status_code == 404
