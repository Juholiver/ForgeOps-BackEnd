from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class CheckStatus(StrEnum):
    UP = "up"
    DOWN = "down"
    TIMEOUT = "timeout"
    ERROR = "error"


class CheckResultResponse(BaseModel):
    id: UUID
    monitor_id: UUID
    status: CheckStatus
    http_status: int | None = None
    response_time_ms: float | None = None
    error_message: str | None = None
    checked_at: datetime

    model_config = {"from_attributes": True}
