"""Constitution endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from alter.api.service import AlterService
from alter.api.deps import get_service

router = APIRouter()


class PrincipleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[List[str]] = None
    weight: Optional[int] = Field(None, ge=1, le=10)


@router.get("/constitution")
def get_constitution(service: AlterService = Depends(get_service)):
    """Get the full constitution."""
    return service.get_constitution()


@router.get("/constitution/principles")
def get_principles(service: AlterService = Depends(get_service)):
    """Get constitution principles."""
    data = service.get_constitution()
    return {"principles": data["principles"]}


@router.get("/constitution/domains")
def get_domains(service: AlterService = Depends(get_service)):
    """Get life domains."""
    data = service.get_constitution()
    return {"domains": data["domains"]}


@router.put("/constitution/principles/{principle_id}")
def update_principle(principle_id: str, body: PrincipleUpdateRequest,
                     service: AlterService = Depends(get_service)):
    """Update a constitution principle."""
    updates = body.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        return service.update_principle(principle_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
