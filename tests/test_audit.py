from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"name": "Test User", "email": email, "password": "password123"},
    )
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_audit_log_on_register(client: TestClient):
    headers = register_and_login(client, "audit-test@example.com")

    response = client.get("/audit?action=user.register", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "user.register"
    assert data["items"][0]["resource"] == "user"


def test_audit_log_on_login(client: TestClient):
    headers = register_and_login(client, "audit-login@example.com")

    response = client.get("/audit?action=user.login", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "user.login"


def test_audit_log_on_monitor_create(client: TestClient, auth_headers: dict[str, str]):
    client.post(
        "/monitors",
        json={"name": "Audit Test", "url": "https://example.com"},
        headers=auth_headers,
    )

    response = client.get("/audit?action=monitor.create", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "monitor.create"
    assert data["items"][0]["resource"] == "monitor"


def test_audit_log_on_monitor_toggle(client: TestClient, auth_headers: dict[str, str]):
    create_resp = client.post(
        "/monitors",
        json={"name": "Toggle Test", "url": "https://example.com"},
        headers=auth_headers,
    )
    monitor_id = create_resp.json()["id"]

    client.post(f"/monitors/{monitor_id}/toggle", headers=auth_headers)

    response = client.get("/audit?action=monitor.toggle", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "monitor.toggle"


def test_audit_log_on_monitor_delete(client: TestClient, auth_headers: dict[str, str]):
    create_resp = client.post(
        "/monitors",
        json={"name": "Delete Test", "url": "https://example.com"},
        headers=auth_headers,
    )
    monitor_id = create_resp.json()["id"]

    client.delete(f"/monitors/{monitor_id}", headers=auth_headers)

    response = client.get("/audit?action=monitor.delete", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "monitor.delete"


def test_audit_log_empty(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/audit?action=nonexistent", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_audit_log_pagination(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/audit?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
