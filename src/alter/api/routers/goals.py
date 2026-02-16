"""Goal management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from alter.api.service import AlterService
from alter.api.deps import get_service
from alter.api.models.goals import GoalCreateRequest, GoalCompleteRequest

router = APIRouter()


@router.get("/users/{user_id}/goals")
def list_goals(
    user_id: str,
    domain: Optional[str] = Query(None),
    horizon: Optional[str] = Query(None),
    status: Optional[str] = Query(None, alias="status"),
    service: AlterService = Depends(get_service)
):
    """List goals with optional filters."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.list_goals(user_id, domain=domain, horizon=horizon, status=status)


@router.post("/users/{user_id}/goals")
def create_goal(user_id: str, body: GoalCreateRequest,
                service: AlterService = Depends(get_service)):
    """Add a new goal."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return service.add_goal(
        user_id, body.description, body.domain,
        body.time_horizon, body.parent_goal_id
    )


@router.post("/users/{user_id}/goals/{goal_id}/complete")
def complete_goal(user_id: str, goal_id: str, body: GoalCompleteRequest,
                  service: AlterService = Depends(get_service)):
    """Mark a goal as completed."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    try:
        return service.complete_goal(user_id, goal_id, body.outcome, body.notes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
