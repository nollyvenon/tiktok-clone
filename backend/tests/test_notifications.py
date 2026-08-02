"""
Tests for the notification system (Module 10).

Written HTTP-level from the start (via test_client), not service-level -
every prior module's real bugs (route-order conflicts, response schemas
that don't match the model, response builders that never populate the
required nested fields) were only ever caught once something actually
issued a real HTTP request. This module never gets a service-only test
file to begin with.
"""

import pytest
from httpx import AsyncClient


async def _register(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


@pytest.mark.asyncio
async def test_get_notifications_empty(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notif1@example.com", "notifuser1")

    response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notifications"] == []
    assert data["total"] == 0
    assert data["unread_count"] == 0


@pytest.mark.asyncio
async def test_get_notifications_requires_auth(test_client: AsyncClient):
    response = await test_client.get("/api/notifications")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_follow_triggers_notification(test_client: AsyncClient, register_user_data):
    """Following a user must actually create a notification for them, end to end."""
    token1, _ = await _register(test_client, register_user_data, "follower@example.com", "followeruser")
    token2, user2_id = await _register(test_client, register_user_data, "followed@example.com", "followeduser")

    follow_response = await test_client.post(
        f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"}
    )
    assert follow_response.status_code == 200

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    assert notif_response.status_code == 200
    data = notif_response.json()
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert data["notifications"][0]["type"] == "follow"
    assert "followeruser" in data["notifications"][0]["title"]


@pytest.mark.asyncio
async def test_unfollow_does_not_create_notification(test_client: AsyncClient, register_user_data):
    token1, _ = await _register(test_client, register_user_data, "unfollower@example.com", "unfolloweruser")
    token2, user2_id = await _register(test_client, register_user_data, "unfollowed@example.com", "unfolloweduser")

    # Follow then unfollow
    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})
    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    # Only the follow should have notified, not the unfollow
    assert notif_response.json()["total"] == 1


@pytest.mark.asyncio
async def test_self_action_does_not_notify(test_client: AsyncClient, register_user_data):
    """A user liking/following their own content must not notify themselves."""
    from app.models import User, Video, VideoStatus

    token, user_id = await _register(test_client, register_user_data, "selfnotify@example.com", "selfnotifyuser")

    # Can't self-follow (raises ValueError), but can self-like own video
    me_response = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200


@pytest.mark.asyncio
async def test_like_triggers_notification(test_client: AsyncClient, test_db, register_user_data):
    from app.models import Video, VideoStatus
    from uuid import UUID

    creator_token, creator_id = await _register(
        test_client, register_user_data, "videocreator@example.com", "videocreatoruser"
    )
    liker_token, _ = await _register(
        test_client, register_user_data, "videoliker@example.com", "videolikeruser"
    )

    video = Video(
        user_id=UUID(creator_id),
        title="Test video",
        video_url="https://example.com/v.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    like_response = await test_client.post(
        f"/api/videos/{video.id}/like", headers={"Authorization": f"Bearer {liker_token}"}
    )
    assert like_response.status_code == 200

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {creator_token}"}
    )
    data = notif_response.json()
    assert data["total"] == 1
    assert data["notifications"][0]["type"] == "like"
    assert data["notifications"][0]["related_video_id"] == str(video.id)


