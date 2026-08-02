"""
HTTP-level tests for search routes (Module 8).

test_search.py only exercises SearchService directly, never through
test_client. All /api/search/* routes require authentication (they all
depend on get_current_user) - that requirement is itself only visible at
the HTTP layer, so it's worth covering here too.
"""

import pytest
from httpx import AsyncClient

from app.models import User, Video, VideoStatus


@pytest.mark.asyncio
async def test_search_videos_route_requires_auth(test_client: AsyncClient):
    response = await test_client.get("/api/search/videos", params={"q": "dance"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_videos_route(test_client: AsyncClient, test_db, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token = register_response.json()["access_token"]

    user = User(email="creator@example.com", username="creator1", password_hash="x", is_active=True)
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="Dance Tutorial",
        video_url="https://example.com/v.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    response = await test_client.get(
        "/api/search/videos",
        params={"q": "dance"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(v["title"] == "Dance Tutorial" for v in data["results"])


@pytest.mark.asyncio
async def test_search_creators_route(test_client: AsyncClient, test_db, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token = register_response.json()["access_token"]

    user = User(email="dancer@example.com", username="dancerpro", password_hash="x", is_active=True)
    test_db.add(user)
    await test_db.commit()

    response = await test_client.get(
        "/api/search/creators",
        params={"q": "dancer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert any(c["username"] == "dancerpro" for c in response.json()["results"])


@pytest.mark.asyncio
async def test_discover_by_category_route(test_client: AsyncClient, test_db, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token = register_response.json()["access_token"]

    user = User(email="cat@example.com", username="catuser", password_hash="x", is_active=True)
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="Dance Moves",
        hashtags="#dance, #music",
        video_url="https://example.com/v.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    response = await test_client.get(
        "/api/search/discover/dance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["category"] == "dance"


@pytest.mark.asyncio
async def test_search_suggestions_route(test_client: AsyncClient, test_db, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token = register_response.json()["access_token"]

    response = await test_client.get(
        "/api/search/suggestions",
        params={"q": "da"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
