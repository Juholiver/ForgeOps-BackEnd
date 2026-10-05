from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_authenticated_user
from app.application.monitor_service import MonitorService
from app.domain.models import User
from app.domain.monitor_schemas import (
    MonitorCreate,
    MonitorListResponse,
    MonitorResponse,
    MonitorUpdate,
)
from app.infrastructure.database import get_db

router = APIRouter(prefix="/monitors", tags=["monitors"])


def get_monitor_service(
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> MonitorService:
    return MonitorService(session)


@router.post("", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    data: MonitorCreate,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: MonitorService = Depends(get_monitor_service),  # noqa: B008
) -> MonitorResponse:
    return await service.create_monitor(data, user.id)


@router.get("", response_model=MonitorListResponse)
async def list_monitors(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    active_only: bool = Query(default=False),
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: MonitorService = Depends(get_monitor_service),  # noqa: B008
) -> MonitorListResponse:
    return await service.list_monitors(page, page_size, active_only, user_id=user.id)


@router.get("/{monitor_id}", response_model=MonitorResponse)
async def get_monitor(
    monitor_id: UUID,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: MonitorService = Depends(get_monitor_service),  # noqa: B008
) -> MonitorResponse:
    try:
        return await service.get_monitor(monitor_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{monitor_id}", response_model=MonitorResponse)
async def update_monitor(
    monitor_id: UUID,
    data: MonitorUpdate,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: MonitorService = Depends(get_monitor_service),  # noqa: B008
) -> MonitorResponse:
    try:
        return await service.update_monitor(monitor_id, data, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{monitor_id}/toggle", response_model=MonitorResponse)
async def toggle_monitor(
    monitor_id: UUID,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: MonitorService = Depends(get_monitor_service),  # noqa: B008
) -> MonitorResponse:
    try:
        return await service.toggle_monitor(monitor_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: UUID,
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: MonitorService = Depends(get_monitor_service),  # noqa: B008
) -> None:
    try:
        await service.delete_monitor(monitor_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
