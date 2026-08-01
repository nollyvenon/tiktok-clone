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
