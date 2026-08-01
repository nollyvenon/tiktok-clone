"""
Recommendation engine API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.schemas import (
    RecommendationsListResponse, RecommendationResponse,
    UserPreferenceResponse, UserPreferenceUpdate,
    RecommendationFeedbackRequest, ABTestResponse, ErrorResponse
)
from app.services.recommendations import RecommendationService
from app.routes.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# ============================================================================
# Personalized Feed
# ============================================================================

@router.get(
    "/for-you",
    response_model=RecommendationsListResponse,
    responses={
        200: {"description": "Personalized recommendations"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_for_you_feed(
    limit: int = Query(30, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get personalized For-You feed with ML recommendations

    **Algorithm:** Ensemble of:
    - Collaborative filtering (users with similar taste)
    - Content-based filtering (similar to liked videos)
    - Social graph (from followed creators)
    - Trending algorithm (viral content)

    **Personalization factors:**
    - User watch history
    - Engagement patterns (likes, bookmarks, shares)
    - User preferences (hashtags, creators, genres)
    - Time spent on videos
    - Device and location
    """
    try:
        recommendations, next_cursor = await RecommendationService.get_for_you_feed(
            db, current_user.id, limit, cursor
        )

        return RecommendationsListResponse(
            recommendations=[RecommendationResponse.from_orm(r) for r in recommendations],
            cursor=next_cursor,
            total=len(recommendations),
        )
    except Exception as e:
        logger.error(f"Get for-you feed error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommendations",
        )


@router.post(
    "/compute",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Recommendations queued for computation"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def compute_fresh_recommendations(
    limit: int = Query(100, ge=10, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger fresh recommendation computation

    Computes new recommendations using multiple algorithms:
    - Collaborative filtering
    - Content-based filtering
    - Social signals
    - Trending content
    - Engagement metrics
    """
    try:
        recommendations = await RecommendationService.compute_recommendations(
            db, current_user.id, limit
        )

        return {
            "status": "computed",
            "count": len(recommendations),
            "message": f"Generated {len(recommendations)} recommendations",
        }
    except Exception as e:
        logger.error(f"Compute recommendations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute recommendations",
        )


# ============================================================================
# Similar Videos
# ============================================================================

@router.get(
    "/similar/{video_id}",
    response_model=RecommendationsListResponse,
    responses={
        200: {"description": "Similar videos"},
        404: {"model": ErrorResponse, "description": "Video not found"},
    },
)
async def get_similar_videos(
    video_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get videos similar to given video

    **Similarity factors:**
    - Shared hashtags
    - Same creator/channel
    - Similar genre/category
    - Similar engagement patterns
    - Co-viewed videos
    """
    try:
        similar_videos = await RecommendationService.get_similar_videos(
            db, video_id, limit
        )

        return RecommendationsListResponse(
            recommendations=[{"video": v} for v in similar_videos],
            total=len(similar_videos),
        )
    except Exception as e:
        logger.error(f"Get similar videos error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve similar videos",
        )


# ============================================================================
# User Preferences
# ============================================================================

@router.get(
    "/preferences",
    response_model=UserPreferenceResponse,
    responses={
        200: {"description": "User preferences"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's recommendation preferences"""
    try:
        prefs = await RecommendationService.get_or_create_user_preferences(db, current_user.id)
        return UserPreferenceResponse.from_orm(prefs)
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences",
        )


@router.put(
    "/preferences",
    response_model=UserPreferenceResponse,
    responses={
        200: {"description": "Preferences updated"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def update_user_preferences(
    update: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user's recommendation preferences

    **Customizable preferences:**
    - Preferred creators and channels
    - Preferred hashtags and topics
    - Preferred genres
    - Preferred languages
    - Content diversity score (0 = niche, 1 = diverse)
    - Recency preference (0 = older content, 1 = recent)
    """
    try:
        prefs = await RecommendationService.update_user_preferences(
            db, current_user.id, update
        )
        return UserPreferenceResponse.from_orm(prefs)
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences",
        )


# ============================================================================
# Recommendation Feedback
# ============================================================================

@router.post(
    "/{recommendation_id}/feedback",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Feedback recorded"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def record_recommendation_feedback(
    recommendation_id: UUID,
    feedback: RecommendationFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record feedback on recommendation quality

    **Feedback types:**
    - relevant: Video was useful/interesting
    - irrelevant: Video was not relevant
    - duplicate: Similar to other videos
    - nsfw: Inappropriate content
    - not_interested: Not interested in this type of content

    **Feedback helps:**
    - Improve recommendation algorithm
    - Personalize feed better
    - Reduce irrelevant recommendations
    - Train machine learning models
    """
    try:
        fb = await RecommendationService.record_recommendation_feedback(
            db,
            recommendation_id,
            current_user.id,
            feedback.feedback_type,
            feedback.rating,
            feedback.reason,
        )

        return {
            "status": "recorded",
            "message": "Thank you for the feedback",
        }
    except Exception as e:
        logger.error(f"Record feedback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback",
        )


# ============================================================================
# Analytics
# ============================================================================

@router.get(
    "/stats",
    responses={
        200: {"description": "Recommendation statistics"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_recommendation_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recommendation system statistics

    **Metrics:**
    - Total recommendations shown
    - Click-through rate (CTR)
    - Watch rate
    - Like rate
    - Algorithm performance
    - Diversity score
    """
    try:
        stats = await RecommendationService.get_recommendation_stats(db, current_user.id)
        return stats
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


# ============================================================================
# A/B Testing
# ============================================================================

@router.get(
    "/ab-tests/active",
    responses={
        200: {"description": "Active A/B tests"},
    },
)
async def get_active_ab_tests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active A/B tests for recommendation algorithm"""
    try:
        tests = await RecommendationService.get_active_ab_tests(db)
        return {
            "tests": [ABTestResponse.from_orm(t) for t in tests],
            "total": len(tests),
        }
    except Exception as e:
        logger.error(f"Get A/B tests error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B tests",
        )


# ============================================================================
# Algorithm Info
# ============================================================================

@router.get(
    "/algorithm/info",
    responses={
        200: {"description": "Algorithm information"},
    },
)
async def get_algorithm_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get information about the recommendation algorithm

    **Algorithm components:**
    - Collaborative Filtering (35%): Users with similar taste
    - Content-Based (30%): Similar to liked videos
    - Social (15%): From followed creators
    - Trending (20%): Popular/viral videos

    **Real-time factors:**
    - User engagement (likes, watches, shares)
    - Video popularity and growth
    - User preference updates
    - Time of day and user activity patterns
    """
    return {
        "algorithm": "ensemble",
        "version": "v2.0",
        "components": {
            "collaborative_filtering": {
                "weight": 0.35,
                "description": "Recommendations based on users with similar taste",
            },
            "content_based": {
                "weight": 0.30,
                "description": "Videos similar to content user has liked",
            },
            "social_graph": {
                "weight": 0.15,
                "description": "Videos from followed creators",
            },
            "trending": {
                "weight": 0.20,
                "description": "Popular and viral content",
            },
        },
        "update_frequency": "real-time with batch updates every 6 hours",
        "personalization_factors": [
            "Watch history",
            "Engagement patterns",
            "User preferences",
            "Social connections",
            "Time spent on videos",
            "Device and location",
            "Trending content",
        ],
    }
