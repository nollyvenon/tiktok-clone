"""
Comment service - creating, threading, liking, pinning, and deleting
comments on videos.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment, CommentLike, Video

logger = logging.getLogger(__name__)


class CommentService:
    """Service for comment CRUD, threading, likes, and pinning"""

    @staticmethod
    async def create_comment(
        db: AsyncSession,
        video_id: UUID,
        user_id: UUID,
        content: str,
        parent_comment_id: Optional[UUID] = None,
    ) -> Comment:
        """
        Create a top-level comment or a reply.

        Raises:
            ValueError: If the video doesn't exist, comments are disabled,
                or the parent comment doesn't exist / belongs to a
                different video / is itself a reply (only one level of
                threading is supported).
        """
        video = await db.get(Video, video_id)
        if not video or video.deleted_at is not None:
            raise ValueError("Video not found")
        if not video.allow_comments:
            raise ValueError("Comments are disabled for this video")

        if parent_comment_id is not None:
            parent = await db.get(Comment, parent_comment_id)
            if not parent or parent.deleted_at is not None:
                raise ValueError("Parent comment not found")
            if parent.video_id != video_id:
                raise ValueError("Parent comment belongs to a different video")
            if parent.parent_comment_id is not None:
                raise ValueError("Cannot reply to a reply - only one level of threading is supported")

        comment = Comment(
            video_id=video_id,
            user_id=user_id,
            parent_comment_id=parent_comment_id,
            content=content,
        )
        db.add(comment)

        video.comments_count += 1
        if parent_comment_id is not None:
            parent.replies_count += 1

        await db.commit()
        await db.refresh(comment)
        logger.info(f"Comment created: {comment.id} on video {video_id}")
        return comment

    @staticmethod
    async def get_video_comments(
        db: AsyncSession,
        video_id: UUID,
        current_user_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Comment], int]:
        """Get top-level comments for a video, pinned first then newest first"""
        filters = [
            Comment.video_id == video_id,
            Comment.parent_comment_id.is_(None),
            Comment.deleted_at.is_(None),
        ]

        total_result = await db.execute(select(func.count(Comment.id)).where(*filters))
        total = total_result.scalar() or 0

        result = await db.execute(
            select(Comment)
            .where(*filters)
            .order_by(Comment.is_pinned.desc(), Comment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        comments = result.scalars().all()
        return comments, total

    @staticmethod
    async def get_replies(
        db: AsyncSession,
        parent_comment_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Comment], int]:
        """Get replies to a comment, oldest first (conversational order)"""
        filters = [
            Comment.parent_comment_id == parent_comment_id,
            Comment.deleted_at.is_(None),
        ]

        total_result = await db.execute(select(func.count(Comment.id)).where(*filters))
        total = total_result.scalar() or 0

        result = await db.execute(
            select(Comment)
            .where(*filters)
            .order_by(Comment.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        replies = result.scalars().all()
        return replies, total

    @staticmethod
    async def is_liked_by(db: AsyncSession, comment_id: UUID, user_id: UUID) -> bool:
        result = await db.execute(
            select(CommentLike).where(
                and_(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
            )
        )
        return result.scalar() is not None

    @staticmethod
    async def update_comment(
        db: AsyncSession, comment_id: UUID, user_id: UUID, content: str
    ) -> Comment:
        """
        Edit a comment's content. Only the comment's author may edit it.

        Raises:
            ValueError: If not found or not owned by user_id.
        """
        comment = await db.get(Comment, comment_id)
        if not comment or comment.deleted_at is not None:
            raise ValueError("Comment not found")
        if comment.user_id != user_id:
            raise ValueError("Not authorized to edit this comment")

        comment.content = content
        comment.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def delete_comment(
        db: AsyncSession, comment_id: UUID, user_id: UUID
    ) -> None:
        """
        Soft-delete a comment. Allowed for the comment's author or the
        video's owner (moderation).

        Raises:
            ValueError: If not found or not authorized.
        """
        comment = await db.get(Comment, comment_id)
        if not comment or comment.deleted_at is not None:
            raise ValueError("Comment not found")

        video = await db.get(Video, comment.video_id)
        is_own_comment = comment.user_id == user_id
        is_video_owner = video is not None and video.user_id == user_id
        if not is_own_comment and not is_video_owner:
            raise ValueError("Not authorized to delete this comment")

        comment.deleted_at = datetime.utcnow()
        if video:
            video.comments_count = max(0, video.comments_count - 1)
        if comment.parent_comment_id is not None:
            parent = await db.get(Comment, comment.parent_comment_id)
            if parent:
                parent.replies_count = max(0, parent.replies_count - 1)

        await db.commit()

    @staticmethod
    async def toggle_like(db: AsyncSession, comment_id: UUID, user_id: UUID) -> Tuple[bool, int]:
        """Like or unlike a comment. Returns (is_liked, likes_count)."""
        comment = await db.get(Comment, comment_id)
        if not comment or comment.deleted_at is not None:
            raise ValueError("Comment not found")

        result = await db.execute(
            select(CommentLike).where(
                and_(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
            )
        )
        like = result.scalar()

        if like:
            await db.delete(like)
            comment.likes_count = max(0, comment.likes_count - 1)
            is_liked = False
        else:
            db.add(CommentLike(comment_id=comment_id, user_id=user_id))
            comment.likes_count += 1
            is_liked = True

        await db.commit()
        return is_liked, comment.likes_count

    @staticmethod
    async def toggle_pin(db: AsyncSession, comment_id: UUID, user_id: UUID) -> Comment:
        """
        Pin or unpin a comment. Only the video's owner may pin comments,
        and only top-level comments can be pinned.

        Raises:
            ValueError: If not found, not authorized, or a reply.
        """
        comment = await db.get(Comment, comment_id)
        if not comment or comment.deleted_at is not None:
            raise ValueError("Comment not found")
        if comment.parent_comment_id is not None:
            raise ValueError("Replies cannot be pinned")

        video = await db.get(Video, comment.video_id)
        if not video or video.user_id != user_id:
            raise ValueError("Only the video owner can pin comments")

        comment.is_pinned = not comment.is_pinned
        await db.commit()
        await db.refresh(comment)
        return comment
