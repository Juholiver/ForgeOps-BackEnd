import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.health_check import router as health_check_router
from app.api.incident import router as incident_router
from app.api.metrics import router as metrics_router
from app.api.metrics_middleware import MetricsMiddleware
from app.api.middleware import RateLimitMiddleware
from app.api.monitor import router as monitor_router
from app.api.readiness import router as readiness_router
from app.api.security import SecurityHeadersMiddleware
from app.core.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.health import check_database

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("forgeops starting", env=settings.APP_ENV)
    yield
    logger.info("forgeops shutting down")


app = FastAPI(
    title="ForgeOps",
    description="API Monitoring and Observability Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(monitor_router)
app.include_router(health_check_router)
app.include_router(incident_router)
app.include_router(dashboard_router)
app.include_router(metrics_router)
app.include_router(readiness_router)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID", str(time.time_ns()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "forgeops", "version": "0.1.0"}


@app.get("/health/db", tags=["health"])
async def health_check_db(session: AsyncSession = Depends(get_db)) -> dict[str, str]:  # noqa: B008
    return await check_database(session)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
