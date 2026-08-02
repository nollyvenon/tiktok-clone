"""
Tests for the admin dashboard (Module 25): platform stats, user
management, and audit log.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10.
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4

from app.models import User, UserRole, Video, VideoStatus


async def _register(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


async def _make_admin(test_db, user_id: str):
    user = await test_db.get(User, UUID(user_id))
    user.role = UserRole.ADMIN
    await test_db.commit()


async def _make_video(test_db, user_id):
    video = Video(
        user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
        title="Admin test video",
        video_url="https://example.com/admintest.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()
    await test_db.refresh(video)
    return video


@pytest.mark.asyncio
async def test_non_admin_cannot_view_stats(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadminstats@example.com", "notadminstatsuser")
    response = await test_client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_view_stats(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "statsadmin@example.com", "statsadminuser")
    await _make_admin(test_db, admin_id)

    _, creator_id = await _register(test_client, register_user_data, "statscreator@example.com", "statscreatoruser")
    await _make_video(test_db, creator_id)

    response = await test_client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] >= 2
    assert data["total_videos"] >= 1
    assert data["active_users"] >= 1


@pytest.mark.asyncio
async def test_admin_can_list_users(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "listadmin@example.com", "listadminuser")
    await _make_admin(test_db, admin_id)
    _, _ = await _register(test_client, register_user_data, "listedone@example.com", "listedoneuser")

    response = await test_client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    usernames = [u["username"] for u in data["users"]]
    assert "listedoneuser" in usernames
    assert "listadminuser" in usernames


@pytest.mark.asyncio
async def test_admin_can_search_users(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "searchadmin@example.com", "searchadminuser")
    await _make_admin(test_db, admin_id)
    await _register(test_client, register_user_data, "findme@example.com", "findmeuser")
    await _register(test_client, register_user_data, "other@example.com", "otheruser")

    response = await test_client.get(
        "/api/admin/users", params={"search": "findme"}, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["users"][0]["username"] == "findmeuser"


@pytest.mark.asyncio
async def test_non_admin_cannot_list_users(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadminusers@example.com", "notadminusersuser")
    response = await test_client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_suspend_and_reactivate_user(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "suspendadmin@example.com", "suspendadminuser")
    await _make_admin(test_db, admin_id)
    target_token, target_id = await _register(test_client, register_user_data, "suspendtarget3@example.com", "suspendtarget3user")

    suspend_response = await test_client.post(
        f"/api/admin/users/{target_id}/suspend", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert suspend_response.status_code == 200
    assert suspend_response.json()["is_active"] is False

    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": "suspendtarget3@example.com", "password": register_user_data["password"]},
    )
    assert login_response.status_code == 401

    reactivate_response = await test_client.post(
        f"/api/admin/users/{target_id}/reactivate", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["is_active"] is True

    login_response2 = await test_client.post(
        "/api/auth/login",
        json={"email": "suspendtarget3@example.com", "password": register_user_data["password"]},
    )
    assert login_response2.status_code == 200


@pytest.mark.asyncio
async def test_suspend_nonexistent_user_rejected(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "suspendfakeadmin@example.com", "suspendfakeadminuser")
    await _make_admin(test_db, admin_id)

    response = await test_client.post(
        f"/api/admin/users/{uuid4()}/suspend", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_cannot_suspend_user(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadminsuspend@example.com", "notadminsuspenduser")
    _, target_id = await _register(test_client, register_user_data, "suspendvictim@example.com", "suspendvictimuser")

    response = await test_client.post(
        f"/api/admin/users/{target_id}/suspend", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_view_audit_log(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "auditadmin@example.com", "auditadminuser")
    await _make_admin(test_db, admin_id)
    reporter_token, _ = await _register(test_client, register_user_data, "auditreporter@example.com", "auditreporteruser")
    _, creator_id = await _register(test_client, register_user_data, "auditcreator@example.com", "auditcreatoruser")

    video = await _make_video(test_db, creator_id)
    report_response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "spam"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    report_id = report_response.json()["id"]
    await test_client.post(
        f"/api/moderation/reports/{report_id}/decide",
        json={"action": "dismiss", "notes": "False alarm"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await test_client.get("/api/admin/audit-log", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    entry = data["entries"][0]
    assert entry["action"] == "dismiss"
    assert entry["moderator_username"] == "auditadminuser"
    assert entry["report_content_type"] == "video"
    assert entry["notes"] == "False alarm"


@pytest.mark.asyncio
async def test_non_admin_cannot_view_audit_log(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadminaudit@example.com", "notadminaudituser")
    response = await test_client.get("/api/admin/audit-log", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
