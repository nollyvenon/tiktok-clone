"""
Recommendation engine service for personalized feed
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
import logging
import json
import random
from math import log

from app.models import (
    Recommendation, UserPreference, RecommendationFeedback,
    Video, Like, View, Follow, ABTest, VideoStatus
)
from app.schemas import UserPreferenceUpdate

logger = logging.getLogger(__name__)

# Algorithm weights
ALGORITHM_WEIGHTS = {
    "collaborative": 0.35,  # Similar users like
    "content_based": 0.30,  # Similar to liked videos
    "social": 0.15,         # From followed creators
    "trending": 0.20,       # Trending videos
}


class RecommendationService:
    """Service for personalized video recommendations"""

    @staticmethod
    async def get_for_you_feed(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 30,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Recommendation], Optional[str]]:
        """
        Get personalized For-You feed recommendations

        Args:
            db: Database session
            user_id: User ID
            limit: Number of recommendations
            cursor: Pagination cursor

        Returns:
            List of recommendations and next cursor
        """
        # Build recommendation query
        query = select(Recommendation).where(
            Recommendation.user_id == user_id
        ).order_by(desc(Recommendation.score))

        # Apply cursor if provided
        if cursor:
            # Decode cursor (could be timestamp or ID)
            try:
                cursor_id = UUID(cursor)
                result = await db.execute(
                    select(Recommendation).where(Recommendation.id == cursor_id)
                )
                cursor_rec = result.scalar()
                if cursor_rec:
                    query = query.where(Recommendation.score < cursor_rec.score)
            except (ValueError, AttributeError):
                pass

        query = query.limit(limit + 1)
        result = await db.execute(query)
        recommendations = result.scalars().all()

        # Prepare next cursor
        next_cursor = None
        if len(recommendations) > limit:
            next_cursor = str(recommendations[limit - 1].id)
            recommendations = recommendations[:limit]

        logger.info(f"Fetched {len(recommendations)} recommendations for user {user_id}")
        return recommendations, next_cursor

    @staticmethod
    async def compute_recommendations(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 100,
    ) -> List[Recommendation]:
        """
        Compute fresh recommendations for user using multiple algorithms

        Args:
            db: Database session
            user_id: User ID
            limit: Max recommendations to generate

        Returns:
            List of computed recommendations
        """
        # Get user preferences
        result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        user_prefs = result.scalar()

        # Fetch candidate videos
        videos_result = await db.execute(
            select(Video).where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                )
            ).limit(1000)
        )
        videos = videos_result.scalars().all()

        recommendations = []

        # Generate recommendations using multiple algorithms
        for video in videos:
            score = 0

            # 1. Collaborative filtering (similar users)
            score += await RecommendationService._score_collaborative(
                db, user_id, video
            ) * ALGORITHM_WEIGHTS["collaborative"]

            # 2. Content-based filtering
            score += await RecommendationService._score_content_based(
                db, user_id, video, user_prefs
            ) * ALGORITHM_WEIGHTS["content_based"]

            # 3. Social graph (from followed creators)
            score += await RecommendationService._score_social(
                db, user_id, video
            ) * ALGORITHM_WEIGHTS["social"]

            # 4. Trending algorithm
            score += await RecommendationService._score_trending(
                db, video
            ) * ALGORITHM_WEIGHTS["trending"]

            if score > 0:
                rec = Recommendation(
                    user_id=user_id,
                    video_id=video.id,
                    score=score,
                    algorithm="ensemble",
                    reason="personalized",
                )
                recommendations.append(rec)

        # Sort by score and limit
        recommendations.sort(key=lambda r: r.score, reverse=True)
        recommendations = recommendations[:limit]

        # Save recommendations
        db.add_all(recommendations)
        await db.commit()

        logger.info(f"Computed {len(recommendations)} recommendations for user {user_id}")
        return recommendations

    @staticmethod
    async def _score_collaborative(
        db: AsyncSession,
        user_id: UUID,
        video: Video,
    ) -> float:
        """
        Score video using collaborative filtering (similar users)
        """
        # Find users similar to current user
        result = await db.execute(
            select(Like).where(Like.video_id == video.id)
        )
        likers = result.scalars().all()

        if not likers:
            return 0.0

        # Check if current user already engaged
        result = await db.execute(
            select(Like).where(
                and_(
                    Like.video_id == video.id,
                    Like.user_id == user_id,
                )
            )
        )
        if result.scalar():
            return 0.0  # Already liked

        # Score based on number of similar users who liked
        return min(1.0, len(likers) / 100.0)

    @staticmethod
    async def _score_content_based(
        db: AsyncSession,
        user_id: UUID,
        video: Video,
        user_prefs: Optional[UserPreference],
    ) -> float:
        """
        Score video using content-based filtering
        """
        score = 0.0

        # Check hashtag matches
        if user_prefs and user_prefs.preferred_hashtags and video.hashtags:
            video_hashtags = set(video.hashtags.split(","))
            user_hashtags = set(user_prefs.preferred_hashtags)
            matches = len(video_hashtags.intersection(user_hashtags))
            score += matches * 0.1

        # Check creator match
        if user_prefs and user_prefs.preferred_creators:
            preferred_ids = [UUID(id) for id in user_prefs.preferred_creators]
            if video.user_id in preferred_ids:
                score += 0.5

        return min(1.0, score)

    @staticmethod
    async def _score_social(
        db: AsyncSession,
        user_id: UUID,
        video: Video,
    ) -> float:
        """
        Score video based on social graph (followed creators)
        """
        # Check if user follows video creator
        result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.following_id == video.user_id,
                )
            )
        )
        if result.scalar():
            return 0.8

        return 0.0

    @staticmethod
    async def _score_trending(
        db: AsyncSession,
        video: Video,
    ) -> float:
        """
        Score video based on trending popularity
        """
        # Calculate trending score based on views and recency
        if video.published_at is None:
            return 0.0

        age_hours = (datetime.utcnow() - video.published_at).total_seconds() / 3600
        if age_hours > 168:  # Older than 1 week
            return 0.0

        # Views decay over time (more recent = higher score)
        decay_factor = 1.0 / (1.0 + log(max(1, age_hours)))
        views_score = min(1.0, video.views_count / 100000.0)

        return views_score * decay_factor

    @staticmethod
    async def get_user_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[UserPreference]:
        """Get user preferences"""
        result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar()

    @staticmethod
    async def get_or_create_user_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> UserPreference:
        """Get user preferences, creating a default row on first access"""
        prefs = await RecommendationService.get_user_preferences(db, user_id)
        if prefs:
            return prefs

        prefs = UserPreference(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        return prefs

    @staticmethod
    async def update_user_preferences(
        db: AsyncSession,
        user_id: UUID,
        update: UserPreferenceUpdate,
    ) -> UserPreference:
        """Update user preferences"""
        result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        prefs = result.scalar()

        if not prefs:
            prefs = UserPreference(user_id=user_id)
            db.add(prefs)

        # Update fields
        if update.preferred_creators is not None:
            prefs.preferred_creators = json.dumps([str(id) for id in update.preferred_creators])
        if update.preferred_hashtags is not None:
            prefs.preferred_hashtags = json.dumps(update.preferred_hashtags)
        if update.preferred_genres is not None:
            prefs.preferred_genres = json.dumps(update.preferred_genres)
        if update.preferred_languages is not None:
            prefs.preferred_languages = json.dumps(update.preferred_languages)
        if update.content_diversity_score is not None:
            prefs.content_diversity_score = update.content_diversity_score
        if update.recency_preference is not None:
            prefs.recency_preference = update.recency_preference

        prefs.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(prefs)

        logger.info(f"Updated preferences for user {user_id}")
        return prefs

    @staticmethod
    async def record_recommendation_feedback(
        db: AsyncSession,
        recommendation_id: UUID,
        user_id: UUID,
        feedback_type: str,
        rating: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> RecommendationFeedback:
        """
        Record user feedback on recommendation

        Raises:
            ValueError: If the recommendation doesn't exist - it previously
                inserted feedback unconditionally, which meant a stale or
                fabricated recommendation_id caused a raw ForeignKeyViolation
                under Postgres (silently succeeded under SQLite's lax FK
                enforcement in tests) instead of a clean 404.
        """
        recommendation = await db.get(Recommendation, recommendation_id)
        if not recommendation:
            raise ValueError("Recommendation not found")

        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            user_id=user_id,
            feedback_type=feedback_type,
            rating=rating,
            reason=reason,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        logger.info(f"Recorded feedback for recommendation {recommendation_id}: {feedback_type}")
        return feedback

    @staticmethod
    async def get_similar_videos(
        db: AsyncSession,
        video_id: UUID,
        limit: int = 10,
    ) -> List[Video]:
        """
        Get videos similar to given video (by hashtags, creator, genre)
        """
        result = await db.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar()
        if not video:
            return []

        # Find videos with similar hashtags
        video_hashtags = set(video.hashtags.split(",")) if video.hashtags else set()

        query = select(Video).where(
            and_(
                Video.id != video_id,
                Video.status == VideoStatus.PUBLISHED,
                Video.is_public == True,
            )
        ).order_by(desc(Video.views_count))

        result = await db.execute(query.limit(limit))
        similar_videos = result.scalars().all()

        # Score by hashtag similarity
        scored_videos = []
        for v in similar_videos:
            v_hashtags = set(v.hashtags.split(",")) if v.hashtags else set()
            similarity = len(video_hashtags.intersection(v_hashtags))
            scored_videos.append((v, similarity))

        scored_videos.sort(key=lambda x: x[1], reverse=True)
        return [v for v, _ in scored_videos[:limit]]

    @staticmethod
    async def get_recommendation_stats(
        db: AsyncSession,
        user_id: Optional[UUID] = None,
    ) -> dict:
        """Get recommendation system statistics"""
        query = select(Recommendation)
        if user_id:
            query = query.where(Recommendation.user_id == user_id)

        result = await db.execute(query)
        recommendations = result.scalars().all()

        # Calculate metrics
        total = len(recommendations)
        clicked = sum(1 for r in recommendations if r.clicked)
        watched = sum(1 for r in recommendations if r.watched)
        liked = sum(1 for r in recommendations if r.liked)

        return {
            "total_recommendations": total,
            "clicked": clicked,
            "click_through_rate": (clicked / total * 100) if total > 0 else 0,
            "watched": watched,
            "watch_rate": (watched / total * 100) if total > 0 else 0,
            "liked": liked,
            "like_rate": (liked / total * 100) if total > 0 else 0,
        }

    @staticmethod
    async def create_ab_test(
        db: AsyncSession,
        name: str,
        control_version: str,
        treatment_version: str,
        split_percentage: int = 50,
        description: Optional[str] = None,
    ) -> ABTest:
        """Create A/B test for recommendation algorithm"""
        test = ABTest(
            name=name,
            description=description,
            test_type="algorithm",
            control_version=control_version,
            treatment_version=treatment_version,
            split_percentage=split_percentage,
            started_at=datetime.utcnow(),
        )
        db.add(test)
        await db.commit()
        await db.refresh(test)

        logger.info(f"Created A/B test: {name}")
        return test

    @staticmethod
    async def get_active_ab_tests(
        db: AsyncSession,
    ) -> List[ABTest]:
        """Get active A/B tests"""
        result = await db.execute(
            select(ABTest).where(ABTest.is_active == True)
        )
        return result.scalars().all()

    @staticmethod
    async def assign_user_to_ab_test(
        user_id: UUID,
        test: ABTest,
    ) -> str:
        """
        Assign user to control or treatment group
        Uses consistent hashing based on user ID
        """
        # Hash user ID to consistent group assignment
        hash_value = hash(user_id) % 100
        if hash_value < test.split_percentage:
            return "treatment"
        return "control"

    @staticmethod
    async def calculate_recommendation_diversity(
        db: AsyncSession,
        recommendations: List[Recommendation],
    ) -> float:
        """
        Calculate diversity score of recommendations (0-1)
        Higher = more diverse
        """
        if not recommendations:
            return 0.0

        creators = set()
        genres = set()

        for rec in recommendations:
            # TODO: Fetch actual video data to get creator and genre
            creators.add(rec.video_id)  # Placeholder

        # Diversity = (unique_creators + unique_genres) / (2 * total_videos)
        diversity = (len(creators) + len(genres)) / (2 * len(recommendations))
        return min(1.0, diversity)

    @staticmethod
    async def batch_compute_recommendations(
        db: AsyncSession,
        user_ids: List[UUID],
        limit: int = 100,
    ) -> int:
        """
        Batch compute recommendations for multiple users
        Useful for nightly batch processing

        Returns:
            Number of users processed
        """
        count = 0
        for user_id in user_ids:
            try:
                await RecommendationService.compute_recommendations(db, user_id, limit)
                count += 1
            except Exception as e:
                logger.error(f"Error computing recommendations for user {user_id}: {e}")

        logger.info(f"Batch computed recommendations for {count}/{len(user_ids)} users")
        return count

    @staticmethod
    async def cleanup_old_recommendations(
        db: AsyncSession,
        days_old: int = 7,
    ) -> int:
        """
        Clean up old recommendation records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await db.execute(
            select(Recommendation).where(Recommendation.created_at < cutoff_date)
        )
        old_recs = result.scalars().all()

        for rec in old_recs:
            await db.delete(rec)

        await db.commit()
        logger.info(f"Cleaned up {len(old_recs)} old recommendations")
        return len(old_recs)
