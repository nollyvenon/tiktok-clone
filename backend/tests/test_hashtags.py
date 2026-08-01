"""
Tests for hashtag trending system (Module 9)
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HashtagTrend, HashtagAnalytics, Challenge, VideoStatus, Video
from app.services.hashtags import HashtagService


@pytest.mark.asyncio
async def test_get_trending_hashtags(db: AsyncSession):
    """Test getting trending hashtags"""
    # Create test hashtags
    hashtag1 = HashtagTrend(
        hashtag="dance",
        region="US",
        usage_count=1000,
        unique_creators=50,
        popularity_score=85,
        rank_position=1,
    )
    hashtag2 = HashtagTrend(
        hashtag="music",
        region="US",
        usage_count=800,
        unique_creators=40,
        popularity_score=75,
        rank_position=2,
    )
    db.add(hashtag1)
    db.add(hashtag2)
    await db.commit()

    # Get trending
    trends = await HashtagService.get_trending_hashtags(db, region="US", limit=10)
    assert len(trends) >= 2


@pytest.mark.asyncio
async def test_track_hashtag_usage(db: AsyncSession):
    """Test tracking hashtag usage"""
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    # Track usage
    await HashtagService.track_hashtag_usage(db, "#trends", "US", user_id)

    # Verify trend was created
    trend = await db.execute(
        db.query(HashtagTrend).filter(HashtagTrend.hashtag == "#trends")
    )
    assert trend is not None


@pytest.mark.asyncio
async def test_get_hashtag_analytics(db: AsyncSession):
    """Test getting hashtag analytics"""
    hashtag = "dance"

    # Create analytics records
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        analytics = HashtagAnalytics(
            hashtag=hashtag,
            date=date,
            usage_count=100 + (i * 10),
            unique_creators=20 + i,
        )
        db.add(analytics)
    await db.commit()

    # Get analytics
    results = await HashtagService.get_hashtag_analytics(db, hashtag, days=30)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_create_challenge(db: AsyncSession):
    """Test creating a hashtag challenge"""
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=7)

    challenge = await HashtagService.create_challenge(
        db,
        hashtag="dance",
        title="Dancing Challenge",
        description="Show your best moves",
        rules="Keep it family friendly",
        start_date=start_date,
        end_date=end_date,
        prize_pool=5000,
    )

    assert challenge.hashtag == "dance"
    assert challenge.title == "Dancing Challenge"
    assert challenge.prize_pool == 5000


@pytest.mark.asyncio
async def test_get_active_challenges(db: AsyncSession):
    """Test getting active challenges"""
    now = datetime.utcnow()

    # Create active challenge
    challenge = Challenge(
        hashtag="dance",
        title="Active Challenge",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=6),
        is_active=True,
    )
    db.add(challenge)
    await db.commit()

    # Get active challenges
    challenges = await HashtagService.get_active_challenges(db, region="US")
    assert len(challenges) > 0


@pytest.mark.asyncio
async def test_get_hashtag_stats(db: AsyncSession):
    """Test getting hashtag statistics"""
    hashtag = "music"
    region = "US"

    # Create trend
    trend = HashtagTrend(
        hashtag=hashtag,
        region=region,
        usage_count=500,
        unique_creators=25,
        total_views=10000,
        total_likes=2000,
        popularity_score=70,
    )
    db.add(trend)
    await db.commit()

    # Get stats
    stats = await HashtagService.get_hashtag_stats(db, hashtag, region)
    assert stats["hashtag"] == hashtag
    assert stats["usage_count"] == 500


@pytest.mark.asyncio
async def test_search_hashtags(db: AsyncSession):
    """Test searching hashtags"""
    # Create test hashtags
    hashtag1 = HashtagTrend(
        hashtag="dancetrend",
        region="US",
        usage_count=500,
    )
    hashtag2 = HashtagTrend(
        hashtag="dance",
        region="US",
        usage_count=300,
    )
    db.add(hashtag1)
    db.add(hashtag2)
    await db.commit()

    # Search
    results = await HashtagService.search_hashtags(db, "dance", "US", limit=10)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_get_category_trends(db: AsyncSession):
    """Test getting trends by category"""
    # Create categorized hashtags
    hashtag1 = HashtagTrend(
        hashtag="music",
        region="US",
        category="Entertainment",
        usage_count=500,
        popularity_score=80,
    )
    hashtag2 = HashtagTrend(
        hashtag="fitness",
        region="US",
        category="Health",
        usage_count=400,
        popularity_score=70,
    )
    db.add(hashtag1)
    db.add(hashtag2)
    await db.commit()

    # Get Entertainment trends
    results = await HashtagService.get_category_trends(
        db, "Entertainment", "US", limit=10
    )
    assert len(results) > 0


@pytest.mark.asyncio
async def test_calculate_trend_metrics(db: AsyncSession):
    """Test calculating trend metrics"""
    hashtag = "trending"
    region = "US"

    # Create trend
    trend = HashtagTrend(
        hashtag=hashtag,
        region=region,
        usage_count=1000,
    )
    db.add(trend)

    # Create analytics for past 7 days
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        analytics = HashtagAnalytics(
            hashtag=hashtag,
            date=date,
            usage_count=100 + (i * 20),
            unique_creators=10 + i,
        )
        db.add(analytics)

    await db.commit()

    # Calculate metrics
    metrics = await HashtagService.calculate_trend_metrics(db, hashtag, region)
    assert "popularity_score" in metrics
    assert "trend_velocity" in metrics


@pytest.mark.asyncio
async def test_update_challenge_stats(db: AsyncSession):
    """Test updating challenge participation stats"""
    challenge = Challenge(
        hashtag="dance",
        title="Test Challenge",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
        participation_count=0,
    )
    db.add(challenge)
    await db.commit()

    # Update stats
    video_id = UUID("00000000-0000-0000-0000-000000000001")
    await HashtagService.update_challenge_stats(db, challenge.id, video_id)

    # Verify
    updated = await db.get(Challenge, challenge.id)
    assert updated.participation_count > 0


@pytest.mark.asyncio
async def test_get_challenge_details(db: AsyncSession):
    """Test getting challenge details"""
    challenge = Challenge(
        hashtag="music",
        title="Music Challenge",
        description="Show your musical talents",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
    )
    db.add(challenge)
    await db.commit()

    # Get details
    result = await HashtagService.get_challenge_details(db, challenge.id)
    assert result is not None
    assert result.title == "Music Challenge"


@pytest.mark.asyncio
async def test_clean_old_analytics(db: AsyncSession):
    """Test cleaning old analytics records"""
    hashtag = "old"

    # Create old records (100+ days old)
    old_date = datetime.utcnow() - timedelta(days=120)
    for i in range(5):
        analytics = HashtagAnalytics(
            hashtag=hashtag,
            date=old_date - timedelta(days=i),
            usage_count=50,
            unique_creators=5,
        )
        db.add(analytics)

    # Create recent records
    recent = HashtagAnalytics(
        hashtag=hashtag,
        date=datetime.utcnow(),
        usage_count=50,
        unique_creators=5,
    )
    db.add(recent)
    await db.commit()

    # Clean old
    deleted = await HashtagService.clean_old_analytics(db, days_old=90)
    assert deleted >= 5


@pytest.mark.asyncio
async def test_get_challenge_videos(db: AsyncSession):
    """Test getting videos for a challenge"""
    # Create challenge
    challenge = Challenge(
        hashtag="dance",
        title="Dance Challenge",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
    )
    db.add(challenge)
    await db.commit()

    # Get challenge videos
    videos, total = await HashtagService.get_challenge_videos(
        db, challenge.id, limit=30, offset=0
    )
    assert isinstance(videos, list)
    assert isinstance(total, int)


@pytest.mark.asyncio
async def test_hashtag_by_region(db: AsyncSession):
    """Test hashtag trending by region"""
    # Create hashtags in different regions
    us_hashtag = HashtagTrend(
        hashtag="dance",
        region="US",
        usage_count=1000,
        rank_position=1,
    )
    uk_hashtag = HashtagTrend(
        hashtag="dance",
        region="UK",
        usage_count=500,
        rank_position=1,
    )
    db.add(us_hashtag)
    db.add(uk_hashtag)
    await db.commit()

    # Get US trends
    us_trends = await HashtagService.get_trending_hashtags(db, region="US")
    # Get UK trends
    uk_trends = await HashtagService.get_trending_hashtags(db, region="UK")

    assert len(us_trends) > 0
    assert len(uk_trends) > 0


@pytest.mark.asyncio
async def test_hashtag_trending_velocity(db: AsyncSession):
    """Test trend velocity calculation"""
    hashtag = "viral"
    region = "US"

    # Create trend with initial data
    trend = HashtagTrend(
        hashtag=hashtag,
        region=region,
        usage_count=1000,
    )
    db.add(trend)

    # Create analytics showing growth
    base_date = datetime.utcnow()
    for day in range(7):
        date = base_date - timedelta(days=day)
        analytics = HashtagAnalytics(
            hashtag=hashtag,
            date=date,
            usage_count=100 + (day * 30),
            unique_creators=10 + day,
        )
        db.add(analytics)

    await db.commit()

    # Calculate metrics
    metrics = await HashtagService.calculate_trend_metrics(db, hashtag, region)
    # Positive velocity indicates growth
    assert "trend_velocity" in metrics


@pytest.mark.asyncio
async def test_hashtag_unique_creators(db: AsyncSession):
    """Test tracking unique creators per hashtag"""
    hashtag = "music"
    region = "US"

    trend = HashtagTrend(
        hashtag=hashtag,
        region=region,
        usage_count=100,
        unique_creators=50,
    )
    db.add(trend)
    await db.commit()

    # Get stats
    stats = await HashtagService.get_hashtag_stats(db, hashtag, region)
    assert stats["unique_creators"] == 50


@pytest.mark.asyncio
async def test_hashtag_analytics_daily_tracking(db: AsyncSession):
    """Test daily analytics tracking"""
    hashtag = "daily"

    # Create multiple days of analytics
    for day in range(7):
        date = datetime.utcnow() - timedelta(days=day)
        analytics = HashtagAnalytics(
            hashtag=hashtag,
            date=date,
            usage_count=100 * (day + 1),
            unique_creators=10 * (day + 1),
        )
        db.add(analytics)

    await db.commit()

    # Get 7-day analytics
    results = await HashtagService.get_hashtag_analytics(db, hashtag, days=7)
    assert len(results) == 7


@pytest.mark.asyncio
async def test_challenge_participation_count(db: AsyncSession):
    """Test challenge participation tracking"""
    challenge = Challenge(
        hashtag="contest",
        title="Contest",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        participation_count=0,
    )
    db.add(challenge)
    await db.commit()

    # Update participation 5 times
    for _ in range(5):
        video_id = UUID("00000000-0000-0000-0000-000000000001")
        await HashtagService.update_challenge_stats(db, challenge.id, video_id)

    # Verify count
    updated = await db.get(Challenge, challenge.id)
    assert updated.participation_count >= 5


@pytest.mark.asyncio
async def test_hashtag_none_returns_empty(db: AsyncSession):
    """Test that non-existent hashtag returns empty stats"""
    stats = await HashtagService.get_hashtag_stats(db, "nonexistent", "US")
    assert stats["usage_count"] == 0
    assert stats["popularity_score"] == 0
