from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    "forgeops_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "forgeops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

celery_tasks_total = Counter(
    "forgeops_celery_tasks_total",
    "Total Celery tasks executed",
    ["task_name", "status"],
)

celery_task_duration_seconds = Histogram(
    "forgeops_celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

active_monitors = Gauge(
    "forgeops_active_monitors",
    "Number of active monitors",
)

open_incidents = Gauge(
    "forgeops_open_incidents",
    "Number of open incidents",
)

db_connection_pool = Gauge(
    "forgeops_db_connection_pool",
    "Database connection pool size",
    ["state"],
)
