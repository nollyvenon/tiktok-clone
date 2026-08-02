"""
Admin dashboard service - platform stats, user management, audit log.
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, Video, Comment, ContentReport, ModerationDecision, ReportStatus,
)

logger = logging.getLogger(__name__)


class AdminService:
    """Service for platform-wide admin operations"""

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """Aggregate platform-wide counts for the admin overview"""
        total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
        active_users = (
            await db.execute(select(func.count()).select_from(User).where(User.is_active == True))
        ).scalar() or 0
        total_videos = (
            await db.execute(select(func.count()).select_from(Video).where(Video.deleted_at.is_(None)))
        ).scalar() or 0
        total_comments = (
            await db.execute(select(func.count()).select_from(Comment).where(Comment.deleted_at.is_(None)))
        ).scalar() or 0

        report_counts = {}
        for status_value in ReportStatus:
            count = (
                await db.execute(
                    select(func.count()).select_from(ContentReport).where(ContentReport.status == status_value)
                )
            ).scalar() or 0
            report_counts[status_value] = count

        return {
            "total_users": total_users,
            "active_users": active_users,
            "suspended_users": total_users - active_users,
            "total_videos": total_videos,
            "total_comments": total_comments,
            "pending_reports": report_counts.get(ReportStatus.PENDING, 0),
            "actioned_reports": report_counts.get(ReportStatus.ACTIONED, 0),
            "dismissed_reports": report_counts.get(ReportStatus.DISMISSED, 0),
        }

    @staticmethod
    async def get_users(
        db: AsyncSession,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[User], int]:
        """List/search users for admin management, newest first"""
        filters = []
        if search:
            like = f"%{search}%"
            filters.append(or_(User.username.ilike(like), User.email.ilike(like)))

        query = select(User)
        count_query = select(func.count()).select_from(User)
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total = (await db.execute(count_query)).scalar() or 0
        result = await db.execute(query.order_by(desc(User.created_at)).offset(offset).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def set_user_active(db: AsyncSession, user_id: UUID, is_active: bool) -> User:
        """Directly suspend or reactivate a user, without requiring a
        content report first - the moderation queue's suspend/ban actions
        are the report-driven path; this is the direct admin path."""
        user = await db.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        user.is_active = is_active
        await db.commit()
        await db.refresh(user)
        logger.info(f"Admin {'reactivated' if is_active else 'suspended'} user {user_id}")
        return user

    @staticmethod
    async def get_audit_log(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """Get the moderation decision audit log, newest first, enriched
        with the moderator's username and the report's context."""
        total = (await db.execute(select(func.count()).select_from(ModerationDecision))).scalar() or 0

        result = await db.execute(
            select(ModerationDecision)
            .order_by(desc(ModerationDecision.created_at))
            .offset(offset)
            .limit(limit)
        )
        decisions = result.scalars().all()

        entries = []
        for decision in decisions:
            moderator = await db.get(User, decision.moderator_id)
            report = await db.get(ContentReport, decision.report_id)
            entries.append({
                "id": decision.id,
                "report_id": decision.report_id,
                "moderator_id": decision.moderator_id,
                "moderator_username": moderator.username if moderator else "unknown",
                "action": decision.action,
                "notes": decision.notes,
                "report_content_type": report.content_type if report else None,
                "report_reason": report.reason if report else None,
                "created_at": decision.created_at,
            })

        return entries, total
