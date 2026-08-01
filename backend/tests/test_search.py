"""
Tests for search and discovery (Module 8)
"""

import pytest
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Video, User, VideoStatus
from app.services.search import SearchService


@pytest.mark.asyncio
async def test_search_videos_by_title(test_db: AsyncSession):
    """Test searching videos by title"""
    # Create test user
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    # Create test videos
    video1 = Video(
        user_id=user.id,
        title="Learn to Dance Tutorial",
        description="Complete dance tutorial",
        video_url="https://s3.example.com/video1.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    video2 = Video(
        user_id=user.id,
        title="Cooking Recipe Video",
        description="Easy pasta recipe",
        video_url="https://s3.example.com/video2.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video1)
    test_db.add(video2)
    await test_db.commit()

    # Search for "dance"
    results, total = await SearchService.search_videos(test_db, "dance", limit=10)
    assert len(results) >= 1
    assert total >= 1


@pytest.mark.asyncio
async def test_search_videos_by_description(test_db: AsyncSession):
    """Test searching videos by description"""
    user = User(
        email="test2@example.com",
        username="testuser2",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="My Video",
        description="This is about fitness and exercise",
        video_url="https://s3.example.com/video.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    results, total = await SearchService.search_videos(test_db, "fitness")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_videos_by_hashtags(test_db: AsyncSession):
    """Test searching videos by hashtags"""
    user = User(
        email="test3@example.com",
        username="testuser3",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="Dance Video",
        description="Fun dance",
        hashtags="#dance, #trending, #music",
        video_url="https://s3.example.com/video.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    results, total = await SearchService.search_videos(test_db, "#dance")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_creators(test_db: AsyncSession):
    """Test searching for creators"""
    creator1 = User(
        email="creator1@example.com",
        username="dancecreator",
        password_hash="hashed",
        first_name="Dance",
        last_name="Master",
        is_active=True,
    )
    creator2 = User(
        email="creator2@example.com",
        username="musicproducer",
        password_hash="hashed",
        first_name="Music",
        last_name="Maker",
        is_active=True,
    )
    test_db.add(creator1)
    test_db.add(creator2)
    await test_db.commit()

    # Search by username
    results, total = await SearchService.search_creators(test_db, "dance")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_creators_by_name(test_db: AsyncSession):
    """Test searching creators by first/last name"""
    creator = User(
        email="john@example.com",
        username="johnsmith123",
        password_hash="hashed",
        first_name="John",
        last_name="Smith",
        is_active=True,
    )
    test_db.add(creator)
    await test_db.commit()

    results, total = await SearchService.search_creators(test_db, "john")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_hashtags(test_db: AsyncSession):
    """Test searching hashtags from videos"""
    user = User(
        email="test4@example.com",
        username="testuser4",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    # Create videos with hashtags
    for i in range(3):
        video = Video(
            user_id=user.id,
            title=f"Video {i}",
            hashtags="#trending, #dance, #music",
            video_url=f"https://s3.example.com/video{i}.mp4",
            status=VideoStatus.PUBLISHED,
            is_public=True,
        )
        test_db.add(video)
    await test_db.commit()

    hashtags = await SearchService.search_hashtags(test_db, "#dance")
    assert isinstance(hashtags, list)


@pytest.mark.asyncio
async def test_search_with_duration_filter(test_db: AsyncSession):
    """Test searching videos with duration filters"""
    user = User(
        email="test5@example.com",
        username="testuser5",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video1 = Video(
        user_id=user.id,
        title="Short Video",
        duration=15,
        video_url="https://s3.example.com/short.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    video2 = Video(
        user_id=user.id,
        title="Long Video",
        duration=60,
        video_url="https://s3.example.com/long.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video1)
    test_db.add(video2)
    await test_db.commit()

    # Search for short videos (max 30 seconds)
    results, total = await SearchService.search_videos(
        test_db, "video", duration_max=30
    )
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_sorting_by_recent(test_db: AsyncSession):
    """Test search results sorting by recent"""
    user = User(
        email="test6@example.com",
        username="testuser6",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video1 = Video(
        user_id=user.id,
        title="Old Video",
        video_url="https://s3.example.com/old.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video1)
    await test_db.commit()

    results, total = await SearchService.search_videos(
        test_db, "video", sort_by="recent"
    )
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_sorting_by_popular(test_db: AsyncSession):
    """Test search results sorting by popularity"""
    user = User(
        email="test7@example.com",
        username="testuser7",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="Popular Video",
        video_url="https://s3.example.com/popular.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
        views_count=10000,
    )
    test_db.add(video)
    await test_db.commit()

    results, total = await SearchService.search_videos(
        test_db, "video", sort_by="popular"
    )
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_get_search_suggestions(test_db: AsyncSession):
    """Test getting search suggestions"""
    creator = User(
        email="suggest@example.com",
        username="dance_creator",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(creator)
    await test_db.commit()

    suggestions = await SearchService.get_search_suggestions(test_db, "dance")
    assert "creators" in suggestions
    assert "hashtags" in suggestions


@pytest.mark.asyncio
async def test_discover_by_category(test_db: AsyncSession):
    """Test discovering videos by category"""
    user = User(
        email="test8@example.com",
        username="testuser8",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="Dance Moves",
        hashtags="#dance, #entertainment",
        video_url="https://s3.example.com/dance.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    videos = await SearchService.get_discover_by_category(test_db, "dance")
    assert isinstance(videos, list)


@pytest.mark.asyncio
async def test_advanced_search_with_creator_filter(test_db: AsyncSession):
    """Test advanced search with creator filter"""
    user = User(
        email="test9@example.com",
        username="testuser9",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="Test Video",
        video_url="https://s3.example.com/test.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    videos, total = await SearchService.search_advanced(
        test_db, creator_id=user.id
    )
    assert len(videos) >= 1


@pytest.mark.asyncio
async def test_advanced_search_with_hashtag_filter(test_db: AsyncSession):
    """Test advanced search with hashtag filtering"""
    user = User(
        email="test10@example.com",
        username="testuser10",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    video = Video(
        user_id=user.id,
        title="Music Video",
        hashtags="#music, #trending",
        video_url="https://s3.example.com/music.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=True,
    )
    test_db.add(video)
    await test_db.commit()

    videos, total = await SearchService.search_advanced(
        test_db, hashtags=["music"]
    )
    assert len(videos) >= 1


@pytest.mark.asyncio
async def test_search_excludes_private_videos(test_db: AsyncSession):
    """Test that search excludes private videos"""
    user = User(
        email="test11@example.com",
        username="testuser11",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    private_video = Video(
        user_id=user.id,
        title="Private Dance Video",
        video_url="https://s3.example.com/private.mp4",
        status=VideoStatus.PUBLISHED,
        is_public=False,
    )
    test_db.add(private_video)
    await test_db.commit()

    results, total = await SearchService.search_videos(test_db, "dance")
    # Private videos should not appear
    assert all(v.is_public for v in results)


@pytest.mark.asyncio
async def test_search_excludes_drafts(test_db: AsyncSession):
    """Test that search excludes draft videos"""
    user = User(
        email="test12@example.com",
        username="testuser12",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    draft_video = Video(
        user_id=user.id,
        title="Draft Dance Video",
        video_url="https://s3.example.com/draft.mp4",
        status=VideoStatus.DRAFT,
        is_public=True,
    )
    test_db.add(draft_video)
    await test_db.commit()

    results, total = await SearchService.search_videos(test_db, "dance")
    # Drafts should not appear
    assert all(v.status == VideoStatus.PUBLISHED for v in results)


@pytest.mark.asyncio
async def test_record_search_analytics(test_db: AsyncSession):
    """Test recording search analytics"""
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await SearchService.record_search(test_db, user_id, "dance", 10)
    # Should not raise exception


@pytest.mark.asyncio
async def test_search_pagination(test_db: AsyncSession):
    """Test search result pagination"""
    user = User(
        email="test13@example.com",
        username="testuser13",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()

    # Create multiple videos
    for i in range(5):
        video = Video(
            user_id=user.id,
            title=f"Video {i}",
            video_url=f"https://s3.example.com/video{i}.mp4",
            status=VideoStatus.PUBLISHED,
            is_public=True,
        )
        test_db.add(video)
    await test_db.commit()

    # Get first page
    results1, total = await SearchService.search_videos(
        test_db, "video", limit=2, offset=0
    )
    assert len(results1) <= 2

    # Get second page
    results2, total = await SearchService.search_videos(
        test_db, "video", limit=2, offset=2
    )
    assert len(results2) <= 2
