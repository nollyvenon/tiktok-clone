"""
Seed the database with realistic demo data covering the app's core
modules: users, follows, videos, likes/comments, a creator fund
program + application, and a creator shop with products.

Run against a freshly-migrated database:
    python -m scripts.seed

Idempotent-ish: re-running will raise on unique-constraint conflicts
(duplicate emails/usernames) rather than silently duplicating data -
intended to run once against a fresh database, matching how this repo
runs migrations fresh before seeding.
"""

import asyncio
from datetime import datetime, timedelta

from app.database import AsyncSessionLocal
from app.security import hash_password
from app.models import (
    User, UserRole, Follow, Video, VideoStatus, Like, Comment,
    FundingProgram, CreatorApplication, ApplicationStatus,
    Shop, ShopProduct,
)


DEMO_PASSWORD = "DemoPass@2026"


async def seed():
    async with AsyncSessionLocal() as db:
        print("Seeding users...")
        users = {}
        user_specs = [
            ("admin@tiktokclone.demo", "admin", "Ada", "Min", UserRole.ADMIN, True, True),
            ("maya.creates@tiktokclone.demo", "mayacreates", "Maya", "Chen", UserRole.CREATOR, True, True),
            ("jordan.films@tiktokclone.demo", "jordanfilms", "Jordan", "Reyes", UserRole.CREATOR, True, False),
            ("priya.codes@tiktokclone.demo", "priyacodes", "Priya", "Sharma", UserRole.CREATOR, True, False),
            ("sam.viewer@tiktokclone.demo", "samviewer", "Sam", "Okafor", UserRole.USER, False, False),
            ("lee.viewer@tiktokclone.demo", "leeviewer", "Lee", "Park", UserRole.USER, False, False),
        ]
        for email, username, first, last, role, is_creator, is_verified in user_specs:
            user = User(
                email=email,
                username=username,
                password_hash=hash_password(DEMO_PASSWORD),
                first_name=first,
                last_name=last,
                bio=f"Hey, I'm {first}! Sharing what I love on TikTok Clone.",
                is_active=True,
                is_verified=is_verified,
                is_creator=is_creator,
                role=role,
            )
            db.add(user)
            users[username] = user
        await db.commit()
        for user in users.values():
            await db.refresh(user)
        print(f"  {len(users)} users created")

        print("Seeding follows...")
        follow_pairs = [
            ("samviewer", "mayacreates"),
            ("samviewer", "jordanfilms"),
            ("leeviewer", "mayacreates"),
            ("leeviewer", "priyacodes"),
            ("jordanfilms", "mayacreates"),
            ("priyacodes", "mayacreates"),
        ]
        for follower, following in follow_pairs:
            db.add(Follow(follower_id=users[follower].id, following_id=users[following].id, is_active=True))
        await db.commit()
        print(f"  {len(follow_pairs)} follows created")

        print("Seeding videos...")
        video_specs = [
            ("mayacreates", "Sunset timelapse from the rooftop", "#sunset #timelapse #citylife", 15400, 2100),
            ("mayacreates", "3-ingredient pasta that actually slaps", "#cooking #pasta #easyrecipe", 48200, 6700),
            ("jordanfilms", "Shot this entirely on a phone gimbal", "#filmmaking #cinematography", 9800, 1200),
            ("jordanfilms", "Color grading before/after", "#colorgrading #filmmaking", 21300, 3400),
            ("priyacodes", "Explaining recursion in 60 seconds", "#coding #python #learnontiktok", 33100, 5200),
        ]
        videos = []
        for username, title, hashtags, views, likes in video_specs:
            video = Video(
                user_id=users[username].id,
                title=title,
                description=title,
                video_url=f"https://example.com/videos/{username}-{len(videos)}.mp4",
                thumbnail_url=f"https://example.com/thumbnails/{username}-{len(videos)}.jpg",
                duration=30,
                hashtags=hashtags,
                status=VideoStatus.PUBLISHED,
                is_public=True,
                views_count=views,
                likes_count=likes,
                comments_count=0,
                published_at=datetime.utcnow() - timedelta(days=len(videos)),
            )
            db.add(video)
            videos.append(video)
        await db.commit()
        for video in videos:
            await db.refresh(video)
        print(f"  {len(videos)} videos created")

        print("Seeding likes and comments...")
        viewers = [users["samviewer"], users["leeviewer"], users["jordanfilms"], users["priyacodes"]]
        comment_texts = [
            "This is amazing!", "Wait this is so good", "How did you do this??",
            "Saving this for later", "Underrated creator fr",
        ]
        comment_count = 0
        for video in videos:
            for viewer in viewers:
                if viewer.id == video.user_id:
                    continue
                db.add(Like(user_id=viewer.id, video_id=video.id))
            db.add(Comment(
                video_id=video.id,
                user_id=viewers[comment_count % len(viewers)].id,
                content=comment_texts[comment_count % len(comment_texts)],
            ))
            video.comments_count += 1
            comment_count += 1
        await db.commit()
        print(f"  likes + {comment_count} comments created")

        print("Seeding a Creator Fund program and application...")
        program = FundingProgram(
            name="Rising Creators Fund",
            description="Support for creators building their first real audience.",
            min_followers=1,
            min_published_videos=1,
            min_total_views=1000,
            award_amount=50000,
        )
        db.add(program)
        await db.commit()
        await db.refresh(program)

        db.add(CreatorApplication(
            program_id=program.id,
            user_id=users["mayacreates"].id,
            followers_count=2,
            published_videos_count=2,
            total_views_count=63600,
            meets_requirements=True,
            status=ApplicationStatus.PENDING,
        ))
        await db.commit()
        print("  1 funding program + 1 pending application created")

        print("Seeding a Creator Shop...")
        shop = Shop(
            user_id=users["mayacreates"].id,
            name="Maya's Studio Shop",
            description="Behind-the-scenes merch and digital presets.",
        )
        db.add(shop)
        await db.commit()
        await db.refresh(shop)

        db.add_all([
            ShopProduct(
                shop_id=shop.id,
                name="Cinematic LUT Pack (Vol. 1)",
                description="10 color grading presets used in my videos.",
                price=1200,
                stock_quantity=None,
            ),
            ShopProduct(
                shop_id=shop.id,
                name="Studio Logo Sticker Pack",
                description="Set of 5 vinyl stickers.",
                price=800,
                stock_quantity=150,
            ),
        ])
        await db.commit()
        print("  1 shop + 2 products created")

        print("\nDone. Demo login (any seeded user): password is", DEMO_PASSWORD)
        print("Admin: admin@tiktokclone.demo")
        print("Creators: maya.creates@tiktokclone.demo, jordan.films@tiktokclone.demo, priya.codes@tiktokclone.demo")
        print("Viewers: sam.viewer@tiktokclone.demo, lee.viewer@tiktokclone.demo")


if __name__ == "__main__":
    asyncio.run(seed())
