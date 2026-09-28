from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.models import IncidentStatus


class IncidentResponse(BaseModel):
    id: UUID
    monitor_id: UUID
    status: IncidentStatus
    reason: str
    started_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class IncidentUpdate(BaseModel):
    status: IncidentStatus


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int
