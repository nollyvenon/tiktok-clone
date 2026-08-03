"""
Monetization API routes - earnings ledger and payout requests
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user, require_admin
from app.models import User, PayoutStatus
from app.services.monetization import MonetizationService
from app.schemas import (
    EarningResponse, EarningsSummaryResponse,
    PayoutRequest, PayoutResponse, PayoutListResponse, PayoutDecisionRequest,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monetization", tags=["Monetization"])


@router.get("/summary", response_model=EarningsSummaryResponse)
async def get_earnings_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Your earnings ledger: total earned, paid out, pending, and available balance"""
    summary = await MonetizationService.get_earnings_summary(db, current_user.id)
    return EarningsSummaryResponse(
        total_earned=summary["total_earned"],
        total_paid_out=summary["total_paid_out"],
        pending_payout_total=summary["pending_payout_total"],
        available_balance=summary["available_balance"],
        earnings=[EarningResponse.model_validate(e) for e in summary["earnings"]],
    )


@router.post(
    "/payouts",
    response_model=PayoutResponse,
    responses={400: {"model": ErrorResponse, "description": "Amount exceeds available balance"}},
)
async def request_payout(
    request: PayoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request a payout against your available balance"""
    try:
        payout = await MonetizationService.request_payout(db, current_user.id, request.amount)
        return PayoutResponse.model_validate(payout)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/payouts/me", response_model=list[PayoutResponse])
async def list_my_payouts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Your own payout requests"""
    payouts = await MonetizationService.list_my_payouts(db, current_user.id)
    return [PayoutResponse.model_validate(p) for p in payouts]


@router.get(
    "/admin/payouts",
    response_model=PayoutListResponse,
    responses={403: {"model": ErrorResponse, "description": "Admin access required"}},
)
async def list_payouts(
    status_filter: Optional[PayoutStatus] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list/filter all payout requests"""
    payouts, total = await MonetizationService.list_payouts(db, status_filter=status_filter, limit=limit, offset=offset)
    return PayoutListResponse(
        payouts=[PayoutResponse.model_validate(p) for p in payouts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/admin/payouts/{payout_id}/decide",
    response_model=PayoutResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Payout not found or already decided"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
async def decide_payout(
    payout_id: UUID,
    request: PayoutDecisionRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: mark a payout completed or cancelled"""
    try:
        payout = await MonetizationService.decide_payout(
            db, payout_id, current_user.id, request.status, request.notes
        )
        return PayoutResponse.model_validate(payout)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
