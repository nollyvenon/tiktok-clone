"""
Collaborations service - team content creation with an agreed-upfront
revenue split, tracked the same way Creator Fund awards are: as figures
on the row, not real money moving through a payment processor.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Collaboration, Collaborator, CollaborationStatus, CollaboratorStatus, Video,
)

logger = logging.getLogger(__name__)


class CollaborationService:
    """Service for team-content collaborations and their revenue splits"""

    @staticmethod
    async def create_collaboration(
        db: AsyncSession,
        initiator_id: UUID,
        video_id: UUID,
        title: Optional[str],
        splits: List[dict],
    ) -> Collaboration:
        video = await db.get(Video, video_id)
        if not video or video.deleted_at is not None:
            raise ValueError("Video not found")
        if video.user_id != initiator_id:
            raise ValueError("You can only start a collaboration on your own video")

        initiator_split = next((s for s in splits if s["user_id"] == initiator_id), None)
        if initiator_split is None:
            raise ValueError("The initiator must be included among the collaborators")

        collaboration = Collaboration(
            video_id=video_id,
            initiator_id=initiator_id,
            title=title,
            status=CollaborationStatus.PENDING,
        )
        db.add(collaboration)
        await db.flush()

        for split in splits:
            is_initiator = split["user_id"] == initiator_id
            collaborator = Collaborator(
                collaboration_id=collaboration.id,
                user_id=split["user_id"],
                revenue_split_percent=split["revenue_split_percent"],
                is_initiator=is_initiator,
                status=CollaboratorStatus.ACCEPTED if is_initiator else CollaboratorStatus.INVITED,
                responded_at=datetime.utcnow() if is_initiator else None,
            )
            db.add(collaborator)

        await db.commit()
        return await CollaborationService._get_with_collaborators(db, collaboration.id)

    @staticmethod
    async def _get_with_collaborators(db: AsyncSession, collaboration_id: UUID) -> Collaboration:
        result = await db.execute(
            select(Collaboration)
            .options(selectinload(Collaboration.collaborators))
            .where(Collaboration.id == collaboration_id)
        )
        collaboration = result.scalar()
        if not collaboration:
            raise ValueError("Collaboration not found")
        return collaboration

    @staticmethod
    async def get_collaboration(db: AsyncSession, collaboration_id: UUID, user_id: UUID) -> Collaboration:
        collaboration = await CollaborationService._get_with_collaborators(db, collaboration_id)
        if not any(c.user_id == user_id for c in collaboration.collaborators):
            raise ValueError("You are not part of this collaboration")
        return collaboration

    @staticmethod
    async def list_my_collaborations(db: AsyncSession, user_id: UUID) -> List[Collaboration]:
        result = await db.execute(
            select(Collaboration)
            .options(selectinload(Collaboration.collaborators))
            .join(Collaborator, Collaborator.collaboration_id == Collaboration.id)
            .where(Collaborator.user_id == user_id)
            .order_by(Collaboration.created_at.desc())
        )
        return list(result.scalars().unique().all())

    @staticmethod
    async def respond(db: AsyncSession, collaboration_id: UUID, user_id: UUID, accept: bool) -> Collaboration:
        collaboration = await CollaborationService._get_with_collaborators(db, collaboration_id)
        if collaboration.status != CollaborationStatus.PENDING:
            raise ValueError("This collaboration is no longer awaiting responses")

        collaborator = next((c for c in collaboration.collaborators if c.user_id == user_id), None)
        if collaborator is None:
            raise ValueError("You are not invited to this collaboration")
        if collaborator.status != CollaboratorStatus.INVITED:
            raise ValueError("You have already responded to this invitation")

        collaborator.status = CollaboratorStatus.ACCEPTED if accept else CollaboratorStatus.DECLINED
        collaborator.responded_at = datetime.utcnow()

        if not accept:
            collaboration.status = CollaborationStatus.CANCELLED
        elif all(c.status == CollaboratorStatus.ACCEPTED for c in collaboration.collaborators):
            collaboration.status = CollaborationStatus.ACTIVE

        await db.commit()
        return await CollaborationService._get_with_collaborators(db, collaboration_id)

    @staticmethod
    async def cancel(db: AsyncSession, collaboration_id: UUID, user_id: UUID) -> Collaboration:
        collaboration = await CollaborationService._get_with_collaborators(db, collaboration_id)
        if collaboration.initiator_id != user_id:
            raise ValueError("Only the initiator can cancel a collaboration")
        if collaboration.status == CollaborationStatus.CANCELLED:
            raise ValueError("This collaboration is already cancelled")

        collaboration.status = CollaborationStatus.CANCELLED
        await db.commit()
        return await CollaborationService._get_with_collaborators(db, collaboration_id)
