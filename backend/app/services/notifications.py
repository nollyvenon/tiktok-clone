"""
Notification service - creation, delivery preferences, and read-state
management for in-app notifications.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationPreference, NotificationType

logger = __import__("logging").getLogger(__name__)


class NotificationService:
    """Service for creating and managing user notifications"""

    @staticmethod
    async def get_or_create_preferences(
        db: AsyncSession, user_id: UUID
    ) -> NotificationPreference:
        """Get a user's notification preferences, creating defaults on first access"""
        result = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        prefs = result.scalar()
        if prefs:
            return prefs

        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        return prefs

    @staticmethod
    async def _is_type_enabled(prefs: NotificationPreference, notification_type: NotificationType) -> bool:
        """Checks the per-type preference flag, defaulting to enabled for types with no flag"""
        type_flags = {
            NotificationType.FOLLOW: prefs.follow_notifications,
            NotificationType.LIKE: prefs.like_notifications,
            NotificationType.COMMENT: prefs.comment_notifications,
            NotificationType.MENTION: prefs.mention_notifications,
            NotificationType.MESSAGE: prefs.message_notifications,
        }
        return type_flags.get(notification_type, True)

    @staticmethod
    async def send_notification(
        db: AsyncSession,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: Optional[str] = None,
        actor_id: Optional[UUID] = None,
        related_video_id: Optional[UUID] = None,
        related_comment_id: Optional[UUID] = None,
    ) -> Optional[Notification]:
        """
        Create a notification for a user, respecting their in-app preference
        for this notification type. Returns None (and creates nothing) if the
        user has disabled in-app notifications or this specific type - this
        is a deliberate no-op, not an error.
        """
        if actor_id is not None and actor_id == user_id:
            # Don't notify users about their own actions (e.g. following/liking your own content)
            return None

        prefs = await NotificationService.get_or_create_preferences(db, user_id)
        if not prefs.in_app_enabled:
            return None
        if not await NotificationService._is_type_enabled(prefs, notification_type):
            return None

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            actor_id=actor_id,
            related_video_id=related_video_id,
            related_comment_id=related_comment_id,
            title=title,
            message=message,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        logger.info(f"Notification sent: {notification_type.value} to user {user_id}")
        return notification

    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> Tuple[List[Notification], int, int]:
        """Returns (notifications, total_count, unread_count)"""
        filters = [Notification.user_id == user_id]
        if unread_only:
            filters.append(Notification.is_read == False)  # noqa: E712

        total_result = await db.execute(
            select(func.count(Notification.id)).where(*filters)
        )
        total = total_result.scalar() or 0

        unread_result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id, Notification.is_read == False  # noqa: E712
            )
        )
        unread_count = unread_result.scalar() or 0

        result = await db.execute(
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        notifications = result.scalars().all()

        return notifications, total, unread_count

    @staticmethod
    async def mark_as_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """Marks a single notification as read. Returns None if not found/not owned."""
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )
        notification = result.scalar()
        if not notification:
            return None

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: UUID) -> int:
        """Marks all of a user's unread notifications as read. Returns the count updated."""
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == user_id, Notification.is_read == False  # noqa: E712
            )
        )
        unread = result.scalars().all()
        now = datetime.utcnow()
        for notification in unread:
            notification.is_read = True
            notification.read_at = now
        await db.commit()
        return len(unread)

    @staticmethod
    async def delete_notification(db: AsyncSession, notification_id: UUID, user_id: UUID) -> bool:
        """Deletes a notification. Returns False if not found/not owned."""
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )
        notification = result.scalar()
        if not notification:
            return False

        await db.delete(notification)
        await db.commit()
        return True

    @staticmethod
    async def update_preferences(
        db: AsyncSession, user_id: UUID, updates: dict
    ) -> NotificationPreference:
        """Applies a partial update to a user's notification preferences"""
        prefs = await NotificationService.get_or_create_preferences(db, user_id)
        for field, value in updates.items():
            if value is not None:
                setattr(prefs, field, value)
        prefs.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(prefs)
        return prefs
