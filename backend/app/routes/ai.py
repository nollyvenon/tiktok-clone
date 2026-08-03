"""
AI Creator Studio API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging
import json

from app.database import get_db
from app.schemas import (
    BackgroundRemovalRequest, BackgroundRemovalResponse, VoiceoverRequest,
    VoiceoverResponse, AutoCaptionRequest, AutoCaptionResponse,
    SoundRecommendationsListResponse, SoundRecommendationResponse, SoundCreate,
    ColorCorrectionRequest, ColorCorrectionResponse, AutoFrameResponse,
    TrendSuggestionsListResponse, TrendSuggestionResponse,
    AIGenerationResponse, AICreditsResponse, AIOperationHistoryResponse,
    ErrorResponse, FeedResponse, VideoDetailResponse, UserPublicProfile, MusicPreview,
    FilterPresetListResponse, FilterPresetResponse,
    AIAgentListResponse, AIAgentResponse, AgentExecutionResponse, AgentExecutionListResponse,
)
from app.services.ai import AIService
from app.services.ai_agents import AIAgentService
from app.services.uploads import UploadService
from app.services.videos import VideoService
from app.services.profiles import ProfileService
from app.routes.auth import get_current_user
from app.models import User, Segment, AIGeneration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Creator Studio"])


def _build_frame_response(auto_frame, generation_status: str) -> AutoFrameResponse:
    """
    Builds an AutoFrameResponse from an AutoFrame row.

    The model stores the primary crop as flat crop_x/y/width/height columns
    and alternatives as a JSON string, while the schema wants a nested
    `suggested_crop: CropSuggestion` and `alternative_crops: list[CropSuggestion]`.
    """
    import json
    from app.schemas import CropSuggestion

    alt_crops_raw = json.loads(auto_frame.alternative_crops) if auto_frame.alternative_crops else []
    return AutoFrameResponse(
        id=auto_frame.id,
        ai_generation_id=auto_frame.ai_generation_id,
        target_aspect_ratio=auto_frame.target_aspect_ratio,
        suggested_crop=CropSuggestion(
            crop_x=auto_frame.crop_x,
            crop_y=auto_frame.crop_y,
            crop_width=auto_frame.crop_width,
            crop_height=auto_frame.crop_height,
            confidence=auto_frame.confidence,
        ),
        alternative_crops=[CropSuggestion(**c) for c in alt_crops_raw],
        output_url=auto_frame.output_url,
        preview_url=auto_frame.preview_url,
        status=generation_status,
        created_at=auto_frame.created_at,
    )


def _build_caption_response(caption, generation_status: str) -> AutoCaptionResponse:
    """
    Builds an AutoCaptionResponse from an AutoCaption row.

    The model stores generated captions as a JSON string in `captions_data`
    (there is no `captions` attribute), and the response schema's `captions`
    field is a typed list - a plain from_orm()/model_validate() would either
    KeyError or silently default to [] depending on pydantic version, hiding
    real caption data.
    """
    import json

    captions_data = json.loads(caption.captions_data) if caption.captions_data else []
    return AutoCaptionResponse(
        id=caption.id,
        ai_generation_id=caption.ai_generation_id,
        language=caption.language,
        captions=captions_data,
        vtt_url=caption.vtt_url,
        status=generation_status,
        created_at=caption.created_at,
    )


async def _get_generation_status(db: AsyncSession, ai_generation_id: UUID) -> str:
    """
    Look up the processing status for an AI sub-resource.

    The BackgroundRemoval/Voiceover/AutoCaption/ColorCorrection/AutoFrame
    tables don't carry their own status column - `status` lives on the
    related AIGeneration row (ai_generation_id), so every response builder
    needs this join rather than a plain from_orm() on the sub-resource.
    """
    ai_gen = await db.get(AIGeneration, ai_generation_id)
    return ai_gen.status.value if ai_gen else "unknown"


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

        return BackgroundRemovalResponse(
            id=bg_removal.id,
            ai_generation_id=bg_removal.ai_generation_id,
            mode=bg_removal.mode,
            blur_level=bg_removal.blur_level,
            output_url=bg_removal.output_url,
            preview_url=bg_removal.preview_url,
            status=ai_gen.status.value,
            created_at=bg_removal.created_at,
        )
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
        return BackgroundRemovalResponse(
            id=removal.id,
            ai_generation_id=removal.ai_generation_id,
            mode=removal.mode,
            blur_level=removal.blur_level,
            output_url=removal.output_url,
            preview_url=removal.preview_url,
            status=await _get_generation_status(db, removal.ai_generation_id),
            created_at=removal.created_at,
        )
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

        return VoiceoverResponse(
            id=voiceover.id,
            ai_generation_id=voiceover.ai_generation_id,
            text=voiceover.text,
            language=voiceover.language,
            voice_id=voiceover.voice_id,
            audio_url=voiceover.audio_url,
            duration=voiceover.duration,
            status=ai_gen.status.value,
            created_at=voiceover.created_at,
        )
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
        return VoiceoverResponse(
            id=voiceover.id,
            ai_generation_id=voiceover.ai_generation_id,
            text=voiceover.text,
            language=voiceover.language,
            voice_id=voiceover.voice_id,
            audio_url=voiceover.audio_url,
            duration=voiceover.duration,
            status=await _get_generation_status(db, voiceover.ai_generation_id),
            created_at=voiceover.created_at,
        )
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

        return _build_caption_response(caption, ai_gen.status.value)
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
        return _build_caption_response(
            caption, await _get_generation_status(db, caption.ai_generation_id)
        )
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


@router.post(
    "/sounds",
    response_model=SoundRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sound(
    request: SoundCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Contribute a sound to the shared music/sound library

    **Authorization:** Requires valid access token

    Sounds added here are immediately browsable via
    `/ai/sounds/recommendations` and `/ai/sounds/trending`, and can be
    attached to a video draft via its `music_id` field.
    """
    try:
        sound = await AIService.create_sound(
            db,
            current_user.id,
            request.sound_url,
            request.sound_title,
            request.artist,
            request.category,
            request.mood,
            request.genre,
            request.region,
            request.duration,
            request.license_type,
            request.credit_required,
        )
        return SoundRecommendationResponse.from_orm(sound)
    except Exception as e:
        logger.error(f"Create sound error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add sound to library",
        )


