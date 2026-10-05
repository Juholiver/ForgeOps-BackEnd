from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_authenticated_user
from app.application.audit_service import AuditService
from app.domain.audit_schemas import AuditLogListResponse
from app.domain.models import User, UserRole
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
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: AuditService = Depends(get_audit_service),  # noqa: B008
) -> AuditLogListResponse:
    target_user_id = user_id if user.role == UserRole.ADMIN else user.id
    return await service.list_logs(page, page_size, target_user_id, action, resource)
