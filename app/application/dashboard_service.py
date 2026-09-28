from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.dashboard_schemas import (
    AvailabilityResponse,
    CheckHistoryResponse,
    DashboardSummaryResponse,
    IncidentSummaryResponse,
    LatencyResponse,
    UptimeResponse,
)
from app.infrastructure.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dashboard_repo = DashboardRepository(session)

    async def get_uptime(
        self, monitor_id: UUID, days: int = 7
    ) -> UptimeResponse:
        since = datetime.now(UTC) - timedelta(days=days)
        total, success = await self.dashboard_repo.get_uptime(monitor_id, since)
        uptime_pct = (success / total * 100) if total > 0 else 100.0
        return UptimeResponse(
            monitor_id=monitor_id,
            uptime_percentage=round(uptime_pct, 2),
            total_checks=total,
            successful_checks=success,
            period_start=since,
            period_end=datetime.now(UTC),
        )

    async def get_latency(
        self, monitor_id: UUID, days: int = 7
    ) -> LatencyResponse:
        since = datetime.now(UTC) - timedelta(days=days)
        avg, p95, p99, min_lat, max_lat, total = (
            await self.dashboard_repo.get_latency_stats(monitor_id, since)
        )
        return LatencyResponse(
            monitor_id=monitor_id,
            avg_latency_ms=round(avg, 2),
            p95_latency_ms=round(p95, 2),
            p99_latency_ms=round(p99, 2),
            min_latency_ms=round(min_lat, 2),
            max_latency_ms=round(max_lat, 2),
            total_checks=total,
        )

    async def get_incident_summary(self) -> IncidentSummaryResponse:
        total, open_count, investigating, resolved = (
            await self.dashboard_repo.get_incident_summary()
        )
        return IncidentSummaryResponse(
            total=total,
            open=open_count,
            investigating=investigating,
            resolved=resolved,
        )

    async def get_availability(
        self, monitor_id: UUID, days: int = 7
    ) -> AvailabilityResponse:
        since = datetime.now(UTC) - timedelta(days=days)
        total, failed = await self.dashboard_repo.get_availability(
            monitor_id, since
        )
        availability_pct = (
            ((total - failed) / total * 100) if total > 0 else 100.0
        )
        return AvailabilityResponse(
            monitor_id=monitor_id,
            availability_percentage=round(availability_pct, 2),
            total_checks=total,
            failed_checks=failed,
            period_start=since,
            period_end=datetime.now(UTC),
        )

    async def get_check_history(
        self,
        monitor_id: UUID,
        page: int = 1,
        page_size: int = 50,
        days: int = 7,
    ) -> CheckHistoryResponse:
        since = datetime.now(UTC) - timedelta(days=days)
        checks, total = await self.dashboard_repo.get_check_history(
            monitor_id, page, page_size, since
        )
        return CheckHistoryResponse(
            monitor_id=monitor_id,
            checks=[
                {
                    "id": str(c.id),
                    "status": c.status,
                    "http_status": c.http_status,
                    "response_time_ms": c.response_time_ms,
                    "error_message": c.error_message,
                    "checked_at": c.checked_at.isoformat(),
                }
                for c in checks
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_dashboard_summary(self) -> DashboardSummaryResponse:
        since = datetime.now(UTC) - timedelta(days=7)
        (
            total_monitors,
            active_monitors,
            total_checks,
            total_incidents,
            open_incidents,
            avg_uptime,
            avg_latency,
        ) = await self.dashboard_repo.get_dashboard_summary(since)
        return DashboardSummaryResponse(
            total_monitors=total_monitors,
            active_monitors=active_monitors,
            total_checks=total_checks,
            total_incidents=total_incidents,
            open_incidents=open_incidents,
            avg_uptime=round(avg_uptime, 2),
            avg_latency_ms=round(avg_latency, 2),
        )