@router.get(
    "/sounds/{sound_id}/videos",
    response_model=FeedResponse,
    responses={404: {"model": ErrorResponse, "description": "Sound not found"}},
)
async def get_videos_using_sound(
    sound_id: UUID,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get videos that used this sound, newest first"""
    sound = await AIService.get_sound(db, sound_id)
    if not sound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound not found")

    try:
        videos, total = await VideoService.get_videos_using_sound(db, sound_id, limit=limit, offset=offset)
        music_preview = MusicPreview(id=sound.id, sound_title=sound.sound_title, artist=sound.artist)

        video_responses = []
        for video in videos:
            user = await ProfileService.get_user_profile(db, video.user_id)
            video_responses.append(
                VideoDetailResponse(
                    id=video.id,
                    user_id=video.user_id,
                    user=UserPublicProfile.from_orm(user),
                    title=video.title,
                    description=video.description,
                    video_url=video.video_url,
                    thumbnail_url=video.thumbnail_url,
                    duration=video.duration,
                    hashtags=video.hashtags,
                    location=video.location,
                    is_public=video.is_public,
                    views_count=video.views_count,
                    likes_count=video.likes_count,
                    comments_count=video.comments_count,
                    shares_count=video.shares_count,
                    bookmarks_count=video.bookmarks_count,
                    completion_rate=video.completion_rate,
                    created_at=video.created_at,
                    published_at=video.published_at,
                    is_liked=False,
                    is_bookmarked=False,
                    allow_comments=video.allow_comments,
                    allow_duets=video.allow_duets,
                    allow_stitches=video.allow_stitches,
                    remix_type=video.remix_type,
                    music=music_preview,
                )
            )

        return FeedResponse(videos=video_responses, total=total)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get videos using sound error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve videos for this sound",
        )


# ============================================================================
# Color Correction
# ============================================================================

@router.get("/filters/presets", response_model=FilterPresetListResponse)
async def list_filter_presets(db: AsyncSession = Depends(get_db)):
    """List named color-grade filter presets, for use with the
    color-correction endpoint's method='preset'"""
    presets = await AIService.list_filter_presets(db)
    return FilterPresetListResponse(
        presets=[FilterPresetResponse.model_validate(p) for p in presets]
    )


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

        return ColorCorrectionResponse(
            id=color_correction.id,
            ai_generation_id=color_correction.ai_generation_id,
            method=color_correction.method,
            preset_name=color_correction.preset_name,
            output_url=color_correction.output_url,
            preview_url=color_correction.preview_url,
            status=ai_gen.status.value,
            created_at=color_correction.created_at,
        )
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
        return ColorCorrectionResponse(
            id=correction.id,
            ai_generation_id=correction.ai_generation_id,
            method=correction.method,
            preset_name=correction.preset_name,
            output_url=correction.output_url,
            preview_url=correction.preview_url,
            status=await _get_generation_status(db, correction.ai_generation_id),
            created_at=correction.created_at,
        )
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

        return _build_frame_response(auto_frame, ai_gen.status.value)
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


# ============================================================================
# AI Agents
# ============================================================================

@router.get("/agents", response_model=AIAgentListResponse)
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List available AI agents - named recipes that chain existing AI
    Creator Studio operations into a single one-click run"""
    agents = await AIAgentService.list_agents(db)
    return AIAgentListResponse(agents=[AIAgentResponse(**a) for a in agents])


@router.post(
    "/agents/{agent_id}/execute",
    response_model=AgentExecutionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Agent or segment not found"},
        403: {"model": ErrorResponse, "description": "Not authorized"},
    },
)
async def execute_agent(
    agent_id: UUID,
    segment_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run an agent's full step sequence against a segment"""
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    segment = result.scalar()
    if not segment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Segment not found")

    draft = await UploadService.get_draft(db, segment.draft_id)
    if not draft or draft.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        execution = await AIAgentService.execute_agent(db, current_user.id, agent_id, segment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return AgentExecutionResponse(
        id=execution.id,
        agent_id=execution.agent_id,
        segment_id=execution.segment_id,
        status=execution.status,
        steps_log=json.loads(execution.steps_log) if execution.steps_log else [],
        total_credits_used=execution.total_credits_used,
        error_message=execution.error_message,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
    )


@router.get("/agents/executions", response_model=AgentExecutionListResponse)
async def list_my_agent_executions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List your own past agent executions, newest first"""
    executions = await AIAgentService.list_my_executions(db, current_user.id)
    return AgentExecutionListResponse(executions=[
        AgentExecutionResponse(
            id=e.id,
            agent_id=e.agent_id,
            segment_id=e.segment_id,
            status=e.status,
            steps_log=json.loads(e.steps_log) if e.steps_log else [],
            total_credits_used=e.total_credits_used,
            error_message=e.error_message,
            started_at=e.started_at,
            completed_at=e.completed_at,
        )
        for e in executions
    ])
