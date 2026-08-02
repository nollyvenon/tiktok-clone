"""
Upload and draft API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from uuid import UUID

from app.database import get_db
from app.schemas import (
    UploadResponse, DraftCreate, DraftResponse, PublishDraftRequest,
    UploadPresignedURLRequest, UploadPresignedURLResponse, ErrorResponse
)
from app.services.uploads import UploadService
from app.services.notifications import NotificationService
from app.routes.auth import get_current_user
from app.models import User, NotificationType, Video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads & Drafts"])


# ============================================================================
# Upload Endpoints
# ============================================================================

@router.post(
    "/presigned-url",
    response_model=UploadPresignedURLResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Presigned URL generated"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_presigned_url(
    request: UploadPresignedURLRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get presigned URL for direct S3 upload

    **Authorization:** Requires valid access token

    **Request body:**
    - filename: Original filename
    - file_size: File size in bytes
    - mime_type: MIME type (video/mp4, etc.)

    **Returns:** Presigned URL for direct upload
    """
    try:
        # Create upload record
        upload = await UploadService.create_upload(
            db,
            current_user.id,
            request.filename,
            request.file_size,
            request.mime_type,
            storage_path=f"uploads/{current_user.id}/{request.filename}",
        )

        # Get presigned URL
        presigned_url = await UploadService.get_presigned_url(upload.id, request.filename)

        return UploadPresignedURLResponse(
            upload_id=upload.id,
            presigned_url=presigned_url,
            expires_in=3600,  # 1 hour
        )
    except Exception as e:
        logger.error(f"Get presigned URL error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate presigned URL",
        )


@router.post(
    "/{upload_id}/complete",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Upload completed"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Upload not found"},
    },
)
async def complete_upload(
    upload_id: UUID,
    processed_video_url: str = Query(...),
    thumbnail_url: str = Query(...),
    duration: int = Query(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark upload as completed

    **Authorization:** Requires valid access token

    **Parameters:**
    - processed_video_url: URL to processed video
    - thumbnail_url: URL to thumbnail
    - duration: Video duration in seconds
    """
    try:
        # Verify ownership
        upload = await UploadService.get_upload(db, upload_id)
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found",
            )

        if upload.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        # Mark as completed
        upload = await UploadService.mark_upload_completed(
            db,
            upload_id,
            processed_video_url,
            thumbnail_url,
            duration,
        )

        return UploadResponse.from_orm(upload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete upload",
        )


@router.get(
    "/drafts",
    responses={
        200: {"description": "User drafts"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_user_drafts(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's drafts"""
    try:
        drafts, total = await UploadService.get_user_drafts(
            db,
            current_user.id,
            limit=limit,
            offset=offset,
        )

        return {
            "drafts": [DraftResponse.from_orm(d) for d in drafts],
            "total": total,
        }
    except Exception as e:
        logger.error(f"Get user drafts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drafts",
        )



@router.get(
    "/{upload_id}",
    response_model=UploadResponse,
    responses={
        200: {"description": "Upload info"},
        404: {"model": ErrorResponse, "description": "Upload not found"},
    },
)
async def get_upload(
    upload_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get upload status and progress"""
    try:
        upload = await UploadService.get_upload(db, upload_id)
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found",
            )

        return UploadResponse.from_orm(upload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upload",
        )


# ============================================================================
# Draft Endpoints
# ============================================================================

@router.post(
    "/drafts",
    response_model=DraftResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Draft created"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def create_draft(
    request: DraftCreate,
    upload_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create video draft

    **Authorization:** Requires valid access token

    **Parameters:**
    - upload_id: Associated upload ID (optional)

    **Request body:**
    - title: Video title
    - description: Video description
    - hashtags: Comma-separated hashtags
    - is_public: Publish publicly (default true)
    """
    try:
        draft = await UploadService.create_draft(
            db,
            current_user.id,
            upload_id=upload_id,
            draft_data=request,
        )

        return DraftResponse.from_orm(draft)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Create draft error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create draft",
        )


@router.get(
    "/drafts/{draft_id}",
    response_model=DraftResponse,
    responses={
        200: {"description": "Draft retrieved"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
    },
)
async def get_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get draft by ID"""
    try:
        draft = await UploadService.get_draft(db, draft_id)
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found",
            )

        if draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        return DraftResponse.from_orm(draft)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get draft error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve draft",
        )


@router.put(
    "/drafts/{draft_id}",
    response_model=DraftResponse,
    responses={
        200: {"description": "Draft updated"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
    },
)
async def update_draft(
    draft_id: UUID,
    request: DraftCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update draft"""
    try:
        draft = await UploadService.update_draft(
            db,
            draft_id,
            current_user.id,
            request,
        )

        return DraftResponse.from_orm(draft)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Update draft error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update draft",
        )


@router.delete(
    "/drafts/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Draft deleted"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
    },
)
async def delete_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete draft"""
    try:
        await UploadService.delete_draft(db, draft_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Delete draft error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete draft",
        )



@router.post(
    "/drafts/{draft_id}/publish",
    responses={
        200: {"description": "Draft published"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
    },
)
async def publish_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish draft as video

    **Authorization:** Requires valid access token
    """
    try:
        video = await UploadService.publish_draft(
            db,
            draft_id,
            current_user.id,
        )

        if video.original_video_id is not None:
            original = await db.get(Video, video.original_video_id)
            if original:
                await NotificationService.send_notification(
                    db,
                    user_id=original.user_id,
                    notification_type=NotificationType.DUET_STITCH,
                    title=f"{current_user.username} made a {video.remix_type.value} with your video",
                    actor_id=current_user.id,
                    related_video_id=video.id,
                )

        return {
            "message": "Draft published successfully",
            "video_id": str(video.id),
            "status": "published",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not found" not in str(e).lower() else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Publish draft error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish draft",
        )


@router.post(
    "/drafts/{draft_id}/schedule",
    response_model=DraftResponse,
    responses={
        200: {"description": "Draft scheduled"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
    },
)
async def schedule_draft(
    draft_id: UUID,
    publish_at: str = Query(..., description="ISO 8601 datetime"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Schedule draft for future publishing

    **Authorization:** Requires valid access token

    **Parameters:**
    - publish_at: ISO 8601 datetime (e.g., 2024-08-15T14:30:00)
    """
    try:
        from datetime import datetime
        publish_time = datetime.fromisoformat(publish_at)

        draft = await UploadService.schedule_publish(
            db,
            draft_id,
            current_user.id,
            publish_time,
        )

        return DraftResponse.from_orm(draft)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Schedule draft error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule draft",
        )
