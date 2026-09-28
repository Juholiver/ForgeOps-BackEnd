from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User, UserRole
from app.domain.schemas import TokenResponse, UserCreate, UserResponse
from app.infrastructure.repositories import UserRepository
from app.infrastructure.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: UserCreate) -> UserResponse:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=UserRole.VIEWER,
        )
        await self.user_repo.create(user)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User is inactive")

        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id_str = payload.get("sub")
        if not isinstance(user_id_str, str):
            raise ValueError("Invalid token payload")
        user_id = UUID(user_id_str)
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_current_user(self, token: str) -> User:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise ValueError("Invalid token")

        user_id_str = payload.get("sub")
        if not isinstance(user_id_str, str):
            raise ValueError("Invalid token payload")
        user_id = UUID(user_id_str)
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        return user
