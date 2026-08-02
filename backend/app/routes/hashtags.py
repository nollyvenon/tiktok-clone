"""
Hashtag trending and challenges routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID

from app.models import User
from app.database import get_db
from app.routes.auth import get_current_user
from app.services.hashtags import HashtagService
from app.services.profiles import ProfileService
from app.schemas import (
    HashtagTrendResponse,
    ChallengeResponse,
    HashtagAnalyticsResponse,
    VideoDetailResponse,
    UserPublicProfile,
)

router = APIRouter(prefix="/hashtags", tags=["Hashtags"])


async def _build_video_response(db: AsyncSession, video) -> VideoDetailResponse:
    """Builds a VideoDetailResponse (with nested author) for a bare Video row."""
    author = await ProfileService.get_user_profile(db, video.user_id)
    return VideoDetailResponse(
        id=video.id,
        user_id=video.user_id,
        user=UserPublicProfile.from_orm(author),
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
        allow_comments=video.allow_comments,
        allow_duets=video.allow_duets,
        allow_stitches=video.allow_stitches,
    )


@router.get("/trending", response_model=list[HashtagTrendResponse])
async def get_trending_hashtags(
    region: str = Query("US"),
    category: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get trending hashtags by region"""
    hashtags = await HashtagService.get_trending_hashtags(
        db, region=region, category=category, limit=limit
    )
    return hashtags


@router.get("/{hashtag}/stats")
async def get_hashtag_stats(
    hashtag: str,
    region: str = Query("US"),
    db: AsyncSession = Depends(get_db),
):
    """Get hashtag statistics"""
    stats = await HashtagService.get_hashtag_stats(db, hashtag, region)
    return stats


@router.get("/{hashtag}/analytics", response_model=list[HashtagAnalyticsResponse])
async def get_hashtag_analytics(
    hashtag: str,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get hashtag analytics over time"""
    analytics = await HashtagService.get_hashtag_analytics(db, hashtag, days)
    return analytics


@router.get("/search", response_model=list[HashtagTrendResponse])
async def search_hashtags(
    q: str = Query(..., min_length=1),
    region: str = Query("US"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search hashtags by name"""
    hashtags = await HashtagService.search_hashtags(db, q, region, limit)
    return hashtags


@router.get("/category/{category}", response_model=list[HashtagTrendResponse])
async def get_category_trends(
    category: str,
    region: str = Query("US"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get trending hashtags by category"""
    hashtags = await HashtagService.get_category_trends(db, category, region, limit)
    return hashtags


@router.get("/challenges/active", response_model=list[ChallengeResponse])
async def get_active_challenges(
    region: str = Query("US"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get active challenges"""
    challenges = await HashtagService.get_active_challenges(db, region, limit)
    return challenges


@router.get("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge_details(
    challenge_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get challenge details"""
    challenge = await HashtagService.get_challenge_details(db, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@router.post("/challenges", response_model=ChallengeResponse)
async def create_challenge(
    hashtag: str,
    title: str,
    description: str = None,
    rules: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    prize_pool: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new challenge (admin only)"""
    challenge = await HashtagService.create_challenge(
        db,
        hashtag=hashtag,
        title=title,
        description=description,
        rules=rules,
        start_date=start_date,
        end_date=end_date,
        prize_pool=prize_pool,
    )
    return challenge


@router.get("/challenges/{challenge_id}/videos")
async def get_challenge_videos(
    challenge_id: UUID,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get videos for a challenge"""
    videos, total = await HashtagService.get_challenge_videos(
        db, challenge_id, limit, offset
    )
    return {
        "videos": [await _build_video_response(db, v) for v in videos],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{hashtag}/track")
async def track_hashtag_usage(
    hashtag: str,
    region: str = Query("US"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track hashtag usage when user posts video"""
    await HashtagService.track_hashtag_usage(db, hashtag, region, current_user.id)
    return {"status": "tracked"}


@router.get("/metrics/compare")
async def compare_hashtags(
    hashtags: list[str] = Query(...),
    region: str = Query("US"),
    db: AsyncSession = Depends(get_db),
):
    """Compare metrics between multiple hashtags"""
    stats = {}
    for hashtag in hashtags:
        stats[hashtag] = await HashtagService.get_hashtag_stats(db, hashtag, region)
    return stats
