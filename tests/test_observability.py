from fastapi.testclient import TestClient

from app.infrastructure.metrics import (
    celery_task_duration_seconds,
    celery_tasks_total,
    http_request_duration_seconds,
    http_requests_total,
)


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "forgeops"


def test_ready_endpoint(client: TestClient):
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_metrics_endpoint(client: TestClient):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "forgeops_http_requests_total" in response.text


def test_http_requests_metric_exists():
    metric = http_requests_total.labels(
        method="GET", endpoint="/health", status="200"
    )
    assert metric is not None


def test_http_request_duration_metric_exists():
    metric = http_request_duration_seconds.labels(
        method="GET", endpoint="/health"
    )
    assert metric is not None


def test_celery_tasks_metric_exists():
    metric = celery_tasks_total.labels(
        task_name="run_health_check", status="up"
    )
    assert metric is not None


def test_celery_task_duration_metric_exists():
    metric = celery_task_duration_seconds.labels(task_name="run_health_check")
    assert metric is not None


def test_request_id_header(client: TestClient):
    response = client.get("/health")
    assert "X-Request-ID" in response.headers


def test_structured_logging(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