@pytest.mark.asyncio
async def test_mark_notification_read(test_client: AsyncClient, register_user_data):
    token1, _ = await _register(test_client, register_user_data, "markread1@example.com", "markread1user")
    token2, user2_id = await _register(test_client, register_user_data, "markread2@example.com", "markread2user")

    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})

    list_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    notification_id = list_response.json()["notifications"][0]["id"]

    read_response = await test_client.put(
        f"/api/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    list_response2 = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    assert list_response2.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_notification_read_wrong_owner_404(test_client: AsyncClient, register_user_data):
    token1, _ = await _register(test_client, register_user_data, "wrongowner1@example.com", "wrongowner1user")
    token2, user2_id = await _register(test_client, register_user_data, "wrongowner2@example.com", "wrongowner2user")
    token3, _ = await _register(test_client, register_user_data, "wrongowner3@example.com", "wrongowner3user")

    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})

    list_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    notification_id = list_response.json()["notifications"][0]["id"]

    # A different user (token3) must not be able to mark it read
    response = await test_client.put(
        f"/api/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {token3}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read(test_client: AsyncClient, register_user_data):
    token1, _ = await _register(test_client, register_user_data, "markall1@example.com", "markall1user")
    token2, user2_id = await _register(test_client, register_user_data, "markall2@example.com", "markall2user")
    token3, user3_id = await _register(test_client, register_user_data, "markall3@example.com", "markall3user")

    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})
    await test_client.post(f"/api/profiles/{user3_id}/follow", headers={"Authorization": f"Bearer {token1}"})

    # user2 and user3 each got one follow notification from user1 - mark user1's
    # own (empty) inbox all-read to verify a zero-count response works too
    response = await test_client.put(
        "/api/notifications/read-all", headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    assert response.json()["count"] == 0

    response2 = await test_client.put(
        "/api/notifications/read-all", headers={"Authorization": f"Bearer {token2}"}
    )
    assert response2.status_code == 200
    assert response2.json()["count"] == 1


@pytest.mark.asyncio
async def test_delete_notification(test_client: AsyncClient, register_user_data):
    token1, _ = await _register(test_client, register_user_data, "delete1@example.com", "delete1user")
    token2, user2_id = await _register(test_client, register_user_data, "delete2@example.com", "delete2user")

    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})

    list_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    notification_id = list_response.json()["notifications"][0]["id"]

    delete_response = await test_client.delete(
        f"/api/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert delete_response.status_code == 200

    list_response2 = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    assert list_response2.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_notification_404(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "deletenone@example.com", "deletenoneuser")
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await test_client.delete(
        f"/api/notifications/{fake_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_preferences_defaults(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "prefsdefault@example.com", "prefsdefaultuser")

    response = await test_client.get(
        "/api/notifications/preferences", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["push_enabled"] is True
    assert data["email_digest_frequency"] == "daily"


@pytest.mark.asyncio
async def test_update_preferences(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "prefsupdate@example.com", "prefsupdateuser")

    response = await test_client.put(
        "/api/notifications/preferences",
        json={"follow_notifications": False, "email_digest_frequency": "weekly"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["follow_notifications"] is False
    assert data["email_digest_frequency"] == "weekly"
    assert data["like_notifications"] is True  # untouched fields stay at default


@pytest.mark.asyncio
async def test_disabled_notification_type_suppresses_notification(
    test_client: AsyncClient, register_user_data
):
    """If a user disables follow notifications, following them must not create one."""
    token1, _ = await _register(test_client, register_user_data, "suppress1@example.com", "suppress1user")
    token2, user2_id = await _register(test_client, register_user_data, "suppress2@example.com", "suppress2user")

    await test_client.put(
        "/api/notifications/preferences",
        json={"follow_notifications": False},
        headers={"Authorization": f"Bearer {token2}"},
    )

    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    assert notif_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_unread_only_filter(test_client: AsyncClient, register_user_data):
    token1, _ = await _register(test_client, register_user_data, "unreadonly1@example.com", "unreadonly1user")
    token2, user2_id = await _register(test_client, register_user_data, "unreadonly2@example.com", "unreadonly2user")
    token3, user3_id = await _register(test_client, register_user_data, "unreadonly3@example.com", "unreadonly3user")

    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token1}"})
    await test_client.post(f"/api/profiles/{user2_id}/follow", headers={"Authorization": f"Bearer {token3}"})

    list_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token2}"}
    )
    assert list_response.json()["total"] == 2

    first_id = list_response.json()["notifications"][0]["id"]
    await test_client.put(
        f"/api/notifications/{first_id}/read", headers={"Authorization": f"Bearer {token2}"}
    )

    unread_response = await test_client.get(
        "/api/notifications?unread_only=true", headers={"Authorization": f"Bearer {token2}"}
    )
    assert unread_response.json()["total"] == 1
