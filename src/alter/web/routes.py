"""Web UI routes - serves HTML pages."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from alter.api.service import AlterService
from alter.api.deps import get_service

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

DEFAULT_USER = "default"


def _get_user_id(request: Request) -> str:
    """Get user_id from cookie or default."""
    return request.cookies.get("alter_user_id", DEFAULT_USER)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, service: AlterService = Depends(get_service)):
    """Main dashboard page."""
    user_id = _get_user_id(request)

    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)

    status = service.get_status(user_id)
    goals_data = service.list_goals(user_id, status="active")

    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "user_id": user_id,
        "status": status,
        "goals": goals_data["goals"],
        "page": "dashboard"
    })


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request):
    """First-time setup page."""
    return templates.TemplateResponse("pages/init.html", {
        "request": request,
        "page": "setup"
    })


@router.post("/setup")
def setup_submit(request: Request, service: AlterService = Depends(get_service)):
    """Handle setup form submission."""
    import asyncio
    # We need to read form data synchronously
    return RedirectResponse(url="/", status_code=302)


@router.get("/goals", response_class=HTMLResponse)
def goals_page(request: Request, service: AlterService = Depends(get_service)):
    """Goals management page."""
    user_id = _get_user_id(request)

    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)

    goals_data = service.list_goals(user_id)

    return templates.TemplateResponse("pages/goals.html", {
        "request": request,
        "user_id": user_id,
        "goals": goals_data["goals"],
        "total": goals_data["total"],
        "page": "goals"
    })


@router.get("/constitution", response_class=HTMLResponse)
def constitution_page(request: Request, service: AlterService = Depends(get_service)):
    """Constitution viewer page."""
    constitution = service.get_constitution()

    return templates.TemplateResponse("pages/constitution.html", {
        "request": request,
        "constitution": constitution,
        "page": "constitution"
    })


@router.get("/plan", response_class=HTMLResponse)
def plan_page(request: Request, service: AlterService = Depends(get_service)):
    """Daily planning page."""
    user_id = _get_user_id(request)

    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)

    status = service.get_status(user_id)

    return templates.TemplateResponse("pages/daily_plan.html", {
        "request": request,
        "user_id": user_id,
        "status": status,
        "page": "plan"
    })


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, service: AlterService = Depends(get_service)):
    """User settings page."""
    user_id = _get_user_id(request)

    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)

    status = service.get_status(user_id)

    return templates.TemplateResponse("pages/settings.html", {
        "request": request,
        "user_id": user_id,
        "status": status,
        "page": "settings"
    })


@router.get("/thoughts", response_class=HTMLResponse)
def thoughts_page(request: Request):
    """Consciousness thought stream page."""
    user_id = _get_user_id(request)
    adapter = getattr(request.app.state, "consciousness", None)

    consciousness_active = adapter is not None and adapter.is_running
    status = adapter.get_status() if adapter else {}
    activity = adapter.get_activity(limit=50) if adapter else []
    notifications = (
        adapter.consciousness_state.get_pending_notifications() if adapter else []
    )

    return templates.TemplateResponse("pages/thoughts.html", {
        "request": request,
        "user_id": user_id,
        "page": "thoughts",
        "consciousness_active": consciousness_active,
        "status": status,
        "activity": activity,
        "notifications": notifications,
    })


# HTMX Partials

@router.get("/partials/goal-list", response_class=HTMLResponse)
def goal_list_partial(request: Request, service: AlterService = Depends(get_service)):
    """HTMX partial: goal list."""
    user_id = _get_user_id(request)
    goals_data = service.list_goals(user_id)

    return templates.TemplateResponse("partials/goal_list.html", {
        "request": request,
        "user_id": user_id,
        "goals": goals_data["goals"]
    })


@router.get("/partials/goal-form", response_class=HTMLResponse)
def goal_form_partial(request: Request):
    """HTMX partial: goal add form."""
    user_id = _get_user_id(request)
    return templates.TemplateResponse("partials/goal_form.html", {
        "request": request,
        "user_id": user_id
    })


@router.get("/partials/status-card", response_class=HTMLResponse)
def status_card_partial(request: Request, service: AlterService = Depends(get_service)):
    """HTMX partial: status card."""
    user_id = _get_user_id(request)
    status = service.get_status(user_id)

    return templates.TemplateResponse("partials/status_card.html", {
        "request": request,
        "status": status
    })


@router.get("/partials/thought-stream", response_class=HTMLResponse)
def thought_stream_partial(request: Request):
    """HTMX partial: live thought stream updates."""
    adapter = getattr(request.app.state, "consciousness", None)
    activity = adapter.get_activity(limit=20) if adapter else []
    notifications = (
        adapter.consciousness_state.get_pending_notifications() if adapter else []
    )

    return templates.TemplateResponse("partials/thought_stream.html", {
        "request": request,
        "activity": activity,
        "notifications": notifications,
    })
