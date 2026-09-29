from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit_service import AuditService
from app.domain.models import Monitor
from app.domain.monitor_schemas import (
    MonitorCreate,
    MonitorListResponse,
    MonitorResponse,
    MonitorUpdate,
)
from app.infrastructure.monitor_repository import MonitorRepository


class MonitorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.monitor_repo = MonitorRepository(session)
        self.audit = AuditService(session)

    async def create_monitor(self, data: MonitorCreate) -> MonitorResponse:
        monitor = Monitor(
            name=data.name,
            url=str(data.url),
            method=data.method,
            interval_seconds=data.interval_seconds,
            timeout_seconds=data.timeout_seconds,
            expected_status=data.expected_status,
        )
        await self.monitor_repo.create(monitor)
        await self.audit.log(
            action="monitor.create",
            resource="monitor",
            resource_id=str(monitor.id),
            metadata={"name": monitor.name, "url": monitor.url},
        )
        return MonitorResponse.model_validate(monitor)

    async def list_monitors(
        self, page: int = 1, page_size: int = 20, active_only: bool = False
    ) -> MonitorListResponse:
        monitors, total = await self.monitor_repo.list(page, page_size, active_only)
        return MonitorListResponse(
            items=[MonitorResponse.model_validate(m) for m in monitors],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_monitor(self, monitor_id: UUID) -> MonitorResponse:
        monitor = await self.monitor_repo.get_by_id(monitor_id)
        if not monitor:
            raise ValueError("Monitor not found")
        return MonitorResponse.model_validate(monitor)

    async def update_monitor(self, monitor_id: UUID, data: MonitorUpdate) -> MonitorResponse:
        monitor = await self.monitor_repo.get_by_id(monitor_id)
        if not monitor:
            raise ValueError("Monitor not found")

        update_data = data.model_dump(exclude_unset=True)
        if "url" in update_data:
            update_data["url"] = str(update_data["url"])

        for field, value in update_data.items():
            setattr(monitor, field, value)

        await self.monitor_repo.update(monitor)
        await self.audit.log(
            action="monitor.update",
            resource="monitor",
            resource_id=str(monitor.id),
            metadata={"updated_fields": list(update_data.keys())},
        )
        return MonitorResponse.model_validate(monitor)

    async def toggle_monitor(self, monitor_id: UUID) -> MonitorResponse:
        monitor = await self.monitor_repo.get_by_id(monitor_id)
        if not monitor:
            raise ValueError("Monitor not found")

        monitor.active = not monitor.active
        await self.monitor_repo.update(monitor)
        await self.audit.log(
            action="monitor.toggle",
            resource="monitor",
            resource_id=str(monitor.id),
            metadata={"active": monitor.active},
        )
        return MonitorResponse.model_validate(monitor)

    async def delete_monitor(self, monitor_id: UUID) -> None:
        monitor = await self.monitor_repo.get_by_id(monitor_id)
        if not monitor:
            raise ValueError("Monitor not found")
        await self.monitor_repo.delete(monitor)
        await self.audit.log(
            action="monitor.delete",
            resource="monitor",
            resource_id=str(monitor.id),
            metadata={"name": monitor.name},
        )
