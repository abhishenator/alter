"""Inbox API — Staged consciousness output for user curation."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/inbox")


def _get_adapter(request: Request):
    adapter = getattr(request.app.state, "consciousness", None)
    if adapter is None:
        raise HTTPException(status_code=503, detail="Consciousness engine not running.")
    return adapter


@router.get("")
def list_inbox(request: Request):
    """Get all pending inbox items."""
    adapter = _get_adapter(request)
    items = adapter.consciousness_state.get_pending_inbox()
    return {
        "items": [i.to_dict() for i in items],
        "total": len(items),
    }


@router.post("/{item_id}/pin")
def pin_inbox_item(request: Request, item_id: str):
    """Pin an inbox item as a note."""
    adapter = _get_adapter(request)
    item = adapter.consciousness_state.resolve_inbox_item(item_id, "pinned", "pinned")
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or already resolved")

    # Create a PinnedNote on the user model
    from alter.core.user_model import PinnedNote
    import uuid
    note = PinnedNote(
        id=str(uuid.uuid4())[:8],
        text=item.body or item.title,
        domain=item.domain,
        source_inbox_id=item.id,
    )
    adapter.user_model.add_pinned_note(note)
    adapter.user_model.save()
    adapter.consciousness_state.save()
    return {"status": "pinned", "note": note.to_dict()}


@router.post("/{item_id}/dismiss")
def dismiss_inbox_item(request: Request, item_id: str):
    """Dismiss an inbox item."""
    adapter = _get_adapter(request)
    item = adapter.consciousness_state.resolve_inbox_item(item_id, "dismissed", "dismissed")
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or already resolved")
    adapter.consciousness_state.save()
    return {"status": "dismissed", "item_id": item_id}


class ConvertRequest(BaseModel):
    to: str  # "goal" | "habit"
    description: Optional[str] = None
    domain: Optional[str] = None
    time_horizon: Optional[str] = None


@router.post("/{item_id}/convert")
def convert_inbox_item(request: Request, item_id: str, body: ConvertRequest):
    """Convert an inbox item to a goal or habit."""
    adapter = _get_adapter(request)
    state = adapter.consciousness_state
    item = state.get_inbox_item(item_id)
    if not item or item.status != "pending":
        raise HTTPException(status_code=404, detail="Item not found or already resolved")

    import uuid as _uuid

    if body.to == "goal":
        from alter.core.user_model import Goal
        goal = Goal(
            id=str(_uuid.uuid4()),
            domain=body.domain or item.domain or "general",
            description=body.description or item.suggested_goal.get("description", item.title) if item.suggested_goal else item.title,
            time_horizon=body.time_horizon or (item.suggested_goal.get("time_horizon", "quarter") if item.suggested_goal else "quarter"),
        )
        adapter.user_model.add_goal(goal)
        state.resolve_inbox_item(item_id, "converted", "converted_to_goal")
        adapter.user_model.save()
        state.save()
        return {"status": "converted", "to": "goal", "goal_id": goal.id}

    elif body.to == "habit":
        from alter.core.user_model import Habit
        habit = Habit(
            id=str(_uuid.uuid4())[:8],
            name=body.description or item.title,
            domain=body.domain or item.domain or "general",
            source_inbox_id=item.id,
        )
        adapter.user_model.add_habit(habit)
        state.resolve_inbox_item(item_id, "converted", "converted_to_habit")
        adapter.user_model.save()
        state.save()
        return {"status": "converted", "to": "habit", "habit": habit.to_dict()}

    else:
        raise HTTPException(status_code=400, detail="'to' must be 'goal' or 'habit'")
