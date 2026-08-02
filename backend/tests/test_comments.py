"""
Tests for the comments & replies system (Module 11).

Written HTTP-level from the start (via test_client) - every prior module's
real bugs (route-order conflicts, response schemas that don't match the
model, response builders that never populate required nested fields) were
only ever caught once something actually issued a real HTTP request.
"""

import pytest
from httpx import AsyncClient
from uuid import UUID


async def _register(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


async def _make_video(test_db, user_id, allow_comments=True):
    from app.models import Video, VideoStatus

    video = Video(
        user_id=UUID(user_id),
        title="Test video",
        video_url="https://example.com/v.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
        allow_comments=allow_comments,
    )
    test_db.add(video)
    await test_db.commit()
    await test_db.refresh(video)
    return video


@pytest.mark.asyncio
async def test_create_comment(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(
        test_client, register_user_data, "ccreator@example.com", "ccreatoruser"
    )
    commenter_token, _ = await _register(
        test_client, register_user_data, "ccommenter@example.com", "ccommenteruser"
    )
    video = await _make_video(test_db, creator_id)

    response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Nice video!"},
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Nice video!"
    assert data["parent_comment_id"] is None
    assert data["likes_count"] == 0
    assert data["replies_count"] == 0
    assert data["is_liked"] is False
    assert data["user"]["username"] == "ccommenteruser"


@pytest.mark.asyncio
async def test_create_comment_requires_auth(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "noauth1@example.com", "noauth1user")
    video = await _make_video(test_db, creator_id)

    response = await test_client.post(
        f"/api/videos/{video.id}/comments", json={"content": "hi"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_comments_disabled_rejected(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(
        test_client, register_user_data, "disabled1@example.com", "disabled1user"
    )
    commenter_token, _ = await _register(
        test_client, register_user_data, "disabled2@example.com", "disabled2user"
    )
    video = await _make_video(test_db, creator_id, allow_comments=False)

    response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "hi"},
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_reply(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "reply1@example.com", "reply1user")
    token_a, _ = await _register(test_client, register_user_data, "reply2@example.com", "reply2user")
    token_b, _ = await _register(test_client, register_user_data, "reply3@example.com", "reply3user")
    video = await _make_video(test_db, creator_id)

    top_response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Top level"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    top_id = top_response.json()["id"]

    reply_response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "A reply", "parent_comment_id": top_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert reply_response.status_code == 201
    assert reply_response.json()["parent_comment_id"] == top_id

    # parent's replies_count should now be reflected in the list
    list_response = await test_client.get(f"/api/videos/{video.id}/comments")
    assert list_response.json()["comments"][0]["replies_count"] == 1


@pytest.mark.asyncio
async def test_reply_to_reply_rejected(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "nested1@example.com", "nested1user")
    token_a, _ = await _register(test_client, register_user_data, "nested2@example.com", "nested2user")
    video = await _make_video(test_db, creator_id)

    top_response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Top"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    top_id = top_response.json()["id"]

    reply_response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Reply", "parent_comment_id": top_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    reply_id = reply_response.json()["id"]

    nested_response = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Nested reply", "parent_comment_id": reply_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert nested_response.status_code == 400


@pytest.mark.asyncio
async def test_list_top_level_comments_pinned_first(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(
        test_client, register_user_data, "pin1@example.com", "pin1user"
    )
    token_a, _ = await _register(test_client, register_user_data, "pin2@example.com", "pin2user")
    video = await _make_video(test_db, creator_id)

    first = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "First"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    second = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Second"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    first_id = first.json()["id"]

    # Pin the first (older) comment as the video owner
    pin_response = await test_client.post(
        f"/api/comments/{first_id}/pin", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert pin_response.status_code == 200
    assert pin_response.json()["is_pinned"] is True

    list_response = await test_client.get(f"/api/videos/{video.id}/comments")
    comments = list_response.json()["comments"]
    assert comments[0]["id"] == first_id
    assert comments[0]["is_pinned"] is True
    assert comments[1]["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_get_replies_oldest_first(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "order1@example.com", "order1user")
    token_a, _ = await _register(test_client, register_user_data, "order2@example.com", "order2user")
    video = await _make_video(test_db, creator_id)

    top = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Top"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    top_id = top.json()["id"]

    reply1 = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "First reply", "parent_comment_id": top_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    reply2 = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Second reply", "parent_comment_id": top_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    replies_response = await test_client.get(f"/api/comments/{top_id}/replies")
    replies = replies_response.json()["comments"]
    assert replies[0]["id"] == reply1.json()["id"]
    assert replies[1]["id"] == reply2.json()["id"]


@pytest.mark.asyncio
async def test_edit_own_comment(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "edit1@example.com", "edit1user")
    token_a, _ = await _register(test_client, register_user_data, "edit2@example.com", "edit2user")
    video = await _make_video(test_db, creator_id)

    created = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Original"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    comment_id = created.json()["id"]

    edit_response = await test_client.put(
        f"/api/comments/{comment_id}",
        json={"content": "Edited"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["content"] == "Edited"


@pytest.mark.asyncio
async def test_edit_others_comment_rejected(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "edit3@example.com", "edit3user")
    token_a, _ = await _register(test_client, register_user_data, "edit4@example.com", "edit4user")
    token_b, _ = await _register(test_client, register_user_data, "edit5@example.com", "edit5user")
    video = await _make_video(test_db, creator_id)

    created = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Original"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    comment_id = created.json()["id"]

    edit_response = await test_client.put(
        f"/api/comments/{comment_id}",
        json={"content": "Hijacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert edit_response.status_code == 400


@pytest.mark.asyncio
async def test_delete_own_comment(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "del1@example.com", "del1user")
    token_a, _ = await _register(test_client, register_user_data, "del2@example.com", "del2user")
    video = await _make_video(test_db, creator_id)

    created = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Delete me"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    comment_id = created.json()["id"]

    delete_response = await test_client.delete(
        f"/api/comments/{comment_id}", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert delete_response.status_code == 200

    list_response = await test_client.get(f"/api/videos/{video.id}/comments")
    assert list_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_video_owner_can_delete_any_comment(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(
        test_client, register_user_data, "del3@example.com", "del3user"
    )
    token_a, _ = await _register(test_client, register_user_data, "del4@example.com", "del4user")
    video = await _make_video(test_db, creator_id)

    created = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Moderate me"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    comment_id = created.json()["id"]

    delete_response = await test_client.delete(
        f"/api/comments/{comment_id}", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_delete_others_comment_rejected(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "del5@example.com", "del5user")
    token_a, _ = await _register(test_client, register_user_data, "del6@example.com", "del6user")
    token_b, _ = await _register(test_client, register_user_data, "del7@example.com", "del7user")
    video = await _make_video(test_db, creator_id)

    created = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Not yours"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    comment_id = created.json()["id"]

    delete_response = await test_client.delete(
        f"/api/comments/{comment_id}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert delete_response.status_code == 400


@pytest.mark.asyncio
async def test_toggle_like_comment(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "like1@example.com", "like1user")
    token_a, _ = await _register(test_client, register_user_data, "like2@example.com", "like2user")
    token_b, _ = await _register(test_client, register_user_data, "like3@example.com", "like3user")
    video = await _make_video(test_db, creator_id)

    created = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Like me"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    comment_id = created.json()["id"]

    like_response = await test_client.post(
        f"/api/comments/{comment_id}/like", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert like_response.status_code == 200
    assert like_response.json()["is_liked"] is True
    assert like_response.json()["likes_count"] == 1

    unlike_response = await test_client.post(
        f"/api/comments/{comment_id}/like", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert unlike_response.json()["is_liked"] is False
    assert unlike_response.json()["likes_count"] == 0


@pytest.mark.asyncio
async def test_pin_requires_video_owner(test_client: AsyncClient, test_db, register_user_data):
    _, creator_id = await _register(test_client, register_user_data, "pinauth1@example.com", "pinauth1user")
    token_a, _ = await _register(test_client, register_user_data, "pinauth2@example.com", "pinauth2user")
    video = await _make_video(test_db, creator_id)

    created = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Pin attempt"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    comment_id = created.json()["id"]

    pin_response = await test_client.post(
        f"/api/comments/{comment_id}/pin", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert pin_response.status_code == 400


@pytest.mark.asyncio
async def test_reply_cannot_be_pinned(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(
        test_client, register_user_data, "pinauth3@example.com", "pinauth3user"
    )
    token_a, _ = await _register(test_client, register_user_data, "pinauth4@example.com", "pinauth4user")
    video = await _make_video(test_db, creator_id)

    top = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Top"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    top_id = top.json()["id"]
    reply = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Reply", "parent_comment_id": top_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    reply_id = reply.json()["id"]

    pin_response = await test_client.post(
        f"/api/comments/{reply_id}/pin", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert pin_response.status_code == 400


@pytest.mark.asyncio
async def test_top_level_comment_notifies_video_owner(test_client: AsyncClient, test_db, register_user_data):
    creator_token, creator_id = await _register(
        test_client, register_user_data, "notify1@example.com", "notify1user"
    )
    token_a, _ = await _register(test_client, register_user_data, "notify2@example.com", "notify2user")
    video = await _make_video(test_db, creator_id)

    await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Great content"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {creator_token}"}
    )
    data = notif_response.json()
    assert data["total"] == 1
    assert data["notifications"][0]["type"] == "comment"


@pytest.mark.asyncio
async def test_reply_notifies_parent_author_not_video_owner(
    test_client: AsyncClient, test_db, register_user_data
):
    creator_token, creator_id = await _register(
        test_client, register_user_data, "notify3@example.com", "notify3user"
    )
    token_a, _ = await _register(test_client, register_user_data, "notify4@example.com", "notify4user")
    token_b, _ = await _register(test_client, register_user_data, "notify5@example.com", "notify5user")
    video = await _make_video(test_db, creator_id)

    top = await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Top"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    top_id = top.json()["id"]

    # clear the video owner's comment notification from the top-level comment
    await test_client.put(
        "/api/notifications/read-all", headers={"Authorization": f"Bearer {creator_token}"}
    )

    await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "A reply", "parent_comment_id": top_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # parent comment author (token_a / notify4user) should get a REPLY notification
    parent_notif = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token_a}"}
    )
    parent_data = parent_notif.json()
    assert parent_data["total"] == 1
    assert parent_data["notifications"][0]["type"] == "reply"

    # video owner should NOT get a second notification for the reply
    owner_notif = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert owner_notif.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_self_comment_does_not_notify_self(test_client: AsyncClient, test_db, register_user_data):
    token, user_id = await _register(test_client, register_user_data, "notify6@example.com", "notify6user")
    video = await _make_video(test_db, user_id)

    await test_client.post(
        f"/api/videos/{video.id}/comments",
        json={"content": "Commenting on my own video"},
        headers={"Authorization": f"Bearer {token}"},
    )

    notif_response = await test_client.get(
        "/api/notifications", headers={"Authorization": f"Bearer {token}"}
    )
    assert notif_response.json()["total"] == 0
