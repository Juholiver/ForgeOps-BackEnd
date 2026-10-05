from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_authenticated_user
from app.application.incident_service import IncidentService
from app.domain.incident_schemas import (
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
)
from app.domain.models import IncidentStatus, User
from app.infrastructure.database import get_db

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_incident_service(
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> IncidentService:
    return IncidentService(session)


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: IncidentStatus | None = Query(default=None, alias="status"),  # noqa: B008
    monitor_id: UUID | None = None,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: IncidentService = Depends(get_incident_service),  # noqa: B008
) -> IncidentListResponse:
    return await service.list_incidents(page, page_size, status_filter, monitor_id, user_id=user.id)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: IncidentService = Depends(get_incident_service),  # noqa: B008
) -> IncidentResponse:
    try:
        return await service.get_incident(incident_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: IncidentService = Depends(get_incident_service),  # noqa: B008
) -> IncidentResponse:
    try:
        return await service.update_incident(incident_id, data, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
