from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import CheckResult, Incident, IncidentStatus, Monitor


class DashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_uptime(
        self, monitor_id: UUID, since: datetime
    ) -> tuple[int, int]:
        result = await self.session.execute(
            select(
                func.count(CheckResult.id),
                func.sum(
                    case((CheckResult.status == "up", 1), else_=0)
                ),
            ).where(
                CheckResult.monitor_id == monitor_id,
                CheckResult.checked_at >= since,
            )
        )
        row = result.one()
        total = row[0] or 0
        success = row[1] or 0
        return total, success

    async def get_latency_stats(
        self, monitor_id: UUID, since: datetime
    ) -> tuple[float, float, float, float, float, int]:
        result = await self.session.execute(
            select(
                func.avg(CheckResult.response_time_ms),
                func.min(CheckResult.response_time_ms),
                func.max(CheckResult.response_time_ms),
                func.count(CheckResult.id),
            ).where(
                CheckResult.monitor_id == monitor_id,
                CheckResult.checked_at >= since,
                CheckResult.response_time_ms.is_not(None),
            )
        )
        row = result.one()

        times_result = await self.session.execute(
            select(CheckResult.response_time_ms).where(
                CheckResult.monitor_id == monitor_id,
                CheckResult.checked_at >= since,
                CheckResult.response_time_ms.is_not(None),
            )
        )
        times = sorted([r[0] for r in times_result.all() if r[0] is not None])

        p95 = self._percentile(times, 95)
        p99 = self._percentile(times, 99)

        return (
            row[0] or 0.0,
            p95,
            p99,
            row[1] or 0.0,
            row[2] or 0.0,
            row[3] or 0,
        )

    @staticmethod
    def _percentile(sorted_values: list[float], percentile: float) -> float:
        if not sorted_values:
            return 0.0
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    async def get_incident_summary(self) -> tuple[int, int, int, int]:
        result = await self.session.execute(
            select(
                func.count(Incident.id),
                func.sum(
                    case((Incident.status == IncidentStatus.OPEN, 1), else_=0)
                ),
                func.sum(
                    case(
                        (
                            Incident.status == IncidentStatus.INVESTIGATING,
                            1,
                        ),
                        else_=0,
                    )
                ),
                func.sum(
                    case(
                        (
                            Incident.status == IncidentStatus.RESOLVED,
                            1,
                        ),
                        else_=0,
                    )
                ),
            )
        )
        row = result.one()
        return (
            row[0] or 0,
            row[1] or 0,
            row[2] or 0,
            row[3] or 0,
        )

    async def get_availability(
        self, monitor_id: UUID, since: datetime
    ) -> tuple[int, int]:
        result = await self.session.execute(
            select(
                func.count(CheckResult.id),
                func.sum(
                    case((CheckResult.status != "up", 1), else_=0)
                ),
            ).where(
                CheckResult.monitor_id == monitor_id,
                CheckResult.checked_at >= since,
            )
        )
        row = result.one()
        total = row[0] or 0
        failed = row[1] or 0
        return total, failed

    async def get_check_history(
        self,
        monitor_id: UUID,
        page: int = 1,
        page_size: int = 50,
        since: datetime | None = None,
    ) -> tuple[list[CheckResult], int]:
        query = select(CheckResult).where(CheckResult.monitor_id == monitor_id)
        count_query = select(func.count(CheckResult.id)).where(
            CheckResult.monitor_id == monitor_id
        )

        if since:
            query = query.where(CheckResult.checked_at >= since)
            count_query = count_query.where(CheckResult.checked_at >= since)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(CheckResult.checked_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        checks = list(result.scalars().all())
        return checks, total

    async def get_dashboard_summary(
        self, since: datetime
    ) -> tuple[int, int, int, int, int, float, float]:
        monitors_total = (
            await self.session.execute(select(func.count(Monitor.id)))
        ).scalar() or 0
        monitors_active = (
            await self.session.execute(
                select(func.count(Monitor.id)).where(Monitor.active.is_(True))
            )
        ).scalar() or 0
        checks_total = (
            await self.session.execute(
                select(func.count(CheckResult.id)).where(
                    CheckResult.checked_at >= since
                )
            )
        ).scalar() or 0
        incidents_total = (
            await self.session.execute(select(func.count(Incident.id)))
        ).scalar() or 0
        incidents_open = (
            await self.session.execute(
                select(func.count(Incident.id)).where(
                    Incident.status == IncidentStatus.OPEN
                )
            )
        ).scalar() or 0
        avg_uptime_row = (
            await self.session.execute(
                select(
                    func.avg(
                        case((CheckResult.status == "up", 1.0), else_=0.0)
                    )
                ).where(CheckResult.checked_at >= since)
            )
        ).scalar()
        avg_uptime = (avg_uptime_row or 0.0) * 100
        avg_latency_row = (
            await self.session.execute(
                select(func.avg(CheckResult.response_time_ms)).where(
                    CheckResult.checked_at >= since,
                    CheckResult.response_time_ms.is_not(None),
                )
            )
        ).scalar()
        avg_latency = avg_latency_row or 0.0

        return (
            monitors_total,
            monitors_active,
            checks_total,
            incidents_total,
            incidents_open,
            avg_uptime,
            avg_latency,
        )
