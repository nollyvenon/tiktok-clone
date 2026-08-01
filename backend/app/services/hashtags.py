"""
Hashtag trending service
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import json

from app.models import HashtagTrend, HashtagAnalytics, Challenge, Video, VideoStatus

logger = logging.getLogger(__name__)


class HashtagService:
    """Service for hashtag trending and challenges"""

    @staticmethod
    async def get_trending_hashtags(
        db: AsyncSession,
        region: str = "US",
        limit: int = 20,
        category: Optional[str] = None,
    ) -> List[HashtagTrend]:
        """Get trending hashtags by region"""
        query = select(HashtagTrend).where(
            and_(
                HashtagTrend.region == region,
                HashtagTrend.rank_position.isnot(None),
            )
        )

        if category:
            query = query.where(HashtagTrend.category == category)

        query = query.order_by(HashtagTrend.rank_position).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_hashtag_analytics(
        db: AsyncSession,
        hashtag: str,
        days: int = 30,
    ) -> List[HashtagAnalytics]:
        """Get analytics for hashtag over time"""
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(HashtagAnalytics)
            .where(
                and_(
                    HashtagAnalytics.hashtag == hashtag,
                    HashtagAnalytics.date >= start_date,
                )
            )
            .order_by(desc(HashtagAnalytics.date))
        )
        return result.scalars().all()

    @staticmethod
    async def track_hashtag_usage(
        db: AsyncSession,
        hashtag: str,
        region: str,
        user_id: UUID,
    ) -> None:
        """Track hashtag usage for trend calculation"""
        # Get or create trend
        result = await db.execute(
            select(HashtagTrend).where(
                and_(
                    HashtagTrend.hashtag == hashtag,
                    HashtagTrend.region == region,
                )
            )
        )
        trend = result.scalar()

        if not trend:
            trend = HashtagTrend(
                hashtag=hashtag,
                region=region,
                usage_count=1,
                unique_creators=1,
            )
            db.add(trend)
        else:
            trend.usage_count += 1

        # Update analytics for today
        today = datetime.utcnow().date()
        result = await db.execute(
            select(HashtagAnalytics).where(
                and_(
                    HashtagAnalytics.hashtag == hashtag,
                    func.date(HashtagAnalytics.date) == today,
                )
            )
        )
        analytics = result.scalar()

        if not analytics:
            analytics = HashtagAnalytics(
                hashtag=hashtag,
                date=datetime.utcnow(),
                usage_count=1,
                unique_creators=1,
            )
            db.add(analytics)
        else:
            analytics.usage_count += 1

        await db.commit()
        logger.info(f"Tracked hashtag usage: {hashtag}")

    @staticmethod
    async def get_active_challenges(
        db: AsyncSession,
        region: str = "US",
        limit: int = 10,
    ) -> List[Challenge]:
        """Get active challenges"""
        now = datetime.utcnow()

        result = await db.execute(
            select(Challenge)
            .where(
                and_(
                    Challenge.is_active == True,
                    Challenge.start_date <= now,
                    Challenge.end_date >= now,
                )
            )
            .order_by(desc(Challenge.participation_count))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def create_challenge(
        db: AsyncSession,
        hashtag: str,
        title: str,
        description: Optional[str],
        rules: Optional[str],
        start_date: datetime,
        end_date: datetime,
        prize_pool: Optional[int] = None,
    ) -> Challenge:
        """Create a new hashtag challenge"""
        challenge = Challenge(
            hashtag=hashtag,
            title=title,
            description=description,
            rules=rules,
            start_date=start_date,
            end_date=end_date,
            prize_pool=prize_pool,
        )
        db.add(challenge)
        await db.commit()
        await db.refresh(challenge)

        logger.info(f"Challenge created: {hashtag}")
        return challenge

    @staticmethod
    async def update_challenge_stats(
        db: AsyncSession,
        challenge_id: UUID,
        video_id: UUID,
    ) -> None:
        """Update challenge participation stats"""
        result = await db.execute(
            select(Challenge).where(Challenge.id == challenge_id)
        )
        challenge = result.scalar()
        if challenge:
            challenge.participation_count += 1
            await db.commit()

    @staticmethod
    async def calculate_trend_metrics(
        db: AsyncSession,
        hashtag: str,
        region: str,
    ) -> dict:
        """Calculate popularity and velocity metrics"""
        # Get trend
        result = await db.execute(
            select(HashtagTrend).where(
                and_(
                    HashtagTrend.hashtag == hashtag,
                    HashtagTrend.region == region,
                )
            )
        )
        trend = result.scalar()

        if not trend:
            return {"popularity_score": 0, "trend_velocity": 0}

        # Get analytics from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await db.execute(
            select(HashtagAnalytics)
            .where(
                and_(
                    HashtagAnalytics.hashtag == hashtag,
                    HashtagAnalytics.date >= week_ago,
                )
            )
            .order_by(desc(HashtagAnalytics.date))
        )
        analytics = result.scalars().all()

        if len(analytics) < 2:
            return {
                "popularity_score": min(100, trend.usage_count),
                "trend_velocity": 0,
            }

        # Calculate velocity (growth rate)
        today_usage = analytics[0].usage_count
        week_ago_usage = analytics[-1].usage_count
        velocity = (
            ((today_usage - week_ago_usage) / max(1, week_ago_usage)) * 100
            if week_ago_usage > 0
            else 0
        )

        popularity = min(100, (trend.usage_count // 10))

        return {
            "popularity_score": popularity,
            "trend_velocity": velocity,
        }

    @staticmethod
    async def search_hashtags(
        db: AsyncSession,
        query: str,
        region: str = "US",
        limit: int = 20,
    ) -> List[HashtagTrend]:
        """Search hashtags by name"""
        result = await db.execute(
            select(HashtagTrend)
            .where(
                and_(
                    HashtagTrend.hashtag.ilike(f"%{query}%"),
                    HashtagTrend.region == region,
                )
            )
            .order_by(desc(HashtagTrend.usage_count))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_category_trends(
        db: AsyncSession,
        category: str,
        region: str = "US",
        limit: int = 20,
    ) -> List[HashtagTrend]:
        """Get trending hashtags by category"""
        result = await db.execute(
            select(HashtagTrend)
            .where(
                and_(
                    HashtagTrend.category == category,
                    HashtagTrend.region == region,
                )
            )
            .order_by(desc(HashtagTrend.popularity_score))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_challenge_details(
        db: AsyncSession,
        challenge_id: UUID,
    ) -> Optional[Challenge]:
        """Get challenge details"""
        result = await db.execute(
            select(Challenge).where(Challenge.id == challenge_id)
        )
        return result.scalar()

    @staticmethod
    async def get_challenge_videos(
        db: AsyncSession,
        challenge_id: UUID,
        limit: int = 30,
        offset: int = 0,
    ) -> Tuple[List[Video], int]:
        """Get videos for challenge"""
        result = await db.execute(
            select(Challenge).where(Challenge.id == challenge_id)
        )
        challenge = result.scalar()
        if not challenge:
            return [], 0

        # Get videos with challenge hashtag
        count_result = await db.execute(
            select(func.count(Video.id)).where(
                and_(
                    Video.hashtags.ilike(f"%{challenge.hashtag}%"),
                    Video.status == VideoStatus.PUBLISHED,
                )
            )
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(Video)
            .where(
                and_(
                    Video.hashtags.ilike(f"%{challenge.hashtag}%"),
                    Video.status == VideoStatus.PUBLISHED,
                )
            )
            .order_by(desc(Video.published_at))
            .offset(offset)
            .limit(limit)
        )
        videos = result.scalars().all()

        return videos, total

    @staticmethod
    async def get_hashtag_stats(
        db: AsyncSession,
        hashtag: str,
        region: str = "US",
    ) -> dict:
        """Get complete hashtag statistics"""
        result = await db.execute(
            select(HashtagTrend).where(
                and_(
                    HashtagTrend.hashtag == hashtag,
                    HashtagTrend.region == region,
                )
            )
        )
        trend = result.scalar()

        if not trend:
            return {
                "hashtag": hashtag,
                "usage_count": 0,
                "popularity_score": 0,
                "trend_velocity": 0,
            }

        metrics = await HashtagService.calculate_trend_metrics(db, hashtag, region)

        return {
            "hashtag": hashtag,
            "usage_count": trend.usage_count,
            "unique_creators": trend.unique_creators,
            "total_views": trend.total_views,
            "total_likes": trend.total_likes,
            "popularity_score": metrics["popularity_score"],
            "trend_velocity": metrics["trend_velocity"],
            "is_challenge": trend.is_challenge,
            "category": trend.category,
        }

    @staticmethod
    async def clean_old_analytics(
        db: AsyncSession,
        days_old: int = 90,
    ) -> int:
        """Clean up old analytics records"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await db.execute(
            select(HashtagAnalytics).where(HashtagAnalytics.date < cutoff_date)
        )
        old_records = result.scalars().all()

        for record in old_records:
            await db.delete(record)

        await db.commit()
        logger.info(f"Cleaned {len(old_records)} old analytics records")
        return len(old_records)
