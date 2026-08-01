"""
AI Creator Studio API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas import (
    BackgroundRemovalRequest, BackgroundRemovalResponse, VoiceoverRequest,
    VoiceoverResponse, AutoCaptionRequest, AutoCaptionResponse,
    SoundRecommendationsListResponse, SoundRecommendationResponse,
    ColorCorrectionRequest, ColorCorrectionResponse, AutoFrameResponse,
    TrendSuggestionsListResponse, TrendSuggestionResponse,
    AIGenerationResponse, AICreditsResponse, AIOperationHistoryResponse,
    ErrorResponse
)
from app.services.ai import AIService
from app.services.uploads import UploadService
from app.routes.auth import get_current_user
from app.models import User, Segment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Creator Studio"])


# ============================================================================
# Background Removal
# ============================================================================

@router.post(
    "/background-removal",
    response_model=BackgroundRemovalResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Background removal operation queued"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Segment not found"},
    },
)
async def remove_background(
    request: BackgroundRemovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove or replace background in video segment

    **Authorization:** Requires valid access token

    **Request body:**
    - segment_id: UUID of segment
    - mode: blur, remove, replace, green_screen
    - blur_level: 0-10 (for blur mode)
    - background_url: URL to replacement background (for replace mode)
    - background_type: image, video, color, blur
    """
    try:
        # Get segment and verify ownership
        result = await db.execute(
            select(Segment).where(Segment.id == request.segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Segment not found",
            )

        # Verify draft ownership
        draft = await UploadService.get_draft(db, segment.draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        bg_removal, ai_gen = await AIService.remove_background(
            db, current_user.id, request.segment_id, request
        )

        return BackgroundRemovalResponse.from_orm(bg_removal)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Background removal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process background removal",
        )


@router.get(
    "/background-removal/{removal_id}",
    response_model=BackgroundRemovalResponse,
)
async def get_background_removal(
    removal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get background removal operation status"""
    try:
        removal = await AIService.get_background_removal(db, removal_id)
        if not removal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Background removal not found",
            )
        return BackgroundRemovalResponse.from_orm(removal)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get background removal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve background removal",
        )


# ============================================================================
# Voiceover Generation
# ============================================================================

@router.post(
    "/voiceover",
    response_model=VoiceoverResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_voiceover(
    request: VoiceoverRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate text-to-speech voiceover

    **Supported Languages:**
    - en (English), es (Spanish), fr (French), de (German)
    - ja (Japanese), zh (Chinese), pt (Portuguese), it (Italian)
    - ru (Russian), ko (Korean), and 20+ more

    **Speed:** 50-200% (100 = normal speed)
    **Pitch:** 50-200% (100 = normal pitch)
    **Volume:** 0-100%
    """
    try:
        # Verify segment ownership
        result = await db.execute(
            select(Segment).where(Segment.id == request.segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Segment not found",
            )

        draft = await UploadService.get_draft(db, segment.draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        voiceover, ai_gen = await AIService.generate_voiceover(
            db, current_user.id, request.segment_id, request
        )

        return VoiceoverResponse.from_orm(voiceover)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voiceover generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate voiceover",
        )


@router.get(
    "/voiceover/{voiceover_id}",
    response_model=VoiceoverResponse,
)
async def get_voiceover(
    voiceover_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get voiceover generation status"""
    try:
        voiceover = await AIService.get_voiceover(db, voiceover_id)
        if not voiceover:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voiceover not found",
            )
        return VoiceoverResponse.from_orm(voiceover)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get voiceover error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voiceover",
        )


# ============================================================================
# Auto Captions
# ============================================================================

@router.post(
    "/captions",
    response_model=AutoCaptionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_captions(
    request: AutoCaptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate automatic captions/subtitles

    **Styles:** default, bold, shadow, background
    **Positions:** top, middle, bottom
    **Font sizes:** 12-48px
    """
    try:
        # Verify segment ownership
        result = await db.execute(
            select(Segment).where(Segment.id == request.segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Segment not found",
            )

        draft = await UploadService.get_draft(db, segment.draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        caption, ai_gen = await AIService.generate_captions(
            db, current_user.id, request.segment_id, request
        )

        return AutoCaptionResponse.from_orm(caption)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Caption generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate captions",
        )


@router.get(
    "/captions/{caption_id}",
    response_model=AutoCaptionResponse,
)
async def get_captions(
    caption_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get caption generation status"""
    try:
        caption = await AIService.get_captions(db, caption_id)
        if not caption:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Captions not found",
            )
        return AutoCaptionResponse.from_orm(caption)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get captions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve captions",
        )


# ============================================================================
# Sound Recommendations
# ============================================================================

@router.get(
    "/sounds/recommendations",
    response_model=SoundRecommendationsListResponse,
)
async def get_sound_recommendations(
    category: Optional[str] = Query(None, description="background, sound_effect, music"),
    mood: Optional[str] = Query(None, description="happy, sad, epic, calm, energetic"),
    region: str = Query("US", description="US, UK, Global, etc."),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recommended sounds by category/mood

    **Categories:** background, sound_effect, music, ambient
    **Moods:** happy, sad, epic, calm, energetic, romantic, intense
    **Regions:** US, UK, IN, BR, MX, Global
    """
    try:
        sounds = await AIService.get_sound_recommendations(
            db, None, category, mood, region, limit
        )
        return SoundRecommendationsListResponse(
            sounds=[SoundRecommendationResponse.from_orm(s) for s in sounds],
            total=len(sounds),
            category=category or "all",
            region=region,
        )
    except Exception as e:
        logger.error(f"Get sound recommendations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sound recommendations",
        )


@router.get(
    "/sounds/trending",
    response_model=SoundRecommendationsListResponse,
)
async def get_trending_sounds(
    region: str = Query("US"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get currently trending sounds in region"""
    try:
        sounds = await AIService.get_trending_sounds(db, region, limit)
        return SoundRecommendationsListResponse(
            sounds=[SoundRecommendationResponse.from_orm(s) for s in sounds],
            total=len(sounds),
            category="trending",
            region=region,
        )
    except Exception as e:
        logger.error(f"Get trending sounds error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trending sounds",
        )


# ============================================================================
# Color Correction
# ============================================================================

@router.post(
    "/color-correction",
    response_model=ColorCorrectionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def apply_color_correction(
    request: ColorCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply color correction/grading

    **Methods:**
    - preset: Apply cinematic presets (cinematic, vintage, desaturated, noir)
    - auto_enhance: AI-powered auto enhancement
    - lut: Apply LUT file
    - custom: Manual adjustments

    **Adjustment Ranges:** -100 to 100 (except hue -180 to 180)
    """
    try:
        # Verify segment ownership
        result = await db.execute(
            select(Segment).where(Segment.id == request.segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Segment not found",
            )

        draft = await UploadService.get_draft(db, segment.draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        color_correction, ai_gen = await AIService.apply_color_correction(
            db, current_user.id, request.segment_id, request
        )

        return ColorCorrectionResponse.from_orm(color_correction)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Color correction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply color correction",
        )


@router.get(
    "/color-correction/{correction_id}",
    response_model=ColorCorrectionResponse,
)
async def get_color_correction(
    correction_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get color correction status"""
    try:
        correction = await AIService.get_color_correction(db, correction_id)
        if not correction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Color correction not found",
            )
        return ColorCorrectionResponse.from_orm(correction)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get color correction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve color correction",
        )


# ============================================================================
# Smart Framing
# ============================================================================

@router.post(
    "/smart-frame",
    response_model=AutoFrameResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def get_frame_suggestions(
    segment_id: UUID,
    target_aspect_ratio: str = Query("9:16", description="16:9, 9:16, 1:1, 4:3"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get smart framing suggestions for segment

    **Aspect Ratios:** 16:9, 9:16, 1:1, 4:3, 21:9
    """
    try:
        # Verify segment ownership
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Segment not found",
            )

        draft = await UploadService.get_draft(db, segment.draft_id)
        if not draft or draft.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        auto_frame, ai_gen = await AIService.get_frame_suggestions(
            db, current_user.id, segment_id, target_aspect_ratio
        )

        return AutoFrameResponse.from_orm(auto_frame)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get frame suggestions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get frame suggestions",
        )


# ============================================================================
# Trend Suggestions
# ============================================================================

@router.get(
    "/trends",
    response_model=TrendSuggestionsListResponse,
)
async def get_trend_suggestions(
    region: str = Query("US"),
    trend_type: Optional[str] = Query(None, description="hashtag, sound, effect, format"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trending suggestions for region

    **Trend Types:** hashtag, sound, effect, format, challenge
    """
    try:
        trends = await AIService.get_trend_suggestions(
            db, None, region, trend_type, limit
        )
        return TrendSuggestionsListResponse(
            trends=[TrendSuggestionResponse.from_orm(t) for t in trends],
            total=len(trends),
            region=region,
        )
    except Exception as e:
        logger.error(f"Get trend suggestions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trend suggestions",
        )


@router.get(
    "/trends/hashtags",
    response_model=TrendSuggestionsListResponse,
)
async def get_trending_hashtags(
    region: str = Query("US"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top trending hashtags in region"""
    try:
        trends = await AIService.get_trending_hashtags(db, region, limit)
        return TrendSuggestionsListResponse(
            trends=[TrendSuggestionResponse.from_orm(t) for t in trends],
            total=len(trends),
            region=region,
        )
    except Exception as e:
        logger.error(f"Get trending hashtags error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trending hashtags",
        )


@router.get(
    "/trends/sounds",
    response_model=TrendSuggestionsListResponse,
)
async def get_hot_trending_sounds(
    region: str = Query("US"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get hottest trending sounds by growth rate"""
    try:
        trends = await AIService.get_hot_trending_sounds(db, region, limit)
        return TrendSuggestionsListResponse(
            trends=[TrendSuggestionResponse.from_orm(t) for t in trends],
            total=len(trends),
            region=region,
        )
    except Exception as e:
        logger.error(f"Get hot trending sounds error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hot trending sounds",
        )


# ============================================================================
# AI Credits & History
# ============================================================================

@router.get(
    "/credits",
    response_model=AICreditsResponse,
)
async def get_ai_credits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI credits balance and usage"""
    # TODO: Integrate with user credits system
    return AICreditsResponse(
        total_credits=1000,
        available_credits=750,
        used_credits=250,
        monthly_limit=1000,
        renewal_date=None,
    )


@router.get(
    "/history/{draft_id}",
    responses={
        200: {"description": "AI operation history"},
    },
)
async def get_ai_operation_history(
    draft_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI operation history for draft"""
    try:
        history = await AIService.get_ai_operation_history(db, draft_id, limit)
        return {
            "operations": [AIGenerationResponse.from_orm(h) for h in history],
            "total": len(history),
        }
    except Exception as e:
        logger.error(f"Get AI history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI history",
        )
