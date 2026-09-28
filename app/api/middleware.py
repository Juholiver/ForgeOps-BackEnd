from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.infrastructure.redis_client import redis_client

RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        allowed, _ = await redis_client.check_rate_limit(
            key, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
            )

        return await call_next(request)
