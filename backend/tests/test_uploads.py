"""
Upload and draft API tests
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_presigned_url(test_client: AsyncClient, register_user_data):
    """Test getting presigned URL"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get presigned URL
    response = await test_client.post(
        "/api/uploads/presigned-url",
        json={
            "filename": "video.mp4",
            "file_size": 104857600,  # 100MB
            "mime_type": "video/mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "upload_id" in data
    assert "presigned_url" in data
    assert data["expires_in"] == 3600


@pytest.mark.asyncio
async def test_complete_upload(test_client: AsyncClient, register_user_data):
    """Test completing an upload"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Get presigned URL (creates upload)
    response = await test_client.post(
        "/api/uploads/presigned-url",
        json={
            "filename": "video.mp4",
            "file_size": 104857600,
            "mime_type": "video/mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    upload_id = response.json()["upload_id"]

    # Complete upload
    response = await test_client.post(
        f"/api/uploads/{upload_id}/complete",
        params={
            "processed_video_url": "https://example.com/video.mp4",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "duration": 30,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    upload = response.json()

    assert upload["status"] == "completed"
    assert upload["progress"] == 100
    assert upload["duration"] == 30


@pytest.mark.asyncio
async def test_get_upload_status(test_client: AsyncClient, register_user_data):
    """Test getting upload status"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create upload
    response = await test_client.post(
        "/api/uploads/presigned-url",
        json={
            "filename": "video.mp4",
            "file_size": 104857600,
            "mime_type": "video/mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    upload_id = response.json()["upload_id"]

    # Get upload status
    response = await test_client.get(f"/api/uploads/{upload_id}")
    assert response.status_code == 200
    upload = response.json()

    assert upload["id"] == upload_id
    assert upload["status"] == "uploading"


@pytest.mark.asyncio
async def test_create_draft(test_client: AsyncClient, register_user_data):
    """Test creating a draft"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft
    response = await test_client.post(
        "/api/uploads/drafts",
        json={
            "title": "My Video",
            "description": "A cool video",
            "hashtags": "#cool #video",
            "is_public": True,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    draft = response.json()

    assert draft["title"] == "My Video"
    assert draft["description"] == "A cool video"
    assert draft["status"] == "editing"


@pytest.mark.asyncio
async def test_get_draft(test_client: AsyncClient, register_user_data):
    """Test getting a draft"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft
    response = await test_client.post(
        "/api/uploads/drafts",
        json={
            "title": "Test Draft",
            "description": "Test",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    # Get draft
    response = await test_client.get(
        f"/api/uploads/drafts/{draft_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    draft = response.json()

    assert draft["id"] == draft_id
    assert draft["title"] == "Test Draft"


@pytest.mark.asyncio
async def test_update_draft(test_client: AsyncClient, register_user_data):
    """Test updating a draft"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft
    response = await test_client.post(
        "/api/uploads/drafts",
        json={
            "title": "Original Title",
            "description": "Original description",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    # Update draft
    response = await test_client.put(
        f"/api/uploads/drafts/{draft_id}",
        json={
            "title": "Updated Title",
            "description": "Updated description",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    draft = response.json()

    assert draft["title"] == "Updated Title"
    assert draft["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_draft(test_client: AsyncClient, register_user_data):
    """Test deleting a draft"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Draft"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    # Delete draft
    response = await test_client.delete(
        f"/api/uploads/drafts/{draft_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 204

    # Try to get deleted draft
    response = await test_client.get(
        f"/api/uploads/drafts/{draft_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_drafts(test_client: AsyncClient, register_user_data):
    """Test getting user's drafts"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create multiple drafts
    for i in range(3):
        await test_client.post(
            "/api/uploads/drafts",
            json={"title": f"Draft {i}"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # Get user drafts
    response = await test_client.get(
        "/api/uploads/drafts",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "drafts" in data
    assert len(data["drafts"]) == 3
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_publish_draft(test_client: AsyncClient, register_user_data):
    """Test publishing a draft"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create upload and complete it
    response = await test_client.post(
        "/api/uploads/presigned-url",
        json={
            "filename": "video.mp4",
            "file_size": 104857600,
            "mime_type": "video/mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    upload_id = response.json()["upload_id"]

    await test_client.post(
        f"/api/uploads/{upload_id}/complete",
        params={
            "processed_video_url": "https://example.com/video.mp4",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "duration": 30,
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Create draft with upload
    response = await test_client.post(
        "/api/uploads/drafts",
        json={
            "title": "My Video",
            "description": "A cool video",
        },
        params={"upload_id": upload_id},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    # Publish draft
    response = await test_client.post(
        f"/api/uploads/drafts/{draft_id}/publish",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "published"
    assert "video_id" in data


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


async def _register(test_client, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


@pytest.mark.asyncio
async def test_publish_draft_as_duet(test_client: AsyncClient, register_user_data):
    """The real client-facing duet flow: publish a video, then publish a
    second user's draft as a duet of it, through the actual draft/publish
    pipeline (not the unused direct POST /videos endpoint)."""
    creator_token, _ = await _register(test_client, register_user_data, "draftduetorig@example.com", "draftduetoriguser")
    duetist_token, _ = await _register(test_client, register_user_data, "draftduetist@example.com", "draftduetistuser")

    upload_id = await _complete_upload(test_client, creator_token, "https://example.com/original2.mp4")
    original_draft = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Original video"},
        params={"upload_id": upload_id},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_publish = await test_client.post(
        f"/api/uploads/drafts/{original_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_video_id = original_publish.json()["video_id"]

    duet_upload_id = await _complete_upload(test_client, duetist_token, "https://example.com/myduet.mp4")
    duet_draft = await test_client.post(
        "/api/uploads/drafts",
        json={
            "title": "My duet",
            "original_video_id": original_video_id,
            "remix_type": "duet",
        },
        params={"upload_id": duet_upload_id},
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    assert duet_draft.json()["original_video_id"] == original_video_id
    assert duet_draft.json()["remix_type"] == "duet"

    publish_response = await test_client.post(
        f"/api/uploads/drafts/{duet_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    assert publish_response.status_code == 200
    duet_video_id = publish_response.json()["video_id"]

    detail = await test_client.get(f"/api/videos/{duet_video_id}")
    data = detail.json()
    assert data["remix_type"] == "duet"
    assert data["original_video"]["id"] == original_video_id


@pytest.mark.asyncio
async def test_publish_draft_duet_rejected_when_disabled(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register(test_client, register_user_data, "draftnoduetorig@example.com", "draftnoduetoriguser")
    duetist_token, _ = await _register(test_client, register_user_data, "draftnoduetist@example.com", "draftnoduetistuser")

    upload_id = await _complete_upload(test_client, creator_token)
    original_draft = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "No duets", "allow_duets": False},
        params={"upload_id": upload_id},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_publish = await test_client.post(
        f"/api/uploads/drafts/{original_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_video_id = original_publish.json()["video_id"]

    duet_upload_id = await _complete_upload(test_client, duetist_token)
    duet_draft = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Attempted duet", "original_video_id": original_video_id, "remix_type": "duet"},
        params={"upload_id": duet_upload_id},
        headers={"Authorization": f"Bearer {duetist_token}"},
    )

    publish_response = await test_client.post(
        f"/api/uploads/drafts/{duet_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    assert publish_response.status_code == 400


@pytest.mark.asyncio
async def test_publish_draft_duet_revoked_between_draft_and_publish(test_client: AsyncClient, register_user_data):
    """Duet permission is checked at publish time, not draft-save time -
    disabling duets after the draft was created must still block publish."""
    creator_token, _ = await _register(test_client, register_user_data, "revokeorig@example.com", "revokeoriguser")
    duetist_token, _ = await _register(test_client, register_user_data, "revokeduetist@example.com", "revokeduetistuser")

    upload_id = await _complete_upload(test_client, creator_token)
    original_draft = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Originally allowed"},
        params={"upload_id": upload_id},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_publish = await test_client.post(
        f"/api/uploads/drafts/{original_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_video_id = original_publish.json()["video_id"]

    duet_upload_id = await _complete_upload(test_client, duetist_token)
    duet_draft = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Duet in progress", "original_video_id": original_video_id, "remix_type": "duet"},
        params={"upload_id": duet_upload_id},
        headers={"Authorization": f"Bearer {duetist_token}"},
    )

    # Creator disables duets after the draft already references their video
    await test_client.put(
        f"/api/videos/{original_video_id}",
        json={"allow_duets": False},
        headers={"Authorization": f"Bearer {creator_token}"},
    )

    publish_response = await test_client.post(
        f"/api/uploads/drafts/{duet_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    assert publish_response.status_code == 400


@pytest.mark.asyncio
async def test_publish_duet_triggers_notification(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register(test_client, register_user_data, "notifydraftorig@example.com", "notifydraftoriguser")
    duetist_token, _ = await _register(test_client, register_user_data, "notifydraftist@example.com", "notifydraftistuser")

    upload_id = await _complete_upload(test_client, creator_token)
    original_draft = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Original"},
        params={"upload_id": upload_id},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_publish = await test_client.post(
        f"/api/uploads/drafts/{original_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    original_video_id = original_publish.json()["video_id"]

    duet_upload_id = await _complete_upload(test_client, duetist_token)
    duet_draft = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Notify duet", "original_video_id": original_video_id, "remix_type": "duet"},
        params={"upload_id": duet_upload_id},
        headers={"Authorization": f"Bearer {duetist_token}"},
    )
    await test_client.post(
        f"/api/uploads/drafts/{duet_draft.json()['id']}/publish",
        headers={"Authorization": f"Bearer {duetist_token}"},
    )

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {creator_token}"}
    )
    data = notif_response.json()
    assert data["total"] == 1
    assert data["notifications"][0]["type"] == "duet_stitch"


@pytest.mark.asyncio
async def test_schedule_draft(test_client: AsyncClient, register_user_data):
    """Test scheduling a draft"""
    # Register and login
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    # Create draft
    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Test Draft"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    draft_id = response.json()["id"]

    # Schedule draft
    response = await test_client.post(
        f"/api/uploads/drafts/{draft_id}/schedule",
        params={"publish_at": "2024-08-15T14:30:00"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    draft = response.json()

    assert draft["status"] == "ready_to_publish"
    assert draft["scheduled_publish_at"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
