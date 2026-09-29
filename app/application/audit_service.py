import json
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.audit_schemas import AuditLogListResponse, AuditLogResponse
from app.domain.models import AuditLog
from app.infrastructure.audit_repository import AuditLogRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = AuditLogRepository(session)

    async def log(
        self,
        action: str,
        resource: str,
        user_id: UUID | None = None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            metadata=json.dumps(metadata) if metadata else None,
        )
        return await self.audit_repo.create(log)

    async def list_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        user_id: UUID | None = None,
        action: str | None = None,
        resource: str | None = None,
    ) -> AuditLogListResponse:
        logs, total = await self.audit_repo.list(page, page_size, user_id, action, resource)
        return AuditLogListResponse(
            items=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
        )
