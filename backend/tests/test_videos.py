"""
Video API tests
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_video(test_client: AsyncClient, register_user_data):
    """Test creating a video"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    assert response.status_code == 201
    access_token = response.json()["access_token"]

    # Create video
    video_data = {
        "title": "My First Video",
        "description": "This is my first video",
        "video_url": "https://example.com/video.mp4",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "duration": 15,
        "is_public": True,
    }
    response = await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    video = response.json()

    assert video["title"] == "My First Video"
    assert video["description"] == "This is my first video"
    assert video["video_url"] == "https://example.com/video.mp4"
    assert video["duration"] == 15
    assert video["views_count"] == 0
    assert video["likes_count"] == 0


@pytest.mark.asyncio
async def test_create_video_unauthorized(test_client: AsyncClient):
    """Test creating video without authentication"""
    video_data = {
        "title": "My Video",
        "video_url": "https://example.com/video.mp4",
    }
    response = await test_client.post("/api/videos", json=video_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_video(test_client: AsyncClient, register_user_data):
    """Test getting a video"""
    # Create video
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {
        "title": "Test Video",
        "video_url": "https://example.com/video.mp4",
    }
    response = await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    video_id = response.json()["id"]

    # Get video
    response = await test_client.get(f"/api/videos/{video_id}")
    assert response.status_code == 200
    video = response.json()

    assert video["id"] == video_id
    assert video["title"] == "Test Video"
    assert "user" in video


@pytest.mark.asyncio
async def test_get_feed(test_client: AsyncClient, register_user_data):
    """Test getting video feed"""
    # Create videos
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    for i in range(3):
        video_data = {
            "title": f"Video {i}",
            "video_url": f"https://example.com/video{i}.mp4",
        }
        await test_client.post(
            "/api/videos",
            json=video_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # Get feed
    response = await test_client.get("/api/videos/feed")
    assert response.status_code == 200
    feed = response.json()

    assert "videos" in feed
    assert len(feed["videos"]) > 0


@pytest.mark.asyncio
async def test_like_video(test_client: AsyncClient, register_user_data):
    """Test liking a video"""
    # Create video
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {
        "title": "Test Video",
        "video_url": "https://example.com/video.mp4",
    }
    response = await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    video_id = response.json()["id"]

    # Like video
    response = await test_client.post(
        f"/api/videos/{video_id}/like",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_liked"] is True
    assert data["likes_count"] == 1

    # Unlike video
    response = await test_client.post(
        f"/api/videos/{video_id}/like",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_liked"] is False
    assert data["likes_count"] == 0


@pytest.mark.asyncio
async def test_bookmark_video(test_client: AsyncClient, register_user_data):
    """Test bookmarking a video"""
    # Create video
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {
        "title": "Test Video",
        "video_url": "https://example.com/video.mp4",
    }
    response = await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    video_id = response.json()["id"]

    # Bookmark video
    response = await test_client.post(
        f"/api/videos/{video_id}/bookmark",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_bookmarked"] is True
    assert data["bookmarks_count"] == 1

    # Unbookmark video
    response = await test_client.post(
        f"/api/videos/{video_id}/bookmark",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_bookmarked"] is False
    assert data["bookmarks_count"] == 0


@pytest.mark.asyncio
async def test_track_view(test_client: AsyncClient, register_user_data):
    """Test tracking video view"""
    # Create video
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {
        "title": "Test Video",
        "video_url": "https://example.com/video.mp4",
        "duration": 10,
    }
    response = await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    video_id = response.json()["id"]

    # Track view
    response = await test_client.post(
        f"/api/videos/{video_id}/view",
        json={
            "watch_time": 8,
            "completed": False,
            "device_type": "mobile",
            "platform": "iOS",
        }
    )
    assert response.status_code == 200

    # Check view count increased
    response = await test_client.get(f"/api/videos/{video_id}")
    assert response.status_code == 200
    video = response.json()
    assert video["views_count"] == 1


@pytest.mark.asyncio
async def test_update_video(test_client: AsyncClient, register_user_data):
    """Test updating a video"""
    # Create video
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {
        "title": "Original Title",
        "description": "Original description",
        "video_url": "https://example.com/video.mp4",
    }
    response = await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    video_id = response.json()["id"]

    # Update video
    update_data = {
        "title": "Updated Title",
        "description": "Updated description",
    }
    response = await test_client.put(
        f"/api/videos/{video_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    video = response.json()

    assert video["title"] == "Updated Title"
    assert video["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_video(test_client: AsyncClient, register_user_data):
    """Test deleting a video"""
    # Create video
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {
        "title": "Test Video",
        "video_url": "https://example.com/video.mp4",
    }
    response = await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    video_id = response.json()["id"]

    # Delete video
    response = await test_client.delete(
        f"/api/videos/{video_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 204

    # Try to get deleted video
    response = await test_client.get(f"/api/videos/{video_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_trending_videos(test_client: AsyncClient, register_user_data):
    """Test getting trending videos"""
    response = await test_client.get("/api/videos/search/trending")
    assert response.status_code == 200
    feed = response.json()

    assert "videos" in feed
    assert "total" in feed


@pytest.mark.asyncio
async def test_search_videos(test_client: AsyncClient, register_user_data):
    """Test searching videos"""
    # Create a video with specific title
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {
        "title": "Python Tutorial",
        "description": "Learn Python programming",
        "video_url": "https://example.com/video.mp4",
    }
    await test_client.post(
        "/api/videos",
        json=video_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Search for video
    response = await test_client.get("/api/videos/search?q=Python")
    assert response.status_code == 200
    results = response.json()

    assert "videos" in results
    assert len(results["videos"]) > 0


@pytest.mark.asyncio
async def test_get_user_videos(test_client: AsyncClient, register_user_data):
    """Test getting user's videos"""
    # Create user and videos
    response = await test_client.post("/api/auth/register", json=register_user_data)
    user_id = response.json()["user"]["id"]
    access_token = response.json()["access_token"]

    for i in range(2):
        video_data = {
            "title": f"Video {i}",
            "video_url": f"https://example.com/video{i}.mp4",
        }
        await test_client.post(
            "/api/videos",
            json=video_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # Get user videos
    response = await test_client.get(f"/api/videos/user/{user_id}/videos")
    assert response.status_code == 200
    feed = response.json()

    assert "videos" in feed
    assert len(feed["videos"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
