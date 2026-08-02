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
async def test_get_video_reflects_own_like_and_bookmark_when_authenticated(
    test_client: AsyncClient, register_user_data
):
    """GET /videos/{id} must recognize the requesting user via the
    Authorization header and reflect their real is_liked/is_bookmarked
    state - not silently treat every request as anonymous."""
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    video_data = {"title": "Auth check video", "video_url": "https://example.com/authcheck.mp4"}
    create_response = await test_client.post(
        "/api/videos", json=video_data, headers={"Authorization": f"Bearer {access_token}"}
    )
    video_id = create_response.json()["id"]

    await test_client.post(
        f"/api/videos/{video_id}/like", headers={"Authorization": f"Bearer {access_token}"}
    )
    await test_client.post(
        f"/api/videos/{video_id}/bookmark", headers={"Authorization": f"Bearer {access_token}"}
    )

    response = await test_client.get(
        f"/api/videos/{video_id}", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    video = response.json()
    assert video["is_liked"] is True
    assert video["is_bookmarked"] is True

    # Anonymous request must not see any liked/bookmarked state
    anon_response = await test_client.get(f"/api/videos/{video_id}")
    anon_video = anon_response.json()
    assert anon_video["is_liked"] is False
    assert anon_video["is_bookmarked"] is False


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


async def _register_and_login(test_client, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


@pytest.mark.asyncio
async def test_following_feed_only_shows_followed_creators(test_client: AsyncClient, register_user_data):
    """feed_type=following must actually filter to videos from creators the
    requesting user follows - this silently degraded to the same as
    for_you for every user until the optional-auth dependency bug (current
    user never recognized) was fixed."""
    viewer_token, viewer_id = await _register_and_login(
        test_client, register_user_data, "feedviewer@example.com", "feedvieweruser"
    )
    followed_token, followed_id = await _register_and_login(
        test_client, register_user_data, "feedfollowed@example.com", "feedfolloweduser"
    )
    stranger_token, stranger_id = await _register_and_login(
        test_client, register_user_data, "feedstranger@example.com", "feedstrangeruser"
    )

    await test_client.post(
        f"/api/profiles/{followed_id}/follow", headers={"Authorization": f"Bearer {viewer_token}"}
    )

    followed_video = await test_client.post(
        "/api/videos",
        json={"title": "From followed creator", "video_url": "https://example.com/followed.mp4"},
        headers={"Authorization": f"Bearer {followed_token}"},
    )
    await test_client.post(
        "/api/videos",
        json={"title": "From a stranger", "video_url": "https://example.com/stranger.mp4"},
        headers={"Authorization": f"Bearer {stranger_token}"},
    )

    response = await test_client.get(
        "/api/videos/feed",
        params={"feed_type": "following"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 200
    video_ids = [v["id"] for v in response.json()["videos"]]
    assert followed_video.json()["id"] in video_ids
    assert all(v["user"]["id"] == followed_id for v in response.json()["videos"])


@pytest.mark.asyncio
async def test_feed_reflects_like_state_when_authenticated(test_client: AsyncClient, register_user_data):
    access_token, _ = await _register_and_login(
        test_client, register_user_data, "feedlike@example.com", "feedlikeuser"
    )
    create_response = await test_client.post(
        "/api/videos",
        json={"title": "Feed like check", "video_url": "https://example.com/feedlike.mp4"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    video_id = create_response.json()["id"]
    await test_client.post(
        f"/api/videos/{video_id}/like", headers={"Authorization": f"Bearer {access_token}"}
    )

    response = await test_client.get(
        "/api/videos/feed", headers={"Authorization": f"Bearer {access_token}"}
    )
    video = next(v for v in response.json()["videos"] if v["id"] == video_id)
    assert video["is_liked"] is True


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
async def test_get_creator_dashboard(test_client: AsyncClient, register_user_data):
    creator_token, creator_id = await _register_and_login(
        test_client, register_user_data, "dashboardcreator@example.com", "dashboardcreatoruser"
    )
    viewer_token, _ = await _register_and_login(
        test_client, register_user_data, "dashboardviewer@example.com", "dashboardvieweruser"
    )
    await test_client.post(
        f"/api/profiles/{creator_id}/follow", headers={"Authorization": f"Bearer {viewer_token}"}
    )

    video_a = await test_client.post(
        "/api/videos",
        json={"title": "Popular video", "video_url": "https://example.com/popular.mp4"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    video_b = await test_client.post(
        "/api/videos",
        json={"title": "Less popular", "video_url": "https://example.com/lesspopular.mp4"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )

    await test_client.post(
        f"/api/videos/{video_a.json()['id']}/like", headers={"Authorization": f"Bearer {viewer_token}"}
    )
    await test_client.post(
        f"/api/videos/{video_a.json()['id']}/view",
        json={"watch_time": 10, "completed": True},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    await test_client.post(
        f"/api/videos/{video_a.json()['id']}/view",
        json={"watch_time": 10, "completed": True},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    await test_client.post(
        f"/api/videos/{video_b.json()['id']}/view",
        json={"watch_time": 5, "completed": False},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    response = await test_client.get(
        "/api/videos/dashboard", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["video_count"] == 2
    assert data["total_views"] == 3
    assert data["total_likes"] == 1
    assert data["followers_count"] == 1
    assert data["top_videos"][0]["video_id"] == video_a.json()["id"]
    assert data["top_videos"][0]["views"] == 2


@pytest.mark.asyncio
async def test_creator_dashboard_requires_auth(test_client: AsyncClient):
    response = await test_client.get("/api/videos/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_creator_dashboard_empty_for_new_user(test_client: AsyncClient, register_user_data):
    token, _ = await _register_and_login(
        test_client, register_user_data, "emptydashboard@example.com", "emptydashboarduser"
    )
    response = await test_client.get("/api/videos/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["video_count"] == 0
    assert data["total_views"] == 0
    assert data["average_engagement_rate"] == 0
    assert data["top_videos"] == []


@pytest.mark.asyncio
async def test_anonymous_view_tracking_does_not_violate_foreign_key(
    test_client: AsyncClient, register_user_data
):
    """Regression test: track_view previously inserted a fabricated
    all-zero UUID for anonymous views, referencing a user row that never
    existed - silently fine under SQLite without FK enforcement, but a
    guaranteed ForeignKeyViolation against real Postgres. The test
    fixture now enables SQLite FK enforcement specifically to catch this
    class of bug."""
    token, _ = await _register_and_login(
        test_client, register_user_data, "anonview@example.com", "anonviewuser"
    )
    create_response = await test_client.post(
        "/api/videos",
        json={"title": "Anon view test", "video_url": "https://example.com/anonview.mp4"},
        headers={"Authorization": f"Bearer {token}"},
    )
    video_id = create_response.json()["id"]

    response = await test_client.post(
        f"/api/videos/{video_id}/view",
        json={"watch_time": 5, "completed": False},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_bookmarked_videos(test_client: AsyncClient, register_user_data):
    access_token, _ = await _register_and_login(
        test_client, register_user_data, "bookmarklist1@example.com", "bookmarklist1user"
    )

    saved_response = await test_client.post(
        "/api/videos",
        json={"title": "Saved video", "video_url": "https://example.com/saved.mp4"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    saved_id = saved_response.json()["id"]

    unsaved_response = await test_client.post(
        "/api/videos",
        json={"title": "Not saved", "video_url": "https://example.com/notsaved.mp4"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    unsaved_id = unsaved_response.json()["id"]

    await test_client.post(
        f"/api/videos/{saved_id}/bookmark", headers={"Authorization": f"Bearer {access_token}"}
    )

    response = await test_client.get(
        "/api/videos/bookmarks", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    video_ids = [v["id"] for v in data["videos"]]
    assert saved_id in video_ids
    assert unsaved_id not in video_ids
    assert all(v["is_bookmarked"] is True for v in data["videos"])


@pytest.mark.asyncio
async def test_get_bookmarked_videos_requires_auth(test_client: AsyncClient):
    response = await test_client.get("/api/videos/bookmarks")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unbookmarked_video_disappears_from_bookmarks_list(
    test_client: AsyncClient, register_user_data
):
    access_token, _ = await _register_and_login(
        test_client, register_user_data, "bookmarklist2@example.com", "bookmarklist2user"
    )

    create_response = await test_client.post(
        "/api/videos",
        json={"title": "Toggle test", "video_url": "https://example.com/toggle.mp4"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    video_id = create_response.json()["id"]

    await test_client.post(
        f"/api/videos/{video_id}/bookmark", headers={"Authorization": f"Bearer {access_token}"}
    )
    await test_client.post(
        f"/api/videos/{video_id}/bookmark", headers={"Authorization": f"Bearer {access_token}"}
    )

    response = await test_client.get(
        "/api/videos/bookmarks", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert video_id not in [v["id"] for v in response.json()["videos"]]


@pytest.mark.asyncio
async def test_search_reflects_like_and_bookmark_state_when_authenticated(
    test_client: AsyncClient, register_user_data
):
    """Search results must reflect the requesting user's real is_liked/
    is_bookmarked state, not the hardcoded False that was always returned
    regardless of auth."""
    access_token, _ = await _register_and_login(
        test_client, register_user_data, "searchflags@example.com", "searchflagsuser"
    )

    create_response = await test_client.post(
        "/api/videos",
        json={"title": "Searchable unique flagcheck", "video_url": "https://example.com/searchflag.mp4"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    video_id = create_response.json()["id"]
    await test_client.post(
        f"/api/videos/{video_id}/like", headers={"Authorization": f"Bearer {access_token}"}
    )
    await test_client.post(
        f"/api/videos/{video_id}/bookmark", headers={"Authorization": f"Bearer {access_token}"}
    )

    response = await test_client.get(
        "/api/videos/search",
        params={"q": "flagcheck"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    video = next(v for v in response.json()["videos"] if v["id"] == video_id)
    assert video["is_liked"] is True
    assert video["is_bookmarked"] is True


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


@pytest.mark.asyncio
async def test_create_duet(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register_and_login(
        test_client, register_user_data, "duetorig@example.com", "duetoriguser"
    )
    duetist_token, _ = await _register_and_login(
        test_client, register_user_data, "duetist@example.com", "duetistuser"
    )

    original = await test_client.post(
        "/api/videos",
        json={"title": "Original", "video_url": "https://example.com/original.mp4"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_id = original.json()["id"]

    duet = await test_client.post(
        "/api/videos",
        json={
            "title": "My duet",
            "video_url": "https://example.com/duet.mp4",
            "original_video_id": original_id,
            "remix_type": "duet",
        },
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    assert duet.status_code == 201

    detail = await test_client.get(f"/api/videos/{duet.json()['id']}")
    data = detail.json()
    assert data["remix_type"] == "duet"
    assert data["original_video"]["id"] == original_id
    assert data["original_video"]["user"]["username"] == "duetoriguser"


@pytest.mark.asyncio
async def test_create_stitch(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register_and_login(
        test_client, register_user_data, "stitchorig@example.com", "stitchoriguser"
    )
    stitcher_token, _ = await _register_and_login(
        test_client, register_user_data, "stitcher@example.com", "stitcheruser"
    )

    original = await test_client.post(
        "/api/videos",
        json={"title": "Original", "video_url": "https://example.com/original2.mp4"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_id = original.json()["id"]

    stitch = await test_client.post(
        "/api/videos",
        json={
            "title": "My stitch",
            "video_url": "https://example.com/stitch.mp4",
            "original_video_id": original_id,
            "remix_type": "stitch",
        },
        headers={"Authorization": f"Bearer {stitcher_token}"},
    )
    assert stitch.status_code == 201
    assert stitch.json()["id"] != original_id


@pytest.mark.asyncio
async def test_duet_disabled_rejected(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register_and_login(
        test_client, register_user_data, "nodueorig@example.com", "noduteoriguser"
    )
    duetist_token, _ = await _register_and_login(
        test_client, register_user_data, "noduet@example.com", "noduetuser"
    )

    original = await test_client.post(
        "/api/videos",
        json={
            "title": "No duets allowed",
            "video_url": "https://example.com/noduet.mp4",
            "allow_duets": False,
        },
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_id = original.json()["id"]

    response = await test_client.post(
        "/api/videos",
        json={
            "title": "Attempted duet",
            "video_url": "https://example.com/attempted.mp4",
            "original_video_id": original_id,
            "remix_type": "duet",
        },
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_stitch_disabled_rejected(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register_and_login(
        test_client, register_user_data, "nostitchorig@example.com", "nostitchoriguser"
    )
    stitcher_token, _ = await _register_and_login(
        test_client, register_user_data, "nostitch@example.com", "nostitchuser"
    )

    original = await test_client.post(
        "/api/videos",
        json={
            "title": "No stitches allowed",
            "video_url": "https://example.com/nostitch.mp4",
            "allow_stitches": False,
        },
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_id = original.json()["id"]

    response = await test_client.post(
        "/api/videos",
        json={
            "title": "Attempted stitch",
            "video_url": "https://example.com/attemptedstitch.mp4",
            "original_video_id": original_id,
            "remix_type": "stitch",
        },
        headers={"Authorization": f"Bearer {stitcher_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_remix_type_required_with_original_video_id(test_client: AsyncClient, register_user_data):
    token, _ = await _register_and_login(
        test_client, register_user_data, "mismatch@example.com", "mismatchuser"
    )
    original = await test_client.post(
        "/api/videos",
        json={"title": "Original", "video_url": "https://example.com/mismatchorig.mp4"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await test_client.post(
        "/api/videos",
        json={
            "title": "Missing remix_type",
            "video_url": "https://example.com/missing.mp4",
            "original_video_id": original.json()["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_blocked_user_cannot_duet(test_client: AsyncClient, register_user_data):
    creator_token, creator_id = await _register_and_login(
        test_client, register_user_data, "blockduetorig@example.com", "blockduetoriguser"
    )
    duetist_token, duetist_id = await _register_and_login(
        test_client, register_user_data, "blockduetist@example.com", "blockduetistuser"
    )

    original = await test_client.post(
        "/api/videos",
        json={"title": "Original", "video_url": "https://example.com/blockorig.mp4"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_id = original.json()["id"]

    await test_client.post(
        f"/api/profiles/{duetist_id}/block", headers={"Authorization": f"Bearer {creator_token}"}
    )

    response = await test_client.post(
        "/api/videos",
        json={
            "title": "Blocked duet attempt",
            "video_url": "https://example.com/blockedduet.mp4",
            "original_video_id": original_id,
            "remix_type": "duet",
        },
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_remixes_of_a_video(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register_and_login(
        test_client, register_user_data, "remixlistorig@example.com", "remixlistoriguser"
    )
    duetist_token, _ = await _register_and_login(
        test_client, register_user_data, "remixlistduet@example.com", "remixlistduetuser"
    )
    stitcher_token, _ = await _register_and_login(
        test_client, register_user_data, "remixliststitch@example.com", "remixliststitchuser"
    )

    original = await test_client.post(
        "/api/videos",
        json={"title": "Popular original", "video_url": "https://example.com/popular.mp4"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_id = original.json()["id"]

    await test_client.post(
        "/api/videos",
        json={
            "title": "A duet",
            "video_url": "https://example.com/aduet.mp4",
            "original_video_id": original_id,
            "remix_type": "duet",
        },
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    await test_client.post(
        "/api/videos",
        json={
            "title": "A stitch",
            "video_url": "https://example.com/astitch.mp4",
            "original_video_id": original_id,
            "remix_type": "stitch",
        },
        headers={"Authorization": f"Bearer {stitcher_token}"},
    )

    all_remixes = await test_client.get(f"/api/videos/{original_id}/remixes")
    assert all_remixes.json()["total"] == 2

    duets_only = await test_client.get(
        f"/api/videos/{original_id}/remixes", params={"remix_type": "duet"}
    )
    assert duets_only.json()["total"] == 1
    assert duets_only.json()["videos"][0]["title"] == "A duet"


@pytest.mark.asyncio
async def test_duet_triggers_notification(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register_and_login(
        test_client, register_user_data, "notifyduetorig@example.com", "notifyduetoriguser"
    )
    duetist_token, _ = await _register_and_login(
        test_client, register_user_data, "notifyduetist@example.com", "notifyduetistuser"
    )

    original = await test_client.post(
        "/api/videos",
        json={"title": "Original", "video_url": "https://example.com/notifyorig.mp4"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_id = original.json()["id"]

    await test_client.post(
        "/api/videos",
        json={
            "title": "Notify duet",
            "video_url": "https://example.com/notifyduet.mp4",
            "original_video_id": original_id,
            "remix_type": "duet",
        },
        headers={"Authorization": f"Bearer {duetist_token}"},
    )

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {creator_token}"}
    )
    data = notif_response.json()
    assert data["total"] == 1
    assert data["notifications"][0]["type"] == "duet_stitch"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
