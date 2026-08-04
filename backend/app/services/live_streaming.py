"""
Live Streaming service - stream sessions, viewer presence, and chat.

This app has no RTMP ingest server or WebRTC/HLS playback pipeline
anywhere, so this covers the *social* layer of live streaming honestly:
a real session lifecycle, real viewer tracking, and real chat, without
pretending any video is actually being transported.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LiveStream, LiveStreamStatus, LiveStreamViewer, LiveChatMessage, User

logger = logging.getLogger(__name__)


class LiveStreamingService:
    """Service for live stream sessions, viewers, and chat"""

    @staticmethod
    async def start_stream(db: AsyncSession, creator_id: UUID, title: str) -> LiveStream:
        result = await db.execute(
            select(LiveStream).where(
                and_(LiveStream.creator_id == creator_id, LiveStream.status == LiveStreamStatus.LIVE)
            )
        )
        if result.scalar():
            raise ValueError("You already have a stream in progress")

        stream = LiveStream(creator_id=creator_id, title=title)
        db.add(stream)
        await db.commit()
        await db.refresh(stream)
        logger.info(f"Stream {stream.id} started by {creator_id}")
        return stream

    @staticmethod
    async def end_stream(db: AsyncSession, creator_id: UUID, stream_id: UUID) -> LiveStream:
        stream = await db.get(LiveStream, stream_id)
        if not stream:
            raise ValueError("Stream not found")
        if stream.creator_id != creator_id:
            raise ValueError("Not authorized")
        if stream.status != LiveStreamStatus.LIVE:
            raise ValueError("Stream has already ended")

        stream.status = LiveStreamStatus.ENDED
        stream.ended_at = datetime.utcnow()
        await db.commit()
        await db.refresh(stream)
        return stream

    @staticmethod
    async def list_live_streams(db: AsyncSession) -> List[LiveStream]:
        result = await db.execute(
            select(LiveStream)
            .where(LiveStream.status == LiveStreamStatus.LIVE)
            .order_by(desc(LiveStream.viewer_count))
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_stream(db: AsyncSession, stream_id: UUID) -> LiveStream:
        stream = await db.get(LiveStream, stream_id)
        if not stream:
            raise ValueError("Stream not found")
        return stream

    @staticmethod
    async def join_stream(db: AsyncSession, user_id: UUID, stream_id: UUID) -> LiveStream:
        stream = await db.get(LiveStream, stream_id)
        if not stream or stream.status != LiveStreamStatus.LIVE:
            raise ValueError("Stream not found or has ended")

        result = await db.execute(
            select(LiveStreamViewer).where(
                and_(LiveStreamViewer.stream_id == stream_id, LiveStreamViewer.user_id == user_id)
            )
        )
        viewer = result.scalar()

        if viewer and viewer.left_at is None:
            return stream  # Already an active viewer - idempotent join

        if viewer:
            viewer.left_at = None
            viewer.joined_at = datetime.utcnow()
        else:
            db.add(LiveStreamViewer(stream_id=stream_id, user_id=user_id))

        stream.viewer_count += 1
        stream.peak_viewer_count = max(stream.peak_viewer_count, stream.viewer_count)
        await db.commit()
        await db.refresh(stream)
        return stream

    @staticmethod
    async def leave_stream(db: AsyncSession, user_id: UUID, stream_id: UUID) -> LiveStream:
        stream = await db.get(LiveStream, stream_id)
        if not stream:
            raise ValueError("Stream not found")

        result = await db.execute(
            select(LiveStreamViewer).where(
                and_(LiveStreamViewer.stream_id == stream_id, LiveStreamViewer.user_id == user_id)
            )
        )
        viewer = result.scalar()
        if not viewer or viewer.left_at is not None:
            return stream  # Not an active viewer - idempotent leave

        viewer.left_at = datetime.utcnow()
        stream.viewer_count = max(0, stream.viewer_count - 1)
        await db.commit()
        await db.refresh(stream)
        return stream

    @staticmethod
    async def post_chat_message(db: AsyncSession, user_id: UUID, stream_id: UUID, content: str) -> dict:
        stream = await db.get(LiveStream, stream_id)
        if not stream or stream.status != LiveStreamStatus.LIVE:
            raise ValueError("Stream not found or has ended")

        message = LiveChatMessage(stream_id=stream_id, user_id=user_id, content=content)
        db.add(message)
        await db.commit()
        await db.refresh(message)

        user = await db.get(User, user_id)
        return {
            "id": message.id,
            "stream_id": message.stream_id,
            "user_id": message.user_id,
            "username": user.username if user else "unknown",
            "content": message.content,
            "created_at": message.created_at,
        }

    @staticmethod
    async def list_chat_messages(db: AsyncSession, stream_id: UUID, limit: int = 50) -> List[dict]:
        result = await db.execute(
            select(LiveChatMessage, User.username)
            .join(User, User.id == LiveChatMessage.user_id)
            .where(LiveChatMessage.stream_id == stream_id)
            .order_by(desc(LiveChatMessage.created_at))
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "id": message.id,
                "stream_id": message.stream_id,
                "user_id": message.user_id,
                "username": username,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message, username in reversed(rows)
        ]
