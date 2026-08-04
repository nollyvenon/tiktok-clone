"""
Live Streaming API routes - stream sessions, viewer presence, and chat
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User
from app.services.live_streaming import LiveStreamingService
from app.schemas import (
    LiveStreamStartRequest, LiveStreamResponse, LiveStreamListResponse,
    LiveChatMessageCreate, LiveChatMessageResponse, LiveChatMessageListResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/live", tags=["Live Streaming"])


@router.post(
    "/start",
    response_model=LiveStreamResponse,
    responses={400: {"model": ErrorResponse, "description": "Already have a stream in progress"}},
)
async def start_stream(
    request: LiveStreamStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new live stream session"""
    try:
        stream = await LiveStreamingService.start_stream(db, current_user.id, request.title)
        return LiveStreamResponse.model_validate(stream)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=LiveStreamListResponse)
async def list_live_streams(db: AsyncSession = Depends(get_db)):
    """Discover currently live streams, most viewers first"""
    streams = await LiveStreamingService.list_live_streams(db)
    return LiveStreamListResponse(streams=[LiveStreamResponse.model_validate(s) for s in streams])


@router.post(
    "/{stream_id}/end",
    response_model=LiveStreamResponse,
    responses={400: {"model": ErrorResponse, "description": "Not found, not yours, or already ended"}},
)
async def end_stream(
    stream_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """End your own live stream session"""
    try:
        stream = await LiveStreamingService.end_stream(db, current_user.id, stream_id)
        return LiveStreamResponse.model_validate(stream)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{stream_id}/join",
    response_model=LiveStreamResponse,
    responses={400: {"model": ErrorResponse, "description": "Stream not found or has ended"}},
)
async def join_stream(
    stream_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a live stream as a viewer"""
    try:
        stream = await LiveStreamingService.join_stream(db, current_user.id, stream_id)
        return LiveStreamResponse.model_validate(stream)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{stream_id}/leave",
    response_model=LiveStreamResponse,
    responses={400: {"model": ErrorResponse, "description": "Stream not found"}},
)
async def leave_stream(
    stream_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a live stream you're viewing"""
    try:
        stream = await LiveStreamingService.leave_stream(db, current_user.id, stream_id)
        return LiveStreamResponse.model_validate(stream)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{stream_id}/chat",
    response_model=LiveChatMessageResponse,
    responses={400: {"model": ErrorResponse, "description": "Stream not found or has ended"}},
)
async def post_chat_message(
    stream_id: UUID,
    request: LiveChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Post a chat message to a live stream"""
    try:
        message = await LiveStreamingService.post_chat_message(db, current_user.id, stream_id, request.content)
        return LiveChatMessageResponse(**message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{stream_id}/chat", response_model=LiveChatMessageListResponse)
async def list_chat_messages(
    stream_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List recent chat messages for a stream, oldest first"""
    messages = await LiveStreamingService.list_chat_messages(db, stream_id, limit)
    return LiveChatMessageListResponse(messages=[LiveChatMessageResponse(**m) for m in messages])


@router.get(
    "/{stream_id}",
    response_model=LiveStreamResponse,
    responses={400: {"model": ErrorResponse, "description": "Stream not found"}},
)
async def get_stream(
    stream_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """View a stream's current status and viewer count"""
    try:
        stream = await LiveStreamingService.get_stream(db, stream_id)
        return LiveStreamResponse.model_validate(stream)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
