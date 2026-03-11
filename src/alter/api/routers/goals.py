"""Goal management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from alter.api.service import AlterService
from alter.api.deps import get_service
from alter.api.models.goals import GoalCreateRequest, GoalCompleteRequest, GoalUpdateRequest

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


@router.put("/users/{user_id}/goals/{goal_id}")
def update_goal(user_id: str, goal_id: str, body: GoalUpdateRequest,
                service: AlterService = Depends(get_service)):
    """Update a goal's fields."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    updates = body.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        return service.update_goal(user_id, goal_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{user_id}/goals/{goal_id}")
def delete_goal(user_id: str, goal_id: str,
                service: AlterService = Depends(get_service)):
    """Delete a goal entirely."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    try:
        return service.delete_goal(user_id, goal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


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


@router.post("/users/{user_id}/goals/{goal_id}/decompose")
async def decompose_goal(user_id: str, goal_id: str, request: Request,
                         service: AlterService = Depends(get_service)):
    """Break a goal into sub-goals using consciousness engine."""
    if not service.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    # Find the goal
    goals_data = service.list_goals(user_id)
    goal = None
    for g in goals_data.get("goals", []):
        if g["id"] == goal_id or g["id"].startswith(goal_id):
            goal = g
            break
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")

    # Use consciousness engine if available
    adapter = getattr(request.app.state, "consciousness", None)
    if not adapter:
        raise HTTPException(status_code=503, detail="Consciousness engine not running")

    context = (
        f"Break down this goal into 2-4 concrete sub-goals: "
        f"\"{goal['description']}\" (domain: {goal['domain']}, "
        f"horizon: {goal['time_horizon']}). "
        f"Suggest specific, actionable sub-goals with shorter time horizons."
    )
    result = await adapter.trigger_tick("goal_analysis", context=context)

    # Count sub-goals created from goal_suggestions
    sub_goals_created = 0
    if result and result.goal_suggestions:
        for gs in result.goal_suggestions:
            try:
                service.add_goal(
                    user_id, gs.description, gs.domain or goal["domain"],
                    gs.time_horizon or "month", parent_goal_id=goal_id,
                )
                sub_goals_created += 1
            except Exception:
                pass

    return {"sub_goals_created": sub_goals_created, "goal_id": goal_id}
