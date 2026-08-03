"""
Creator Fund service - funding programs, eligibility, and applications.

No real payment processor exists anywhere in this app, so an approved
award is credited only as a figure on the application row (`awarded_amount`)
- an internal ledger entry, not an actual money transfer.
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    FundingProgram, CreatorApplication, ApplicationStatus, Follow, Video, VideoStatus,
)

logger = logging.getLogger(__name__)


class CreatorFundService:
    """Service for funding programs and creator applications"""

    @staticmethod
    async def list_active_programs(db: AsyncSession) -> List[FundingProgram]:
        result = await db.execute(
            select(FundingProgram)
            .where(FundingProgram.is_active == True)
            .order_by(desc(FundingProgram.created_at))
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_program(db: AsyncSession, data: dict) -> FundingProgram:
        program = FundingProgram(**data)
        db.add(program)
        await db.commit()
        await db.refresh(program)
        return program

    @staticmethod
    async def _compute_creator_stats(db: AsyncSession, user_id: UUID) -> Tuple[int, int, int]:
        """Live follower/published-video/total-views counts for eligibility"""
        followers_count = (
            await db.execute(
                select(func.count()).select_from(Follow).where(
                    and_(Follow.following_id == user_id, Follow.is_active == True)
                )
            )
        ).scalar() or 0

        videos_result = await db.execute(
            select(Video.views_count).where(
                and_(
                    Video.user_id == user_id,
                    Video.status == VideoStatus.PUBLISHED,
                    Video.deleted_at.is_(None),
                )
            )
        )
        views_counts = videos_result.scalars().all()
        published_videos_count = len(views_counts)
        total_views_count = sum(views_counts)

        return followers_count, published_videos_count, total_views_count

    @staticmethod
    async def apply_to_program(db: AsyncSession, user_id: UUID, program_id: UUID) -> CreatorApplication:
        program = await db.get(FundingProgram, program_id)
        if not program or not program.is_active:
            raise ValueError("Funding program not found or no longer active")

        existing = await db.execute(
            select(CreatorApplication).where(
                and_(
                    CreatorApplication.program_id == program_id,
                    CreatorApplication.user_id == user_id,
                )
            )
        )
        if existing.scalar():
            raise ValueError("You have already applied to this program")

        followers_count, published_videos_count, total_views_count = (
            await CreatorFundService._compute_creator_stats(db, user_id)
        )
        meets_requirements = (
            followers_count >= program.min_followers
            and published_videos_count >= program.min_published_videos
            and total_views_count >= program.min_total_views
        )

        application = CreatorApplication(
            program_id=program_id,
            user_id=user_id,
            followers_count=followers_count,
            published_videos_count=published_videos_count,
            total_views_count=total_views_count,
            meets_requirements=meets_requirements,
        )
        db.add(application)
        await db.commit()
        await db.refresh(application)
        logger.info(f"User {user_id} applied to funding program {program_id}")
        return application

    @staticmethod
    async def list_my_applications(db: AsyncSession, user_id: UUID) -> List[CreatorApplication]:
        result = await db.execute(
            select(CreatorApplication)
            .where(CreatorApplication.user_id == user_id)
            .order_by(desc(CreatorApplication.created_at))
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_applications(
        db: AsyncSession,
        status_filter: Optional[ApplicationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[CreatorApplication], int]:
        query = select(CreatorApplication)
        count_query = select(func.count()).select_from(CreatorApplication)
        if status_filter:
            query = query.where(CreatorApplication.status == status_filter)
            count_query = count_query.where(CreatorApplication.status == status_filter)

        total = (await db.execute(count_query)).scalar() or 0
        result = await db.execute(
            query.order_by(desc(CreatorApplication.created_at)).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def decide_application(
        db: AsyncSession,
        application_id: UUID,
        admin_id: UUID,
        decision: ApplicationStatus,
        reason: Optional[str],
    ) -> CreatorApplication:
        from datetime import datetime

        application = await db.get(CreatorApplication, application_id)
        if not application:
            raise ValueError("Application not found")
        if application.status != ApplicationStatus.PENDING:
            raise ValueError("Application has already been decided")

        application.status = decision
        application.decision_reason = reason
        application.reviewed_by = admin_id
        application.reviewed_at = datetime.utcnow()

        if decision == ApplicationStatus.APPROVED:
            program = await db.get(FundingProgram, application.program_id)
            application.awarded_amount = program.award_amount

        await db.commit()
        await db.refresh(application)
        logger.info(f"Admin {admin_id} {decision.value} application {application_id}")
        return application
