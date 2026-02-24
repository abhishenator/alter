"""Habits API — Server-side daily habit tracking."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter(prefix="/users/{user_id}")


def _get_adapter(request: Request):
    adapter = getattr(request.app.state, "consciousness", None)
    if adapter is None:
        raise HTTPException(status_code=503, detail="Consciousness engine not running.")
    return adapter


# ------------------------------------------------------------------
# Habits
# ------------------------------------------------------------------


class HabitCreate(BaseModel):
    name: str
    domain: str = "general"
    linked_goal_id: Optional[str] = None


@router.get("/habits")
def list_habits(request: Request, user_id: str):
    """List all active habits with today's status."""
    adapter = _get_adapter(request)
    from datetime import datetime
    today = datetime.now().date().isoformat()
    habits = adapter.user_model.get_active_habits()
    return {
        "habits": [
            {
                **h.to_dict(),
                "done_today": h.completions.get(today, False),
            }
            for h in habits
        ],
        "today": today,
    }


@router.post("/habits")
def create_habit(request: Request, user_id: str, body: HabitCreate):
    """Create a new habit."""
    adapter = _get_adapter(request)
    from alter.core.user_model import Habit
    habit = Habit(
        id=str(uuid.uuid4())[:8],
        name=body.name,
        domain=body.domain,
        linked_goal_id=body.linked_goal_id,
    )
    adapter.user_model.add_habit(habit)
    adapter.user_model.save()
    return habit.to_dict()


@router.post("/habits/{habit_id}/toggle")
def toggle_habit(request: Request, user_id: str, habit_id: str):
    """Toggle today's completion for a habit."""
    adapter = _get_adapter(request)
    habit = adapter.user_model.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    done = habit.toggle()
    adapter.user_model.save()
    return {"habit_id": habit_id, "done": done, "streak": habit.streak}


@router.delete("/habits/{habit_id}")
def delete_habit(request: Request, user_id: str, habit_id: str):
    """Deactivate a habit."""
    adapter = _get_adapter(request)
    found = adapter.user_model.remove_habit(habit_id)
    if not found:
        raise HTTPException(status_code=404, detail="Habit not found")
    adapter.user_model.save()
    return {"status": "removed", "habit_id": habit_id}


# ------------------------------------------------------------------
# Pinned Notes
# ------------------------------------------------------------------


@router.get("/pinned")
def list_pinned_notes(request: Request, user_id: str):
    """List active pinned notes."""
    adapter = _get_adapter(request)
    notes = adapter.user_model.get_active_pinned_notes()
    return {"notes": [n.to_dict() for n in notes]}


@router.delete("/pinned/{note_id}")
def archive_pinned_note(request: Request, user_id: str, note_id: str):
    """Archive a pinned note."""
    adapter = _get_adapter(request)
    found = adapter.user_model.archive_pinned_note(note_id)
    if not found:
        raise HTTPException(status_code=404, detail="Note not found")
    adapter.user_model.save()
    return {"status": "archived", "note_id": note_id}
