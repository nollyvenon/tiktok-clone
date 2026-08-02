"""
Moderation service - content reporting and admin review/enforcement.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ContentReport, ModerationDecision, ReportedContentType, ReportReason,
    ReportStatus, ModerationActionType, Video, VideoStatus, Comment, User,
)

logger = logging.getLogger(__name__)


class ModerationService:
    """Service for content reports and moderation decisions"""

    @staticmethod
    async def create_report(
        db: AsyncSession,
        reporter_id: UUID,
        content_type: ReportedContentType,
        content_id: UUID,
        reason: ReportReason,
        description: Optional[str] = None,
    ) -> ContentReport:
        """
        Submit a content report against a video, comment, or user.

        Raises:
            ValueError: If the reported content doesn't exist, or a user
                tries to report their own content/themselves.
        """
        report = ContentReport(
            reporter_id=reporter_id,
            content_type=content_type,
            reason=reason,
            description=description,
        )

        if content_type == ReportedContentType.VIDEO:
            video = await db.get(Video, content_id)
            if not video or video.deleted_at is not None:
                raise ValueError("Video not found")
            if video.user_id == reporter_id:
                raise ValueError("Cannot report your own video")
            report.reported_video_id = content_id

        elif content_type == ReportedContentType.COMMENT:
            comment = await db.get(Comment, content_id)
            if not comment or comment.deleted_at is not None:
                raise ValueError("Comment not found")
            if comment.user_id == reporter_id:
                raise ValueError("Cannot report your own comment")
            report.reported_comment_id = content_id

        elif content_type == ReportedContentType.USER:
            user = await db.get(User, content_id)
            if not user:
                raise ValueError("User not found")
            if user.id == reporter_id:
                raise ValueError("Cannot report yourself")
            report.reported_user_id = content_id

        db.add(report)
        await db.commit()
        await db.refresh(report)
        logger.info(f"Report created: {report.id} ({content_type.value}) by {reporter_id}")
        return report

    @staticmethod
    async def get_report(db: AsyncSession, report_id: UUID) -> Optional[ContentReport]:
        return await db.get(ContentReport, report_id)

    @staticmethod
    async def get_user_reports(
        db: AsyncSession, reporter_id: UUID, limit: int = 20, offset: int = 0
    ) -> Tuple[List[ContentReport], int]:
        """Get reports a user has submitted, newest first"""
        filters = [ContentReport.reporter_id == reporter_id]

        count_result = await db.execute(select(func.count()).select_from(ContentReport).where(and_(*filters)))
        total = count_result.scalar() or 0

        result = await db.execute(
            select(ContentReport).where(and_(*filters)).order_by(desc(ContentReport.created_at)).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_report_queue(
        db: AsyncSession,
        status_filter: Optional[ReportStatus] = None,
        content_type: Optional[ReportedContentType] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[ContentReport], int]:
        """Admin queue: all reports, optionally filtered, oldest-pending-first
        so the longest-waiting reports get reviewed first."""
        count_query = select(func.count()).select_from(ContentReport)
        query = select(ContentReport)
        if status_filter is not None:
            count_query = count_query.where(ContentReport.status == status_filter)
            query = query.where(ContentReport.status == status_filter)
        if content_type is not None:
            count_query = count_query.where(ContentReport.content_type == content_type)
            query = query.where(ContentReport.content_type == content_type)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(ContentReport.created_at.asc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def decide_report(
        db: AsyncSession,
        report_id: UUID,
        moderator_id: UUID,
        action: ModerationActionType,
        notes: Optional[str] = None,
    ) -> ModerationDecision:
        """
        Record a moderator's decision on a report and apply its effect:
        - remove_content: soft-deletes the reported video/comment
        - suspend_user/ban_user: deactivates the reported user's account
        - warn_user/dismiss: logged only, no state change

        Raises:
            ValueError: If the report doesn't exist or was already decided.
        """
        report = await db.get(ContentReport, report_id)
        if not report:
            raise ValueError("Report not found")
        if report.status != ReportStatus.PENDING:
            raise ValueError("Report has already been decided")

        if action == ModerationActionType.REMOVE_CONTENT:
            if report.content_type == ReportedContentType.VIDEO:
                video = await db.get(Video, report.reported_video_id)
                if video:
                    video.status = VideoStatus.DELETED
                    video.deleted_at = datetime.utcnow()
            elif report.content_type == ReportedContentType.COMMENT:
                comment = await db.get(Comment, report.reported_comment_id)
                if comment:
                    comment.deleted_at = datetime.utcnow()

        elif action in (ModerationActionType.SUSPEND_USER, ModerationActionType.BAN_USER):
            target_user_id = report.reported_user_id
            if target_user_id is None:
                # A video/comment report can still result in suspending its author
                if report.content_type == ReportedContentType.VIDEO:
                    video = await db.get(Video, report.reported_video_id)
                    target_user_id = video.user_id if video else None
                elif report.content_type == ReportedContentType.COMMENT:
                    comment = await db.get(Comment, report.reported_comment_id)
                    target_user_id = comment.user_id if comment else None
            if target_user_id:
                target_user = await db.get(User, target_user_id)
                if target_user:
                    target_user.is_active = False

        report.status = (
            ReportStatus.DISMISSED if action == ModerationActionType.DISMISS else ReportStatus.ACTIONED
        )

        decision = ModerationDecision(
            report_id=report_id,
            moderator_id=moderator_id,
            action=action,
            notes=notes,
        )
        db.add(decision)
        await db.commit()
        await db.refresh(decision)
        logger.info(f"Report {report_id} decided: {action.value} by {moderator_id}")
        return decision
