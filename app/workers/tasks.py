import structlog
from celery import Task  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.domain.models import CheckResult, Monitor
from app.infrastructure.health_check_client import HealthCheckClient
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


class DatabaseTask(Task):  # type: ignore[misc]
    _session_maker: async_sessionmaker[AsyncSession] | None = None

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._session_maker is None:
            engine = create_async_engine(settings.database_url)
            self._session_maker = async_sessionmaker(engine, class_=AsyncSession)
        return self._session_maker


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3, default_retry_delay=60)  # type: ignore[untyped-decorator]
def run_health_check(self: Task, monitor_id: str) -> dict[str, object]:
    import asyncio

    return asyncio.run(_run_health_check_async(self, monitor_id))


async def _run_health_check_async(task: Task, monitor_id: str) -> dict[str, object]:
    session_maker = task.session_maker
    async with session_maker() as session:
        result = await session.execute(
            select(Monitor).where(Monitor.id == monitor_id)
        )
        monitor = result.scalar_one_or_none()

        if not monitor:
            logger.warning("monitor_not_found", monitor_id=monitor_id)
            return {"status": "error", "error": "Monitor not found"}

        client = HealthCheckClient()
        check_result = await client.check(
            url=monitor.url,
            method=monitor.method,
            timeout_seconds=monitor.timeout_seconds,
        )

        status = check_result.status
        if status == "up" and check_result.http_status != monitor.expected_status:
            status = "error"
            check_result.error_message = (
                f"Expected status {monitor.expected_status}, "
                f"got {check_result.http_status}"
            )

        db_result = CheckResult(
            monitor_id=monitor.id,
            status=status,
            http_status=check_result.http_status,
            response_time_ms=check_result.response_time_ms,
            error_message=check_result.error_message,
        )
        session.add(db_result)
        await session.commit()

        logger.info(
            "health_check_completed",
            monitor_id=str(monitor.id),
            status=status,
            http_status=check_result.http_status,
            response_time_ms=check_result.response_time_ms,
        )

        return {
            "monitor_id": str(monitor.id),
            "status": status,
            "http_status": check_result.http_status,
            "response_time_ms": check_result.response_time_ms,
        }


@celery_app.task(bind=True, base=DatabaseTask)  # type: ignore[untyped-decorator]
def run_all_health_checks(self: Task) -> dict[str, object]:
    import asyncio

    return asyncio.run(_run_all_health_checks_async(self))


async def _run_all_health_checks_async(task: Task) -> dict[str, object]:
    session_maker = task.session_maker
    async with session_maker() as session:
        result = await session.execute(
            select(Monitor).where(Monitor.active.is_(True))
        )
        monitors = list(result.scalars().all())

        logger.info("running_all_health_checks", count=len(monitors))

        results = []
        for monitor in monitors:
            try:
                task_result = run_health_check.delay(str(monitor.id))
                results.append({"monitor_id": str(monitor.id), "task_id": task_result.id})
            except Exception as e:
                logger.error(
                    "failed_to_schedule_check",
                    monitor_id=str(monitor.id),
                    error=str(e),
                )

        return {"scheduled": len(results), "results": results}
