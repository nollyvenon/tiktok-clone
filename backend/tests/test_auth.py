"""
Authentication API tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(test_client: AsyncClient, register_user_data):
    """Test successful user registration"""
    response = await test_client.post("/api/auth/register", json=register_user_data)

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == register_user_data["email"]
    assert data["user"]["username"] == register_user_data["username"]


@pytest.mark.asyncio
async def test_register_invalid_email(test_client: AsyncClient, register_user_data):
    """Test registration with invalid email"""
    register_user_data["email"] = "invalid-email"
    response = await test_client.post("/api/auth/register", json=register_user_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_short_password(test_client: AsyncClient, register_user_data):
    """Test registration with password too short"""
    register_user_data["password"] = "short"
    response = await test_client.post("/api/auth/register", json=register_user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(test_client: AsyncClient, register_user_data):
    """Test registration with weak password"""
    register_user_data["password"] = "onlylowercase123"
    response = await test_client.post("/api/auth/register", json=register_user_data)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client: AsyncClient, register_user_data):
    """Test registration with duplicate email"""
    # Register first user
    response1 = await test_client.post("/api/auth/register", json=register_user_data)
    assert response1.status_code == 201

    # Try to register with same email
    register_user_data["username"] = "differentuser"
    response2 = await test_client.post("/api/auth/register", json=register_user_data)

    assert response2.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_username(test_client: AsyncClient, register_user_data):
    """Test registration with duplicate username"""
    # Register first user
    response1 = await test_client.post("/api/auth/register", json=register_user_data)
    assert response1.status_code == 201

    # Try to register with same username
    register_user_data["email"] = "different@example.com"
    response2 = await test_client.post("/api/auth/register", json=register_user_data)

    assert response2.status_code == 400


@pytest.mark.asyncio
async def test_register_short_username(test_client: AsyncClient, register_user_data):
    """Test registration with username too short"""
    register_user_data["username"] = "ab"
    response = await test_client.post("/api/auth/register", json=register_user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, register_user_data, login_user_data):
    """Test successful login"""
    # First register a user
    await test_client.post("/api/auth/register", json=register_user_data)

    # Then login
    response = await test_client.post("/api/auth/login", json=login_user_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_email(test_client: AsyncClient, login_user_data):
    """Test login with non-existent email"""
    response = await test_client.post("/api/auth/login", json=login_user_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(test_client: AsyncClient, register_user_data, login_user_data):
    """Test login with wrong password"""
    # Register user
    await test_client.post("/api/auth/register", json=register_user_data)

    # Try login with wrong password
    login_user_data["password"] = "WrongPassword123!"
    response = await test_client.post("/api/auth/login", json=login_user_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_success(test_client: AsyncClient, register_user_data):
    """Test getting current user info"""
    # Register and login
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    # Get current user
    response = await test_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == register_user_data["email"]
    assert data["username"] == register_user_data["username"]


@pytest.mark.asyncio
async def test_get_current_user_no_token(test_client: AsyncClient):
    """Test getting current user without token"""
    response = await test_client.get("/api/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(test_client: AsyncClient):
    """Test getting current user with invalid token"""
    response = await test_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(test_client: AsyncClient, register_user_data):
    """Test token refresh"""
    # Register user
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    refresh_token = register_response.json()["refresh_token"]

    # Refresh token
    response = await test_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(test_client: AsyncClient):
    """Test token refresh with invalid token"""
    response = await test_client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_success(test_client: AsyncClient, register_user_data):
    """Test logout"""
    # Register and get token
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    # Logout
    response = await test_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logout_no_token(test_client: AsyncClient):
    """Test logout without token"""
    response = await test_client.post("/api/auth/logout")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_access_token_immediately(test_client: AsyncClient, register_user_data):
    """
    A logged-out access token must stop working immediately, not just once
    it naturally expires - logout must invalidate the underlying session,
    not merely be a client-side no-op.
    """
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    # Token works before logout
    pre_logout = await test_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert pre_logout.status_code == 200

    await test_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"})

    # Same token must be rejected after logout, even though the JWT itself
    # has not expired
    post_logout = await test_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert post_logout.status_code == 401


@pytest.mark.asyncio
async def test_default_logout_only_revokes_current_session(test_client: AsyncClient, register_user_data):
    """Logging out on one device must not sign the user out everywhere else"""
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token_a = register_response.json()["access_token"]

    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": register_user_data["email"], "password": register_user_data["password"]},
    )
    token_b = login_response.json()["access_token"]

    await test_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token_a}"})

    # Session A is dead, session B is untouched
    resp_a = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_a.status_code == 401
    assert resp_b.status_code == 200


@pytest.mark.asyncio
async def test_logout_everywhere_revokes_all_sessions(test_client: AsyncClient, register_user_data):
    """?everywhere=true must revoke every session for the user, not just the current one"""
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token_a = register_response.json()["access_token"]

    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": register_user_data["email"], "password": register_user_data["password"]},
    )
    token_b = login_response.json()["access_token"]

    await test_client.post(
        "/api/auth/logout?everywhere=true", headers={"Authorization": f"Bearer {token_a}"}
    )

    resp_a = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_a.status_code == 401
    assert resp_b.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions(test_client: AsyncClient, register_user_data):
    """Listing sessions shows all active devices and marks the current one"""
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token_a = register_response.json()["access_token"]

    await test_client.post(
        "/api/auth/login",
        json={"email": register_user_data["email"], "password": register_user_data["password"]},
    )

    response = await test_client.get("/api/auth/sessions", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) == 2
    current_sessions = [s for s in sessions if s["is_current"]]
    assert len(current_sessions) == 1


@pytest.mark.asyncio
async def test_revoke_specific_session(test_client: AsyncClient, register_user_data):
    """Revoking another device's session logs that device out without affecting the current one"""
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token_a = register_response.json()["access_token"]

    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": register_user_data["email"], "password": register_user_data["password"]},
    )
    token_b = login_response.json()["access_token"]

    sessions_response = await test_client.get(
        "/api/auth/sessions", headers={"Authorization": f"Bearer {token_a}"}
    )
    other_session = next(s for s in sessions_response.json()["sessions"] if not s["is_current"])

    revoke_response = await test_client.delete(
        f"/api/auth/sessions/{other_session['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert revoke_response.status_code == 200

    resp_a = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_a.status_code == 200
    assert resp_b.status_code == 401


@pytest.mark.asyncio
async def test_revoke_nonexistent_session_returns_404(test_client: AsyncClient, register_user_data):
    """Revoking a made-up session id returns 404, not a silent success"""
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token = register_response.json()["access_token"]

    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await test_client.delete(
        f"/api/auth/sessions/{fake_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_change_password_success(test_client: AsyncClient, register_user_data):
    """Test password change"""
    # Register user
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    # Change password
    response = await test_client.post(
        "/api/auth/change-password",
        json={
            "current_password": register_user_data["password"],
            "new_password": "NewPass@1234567",
            "confirm_password": "NewPass@1234567",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200

    # Try login with new password
    login_response = await test_client.post(
        "/api/auth/login",
        json={
            "email": register_user_data["email"],
            "password": "NewPass@1234567",
        }
    )

    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(test_client: AsyncClient, register_user_data):
    """Test password change with wrong current password"""
    # Register user
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    # Try to change password with wrong current
    response = await test_client.post(
        "/api/auth/change-password",
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPass@1234567",
            "confirm_password": "NewPass@1234567",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_change_password_mismatch(test_client: AsyncClient, register_user_data):
    """Test password change with mismatched new passwords"""
    # Register user
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    # Try to change password with mismatched confirmation
    response = await test_client.post(
        "/api/auth/change-password",
        json={
            "current_password": register_user_data["password"],
            "new_password": "NewPass@1234567",
            "confirm_password": "DifferentPass@1234",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_export_my_data(test_client: AsyncClient, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    video_response = await test_client.post(
        "/api/videos",
        json={"title": "Exportable video", "video_url": "https://example.com/export.mp4"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    video_id = video_response.json()["id"]

    await test_client.post(
        f"/api/videos/{video_id}/comments",
        json={"content": "My own comment"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    response = await test_client.get("/api/auth/me/export", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["email"] == register_user_data["email"]
    assert len(data["videos"]) == 1
    assert data["videos"][0]["title"] == "Exportable video"
    assert len(data["comments"]) == 1
    assert data["comments"][0]["content"] == "My own comment"


@pytest.mark.asyncio
async def test_export_requires_auth(test_client: AsyncClient):
    response = await test_client.get("/api/auth/me/export")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_account_requires_correct_password(test_client: AsyncClient, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    response = await test_client.request(
        "DELETE",
        "/api/auth/me",
        json={"password": "WrongPassword@123"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_account_success_and_revokes_login(test_client: AsyncClient, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    response = await test_client.request(
        "DELETE",
        "/api/auth/me",
        json={"password": register_user_data["password"]},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": register_user_data["email"], "password": register_user_data["password"]},
    )
    assert login_response.status_code == 401

    me_response = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_delete_account_requires_auth(test_client: AsyncClient):
    response = await test_client.request("DELETE", "/api/auth/me", json={"password": "whatever"})
    assert response.status_code == 401
