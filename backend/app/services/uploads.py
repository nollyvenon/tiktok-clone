"""
Upload service for video upload and processing
"""

from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
import os

from app.models import Upload, Draft, Video, UploadStatus, DraftStatus, VideoStatus
from app.schemas import DraftCreate
from app.services.videos import VideoService

logger = logging.getLogger(__name__)


class UploadService:
    """Service for video upload and processing"""

    @staticmethod
    async def create_upload(
        db: AsyncSession,
        user_id: UUID,
        filename: str,
        file_size: int,
        mime_type: str,
        storage_path: str,
    ) -> Upload:
        """
        Create upload record

        Args:
            db: Database session
            user_id: User ID
            filename: Original filename
            file_size: File size in bytes
            mime_type: MIME type
            storage_path: S3 or local path

        Returns:
            Created upload object
        """
        upload = Upload(
            user_id=user_id,
            original_filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            storage_path=storage_path,
            status=UploadStatus.UPLOADING,
            progress=0,
        )
        db.add(upload)
        await db.commit()
        await db.refresh(upload)

        logger.info(f"Upload created: {upload.id} by user {user_id}")
        return upload

    @staticmethod
    async def get_upload(
        db: AsyncSession,
        upload_id: UUID,
    ) -> Optional[Upload]:
        """Get upload by ID"""
        result = await db.execute(
            select(Upload).where(Upload.id == upload_id)
        )
        return result.scalar()

    @staticmethod
    async def update_upload_progress(
        db: AsyncSession,
        upload_id: UUID,
        progress: int,
    ) -> None:
        """Update upload progress"""
        upload = await UploadService.get_upload(db, upload_id)
        if upload:
            upload.progress = min(100, progress)
            await db.commit()

    @staticmethod
    async def mark_upload_completed(
        db: AsyncSession,
        upload_id: UUID,
        processed_video_url: str,
        thumbnail_url: str,
        duration: int,
    ) -> Upload:
        """
        Mark upload as completed

        Args:
            db: Database session
            upload_id: Upload ID
            processed_video_url: URL to processed video
            thumbnail_url: URL to thumbnail
            duration: Video duration in seconds

        Returns:
            Updated upload
        """
        upload = await UploadService.get_upload(db, upload_id)
        if not upload:
            raise ValueError("Upload not found")

        upload.status = UploadStatus.COMPLETED
        upload.progress = 100
        upload.processed_video_url = processed_video_url
        upload.thumbnail_url = thumbnail_url
        upload.duration = duration
        upload.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(upload)

        logger.info(f"Upload completed: {upload_id}")
        return upload

    @staticmethod
    async def mark_upload_failed(
        db: AsyncSession,
        upload_id: UUID,
        error_message: str,
    ) -> Upload:
        """Mark upload as failed"""
        upload = await UploadService.get_upload(db, upload_id)
        if not upload:
            raise ValueError("Upload not found")

        upload.status = UploadStatus.FAILED
        upload.error_message = error_message

        await db.commit()
        await db.refresh(upload)

        logger.error(f"Upload failed: {upload_id} - {error_message}")
        return upload

    @staticmethod
    async def create_draft(
        db: AsyncSession,
        user_id: UUID,
        upload_id: Optional[UUID] = None,
        draft_data: Optional[DraftCreate] = None,
    ) -> Draft:
        """
        Create video draft

        Args:
            db: Database session
            user_id: Creator user ID
            upload_id: Associated upload ID
            draft_data: Draft metadata

        Returns:
            Created draft
        """
        draft = Draft(
            user_id=user_id,
            upload_id=upload_id,
            status=DraftStatus.EDITING,
        )

        if draft_data:
            draft.title = draft_data.title
            draft.description = draft_data.description
            draft.hashtags = draft_data.hashtags
            draft.thumbnail_url = draft_data.thumbnail_url
            draft.is_public = draft_data.is_public
            draft.allow_comments = draft_data.allow_comments
            draft.allow_duets = draft_data.allow_duets
            draft.allow_stitches = draft_data.allow_stitches
            draft.scheduled_publish_at = draft_data.scheduled_publish_at

        db.add(draft)
        await db.commit()
        await db.refresh(draft)

        logger.info(f"Draft created: {draft.id} by user {user_id}")
        return draft

    @staticmethod
    async def get_draft(
        db: AsyncSession,
        draft_id: UUID,
    ) -> Optional[Draft]:
        """Get draft by ID"""
        result = await db.execute(
            select(Draft).where(Draft.id == draft_id)
        )
        return result.scalar()

    @staticmethod
    async def update_draft(
        db: AsyncSession,
        draft_id: UUID,
        user_id: UUID,
        draft_data: DraftCreate,
    ) -> Draft:
        """
        Update draft

        Args:
            db: Database session
            draft_id: Draft ID
            user_id: Current user ID (must be creator)
            draft_data: Updated draft data

        Returns:
            Updated draft
        """
        draft = await UploadService.get_draft(db, draft_id)
        if not draft:
            raise ValueError("Draft not found")

        if draft.user_id != user_id:
            raise ValueError("Not authorized to update this draft")

        draft.title = draft_data.title
        draft.description = draft_data.description
        draft.hashtags = draft_data.hashtags
        draft.thumbnail_url = draft_data.thumbnail_url
        draft.is_public = draft_data.is_public
        draft.allow_comments = draft_data.allow_comments
        draft.allow_duets = draft_data.allow_duets
        draft.allow_stitches = draft_data.allow_stitches
        draft.scheduled_publish_at = draft_data.scheduled_publish_at

        await db.commit()
        await db.refresh(draft)

        logger.info(f"Draft updated: {draft_id}")
        return draft

    @staticmethod
    async def delete_draft(
        db: AsyncSession,
        draft_id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete draft (and associated upload)"""
        draft = await UploadService.get_draft(db, draft_id)
        if not draft:
            raise ValueError("Draft not found")

        if draft.user_id != user_id:
            raise ValueError("Not authorized to delete this draft")

        # Delete associated upload if exists
        if draft.upload_id:
            upload = await UploadService.get_upload(db, draft.upload_id)
            if upload:
                await db.delete(upload)

        await db.delete(draft)
        await db.commit()

        logger.info(f"Draft deleted: {draft_id}")

    @staticmethod
    async def get_user_drafts(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[list[Draft], int]:
        """Get user's drafts"""
        from sqlalchemy import func, desc

        # Get total count
        count_result = await db.execute(
            select(func.count(Draft.id)).select_from(Draft).where(
                Draft.user_id == user_id
            )
        )
        total = count_result.scalar() or 0

        # Get paginated results
        result = await db.execute(
            select(Draft)
            .where(Draft.user_id == user_id)
            .order_by(desc(Draft.updated_at))
            .offset(offset)
            .limit(limit)
        )
        drafts = result.scalars().all()

        return drafts, total

    @staticmethod
    async def publish_draft(
        db: AsyncSession,
        draft_id: UUID,
        user_id: UUID,
    ) -> Video:
        """
        Publish draft as video

        Args:
            db: Database session
            draft_id: Draft ID
            user_id: Current user ID

        Returns:
            Published video

        Raises:
            ValueError: If draft invalid or user not authorized
        """
        draft = await UploadService.get_draft(db, draft_id)
        if not draft:
            raise ValueError("Draft not found")

        if draft.user_id != user_id:
            raise ValueError("Not authorized to publish this draft")

        if not draft.upload_id:
            raise ValueError("No upload associated with draft")

        # Get upload
        upload = await UploadService.get_upload(db, draft.upload_id)
        if not upload or upload.status != UploadStatus.COMPLETED:
            raise ValueError("Upload not ready for publishing")

        # Create video from draft
        video = Video(
            user_id=user_id,
            title=draft.title,
            description=draft.description,
            video_url=upload.processed_video_url,
            thumbnail_url=draft.thumbnail_url or upload.thumbnail_url,
            duration=upload.duration,
            hashtags=draft.hashtags,
            is_public=draft.is_public,
            allow_comments=draft.allow_comments,
            allow_duets=draft.allow_duets,
            allow_stitches=draft.allow_stitches,
            status=VideoStatus.PUBLISHED,
            published_at=datetime.utcnow(),
        )
        db.add(video)
        await db.flush()
        await db.commit()
        await db.refresh(video)

        # Update draft
        draft.status = DraftStatus.PUBLISHED
        draft.published_video_id = video.id
        await db.commit()

        logger.info(f"Draft published as video: {video.id}")
        return video

    @staticmethod
    async def schedule_publish(
        db: AsyncSession,
        draft_id: UUID,
        user_id: UUID,
        publish_at: datetime,
    ) -> Draft:
        """Schedule draft for future publishing"""
        draft = await UploadService.get_draft(db, draft_id)
        if not draft:
            raise ValueError("Draft not found")

        if draft.user_id != user_id:
            raise ValueError("Not authorized")

        draft.scheduled_publish_at = publish_at
        draft.status = DraftStatus.READY_TO_PUBLISH
        await db.commit()
        await db.refresh(draft)

        logger.info(f"Draft scheduled for publishing: {draft_id}")
        return draft

    @staticmethod
    async def get_presigned_url(
        upload_id: UUID,
        filename: str,
    ) -> str:
        """
        Get presigned URL for S3 upload

        Args:
            upload_id: Upload ID
            filename: Filename

        Returns:
            Presigned URL

        Note: This is a stub - implement with actual S3 boto3 client
        """
        # TODO: Implement with boto3 S3 client
        # For now, return a mock presigned URL
        return f"https://s3.amazonaws.com/tiktok-clone/uploads/{upload_id}/{filename}"


# Type hint import
from typing import Tuple
