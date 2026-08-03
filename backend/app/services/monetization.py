"""
Monetization service - earnings ledger and payout requests.

Earning rows are created automatically elsewhere (CreatorFundService on
fund approval, ShopService on order fulfillment) - this service reads
that ledger and manages payout requests against it. No real payment
processor exists anywhere in this app: a 'completed' payout means an
admin marked it paid through whatever real-world process is used
outside this app, not that this app moved any money.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Earning, Payout, PayoutStatus

logger = logging.getLogger(__name__)


class MonetizationService:
    """Service for the earnings ledger and payout requests"""

    @staticmethod
    async def _total_earned(db: AsyncSession, user_id: UUID) -> int:
        result = await db.execute(
            select(func.coalesce(func.sum(Earning.amount), 0)).where(Earning.user_id == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def _total_by_payout_status(db: AsyncSession, user_id: UUID, status: PayoutStatus) -> int:
        result = await db.execute(
            select(func.coalesce(func.sum(Payout.amount), 0)).where(
                and_(Payout.user_id == user_id, Payout.status == status)
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def get_earnings_summary(db: AsyncSession, user_id: UUID) -> dict:
        total_earned = await MonetizationService._total_earned(db, user_id)
        total_paid_out = await MonetizationService._total_by_payout_status(db, user_id, PayoutStatus.COMPLETED)
        pending_payout_total = await MonetizationService._total_by_payout_status(db, user_id, PayoutStatus.PENDING)

        result = await db.execute(
            select(Earning).where(Earning.user_id == user_id).order_by(desc(Earning.created_at))
        )
        earnings = list(result.scalars().all())

        return {
            "total_earned": total_earned,
            "total_paid_out": total_paid_out,
            "pending_payout_total": pending_payout_total,
            "available_balance": total_earned - total_paid_out - pending_payout_total,
            "earnings": earnings,
        }

    @staticmethod
    async def request_payout(db: AsyncSession, user_id: UUID, amount: int) -> Payout:
        summary = await MonetizationService.get_earnings_summary(db, user_id)
        if amount > summary["available_balance"]:
            raise ValueError("Requested amount exceeds your available balance")

        payout = Payout(user_id=user_id, amount=amount)
        db.add(payout)
        await db.commit()
        await db.refresh(payout)
        logger.info(f"Payout {payout.id} requested by {user_id} for {amount} cents")
        return payout

    @staticmethod
    async def list_my_payouts(db: AsyncSession, user_id: UUID) -> List[Payout]:
        result = await db.execute(
            select(Payout).where(Payout.user_id == user_id).order_by(desc(Payout.requested_at))
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_payouts(
        db: AsyncSession,
        status_filter: Optional[PayoutStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Payout], int]:
        query = select(Payout)
        count_query = select(func.count()).select_from(Payout)
        if status_filter:
            query = query.where(Payout.status == status_filter)
            count_query = count_query.where(Payout.status == status_filter)

        total = (await db.execute(count_query)).scalar() or 0
        result = await db.execute(query.order_by(desc(Payout.requested_at)).offset(offset).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def decide_payout(
        db: AsyncSession, payout_id: UUID, admin_id: UUID, decision: PayoutStatus, notes: Optional[str],
    ) -> Payout:
        payout = await db.get(Payout, payout_id)
        if not payout:
            raise ValueError("Payout not found")
        if payout.status != PayoutStatus.PENDING:
            raise ValueError("Payout has already been decided")

        payout.status = decision
        payout.notes = notes
        payout.decided_by = admin_id
        payout.decided_at = datetime.utcnow()
        await db.commit()
        await db.refresh(payout)
        logger.info(f"Admin {admin_id} {decision.value} payout {payout_id}")
        return payout
