"""
Tests for the Creator Fund (Module 27): funding programs, eligibility-based
applications, and admin approve/reject decisions.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10.
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4

from app.models import User, UserRole, Video, VideoStatus, Follow


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


async def _make_program(test_client, admin_token, **overrides):
    data = {
        "name": "Rising Creators Fund",
        "description": "For creators just getting started",
        "min_followers": 2,
        "min_published_videos": 1,
        "min_total_views": 100,
        "award_amount": 50000,
    }
    data.update(overrides)
    response = await test_client.post(
        "/api/creator-fund/programs", json=data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    return response.json()


async def _make_video(test_db, user_id, views_count=0):
    video = Video(
        user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
        title="Fund test video",
        video_url="https://example.com/fundtest.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
        views_count=views_count,
    )
    test_db.add(video)
    await test_db.commit()
    await test_db.refresh(video)
    return video


async def _make_follows(test_client, register_user_data, test_db, following_id, count):
    """Followers must be real users - the SQLite test fixture enforces
    foreign keys, so a Follow row can't reference a nonexistent user."""
    for i in range(count):
        _, follower_id = await _register(
            test_client, register_user_data, f"follower{i}_{following_id}@example.com", f"follower{i}{following_id[:8]}"
        )
        follow = Follow(follower_id=UUID(follower_id), following_id=UUID(following_id), is_active=True)
        test_db.add(follow)
    await test_db.commit()


@pytest.mark.asyncio
async def test_non_admin_cannot_create_program(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadminfund@example.com", "notadminfunduser")
    response = await test_client.post(
        "/api/creator-fund/programs",
        json={"name": "X", "award_amount": 100},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_and_list_program(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "createfundadmin@example.com", "createfundadminuser")
    await _make_admin(test_db, admin_id)

    program = await _make_program(test_client, admin_token, name="Listable Fund")
    assert program["name"] == "Listable Fund"
    assert program["is_active"] is True

    response = await test_client.get("/api/creator-fund/programs")
    assert response.status_code == 200
    names = [p["name"] for p in response.json()["programs"]]
    assert "Listable Fund" in names


@pytest.mark.asyncio
async def test_apply_meets_requirements(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "meetsadmin@example.com", "meetsadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, creator_id = await _register(test_client, register_user_data, "meetscreator@example.com", "meetscreatoruser")

    program = await _make_program(test_client, admin_token, name="Meets Fund")
    await _make_follows(test_client, register_user_data, test_db, creator_id, 3)
    await _make_video(test_db, creator_id, views_count=150)

    response = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meets_requirements"] is True
    assert data["followers_count"] == 3
    assert data["published_videos_count"] == 1
    assert data["total_views_count"] == 150
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_apply_does_not_meet_requirements(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "failsadmin@example.com", "failsadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, creator_id = await _register(test_client, register_user_data, "failscreator@example.com", "failscreatoruser")

    program = await _make_program(test_client, admin_token, name="Fails Fund")

    response = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meets_requirements"] is False
    assert data["followers_count"] == 0


@pytest.mark.asyncio
async def test_cannot_apply_twice(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "twiceadmin@example.com", "twiceadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "twicecreator@example.com", "twicecreatoruser")

    program = await _make_program(test_client, admin_token, name="Twice Fund")
    first = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert first.status_code == 200

    second = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_cannot_apply_to_inactive_program(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "inactiveadmin@example.com", "inactiveadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "inactivecreator@example.com", "inactivecreatoruser")

    response = await test_client.post(
        f"/api/creator-fund/programs/{uuid4()}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_apply_requires_auth(test_client: AsyncClient):
    response = await test_client.post(f"/api/creator-fund/programs/{uuid4()}/apply")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_my_applications(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "mineadmin@example.com", "mineadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "minecreator@example.com", "minecreatoruser")

    program = await _make_program(test_client, admin_token, name="Mine Fund")
    await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )

    response = await test_client.get(
        "/api/creator-fund/me/applications", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["program_id"] == program["id"]


@pytest.mark.asyncio
async def test_admin_can_approve_application_and_it_awards_amount(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "approveadmin@example.com", "approveadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, creator_id = await _register(test_client, register_user_data, "approvecreator@example.com", "approvecreatoruser")

    program = await _make_program(test_client, admin_token, name="Approve Fund", award_amount=75000)
    apply_response = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    application_id = apply_response.json()["id"]

    decide_response = await test_client.post(
        f"/api/creator-fund/admin/applications/{application_id}/decide",
        json={"status": "approved", "decision_reason": "Great potential"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert decide_response.status_code == 200
    data = decide_response.json()
    assert data["status"] == "approved"
    assert data["awarded_amount"] == 75000
    assert data["decision_reason"] == "Great potential"
    assert data["reviewed_by"] == admin_id


@pytest.mark.asyncio
async def test_admin_can_reject_application(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "rejectadmin@example.com", "rejectadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "rejectcreator@example.com", "rejectcreatoruser")

    program = await _make_program(test_client, admin_token, name="Reject Fund")
    apply_response = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    application_id = apply_response.json()["id"]

    decide_response = await test_client.post(
        f"/api/creator-fund/admin/applications/{application_id}/decide",
        json={"status": "rejected", "decision_reason": "Doesn't meet requirements"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert decide_response.status_code == 200
    data = decide_response.json()
    assert data["status"] == "rejected"
    assert data["awarded_amount"] is None


@pytest.mark.asyncio
async def test_cannot_decide_application_twice(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "twicedecideadmin@example.com", "twicedecideadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "twicedecidecreator@example.com", "twicedecidecreatoruser")

    program = await _make_program(test_client, admin_token, name="Twice Decide Fund")
    apply_response = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    application_id = apply_response.json()["id"]

    await test_client.post(
        f"/api/creator-fund/admin/applications/{application_id}/decide",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    second = await test_client.post(
        f"/api/creator-fund/admin/applications/{application_id}/decide",
        json={"status": "rejected"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_cannot_list_or_decide_applications(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadminlistfund@example.com", "notadminlistfunduser")

    list_response = await test_client.get(
        "/api/creator-fund/admin/applications", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 403

    decide_response = await test_client.post(
        f"/api/creator-fund/admin/applications/{uuid4()}/decide",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert decide_response.status_code == 403


@pytest.mark.asyncio
async def test_decision_status_must_not_be_pending(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "pendingdecideadmin@example.com", "pendingdecideadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "pendingdecidecreator@example.com", "pendingdecidecreatoruser")

    program = await _make_program(test_client, admin_token, name="Pending Decide Fund")
    apply_response = await test_client.post(
        f"/api/creator-fund/programs/{program['id']}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    application_id = apply_response.json()["id"]

    response = await test_client.post(
        f"/api/creator-fund/admin/applications/{application_id}/decide",
        json={"status": "pending"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422
