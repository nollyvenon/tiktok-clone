"""
Recommendation engine API tests
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


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
async def test_record_feedback_relevant(test_client: AsyncClient, register_user_data):
    """Test recording relevant recommendation feedback"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    recommendation_id = uuid4()

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
async def test_record_feedback_irrelevant(test_client: AsyncClient, register_user_data):
    """Test recording irrelevant feedback"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    recommendation_id = uuid4()

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
async def test_record_feedback_not_interested(test_client: AsyncClient, register_user_data):
    """Test recording not interested feedback"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    recommendation_id = uuid4()

    response = await test_client.post(
        f"/api/recommendations/{recommendation_id}/feedback",
        json={
            "feedback_type": "not_interested",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_record_feedback_duplicate(test_client: AsyncClient, register_user_data):
    """Test recording duplicate video feedback"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    recommendation_id = uuid4()

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
async def test_record_feedback_nsfw(test_client: AsyncClient, register_user_data):
    """Test recording NSFW content feedback"""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    recommendation_id = uuid4()

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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
