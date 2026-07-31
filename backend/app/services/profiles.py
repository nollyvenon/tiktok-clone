"""
Profile service for user profile management
"""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.models import User, Follow, Block, Verification, Badge
from app.schemas import UserProfileUpdate, ProfileStatistics

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for profile operations"""

    @staticmethod
    async def get_user_profile(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """
        Get user profile by ID

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await db.execute(
            select(User).where(
                and_(
                    User.id == user_id,
                    User.deleted_at == None,
                )
            )
        )
        return result.scalar()

    @staticmethod
    async def get_user_by_username(
        db: AsyncSession,
        username: str,
    ) -> Optional[User]:
        """
        Get user profile by username

        Args:
            db: Database session
            username: Username

        Returns:
            User object or None if not found
        """
        result = await db.execute(
            select(User).where(
                and_(
                    User.username == username,
                    User.deleted_at == None,
                )
            )
        )
        return result.scalar()

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: UUID,
        update_data: UserProfileUpdate,
    ) -> User:
        """
        Update user profile

        Args:
            db: Database session
            user_id: User ID
            update_data: Profile update data

        Returns:
            Updated user

        Raises:
            ValueError: If user not found
        """
        user = await ProfileService.get_user_profile(db, user_id)
        if not user:
            raise ValueError("User not found")

        # Update fields
        if update_data.first_name is not None:
            user.first_name = update_data.first_name
        if update_data.last_name is not None:
            user.last_name = update_data.last_name
        if update_data.bio is not None:
            user.bio = update_data.bio
        if update_data.avatar_url is not None:
            user.avatar_url = update_data.avatar_url
        if update_data.cover_url is not None:
            user.cover_url = update_data.cover_url
        if update_data.website is not None:
            user.website = update_data.website

        await db.commit()
        await db.refresh(user)

        logger.info(f"Profile updated for user: {user_id}")
        return user

    @staticmethod
    async def follow_user(
        db: AsyncSession,
        follower_id: UUID,
        following_id: UUID,
    ) -> Tuple[bool, int]:
        """
        Follow a user

        Args:
            db: Database session
            follower_id: Follower user ID
            following_id: User to follow ID

        Returns:
            Tuple of (is_following, follower_count)

        Raises:
            ValueError: If users don't exist or self-follow attempt
        """
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")

        # Check users exist
        follower = await ProfileService.get_user_profile(db, follower_id)
        following = await ProfileService.get_user_profile(db, following_id)

        if not follower or not following:
            raise ValueError("User not found")

        # Check if already following
        existing = await db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
        )
        follow = existing.scalar()

        if follow:
            # Already following - unfollow
            follow.is_active = False
            await db.commit()
            is_following = False
        else:
            # Create follow relationship
            follow = Follow(
                follower_id=follower_id,
                following_id=following_id,
                is_active=True,
            )
            db.add(follow)
            await db.commit()
            is_following = True

        # Get follower count
        follower_count_result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.following_id == following_id,
                    Follow.is_active == True,
                )
            )
        )
        follower_count = len(follower_count_result.scalars().all())

        logger.info(f"User {follower_id} {'followed' if is_following else 'unfollowed'} {following_id}")
        return is_following, follower_count

    @staticmethod
    async def get_followers(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[list[User], int]:
        """
        Get user followers

        Args:
            db: Database session
            user_id: User ID
            limit: Number of results
            offset: Offset for pagination

        Returns:
            Tuple of (followers_list, total_count)
        """
        # Get total count
        count_result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.following_id == user_id,
                    Follow.is_active == True,
                )
            )
        )
        total = len(count_result.scalars().all())

        # Get paginated results
        result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.following_id == user_id,
                    Follow.is_active == True,
                )
            ).order_by(desc(Follow.created_at)).offset(offset).limit(limit)
        )
        follows = result.scalars().all()

        # Get users
        follower_ids = [f.follower_id for f in follows]
        users_result = await db.execute(
            select(User).where(User.id.in_(follower_ids))
        )
        users = users_result.scalars().all()

        return users, total

    @staticmethod
    async def get_following(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[list[User], int]:
        """
        Get users that user is following

        Args:
            db: Database session
            user_id: User ID
            limit: Number of results
            offset: Offset for pagination

        Returns:
            Tuple of (following_list, total_count)
        """
        # Get total count
        count_result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.is_active == True,
                )
            )
        )
        total = len(count_result.scalars().all())

        # Get paginated results
        result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.is_active == True,
                )
            ).order_by(desc(Follow.created_at)).offset(offset).limit(limit)
        )
        follows = result.scalars().all()

        # Get users
        following_ids = [f.following_id for f in follows]
        users_result = await db.execute(
            select(User).where(User.id.in_(following_ids))
        )
        users = users_result.scalars().all()

        return users, total

    @staticmethod
    async def is_following(
        db: AsyncSession,
        follower_id: UUID,
        following_id: UUID,
    ) -> bool:
        """
        Check if user is following another user

        Args:
            db: Database session
            follower_id: Follower user ID
            following_id: Following user ID

        Returns:
            True if following
        """
        result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                    Follow.is_active == True,
                )
            )
        )
        return result.scalar() is not None

    @staticmethod
    async def block_user(
        db: AsyncSession,
        blocker_id: UUID,
        blocked_id: UUID,
    ) -> bool:
        """
        Block or unblock a user

        Args:
            db: Database session
            blocker_id: User doing the blocking
            blocked_id: User to block

        Returns:
            True if blocked, False if unblocked
        """
        if blocker_id == blocked_id:
            raise ValueError("Cannot block yourself")

        # Check if already blocked
        existing = await db.execute(
            select(Block).where(
                and_(
                    Block.blocker_id == blocker_id,
                    Block.blocked_id == blocked_id,
                )
            )
        )
        block = existing.scalar()

        if block:
            # Unblock
            await db.delete(block)
            await db.commit()
            return False
        else:
            # Block
            block = Block(
                blocker_id=blocker_id,
                blocked_id=blocked_id,
            )
            db.add(block)
            # Unfollow automatically
            follow_result = await db.execute(
                select(Follow).where(
                    and_(
                        Follow.follower_id == blocker_id,
                        Follow.following_id == blocked_id,
                    )
                )
            )
            follow = follow_result.scalar()
            if follow:
                await db.delete(follow)

            await db.commit()
            return True

    @staticmethod
    async def is_blocked(
        db: AsyncSession,
        blocker_id: UUID,
        blocked_id: UUID,
    ) -> bool:
        """
        Check if user is blocked

        Args:
            db: Database session
            blocker_id: User doing the blocking
            blocked_id: User to check

        Returns:
            True if blocked
        """
        result = await db.execute(
            select(Block).where(
                and_(
                    Block.blocker_id == blocker_id,
                    Block.blocked_id == blocked_id,
                )
            )
        )
        return result.scalar() is not None

    @staticmethod
    async def get_profile_statistics(
        db: AsyncSession,
        user_id: UUID,
    ) -> ProfileStatistics:
        """
        Get profile statistics

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Profile statistics object
        """
        # Count followers
        followers_result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.following_id == user_id,
                    Follow.is_active == True,
                )
            )
        )
        followers_count = len(followers_result.scalars().all())

        # Count following
        following_result = await db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.is_active == True,
                )
            )
        )
        following_count = len(following_result.scalars().all())

        # Placeholder for video counts (Module 3 will implement)
        videos_count = 0
        likes_count = 0
        total_views = 0

        return ProfileStatistics(
            followers_count=followers_count,
            following_count=following_count,
            videos_count=videos_count,
            likes_count=likes_count,
            total_views=total_views,
        )

    @staticmethod
    async def verify_user(
        db: AsyncSession,
        user_id: UUID,
        admin_id: UUID,
        verification_type: str = "influencer",
    ) -> None:
        """
        Verify a user (admin only)

        Args:
            db: Database session
            user_id: User to verify
            admin_id: Admin user ID
            verification_type: Type of verification

        Raises:
            ValueError: If user not found
        """
        user = await ProfileService.get_user_profile(db, user_id)
        if not user:
            raise ValueError("User not found")

        # Check or create verification
        result = await db.execute(
            select(Verification).where(Verification.user_id == user_id)
        )
        verification = result.scalar()

        if verification:
            verification.is_verified = True
            verification.verification_type = verification_type
            verification.verified_by = admin_id
            verification.verified_at = datetime.utcnow()
        else:
            verification = Verification(
                user_id=user_id,
                is_verified=True,
                verification_type=verification_type,
                verified_by=admin_id,
                verified_at=datetime.utcnow(),
            )
            db.add(verification)

        await db.commit()
        logger.info(f"User {user_id} verified as {verification_type}")

    @staticmethod
    async def get_verification(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[Verification]:
        """
        Get user verification status

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Verification object or None
        """
        result = await db.execute(
            select(Verification).where(Verification.user_id == user_id)
        )
        return result.scalar()

    @staticmethod
    async def add_badge(
        db: AsyncSession,
        user_id: UUID,
        badge_type: str,
        badge_name: str,
        badge_icon_url: Optional[str] = None,
    ) -> Badge:
        """
        Add badge to user

        Args:
            db: Database session
            user_id: User ID
            badge_type: Type of badge
            badge_name: Badge display name
            badge_icon_url: URL to badge icon

        Returns:
            Created badge
        """
        badge = Badge(
            user_id=user_id,
            badge_type=badge_type,
            badge_name=badge_name,
            badge_icon_url=badge_icon_url,
        )
        db.add(badge)
        await db.commit()
        await db.refresh(badge)

        logger.info(f"Badge {badge_type} added to user {user_id}")
        return badge

    @staticmethod
    async def get_user_badges(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Badge]:
        """
        Get user badges

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of badges
        """
        result = await db.execute(
            select(Badge).where(Badge.user_id == user_id).order_by(desc(Badge.created_at))
        )
        return result.scalars().all()
