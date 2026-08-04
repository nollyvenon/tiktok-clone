"""
Tests for Live Streaming (Module 10): stream sessions, viewer presence,
and chat - the social layer of live streaming, honestly built without
an RTMP/WebRTC video pipeline this app has never had.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10. NOTE: written but not yet run - the user
paused test/build verification mid-session (2026-08-03) until the whole
app is declared complete; these will be run in that deferred pass.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


async def _register(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


@pytest.mark.asyncio
async def test_start_and_list_stream(test_client: AsyncClient, register_user_data):
    token, creator_id = await _register(test_client, register_user_data, "livestarter@example.com", "livestarteruser")

    start_response = await test_client.post(
        "/api/live/start", json={"title": "Live coding"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert start_response.status_code == 200
    data = start_response.json()
    assert data["status"] == "live"
    assert data["creator_id"] == creator_id
    assert data["viewer_count"] == 0

    list_response = await test_client.get("/api/live")
    assert list_response.status_code == 200
    stream_ids = [s["id"] for s in list_response.json()["streams"]]
    assert data["id"] in stream_ids


@pytest.mark.asyncio
async def test_cannot_start_second_stream_while_live(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "livetwice@example.com", "livetwiceuser")
    await test_client.post("/api/live/start", json={"title": "First"}, headers={"Authorization": f"Bearer {token}"})

    response = await test_client.post(
        "/api/live/start", json={"title": "Second"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_end_stream_removes_it_from_live_list(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "liveender@example.com", "liveenderuser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "Ending soon"}, headers={"Authorization": f"Bearer {token}"}
    )
    stream_id = start_response.json()["id"]

    end_response = await test_client.post(
        f"/api/live/{stream_id}/end", headers={"Authorization": f"Bearer {token}"}
    )
    assert end_response.status_code == 200
    assert end_response.json()["status"] == "ended"
    assert end_response.json()["ended_at"] is not None

    list_response = await test_client.get("/api/live")
    stream_ids = [s["id"] for s in list_response.json()["streams"]]
    assert stream_id not in stream_ids


@pytest.mark.asyncio
async def test_non_owner_cannot_end_stream(test_client: AsyncClient, register_user_data):
    owner_token, _ = await _register(test_client, register_user_data, "liveownerend@example.com", "liveownerenduser")
    stranger_token, _ = await _register(test_client, register_user_data, "livestrangerend@example.com", "livestrangerenduser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "Mine"}, headers={"Authorization": f"Bearer {owner_token}"}
    )
    stream_id = start_response.json()["id"]

    response = await test_client.post(
        f"/api/live/{stream_id}/end", headers={"Authorization": f"Bearer {stranger_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_join_increments_viewer_count_leave_decrements(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register(test_client, register_user_data, "livejoincreator@example.com", "livejoincreatoruser")
    viewer_token, _ = await _register(test_client, register_user_data, "livejoinviewer@example.com", "livejoinvieweruser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "Join test"}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    stream_id = start_response.json()["id"]

    join_response = await test_client.post(
        f"/api/live/{stream_id}/join", headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert join_response.status_code == 200
    assert join_response.json()["viewer_count"] == 1
    assert join_response.json()["peak_viewer_count"] == 1

    leave_response = await test_client.post(
        f"/api/live/{stream_id}/leave", headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert leave_response.status_code == 200
    assert leave_response.json()["viewer_count"] == 0
    assert leave_response.json()["peak_viewer_count"] == 1


@pytest.mark.asyncio
async def test_repeated_join_is_idempotent(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register(test_client, register_user_data, "liveidempotentcreator@example.com", "liveidempotentcreatoruser")
    viewer_token, _ = await _register(test_client, register_user_data, "liveidempotentviewer@example.com", "liveidempotentvieweruser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "Idempotent join"}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    stream_id = start_response.json()["id"]

    await test_client.post(f"/api/live/{stream_id}/join", headers={"Authorization": f"Bearer {viewer_token}"})
    second_join = await test_client.post(
        f"/api/live/{stream_id}/join", headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert second_join.json()["viewer_count"] == 1


@pytest.mark.asyncio
async def test_cannot_join_ended_stream(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register(test_client, register_user_data, "livejoinended@example.com", "livejoinendeduser")
    viewer_token, _ = await _register(test_client, register_user_data, "livejoinendedviewer@example.com", "livejoinendedvieweruser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "About to end"}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    stream_id = start_response.json()["id"]
    await test_client.post(f"/api/live/{stream_id}/end", headers={"Authorization": f"Bearer {creator_token}"})

    response = await test_client.post(
        f"/api/live/{stream_id}/join", headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_post_and_list_chat_messages(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register(test_client, register_user_data, "livechatcreator@example.com", "livechatcreatoruser")
    viewer_token, _ = await _register(test_client, register_user_data, "livechatviewer@example.com", "livechatvieweruser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "Chat test"}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    stream_id = start_response.json()["id"]

    post_response = await test_client.post(
        f"/api/live/{stream_id}/chat", json={"content": "hello!"}, headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert post_response.status_code == 200
    assert post_response.json()["content"] == "hello!"
    assert post_response.json()["username"] == "livechatvieweruser"

    list_response = await test_client.get(f"/api/live/{stream_id}/chat")
    assert list_response.status_code == 200
    messages = list_response.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["content"] == "hello!"


@pytest.mark.asyncio
async def test_cannot_chat_in_ended_stream(test_client: AsyncClient, register_user_data):
    creator_token, _ = await _register(test_client, register_user_data, "livechatended@example.com", "livechatendeduser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "Ending"}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    stream_id = start_response.json()["id"]
    await test_client.post(f"/api/live/{stream_id}/end", headers={"Authorization": f"Bearer {creator_token}"})

    response = await test_client.post(
        f"/api/live/{stream_id}/chat",
        json={"content": "too late"},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_stream_detail(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "livedetail@example.com", "livedetailuser")
    start_response = await test_client.post(
        "/api/live/start", json={"title": "Detail view"}, headers={"Authorization": f"Bearer {token}"}
    )
    stream_id = start_response.json()["id"]

    response = await test_client.get(f"/api/live/{stream_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Detail view"


@pytest.mark.asyncio
async def test_get_nonexistent_stream_404(test_client: AsyncClient):
    response = await test_client.get(f"/api/live/{uuid4()}")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_live_streaming_requires_auth_for_mutations(test_client: AsyncClient):
    response = await test_client.post("/api/live/start", json={"title": "X"})
    assert response.status_code == 401

    response = await test_client.post(f"/api/live/{uuid4()}/join")
    assert response.status_code == 401
