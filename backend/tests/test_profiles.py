"""
Profile API tests
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_user_profile(test_client: AsyncClient, register_user_data):
    """Test getting user profile"""
    # Register user first
    response = await test_client.post("/api/auth/register", json=register_user_data)
    assert response.status_code == 201
    user_id = response.json()["user"]["id"]

    # Get profile
    response = await test_client.get(f"/api/profiles/{user_id}")
    assert response.status_code == 200
    profile = response.json()

    assert profile["user"]["id"] == user_id
    assert profile["user"]["email"] == register_user_data["email"]
    assert profile["user"]["username"] == register_user_data["username"]
    assert profile["statistics"]["followers_count"] == 0
    assert profile["statistics"]["following_count"] == 0


@pytest.mark.asyncio
async def test_get_user_profile_by_username(test_client: AsyncClient, register_user_data):
    """Test getting user profile by username"""
    # Register user
    response = await test_client.post("/api/auth/register", json=register_user_data)
    assert response.status_code == 201

    # Get profile by username
    response = await test_client.get(f"/api/profiles/username/{register_user_data['username']}")
    assert response.status_code == 200
    profile = response.json()

    assert profile["user"]["username"] == register_user_data["username"]
    assert profile["user"]["email"] == register_user_data["email"]


@pytest.mark.asyncio
async def test_get_nonexistent_user_profile(test_client: AsyncClient):
    """Test getting non-existent user profile"""
    fake_id = str(uuid4())
    response = await test_client.get(f"/api/profiles/{fake_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_profile(test_client: AsyncClient, register_user_data):
    """Test updating user profile"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    assert response.status_code == 201
    access_token = response.json()["access_token"]

    # Update profile
    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "bio": "A cool person",
        "website": "https://example.com"
    }
    response = await test_client.put(
        "/api/profiles/me",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    user = response.json()

    assert user["first_name"] == "John"
    assert user["last_name"] == "Doe"
    assert user["bio"] == "A cool person"
    assert user["website"] == "https://example.com"


@pytest.mark.asyncio
async def test_update_profile_unauthorized(test_client: AsyncClient):
    """Test updating profile without authentication"""
    response = await test_client.put(
        "/api/profiles/me",
        json={"first_name": "John"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_follow_user(test_client: AsyncClient, register_user_data):
    """Test following a user"""
    # Register two users
    response1 = await test_client.post("/api/auth/register", json=register_user_data)
    user1_id = response1.json()["user"]["id"]
    token1 = response1.json()["access_token"]

    register_user_data["email"] = "user2@example.com"
    register_user_data["username"] = "user2"
    response2 = await test_client.post("/api/auth/register", json=register_user_data)
    user2_id = response2.json()["user"]["id"]

    # User 1 follows User 2
    response = await test_client.post(
        f"/api/profiles/{user2_id}/follow",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_following"] is True
    assert data["followers_count"] == 1

    # User 1 unfollows User 2
    response = await test_client.post(
        f"/api/profiles/{user2_id}/follow",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_following"] is False
    assert data["followers_count"] == 0


@pytest.mark.asyncio
async def test_cannot_follow_self(test_client: AsyncClient, register_user_data):
    """Test that user cannot follow themselves"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    user_id = response.json()["user"]["id"]
    token = response.json()["access_token"]

    response = await test_client.post(
        f"/api/profiles/{user_id}/follow",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "cannot follow yourself" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_followers(test_client: AsyncClient, register_user_data):
    """Test getting user followers"""
    # Register two users
    response1 = await test_client.post("/api/auth/register", json=register_user_data)
    user1_id = response1.json()["user"]["id"]
    token1 = response1.json()["access_token"]

    register_user_data["email"] = "user2@example.com"
    register_user_data["username"] = "user2"
    response2 = await test_client.post("/api/auth/register", json=register_user_data)
    user2_id = response2.json()["user"]["id"]

    # User 1 follows User 2
    await test_client.post(
        f"/api/profiles/{user2_id}/follow",
        headers={"Authorization": f"Bearer {token1}"}
    )

    # Get followers of User 2
    response = await test_client.get(f"/api/profiles/{user2_id}/followers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["users"]) == 1
    assert data["users"][0]["id"] == user1_id


@pytest.mark.asyncio
async def test_get_following(test_client: AsyncClient, register_user_data):
    """Test getting users that a user is following"""
    # Register two users
    response1 = await test_client.post("/api/auth/register", json=register_user_data)
    user1_id = response1.json()["user"]["id"]
    token1 = response1.json()["access_token"]

    register_user_data["email"] = "user2@example.com"
    register_user_data["username"] = "user2"
    response2 = await test_client.post("/api/auth/register", json=register_user_data)
    user2_id = response2.json()["user"]["id"]

    # User 1 follows User 2
    await test_client.post(
        f"/api/profiles/{user2_id}/follow",
        headers={"Authorization": f"Bearer {token1}"}
    )

    # Get following of User 1
    response = await test_client.get(f"/api/profiles/{user1_id}/following")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["users"]) == 1
    assert data["users"][0]["id"] == user2_id


@pytest.mark.asyncio
async def test_block_user(test_client: AsyncClient, register_user_data):
    """Test blocking a user"""
    # Register two users
    response1 = await test_client.post("/api/auth/register", json=register_user_data)
    user1_id = response1.json()["user"]["id"]
    token1 = response1.json()["access_token"]

    register_user_data["email"] = "user2@example.com"
    register_user_data["username"] = "user2"
    response2 = await test_client.post("/api/auth/register", json=register_user_data)
    user2_id = response2.json()["user"]["id"]

    # User 1 blocks User 2
    response = await test_client.post(
        f"/api/profiles/{user2_id}/block",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_blocked"] is True
    assert "blocked" in data["message"].lower()

    # User 1 unblocks User 2
    response = await test_client.post(
        f"/api/profiles/{user2_id}/block",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_blocked"] is False
    assert "unblocked" in data["message"].lower()


@pytest.mark.asyncio
async def test_cannot_block_self(test_client: AsyncClient, register_user_data):
    """Test that user cannot block themselves"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    user_id = response.json()["user"]["id"]
    token = response.json()["access_token"]

    response = await test_client.post(
        f"/api/profiles/{user_id}/block",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "cannot block yourself" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_blocked_users(test_client: AsyncClient, register_user_data):
    """Test getting blocked users list"""
    # Register two users
    response1 = await test_client.post("/api/auth/register", json=register_user_data)
    token1 = response1.json()["access_token"]

    register_user_data["email"] = "user2@example.com"
    register_user_data["username"] = "user2"
    response2 = await test_client.post("/api/auth/register", json=register_user_data)
    user2_id = response2.json()["user"]["id"]

    # User 1 blocks User 2
    await test_client.post(
        f"/api/profiles/{user2_id}/block",
        headers={"Authorization": f"Bearer {token1}"}
    )

    # Get blocked users for User 1
    response = await test_client.get(
        "/api/profiles/me/blocked",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["users"]) == 1
    assert data["users"][0]["id"] == user2_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
