"""
Tests for moderation (Module 26): content reporting and admin review queue.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from uuid import uuid4, UUID

from app.models import User, UserRole, VideoStatus, Video


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
        title="Reportable video",
        video_url="https://example.com/reportable.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()
    await test_db.refresh(video)
    return video


@pytest.mark.asyncio
async def test_report_video(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "reportcreator@example.com", "reportcreatoruser")
    reporter_token, _ = await _register(test_client, register_user_data, "reporter1@example.com", "reporter1user")

    video = await _make_video(test_db, creator_id)

    response = await test_client.post(
        "/api/moderation/reports",
        json={
            "content_type": "video",
            "content_id": str(video.id),
            "reason": "spam",
            "description": "Looks like spam",
        },
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content_type"] == "video"
    assert data["reported_video_id"] == str(video.id)
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_cannot_report_own_video(test_client: AsyncClient, test_db, register_user_data):
    token, user_id = await _register(test_client, register_user_data, "selfreport@example.com", "selfreportuser")
    video = await _make_video(test_db, user_id)

    response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "spam"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_report_self_as_user(test_client: AsyncClient, register_user_data):
    token, user_id = await _register(test_client, register_user_data, "selfuserreport@example.com", "selfuserreportuser")

    response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "user", "content_id": user_id, "reason": "harassment"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_report_nonexistent_video_rejected(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "fakevideoreport@example.com", "fakevideoreportuser")

    response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(uuid4()), "reason": "spam"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_report_comment(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "commentcreator@example.com", "commentcreatoruser")
    commenter_token, _ = await _register(test_client, register_user_data, "commentauthor@example.com", "commentauthoruser")
    reporter_token, _ = await _register(test_client, register_user_data, "commentreporter@example.com", "commentreporteruser")

    video = await _make_video(test_db, creator_id)
    comment_response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Some comment"},
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    comment_id = comment_response.json()["id"]

    response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "comment", "content_id": comment_id, "reason": "harassment"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    assert response.status_code == 201
    assert response.json()["reported_comment_id"] == comment_id


@pytest.mark.asyncio
async def test_report_user(test_client: AsyncClient, register_user_data):
    _, target_id = await _register(test_client, register_user_data, "reporttarget@example.com", "reporttargetuser")
    reporter_token, _ = await _register(test_client, register_user_data, "userreporter@example.com", "userreporteruser")

    response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "user", "content_id": target_id, "reason": "harassment", "description": "Bad behavior"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    assert response.status_code == 201
    assert response.json()["reported_user_id"] == target_id


@pytest.mark.asyncio
async def test_get_my_reports(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "myreportscreator@example.com", "myreportscreatoruser")
    reporter_token, _ = await _register(test_client, register_user_data, "myreportsuser@example.com", "myreportsuseruser")
    video = await _make_video(test_db, creator_id)

    await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "spam"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )

    response = await test_client.get(
        "/api/moderation/reports/me", headers={"Authorization": f"Bearer {reporter_token}"}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_non_admin_cannot_view_report_queue(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadmin@example.com", "notadminuser")

    response = await test_client.get("/api/moderation/reports", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_view_report_queue(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "queuecreator@example.com", "queuecreatoruser")
    reporter_token, _ = await _register(test_client, register_user_data, "queuereporter@example.com", "queuereporteruser")
    admin_token, admin_id = await _register(test_client, register_user_data, "queueadmin@example.com", "queueadminuser")
    await _make_admin(test_db, admin_id)

    video = await _make_video(test_db, creator_id)
    await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "spam"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )

    response = await test_client.get("/api/moderation/reports", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["reports"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_admin_dismiss_report(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "dismisscreator@example.com", "dismisscreatoruser")
    reporter_token, _ = await _register(test_client, register_user_data, "dismissreporter@example.com", "dismissreporteruser")
    admin_token, admin_id = await _register(test_client, register_user_data, "dismissadmin@example.com", "dismissadminuser")
    await _make_admin(test_db, admin_id)

    video = await _make_video(test_db, creator_id)
    report_response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "spam"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    report_id = report_response.json()["id"]

    decision_response = await test_client.post(
        f"/api/moderation/reports/{report_id}/decide",
        json={"action": "dismiss", "notes": "Not spam"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["action"] == "dismiss"

    video_check = await test_client.get(f"/api/videos/{video.id}")
    assert video_check.status_code == 200


@pytest.mark.asyncio
async def test_admin_remove_video_content(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "removecreator@example.com", "removecreatoruser")
    reporter_token, _ = await _register(test_client, register_user_data, "removereporter@example.com", "removereporteruser")
    admin_token, admin_id = await _register(test_client, register_user_data, "removeadmin@example.com", "removeadminuser")
    await _make_admin(test_db, admin_id)

    video = await _make_video(test_db, creator_id)
    report_response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "nudity"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    report_id = report_response.json()["id"]

    decision_response = await test_client.post(
        f"/api/moderation/reports/{report_id}/decide",
        json={"action": "remove_content"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert decision_response.status_code == 200

    video_check = await test_client.get(f"/api/videos/{video.id}")
    assert video_check.status_code == 404


@pytest.mark.asyncio
async def test_admin_suspend_user_report(test_client: AsyncClient, test_db, register_user_data):
    target_token, target_id = await _register(test_client, register_user_data, "suspendtarget2@example.com", "suspendtarget2user")
    reporter_token, _ = await _register(test_client, register_user_data, "suspendreporter2@example.com", "suspendreporter2user")
    admin_token, admin_id = await _register(test_client, register_user_data, "suspendadmin2@example.com", "suspendadmin2user")
    await _make_admin(test_db, admin_id)

    report_response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "user", "content_id": target_id, "reason": "harassment"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    report_id = report_response.json()["id"]

    decision_response = await test_client.post(
        f"/api/moderation/reports/{report_id}/decide",
        json={"action": "suspend_user", "notes": "Repeated harassment"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert decision_response.status_code == 200

    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": "suspendtarget2@example.com", "password": register_user_data["password"]},
    )
    assert login_response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_cannot_decide_already_decided_report(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "redecidecreator@example.com", "redecidecreatoruser")
    reporter_token, _ = await _register(test_client, register_user_data, "redecidereporter@example.com", "redecidereporteruser")
    admin_token, admin_id = await _register(test_client, register_user_data, "redecideadmin@example.com", "redecideadminuser")
    await _make_admin(test_db, admin_id)

    video = await _make_video(test_db, creator_id)
    report_response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "spam"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    report_id = report_response.json()["id"]

    await test_client.post(
        f"/api/moderation/reports/{report_id}/decide",
        json={"action": "dismiss"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    second_response = await test_client.post(
        f"/api/moderation/reports/{report_id}/decide",
        json={"action": "remove_content"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert second_response.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_cannot_decide_report(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(test_client, register_user_data, "notadmindecide@example.com", "notadmindecideuser")
    reporter_token, _ = await _register(test_client, register_user_data, "notadmindecider@example.com", "notadmindecideruser")
    video = await _make_video(test_db, creator_id)

    report_response = await test_client.post(
        "/api/moderation/reports",
        json={"content_type": "video", "content_id": str(video.id), "reason": "spam"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    report_id = report_response.json()["id"]

    response = await test_client.post(
        f"/api/moderation/reports/{report_id}/decide",
        json={"action": "dismiss"},
        headers={"Authorization": f"Bearer {reporter_token}"},
    )
    assert response.status_code == 403
