"""
Video service for video management and recommendations
"""

from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import random

from app.models import Video, Like, Bookmark, View, User, Follow, VideoStatus
from app.schemas import VideoCreate, VideoUpdate, VideoAnalytics

logger = logging.getLogger(__name__)


class VideoService:
    """Service for video operations"""

    @staticmethod
    async def create_video(
        db: AsyncSession,
        user_id: UUID,
        video_data: VideoCreate,
    ) -> Video:
        """
        Create a new video

        Args:
            db: Database session
            user_id: Creator user ID
            video_data: Video creation data

        Returns:
            Created video object
        """
        video = Video(
            user_id=user_id,
            title=video_data.title,
            description=video_data.description,
            video_url=video_data.video_url,
            thumbnail_url=video_data.thumbnail_url,
            duration=video_data.duration,
            hashtags=video_data.hashtags,
            music_id=video_data.music_id,
            location=video_data.location,
            is_public=video_data.is_public,
            allow_comments=video_data.allow_comments,
            allow_duets=video_data.allow_duets,
            allow_stitches=video_data.allow_stitches,
            status=VideoStatus.PUBLISHED,
            published_at=datetime.utcnow(),
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)

        logger.info(f"Video created: {video.id} by user {user_id}")
        return video

    @staticmethod
    async def get_video(
        db: AsyncSession,
        video_id: UUID,
    ) -> Optional[Video]:
        """
        Get video by ID

        Args:
            db: Database session
            video_id: Video ID

        Returns:
            Video object or None
        """
        result = await db.execute(
            select(Video).where(
                and_(
                    Video.id == video_id,
                    Video.status != VideoStatus.DELETED,
                )
            )
        )
        return result.scalar()

    @staticmethod
    async def update_video(
        db: AsyncSession,
        video_id: UUID,
        user_id: UUID,
        update_data: VideoUpdate,
    ) -> Video:
        """
        Update video

        Args:
            db: Database session
            video_id: Video ID
            user_id: Current user ID (must be creator)
            update_data: Update data

        Returns:
            Updated video

        Raises:
            ValueError: If video not found or user not creator
        """
        video = await VideoService.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")

        if video.user_id != user_id:
            raise ValueError("Not authorized to update this video")

        # Update fields
        if update_data.title is not None:
            video.title = update_data.title
        if update_data.description is not None:
            video.description = update_data.description
        if update_data.thumbnail_url is not None:
            video.thumbnail_url = update_data.thumbnail_url
        if update_data.hashtags is not None:
            video.hashtags = update_data.hashtags
        if update_data.is_public is not None:
            video.is_public = update_data.is_public
        if update_data.allow_comments is not None:
            video.allow_comments = update_data.allow_comments
        if update_data.allow_duets is not None:
            video.allow_duets = update_data.allow_duets
        if update_data.allow_stitches is not None:
            video.allow_stitches = update_data.allow_stitches

        await db.commit()
        await db.refresh(video)

        logger.info(f"Video updated: {video_id}")
        return video

    @staticmethod
    async def delete_video(
        db: AsyncSession,
        video_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete video (soft delete)

        Args:
            db: Database session
            video_id: Video ID
            user_id: Current user ID (must be creator)

        Raises:
            ValueError: If video not found or user not creator
        """
        video = await VideoService.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")

        if video.user_id != user_id:
            raise ValueError("Not authorized to delete this video")

        video.status = VideoStatus.DELETED
        video.deleted_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Video deleted: {video_id}")

    @staticmethod
    async def get_feed(
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        limit: int = 10,
        offset: int = 0,
        feed_type: str = "for_you",  # "for_you" or "following"
    ) -> Tuple[List[Video], int]:
        """
        Get video feed with recommendations

        Args:
            db: Database session
            user_id: Current user ID (for personalization)
            limit: Number of videos to return
            offset: Pagination offset
            feed_type: "for_you" or "following"

        Returns:
            Tuple of (videos_list, total_count)
        """
        query = select(Video).where(
            and_(
                Video.status == VideoStatus.PUBLISHED,
                Video.is_public == True,
            )
        )

        if feed_type == "following" and user_id:
            # Get videos from users that current user follows
            follows_result = await db.execute(
                select(Follow).where(
                    and_(
                        Follow.follower_id == user_id,
                        Follow.is_active == True,
                    )
                )
            )
            following_ids = [f.following_id for f in follows_result.scalars().all()]

            if following_ids:
                query = query.where(Video.user_id.in_(following_ids))
            else:
                # No follows, return empty
                return [], 0

        # Get total count
        count_result = await db.execute(
            select(func.count(Video.id)).select_from(Video).where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                )
            )
        )
        total = count_result.scalar() or 0

        # Get paginated results (sorted by latest first, with some randomization for discovery)
        videos_result = await db.execute(
            query.order_by(desc(Video.published_at)).offset(offset).limit(limit)
        )
        videos = videos_result.scalars().all()

        return videos, total

    @staticmethod
    async def like_video(
        db: AsyncSession,
        user_id: UUID,
        video_id: UUID,
    ) -> Tuple[bool, int]:
        """
        Like or unlike a video

        Args:
            db: Database session
            user_id: User ID
            video_id: Video ID

        Returns:
            Tuple of (is_liked, likes_count)

        Raises:
            ValueError: If video not found
        """
        video = await VideoService.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")

        # Check if already liked
        existing = await db.execute(
            select(Like).where(
                and_(
                    Like.user_id == user_id,
                    Like.video_id == video_id,
                )
            )
        )
        like = existing.scalar()

        if like:
            # Unlike
            await db.delete(like)
            video.likes_count = max(0, video.likes_count - 1)
            is_liked = False
        else:
            # Like
            like = Like(user_id=user_id, video_id=video_id)
            db.add(like)
            video.likes_count += 1
            is_liked = True

        await db.commit()

        logger.info(f"Video {video_id} {'liked' if is_liked else 'unliked'} by user {user_id}")
        return is_liked, video.likes_count

    @staticmethod
    async def is_liked(
        db: AsyncSession,
        user_id: UUID,
        video_id: UUID,
    ) -> bool:
        """
        Check if user liked video

        Args:
            db: Database session
            user_id: User ID
            video_id: Video ID

        Returns:
            True if liked
        """
        result = await db.execute(
            select(Like).where(
                and_(
                    Like.user_id == user_id,
                    Like.video_id == video_id,
                )
            )
        )
        return result.scalar() is not None

    @staticmethod
    async def bookmark_video(
        db: AsyncSession,
        user_id: UUID,
        video_id: UUID,
    ) -> Tuple[bool, int]:
        """
        Bookmark or unbookmark a video

        Args:
            db: Database session
            user_id: User ID
            video_id: Video ID

        Returns:
            Tuple of (is_bookmarked, bookmarks_count)

        Raises:
            ValueError: If video not found
        """
        video = await VideoService.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")

        # Check if already bookmarked
        existing = await db.execute(
            select(Bookmark).where(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.video_id == video_id,
                )
            )
        )
        bookmark = existing.scalar()

        if bookmark:
            # Unbookmark
            await db.delete(bookmark)
            video.bookmarks_count = max(0, video.bookmarks_count - 1)
            is_bookmarked = False
        else:
            # Bookmark
            bookmark = Bookmark(user_id=user_id, video_id=video_id)
            db.add(bookmark)
            video.bookmarks_count += 1
            is_bookmarked = True

        await db.commit()

        logger.info(f"Video {video_id} {'bookmarked' if is_bookmarked else 'unbookmarked'} by user {user_id}")
        return is_bookmarked, video.bookmarks_count

    @staticmethod
    async def is_bookmarked(
        db: AsyncSession,
        user_id: UUID,
        video_id: UUID,
    ) -> bool:
        """
        Check if user bookmarked video

        Args:
            db: Database session
            user_id: User ID
            video_id: Video ID

        Returns:
            True if bookmarked
        """
        result = await db.execute(
            select(Bookmark).where(
                and_(
                    Bookmark.user_id == user_id,
                    Bookmark.video_id == video_id,
                )
            )
        )
        return result.scalar() is not None

    @staticmethod
    async def track_view(
        db: AsyncSession,
        user_id: Optional[UUID],
        video_id: UUID,
        watch_time: int = 0,
        completed: bool = False,
        device_type: Optional[str] = None,
        platform: Optional[str] = None,
        country: Optional[str] = None,
    ) -> None:
        """
        Track video view/watch

        Args:
            db: Database session
            user_id: User ID (can be None for anonymous)
            video_id: Video ID
            watch_time: Seconds watched
            completed: Whether user watched to end
            device_type: Device type
            platform: Platform (iOS, Android, Web)
            country: Country code
        """
        video = await VideoService.get_video(db, video_id)
        if not video:
            logger.warning(f"Attempted view tracking for non-existent video: {video_id}")
            return

        # Create view record
        view = View(
            user_id=user_id or UUID(int=0),  # Use null UUID for anonymous
            video_id=video_id,
            watch_time=watch_time,
            completed=completed,
            device_type=device_type,
            platform=platform,
            country=country,
        )
        db.add(view)

        # Update video analytics
        video.views_count += 1
        if completed:
            video.completion_rate = int(
                (video.completion_rate * (video.views_count - 1) + 100) / video.views_count
            )
        if watch_time > 0:
            video.average_watch_time = int(
                (video.average_watch_time * (video.views_count - 1) + watch_time) / video.views_count
            )

        await db.commit()

        logger.info(f"View tracked for video {video_id}: watch_time={watch_time}s, completed={completed}")

    @staticmethod
    async def get_video_analytics(
        db: AsyncSession,
        video_id: UUID,
        user_id: UUID,
    ) -> VideoAnalytics:
        """
        Get video analytics (owner only)

        Args:
            db: Database session
            video_id: Video ID
            user_id: Current user ID (must be creator)

        Returns:
            Video analytics

        Raises:
            ValueError: If video not found or user not creator
        """
        video = await VideoService.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")

        if video.user_id != user_id:
            raise ValueError("Not authorized to view analytics")

        # Calculate engagement rate
        total_interactions = video.likes_count + video.comments_count + video.bookmarks_count
        engagement_rate = (
            (total_interactions / video.views_count * 100)
            if video.views_count > 0
            else 0
        )

        return VideoAnalytics(
            video_id=video_id,
            views=video.views_count,
            likes=video.likes_count,
            comments=video.comments_count,
            shares=video.shares_count,
            bookmarks=video.bookmarks_count,
            completion_rate=video.completion_rate,
            average_watch_time=video.average_watch_time,
            engagement_rate=round(engagement_rate, 2),
        )

    @staticmethod
    async def get_user_videos(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Video], int]:
        """
        Get videos by a specific user

        Args:
            db: Database session
            user_id: User ID
            limit: Number of results
            offset: Pagination offset

        Returns:
            Tuple of (videos_list, total_count)
        """
        # Get total count
        count_result = await db.execute(
            select(func.count(Video.id)).select_from(Video).where(
                and_(
                    Video.user_id == user_id,
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                )
            )
        )
        total = count_result.scalar() or 0

        # Get paginated results
        result = await db.execute(
            select(Video)
            .where(
                and_(
                    Video.user_id == user_id,
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                )
            )
            .order_by(desc(Video.published_at))
            .offset(offset)
            .limit(limit)
        )
        videos = result.scalars().all()

        return videos, total

    @staticmethod
    async def search_videos(
        db: AsyncSession,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Video], int]:
        """
        Search videos by title, description, hashtags

        Args:
            db: Database session
            query: Search query
            limit: Number of results
            offset: Pagination offset

        Returns:
            Tuple of (videos_list, total_count)
        """
        search_pattern = f"%{query.lower()}%"

        # Get total count
        count_result = await db.execute(
            select(func.count(Video.id)).select_from(Video).where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                    (
                        Video.title.ilike(search_pattern) |
                        Video.description.ilike(search_pattern) |
                        Video.hashtags.ilike(search_pattern)
                    ),
                )
            )
        )
        total = count_result.scalar() or 0

        # Get paginated results
        result = await db.execute(
            select(Video)
            .where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                    (
                        Video.title.ilike(search_pattern) |
                        Video.description.ilike(search_pattern) |
                        Video.hashtags.ilike(search_pattern)
                    ),
                )
            )
            .order_by(desc(Video.published_at))
            .offset(offset)
            .limit(limit)
        )
        videos = result.scalars().all()

        return videos, total

    @staticmethod
    async def get_trending_videos(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        timeframe_hours: int = 24,
    ) -> Tuple[List[Video], int]:
        """
        Get trending videos based on engagement

        Args:
            db: Database session
            limit: Number of results
            offset: Pagination offset
            timeframe_hours: Time period to consider

        Returns:
            Tuple of (videos_list, total_count)
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=timeframe_hours)

        # Get total count
        count_result = await db.execute(
            select(func.count(Video.id)).select_from(Video).where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                    Video.published_at >= cutoff_time,
                )
            )
        )
        total = count_result.scalar() or 0

        # Get paginated results (sorted by engagement)
        result = await db.execute(
            select(Video)
            .where(
                and_(
                    Video.status == VideoStatus.PUBLISHED,
                    Video.is_public == True,
                    Video.published_at >= cutoff_time,
                )
            )
            .order_by(
                desc(Video.likes_count + Video.comments_count + Video.bookmarks_count)
            )
            .offset(offset)
            .limit(limit)
        )
        videos = result.scalars().all()

        return videos, total
