from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Incident, IncidentStatus


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, incident_id: UUID) -> Incident | None:
        result = await self.session.execute(select(Incident).where(Incident.id == incident_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: IncidentStatus | None = None,
        monitor_id: UUID | None = None,
    ) -> tuple[list[Incident], int]:
        query = select(Incident)
        count_query = select(func.count(Incident.id))

        if status:
            query = query.where(Incident.status == status)
            count_query = count_query.where(Incident.status == status)
        if monitor_id:
            query = query.where(Incident.monitor_id == monitor_id)
            count_query = count_query.where(Incident.monitor_id == monitor_id)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Incident.started_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        incidents = list(result.scalars().all())
        return incidents, total

    async def get_open_by_monitor(self, monitor_id: UUID) -> Incident | None:
        result = await self.session.execute(
            select(Incident)
            .where(Incident.monitor_id == monitor_id)
            .where(Incident.status != IncidentStatus.RESOLVED)
            .order_by(Incident.started_at.desc())
        )
        return result.scalar_one_or_none()

    async def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.flush()
        await self.session.refresh(incident)
        return incident

    async def update(self, incident: Incident) -> Incident:
        await self.session.flush()
        await self.session.refresh(incident)
        return incident
