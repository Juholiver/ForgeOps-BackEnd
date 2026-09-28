from fastapi import APIRouter
from prometheus_client import generate_latest
from starlette.responses import PlainTextResponse

router = APIRouter(tags=["observability"])


@router.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(content=generate_latest().decode("utf-8"))
