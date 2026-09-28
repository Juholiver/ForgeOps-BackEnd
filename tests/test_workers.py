from unittest.mock import MagicMock, patch

from app.workers.celery_app import celery_app
from app.workers.tasks import run_all_health_checks, run_health_check


def test_celery_app_configuration():
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.task_track_started is True
    assert celery_app.conf.task_time_limit == 300
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True


def test_celery_task_routes():
    routes = celery_app.conf.task_routes
    assert "app.workers.tasks.run_health_check" in routes
    assert "app.workers.tasks.run_all_health_checks" in routes


def test_celery_beat_schedule():
    schedule = celery_app.conf.beat_schedule
    assert "run-all-health-checks" in schedule
    assert schedule["run-all-health-checks"]["schedule"] == 60.0


@patch("app.workers.tasks._run_health_check_async")
def test_run_health_check_task(mock_async):
    mock_task = MagicMock()
    mock_task.session_maker = MagicMock()
    mock_async.return_value = {"status": "up"}

    result = run_health_check.run(monitor_id="test-id")
    assert result == {"status": "up"}


@patch("app.workers.tasks._run_all_health_checks_async")
def test_run_all_health_checks_task(mock_async):
    mock_task = MagicMock()
    mock_task.session_maker = MagicMock()
    mock_async.return_value = {"scheduled": 2}

    result = run_all_health_checks.run()
    assert result == {"scheduled": 2}


def test_run_health_check_max_retries():
    assert run_health_check.max_retries == 3
    assert run_health_check.default_retry_delay == 60
