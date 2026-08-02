"""
Search and discovery API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from app.database import get_db
from app.schemas import VideoDetailResponse, UserPublicProfile, ErrorResponse
from app.services.search import SearchService
from app.services.profiles import ProfileService
from app.routes.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search & Discovery"])


async def _build_video_response(db: AsyncSession, video) -> VideoDetailResponse:
    """
    Builds a VideoDetailResponse for a bare Video ORM row.

    VideoDetailResponse.user is a required UserPublicProfile - a blind
    from_orm(video) fails because Video has no populated `user` attribute
    matching that shape, only a `user_id` column.
    """
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


# ============================================================================
# Video Search
# ============================================================================

@router.get(
    "/videos",
    responses={
        200: {"description": "Video search results"},
    },
)
async def search_videos(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    duration_min: Optional[int] = Query(None, ge=0, description="Min duration in seconds"),
    duration_max: Optional[int] = Query(None, ge=0, description="Max duration in seconds"),
    sort: str = Query("relevance", description="relevance, recent, popular"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search videos by title, description, hashtags

    **Sort options:**
    - relevance: Best match by engagement
    - recent: Newest videos first
    - popular: Most views first

    **Filters:**
    - duration_min/max: Filter by video length
    """
    try:
        videos, total = await SearchService.search_videos(
            db,
            q,
            limit=limit,
            offset=offset,
            duration_min=duration_min,
            duration_max=duration_max,
            sort_by=sort,
        )

        return {
            "results": [await _build_video_response(db, v) for v in videos],
            "total": total,
            "limit": limit,
            "offset": offset,
            "query": q,
        }
    except Exception as e:
        logger.error(f"Video search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


# ============================================================================
# Creator Search
# ============================================================================

@router.get(
    "/creators",
    responses={
        200: {"description": "Creator search results"},
    },
)
async def search_creators(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search creators by username or display name"""
    try:
        creators, total = await SearchService.search_creators(
            db, q, limit=limit, offset=offset
        )

        return {
            "results": [UserPublicProfile.from_orm(c) for c in creators],
            "total": total,
            "limit": limit,
            "offset": offset,
            "query": q,
        }
    except Exception as e:
        logger.error(f"Creator search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


# ============================================================================
# Hashtag Search
# ============================================================================

@router.get(
    "/hashtags",
    responses={
        200: {"description": "Hashtag suggestions"},
    },
)
async def search_hashtags(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search hashtags by name with usage count"""
    try:
        hashtags = await SearchService.search_hashtags(db, q, limit=limit)

        return {
            "results": hashtags,
            "total": len(hashtags),
            "query": q,
        }
    except Exception as e:
        logger.error(f"Hashtag search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


# ============================================================================
# Global Search Suggestions
# ============================================================================

@router.get(
    "/suggestions",
    responses={
        200: {"description": "Search suggestions"},
    },
)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get search suggestions (creators, hashtags)
    Used for search autocomplete
    """
    try:
        suggestions = await SearchService.get_search_suggestions(db, q)
        return suggestions
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suggestions",
        )


# ============================================================================
# Discover by Category
# ============================================================================

@router.get(
    "/discover/{category}",
    responses={
        200: {"description": "Category videos"},
    },
)
async def discover_by_category(
    category: str,
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Discover videos by category/genre

    **Categories:**
    - music, dance, comedy, cooking, fitness
    - education, travel, fashion, beauty, sports
    - gaming, vlog, tutorial, challenge, trends
    """
    try:
        videos = await SearchService.get_discover_by_category(db, category, limit)

        return {
            "category": category,
            "results": [await _build_video_response(db, v) for v in videos],
            "total": len(videos),
        }
    except Exception as e:
        logger.error(f"Discover error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover videos",
        )


# ============================================================================
# Advanced Search
# ============================================================================

@router.get(
    "/advanced",
    responses={
        200: {"description": "Advanced search results"},
    },
)
async def advanced_search(
    q: Optional[str] = Query(None),
    creator_id: Optional[UUID] = Query(None),
    hashtags: Optional[str] = Query(None, description="Comma-separated hashtags"),
    min_views: Optional[int] = Query(None, ge=0),
    max_duration: Optional[int] = Query(None, ge=0, description="In seconds"),
    after_date: Optional[str] = Query(None, description="ISO date format"),
    before_date: Optional[str] = Query(None, description="ISO date format"),
    sort: str = Query("relevance", description="relevance, recent, popular"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Advanced video search with multiple filters

    **Parameters:**
    - q: Text search query
    - creator_id: Filter by creator UUID
    - hashtags: Comma-separated hashtags
    - min_views: Minimum view count
    - max_duration: Maximum duration in seconds
    - after_date: Videos after date (ISO format)
    - before_date: Videos before date (ISO format)
    - sort: Sort by relevance, recent, or popular
    """
    try:
        # Parse hashtags
        hashtag_list = None
        if hashtags:
            hashtag_list = [h.strip() for h in hashtags.split(",")]

        # Parse dates
        after = None
        before = None
        if after_date:
            from datetime import datetime
            after = datetime.fromisoformat(after_date)
        if before_date:
            from datetime import datetime
            before = datetime.fromisoformat(before_date)

        videos, total = await SearchService.search_advanced(
            db,
            query=q,
            creator_id=creator_id,
            hashtags=hashtag_list,
            min_views=min_views,
            max_duration=max_duration,
            after_date=after,
            before_date=before,
            sort_by=sort,
            limit=limit,
            offset=offset,
        )

        return {
            "results": [await _build_video_response(db, v) for v in videos],
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": {
                "query": q,
                "creator_id": str(creator_id) if creator_id else None,
                "hashtags": hashtag_list,
                "min_views": min_views,
                "max_duration": max_duration,
                "after_date": after_date,
                "before_date": before_date,
            },
        }
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )
