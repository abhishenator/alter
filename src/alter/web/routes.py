"""Web UI routes — serves the 3-screen UI and HTMX partials."""

from datetime import datetime

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
    cookie_user = request.cookies.get("alter_user_id")
    if cookie_user:
        return cookie_user
    adapter = getattr(request.app.state, "consciousness", None)
    if adapter:
        return adapter.user_id
    return DEFAULT_USER


def _get_adapter(request: Request):
    return getattr(request.app.state, "consciousness", None)


def _consciousness_active(request: Request) -> bool:
    adapter = _get_adapter(request)
    return adapter is not None and adapter.is_running


# ─── Pages ───


@router.get("/", response_class=HTMLResponse)
def today_page(request: Request, service: AlterService = Depends(get_service)):
    """Today — daily cockpit."""
    user_id = _get_user_id(request)
    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)
    return templates.TemplateResponse("pages/today.html", {
        "request": request, "user_id": user_id, "page": "today",
        "consciousness_active": _consciousness_active(request),
    })


@router.get("/goals", response_class=HTMLResponse)
def goals_page(request: Request, service: AlterService = Depends(get_service)):
    """Goals — hierarchy, progress, analyses."""
    user_id = _get_user_id(request)
    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)
    status = service.get_status(user_id)
    return templates.TemplateResponse("pages/goals.html", {
        "request": request, "user_id": user_id, "page": "goals",
        "status": status,
        "consciousness_active": _consciousness_active(request),
    })


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, service: AlterService = Depends(get_service)):
    """Settings — identity, imports, thought loops."""
    user_id = _get_user_id(request)
    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)
    status = service.get_status(user_id)
    return templates.TemplateResponse("pages/settings.html", {
        "request": request, "user_id": user_id, "page": "settings",
        "status": status,
        "consciousness_active": _consciousness_active(request),
    })


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request):
    return templates.TemplateResponse("pages/init.html", {
        "request": request, "page": "setup"
    })


# ─── Today Partials ───


@router.get("/partials/today-narrative", response_class=HTMLResponse)
def today_narrative_partial(request: Request):
    adapter = _get_adapter(request)
    narrative = ""
    if adapter:
        narrative = adapter.consciousness_state.narrative or ""
    return templates.TemplateResponse("partials/today_narrative.html", {
        "request": request, "narrative": narrative,
    })


@router.get("/partials/inbox", response_class=HTMLResponse)
def inbox_partial(request: Request):
    adapter = _get_adapter(request)
    items = []
    goal_names = {}
    if adapter:
        items = [i.to_dict() for i in adapter.consciousness_state.get_pending_inbox()]
        # Build a lookup of goal id → description for attribution display
        for g in adapter.user_model.get_active_goals():
            goal_names[g.id] = g.description
    return templates.TemplateResponse("partials/inbox.html", {
        "request": request, "items": items, "goal_names": goal_names,
    })


@router.get("/partials/habits", response_class=HTMLResponse)
def habits_partial(request: Request):
    adapter = _get_adapter(request)
    habits = []
    today_label = datetime.now().strftime("%A, %b %d")
    if adapter:
        today = datetime.now().date().isoformat()
        for h in adapter.user_model.get_active_habits():
            habits.append({
                **h.to_dict(),
                "done_today": h.completions.get(today, False),
            })
    return templates.TemplateResponse("partials/habits.html", {
        "request": request, "habits": habits, "today_label": today_label,
    })


@router.get("/partials/pinned-notes", response_class=HTMLResponse)
def pinned_notes_partial(request: Request):
    adapter = _get_adapter(request)
    notes = []
    if adapter:
        notes = [n.to_dict() for n in adapter.user_model.get_active_pinned_notes()]
    return templates.TemplateResponse("partials/pinned_notes.html", {
        "request": request, "notes": notes,
    })


@router.get("/partials/today-goals", response_class=HTMLResponse)
def today_goals_partial(request: Request):
    adapter = _get_adapter(request)
    goals = []
    if adapter:
        for g in adapter.user_model.get_active_goals():
            goals.append({
                "id": g.id, "domain": g.domain, "description": g.description,
                "time_horizon": g.time_horizon,
            })
    return templates.TemplateResponse("partials/today_goals.html", {
        "request": request, "goals": goals,
    })


# ─── Goals Partials ───


@router.get("/partials/goal-tree", response_class=HTMLResponse)
def goal_tree_partial(request: Request, horizon: str = "", service: AlterService = Depends(get_service)):
    user_id = _get_user_id(request)
    goals_data = service.list_goals(user_id, status="active")
    goals = goals_data.get("goals", [])
    if horizon and horizon != "all":
        goals = [g for g in goals if g.get("time_horizon") == horizon]
    # Group by domain
    domains = {}
    for g in goals:
        d = g.get("domain", "general")
        domains.setdefault(d, []).append(g)
    return templates.TemplateResponse("partials/goal_tree.html", {
        "request": request, "user_id": user_id, "domains": domains, "goals": goals,
    })


