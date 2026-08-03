"""
Collaborations API routes - team content creation with an agreed revenue split
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User
from app.services.collaborations import CollaborationService
from app.schemas import (
    CollaborationCreate,
    CollaborationResponse,
    CollaborationRespondRequest,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collaborations", tags=["Collaborations"])


@router.post(
    "",
    response_model=CollaborationResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid video or collaborator list"}},
)
async def create_collaboration(
    request: CollaborationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a collaboration on one of your own videos"""
    try:
        collaboration = await CollaborationService.create_collaboration(
            db,
            current_user.id,
            request.video_id,
            request.title,
            [c.model_dump() for c in request.collaborators],
        )
        return CollaborationResponse.model_validate(collaboration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=list[CollaborationResponse])
async def list_my_collaborations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List collaborations you initiated or were invited to"""
    collaborations = await CollaborationService.list_my_collaborations(db, current_user.id)
    return [CollaborationResponse.model_validate(c) for c in collaborations]


@router.get(
    "/{collaboration_id}",
    response_model=CollaborationResponse,
    responses={400: {"model": ErrorResponse, "description": "Not found or not a participant"}},
)
async def get_collaboration(
    collaboration_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View a collaboration you're part of"""
    try:
        collaboration = await CollaborationService.get_collaboration(db, collaboration_id, current_user.id)
        return CollaborationResponse.model_validate(collaboration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{collaboration_id}/respond",
    response_model=CollaborationResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid response"}},
)
async def respond_to_collaboration(
    collaboration_id: UUID,
    request: CollaborationRespondRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept or decline your invitation to a collaboration"""
    try:
        collaboration = await CollaborationService.respond(
            db, collaboration_id, current_user.id, request.accept
        )
        return CollaborationResponse.model_validate(collaboration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{collaboration_id}/cancel",
    response_model=CollaborationResponse,
    responses={400: {"model": ErrorResponse, "description": "Cannot cancel"}},
)
async def cancel_collaboration(
    collaboration_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a collaboration you initiated"""
    try:
        collaboration = await CollaborationService.cancel(db, collaboration_id, current_user.id)
        return CollaborationResponse.model_validate(collaboration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
