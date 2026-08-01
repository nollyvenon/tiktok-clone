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
