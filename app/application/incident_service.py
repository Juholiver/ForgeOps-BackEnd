from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit_service import AuditService
from app.domain.check_schemas import CheckResultResponse
from app.domain.incident_schemas import (
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
)
from app.domain.models import Incident, IncidentStatus
from app.infrastructure.incident_repository import IncidentRepository

logger = structlog.get_logger()


class IncidentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.incident_repo = IncidentRepository(session)
        self.audit = AuditService(session)

    async def process_check_result(
        self, monitor_id: UUID, check: CheckResultResponse
    ) -> Incident | None:
        is_healthy = check.status == "up"
        open_incident = await self.incident_repo.get_open_by_monitor(monitor_id)

        if is_healthy and open_incident:
            return await self._resolve_incident(open_incident)

        if not is_healthy and not open_incident:
            return await self._create_incident(monitor_id, check)

        return None

    async def _create_incident(self, monitor_id: UUID, check: CheckResultResponse) -> Incident:
        reason = check.error_message or f"HTTP status {check.http_status}"
        incident = Incident(
            monitor_id=monitor_id,
            status=IncidentStatus.OPEN,
            reason=reason,
        )
        await self.incident_repo.create(incident)
        await self.audit.log(
            action="incident.create",
            resource="incident",
            resource_id=str(incident.id),
            metadata={"monitor_id": str(monitor_id), "reason": reason},
        )
        logger.warning(
            "incident_created",
            monitor_id=str(monitor_id),
            reason=reason,
        )
        return incident

    async def _resolve_incident(self, incident: Incident) -> Incident:
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now(UTC)
        await self.incident_repo.update(incident)
        await self.audit.log(
            action="incident.resolve",
            resource="incident",
            resource_id=str(incident.id),
            metadata={"monitor_id": str(incident.monitor_id)},
        )
        logger.info(
            "incident_resolved",
            incident_id=str(incident.id),
            monitor_id=str(incident.monitor_id),
        )
        return incident

    async def list_incidents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: IncidentStatus | None = None,
        monitor_id: UUID | None = None,
    ) -> IncidentListResponse:
        incidents, total = await self.incident_repo.list(page, page_size, status, monitor_id)
        return IncidentListResponse(
            items=[IncidentResponse.model_validate(i) for i in incidents],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_incident(self, incident_id: UUID) -> IncidentResponse:
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise ValueError("Incident not found")
        return IncidentResponse.model_validate(incident)

    async def update_incident(self, incident_id: UUID, data: IncidentUpdate) -> IncidentResponse:
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise ValueError("Incident not found")

        if data.status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(UTC)

        incident.status = data.status
        await self.incident_repo.update(incident)
        await self.audit.log(
            action="incident.update",
            resource="incident",
            resource_id=str(incident.id),
            metadata={"status": data.status.value},
        )
        return IncidentResponse.model_validate(incident)
