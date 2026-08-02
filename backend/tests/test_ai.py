"""
AI Creator Studio API tests
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_remove_background(test_client: AsyncClient, register_user_data):
    """Test background removal operation"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Remove background
    response = await test_client.post(
        "/api/ai/background-removal",
        json={
            "segment_id": segment_id,
            "mode": "blur",
            "blur_level": 5,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 202
    data = response.json()

    assert data["mode"] == "blur"
    assert data["blur_level"] == 5


@pytest.mark.asyncio
async def test_get_background_removal_status(test_client: AsyncClient, register_user_data):
    """Test getting background removal status"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Remove background
    response = await test_client.post(
        "/api/ai/background-removal",
        json={
            "segment_id": segment_id,
            "mode": "blur",
            "blur_level": 5,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    removal_id = response.json()["id"]

    # Get status
    response = await test_client.get(
        f"/api/ai/background-removal/{removal_id}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(removal_id)
    assert data["mode"] == "blur"


@pytest.mark.asyncio
async def test_generate_voiceover(test_client: AsyncClient, register_user_data):
    """Test voiceover generation"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Generate voiceover
    response = await test_client.post(
        "/api/ai/voiceover",
        json={
            "segment_id": segment_id,
            "text": "Welcome to our video",
            "language": "en",
            "voice_id": "neural_a",
            "speed": 100,
            "pitch": 100,
            "volume": 100,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 202
    data = response.json()

    assert data["text"] == "Welcome to our video"
    assert data["language"] == "en"


@pytest.mark.asyncio
async def test_get_voiceover_status(test_client: AsyncClient, register_user_data):
    """Test getting voiceover status"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Generate voiceover
    response = await test_client.post(
        "/api/ai/voiceover",
        json={
            "segment_id": segment_id,
            "text": "Test text",
            "language": "en",
            "voice_id": "neural_a",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    voiceover_id = response.json()["id"]

    # Get status
    response = await test_client.get(
        f"/api/ai/voiceover/{voiceover_id}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(voiceover_id)


@pytest.mark.asyncio
async def test_generate_captions(test_client: AsyncClient, register_user_data):
    """Test caption generation"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Generate captions
    response = await test_client.post(
        "/api/ai/captions",
        json={
            "segment_id": segment_id,
            "language": "en",
            "style": "default",
            "position": "bottom",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 202
    data = response.json()

    assert data["language"] == "en"


@pytest.mark.asyncio
async def test_get_captions_status(test_client: AsyncClient, register_user_data):
    """Test getting caption status"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Generate captions
    response = await test_client.post(
        "/api/ai/captions",
        json={
            "segment_id": segment_id,
            "language": "en",
            "style": "default",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    caption_id = response.json()["id"]

    # Get status
    response = await test_client.get(
        f"/api/ai/captions/{caption_id}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(caption_id)


@pytest.mark.asyncio
async def test_get_sound_recommendations(test_client: AsyncClient, register_user_data):
    """Test getting sound recommendations"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get recommendations
    response = await test_client.get(
        "/api/ai/sounds/recommendations?category=background&limit=10",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "sounds" in data
    assert data["category"] == "background"
    assert data["region"] == "US"


@pytest.mark.asyncio
async def test_get_sound_recommendations_by_mood(test_client: AsyncClient, register_user_data):
    """Test getting sound recommendations by mood"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get recommendations by mood
    response = await test_client.get(
        "/api/ai/sounds/recommendations?mood=happy&limit=10",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "sounds" in data


@pytest.mark.asyncio
async def test_get_trending_sounds(test_client: AsyncClient, register_user_data):
    """Test getting trending sounds"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get trending sounds
    response = await test_client.get(
        "/api/ai/sounds/trending?region=US",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "sounds" in data
    assert data["region"] == "US"


async def _register(test_client, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


async def _complete_upload(test_client, access_token, video_url="https://example.com/video.mp4"):
    response = await test_client.post(
        "/api/uploads/presigned-url",
        json={"filename": "video.mp4", "file_size": 104857600, "mime_type": "video/mp4"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    upload_id = response.json()["upload_id"]
    await test_client.post(
        f"/api/uploads/{upload_id}/complete",
        params={"processed_video_url": video_url, "thumbnail_url": "https://example.com/thumb.jpg", "duration": 15},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return upload_id


@pytest.mark.asyncio
async def test_create_sound_and_browse(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "soundcreator@example.com", "soundcreatoruser")

    create_response = await test_client.post(
        "/api/ai/sounds",
        json={
            "sound_url": "https://example.com/song.mp3",
            "sound_title": "Summer Vibes",
            "artist": "DJ Test",
            "category": "music",
            "mood": "happy",
            "region": "US",
            "license_type": "royalty_free",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    sound_id = create_response.json()["id"]
    assert create_response.json()["sound_title"] == "Summer Vibes"

    browse_response = await test_client.get(
        "/api/ai/sounds/recommendations?category=music",
        headers={"Authorization": f"Bearer {token}"},
    )
    titles = [s["sound_title"] for s in browse_response.json()["sounds"]]
    assert "Summer Vibes" in titles
    assert any(s["id"] == sound_id for s in browse_response.json()["sounds"])


@pytest.mark.asyncio
async def test_global_sound_appears_in_every_region_browse(test_client: AsyncClient, register_user_data):
    """A sound contributed as region='Global' must surface in every
    region's default browse, not just when a client explicitly queries
    region=Global - otherwise a contributed sound would never be
    discovered by anyone browsing their own region."""
    token, _ = await _register(test_client, register_user_data, "globalsound@example.com", "globalsounduser")

    await test_client.post(
        "/api/ai/sounds",
        json={
            "sound_url": "https://example.com/global.mp3",
            "sound_title": "Worldwide Anthem",
            "category": "music",
            "region": "Global",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await test_client.get(
        "/api/ai/sounds/recommendations?region=UK",
        headers={"Authorization": f"Bearer {token}"},
    )
    titles = [s["sound_title"] for s in response.json()["sounds"]]
    assert "Worldwide Anthem" in titles


@pytest.mark.asyncio
async def test_attach_sound_to_video_via_publish_pipeline(test_client: AsyncClient, register_user_data):
    """The real client-facing flow: attach a sound to a draft, publish it,
    and see the attribution on the resulting video - not the unused direct
    POST /videos endpoint."""
    token, _ = await _register(test_client, register_user_data, "soundattach@example.com", "soundattachuser")

    sound_response = await test_client.post(
        "/api/ai/sounds",
        json={
            "sound_url": "https://example.com/attach.mp3",
            "sound_title": "Attach Me",
            "artist": "Test Artist",
            "category": "music",
            "region": "Global",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    sound_id = sound_response.json()["id"]

    upload_id = await _complete_upload(test_client, token)
    draft_response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Video with sound", "music_id": sound_id},
        params={"upload_id": upload_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert draft_response.json()["music_id"] == sound_id

    publish_response = await test_client.post(
        f"/api/uploads/drafts/{draft_response.json()['id']}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert publish_response.status_code == 200
    video_id = publish_response.json()["video_id"]

    detail_response = await test_client.get(f"/api/videos/{video_id}")
    data = detail_response.json()
    assert data["music"]["id"] == sound_id
    assert data["music"]["sound_title"] == "Attach Me"
    assert data["music"]["artist"] == "Test Artist"


@pytest.mark.asyncio
async def test_draft_with_nonexistent_sound_rejected(test_client: AsyncClient, register_user_data):
    """A fabricated music_id must be rejected with a clean 400 when the
    draft is saved, not surface as a raw ForeignKeyViolation 500 - and not
    silently deferred to publish time either, since the FK constraint
    itself would reject the row at save time regardless."""
    token, _ = await _register(test_client, register_user_data, "fakesound@example.com", "fakesounduser")

    upload_id = await _complete_upload(test_client, token)
    draft_response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Fake sound", "music_id": str(uuid4())},
        params={"upload_id": upload_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert draft_response.status_code == 400


@pytest.mark.asyncio
async def test_get_videos_using_sound(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "soundvideo1@example.com", "soundvideo1user")
    token_b, _ = await _register(test_client, register_user_data, "soundvideo2@example.com", "soundvideo2user")

    sound_response = await test_client.post(
        "/api/ai/sounds",
        json={
            "sound_url": "https://example.com/popular.mp3",
            "sound_title": "Popular Sound",
            "category": "music",
            "region": "Global",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    sound_id = sound_response.json()["id"]

    for token in (token_a, token_b):
        upload_id = await _complete_upload(test_client, token)
        draft_response = await test_client.post(
            "/api/uploads/drafts",
            json={"title": "Using popular sound", "music_id": sound_id},
            params={"upload_id": upload_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        await test_client.post(
            f"/api/uploads/drafts/{draft_response.json()['id']}/publish",
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await test_client.get(f"/api/ai/sounds/{sound_id}/videos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(v["music"]["id"] == sound_id for v in data["videos"])


@pytest.mark.asyncio
async def test_get_videos_using_nonexistent_sound_404(test_client: AsyncClient):
    response = await test_client.get(f"/api/ai/sounds/{uuid4()}/videos")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_apply_color_correction(test_client: AsyncClient, register_user_data):
    """Test color correction"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Apply color correction
    response = await test_client.post(
        "/api/ai/color-correction",
        json={
            "segment_id": segment_id,
            "method": "auto_enhance",
            "brightness": 10,
            "contrast": 5,
            "saturation": 0,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 202
    data = response.json()

    assert data["method"] == "auto_enhance"


@pytest.mark.asyncio
async def test_get_color_correction_status(test_client: AsyncClient, register_user_data):
    """Test getting color correction status"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Apply color correction
    response = await test_client.post(
        "/api/ai/color-correction",
        json={
            "segment_id": segment_id,
            "method": "preset",
            "preset_name": "cinematic",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    correction_id = response.json()["id"]

    # Get status
    response = await test_client.get(
        f"/api/ai/color-correction/{correction_id}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(correction_id)
    assert data["method"] == "preset"


@pytest.mark.asyncio
async def test_get_frame_suggestions(test_client: AsyncClient, register_user_data):
    """Test smart framing suggestions"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segment
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Get frame suggestions
    response = await test_client.post(
        "/api/ai/smart-frame",
        params={
            "segment_id": segment_id,
            "target_aspect_ratio": "9:16",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 202
    data = response.json()

    assert data["target_aspect_ratio"] == "9:16"


@pytest.mark.asyncio
async def test_get_trend_suggestions(test_client: AsyncClient, register_user_data):
    """Test getting trend suggestions"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get trend suggestions
    response = await test_client.get(
        "/api/ai/trends?region=US&limit=20",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "trends" in data
    assert data["region"] == "US"


@pytest.mark.asyncio
async def test_get_trending_hashtags(test_client: AsyncClient, register_user_data):
    """Test getting trending hashtags"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get hashtags
    response = await test_client.get(
        "/api/ai/trends/hashtags?region=US",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "trends" in data


@pytest.mark.asyncio
async def test_get_hot_trending_sounds(test_client: AsyncClient, register_user_data):
    """Test getting hot trending sounds"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get hot sounds
    response = await test_client.get(
        "/api/ai/trends/sounds?region=US",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "trends" in data


@pytest.mark.asyncio
async def test_get_ai_credits(test_client: AsyncClient, register_user_data):
    """Test getting AI credits"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get credits
    response = await test_client.get(
        "/api/ai/credits",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "total_credits" in data
    assert "available_credits" in data
    assert "used_credits" in data


@pytest.mark.asyncio
async def test_get_ai_operation_history(test_client: AsyncClient, register_user_data):
    """Test getting AI operation history"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    # Get history
    response = await test_client.get(
        f"/api/ai/history/{draft_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "operations" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_unauthorized_ai_access(test_client: AsyncClient, register_user_data):
    """Test unauthorized AI access"""
    # Register first user
    response = await test_client.post("/api/auth/register", json=register_user_data)
    token1 = response.json()["access_token"]

    # Create draft as user 1
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "User 1 Video"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    draft_id = response.json()["id"]

    # Create segment
    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {token1}"}
    )
    segment_id = response.json()["id"]

    # Register second user
    user2_data = register_user_data.copy()
    user2_data["email"] = "user2@example.com"
    user2_data["username"] = "user2"
    response = await test_client.post("/api/auth/register", json=user2_data)
    token2 = response.json()["access_token"]

    # Try to apply AI operation as user 2
    response = await test_client.post(
        "/api/ai/background-removal",
        json={
            "segment_id": segment_id,
            "mode": "blur",
        },
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
