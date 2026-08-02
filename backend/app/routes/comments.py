"""
Comment API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user, get_optional_current_user
from app.models import User, NotificationType
from app.services.comments import CommentService
from app.services.profiles import ProfileService
from app.services.notifications import NotificationService
from app.schemas import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
    CommentLikeResponse,
    UserPublicProfile,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Comments"])


async def _build_comment_response(
    db: AsyncSession, comment, current_user_id: Optional[UUID] = None
) -> CommentResponse:
    """Builds a CommentResponse with the nested author populated"""
    author = await ProfileService.get_user_profile(db, comment.user_id)
    is_liked = False
    if current_user_id is not None:
        is_liked = await CommentService.is_liked_by(db, comment.id, current_user_id)

    return CommentResponse(
        id=comment.id,
        video_id=comment.video_id,
        user_id=comment.user_id,
        user=UserPublicProfile.from_orm(author),
        parent_comment_id=comment.parent_comment_id,
        content=comment.content,
        likes_count=comment.likes_count,
        replies_count=comment.replies_count,
        is_pinned=comment.is_pinned,
        is_liked=is_liked,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get(
    "/videos/{video_id}/comments",
    response_model=CommentListResponse,
    responses={404: {"model": ErrorResponse, "description": "Video not found"}},
)
async def get_video_comments(
    video_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top-level comments for a video, pinned comments first"""
    comments, total = await CommentService.get_video_comments(
        db, video_id, limit=limit, offset=offset
    )
    current_user_id = current_user.id if current_user else None
    return CommentListResponse(
        comments=[await _build_comment_response(db, c, current_user_id) for c in comments],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/videos/{video_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def create_comment(
    video_id: UUID,
    request: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a comment, or a reply if parent_comment_id is provided"""
    try:
        comment = await CommentService.create_comment(
            db, video_id, current_user.id, request.content, request.parent_comment_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Notify: the video owner for a top-level comment, or the parent
    # comment's author for a reply - never the actor themselves.
    from app.models import Video, Comment

    if request.parent_comment_id is not None:
        parent = await db.get(Comment, request.parent_comment_id)
        if parent:
            await NotificationService.send_notification(
                db,
                user_id=parent.user_id,
                notification_type=NotificationType.REPLY,
                title=f"{current_user.username} replied to your comment",
                actor_id=current_user.id,
                related_video_id=video_id,
                related_comment_id=comment.id,
            )
    else:
        video = await db.get(Video, video_id)
        if video:
            await NotificationService.send_notification(
                db,
                user_id=video.user_id,
                notification_type=NotificationType.COMMENT,
                title=f"{current_user.username} commented on your video",
                message=request.content[:200],
                actor_id=current_user.id,
                related_video_id=video_id,
                related_comment_id=comment.id,
            )

    return await _build_comment_response(db, comment, current_user.id)


@router.get(
    "/comments/{comment_id}/replies",
    response_model=CommentListResponse,
)
async def get_comment_replies(
    comment_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get replies to a comment, oldest first"""
    replies, total = await CommentService.get_replies(db, comment_id, limit=limit, offset=offset)
    current_user_id = current_user.id if current_user else None
    return CommentListResponse(
        comments=[await _build_comment_response(db, r, current_user_id) for r in replies],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Not authorized or not found"},
    },
)
async def update_comment(
    comment_id: UUID,
    request: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit your own comment"""
    try:
        comment = await CommentService.update_comment(db, comment_id, current_user.id, request.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return await _build_comment_response(db, comment, current_user.id)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Not authorized or not found"},
    },
)
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a comment - allowed for its author or the video's owner"""
    try:
        await CommentService.delete_comment(db, comment_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": "Comment deleted"}


@router.post(
    "/comments/{comment_id}/like",
    response_model=CommentLikeResponse,
    responses={400: {"model": ErrorResponse, "description": "Comment not found"}},
)
async def like_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like on a comment"""
    try:
        is_liked, likes_count = await CommentService.toggle_like(db, comment_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return CommentLikeResponse(is_liked=is_liked, likes_count=likes_count)


@router.post(
    "/comments/{comment_id}/pin",
    response_model=CommentResponse,
    responses={400: {"model": ErrorResponse, "description": "Not authorized or not found"}},
)
async def pin_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pin or unpin a top-level comment - video owner only"""
    try:
        comment = await CommentService.toggle_pin(db, comment_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return await _build_comment_response(db, comment, current_user.id)
