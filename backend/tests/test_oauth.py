"""
Tests for OAuth authentication (Module 1 extension)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

from app.services.oauth import OAuthService


@pytest.mark.asyncio
async def test_authorize_redirect_google(test_client: AsyncClient, monkeypatch):
    """Test that the authorize endpoint redirects to Google's OAuth screen"""
    monkeypatch.setattr("app.config.settings.GOOGLE_CLIENT_ID", "test-client-id")

    response = await test_client.get(
        "/api/auth/oauth/google/authorize",
        params={"redirect_uri": "http://localhost:3000/oauth/callback"},
        follow_redirects=False,
    )

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "client_id=test-client-id" in location
    assert "state=" in location


@pytest.mark.asyncio
async def test_authorize_unsupported_provider(test_client: AsyncClient):
    """Test authorize with an unsupported provider returns 400"""
    response = await test_client.get(
        "/api/auth/oauth/twitter/authorize",
        params={"redirect_uri": "http://localhost:3000/oauth/callback"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_authorize_unconfigured_provider(test_client: AsyncClient, monkeypatch):
    """Test authorize when provider has no client_id configured returns 400"""
    monkeypatch.setattr("app.config.settings.FACEBOOK_CLIENT_ID", None)

    response = await test_client.get(
        "/api/auth/oauth/facebook/authorize",
        params={"redirect_uri": "http://localhost:3000/oauth/callback"},
    )
    assert response.status_code == 400


def test_state_token_roundtrip():
    """Test that a state token can be created and verified for the right provider"""
    state = OAuthService.create_state_token("google", "http://localhost:3000/callback")
    payload = OAuthService.verify_state_token(state, "google")

    assert payload is not None
    assert payload["provider"] == "google"
    assert payload["redirect_uri"] == "http://localhost:3000/callback"


def test_state_token_wrong_provider_rejected():
    """Test that a state token issued for one provider is rejected for another"""
    state = OAuthService.create_state_token("google", "http://localhost:3000/callback")
    payload = OAuthService.verify_state_token(state, "facebook")

    assert payload is None


def test_state_token_invalid_rejected():
    """Test that a garbage state token is rejected"""
    payload = OAuthService.verify_state_token("not-a-real-token", "google")
    assert payload is None


@pytest.mark.asyncio
async def test_callback_invalid_state(test_client: AsyncClient):
    """Test callback with an invalid state token fails cleanly"""
    response = await test_client.post(
        "/api/auth/oauth/callback",
        json={
            "provider": "google",
            "code": "fake-code",
            "state": "invalid-state-token",
            "redirect_uri": "http://localhost:3000/oauth/callback",
        },
    )
    assert response.status_code == 400
    assert "state" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_callback_creates_new_user(test_client: AsyncClient, test_db, monkeypatch):
    """Test full OAuth callback flow creates a new user when none exists"""
    monkeypatch.setattr("app.config.settings.GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr("app.config.settings.GOOGLE_CLIENT_SECRET", "test-secret")

    redirect_uri = "http://localhost:3000/oauth/callback"
    state = OAuthService.create_state_token("google", redirect_uri)

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {
        "access_token": "provider-access-token",
        "refresh_token": "provider-refresh-token",
        "expires_in": 3600,
    }

    mock_userinfo_response = MagicMock()
    mock_userinfo_response.status_code = 200
    mock_userinfo_response.json.return_value = {
        "sub": "google-user-12345",
        "email": "oauthuser@example.com",
        "name": "OAuth User",
        "picture": "https://example.com/avatar.jpg",
    }

    with patch("app.services.oauth.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_response
        mock_client.get.return_value = mock_userinfo_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        response = await test_client.post(
            "/api/auth/oauth/callback",
            json={
                "provider": "google",
                "code": "auth-code-from-google",
                "state": state,
                "redirect_uri": redirect_uri,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "oauthuser@example.com"
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_callback_reuses_existing_oauth_link(test_client: AsyncClient, test_db, monkeypatch):
    """Test that a second OAuth login with the same provider account reuses the user"""
    monkeypatch.setattr("app.config.settings.GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr("app.config.settings.GOOGLE_CLIENT_SECRET", "test-secret")

    redirect_uri = "http://localhost:3000/oauth/callback"

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {
        "access_token": "provider-access-token",
        "refresh_token": "provider-refresh-token",
        "expires_in": 3600,
    }

    mock_userinfo_response = MagicMock()
    mock_userinfo_response.status_code = 200
    mock_userinfo_response.json.return_value = {
        "sub": "google-user-99999",
        "email": "repeatuser@example.com",
        "name": "Repeat User",
        "picture": None,
    }

    user_ids = []
    for _ in range(2):
        state = OAuthService.create_state_token("google", redirect_uri)
        with patch("app.services.oauth.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_token_response
            mock_client.get.return_value = mock_userinfo_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            response = await test_client.post(
                "/api/auth/oauth/callback",
                json={
                    "provider": "google",
                    "code": "auth-code-from-google",
                    "state": state,
                    "redirect_uri": redirect_uri,
                },
            )
        assert response.status_code == 200
        user_ids.append(response.json()["user"]["id"])

    assert user_ids[0] == user_ids[1]


@pytest.mark.asyncio
async def test_callback_token_exchange_failure(test_client: AsyncClient, monkeypatch):
    """Test that a failed token exchange with the provider returns 400"""
    monkeypatch.setattr("app.config.settings.GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr("app.config.settings.GOOGLE_CLIENT_SECRET", "test-secret")

    redirect_uri = "http://localhost:3000/oauth/callback"
    state = OAuthService.create_state_token("google", redirect_uri)

    mock_failure_response = MagicMock()
    mock_failure_response.status_code = 400
    mock_failure_response.text = "invalid_grant"

    with patch("app.services.oauth.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_failure_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        response = await test_client.post(
            "/api/auth/oauth/callback",
            json={
                "provider": "google",
                "code": "bad-code",
                "state": state,
                "redirect_uri": redirect_uri,
            },
        )

    assert response.status_code == 400
