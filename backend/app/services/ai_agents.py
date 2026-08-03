"""
AI Agents service - named recipes that chain the existing AI Creator
Studio operations (background removal, captions, color correction,
smart framing) into a single one-click run against a segment.

This app has no real LLM/agent-framework integration anywhere (the
OPENAI_API_KEY config field is never actually used by any service), so
'agent execution' here orchestrates the AI operations that already
exist and are already fully built, rather than simulating free-form LLM
reasoning that wouldn't be honest to claim.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AIAgent, AgentExecution, AgentExecutionStatus
from app.schemas import (
    BackgroundRemovalRequest, AutoCaptionRequest, ColorCorrectionRequest,
)
from app.services.ai import AIService

logger = logging.getLogger(__name__)

# Canonical agents, seeded into the ai_agents table the first time it's
# queried empty - mirrors the FilterPreset seed-on-read pattern, so the
# SQLite test fixture (Base.metadata.create_all, no migration data) and a
# fresh Postgres deployment behave the same way.
DEFAULT_AGENTS = [
    {
        "name": "auto_polish",
        "label": "Auto Polish",
        "description": "Auto color correction plus smart framing for 9:16.",
        "steps": [
            {"operation": "color_correction", "params": {"method": "auto_enhance"}},
            {"operation": "smart_frame", "params": {"target_aspect_ratio": "9:16"}},
        ],
        "sort_order": 0,
    },
    {
        "name": "caption_and_clean",
        "label": "Caption & Clean",
        "description": "Auto captions plus a blurred background cleanup.",
        "steps": [
            {"operation": "caption", "params": {"language": "en", "style": "default"}},
            {"operation": "background_removal", "params": {"mode": "blur", "blur_level": 5}},
        ],
        "sort_order": 1,
    },
    {
        "name": "full_enhance",
        "label": "Full Enhance",
        "description": "Runs every AI Creator Studio operation in sequence: background cleanup, color correction, captions, and smart framing.",
        "steps": [
            {"operation": "background_removal", "params": {"mode": "blur", "blur_level": 5}},
            {"operation": "color_correction", "params": {"method": "auto_enhance"}},
            {"operation": "caption", "params": {"language": "en", "style": "default"}},
            {"operation": "smart_frame", "params": {"target_aspect_ratio": "9:16"}},
        ],
        "sort_order": 2,
    },
]


class AIAgentService:
    """Service for AI agent recipes and their executions"""

    @staticmethod
    async def list_agents(db: AsyncSession) -> List[dict]:
        """List active agents with parsed steps, seeding defaults if empty"""
        result = await db.execute(
            select(AIAgent).where(AIAgent.is_active == True).order_by(AIAgent.sort_order)
        )
        agents = list(result.scalars().all())

        if not agents:
            for agent_data in DEFAULT_AGENTS:
                db.add(AIAgent(
                    name=agent_data["name"],
                    label=agent_data["label"],
                    description=agent_data["description"],
                    steps=json.dumps(agent_data["steps"]),
                    sort_order=agent_data["sort_order"],
                ))
            await db.commit()
            result = await db.execute(
                select(AIAgent).where(AIAgent.is_active == True).order_by(AIAgent.sort_order)
            )
            agents = list(result.scalars().all())

        return [
            {
                "id": a.id,
                "name": a.name,
                "label": a.label,
                "description": a.description,
                "steps": json.loads(a.steps),
            }
            for a in agents
        ]

    @staticmethod
    async def _run_step(
        db: AsyncSession, user_id: UUID, segment_id: UUID, operation: str, params: dict
    ) -> Tuple[UUID, int]:
        """Run a single agent step via the existing AIService, returning
        (result_id, credits_used). Raises on failure or unknown operation."""
        if operation == "background_removal":
            result, ai_gen = await AIService.remove_background(
                db, user_id, segment_id,
                BackgroundRemovalRequest(segment_id=segment_id, **params),
            )
        elif operation == "caption":
            result, ai_gen = await AIService.generate_captions(
                db, user_id, segment_id,
                AutoCaptionRequest(segment_id=segment_id, **params),
            )
        elif operation == "color_correction":
            result, ai_gen = await AIService.apply_color_correction(
                db, user_id, segment_id,
                ColorCorrectionRequest(segment_id=segment_id, **params),
            )
        elif operation == "smart_frame":
            result, ai_gen = await AIService.get_frame_suggestions(
                db, user_id, segment_id,
                target_aspect_ratio=params.get("target_aspect_ratio", "9:16"),
            )
        else:
            raise ValueError(f"Unknown agent step operation: {operation}")

        return result.id, ai_gen.credits_used

    @staticmethod
    async def execute_agent(
        db: AsyncSession, user_id: UUID, agent_id: UUID, segment_id: UUID
    ) -> AgentExecution:
        agent = await db.get(AIAgent, agent_id)
        if not agent or not agent.is_active:
            raise ValueError("Agent not found or no longer active")

        steps = json.loads(agent.steps)
        execution = AgentExecution(
            agent_id=agent_id,
            user_id=user_id,
            segment_id=segment_id,
            status=AgentExecutionStatus.RUNNING,
        )
        db.add(execution)
        await db.flush()

        steps_log = []
        total_credits = 0
        for step in steps:
            operation = step["operation"]
            try:
                result_id, credits_used = await AIAgentService._run_step(
                    db, user_id, segment_id, operation, step.get("params", {})
                )
                steps_log.append({
                    "operation": operation,
                    "status": "completed",
                    "credits_used": credits_used,
                    "result_id": str(result_id),
                    "error": None,
                })
                total_credits += credits_used
            except Exception as e:
                steps_log.append({
                    "operation": operation,
                    "status": "failed",
                    "credits_used": 0,
                    "result_id": None,
                    "error": str(e),
                })
                execution.status = AgentExecutionStatus.FAILED
                execution.error_message = f"Failed at step '{operation}': {e}"
                execution.steps_log = json.dumps(steps_log)
                execution.total_credits_used = total_credits
                execution.completed_at = datetime.utcnow()
                await db.commit()
                await db.refresh(execution)
                logger.warning(f"Agent execution {execution.id} failed at step {operation}: {e}")
                return execution

        execution.status = AgentExecutionStatus.COMPLETED
        execution.steps_log = json.dumps(steps_log)
        execution.total_credits_used = total_credits
        execution.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(execution)
        logger.info(f"Agent execution {execution.id} completed ({total_credits} credits)")
        return execution

    @staticmethod
    async def list_my_executions(db: AsyncSession, user_id: UUID) -> List[AgentExecution]:
        result = await db.execute(
            select(AgentExecution)
            .where(AgentExecution.user_id == user_id)
            .order_by(desc(AgentExecution.started_at))
        )
        return list(result.scalars().all())
