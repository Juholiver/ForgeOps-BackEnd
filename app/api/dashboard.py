from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_authenticated_user
from app.application.dashboard_service import DashboardService
from app.domain.dashboard_schemas import (
    AvailabilityResponse,
    CheckHistoryResponse,
    DashboardSummaryResponse,
    IncidentSummaryResponse,
    LatencyResponse,
    UptimeResponse,
)
from app.domain.models import User
from app.infrastructure.database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> DashboardService:
    return DashboardService(session)


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> DashboardSummaryResponse:
    return await service.get_dashboard_summary(user_id=user.id)


@router.get("/uptime/{monitor_id}", response_model=UptimeResponse)
async def get_uptime(
    monitor_id: UUID,
    days: int = Query(default=7, ge=1, le=30),
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> UptimeResponse:
    try:
        return await service.get_uptime(monitor_id, days, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/latency/{monitor_id}", response_model=LatencyResponse)
async def get_latency(
    monitor_id: UUID,
    days: int = Query(default=7, ge=1, le=30),
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> LatencyResponse:
    try:
        return await service.get_latency(monitor_id, days, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/incidents", response_model=IncidentSummaryResponse)
async def get_incident_summary(
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> IncidentSummaryResponse:
    return await service.get_incident_summary(user_id=user.id)


@router.get("/availability/{monitor_id}", response_model=AvailabilityResponse)
async def get_availability(
    monitor_id: UUID,
    days: int = Query(default=7, ge=1, le=30),
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> AvailabilityResponse:
    try:
        return await service.get_availability(monitor_id, days, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/history/{monitor_id}", response_model=CheckHistoryResponse)
async def get_check_history(
    monitor_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=30),
    user: User = Depends(get_authenticated_user),  # noqa: B008
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> CheckHistoryResponse:
    try:
        return await service.get_check_history(monitor_id, page, page_size, days, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
