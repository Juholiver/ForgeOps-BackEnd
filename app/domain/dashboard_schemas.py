from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UptimeResponse(BaseModel):
    monitor_id: UUID
    uptime_percentage: float
    total_checks: int
    successful_checks: int
    period_start: datetime
    period_end: datetime


class LatencyResponse(BaseModel):
    monitor_id: UUID
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    total_checks: int


class IncidentSummaryResponse(BaseModel):
    total: int
    open: int
    investigating: int
    resolved: int


class AvailabilityResponse(BaseModel):
    monitor_id: UUID
    availability_percentage: float
    total_checks: int
    failed_checks: int
    period_start: datetime
    period_end: datetime


class CheckHistoryResponse(BaseModel):
    monitor_id: UUID
    checks: list[dict[str, object]]
    total: int
    page: int
    page_size: int


class DashboardSummaryResponse(BaseModel):
    total_monitors: int
    active_monitors: int
    total_checks: int
    total_incidents: int
    open_incidents: int
    avg_uptime: float
    avg_latency_ms: float
