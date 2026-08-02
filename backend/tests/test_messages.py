"""
Tests for direct messaging (Module 14).

Written HTTP-level from the start (via test_client) - the established
rule since Module 10, since every prior module's real bugs were only
ever caught once something actually issued a real HTTP request.
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
async def test_start_conversation(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm1@example.com", "dm1user")
    _, user_b_id = await _register(test_client, register_user_data, "dm2@example.com", "dm2user")

    response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["other_user"]["id"] == user_b_id
    assert data["unread_count"] == 0
    assert data["last_message"] is None


@pytest.mark.asyncio
async def test_start_conversation_is_idempotent(test_client: AsyncClient, register_user_data):
    """Starting a conversation twice with the same user must return the
    same conversation, not create a duplicate."""
    token_a, _ = await _register(test_client, register_user_data, "dm3@example.com", "dm3user")
    _, user_b_id = await _register(test_client, register_user_data, "dm4@example.com", "dm4user")

    first = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    second = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_conversation_same_regardless_of_who_starts_it(test_client: AsyncClient, register_user_data):
    token_a, user_a_id = await _register(test_client, register_user_data, "dm5@example.com", "dm5user")
    token_b, user_b_id = await _register(test_client, register_user_data, "dm6@example.com", "dm6user")

    from_a = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    from_b = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_a_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert from_a.json()["id"] == from_b.json()["id"]


@pytest.mark.asyncio
async def test_cannot_message_self(test_client: AsyncClient, register_user_data):
    token, user_id = await _register(test_client, register_user_data, "dm7@example.com", "dm7user")

    response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_send_and_list_messages(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm8@example.com", "dm8user")
    token_b, user_b_id = await _register(test_client, register_user_data, "dm9@example.com", "dm9user")

    conv_response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conversation_id = conv_response.json()["id"]

    send_response = await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "Hey there!"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert send_response.status_code == 201
    assert send_response.json()["content"] == "Hey there!"
    assert send_response.json()["is_read"] is False

    list_response = await test_client.get(
        f"/api/messages/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_response.status_code == 200
    messages = list_response.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["content"] == "Hey there!"


@pytest.mark.asyncio
async def test_messages_ordered_oldest_first(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm10@example.com", "dm10user")
    _, user_b_id = await _register(test_client, register_user_data, "dm11@example.com", "dm11user")

    conv_response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conversation_id = conv_response.json()["id"]

    await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "First"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "Second"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response = await test_client.get(
        f"/api/messages/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    messages = response.json()["messages"]
    assert [m["content"] for m in messages] == ["First", "Second"]


@pytest.mark.asyncio
async def test_non_participant_cannot_read_or_send(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm12@example.com", "dm12user")
    _, user_b_id = await _register(test_client, register_user_data, "dm13@example.com", "dm13user")
    token_c, _ = await _register(test_client, register_user_data, "dm14@example.com", "dm14user")

    conv_response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conversation_id = conv_response.json()["id"]

    read_response = await test_client.get(
        f"/api/messages/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token_c}"},
    )
    assert read_response.status_code == 403

    send_response = await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "Intruding"},
        headers={"Authorization": f"Bearer {token_c}"},
    )
    assert send_response.status_code == 403


@pytest.mark.asyncio
async def test_blocked_user_cannot_start_conversation(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm15@example.com", "dm15user")
    token_b, user_b_id = await _register(test_client, register_user_data, "dm16@example.com", "dm16user")

    await test_client.post(
        f"/api/profiles/{user_b_id}/block", headers={"Authorization": f"Bearer {token_a}"}
    )

    response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_blocking_mid_conversation_stops_new_messages(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm17@example.com", "dm17user")
    token_b, user_b_id = await _register(test_client, register_user_data, "dm18@example.com", "dm18user")

    conv_response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conversation_id = conv_response.json()["id"]
    await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "Before block"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    await test_client.post(
        f"/api/profiles/{user_b_id}/block", headers={"Authorization": f"Bearer {token_a}"}
    )

    response = await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "After block"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_mark_conversation_read(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm19@example.com", "dm19user")
    token_b, user_b_id = await _register(test_client, register_user_data, "dm20@example.com", "dm20user")

    conv_response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conversation_id = conv_response.json()["id"]
    await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "Unread message"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    unread_check = await test_client.get(
        "/api/messages/conversations", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert unread_check.json()["conversations"][0]["unread_count"] == 1

    read_response = await test_client.put(
        f"/api/messages/conversations/{conversation_id}/read",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert read_response.status_code == 200
    assert read_response.json()["count"] == 1

    after_read = await test_client.get(
        "/api/messages/conversations", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert after_read.json()["conversations"][0]["unread_count"] == 0


@pytest.mark.asyncio
async def test_conversations_list_shows_last_message_and_ordering(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm21@example.com", "dm21user")
    _, user_b_id = await _register(test_client, register_user_data, "dm22@example.com", "dm22user")
    _, user_c_id = await _register(test_client, register_user_data, "dm23@example.com", "dm23user")

    conv_b = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conv_c = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_c_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Message in conv_b, then a later message in conv_c - conv_c should
    # now sort first (most recently active).
    await test_client.post(
        f"/api/messages/conversations/{conv_b.json()['id']}/messages",
        json={"content": "To B"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    await test_client.post(
        f"/api/messages/conversations/{conv_c.json()['id']}/messages",
        json={"content": "To C"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response = await test_client.get(
        "/api/messages/conversations", headers={"Authorization": f"Bearer {token_a}"}
    )
    conversations = response.json()["conversations"]
    assert conversations[0]["other_user"]["id"] == user_c_id
    assert conversations[0]["last_message"]["content"] == "To C"
    assert conversations[1]["other_user"]["id"] == user_b_id


@pytest.mark.asyncio
async def test_message_triggers_notification(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm24@example.com", "dm24user")
    token_b, user_b_id = await _register(test_client, register_user_data, "dm25@example.com", "dm25user")

    conv_response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conversation_id = conv_response.json()["id"]

    await test_client.post(
        f"/api/messages/conversations/{conversation_id}/messages",
        json={"content": "Notify me"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token_b}"}
    )
    data = notif_response.json()
    assert data["total"] == 1
    assert data["notifications"][0]["type"] == "message"


@pytest.mark.asyncio
async def test_get_messages_requires_auth(test_client: AsyncClient, register_user_data):
    token_a, _ = await _register(test_client, register_user_data, "dm26@example.com", "dm26user")
    _, user_b_id = await _register(test_client, register_user_data, "dm27@example.com", "dm27user")

    conv_response = await test_client.post(
        "/api/messages/conversations",
        params={"recipient_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    conversation_id = conv_response.json()["id"]

    response = await test_client.get(f"/api/messages/conversations/{conversation_id}/messages")
    assert response.status_code == 401
