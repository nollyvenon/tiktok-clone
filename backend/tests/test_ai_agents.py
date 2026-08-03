"""
Tests for AI Agents (Module 28): named recipes that chain existing AI
Creator Studio operations into a single one-click run against a segment.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10. NOTE: written but not yet run - the user
paused test/build verification mid-session (2026-08-03) until the whole
app is declared complete; these will be run in that deferred pass.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


async def _register_with_segment(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    access_token = response.json()["access_token"]

    response = await test_client.post(
        "/api/uploads/drafts",
        json={"title": "Agent Test Video"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    draft_id = response.json()["id"]

    response = await test_client.post(
        f"/api/editor/drafts/{draft_id}/segments",
        json={
            "start_time": 0,
            "end_time": 5000,
            "content_type": "video",
            "content_url": "https://example.com/video.mp4",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    segment_id = response.json()["id"]
    return access_token, segment_id


@pytest.mark.asyncio
async def test_list_agents(test_client: AsyncClient):
    """Agents are public and seeded on first request"""
    response = await test_client.get("/api/ai/agents")
    assert response.status_code == 200
    data = response.json()
    names = [a["name"] for a in data["agents"]]
    assert "auto_polish" in names
    assert "caption_and_clean" in names
    assert "full_enhance" in names
    # Each agent's steps are exposed so a client can show what will run
    auto_polish = next(a for a in data["agents"] if a["name"] == "auto_polish")
    assert len(auto_polish["steps"]) == 2


@pytest.mark.asyncio
async def test_execute_agent_runs_every_step(test_client: AsyncClient, register_user_data):
    """Executing 'full_enhance' should run all four underlying AI operations"""
    access_token, segment_id = await _register_with_segment(
        test_client, register_user_data, "agentfull@example.com", "agentfulluser"
    )

    agents_response = await test_client.get("/api/ai/agents")
    full_enhance = next(a for a in agents_response.json()["agents"] if a["name"] == "full_enhance")

    response = await test_client.post(
        f"/api/ai/agents/{full_enhance['id']}/execute",
        params={"segment_id": segment_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["steps_log"]) == 4
    assert all(step["status"] == "completed" for step in data["steps_log"])
    assert data["total_credits_used"] > 0
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_execute_agent_requires_video_ownership(test_client: AsyncClient, register_user_data):
    _, segment_id = await _register_with_segment(
        test_client, register_user_data, "agentowner@example.com", "agentowneruser"
    )
    intruder_data = dict(register_user_data)
    intruder_data["email"] = "agentintruder@example.com"
    intruder_data["username"] = "agentintruderuser"
    intruder_response = await test_client.post("/api/auth/register", json=intruder_data)
    intruder_token = intruder_response.json()["access_token"]

    agents_response = await test_client.get("/api/ai/agents")
    agent_id = agents_response.json()["agents"][0]["id"]

    response = await test_client.post(
        f"/api/ai/agents/{agent_id}/execute",
        params={"segment_id": segment_id},
        headers={"Authorization": f"Bearer {intruder_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_execute_agent_rejects_nonexistent_segment(test_client: AsyncClient, register_user_data):
    response = await test_client.post("/api/auth/register", json=register_user_data)
    access_token = response.json()["access_token"]

    agents_response = await test_client.get("/api/ai/agents")
    agent_id = agents_response.json()["agents"][0]["id"]

    response = await test_client.post(
        f"/api/ai/agents/{agent_id}/execute",
        params={"segment_id": str(uuid4())},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_execute_nonexistent_agent_rejected(test_client: AsyncClient, register_user_data):
    access_token, segment_id = await _register_with_segment(
        test_client, register_user_data, "agentmissing@example.com", "agentmissinguser"
    )

    response = await test_client.post(
        f"/api/ai/agents/{uuid4()}/execute",
        params={"segment_id": segment_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_execute_agent_requires_auth(test_client: AsyncClient):
    response = await test_client.post(
        f"/api/ai/agents/{uuid4()}/execute",
        params={"segment_id": str(uuid4())},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_my_agent_executions(test_client: AsyncClient, register_user_data):
    access_token, segment_id = await _register_with_segment(
        test_client, register_user_data, "agenthistory@example.com", "agenthistoryuser"
    )

    agents_response = await test_client.get("/api/ai/agents")
    agent_id = agents_response.json()["agents"][0]["id"]

    await test_client.post(
        f"/api/ai/agents/{agent_id}/execute",
        params={"segment_id": segment_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    response = await test_client.get(
        "/api/ai/agents/executions", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    executions = response.json()["executions"]
    assert len(executions) == 1
    assert executions[0]["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_list_my_agent_executions_requires_auth(test_client: AsyncClient):
    response = await test_client.get("/api/ai/agents/executions")
    assert response.status_code == 401
