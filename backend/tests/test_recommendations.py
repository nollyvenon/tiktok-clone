"""
Recommendation engine API tests
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4, UUID

from app.models import Recommendation, User, Video, VideoStatus


async def _create_recommendation(test_client, test_db, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    access_token = response.json()["access_token"]
    user_id = UUID(response.json()["user"]["id"])

    creator = User(email=f"creator_{username}@example.com", username=f"creator{username}", password_hash="x", is_active=True)
    test_db.add(creator)
    await test_db.commit()

    video = Video(
        user_id=creator.id,
        title="Recommended",
        video_url="https://example.com/rec.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    rec = Recommendation(user_id=user_id, video_id=video.id, score=0.9, algorithm="collaborative")
    test_db.add(rec)
    await test_db.commit()
    await test_db.refresh(rec)

    return access_token, rec.id


@pytest.mark.asyncio
async def test_get_for_you_feed(test_client: AsyncClient, register_user_data):
    """Test getting For-You personalized feed"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get for-you feed
    response = await test_client.get(
        "/api/recommendations/for-you?limit=10",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "recommendations" in data
    assert "cursor" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_for_you_feed_with_cursor(test_client: AsyncClient, register_user_data):
    """Test pagination with cursor"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get first page
    response = await test_client.get(
        "/api/recommendations/for-you?limit=5",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()
    first_cursor = data.get("cursor")

    # Get next page if cursor exists
    if first_cursor:
        response = await test_client.get(
            f"/api/recommendations/for-you?limit=5&cursor={first_cursor}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_compute_recommendations(test_client: AsyncClient, register_user_data):
    """Test computing fresh recommendations"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Compute recommendations
    response = await test_client.post(
        "/api/recommendations/compute?limit=50",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 202
    data = response.json()

    assert data["status"] == "computed"
    assert "count" in data


@pytest.mark.asyncio
async def test_get_similar_videos(test_client: AsyncClient, register_user_data):
    """Test getting similar videos"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create a video first (would need actual video creation)
    video_id = uuid4()

    # Get similar videos
    response = await test_client.get(
        f"/api/recommendations/similar/{video_id}?limit=10",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code in [200, 404]  # Depending on video existence


@pytest.mark.asyncio
async def test_get_user_preferences(test_client: AsyncClient, register_user_data):
    """Test getting user preferences"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get preferences
    response = await test_client.get(
        "/api/recommendations/preferences",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "content_diversity_score" in data
    assert "recency_preference" in data


@pytest.mark.asyncio
async def test_update_user_preferences(test_client: AsyncClient, register_user_data):
    """Test updating user preferences"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Update preferences
    response = await test_client.put(
        "/api/recommendations/preferences",
        json={
            "preferred_hashtags": ["music", "dance", "comedy"],
            "preferred_genres": ["pop", "hip-hop"],
            "content_diversity_score": 0.7,
            "recency_preference": 0.6,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["content_diversity_score"] == 0.7
    assert data["recency_preference"] == 0.6


@pytest.mark.asyncio
async def test_update_preferences_with_creators(test_client: AsyncClient, register_user_data):
    """Test updating preferences with preferred creators"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    creator_id_1 = uuid4()
    creator_id_2 = uuid4()

    response = await test_client.put(
        "/api/recommendations/preferences",
        json={
            "preferred_creators": [str(creator_id_1), str(creator_id_2)],
            "content_diversity_score": 0.5,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_record_feedback_relevant(test_client: AsyncClient, test_db, register_user_data):
    """Test recording relevant recommendation feedback"""
    access_token, recommendation_id = await _create_recommendation(
        test_client, test_db, register_user_data, "fbrelevant@example.com", "fbrelevantuser"
    )

    response = await test_client.post(
        f"/api/recommendations/{recommendation_id}/feedback",
        json={
            "feedback_type": "relevant",
            "rating": 5,
            "reason": "Great video recommendation",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "recorded"


@pytest.mark.asyncio
async def test_record_feedback_irrelevant(test_client: AsyncClient, test_db, register_user_data):
    """Test recording irrelevant feedback"""
    access_token, recommendation_id = await _create_recommendation(
        test_client, test_db, register_user_data, "fbirrelevant@example.com", "fbirrelevantuser"
    )

    response = await test_client.post(
        f"/api/recommendations/{recommendation_id}/feedback",
        json={
            "feedback_type": "irrelevant",
            "reason": "Not interested in this content",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_record_feedback_not_interested(test_client: AsyncClient, test_db, register_user_data):
    """Test recording not interested feedback"""
    access_token, recommendation_id = await _create_recommendation(
        test_client, test_db, register_user_data, "fbnotinterested@example.com", "fbnotinteresteduser"
    )

    response = await test_client.post(
        f"/api/recommendations/{recommendation_id}/feedback",
        json={
            "feedback_type": "not_interested",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_record_feedback_duplicate(test_client: AsyncClient, test_db, register_user_data):
    """Test recording duplicate video feedback"""
    access_token, recommendation_id = await _create_recommendation(
        test_client, test_db, register_user_data, "fbduplicate@example.com", "fbduplicateuser"
    )

    response = await test_client.post(
        f"/api/recommendations/{recommendation_id}/feedback",
        json={
            "feedback_type": "duplicate",
            "reason": "Already saw similar video",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_record_feedback_nsfw(test_client: AsyncClient, test_db, register_user_data):
    """Test recording NSFW content feedback"""
    access_token, recommendation_id = await _create_recommendation(
        test_client, test_db, register_user_data, "fbnsfw@example.com", "fbnsfwuser"
    )

    response = await test_client.post(
        f"/api/recommendations/{recommendation_id}/feedback",
        json={
            "feedback_type": "nsfw",
            "reason": "Inappropriate content",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_record_feedback_nonexistent_recommendation_404(test_client: AsyncClient, register_user_data):
    """Regression test: feedback on a recommendation_id that doesn't exist
    (fabricated, or for a recommendation that's since been pruned) must
    404 cleanly, not 500 from a raw ForeignKeyViolation. Previously this
    passed silently in tests because SQLite doesn't enforce FK constraints
    by default - it always would have 500'd against real Postgres."""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    response = await test_client.post(
        f"/api/recommendations/{uuid4()}/feedback",
        json={"feedback_type": "relevant"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_recommendation_stats(test_client: AsyncClient, register_user_data):
    """Test getting recommendation statistics"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    response = await test_client.get(
        "/api/recommendations/stats",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "total_recommendations" in data
    assert "click_through_rate" in data
    assert "watch_rate" in data
    assert "like_rate" in data


@pytest.mark.asyncio
async def test_get_active_ab_tests(test_client: AsyncClient, register_user_data):
    """Test getting active A/B tests"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    response = await test_client.get(
        "/api/recommendations/ab-tests/active",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "tests" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_algorithm_info(test_client: AsyncClient, register_user_data):
    """Test getting algorithm information"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    response = await test_client.get(
        "/api/recommendations/algorithm/info",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["algorithm"] == "ensemble"
    assert "components" in data
    assert "collaborative_filtering" in data["components"]
    assert "content_based" in data["components"]
    assert "social_graph" in data["components"]
    assert "trending" in data["components"]


@pytest.mark.asyncio
async def test_for_you_feed_limit_validation(test_client: AsyncClient, register_user_data):
    """Test limit parameter validation"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Test with max limit
    response = await test_client.get(
        "/api/recommendations/for-you?limit=100",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

    # Test with invalid limit (should fail validation)
    response = await test_client.get(
        "/api/recommendations/for-you?limit=200",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_preferences_diversity_score_validation(test_client: AsyncClient, register_user_data):
    """Test diversity score must be between 0 and 1"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Valid score
    response = await test_client.put(
        "/api/recommendations/preferences",
        json={"content_diversity_score": 0.75},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

    # Invalid score (> 1)
    response = await test_client.put(
        "/api/recommendations/preferences",
        json={"content_diversity_score": 1.5},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unauthorized_access(test_client: AsyncClient):
    """Test unauthorized access to recommendations"""
    # Try to access without token
    response = await test_client.get("/api/recommendations/for-you")
    assert response.status_code == 403 or response.status_code == 401


@pytest.mark.asyncio
async def test_get_preferences_returns_defaults(test_client: AsyncClient, register_user_data):
    """Test that getting preferences returns defaults for new user"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    response = await test_client.get(
        "/api/recommendations/preferences",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Should have default values
    assert data["content_diversity_score"] == 0.5
    assert data["recency_preference"] == 0.5


@pytest.mark.asyncio
async def test_for_you_feed_with_real_recommendation_returns_video(
    test_client: AsyncClient, test_db, register_user_data
):
    """
    A For-You feed with an actual Recommendation row must serialize the
    nested video with its author - Recommendation only has a video_id FK,
    no `video` relationship, so a naive from_orm() would 500 here. No prior
    test ever populated a real Recommendation row, so this path was never
    exercised.
    """
    from app.models import Recommendation, User, Video, VideoStatus

    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]
    me_response = await test_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    user_id = UUID(me_response.json()["id"])

    creator = User(email="rec_creator@example.com", username="reccreator", password_hash="x", is_active=True)
    test_db.add(creator)
    await test_db.commit()

    video = Video(
        user_id=creator.id,
        title="Recommended Video",
        video_url="https://example.com/rec.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    rec = Recommendation(
        user_id=user_id,
        video_id=video.id,
        score=0.9,
        algorithm="collaborative",
    )
    test_db.add(rec)
    await test_db.commit()

    response = await test_client.get(
        "/api/recommendations/for-you?limit=10",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["recommendations"][0]["video"]["title"] == "Recommended Video"
    assert data["recommendations"][0]["video"]["user"]["username"] == "reccreator"
    assert data["recommendations"][0]["score"] == 0.9


@pytest.mark.asyncio
async def test_similar_videos_route(test_client: AsyncClient, test_db, register_user_data):
    """
    /similar/{video_id} returns plain Video matches (not scored Recommendation
    records) - must come back as a FeedResponse with a real author, not the
    old {"video": v}-only dict that was missing every other required field.
    """
    from app.models import User, Video, VideoStatus

    register_response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = register_response.json()["access_token"]

    creator = User(email="similar_creator@example.com", username="similarcreator", password_hash="x", is_active=True)
    test_db.add(creator)
    await test_db.commit()

    source_video = Video(
        user_id=creator.id,
        title="Source Video",
        hashtags="dance,fun",
        video_url="https://example.com/source.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    similar_video = Video(
        user_id=creator.id,
        title="Similar Video",
        hashtags="dance,fun",
        video_url="https://example.com/similar.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(source_video)
    test_db.add(similar_video)
    await test_db.commit()
    source_id = source_video.id

    response = await test_client.get(
        f"/api/recommendations/similar/{source_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert any(v["title"] == "Similar Video" for v in data["videos"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
