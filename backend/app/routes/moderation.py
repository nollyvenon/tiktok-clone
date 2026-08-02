"""
Moderation API routes - content reporting and admin review queue
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user, require_admin
from app.models import User, ReportedContentType, ReportStatus
from app.services.moderation import ModerationService
from app.schemas import (
    ContentReportCreate,
    ContentReportResponse,
    ContentReportListResponse,
    ModerationDecisionCreate,
    ModerationDecisionResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/moderation", tags=["Moderation"])


@router.post(
    "/reports",
    response_model=ContentReportResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse, "description": "Invalid report"}},
)
async def create_report(
    request: ContentReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a video, comment, or user"""
    try:
        report = await ModerationService.create_report(
            db,
            current_user.id,
            request.content_type,
            request.content_id,
            request.reason,
            request.description,
        )
        return ContentReportResponse.from_orm(report)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/reports/me",
    response_model=ContentReportListResponse,
)
async def get_my_reports(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get reports the current user has submitted"""
    reports, total = await ModerationService.get_user_reports(db, current_user.id, limit=limit, offset=offset)
    return ContentReportListResponse(
        reports=[ContentReportResponse.from_orm(r) for r in reports],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/reports",
    response_model=ContentReportListResponse,
    responses={403: {"model": ErrorResponse, "description": "Admin access required"}},
)
async def get_report_queue(
    status_filter: Optional[ReportStatus] = Query(None, alias="status"),
    content_type: Optional[ReportedContentType] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: get the report queue, oldest-pending first"""
    reports, total = await ModerationService.get_report_queue(
        db, status_filter=status_filter, content_type=content_type, limit=limit, offset=offset
    )
    return ContentReportListResponse(
        reports=[ContentReportResponse.from_orm(r) for r in reports],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/reports/{report_id}/decide",
    response_model=ModerationDecisionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Report not found or already decided"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
async def decide_report(
    report_id: UUID,
    request: ModerationDecisionCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: decide a report (dismiss, remove content, warn/suspend/ban the user)"""
    try:
        decision = await ModerationService.decide_report(
            db, report_id, current_user.id, request.action, request.notes
        )
        return ModerationDecisionResponse.from_orm(decision)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
