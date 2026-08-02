"""
Direct messaging service - 1-on-1 conversations and messages.

No WebSocket/real-time transport exists yet anywhere in this codebase, so
this is REST-only (poll GET /messages/conversations/{id}/messages for new
messages), matching the pattern already used for notifications before any
push-delivery infrastructure was added.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Message, User
from app.services.profiles import ProfileService

logger = logging.getLogger(__name__)


class MessageService:
    """Service for conversations and messages"""

    @staticmethod
    def _ordered_pair(user_a: UUID, user_b: UUID) -> Tuple[UUID, UUID]:
        """Conversation.user1_id/user2_id are stored in a canonical order
        so the same pair always maps to the same row regardless of who
        started the conversation."""
        return (user_a, user_b) if str(user_a) < str(user_b) else (user_b, user_a)

    @staticmethod
    async def get_or_create_conversation(
        db: AsyncSession, user_id: UUID, other_user_id: UUID
    ) -> Conversation:
        """
        Get the existing 1-on-1 conversation between two users, or create
        one if it doesn't exist yet.

        Raises:
            ValueError: On self-conversation or if either user has blocked
                the other.
        """
        if user_id == other_user_id:
            raise ValueError("Cannot message yourself")

        other_user = await ProfileService.get_user_profile(db, other_user_id)
        if not other_user:
            raise ValueError("User not found")

        if await ProfileService.is_blocked(
            db, other_user_id, user_id
        ) or await ProfileService.is_blocked(db, user_id, other_user_id):
            raise ValueError("Cannot message this user")

        user1_id, user2_id = MessageService._ordered_pair(user_id, other_user_id)

        result = await db.execute(
            select(Conversation).where(
                and_(Conversation.user1_id == user1_id, Conversation.user2_id == user2_id)
            )
        )
        conversation = result.scalar()
        if conversation:
            return conversation

        conversation = Conversation(user1_id=user1_id, user2_id=user2_id)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def get_conversation(db: AsyncSession, conversation_id: UUID) -> Optional[Conversation]:
        return await db.get(Conversation, conversation_id)

    @staticmethod
    def get_other_user_id(conversation: Conversation, user_id: UUID) -> UUID:
        return conversation.user2_id if conversation.user1_id == user_id else conversation.user1_id

    @staticmethod
    def is_participant(conversation: Conversation, user_id: UUID) -> bool:
        return user_id in (conversation.user1_id, conversation.user2_id)

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Conversation], int]:
        """Get a user's conversations, most recently active first"""
        filters = or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)

        count_result = await db.execute(select(func.count()).select_from(Conversation).where(filters))
        total = count_result.scalar() or 0

        result = await db.execute(
            select(Conversation)
            .where(filters)
            .order_by(desc(Conversation.last_message_at))
            .offset(offset)
            .limit(limit)
        )
        conversations = result.scalars().all()
        return conversations, total

    @staticmethod
    async def get_last_message(db: AsyncSession, conversation_id: UUID) -> Optional[Message]:
        result = await db.execute(
            select(Message)
            .where(and_(Message.conversation_id == conversation_id, Message.deleted_at.is_(None)))
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        return result.scalar()

    @staticmethod
    async def get_unread_count(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> int:
        """Unread count of messages sent *to* user_id (not by them)"""
        result = await db.execute(
            select(func.count()).select_from(Message).where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.sender_id != user_id,
                    Message.is_read == False,
                    Message.deleted_at.is_(None),
                )
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def send_message(
        db: AsyncSession, conversation_id: UUID, sender_id: UUID, content: str
    ) -> Message:
        """
        Send a message in a conversation.

        Raises:
            ValueError: If the conversation doesn't exist, the sender
                isn't a participant, or either party has blocked the
                other (blocking after a conversation started must still
                stop new messages).
        """
        conversation = await MessageService.get_conversation(db, conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")
        if not MessageService.is_participant(conversation, sender_id):
            raise ValueError("Not a participant in this conversation")

        other_user_id = MessageService.get_other_user_id(conversation, sender_id)
        if await ProfileService.is_blocked(
            db, other_user_id, sender_id
        ) or await ProfileService.is_blocked(db, sender_id, other_user_id):
            raise ValueError("Cannot message this user")

        message = Message(conversation_id=conversation_id, sender_id=sender_id, content=content)
        db.add(message)
        conversation.last_message_at = datetime.utcnow()

        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_messages(
        db: AsyncSession, conversation_id: UUID, limit: int = 30, offset: int = 0
    ) -> Tuple[List[Message], int]:
        """Get messages in a conversation, oldest first (chat order)"""
        filters = and_(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))

        count_result = await db.execute(select(func.count()).select_from(Message).where(filters))
        total = count_result.scalar() or 0

        result = await db.execute(
            select(Message).where(filters).order_by(desc(Message.created_at)).offset(offset).limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return messages, total

    @staticmethod
    async def mark_conversation_read(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> int:
        """Mark all messages sent *to* user_id in this conversation as read.
        Returns the number of messages updated."""
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.sender_id != user_id,
                    Message.is_read == False,
                    Message.deleted_at.is_(None),
                )
            )
        )
        messages = result.scalars().all()
        now = datetime.utcnow()
        for message in messages:
            message.is_read = True
            message.read_at = now

        if messages:
            await db.commit()
        return len(messages)
