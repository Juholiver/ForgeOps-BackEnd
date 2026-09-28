from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit_service import AuditService
from app.domain.audit_schemas import AuditLogListResponse
from app.infrastructure.database import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_service(
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> AuditService:
    return AuditService(session)


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    user_id: UUID | None = None,
    action: str | None = None,
    resource: str | None = None,
    service: AuditService = Depends(get_audit_service),  # noqa: B008
) -> AuditLogListResponse:
    return await service.list_logs(page, page_size, user_id, action, resource)
