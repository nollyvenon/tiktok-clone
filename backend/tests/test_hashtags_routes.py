"""
HTTP-level tests for hashtag routes (Module 9).

Module 9's existing test_hashtags.py only exercises HashtagService directly,
never through test_client - which is why the route registration bug (the
router's own prefix already included /api/hashtags, and main.py added
another /api on top, doubling to /api/api/hashtags/...) went undetected.
These tests hit the actual HTTP paths to catch that class of bug.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.models import HashtagTrend, Challenge, User, Video, VideoStatus


@pytest.mark.asyncio
async def test_get_trending_hashtags_route(test_client: AsyncClient, test_db):
    trend = HashtagTrend(hashtag="dance", region="US", usage_count=500, rank_position=1)
    test_db.add(trend)
    await test_db.commit()

    response = await test_client.get("/api/hashtags/trending", params={"region": "US"})
    assert response.status_code == 200
    assert any(t["hashtag"] == "dance" for t in response.json())


@pytest.mark.asyncio
async def test_get_hashtag_stats_route(test_client: AsyncClient, test_db):
    trend = HashtagTrend(hashtag="music", region="US", usage_count=100)
    test_db.add(trend)
    await test_db.commit()

    response = await test_client.get("/api/hashtags/music/stats", params={"region": "US"})
    assert response.status_code == 200
    assert response.json()["hashtag"] == "music"


@pytest.mark.asyncio
async def test_search_hashtags_route(test_client: AsyncClient, test_db):
    trend = HashtagTrend(hashtag="dancetrend", region="US", usage_count=200)
    test_db.add(trend)
    await test_db.commit()

    response = await test_client.get("/api/hashtags/search", params={"q": "dance", "region": "US"})
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_get_active_challenges_route(test_client: AsyncClient, test_db):
    now = datetime.utcnow()
    challenge = Challenge(
        hashtag="dance",
        title="Dance Challenge",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=6),
        is_active=True,
    )
    test_db.add(challenge)
    await test_db.commit()

    response = await test_client.get("/api/hashtags/challenges/active", params={"region": "US"})
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_challenges_active_not_shadowed_by_challenge_id_route(test_client: AsyncClient, test_db):
    """
    '/challenges/active' must resolve to the active-challenges list endpoint,
    not be swallowed by '/challenges/{challenge_id}' trying (and failing) to
    parse 'active' as a UUID.
    """
    response = await test_client.get("/api/hashtags/challenges/active", params={"region": "US"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_track_hashtag_usage_route(test_client: AsyncClient, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token = register_response.json()["access_token"]

    response = await test_client.post(
        "/api/hashtags/%23trending/track",
        params={"region": "US"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_track_hashtag_usage_requires_auth(test_client: AsyncClient):
    response = await test_client.post("/api/hashtags/%23trending/track", params={"region": "US"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_challenge_route(test_client: AsyncClient, register_user_data):
    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    token = register_response.json()["access_token"]

    start = datetime.utcnow().isoformat()
    end = (datetime.utcnow() + timedelta(days=7)).isoformat()

    response = await test_client.post(
        "/api/hashtags/challenges",
        params={
            "hashtag": "dance",
            "title": "Dance Challenge",
            "start_date": start,
            "end_date": end,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["hashtag"] == "dance"


@pytest.mark.asyncio
async def test_get_challenge_videos_route_includes_author(test_client: AsyncClient, test_db):
    """
    The challenge-videos response must be a real VideoDetailResponse with a
    nested author, not a raw ORM dump missing `user` - clients (web/mobile)
    render video.user.username directly.
    """
    user = User(email="challenger@example.com", username="challenger1", password_hash="x", is_active=True)
    test_db.add(user)
    await test_db.commit()

    challenge = Challenge(
        hashtag="dance",
        title="Dance Challenge",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
    )
    test_db.add(challenge)

    video = Video(
        user_id=user.id,
        title="My Entry",
        hashtags="dance",
        video_url="https://example.com/v.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    response = await test_client.get(f"/api/hashtags/challenges/{challenge.id}/videos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["videos"][0]["user"]["username"] == "challenger1"
