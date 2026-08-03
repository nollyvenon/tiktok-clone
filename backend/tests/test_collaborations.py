"""
Tests for Collaborations (Module 29): team content creation with an
agreed-upfront revenue split, invite/accept/decline, and cancellation.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10.
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4

from app.models import Video, VideoStatus


async def _register(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


async def _make_video(test_db, user_id):
    video = Video(
        user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
        title="Collab test video",
        video_url="https://example.com/collabtest.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()
    await test_db.refresh(video)
    return video


@pytest.mark.asyncio
async def test_create_collaboration_requires_video_ownership(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "notownerA@example.com", "notownerauser")
    _, other_id = await _register(test_client, register_user_data, "notownerB@example.com", "notownerbuser")
    video = await _make_video(test_db, other_id)

    response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [{"user_id": owner_id, "revenue_split_percent": 100}],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_collaboration_requires_splits_sum_to_100(test_client: AsyncClient, test_db, register_user_data):
    token, user_id = await _register(test_client, register_user_data, "badsplit@example.com", "badsplituser")
    video = await _make_video(test_db, user_id)

    response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [{"user_id": user_id, "revenue_split_percent": 60}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_collaboration_requires_initiator_included(test_client: AsyncClient, test_db, register_user_data):
    token, user_id = await _register(test_client, register_user_data, "noselfsplit@example.com", "noselfsplituser")
    _, other_id = await _register(test_client, register_user_data, "otherselfsplit@example.com", "otherselfsplituser")
    video = await _make_video(test_db, user_id)

    response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [{"user_id": other_id, "revenue_split_percent": 100}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_full_collaboration_workflow_to_active(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "flowowner@example.com", "flowowneruser")
    partner_token, partner_id = await _register(test_client, register_user_data, "flowpartner@example.com", "flowpartneruser")
    video = await _make_video(test_db, owner_id)

    create_response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "title": "Duet special",
            "collaborators": [
                {"user_id": owner_id, "revenue_split_percent": 60},
                {"user_id": partner_id, "revenue_split_percent": 40},
            ],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_response.status_code == 200
    data = create_response.json()
    assert data["status"] == "pending"
    collaborators = {c["user_id"]: c for c in data["collaborators"]}
    assert collaborators[owner_id]["status"] == "accepted"
    assert collaborators[owner_id]["is_initiator"] is True
    assert collaborators[partner_id]["status"] == "invited"
    collaboration_id = data["id"]

    respond_response = await test_client.post(
        f"/api/collaborations/{collaboration_id}/respond",
        json={"accept": True},
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_declining_cancels_the_collaboration(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "declineowner@example.com", "declineowneruser")
    partner_token, partner_id = await _register(test_client, register_user_data, "declinepartner@example.com", "declinepartneruser")
    video = await _make_video(test_db, owner_id)

    create_response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [
                {"user_id": owner_id, "revenue_split_percent": 50},
                {"user_id": partner_id, "revenue_split_percent": 50},
            ],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    collaboration_id = create_response.json()["id"]

    respond_response = await test_client.post(
        f"/api/collaborations/{collaboration_id}/respond",
        json={"accept": False},
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_uninvited_user_cannot_respond(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "uninvitedowner@example.com", "uninvitedowneruser")
    _, stranger_id = await _register(test_client, register_user_data, "strangerresp@example.com", "strangerrespuser")
    stranger_token, _ = await _register(test_client, register_user_data, "strangertoken@example.com", "strangertokenuser")
    video = await _make_video(test_db, owner_id)

    create_response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [{"user_id": owner_id, "revenue_split_percent": 100}],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    collaboration_id = create_response.json()["id"]

    response = await test_client.post(
        f"/api/collaborations/{collaboration_id}/respond",
        json={"accept": True},
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_respond_twice(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "twicerespowner@example.com", "twicerespowneruser")
    partner_token, partner_id = await _register(test_client, register_user_data, "twicerespartner@example.com", "twicerespartneruser")
    video = await _make_video(test_db, owner_id)

    create_response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [
                {"user_id": owner_id, "revenue_split_percent": 50},
                {"user_id": partner_id, "revenue_split_percent": 50},
            ],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    collaboration_id = create_response.json()["id"]

    await test_client.post(
        f"/api/collaborations/{collaboration_id}/respond",
        json={"accept": True},
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    second = await test_client.post(
        f"/api/collaborations/{collaboration_id}/respond",
        json={"accept": True},
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_initiator_can_cancel_pending_collaboration(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "cancelowner@example.com", "cancelowneruser")
    _, partner_id = await _register(test_client, register_user_data, "cancelpartner@example.com", "cancelpartneruser")
    video = await _make_video(test_db, owner_id)

    create_response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [
                {"user_id": owner_id, "revenue_split_percent": 50},
                {"user_id": partner_id, "revenue_split_percent": 50},
            ],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    collaboration_id = create_response.json()["id"]

    cancel_response = await test_client.post(
        f"/api/collaborations/{collaboration_id}/cancel",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_non_initiator_cannot_cancel(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "nocancelowner@example.com", "nocancelowneruser")
    partner_token, partner_id = await _register(test_client, register_user_data, "nocancelpartner@example.com", "nocancelpartneruser")
    video = await _make_video(test_db, owner_id)

    create_response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [
                {"user_id": owner_id, "revenue_split_percent": 50},
                {"user_id": partner_id, "revenue_split_percent": 50},
            ],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    collaboration_id = create_response.json()["id"]

    response = await test_client.post(
        f"/api/collaborations/{collaboration_id}/cancel",
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_my_collaborations_includes_both_roles(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "listowner@example.com", "listowneruser")
    partner_token, partner_id = await _register(test_client, register_user_data, "listpartner@example.com", "listpartneruser")
    video = await _make_video(test_db, owner_id)

    await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [
                {"user_id": owner_id, "revenue_split_percent": 70},
                {"user_id": partner_id, "revenue_split_percent": 30},
            ],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    owner_list = await test_client.get("/api/collaborations/me", headers={"Authorization": f"Bearer {owner_token}"})
    partner_list = await test_client.get("/api/collaborations/me", headers={"Authorization": f"Bearer {partner_token}"})
    assert owner_list.status_code == 200
    assert partner_list.status_code == 200
    assert len(owner_list.json()) == 1
    assert len(partner_list.json()) == 1


@pytest.mark.asyncio
async def test_non_participant_cannot_view_collaboration(test_client: AsyncClient, test_db, register_user_data):
    owner_token, owner_id = await _register(test_client, register_user_data, "viewowner@example.com", "viewowneruser")
    stranger_token, _ = await _register(test_client, register_user_data, "viewstranger@example.com", "viewstrangeruser")
    video = await _make_video(test_db, owner_id)

    create_response = await test_client.post(
        "/api/collaborations",
        json={
            "video_id": str(video.id),
            "collaborators": [{"user_id": owner_id, "revenue_split_percent": 100}],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    collaboration_id = create_response.json()["id"]

    response = await test_client.get(
        f"/api/collaborations/{collaboration_id}", headers={"Authorization": f"Bearer {stranger_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_collaboration_requires_auth(test_client: AsyncClient):
    response = await test_client.post(
        "/api/collaborations",
        json={"video_id": str(uuid4()), "collaborators": [{"user_id": str(uuid4()), "revenue_split_percent": 100}]},
    )
    assert response.status_code == 401
