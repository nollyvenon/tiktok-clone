"""
Admin dashboard API routes - platform stats, user management, audit log
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import require_admin
from app.models import User
from app.services.admin import AdminService
from app.schemas import (
    AdminStatsResponse,
    AdminUserSummary,
    AdminUserListResponse,
    AdminAuditLogEntry,
    AdminAuditLogResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    responses={403: {"model": ErrorResponse, "description": "Admin access required"}},
)
async def get_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform-wide overview stats"""
    stats = await AdminService.get_stats(db)
    return AdminStatsResponse(**stats)


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    responses={403: {"model": ErrorResponse, "description": "Admin access required"}},
)
async def get_users(
    search: Optional[str] = Query(None, description="Search by username or email"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List/search users for management"""
    users, total = await AdminService.get_users(db, search=search, limit=limit, offset=offset)
    return AdminUserListResponse(
        users=[AdminUserSummary.from_orm(u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/users/{user_id}/suspend",
    response_model=AdminUserSummary,
    responses={
        400: {"model": ErrorResponse, "description": "User not found"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
async def suspend_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Directly suspend a user's account (no report required)"""
    try:
        user = await AdminService.set_user_active(db, user_id, False)
        return AdminUserSummary.from_orm(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/users/{user_id}/reactivate",
    response_model=AdminUserSummary,
    responses={
        400: {"model": ErrorResponse, "description": "User not found"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
async def reactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reactivate a suspended user's account"""
    try:
        user = await AdminService.set_user_active(db, user_id, True)
        return AdminUserSummary.from_orm(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/audit-log",
    response_model=AdminAuditLogResponse,
    responses={403: {"model": ErrorResponse, "description": "Admin access required"}},
)
async def get_audit_log(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get the moderation decision audit log, newest first"""
    entries, total = await AdminService.get_audit_log(db, limit=limit, offset=offset)
    return AdminAuditLogResponse(
        entries=[AdminAuditLogEntry(**e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )
