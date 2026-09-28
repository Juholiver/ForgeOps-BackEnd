import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_connection(session: AsyncSession):
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_database_session_works(session: AsyncSession):
    result = await session.execute(text("SELECT 1 + 1"))
    assert result.scalar() == 2
