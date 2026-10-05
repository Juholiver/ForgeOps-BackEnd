from uuid import UUID

from httpx import HTTPError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit_service import AuditService
from app.domain.models import User, UserRole
from app.domain.schemas import TokenResponse, UserCreate, UserResponse
from app.infrastructure.google_oauth import GoogleOAuthClient, GoogleUserInfo
from app.infrastructure.repositories import UserRepository
from app.infrastructure.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_valid_oauth_state,
    verify_password,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit = AuditService(session)

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
        await self.audit.log(
            action="user.register",
            resource="user",
            user_id=user.id,
            resource_id=str(user.id),
            metadata={"email": data.email},
        )
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or user.password_hash is None:
            raise ValueError("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User is inactive")

        await self.audit.log(
            action="user.login",
            resource="user",
            user_id=user.id,
            resource_id=str(user.id),
        )
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

    async def handle_google_callback(self, code: str, state: str) -> TokenResponse:
        if not code or not is_valid_oauth_state(state):
            raise ValueError("Invalid OAuth state or code")

        try:
            oauth_client = GoogleOAuthClient()
            google_access_token = await oauth_client.exchange_code(code)
            info = await oauth_client.get_userinfo(google_access_token)
        except (HTTPError, ValueError) as e:
            raise ValueError("Google OAuth exchange failed") from e

        user = await self.get_or_create_google_user(info)
        if not user.is_active:
            raise ValueError("User is inactive")

        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_or_create_google_user(self, info: GoogleUserInfo) -> User:
        user = await self.user_repo.get_by_google_id(info.sub)
        if user:
            return user

        user = await self.user_repo.get_by_email(info.email)
        if user:
            user.google_id = info.sub
            if info.picture:
                user.avatar_url = info.picture
            await self.user_repo.update(user)
            await self.audit.log(
                action="user.link_google",
                resource="user",
                user_id=user.id,
                resource_id=str(user.id),
                metadata={"email": info.email},
            )
            return user

        user = User(
            name=info.name,
            email=info.email,
            password_hash=None,
            google_id=info.sub,
            avatar_url=info.picture,
            role=UserRole.VIEWER,
        )
        await self.user_repo.create(user)
        await self.audit.log(
            action="user.register_google",
            resource="user",
            user_id=user.id,
            resource_id=str(user.id),
            metadata={"email": info.email},
        )
        return user
