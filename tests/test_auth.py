import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User, UserRole
from app.infrastructure.security import hash_password


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.VIEWER,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


def test_register(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "name": "New User",
            "email": "new@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["role"] == "viewer"
    assert "id" in data


def test_register_duplicate_email(client: TestClient, test_user: User):
    response = client.post(
        "/auth/register",
        json={
            "name": "Another User",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 400


def test_login_success(client: TestClient, test_user: User):
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, test_user: User):
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_get_current_user(client: TestClient, test_user: User):
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_get_current_user_no_token(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client: TestClient):
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


def test_refresh_token(client: TestClient, test_user: User):
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_invalid_token(client: TestClient):
    response = client.post("/auth/refresh", json={"refresh_token": "invalid"})
    assert response.status_code == 401
