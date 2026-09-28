from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.health import check_database


@pytest.mark.asyncio
async def test_check_database_success():
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = None

    result = await check_database(session)

    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_check_database_failure():
    session = AsyncMock(spec=AsyncSession)
    session.execute.side_effect = Exception("connection refused")

    result = await check_database(session)

    assert result["status"] == "error"
    assert "connection refused" in result["detail"]
