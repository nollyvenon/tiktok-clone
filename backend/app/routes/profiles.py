"""
Profile API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from uuid import UUID

from app.database import get_db
from app.schemas import (
    UserFullProfile, UserProfileUpdate, ProfileResponse, ProfileStatistics,
    FollowResponse, FollowersResponse, FollowingResponse, BlockResponse,
    BlockedUsersResponse, UserPublicProfile, ErrorResponse
)
from app.services.profiles import ProfileService
from app.routes.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["Profiles"])


# ============================================================================
# Public Profile Endpoints
# ============================================================================

@router.get(
    "/{user_id}",
    response_model=ProfileResponse,
    responses={
        200: {"description": "User profile retrieved"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_user_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(lambda auth=Header(None), db=Depends(get_db): get_current_user(auth, db) if auth else None),
):
    """
    Get user profile by ID

    **Parameters:**
    - user_id: User UUID

    **Returns:** User profile with statistics and verification
    """
    try:
        user = await ProfileService.get_user_profile(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Get statistics
        stats = await ProfileService.get_profile_statistics(db, user_id)

        # Get verification
        verification = await ProfileService.get_verification(db, user_id)

        # Get badges
        badges = await ProfileService.get_user_badges(db, user_id)

        # Check if current user is following
        is_following = False
        is_blocked = False
        if current_user:
            is_following = await ProfileService.is_following(db, current_user.id, user_id)
            is_blocked = await ProfileService.is_blocked(db, user_id, current_user.id)

        return ProfileResponse(
            user=UserFullProfile.from_orm(user),
            statistics=stats,
            verification=verification,
            badges=badges,
            is_following=is_following,
            is_blocked=is_blocked,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )


@router.get(
    "/username/{username}",
    response_model=ProfileResponse,
    responses={
        200: {"description": "User profile retrieved"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_user_profile_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(lambda auth=Header(None), db=Depends(get_db): get_current_user(auth, db) if auth else None),
):
    """
    Get user profile by username

    **Parameters:**
    - username: Username

    **Returns:** User profile with statistics and verification
    """
    try:
        user = await ProfileService.get_user_by_username(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Get statistics
        stats = await ProfileService.get_profile_statistics(db, user.id)

        # Get verification
        verification = await ProfileService.get_verification(db, user.id)

        # Get badges
        badges = await ProfileService.get_user_badges(db, user.id)

        # Check if current user is following
        is_following = False
        is_blocked = False
        if current_user:
            is_following = await ProfileService.is_following(db, current_user.id, user.id)
            is_blocked = await ProfileService.is_blocked(db, user.id, current_user.id)

        return ProfileResponse(
            user=UserFullProfile.from_orm(user),
            statistics=stats,
            verification=verification,
            badges=badges,
            is_following=is_following,
            is_blocked=is_blocked,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile by username error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )


# ============================================================================
# Protected Profile Endpoints
# ============================================================================

@router.put(
    "/me",
    response_model=UserFullProfile,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Profile updated"},
        400: {"model": ErrorResponse, "description": "Invalid data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def update_profile(
    request: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile

    **Authorization:** Requires valid access token

    **Request body:**
    - first_name: First name (optional)
    - last_name: Last name (optional)
    - bio: User bio (max 150 characters)
    - avatar_url: Avatar image URL
    - cover_url: Cover image URL
    - website: Personal website URL
    """
    try:
        updated_user = await ProfileService.update_profile(db, current_user.id, request)
        return UserFullProfile.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


# ============================================================================
# Follow Endpoints
# ============================================================================

@router.post(
    "/{user_id}/follow",
    response_model=FollowResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Follow status changed"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def follow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Follow or unfollow a user

    **Authorization:** Requires valid access token

    **Parameters:**
    - user_id: User to follow UUID

    **Returns:** Follow status and follower count
    """
    try:
        is_following, follower_count = await ProfileService.follow_user(
            db, current_user.id, user_id
        )
        return FollowResponse(
            is_following=is_following,
            followers_count=follower_count,
            following_count=0,  # Will be populated by frontend
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Follow user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to follow user",
        )


@router.get(
    "/{user_id}/followers",
    response_model=FollowersResponse,
    responses={
        200: {"description": "Followers list"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_followers(
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    Get user followers list

    **Parameters:**
    - user_id: User UUID
    - limit: Number of results (default 20)
    - offset: Pagination offset (default 0)

    **Returns:** List of followers with total count
    """
    try:
        followers, total = await ProfileService.get_followers(
            db, user_id, limit=limit, offset=offset
        )
        return FollowersResponse(
            users=[UserPublicProfile.from_orm(u) for u in followers],
            total=total,
        )
    except Exception as e:
        logger.error(f"Get followers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve followers",
        )


@router.get(
    "/{user_id}/following",
    response_model=FollowingResponse,
    responses={
        200: {"description": "Following list"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_following(
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    Get users that user is following

    **Parameters:**
    - user_id: User UUID
    - limit: Number of results (default 20)
    - offset: Pagination offset (default 0)

    **Returns:** List of following with total count
    """
    try:
        following, total = await ProfileService.get_following(
            db, user_id, limit=limit, offset=offset
        )
        return FollowingResponse(
            users=[UserPublicProfile.from_orm(u) for u in following],
            total=total,
        )
    except Exception as e:
        logger.error(f"Get following error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve following",
        )


# ============================================================================
# Block Endpoints
# ============================================================================

@router.post(
    "/{user_id}/block",
    response_model=BlockResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Block status changed"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def block_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Block or unblock a user

    **Authorization:** Requires valid access token

    **Parameters:**
    - user_id: User to block UUID

    **Returns:** Block status
    """
    try:
        is_blocked = await ProfileService.block_user(db, current_user.id, user_id)
        return BlockResponse(
            is_blocked=is_blocked,
            message="User blocked" if is_blocked else "User unblocked",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Block user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block user",
        )


@router.get(
    "/me/blocked",
    response_model=BlockedUsersResponse,
    responses={
        200: {"description": "Blocked users list"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_blocked_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of blocked users

    **Authorization:** Requires valid access token

    **Returns:** List of blocked users
    """
    try:
        from app.models import Block
        result = await db.execute(
            select(Block).where(Block.blocker_id == current_user.id)
        )
        blocks = result.scalars().all()

        blocked_ids = [b.blocked_id for b in blocks]
        if not blocked_ids:
            return BlockedUsersResponse(users=[], total=0)

        users_result = await db.execute(
            select(User).where(User.id.in_(blocked_ids))
        )
        users = users_result.scalars().all()

        return BlockedUsersResponse(
            users=[UserPublicProfile.from_orm(u) for u in users],
            total=len(users),
        )
    except Exception as e:
        logger.error(f"Get blocked users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blocked users",
        )


# Helper for get_blocked_users
from sqlalchemy import select
