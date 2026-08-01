"""
Video editor API tests
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_add_segment(test_client: AsyncClient, register_user_data):
    """Test adding segment to draft"""
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

    # Add segment
    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
            "volume": 100,
            "muted": False,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    segment = response.json()

    assert segment["start_time"] == 0
    assert segment["end_time"] == 5000
    assert segment["content_type"] == "video"
    assert segment["order"] == 0


@pytest.mark.asyncio
async def test_get_segments(test_client: AsyncClient, register_user_data):
    """Test getting segments for draft"""
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

    # Add multiple segments
    for i in range(3):
        await test_client.post(
            f"/api/editor/drafts/{draft_id}/segments",
            json={
                "start_time": i * 5000,
                "end_time": (i + 1) * 5000,
                "content_type": "video",
                "content_url": f"https://example.com/video{i}.mp4",
                "volume": 100,
                "muted": False,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # Get segments
    response = await test_client.get(f"/api/editor/drafts/{draft_id}/segments")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert len(data["segments"]) == 3


@pytest.mark.asyncio
async def test_update_segment(test_client: AsyncClient, register_user_data):
    """Test updating a segment"""
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
            "volume": 100,
            "muted": False,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Update segment
    response = await test_client.put(
        f"/api/editor/segments/{segment_id}",
        json={
            "start_time": 0,
            "end_time": 6000,
            "content_type": "video",
            "content_url": "https://example.com/video_updated.mp4",
            "volume": 80,
            "muted": True,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    segment = response.json()

    assert segment["end_time"] == 6000
    assert segment["volume"] == 80
    assert segment["muted"] is True


@pytest.mark.asyncio
async def test_delete_segment(test_client: AsyncClient, register_user_data):
    """Test deleting a segment"""
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
            "volume": 100,
            "muted": False,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Delete segment
    response = await test_client.delete(
        f"/api/editor/segments/{segment_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reorder_segments(test_client: AsyncClient, register_user_data):
    """Test reordering segments"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and segments
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Video"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    segment_ids = []
    for i in range(3):
        response = await test_client.post(
            f"/api/editor/drafts/{draft_id}/segments",
            json={
                "start_time": i * 5000,
                "end_time": (i + 1) * 5000,
                "content_type": "video",
                "content_url": f"https://example.com/video{i}.mp4",
                "volume": 100,
                "muted": False,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        segment_ids.append(response.json()["id"])

    # Reorder segments
    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/reorder-segments",
        params={"segment_ids": segment_ids[::-1]},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_add_text_overlay(test_client: AsyncClient, register_user_data):
    """Test adding text overlay to segment"""
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

    # Add text overlay
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/overlays",
        json={
            "text": "Hello World",
            "font_family": "Arial",
            "font_size": 24,
            "color": "#FFFFFF",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 50,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    overlay = response.json()

    assert overlay["text"] == "Hello World"
    assert overlay["font_size"] == 24


@pytest.mark.asyncio
async def test_get_text_overlays(test_client: AsyncClient, register_user_data):
    """Test getting text overlays for segment"""
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

    # Add multiple overlays
    for i in range(2):
        await test_client.post(
            f"/api/editor/segments/{segment_id}/overlays",
            json={
                "text": f"Text {i}",
                "font_family": "Arial",
                "font_size": 24,
                "color": "#FFFFFF",
                "x": 100 + i * 50,
                "y": 100,
                "width": 200,
                "height": 50,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # Get overlays
    response = await test_client.get(f"/api/editor/segments/{segment_id}/overlays")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert len(data["overlays"]) == 2


@pytest.mark.asyncio
async def test_delete_text_overlay(test_client: AsyncClient, register_user_data):
    """Test deleting text overlay"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft, segment, and overlay
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

    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/overlays",
        json={
            "text": "Delete me",
            "font_family": "Arial",
            "font_size": 24,
            "color": "#FFFFFF",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 50,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    overlay_id = response.json()["id"]

    # Delete overlay
    response = await test_client.delete(
        f"/api/editor/overlays/{overlay_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_add_sticker(test_client: AsyncClient, register_user_data):
    """Test adding sticker to segment"""
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

    # Add sticker
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/stickers",
        json={
            "sticker_url": "https://example.com/sticker.png",
            "sticker_type": "emoji",
            "x": 50,
            "y": 50,
            "width": 100,
            "height": 100,
            "rotation": 0,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    sticker = response.json()

    assert sticker["sticker_type"] == "emoji"
    assert sticker["rotation"] == 0


@pytest.mark.asyncio
async def test_get_stickers(test_client: AsyncClient, register_user_data):
    """Test getting stickers for segment"""
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

    # Add multiple stickers
    for i in range(2):
        await test_client.post(
            f"/api/editor/segments/{segment_id}/stickers",
            json={
                "sticker_url": f"https://example.com/sticker{i}.png",
                "sticker_type": "emoji",
                "x": 50 + i * 50,
                "y": 50,
                "width": 100,
                "height": 100,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # Get stickers
    response = await test_client.get(f"/api/editor/segments/{segment_id}/stickers")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert len(data["stickers"]) == 2


@pytest.mark.asyncio
async def test_delete_sticker(test_client: AsyncClient, register_user_data):
    """Test deleting sticker"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft, segment, and sticker
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

    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/stickers",
        json={
            "sticker_url": "https://example.com/sticker.png",
            "sticker_type": "emoji",
            "x": 50,
            "y": 50,
            "width": 100,
            "height": 100,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    sticker_id = response.json()["id"]

    # Delete sticker
    response = await test_client.delete(
        f"/api/editor/stickers/{sticker_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_apply_effect(test_client: AsyncClient, register_user_data):
    """Test applying effect to segment"""
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

    # Apply effect
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/effects/blur",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    segment = response.json()

    assert segment["effects"] is not None


@pytest.mark.asyncio
async def test_trim_video(test_client: AsyncClient, register_user_data):
    """Test trimming video segment"""
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
            "end_time": 10000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    segment_id = response.json()["id"]

    # Trim video
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/trim",
        params={"start_time": 1000, "end_time": 8000},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    segment = response.json()

    assert segment["start_time"] == 1000
    assert segment["end_time"] == 8000


@pytest.mark.asyncio
async def test_adjust_speed(test_client: AsyncClient, register_user_data):
    """Test adjusting segment speed"""
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

    # Adjust speed
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/speed",
        params={"speed": 1.5},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    segment = response.json()

    assert segment["effects"] is not None


@pytest.mark.asyncio
async def test_adjust_volume(test_client: AsyncClient, register_user_data):
    """Test adjusting segment volume"""
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

    # Adjust volume
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/volume",
        params={"volume": 50},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    segment = response.json()

    assert segment["volume"] == 50


@pytest.mark.asyncio
async def test_mute_segment(test_client: AsyncClient, register_user_data):
    """Test muting segment"""
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

    # Mute segment
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/mute",
        params={"muted": True},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    segment = response.json()

    assert segment["muted"] is True


@pytest.mark.asyncio
async def test_get_editor_state(test_client: AsyncClient, register_user_data):
    """Test getting complete editor state"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft and add content
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

    await test_client.post(
        f"/api/editor/segments/{segment_id}/overlays",
        json={
            "text": "Hello",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 50,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Get editor state
    response = await test_client.get(
        f"/api/editor/drafts/{draft_id}/state"
    )
    assert response.status_code == 200
    state = response.json()

    assert state["draft_id"] == str(draft_id)
    assert len(state["segments"]) == 1
    assert len(state["text_overlays"]) == 1
    assert state["total_duration"] == 5000


@pytest.mark.asyncio
async def test_export_video(test_client: AsyncClient, register_user_data):
    """Test exporting video"""
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

    # Export video
    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/export",
        params={"quality": "1080p", "format": "mp4"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    export = response.json()

    assert export["draft_id"] == str(draft_id)
    assert export["quality"] == "1080p"
    assert export["format"] == "mp4"
    assert export["status"] == "queued"


@pytest.mark.asyncio
async def test_unauthorized_segment_access(test_client: AsyncClient, register_user_data):
    """Test unauthorized segment access"""
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

    # Register second user
    user2_data = register_user_data.copy()
    user2_data["email"] = "user2@example.com"
    user2_data["username"] = "user2"
    response = await test_client.post("/api/auth/register", json=user2_data)
    token2 = response.json()["access_token"]

    # Try to add segment as user 2
    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_export_quality(test_client: AsyncClient, register_user_data):
    """Test export with invalid quality"""
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

    # Export with invalid quality (should still work - validation is optional)
    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/export",
        params={"quality": "invalid", "format": "mp4"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_missing_required_segment_fields(test_client: AsyncClient, register_user_data):
    """Test creating segment with missing fields"""
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

    # Try to add segment with missing fields
    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "content_type": "video",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_overlay_with_animation(test_client: AsyncClient, register_user_data):
    """Test adding overlay with animation"""
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

    # Add overlay with animation
    response = await test_client.post(
        f"/api/editor/segments/{segment_id}/overlays",
        json={
            "text": "Animated Text",
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 50,
            "animation_type": "fade_in",
            "animation_duration": 500,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    overlay = response.json()

    assert overlay["animation_type"] == "fade_in"
    assert overlay["animation_duration"] == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
