from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    method: str = Field(default="GET", pattern="^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)$")
    interval_seconds: int = Field(default=60, ge=10, le=3600)
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    expected_status: int = Field(default=200, ge=100, le=599)


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    method: str | None = Field(default=None, pattern="^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)$")
    interval_seconds: int | None = Field(default=None, ge=10, le=3600)
    timeout_seconds: int | None = Field(default=None, ge=1, le=120)
    expected_status: int | None = Field(default=None, ge=100, le=599)
    active: bool | None = None


class MonitorResponse(BaseModel):
    id: UUID
    name: str
    url: str
    method: str
    interval_seconds: int
    timeout_seconds: int
    expected_status: int
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonitorListResponse(BaseModel):
    items: list[MonitorResponse]
    total: int
    page: int
    page_size: int
