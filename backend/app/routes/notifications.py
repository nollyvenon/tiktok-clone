"""
Notification API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User
from app.services.notifications import NotificationService
from app.schemas import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's notifications, most recent first"""
    notifications, total, unread_count = await NotificationService.get_user_notifications(
        db, current_user.id, limit=limit, offset=offset, unread_only=unread_only
    )
    return NotificationListResponse(
        notifications=[NotificationResponse.from_orm(n) for n in notifications],
        total=total,
        unread_count=unread_count,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    responses={404: {"model": ErrorResponse, "description": "Notification not found"}},
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read"""
    notification = await NotificationService.mark_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse.from_orm(notification)


@router.put("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all of the current user's unread notifications as read"""
    count = await NotificationService.mark_all_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read", "count": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse, "description": "Notification not found"}},
)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification"""
    deleted = await NotificationService.delete_notification(db, notification_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"message": "Notification deleted"}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's notification delivery preferences"""
    prefs = await NotificationService.get_or_create_preferences(db, current_user.id)
    return NotificationPreferenceResponse.from_orm(prefs)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    request: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's notification delivery preferences"""
    prefs = await NotificationService.update_preferences(
        db, current_user.id, request.dict(exclude_unset=True)
    )
    return NotificationPreferenceResponse.from_orm(prefs)
