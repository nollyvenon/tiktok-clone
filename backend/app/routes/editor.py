"""
Video editor API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging
from uuid import UUID

from app.database import get_db
from app.schemas import (
    SegmentCreate, SegmentResponse, TextOverlayCreate, TextOverlayResponse,
    StickerCreate, StickerResponse, EditorStateResponse, ExportResponse,
    ErrorResponse
)
from app.services.editor import EditorService
from app.services.uploads import UploadService
from app.routes.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/editor", tags=["Video Editor"])


# ============================================================================
# Segment Management
# ============================================================================

@router.post(
    "/drafts/{draft_id}/segments",
    response_model=SegmentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Segment created"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
    },
)
async def add_segment(
    draft_id: UUID,
    request: SegmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add segment to timeline

    **Authorization:** Requires valid access token

    **Parameters:**
    - draft_id: Draft UUID

    **Request body:**
    - content_type: video, image, text, music, voiceover
    - content_url: URL to content
    - start_time: Start time in milliseconds
    - end_time: End time in milliseconds
    """
    try:
        # Verify ownership
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

        segment = await EditorService.add_segment(db, draft_id, request)
        return SegmentResponse.from_orm(segment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add segment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add segment",
        )


@router.get(
    "/drafts/{draft_id}/segments",
    responses={
        200: {"description": "Segments list"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
    },
)
async def get_segments(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all segments for draft"""
    try:
        segments = await EditorService.get_segments(db, draft_id)
        return {
            "segments": [SegmentResponse.from_orm(s) for s in segments],
            "total": len(segments),
        }
    except Exception as e:
        logger.error(f"Get segments error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve segments",
        )


@router.put(
    "/segments/{segment_id}",
    response_model=SegmentResponse,
    responses={
        200: {"description": "Segment updated"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def update_segment(
    segment_id: UUID,
    request: SegmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update segment"""
    try:
        segment = await EditorService.update_segment(db, segment_id, request)
        return SegmentResponse.from_orm(segment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Update segment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update segment",
        )


@router.delete(
    "/segments/{segment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Segment deleted"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def delete_segment(
    segment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete segment"""
    try:
        await EditorService.delete_segment(db, segment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Delete segment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete segment",
        )


@router.post(
    "/drafts/{draft_id}/reorder-segments",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Segments reordered"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def reorder_segments(
    draft_id: UUID,
    segment_ids: List[UUID] = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder segments in timeline"""
    try:
        await EditorService.reorder_segments(db, draft_id, segment_ids)
        return {"message": "Segments reordered"}
    except Exception as e:
        logger.error(f"Reorder segments error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder segments",
        )


# ============================================================================
# Text Overlays
# ============================================================================

@router.post(
    "/segments/{segment_id}/overlays",
    response_model=TextOverlayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_text_overlay(
    segment_id: UUID,
    request: TextOverlayCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add text overlay to segment"""
    try:
        overlay = await EditorService.add_text_overlay(db, segment_id, request)
        return TextOverlayResponse.from_orm(overlay)
    except Exception as e:
        logger.error(f"Add text overlay error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add text overlay",
        )


@router.get(
    "/segments/{segment_id}/overlays",
    responses={
        200: {"description": "Text overlays"},
    },
)
async def get_text_overlays(
    segment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get text overlays for segment"""
    try:
        overlays = await EditorService.get_text_overlays(db, segment_id)
        return {
            "overlays": [TextOverlayResponse.from_orm(o) for o in overlays],
            "total": len(overlays),
        }
    except Exception as e:
        logger.error(f"Get text overlays error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overlays",
        )


@router.delete(
    "/overlays/{overlay_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_text_overlay(
    overlay_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete text overlay"""
    try:
        await EditorService.delete_text_overlay(db, overlay_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Delete text overlay error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete overlay",
        )


# ============================================================================
# Stickers
# ============================================================================

@router.post(
    "/segments/{segment_id}/stickers",
    response_model=StickerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_sticker(
    segment_id: UUID,
    request: StickerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add sticker to segment"""
    try:
        sticker = await EditorService.add_sticker(db, segment_id, request)
        return StickerResponse.from_orm(sticker)
    except Exception as e:
        logger.error(f"Add sticker error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add sticker",
        )


@router.get(
    "/segments/{segment_id}/stickers",
    responses={
        200: {"description": "Stickers"},
    },
)
async def get_stickers(
    segment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get stickers for segment"""
    try:
        stickers = await EditorService.get_stickers(db, segment_id)
        return {
            "stickers": [StickerResponse.from_orm(s) for s in stickers],
            "total": len(stickers),
        }
    except Exception as e:
        logger.error(f"Get stickers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stickers",
        )


@router.delete(
    "/stickers/{sticker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_sticker(
    sticker_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete sticker"""
    try:
        await EditorService.delete_sticker(db, sticker_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Delete sticker error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sticker",
        )


# ============================================================================
# Effects & Editing
# ============================================================================

@router.post(
    "/segments/{segment_id}/effects/{effect_name}",
    response_model=SegmentResponse,
)
async def apply_effect(
    segment_id: UUID,
    effect_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply effect to segment (blur, brighten, saturate, etc.)"""
    try:
        segment = await EditorService.apply_effect(db, segment_id, effect_name)
        return SegmentResponse.from_orm(segment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Apply effect error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply effect",
        )


@router.post(
    "/segments/{segment_id}/trim",
    response_model=SegmentResponse,
)
async def trim_video(
    segment_id: UUID,
    start_time: int = Query(..., ge=0),
    end_time: int = Query(..., ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trim segment to specific time range"""
    try:
        segment = await EditorService.trim_video(db, segment_id, start_time, end_time)
        return SegmentResponse.from_orm(segment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Trim video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trim video",
        )


@router.post(
    "/segments/{segment_id}/speed",
    response_model=SegmentResponse,
)
async def adjust_speed(
    segment_id: UUID,
    speed: float = Query(..., ge=0.25, le=4.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adjust playback speed (0.25-4.0x)"""
    try:
        segment = await EditorService.adjust_speed(db, segment_id, speed)
        return SegmentResponse.from_orm(segment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Adjust speed error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust speed",
        )


@router.post(
    "/segments/{segment_id}/volume",
    response_model=SegmentResponse,
)
async def adjust_volume(
    segment_id: UUID,
    volume: int = Query(..., ge=0, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adjust segment volume (0-100%)"""
    try:
        segment = await EditorService.adjust_volume(db, segment_id, volume)
        return SegmentResponse.from_orm(segment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Adjust volume error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust volume",
        )


@router.post(
    "/segments/{segment_id}/mute",
    response_model=SegmentResponse,
)
async def mute_segment(
    segment_id: UUID,
    muted: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mute or unmute segment audio"""
    try:
        segment = await EditorService.mute_segment(db, segment_id, muted)
        return SegmentResponse.from_orm(segment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Mute segment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mute segment",
        )


# ============================================================================
# Editor State & Export
# ============================================================================

@router.get(
    "/drafts/{draft_id}/state",
    response_model=EditorStateResponse,
)
async def get_editor_state(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get complete editor state (segments, overlays, stickers, duration)"""
    try:
        state = await EditorService.get_editor_state(db, draft_id)
        return state
    except Exception as e:
        logger.error(f"Get editor state error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve editor state",
        )


@router.post(
    "/drafts/{draft_id}/export",
    response_model=ExportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def export_video(
    draft_id: UUID,
    quality: str = Query("1080p", description="360p, 720p, 1080p, 4k"),
    format: str = Query("mp4", description="mp4, webm, mov"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export edited video (queues for processing)

    **Authorization:** Requires valid access token

    **Parameters:**
    - quality: 360p, 720p, 1080p, 4k
    - format: mp4, webm, mov
    """
    try:
        # Verify ownership
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

        export = await EditorService.export_video(db, draft_id, quality, format)
        return export
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export video",
        )
