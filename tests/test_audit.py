from fastapi.testclient import TestClient


def test_audit_log_on_register(client: TestClient):
    client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "audit-test@example.com",
            "password": "password123",
        },
    )

    response = client.get("/audit?action=user.register")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "user.register"
    assert data["items"][0]["resource"] == "user"


def test_audit_log_on_login(client: TestClient):
    client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "audit-login@example.com",
            "password": "password123",
        },
    )

    client.post(
        "/auth/login",
        json={"email": "audit-login@example.com", "password": "password123"},
    )

    response = client.get("/audit?action=user.login")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "user.login"


def test_audit_log_on_monitor_create(client: TestClient):
    client.post(
        "/monitors",
        json={"name": "Audit Test", "url": "https://example.com"},
    )

    response = client.get("/audit?action=monitor.create")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "monitor.create"
    assert data["items"][0]["resource"] == "monitor"


def test_audit_log_on_monitor_toggle(client: TestClient):
    create_resp = client.post(
        "/monitors",
        json={"name": "Toggle Test", "url": "https://example.com"},
    )
    monitor_id = create_resp.json()["id"]

    client.post(f"/monitors/{monitor_id}/toggle")

    response = client.get("/audit?action=monitor.toggle")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "monitor.toggle"


def test_audit_log_on_monitor_delete(client: TestClient):
    create_resp = client.post(
        "/monitors",
        json={"name": "Delete Test", "url": "https://example.com"},
    )
    monitor_id = create_resp.json()["id"]

    client.delete(f"/monitors/{monitor_id}")

    response = client.get("/audit?action=monitor.delete")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "monitor.delete"


def test_audit_log_empty(client: TestClient):
    response = client.get("/audit?action=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_audit_log_pagination(client: TestClient):
    response = client.get("/audit?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
