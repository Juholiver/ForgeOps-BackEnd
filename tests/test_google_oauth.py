from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.core.config import settings
from app.infrastructure.google_oauth import GoogleUserInfo


def get_oauth_state(client: TestClient) -> str:
    response = client.get("/auth/google", follow_redirects=False)
    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/")
    state = parse_qs(urlparse(location).query).get("state")
    assert state
    return state[0]


def callback(client: TestClient, state: str, code: str = "test-code"):
    return client.get(
        "/auth/google/callback",
        params={"code": code, "state": state},
        follow_redirects=False,
    )


def parse_redirect_tokens(location: str) -> tuple[str, str]:
    assert location.startswith(f"{settings.FRONTEND_URL}/auth/callback")
    query = parse_qs(urlparse(location).query)
    return query["access_token"][0], query["refresh_token"][0]


def test_google_login_redirects_to_consent(client: TestClient):
    state = get_oauth_state(client)
    assert state


@patch("app.application.auth_service.GoogleOAuthClient.get_userinfo")
@patch("app.application.auth_service.GoogleOAuthClient.exchange_code")
def test_google_callback_creates_user_and_returns_tokens(
    mock_exchange, mock_userinfo, client: TestClient
):
    mock_exchange.return_value = "google-access-token"
    mock_userinfo.return_value = GoogleUserInfo(
        sub="google-sub-123",
        email="new-user@example.com",
        name="New User",
        picture="https://example.com/avatar.png",
    )

    state = get_oauth_state(client)
    response = callback(client, state)
    assert response.status_code == 307

    access_token, refresh_token = parse_redirect_tokens(response.headers["location"])
    assert access_token
    assert refresh_token

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "new-user@example.com"
    assert data["name"] == "New User"

    monitors = client.get("/monitors", headers={"Authorization": f"Bearer {access_token}"})
    assert monitors.status_code == 200


@patch("app.application.auth_service.GoogleOAuthClient.get_userinfo")
@patch("app.application.auth_service.GoogleOAuthClient.exchange_code")
def test_google_callback_is_idempotent(mock_exchange, mock_userinfo, client: TestClient):
    mock_exchange.return_value = "google-access-token"
    mock_userinfo.return_value = GoogleUserInfo(
        sub="google-sub-123",
        email="new-user@example.com",
        name="New User",
    )

    state = get_oauth_state(client)
    first = callback(client, state)
    first_token = parse_qs(urlparse(first.headers["location"]).query)["access_token"][0]

    state = get_oauth_state(client)
    second = callback(client, state)
    assert second.status_code == 307

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "new-user@example.com"

    duplicate = client.post(
        "/auth/register",
        json={"name": "Dup", "email": "new-user@example.com", "password": "password123"},
    )
    assert duplicate.status_code == 400


@patch("app.application.auth_service.GoogleOAuthClient.get_userinfo")
@patch("app.application.auth_service.GoogleOAuthClient.exchange_code")
def test_google_callback_links_existing_password_user(
    mock_exchange, mock_userinfo, client: TestClient
):
    client.post(
        "/auth/register",
        json={"name": "Legacy", "email": "legacy@example.com", "password": "password123"},
    )

    mock_exchange.return_value = "google-access-token"
    mock_userinfo.return_value = GoogleUserInfo(
        sub="google-sub-legacy",
        email="legacy@example.com",
        name="Legacy",
    )

    state = get_oauth_state(client)
    response = callback(client, state)
    assert response.status_code == 307

    login = client.post(
        "/auth/login",
        json={"email": "legacy@example.com", "password": "password123"},
    )
    assert login.status_code == 200


def test_google_callback_invalid_state(client: TestClient):
    response = client.get(
        "/auth/google/callback",
        params={"code": "abc", "state": "not-a-valid-state"},
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_google_callback_missing_code(client: TestClient):
    state = get_oauth_state(client)
    response = client.get(
        "/auth/google/callback",
        params={"state": state},
        follow_redirects=False,
    )
    assert response.status_code == 400


@patch("app.application.auth_service.GoogleOAuthClient.exchange_code")
def test_google_callback_exchange_failure(mock_exchange, client: TestClient):
    mock_exchange.side_effect = ValueError("bad code")

    state = get_oauth_state(client)
    response = callback(client, state, code="bad-code")
    assert response.status_code == 400
