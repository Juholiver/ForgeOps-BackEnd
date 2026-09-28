from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Monitor


class MonitorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, monitor_id: UUID) -> Monitor | None:
        result = await self.session.execute(
            select(Monitor).where(Monitor.id == monitor_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self, page: int = 1, page_size: int = 20, active_only: bool = False
    ) -> tuple[list[Monitor], int]:
        query = select(Monitor)
        count_query = select(func.count(Monitor.id))

        if active_only:
            query = query.where(Monitor.active.is_(True))
            count_query = count_query.where(Monitor.active.is_(True))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Monitor.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        monitors = list(result.scalars().all())
        return monitors, total

    async def create(self, monitor: Monitor) -> Monitor:
        self.session.add(monitor)
        await self.session.flush()
        await self.session.refresh(monitor)
        return monitor

    async def update(self, monitor: Monitor) -> Monitor:
        await self.session.flush()
        await self.session.refresh(monitor)
        return monitor

    async def delete(self, monitor: Monitor) -> None:
        await self.session.delete(monitor)
        await self.session.flush()
