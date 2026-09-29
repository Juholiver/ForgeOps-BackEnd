from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.health_check_service import HealthCheckService
from app.domain.check_schemas import CheckResultResponse
from app.infrastructure.database import get_db

router = APIRouter(prefix="/health-check", tags=["health-check"])


def get_health_check_service(
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> HealthCheckService:
    return HealthCheckService(session)


@router.post("/run-all", response_model=list[CheckResultResponse])
async def execute_all_checks(
    service: HealthCheckService = Depends(get_health_check_service),  # noqa: B008
) -> list[CheckResultResponse]:
    return await service.execute_all_active()


@router.post("/{monitor_id}", response_model=CheckResultResponse)
async def execute_check(
    monitor_id: UUID,
    service: HealthCheckService = Depends(get_health_check_service),  # noqa: B008
) -> CheckResultResponse:
    try:
        return await service.execute_check(monitor_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
