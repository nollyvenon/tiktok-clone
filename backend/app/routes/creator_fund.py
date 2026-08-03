"""
Creator Fund API routes - browse programs, apply, and (admin) review applications
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user, require_admin
from app.models import User, ApplicationStatus
from app.services.creator_fund import CreatorFundService
from app.schemas import (
    FundingProgramCreate,
    FundingProgramResponse,
    FundingProgramListResponse,
    CreatorApplicationResponse,
    CreatorApplicationListResponse,
    ApplicationDecisionRequest,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creator-fund", tags=["Creator Fund"])


@router.get("/programs", response_model=FundingProgramListResponse)
async def list_programs(db: AsyncSession = Depends(get_db)):
    """List active funding programs creators can apply to"""
    programs = await CreatorFundService.list_active_programs(db)
    return FundingProgramListResponse(
        programs=[FundingProgramResponse.from_orm(p) for p in programs]
    )


@router.post(
    "/programs",
    response_model=FundingProgramResponse,
    responses={403: {"model": ErrorResponse, "description": "Admin access required"}},
)
async def create_program(
    request: FundingProgramCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: create a new funding program"""
    program = await CreatorFundService.create_program(db, request.model_dump())
    return FundingProgramResponse.from_orm(program)


@router.post(
    "/programs/{program_id}/apply",
    response_model=CreatorApplicationResponse,
    responses={400: {"model": ErrorResponse, "description": "Program inactive or already applied"}},
)
async def apply_to_program(
    program_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply to a funding program with your current creator stats"""
    try:
        application = await CreatorFundService.apply_to_program(db, current_user.id, program_id)
        return CreatorApplicationResponse.from_orm(application)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me/applications", response_model=list[CreatorApplicationResponse])
async def list_my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Your own fund applications and their status"""
    applications = await CreatorFundService.list_my_applications(db, current_user.id)
    return [CreatorApplicationResponse.from_orm(a) for a in applications]


@router.get(
    "/admin/applications",
    response_model=CreatorApplicationListResponse,
    responses={403: {"model": ErrorResponse, "description": "Admin access required"}},
)
async def list_applications(
    status_filter: Optional[ApplicationStatus] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list/filter all fund applications"""
    applications, total = await CreatorFundService.list_applications(
        db, status_filter=status_filter, limit=limit, offset=offset
    )
    return CreatorApplicationListResponse(
        applications=[CreatorApplicationResponse.from_orm(a) for a in applications],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/admin/applications/{application_id}/decide",
    response_model=CreatorApplicationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Application not found or already decided"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
async def decide_application(
    application_id: UUID,
    request: ApplicationDecisionRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: approve or reject a fund application"""
    try:
        application = await CreatorFundService.decide_application(
            db, application_id, current_user.id, request.status, request.decision_reason
        )
        return CreatorApplicationResponse.from_orm(application)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
