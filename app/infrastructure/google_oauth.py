from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.core.config import settings

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


@dataclass
class GoogleUserInfo:
    sub: str
    email: str
    name: str
    picture: str | None = None


def build_authorization_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"


class GoogleOAuthClient:
    async def exchange_code(self, code: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            payload = response.json()
            access_token = payload.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise ValueError("Token response missing access_token")
            return access_token

    async def get_userinfo(self, access_token: str) -> GoogleUserInfo:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            payload = response.json()
            sub = payload.get("sub")
            email = payload.get("email")
            if not isinstance(sub, str) or not sub:
                raise ValueError("Userinfo response missing sub")
            if not isinstance(email, str) or not email:
                raise ValueError("Userinfo response missing email")
            name = payload.get("name")
            picture = payload.get("picture")
            return GoogleUserInfo(
                sub=sub,
                email=email,
                name=name if isinstance(name, str) and name else email,
                picture=picture if isinstance(picture, str) and picture else None,
            )
