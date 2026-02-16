"""Constitution endpoints."""

from fastapi import APIRouter, Depends
from alter.api.service import AlterService
from alter.api.deps import get_service

router = APIRouter()


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
