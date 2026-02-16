"""User management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from alter.api.service import AlterService
from alter.api.deps import get_service
from alter.api.models.user import (
    UserInitRequest, UserInitResponse, PurposeUpdateRequest,
    PurposeResponse, UserStatusResponse
)

router = APIRouter()


@router.post("/users/init", response_model=UserInitResponse)
def init_user(body: UserInitRequest, service: AlterService = Depends(get_service)):
    """Initialize a new ALTER user."""
    if service.user_exists(body.user_id):
        raise HTTPException(status_code=409, detail=f"User '{body.user_id}' already exists")
    result = service.init_user(body.user_id, body.purpose)
    return result


@router.get("/users/{user_id}/status")
def get_status(user_id: str, service: AlterService = Depends(get_service)):
    """Get full user status overview."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.get_status(user_id)


@router.put("/users/{user_id}/purpose")
def update_purpose(user_id: str, body: PurposeUpdateRequest,
                   service: AlterService = Depends(get_service)):
    """Set or update life purpose."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.set_purpose(user_id, body.purpose, body.notes)


@router.get("/users/{user_id}/purpose")
def get_purpose(user_id: str, service: AlterService = Depends(get_service)):
    """Get current purpose and history."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.get_purpose(user_id)
