"""
Video editor service for editing operations
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import json

from app.models import Draft, Segment, Edit, TextOverlay, Sticker
from app.schemas import SegmentCreate, TextOverlayCreate, StickerCreate

logger = logging.getLogger(__name__)


class EditorService:
    """Service for video editing operations"""

    @staticmethod
    async def add_segment(
        db: AsyncSession,
        draft_id: UUID,
        segment_data: SegmentCreate,
    ) -> Segment:
        """
        Add segment to timeline

        Args:
            db: Database session
            draft_id: Draft ID
            segment_data: Segment data

        Returns:
            Created segment
        """
        # Get max order
        result = await db.execute(
            select(Segment).where(Segment.draft_id == draft_id)
            .order_by(desc(Segment.order))
            .limit(1)
        )
        last_segment = result.scalar()
        next_order = (last_segment.order + 1) if last_segment else 0

        segment = Segment(
            draft_id=draft_id,
            start_time=segment_data.start_time,
            end_time=segment_data.end_time,
            order=next_order,
            content_type=segment_data.content_type,
            content_url=segment_data.content_url,
            effects=json.dumps(segment_data.effects) if segment_data.effects else None,
            transition_type=segment_data.transition_type,
            transition_duration=segment_data.transition_duration,
            volume=segment_data.volume,
            muted=segment_data.muted,
        )
        db.add(segment)
        await db.commit()
        await db.refresh(segment)

        logger.info(f"Segment added to draft {draft_id}")
        return segment

    @staticmethod
    async def get_segments(
        db: AsyncSession,
        draft_id: UUID,
    ) -> List[Segment]:
        """Get all segments for draft"""
        result = await db.execute(
            select(Segment).where(Segment.draft_id == draft_id)
            .order_by(Segment.order)
        )
        return result.scalars().all()

    @staticmethod
    async def update_segment(
        db: AsyncSession,
        segment_id: UUID,
        segment_data: SegmentCreate,
    ) -> Segment:
        """Update segment"""
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        segment.start_time = segment_data.start_time
        segment.end_time = segment_data.end_time
        segment.content_type = segment_data.content_type
        segment.content_url = segment_data.content_url
        segment.effects = json.dumps(segment_data.effects) if segment_data.effects else None
        segment.transition_type = segment_data.transition_type
        segment.transition_duration = segment_data.transition_duration
        segment.volume = segment_data.volume
        segment.muted = segment_data.muted

        await db.commit()
        await db.refresh(segment)

        logger.info(f"Segment updated: {segment_id}")
        return segment

    @staticmethod
    async def delete_segment(
        db: AsyncSession,
        segment_id: UUID,
    ) -> None:
        """Delete segment"""
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        await db.delete(segment)
        await db.commit()

        logger.info(f"Segment deleted: {segment_id}")

    @staticmethod
    async def reorder_segments(
        db: AsyncSession,
        draft_id: UUID,
        segment_ids: List[UUID],
    ) -> None:
        """
        Reorder segments in timeline

        Args:
            db: Database session
            draft_id: Draft ID
            segment_ids: List of segment IDs in new order
        """
        for order, segment_id in enumerate(segment_ids):
            result = await db.execute(
                select(Segment).where(
                    and_(
                        Segment.id == segment_id,
                        Segment.draft_id == draft_id,
                    )
                )
            )
            segment = result.scalar()
            if segment:
                segment.order = order

        await db.commit()
        logger.info(f"Segments reordered in draft {draft_id}")

    @staticmethod
    async def add_text_overlay(
        db: AsyncSession,
        segment_id: UUID,
        text_data: TextOverlayCreate,
    ) -> TextOverlay:
        """Add text overlay to segment"""
        overlay = TextOverlay(
            segment_id=segment_id,
            text=text_data.text,
            font_family=text_data.font_family,
            font_size=text_data.font_size,
            color=text_data.color,
            x=text_data.x,
            y=text_data.y,
            width=text_data.width,
            height=text_data.height,
            animation_type=text_data.animation_type,
            animation_duration=text_data.animation_duration,
        )
        db.add(overlay)
        await db.commit()
        await db.refresh(overlay)

        logger.info(f"Text overlay added to segment {segment_id}")
        return overlay

    @staticmethod
    async def get_text_overlays(
        db: AsyncSession,
        segment_id: UUID,
    ) -> List[TextOverlay]:
        """Get text overlays for segment"""
        result = await db.execute(
            select(TextOverlay).where(TextOverlay.segment_id == segment_id)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_text_overlay(
        db: AsyncSession,
        overlay_id: UUID,
    ) -> None:
        """Delete text overlay"""
        result = await db.execute(
            select(TextOverlay).where(TextOverlay.id == overlay_id)
        )
        overlay = result.scalar()
        if not overlay:
            raise ValueError("Text overlay not found")

        await db.delete(overlay)
        await db.commit()

        logger.info(f"Text overlay deleted: {overlay_id}")

    @staticmethod
    async def add_sticker(
        db: AsyncSession,
        segment_id: UUID,
        sticker_data: StickerCreate,
    ) -> Sticker:
        """Add sticker to segment"""
        sticker = Sticker(
            segment_id=segment_id,
            sticker_url=sticker_data.sticker_url,
            sticker_type=sticker_data.sticker_type,
            x=sticker_data.x,
            y=sticker_data.y,
            width=sticker_data.width,
            height=sticker_data.height,
            rotation=sticker_data.rotation,
            animation_type=sticker_data.animation_type,
        )
        db.add(sticker)
        await db.commit()
        await db.refresh(sticker)

        logger.info(f"Sticker added to segment {segment_id}")
        return sticker

    @staticmethod
    async def get_stickers(
        db: AsyncSession,
        segment_id: UUID,
    ) -> List[Sticker]:
        """Get stickers for segment"""
        result = await db.execute(
            select(Sticker).where(Sticker.segment_id == segment_id)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_sticker(
        db: AsyncSession,
        sticker_id: UUID,
    ) -> None:
        """Delete sticker"""
        result = await db.execute(
            select(Sticker).where(Sticker.id == sticker_id)
        )
        sticker = result.scalar()
        if not sticker:
            raise ValueError("Sticker not found")

        await db.delete(sticker)
        await db.commit()

        logger.info(f"Sticker deleted: {sticker_id}")

    @staticmethod
    async def apply_effect(
        db: AsyncSession,
        segment_id: UUID,
        effect_name: str,
        effect_params: Optional[dict] = None,
    ) -> Segment:
        """
        Apply effect to segment

        Args:
            db: Database session
            segment_id: Segment ID
            effect_name: Name of effect (blur, brighten, saturate, etc.)
            effect_params: Effect parameters

        Returns:
            Updated segment
        """
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        # Effects are stored as a flat list of effect-name strings (matching
        # SegmentResponse.effects: list[str]); effect_params isn't persisted
        # since there's no schema field for it yet.
        effects = json.loads(segment.effects) if segment.effects else []
        effects.append(effect_name)
        segment.effects = json.dumps(effects)
        await db.commit()
        await db.refresh(segment)

        logger.info(f"Effect '{effect_name}' applied to segment {segment_id}")
        return segment

    @staticmethod
    async def remove_effect(
        db: AsyncSession,
        segment_id: UUID,
        effect_name: str,
    ) -> Segment:
        """Remove effect from segment"""
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        # Parse current effects
        effects = json.loads(segment.effects) if segment.effects else []

        # Remove effect
        effects = [e for e in effects if e != effect_name]

        segment.effects = json.dumps(effects) if effects else None
        await db.commit()
        await db.refresh(segment)

        logger.info(f"Effect '{effect_name}' removed from segment {segment_id}")
        return segment

    @staticmethod
    async def calculate_total_duration(
        db: AsyncSession,
        draft_id: UUID,
    ) -> int:
        """
        Calculate total video duration

        Args:
            db: Database session
            draft_id: Draft ID

        Returns:
            Total duration in milliseconds
        """
        result = await db.execute(
            select(Segment).where(Segment.draft_id == draft_id)
            .order_by(Segment.order)
        )
        segments = result.scalars().all()

        if not segments:
            return 0

        # Total duration is the end time of the last segment
        return segments[-1].end_time

    @staticmethod
    async def get_editor_state(
        db: AsyncSession,
        draft_id: UUID,
    ) -> dict:
        """
        Get complete editor state for draft

        Args:
            db: Database session
            draft_id: Draft ID

        Returns:
            Complete editor state with segments, overlays, stickers
        """
        # Get segments
        segments_result = await db.execute(
            select(Segment).where(Segment.draft_id == draft_id)
            .order_by(Segment.order)
        )
        segments = segments_result.scalars().all()

        # Get all overlays and stickers
        segment_ids = [s.id for s in segments]

        overlays_result = await db.execute(
            select(TextOverlay).where(TextOverlay.segment_id.in_(segment_ids))
            if segment_ids else select(TextOverlay).where(False)
        )
        overlays = overlays_result.scalars().all()

        stickers_result = await db.execute(
            select(Sticker).where(Sticker.segment_id.in_(segment_ids))
            if segment_ids else select(Sticker).where(False)
        )
        stickers = stickers_result.scalars().all()

        # Calculate total duration
        total_duration = await EditorService.calculate_total_duration(db, draft_id)

        return {
            "draft_id": draft_id,
            "segments": segments,
            "text_overlays": overlays,
            "stickers": stickers,
            "total_duration": total_duration,
        }

    @staticmethod
    async def export_video(
        db: AsyncSession,
        draft_id: UUID,
        export_quality: str = "1080p",  # 360p, 720p, 1080p, 4k
        export_format: str = "mp4",
    ) -> dict:
        """
        Export edited video (queue for processing)

        Args:
            db: Database session
            draft_id: Draft ID
            export_quality: Export quality
            export_format: Export format (mp4, webm, mov, etc.)

        Returns:
            Export job info
        """
        # TODO: Implement actual video export with FFmpeg/celery
        # For now, return stub response

        from uuid import uuid4

        export_id = uuid4()

        logger.info(f"Video export queued: draft {draft_id}, quality {export_quality}")

        return {
            "export_id": export_id,
            "draft_id": draft_id,
            "quality": export_quality,
            "format": export_format,
            "status": "queued",
            "progress": 0,
            "created_at": datetime.utcnow(),
        }

    @staticmethod
    async def trim_video(
        db: AsyncSession,
        segment_id: UUID,
        start_time: int,
        end_time: int,
    ) -> Segment:
        """
        Trim segment to specific time range

        Args:
            db: Database session
            segment_id: Segment ID
            start_time: Start time in ms
            end_time: End time in ms

        Returns:
            Updated segment
        """
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        segment.start_time = start_time
        segment.end_time = end_time

        await db.commit()
        await db.refresh(segment)

        logger.info(f"Segment trimmed: {segment_id}")
        return segment

    @staticmethod
    async def adjust_speed(
        db: AsyncSession,
        segment_id: UUID,
        speed_multiplier: float,  # 0.5, 1.0, 1.5, 2.0, etc.
    ) -> Segment:
        """
        Adjust playback speed of segment

        Args:
            db: Database session
            segment_id: Segment ID
            speed_multiplier: Speed multiplier (0.5 = half speed, 2.0 = double speed)

        Returns:
            Updated segment
        """
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        # Apply speed effect
        await EditorService.apply_effect(
            db,
            segment_id,
            "speed",
            {"multiplier": speed_multiplier},
        )

        logger.info(f"Speed adjusted for segment {segment_id}: {speed_multiplier}x")
        return segment

    @staticmethod
    async def mute_segment(
        db: AsyncSession,
        segment_id: UUID,
        muted: bool,
    ) -> Segment:
        """Mute or unmute segment audio"""
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        segment.muted = muted
        await db.commit()
        await db.refresh(segment)

        logger.info(f"Segment {segment_id} {'muted' if muted else 'unmuted'}")
        return segment

    @staticmethod
    async def adjust_volume(
        db: AsyncSession,
        segment_id: UUID,
        volume: int,  # 0-100
    ) -> Segment:
        """
        Adjust segment volume

        Args:
            db: Database session
            segment_id: Segment ID
            volume: Volume level (0-100)

        Returns:
            Updated segment
        """
        result = await db.execute(
            select(Segment).where(Segment.id == segment_id)
        )
        segment = result.scalar()
        if not segment:
            raise ValueError("Segment not found")

        segment.volume = max(0, min(100, volume))
        await db.commit()
        await db.refresh(segment)

        logger.info(f"Volume adjusted for segment {segment_id}: {segment.volume}%")
        return segment
