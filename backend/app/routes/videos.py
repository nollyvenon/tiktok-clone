"""
Video API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from uuid import UUID

from app.database import get_db
from app.schemas import (
    VideoCreate, VideoUpdate, VideoResponse, VideoDetailResponse,
    FeedResponse, LikeResponse, BookmarkResponse, ViewTrackingRequest,
    VideoAnalytics, ErrorResponse, UserPublicProfile, OriginalVideoPreview,
    CreatorDashboardResponse
)
from app.services.videos import VideoService
from app.services.profiles import ProfileService
from app.services.notifications import NotificationService
from app.routes.auth import get_current_user, get_optional_current_user
from app.models import User, NotificationType, Video, RemixType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Videos"])


async def _build_original_video_preview(db: AsyncSession, video: Video) -> Optional[OriginalVideoPreview]:
    """Builds the duet/stitch attribution preview for a remix video, if any"""
    if video.original_video_id is None:
        return None
    original = await db.get(Video, video.original_video_id)
    if not original:
        return None
    original_user = await ProfileService.get_user_profile(db, original.user_id)
    return OriginalVideoPreview(
        id=original.id,
        title=original.title,
        thumbnail_url=original.thumbnail_url,
        user=UserPublicProfile.from_orm(original_user),
    )


# ============================================================================
# Feed Endpoints
# ============================================================================

@router.get(
    "/feed",
    response_model=FeedResponse,
    responses={
        200: {"description": "Video feed"},
    },
)
async def get_feed(
    feed_type: str = Query("for_you", description="'for_you' or 'following'"),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get video feed

    **Parameters:**
    - feed_type: 'for_you' (default) or 'following'
    - limit: Number of videos (1-50, default 10)
    - offset: Pagination offset (default 0)

    **Returns:** Video feed with pagination cursor
    """
    try:
        user_id = current_user.id if current_user else None
        videos, total = await VideoService.get_feed(
            db, user_id=user_id, limit=limit, offset=offset, feed_type=feed_type
        )

        # Build responses with engagement status
        video_responses = []
        for video in videos:
            is_liked = False
            is_bookmarked = False
            if current_user:
                is_liked = await VideoService.is_liked(db, current_user.id, video.id)
                is_bookmarked = await VideoService.is_bookmarked(db, current_user.id, video.id)

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
                    is_liked=is_liked,
                    is_bookmarked=is_bookmarked,
                    allow_comments=video.allow_comments,
                    allow_duets=video.allow_duets,
                    allow_stitches=video.allow_stitches,
                    remix_type=video.remix_type,
                    original_video=await _build_original_video_preview(db, video),
                )
            )

        return FeedResponse(
            videos=video_responses,
            cursor=None,  # TODO: Implement cursor-based pagination
            total=total,
        )
    except Exception as e:
        logger.error(f"Get feed error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feed",
        )


# ============================================================================
# Search & Trending
# ============================================================================

@router.get(
    "/search/trending",
    response_model=FeedResponse,
    responses={
        200: {"description": "Trending videos"},
    },
)
async def get_trending(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    timeframe_hours: int = Query(24, ge=1, le=168),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trending videos

    **Parameters:**
    - limit: Number of videos (default 20)
    - offset: Pagination offset
    - timeframe_hours: Time period (1-168 hours, default 24)
    """
    try:
        videos, total = await VideoService.get_trending_videos(
            db, limit=limit, offset=offset, timeframe_hours=timeframe_hours
        )

        video_responses = []
        for video in videos:
            user = await ProfileService.get_user_profile(db, video.user_id)
            is_liked = False
            is_bookmarked = False
            if current_user:
                is_liked = await VideoService.is_liked(db, current_user.id, video.id)
                is_bookmarked = await VideoService.is_bookmarked(db, current_user.id, video.id)

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
                    is_liked=is_liked,
                    is_bookmarked=is_bookmarked,
                    allow_comments=video.allow_comments,
                    allow_duets=video.allow_duets,
                    allow_stitches=video.allow_stitches,
                    remix_type=video.remix_type,
                    original_video=await _build_original_video_preview(db, video),
                )
            )

        return FeedResponse(videos=video_responses, total=total)
    except Exception as e:
        logger.error(f"Get trending error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trending videos",
        )


@router.get(
    "/search",
    response_model=FeedResponse,
    responses={
        200: {"description": "Search results"},
    },
)
async def search_videos(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search videos

    **Parameters:**
    - q: Search query (required)
    - limit: Number of results (default 20)
    - offset: Pagination offset
    """
    try:
        videos, total = await VideoService.search_videos(db, q, limit=limit, offset=offset)

        video_responses = []
        for video in videos:
            user = await ProfileService.get_user_profile(db, video.user_id)
            is_liked = False
            is_bookmarked = False
            if current_user:
                is_liked = await VideoService.is_liked(db, current_user.id, video.id)
                is_bookmarked = await VideoService.is_bookmarked(db, current_user.id, video.id)

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
                    is_liked=is_liked,
                    is_bookmarked=is_bookmarked,
                    allow_comments=video.allow_comments,
                    allow_duets=video.allow_duets,
                    allow_stitches=video.allow_stitches,
                    remix_type=video.remix_type,
                    original_video=await _build_original_video_preview(db, video),
                )
            )

        return FeedResponse(videos=video_responses, total=total)
    except Exception as e:
        logger.error(f"Search videos error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search videos",
        )


