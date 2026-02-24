"""User management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from alter.api.service import AlterService
from alter.api.deps import get_service
from alter.api.models.user import (
    UserInitRequest, UserInitResponse, PurposeUpdateRequest,
    PurposeResponse, UserStatusResponse,
    ProfileUpdateRequest, ImportRequest, ImportResponse,
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


@router.put("/users/{user_id}/profile")
def update_profile(user_id: str, body: ProfileUpdateRequest,
                   service: AlterService = Depends(get_service)):
    """Update personality traits, strengths, and growth areas."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.update_profile(
        user_id,
        personality_traits=body.personality_traits,
        strengths=body.strengths,
        growth_areas=body.growth_areas,
    )


@router.post("/users/{user_id}/import", response_model=ImportResponse)
def import_context(user_id: str, body: ImportRequest,
                   service: AlterService = Depends(get_service)):
    """Import context from external sources (ChatGPT, Claude, Gemini, plain text)."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.import_context(user_id, body.source, body.content)


@router.get("/users/{user_id}/memories")
def get_memories(user_id: str, service: AlterService = Depends(get_service)):
    """Get parsed memories from imported context."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    memories = service.get_parsed_memories(user_id)
    return {"memories": memories, "total": len(memories)}
