from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.incident_service import IncidentService
from app.domain.check_schemas import CheckResultResponse
from app.domain.models import CheckResult
from app.infrastructure.cache import DistributedLock, HealthCheckCache
from app.infrastructure.health_check_client import HealthCheckClient
from app.infrastructure.monitor_repository import MonitorRepository

logger = structlog.get_logger()


class HealthCheckService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.monitor_repo = MonitorRepository(session)
        self.check_client = HealthCheckClient()
        self.cache = HealthCheckCache(ttl=60)
        self.lock = DistributedLock(lock_timeout=60)
        self.incident_service = IncidentService(session)

    async def execute_check(self, monitor_id: UUID) -> CheckResultResponse:
        cached = await self.cache.get(str(monitor_id))
        if cached:
            return CheckResultResponse(**cached)

        if not await self.lock.acquire(f"health_check:{monitor_id}"):
            logger.warning("check_already_running", monitor_id=str(monitor_id))
            raise ValueError("Check already in progress for this monitor")

        try:
            monitor = await self.monitor_repo.get_by_id(monitor_id)
            if not monitor:
                raise ValueError("Monitor not found")

            result_data = await self.check_client.check(
                url=monitor.url,
                method=monitor.method,
                timeout_seconds=monitor.timeout_seconds,
            )

            status = result_data.status
            if status == "up" and result_data.http_status != monitor.expected_status:
                status = "error"
                result_data.error_message = (
                    f"Expected status {monitor.expected_status}, "
                    f"got {result_data.http_status}"
                )

            check_result = CheckResult(
                monitor_id=monitor.id,
                status=status,
                http_status=result_data.http_status,
                response_time_ms=result_data.response_time_ms,
                error_message=result_data.error_message,
            )
            self.session.add(check_result)
            await self.session.flush()
            await self.session.refresh(check_result)

            response = CheckResultResponse.model_validate(check_result)
            await self.cache.set(str(monitor_id), response.model_dump(mode="json"))

            await self.incident_service.process_check_result(monitor.id, response)

            return response
        finally:
            await self.lock.release(f"health_check:{monitor_id}")

    async def execute_all_active(self) -> list[CheckResultResponse]:
        monitors, _ = await self.monitor_repo.list(active_only=True)
        results = []
        for monitor in monitors:
            result_data = await self.check_client.check(
                url=monitor.url,
                method=monitor.method,
                timeout_seconds=monitor.timeout_seconds,
            )

            status = result_data.status
            if status == "up" and result_data.http_status != monitor.expected_status:
                status = "error"
                result_data.error_message = (
                    f"Expected status {monitor.expected_status}, "
                    f"got {result_data.http_status}"
                )

            check_result = CheckResult(
                monitor_id=monitor.id,
                status=status,
                http_status=result_data.http_status,
                response_time_ms=result_data.response_time_ms,
                error_message=result_data.error_message,
            )
            self.session.add(check_result)
            await self.session.flush()
            await self.session.refresh(check_result)
            response = CheckResultResponse.model_validate(check_result)
            results.append(response)

            await self.incident_service.process_check_result(monitor.id, response)

        return results