@router.get(
    "/dashboard",
    response_model=CreatorDashboardResponse,
    responses={
        200: {"description": "Creator analytics dashboard"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_creator_dashboard(
    top_videos_limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregate analytics across all of the current user's own videos

    **Authorization:** Requires valid access token - this is the owner's
    own dashboard, not a public-facing view.
    """
    try:
        return await VideoService.get_creator_dashboard(
            db, current_user.id, top_videos_limit=top_videos_limit
        )
    except Exception as e:
        logger.error(f"Get creator dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard",
        )


@router.get(
    "/bookmarks",
    response_model=FeedResponse,
    responses={
        200: {"description": "Bookmarked videos"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_bookmarked_videos(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user's bookmarked videos, most recently saved first

    **Authorization:** Requires valid access token - bookmarks are private
    and never exposed for any user other than their owner.
    """
    try:
        videos, total = await VideoService.get_bookmarked_videos(
            db, current_user.id, limit=limit, offset=offset
        )

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
                    is_liked=await VideoService.is_liked(db, current_user.id, video.id),
                    is_bookmarked=True,
                    allow_comments=video.allow_comments,
                    allow_duets=video.allow_duets,
                    allow_stitches=video.allow_stitches,
                    remix_type=video.remix_type,
                    original_video=await _build_original_video_preview(db, video),
                )
            )

        return FeedResponse(videos=video_responses, total=total)
    except Exception as e:
        logger.error(f"Get bookmarked videos error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookmarked videos",
        )


@router.get(
    "/{video_id}",
    response_model=VideoDetailResponse,
    responses={
        200: {"description": "Video retrieved"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def get_video(
    video_id: UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get video by ID

    **Parameters:**
    - video_id: Video UUID

    **Returns:** Video with full details
    """
    try:
        video = await VideoService.get_video(db, video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )

        user = await ProfileService.get_user_profile(db, video.user_id)

        is_liked = False
        is_bookmarked = False
        if current_user:
            is_liked = await VideoService.is_liked(db, current_user.id, video_id)
            is_bookmarked = await VideoService.is_bookmarked(db, current_user.id, video_id)

        return VideoDetailResponse(
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
            is_liked=is_liked,
            is_bookmarked=is_bookmarked,
            allow_comments=video.allow_comments,
            allow_duets=video.allow_duets,
            allow_stitches=video.allow_stitches,
            remix_type=video.remix_type,
            original_video=await _build_original_video_preview(db, video),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video",
        )


@router.get(
    "/user/{user_id}/videos",
    response_model=FeedResponse,
    responses={
        200: {"description": "User videos"},
    },
)
async def get_user_videos(
    user_id: UUID,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get videos by a specific user

    **Parameters:**
    - user_id: User UUID
    - limit: Number of videos (default 20)
    - offset: Pagination offset
    """
    try:
        videos, total = await VideoService.get_user_videos(
            db, user_id, limit=limit, offset=offset
        )

        video_responses = []
        for video in videos:
            user = await ProfileService.get_user_profile(db, video.user_id)
            is_liked = False
            is_bookmarked = False
            if current_user:
                is_liked = await VideoService.is_liked(db, current_user.id, video.id)
                is_bookmarked = await VideoService.is_bookmarked(db, current_user.id, video.id)

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
                    is_liked=is_liked,
                    is_bookmarked=is_bookmarked,
                    allow_comments=video.allow_comments,
                    allow_duets=video.allow_duets,
                    allow_stitches=video.allow_stitches,
                    remix_type=video.remix_type,
                    original_video=await _build_original_video_preview(db, video),
                )
            )

        return FeedResponse(videos=video_responses, total=total)
    except Exception as e:
        logger.error(f"Get user videos error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user videos",
        )


# ============================================================================
# Video Management (Protected)
# ============================================================================

@router.post(
    "",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Video created"},
        400: {"model": ErrorResponse, "description": "Invalid data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def create_video(
    request: VideoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new video

    **Authorization:** Requires valid access token

    **Request body:**
    - title: Video title (optional)
    - description: Video description (max 2200 chars)
    - video_url: URL to video file
    - thumbnail_url: URL to thumbnail
    - duration: Video duration in seconds
    - hashtags: Comma-separated hashtags
    - is_public: Publish publicly (default true)
    - allow_comments: Allow comments (default true)
    """
    try:
        video = await VideoService.create_video(db, current_user.id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Create video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video",
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

    return VideoResponse.from_orm(video)


@router.put(
    "/{video_id}",
    response_model=VideoResponse,
    responses={
        200: {"description": "Video updated"},
        400: {"model": ErrorResponse, "description": "Invalid data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def update_video(
    video_id: UUID,
    request: VideoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update video

    **Authorization:** Requires valid access token (must be creator)
    """
    try:
        video = await VideoService.update_video(db, video_id, current_user.id, request)
        return VideoResponse.from_orm(video)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if str(e) != "Not authorized to update this video" else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Update video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update video",
        )


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Video deleted"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def delete_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete video

    **Authorization:** Requires valid access token (must be creator)
    """
    try:
        await VideoService.delete_video(db, video_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if str(e) != "Not authorized to delete this video" else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Delete video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video",
        )


# ============================================================================
# Engagement Endpoints
# ============================================================================

@router.post(
    "/{video_id}/like",
    response_model=LikeResponse,
    responses={
        200: {"description": "Like status changed"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def like_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Like or unlike a video

    **Authorization:** Requires valid access token
    """
    try:
        is_liked, likes_count = await VideoService.like_video(db, current_user.id, video_id)
        if is_liked:
            video = await VideoService.get_video(db, video_id)
            if video:
                await NotificationService.send_notification(
                    db,
                    user_id=video.user_id,
                    notification_type=NotificationType.LIKE,
                    title=f"{current_user.username} liked your video",
                    actor_id=current_user.id,
                    related_video_id=video_id,
                )
        return LikeResponse(is_liked=is_liked, likes_count=likes_count)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Like video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to like video",
        )


@router.post(
    "/{video_id}/bookmark",
    response_model=BookmarkResponse,
    responses={
        200: {"description": "Bookmark status changed"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def bookmark_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bookmark or unbookmark a video

    **Authorization:** Requires valid access token
    """
    try:
        is_bookmarked, bookmarks_count = await VideoService.bookmark_video(
            db, current_user.id, video_id
        )
        return BookmarkResponse(is_bookmarked=is_bookmarked, bookmarks_count=bookmarks_count)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Bookmark video error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bookmark video",
        )


@router.post(
    "/{video_id}/view",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "View tracked"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def track_view(
    video_id: UUID,
    request: ViewTrackingRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Track video view/watch

    **Parameters:**
    - watch_time: Seconds watched
    - completed: User watched to end (boolean)
    - device_type: Device type (mobile, desktop, tablet)
    - platform: Platform (iOS, Android, Web)
    """
    try:
        user_id = current_user.id if current_user else None
        await VideoService.track_view(
            db,
            user_id=user_id,
            video_id=video_id,
            watch_time=request.watch_time,
            completed=request.completed,
            device_type=request.device_type,
            platform=request.platform,
            country=request.country,
        )
        return {"message": "View tracked"}
    except Exception as e:
        logger.error(f"Track view error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track view",
        )


@router.get(
    "/{video_id}/remixes",
    response_model=FeedResponse,
    responses={200: {"description": "Duets/stitches made from this video"}},
)
async def get_remixes(
    video_id: UUID,
    remix_type: Optional[str] = Query(None, description="'duet' or 'stitch' - omit for both"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get duets and/or stitches made from this video, newest first"""
    parsed_type = None
    if remix_type is not None:
        try:
            parsed_type = RemixType(remix_type)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="remix_type must be 'duet' or 'stitch'")

    try:
        videos, total = await VideoService.get_remixes(
            db, video_id, remix_type=parsed_type, limit=limit, offset=offset
        )

        video_responses = []
        for video in videos:
            user = await ProfileService.get_user_profile(db, video.user_id)
            is_liked = False
            is_bookmarked = False
            if current_user:
                is_liked = await VideoService.is_liked(db, current_user.id, video.id)
                is_bookmarked = await VideoService.is_bookmarked(db, current_user.id, video.id)

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
                    is_liked=is_liked,
                    is_bookmarked=is_bookmarked,
                    allow_comments=video.allow_comments,
                    allow_duets=video.allow_duets,
                    allow_stitches=video.allow_stitches,
                    remix_type=video.remix_type,
                    original_video=await _build_original_video_preview(db, video),
                )
            )

        return FeedResponse(videos=video_responses, total=total)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get remixes error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve remixes",
        )


@router.get(
    "/{video_id}/analytics",
    response_model=VideoAnalytics,
    responses={
        200: {"description": "Video analytics"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def get_analytics(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get video analytics (creator only)

    **Authorization:** Requires valid access token (must be creator)
    """
    try:
        analytics = await VideoService.get_video_analytics(db, video_id, current_user.id)
        return analytics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics",
        )


