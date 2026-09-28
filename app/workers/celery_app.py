from celery import Celery  # type: ignore[import-untyped]

from app.core.config import settings

celery_app = Celery(
    "forgeops",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="health_checks",
    task_routes={
        "app.workers.tasks.run_health_check": {"queue": "health_checks"},
        "app.workers.tasks.run_all_health_checks": {"queue": "health_checks"},
    },
    beat_schedule={
        "run-all-health-checks": {
            "task": "app.workers.tasks.run_all_health_checks",
            "schedule": 60.0,
        },
    },
)
