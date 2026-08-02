"""
Direct messaging API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User, NotificationType
from app.services.messages import MessageService
from app.services.profiles import ProfileService
from app.services.notifications import NotificationService
from app.schemas import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ConversationResponse,
    ConversationListResponse,
    UserPublicProfile,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["Messages"])


async def _build_conversation_response(db: AsyncSession, conversation, current_user_id: UUID) -> ConversationResponse:
    other_user_id = MessageService.get_other_user_id(conversation, current_user_id)
    other_user = await ProfileService.get_user_profile(db, other_user_id)
    last_message = await MessageService.get_last_message(db, conversation.id)
    unread_count = await MessageService.get_unread_count(db, conversation.id, current_user_id)

    return ConversationResponse(
        id=conversation.id,
        other_user=UserPublicProfile.from_orm(other_user),
        last_message=MessageResponse.from_orm(last_message) if last_message else None,
        unread_count=unread_count,
        updated_at=conversation.last_message_at,
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse, "description": "Cannot start conversation"}},
)
async def start_conversation(
    recipient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the existing conversation with recipient_id, or create one"""
    try:
        conversation = await MessageService.get_or_create_conversation(db, current_user.id, recipient_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return await _build_conversation_response(db, conversation, current_user.id)


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
)
async def get_conversations(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's conversations, most recently active first"""
    conversations, total = await MessageService.get_user_conversations(
        db, current_user.id, limit=limit, offset=offset
    )
    return ConversationListResponse(
        conversations=[
            await _build_conversation_response(db, c, current_user.id) for c in conversations
        ],
        total=total,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Not a participant"},
        404: {"model": ErrorResponse, "description": "Conversation not found"},
    },
)
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages in a conversation, oldest first"""
    conversation = await MessageService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if not MessageService.is_participant(conversation, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant in this conversation")

    messages, total = await MessageService.get_messages(db, conversation_id, limit=limit, offset=offset)
    return MessageListResponse(
        messages=[MessageResponse.from_orm(m) for m in messages],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Cannot send message"},
        403: {"model": ErrorResponse, "description": "Not a participant"},
    },
)
async def send_message(
    conversation_id: UUID,
    request: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in an existing conversation"""
    try:
        message = await MessageService.send_message(
            db, conversation_id, current_user.id, request.content
        )
    except ValueError as e:
        detail = str(e)
        status_code = (
            status.HTTP_403_FORBIDDEN
            if detail == "Not a participant in this conversation"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=detail)

    conversation = await MessageService.get_conversation(db, conversation_id)
    recipient_id = MessageService.get_other_user_id(conversation, current_user.id)
    await NotificationService.send_notification(
        db,
        user_id=recipient_id,
        notification_type=NotificationType.MESSAGE,
        title=f"New message from {current_user.username}",
        message=request.content[:200],
        actor_id=current_user.id,
    )

    return MessageResponse.from_orm(message)


@router.put(
    "/conversations/{conversation_id}/read",
    responses={403: {"model": ErrorResponse, "description": "Not a participant"}},
)
async def mark_conversation_read(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all messages sent to the current user in this conversation as read"""
    conversation = await MessageService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if not MessageService.is_participant(conversation, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant in this conversation")

    count = await MessageService.mark_conversation_read(db, conversation_id, current_user.id)
    return {"count": count}
