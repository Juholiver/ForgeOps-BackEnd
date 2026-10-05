import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models import User
from app.infrastructure.database import get_db
from app.infrastructure.models import Base
from app.infrastructure.repositories import UserRepository
from app.infrastructure.security import create_access_token
from app.main import app


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncSession:
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def client(session: AsyncSession) -> TestClient:
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    repo = UserRepository(session)
    return await repo.create(
        User(name="Auth User", email="auth-user@example.com", password_hash=None)
    )


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def other_user(session: AsyncSession) -> User:
    repo = UserRepository(session)
    return await repo.create(
        User(name="Other User", email="other-user@example.com", password_hash=None)
    )


@pytest.fixture
def other_headers(other_user: User) -> dict[str, str]:
    token = create_access_token(other_user.id, other_user.role.value)
    return {"Authorization": f"Bearer {token}"}
