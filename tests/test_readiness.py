from fastapi.testclient import TestClient


def test_readiness_db_failure(client: TestClient):
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]


def test_readiness_response_structure(client: TestClient):
    response = client.get("/ready")
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]
    assert isinstance(data["checks"], dict)