@router.get("/partials/goal-graph", response_class=HTMLResponse)
def goal_graph_partial(request: Request, service: AlterService = Depends(get_service)):
    """Goal graph — goals layered by time horizon with attributed thoughts."""
    user_id = _get_user_id(request)
    adapter = _get_adapter(request)

    goals_data = service.list_goals(user_id, status="active")
    goals = goals_data.get("goals", [])

    # Build horizon layers (broad → narrow)
    horizon_order = ["life", "5_year", "1_year", "quarter", "month", "week", "day"]
    horizon_labels = {
        "life": "Life", "5_year": "5 Year", "1_year": "Year",
        "quarter": "Quarter", "month": "Month", "week": "Week", "day": "Day",
    }
    layers = []
    for h in horizon_order:
        h_goals = [g for g in goals if g.get("time_horizon") == h]
        if h_goals:
            layers.append({"key": h, "label": horizon_labels.get(h, h), "goals": h_goals})

    # Collect attributed stream items, habits, and notes per goal
    goal_children = {}  # goal_id → { "thoughts": [...], "habits": [...], "notes": [...] }
    if adapter:
        # Pending + recent resolved inbox items
        all_inbox = adapter.consciousness_state.inbox
        for item in all_inbox:
            gid = item.linked_goal_id
            if gid:
                goal_children.setdefault(gid, {"thoughts": [], "habits": [], "notes": []})
                goal_children[gid]["thoughts"].append({
                    "title": item.title[:50],
                    "type": item.item_type,
                    "status": item.status,
                })

        # Habits linked to goals
        for h in adapter.user_model.get_active_habits():
            if h.linked_goal_id:
                goal_children.setdefault(h.linked_goal_id, {"thoughts": [], "habits": [], "notes": []})
                goal_children[h.linked_goal_id]["habits"].append({"name": h.name, "streak": h.streak})

        # Pinned notes linked to goals
        for n in adapter.user_model.get_active_pinned_notes():
            if n.linked_goal_id:
                goal_children.setdefault(n.linked_goal_id, {"thoughts": [], "habits": [], "notes": []})
                goal_children[n.linked_goal_id]["notes"].append({"text": n.text[:50]})

    return templates.TemplateResponse("partials/goal_graph.html", {
        "request": request, "layers": layers, "goal_children": goal_children,
    })


@router.get("/partials/goal-analyses", response_class=HTMLResponse)
def goal_analyses_partial(request: Request):
    adapter = _get_adapter(request)
    goal_analyses = []
    if adapter:
        seen = set()
        for item in adapter.get_activity(limit=100):
            if not isinstance(item, dict):
                continue
            if item.get("event_type") == "goal_analysis":
                summary = item.get("summary", "")
                if summary not in seen:
                    seen.add(summary)
                    goal_analyses.append(item)
        goal_analyses = goal_analyses[:5]
    return templates.TemplateResponse("partials/goal_analyses_section.html", {
        "request": request, "goal_analyses": goal_analyses,
    })


@router.get("/partials/completed-goals", response_class=HTMLResponse)
def completed_goals_partial(request: Request, service: AlterService = Depends(get_service)):
    user_id = _get_user_id(request)
    goals_data = service.list_goals(user_id, status="completed")
    return templates.TemplateResponse("partials/completed_goals.html", {
        "request": request, "goals": goals_data.get("goals", []),
    })


# ─── Settings Partials ───


@router.get("/partials/profile-skills", response_class=HTMLResponse)
def profile_skills_partial(request: Request):
    adapter = _get_adapter(request)
    skills = []
    if adapter:
        for info in adapter.skill_registry.list_skills():
            skills.append({
                "name": info.name,
                "description": info.description,
                "domains": info.domains,
                "metrics": [m.name for m in info.metrics],
            })
    return templates.TemplateResponse("partials/profile_skills.html", {
        "request": request, "skills": skills,
    })


@router.get("/partials/profile-constitution", response_class=HTMLResponse)
def profile_constitution_partial(request: Request, service: AlterService = Depends(get_service)):
    constitution = service.get_constitution()
    return templates.TemplateResponse("partials/profile_constitution.html", {
        "request": request, "constitution": constitution,
    })


@router.get("/partials/profile-memories", response_class=HTMLResponse)
def profile_memories_partial(request: Request, service: AlterService = Depends(get_service)):
    user_id = _get_user_id(request)
    imports = service.get_imports(user_id)
    memories = service.get_parsed_memories(user_id)
    return templates.TemplateResponse("partials/profile_memories.html", {
        "request": request, "imports": imports, "memories": memories,
    })


# ─── Legacy partials still needed by old pages until fully cleaned ───


@router.get("/partials/stream-feed", response_class=HTMLResponse)
def stream_feed_partial(request: Request, domain: str = ""):
    adapter = _get_adapter(request)
    activity = []
    if adapter:
        activity = adapter.get_activity(limit=50)
    if domain:
        activity = [a for a in activity if domain in str(a)]
    return templates.TemplateResponse("partials/stream_feed.html", {
        "request": request, "activity": activity,
    })


@router.get("/partials/mirror-vitals", response_class=HTMLResponse)
def mirror_vitals_partial(request: Request, service: AlterService = Depends(get_service)):
    user_id = _get_user_id(request)
    today = datetime.now().date().isoformat()
    try:
        daily = service.get_daily_data(user_id, today)
    except Exception:
        daily = {}
    health = daily.get("health", {})
    emotions = daily.get("emotions", {})
    return templates.TemplateResponse("partials/mirror_vitals.html", {
        "request": request,
        "mood": emotions.get("mood"),
        "energy": emotions.get("energy"),
        "stress": emotions.get("stress"),
        "sleep": health.get("sleep_hours"),
        "exercise": health.get("exercise_minutes"),
    })


# ─── Redirects from old URLs ───


@router.get("/stream", response_class=HTMLResponse)
def stream_redirect(request: Request):
    return RedirectResponse(url="/", status_code=302)

@router.get("/direction", response_class=HTMLResponse)
def direction_redirect(request: Request):
    return RedirectResponse(url="/goals", status_code=302)

@router.get("/profile", response_class=HTMLResponse)
def profile_redirect(request: Request):
    return RedirectResponse(url="/settings", status_code=302)

@router.get("/world", response_class=HTMLResponse)
def world_redirect(request: Request):
    return RedirectResponse(url="/", status_code=302)

@router.get("/thoughts", response_class=HTMLResponse)
def thoughts_redirect(request: Request):
    return RedirectResponse(url="/", status_code=302)
