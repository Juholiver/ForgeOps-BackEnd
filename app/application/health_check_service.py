from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.check_schemas import CheckResultResponse
from app.domain.models import CheckResult
from app.infrastructure.health_check_client import HealthCheckClient
from app.infrastructure.monitor_repository import MonitorRepository


class HealthCheckService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.monitor_repo = MonitorRepository(session)
        self.check_client = HealthCheckClient()

    async def execute_check(self, monitor_id: UUID) -> CheckResultResponse:
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

        return CheckResultResponse.model_validate(check_result)

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
            results.append(CheckResultResponse.model_validate(check_result))

        return results
