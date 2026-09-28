from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard_service import DashboardService
from app.domain.dashboard_schemas import (
    AvailabilityResponse,
    CheckHistoryResponse,
    DashboardSummaryResponse,
    IncidentSummaryResponse,
    LatencyResponse,
    UptimeResponse,
)
from app.infrastructure.database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> DashboardService:
    return DashboardService(session)


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> DashboardSummaryResponse:
    return await service.get_dashboard_summary()


@router.get("/uptime/{monitor_id}", response_model=UptimeResponse)
async def get_uptime(
    monitor_id: UUID,
    days: int = Query(default=7, ge=1, le=30),
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> UptimeResponse:
    return await service.get_uptime(monitor_id, days)


@router.get("/latency/{monitor_id}", response_model=LatencyResponse)
async def get_latency(
    monitor_id: UUID,
    days: int = Query(default=7, ge=1, le=30),
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> LatencyResponse:
    return await service.get_latency(monitor_id, days)


@router.get("/incidents", response_model=IncidentSummaryResponse)
async def get_incident_summary(
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> IncidentSummaryResponse:
    return await service.get_incident_summary()


@router.get("/availability/{monitor_id}", response_model=AvailabilityResponse)
async def get_availability(
    monitor_id: UUID,
    days: int = Query(default=7, ge=1, le=30),
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> AvailabilityResponse:
    return await service.get_availability(monitor_id, days)


@router.get("/history/{monitor_id}", response_model=CheckHistoryResponse)
async def get_check_history(
    monitor_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=30),
    service: DashboardService = Depends(get_dashboard_service),  # noqa: B008
) -> CheckHistoryResponse:
    return await service.get_check_history(monitor_id, page, page_size, days)
