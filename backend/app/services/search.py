"""
Search and discovery service for videos, creators, hashtags
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.models import Video, User, VideoStatus

logger = logging.getLogger(__name__)

# Search results per page
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class SearchService:
    """Service for searching videos, creators, and hashtags"""

    @staticmethod
    async def search_videos(
        db: AsyncSession,
        query: str,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
        sort_by: str = "relevance",  # relevance, recent, popular
    ) -> Tuple[List[Video], int]:
        """
        Search videos by title, description, hashtags

        Args:
            db: Database session
            query: Search query
            limit: Results per page
            offset: Pagination offset
            duration_min: Minimum duration in seconds
            duration_max: Maximum duration in seconds
            sort_by: Sorting method

        Returns:
            List of videos and total count
        """
        limit = min(limit, MAX_LIMIT)

        # Build search query
        search_filter = and_(
            Video.status == VideoStatus.PUBLISHED,
            Video.is_public == True,
            or_(
                Video.title.ilike(f"%{query}%"),
                Video.description.ilike(f"%{query}%"),
                Video.hashtags.ilike(f"%{query}%"),
            ),
        )

        # Add duration filters if provided
        if duration_min is not None:
            search_filter = and_(search_filter, Video.duration >= duration_min * 1000)
        if duration_max is not None:
            search_filter = and_(search_filter, Video.duration <= duration_max * 1000)

        # Build base query
        base_query = select(Video).where(search_filter)

        # Apply sorting
        if sort_by == "recent":
            base_query = base_query.order_by(desc(Video.published_at))
        elif sort_by == "popular":
            base_query = base_query.order_by(desc(Video.views_count))
        else:  # relevance (default)
            base_query = base_query.order_by(desc(Video.likes_count))

        # Get total count
        count_result = await db.execute(
            select(func.count(Video.id)).where(search_filter)
        )
        total_count = count_result.scalar() or 0

        # Get paginated results
        query_result = await db.execute(
            base_query.offset(offset).limit(limit)
        )
        videos = query_result.scalars().all()

        logger.info(f"Video search: '{query}' returned {len(videos)} results")
        return videos, total_count

    @staticmethod
    async def search_creators(
        db: AsyncSession,
        query: str,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> Tuple[List[User], int]:
        """Search creators by username, display name"""
        limit = min(limit, MAX_LIMIT)

        search_filter = and_(
            User.is_active == True,
            or_(
                User.username.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
            ),
        )

        # Get total count
        count_result = await db.execute(
            select(func.count(User.id)).where(search_filter)
        )
        total_count = count_result.scalar() or 0

        # Get paginated results (prioritize verified creators)
        query_result = await db.execute(
            select(User)
            .where(search_filter)
            .order_by(User.is_verified.desc())
            .offset(offset)
            .limit(limit)
        )
        users = query_result.scalars().all()

        logger.info(f"Creator search: '{query}' returned {len(users)} results")
        return users, total_count

    @staticmethod
    async def search_hashtags(
        db: AsyncSession,
        query: str,
        limit: int = 20,
    ) -> List[dict]:
        """
        Search hashtags by name with usage count

        Args:
            db: Database session
            query: Hashtag query
            limit: Number of suggestions

        Returns:
            List of hashtags with usage counts
        """
        # Extract hashtags from videos containing query
        result = await db.execute(
            select(Video.hashtags)
            .where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                    Video.hashtags.ilike(f"%{query}%"),
                )
            )
            .limit(100)
        )

        hashtag_rows = result.scalars().all()
        hashtag_counts = {}

        for row in hashtag_rows:
            if row:
                tags = [tag.strip() for tag in row.split(",")]
                for tag in tags:
                    if query.lower() in tag.lower():
                        hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1

        # Sort by count and return top matches
        sorted_tags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"tag": tag, "count": count}
            for tag, count in sorted_tags[:limit]
        ]

    @staticmethod
    async def get_search_suggestions(
        db: AsyncSession,
        query: str,
        limit: int = 10,
    ) -> dict:
        """
        Get search suggestions (creators, hashtags, videos)
        """
        creators, _ = await SearchService.search_creators(db, query, limit=5)
        hashtags = await SearchService.search_hashtags(db, query, limit=5)

        return {
            "creators": [
                {
                    "id": str(c.id),
                    "username": c.username,
                    "avatar_url": c.avatar_url,
                    "is_verified": c.is_verified,
                }
                for c in creators
            ],
            "hashtags": hashtags,
        }

    @staticmethod
    async def get_popular_searches(
        db: AsyncSession,
        region: str = "US",
        limit: int = 20,
    ) -> List[str]:
        """Get trending/popular searches in region"""
        # TODO: Implement with search analytics table
        # For now, return empty list
        return []

    @staticmethod
    async def record_search(
        db: AsyncSession,
        user_id: UUID,
        query: str,
        result_count: int,
    ) -> None:
        """Record search for analytics"""
        # TODO: Implement with search_analytics table
        logger.info(f"Search recorded: user={user_id}, query='{query}', results={result_count}")

    @staticmethod
    async def get_discover_by_category(
        db: AsyncSession,
        category: str,
        limit: int = 30,
    ) -> List[Video]:
        """
        Get videos by category/genre

        Categories: music, dance, comedy, cooking, fitness, education, etc.
        """
        # Search for videos with hashtags matching category
        result = await db.execute(
            select(Video)
            .where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                    Video.hashtags.ilike(f"%{category}%"),
                )
            )
            .order_by(desc(Video.published_at))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_trending_searches(
        db: AsyncSession,
        days: int = 7,
        limit: int = 20,
    ) -> List[dict]:
        """Get trending searches from past N days"""
        # TODO: Implement with search_analytics table
        return []

    @staticmethod
    async def search_advanced(
        db: AsyncSession,
        query: Optional[str] = None,
        creator_id: Optional[UUID] = None,
        hashtags: Optional[List[str]] = None,
        min_views: Optional[int] = None,
        max_duration: Optional[int] = None,
        after_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
        sort_by: str = "relevance",
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> Tuple[List[Video], int]:
        """
        Advanced search with multiple filters

        Args:
            query: Text search query
            creator_id: Filter by creator
            hashtags: Filter by hashtags
            min_views: Minimum view count
            max_duration: Maximum video duration
            after_date: Videos after date
            before_date: Videos before date
            sort_by: Sorting method
            limit: Results per page
            offset: Pagination offset

        Returns:
            List of videos and total count
        """
        limit = min(limit, MAX_LIMIT)
        filters = [
            Video.status == VideoStatus.PUBLISHED,
            Video.is_public == True,
        ]

        # Text search
        if query:
            filters.append(
                or_(
                    Video.title.ilike(f"%{query}%"),
                    Video.description.ilike(f"%{query}%"),
                    Video.hashtags.ilike(f"%{query}%"),
                )
            )

        # Creator filter
        if creator_id:
            filters.append(Video.user_id == creator_id)

        # Hashtag filters
        if hashtags:
            hashtag_condition = None
            for tag in hashtags:
                if hashtag_condition is None:
                    hashtag_condition = Video.hashtags.ilike(f"%{tag}%")
                else:
                    hashtag_condition = or_(hashtag_condition, Video.hashtags.ilike(f"%{tag}%"))
            if hashtag_condition is not None:
                filters.append(hashtag_condition)

        # View filter
        if min_views is not None:
            filters.append(Video.views_count >= min_views)

        # Duration filter
        if max_duration is not None:
            filters.append(Video.duration <= max_duration * 1000)

        # Date filters
        if after_date:
            filters.append(Video.published_at >= after_date)
        if before_date:
            filters.append(Video.published_at <= before_date)

        # Build query
        search_query = select(Video).where(and_(*filters))

        # Apply sorting
        if sort_by == "recent":
            search_query = search_query.order_by(desc(Video.published_at))
        elif sort_by == "popular":
            search_query = search_query.order_by(desc(Video.views_count))
        else:  # relevance
            search_query = search_query.order_by(desc(Video.likes_count))

        # Get count
        count_result = await db.execute(
            select(func.count(Video.id)).where(and_(*filters))
        )
        total_count = count_result.scalar() or 0

        # Get results
        result = await db.execute(search_query.offset(offset).limit(limit))
        videos = result.scalars().all()

        logger.info(f"Advanced search returned {len(videos)} results")
        return videos, total_count
