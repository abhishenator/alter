"""Web UI routes — serves the 3-screen UI and HTMX partials."""

from datetime import datetime, timedelta

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


def _time_greeting() -> str:
    """Return a time-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    elif hour < 21:
        return "Good evening"
    return "Good night"


# ─── Pages ───


@router.get("/", response_class=HTMLResponse)
def today_page(
    request: Request,
    first: str = "",
    service: AlterService = Depends(get_service),
):
    """Today — daily cockpit."""
    user_id = _get_user_id(request)
    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)

    adapter = _get_adapter(request)
    today = datetime.now().date().isoformat()

    # Check if today's data has been logged
    today_logged = False
    today_data = {}
    if adapter:
        daily = adapter.user_model.get_daily_data(today) if hasattr(adapter.user_model, 'get_daily_data') else {}
        if daily:
            today_logged = True
            today_data = daily
    if not today_logged:
        try:
            daily = service.get_daily_data(user_id, today)
            if daily and any(daily.get(k) for k in ["health", "emotions", "calendar"]):
                today_logged = True
                today_data = daily
        except Exception:
            pass

    # Count active goals
    active_goal_count = 0
    if adapter:
        active_goal_count = len(adapter.user_model.get_active_goals())
    else:
        try:
            goals_data = service.list_goals(user_id, status="active")
            active_goal_count = goals_data.get("total", 0)
        except Exception:
            pass

    return templates.TemplateResponse("pages/today.html", {
        "request": request, "user_id": user_id, "page": "today",
        "consciousness_active": _consciousness_active(request),
        "today_logged": today_logged,
        "today_data": today_data,
        "active_goal_count": active_goal_count,
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


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, service: AlterService = Depends(get_service)):
    """Dashboard — staging area, inbox, habits, goals, notes."""
    user_id = _get_user_id(request)
    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)
    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request, "user_id": user_id, "page": "dashboard",
        "consciousness_active": _consciousness_active(request),
    })


@router.get("/me", response_class=HTMLResponse)
def me_page(request: Request, service: AlterService = Depends(get_service)):
    """Me — patterns, vitals, world model, memories."""
    user_id = _get_user_id(request)
    if not service.user_exists(user_id):
        return RedirectResponse(url="/setup", status_code=302)
    adapter = _get_adapter(request)
    status = service.get_status(user_id)

    # Get purpose for inline editor
    purpose = ""
    if adapter:
        purpose = adapter.user_model.purpose_statement or ""
    else:
        purpose = status.get("purpose", "") or ""

    # Get patterns
    patterns = []
    if adapter:
        try:
            cs = adapter.consciousness_state
            if hasattr(cs, 'world_model') and cs.world_model:
                for exp in cs.world_model.get_all_expectations():
                    patterns.append({
                        "domain": exp.domain,
                        "aspect": exp.aspect,
                        "description": exp.description,
                        "confidence": exp.confidence,
                    })
        except Exception:
            pass

    return templates.TemplateResponse("pages/me.html", {
        "request": request, "user_id": user_id, "page": "me",
        "consciousness_active": _consciousness_active(request),
        "status": status,
        "purpose": purpose,
        "patterns": patterns,
    })


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request):
    return templates.TemplateResponse("pages/init.html", {
        "request": request, "page": "setup"
    })


# ─── Today Partials ───


@router.get("/partials/today-narrative", response_class=HTMLResponse)
def today_narrative_partial(request: Request, service: AlterService = Depends(get_service)):
    adapter = _get_adapter(request)
    user_id = _get_user_id(request)
    today = datetime.now().date().isoformat()

    narrative = ""
    elevated_observations = []
    top_inbox_item = None
    focus_goals = []
    hours_since_checkin = None
    consciousness_active = False
    has_any_data = False

    if adapter:
        consciousness_active = adapter.is_running
        narrative = adapter.consciousness_state.narrative or ""
        has_any_data = bool(narrative) or bool(adapter.consciousness_state.inbox)

        # Get elevated observations from last 24h
        since = datetime.now() - timedelta(hours=24)
        all_obs = adapter.consciousness_state.get_observations_since(since)
        elevated_observations = [
            {"domain": o.domain, "aspect": o.aspect, "summary": o.summary, "severity": o.severity}
            for o in all_obs if o.severity != "normal"
        ][:3]

        # Get top inbox item by priority
        priority_order = ["notification", "decision", "goal_suggestion", "insight", "discovery"]
        pending = adapter.consciousness_state.get_pending_inbox()
        if pending:
            has_any_data = True
            sorted_items = sorted(
                pending,
                key=lambda i: priority_order.index(i.item_type) if i.item_type in priority_order else 99
            )
            top_inbox_item = sorted_items[0].to_dict()

        # Get short-horizon active goals (week/day)
        for g in adapter.user_model.get_active_goals():
            if g.time_horizon in ("week", "day"):
                focus_goals.append({
                    "id": g.id, "domain": g.domain, "description": g.description,
                    "time_horizon": g.time_horizon,
                })
                if len(focus_goals) >= 3:
                    break

        # Hours since last check-in
        daily = adapter.user_model.get_daily_data(today) if hasattr(adapter.user_model, 'get_daily_data') else {}
        if daily:
            hours_since_checkin = 0
        else:
            # Check previous days
            for days_ago in range(1, 8):
                prev_date = (datetime.now() - timedelta(days=days_ago)).date().isoformat()
                prev_data = adapter.user_model.get_daily_data(prev_date) if hasattr(adapter.user_model, 'get_daily_data') else {}
                if prev_data:
                    hours_since_checkin = days_ago * 24
                    break

    # Check data via service fallback
    if not has_any_data:
        try:
            daily = service.get_daily_data(user_id, today)
            if daily and any(daily.get(k) for k in ["health", "emotions"]):
                has_any_data = True
        except Exception:
            pass
        try:
            goals_data = service.list_goals(user_id, status="active")
            if goals_data.get("total", 0) > 0:
                has_any_data = True
                if not focus_goals:
                    for g in goals_data.get("goals", []):
                        if g.get("time_horizon") in ("week", "day"):
                            focus_goals.append(g)
                            if len(focus_goals) >= 3:
                                break
        except Exception:
            pass

    # Count active goals and habits for cold start progress
    active_goal_count = 0
    if adapter:
        active_goal_count = len(adapter.user_model.get_active_goals())
    else:
        try:
            active_goal_count = service.list_goals(user_id, status="active").get("total", 0)
        except Exception:
            pass

    return templates.TemplateResponse("partials/today_narrative.html", {
        "request": request,
        "narrative": narrative,
        "user_id": user_id,
        "greeting": _time_greeting(),
        "elevated_observations": elevated_observations,
        "top_inbox_item": top_inbox_item,
        "focus_goals": focus_goals,
        "hours_since_checkin": hours_since_checkin,
        "consciousness_active": consciousness_active,
        "has_any_data": has_any_data,
        "active_goal_count": active_goal_count,
    })


@router.get("/partials/today-actions", response_class=HTMLResponse)
def today_actions_partial(request: Request):
    """Curated top-5 inbox items for the Today page."""
    adapter = _get_adapter(request)
    items = []
    goal_names = {}
    remaining_count = 0

    if adapter:
        priority_order = ["notification", "decision", "goal_suggestion", "insight", "discovery"]
        pending = [i.to_dict() for i in adapter.consciousness_state.get_pending_inbox()]

        # Sort by priority
        sorted_items = sorted(
            pending,
            key=lambda i: priority_order.index(i.get("item_type", "")) if i.get("item_type") in priority_order else 99
        )
        items = sorted_items[:5]
        remaining_count = max(0, len(sorted_items) - 5)

        # Build goal name lookup
        for g in adapter.user_model.get_active_goals():
            goal_names[g.id] = g.description

    return templates.TemplateResponse("partials/today_actions.html", {
        "request": request, "items": items,
        "goal_names": goal_names, "remaining_count": remaining_count,
    })


@router.get("/partials/vitals", response_class=HTMLResponse)
def vitals_sparklines_partial(request: Request):
    """7-day vitals sparklines."""
    adapter = _get_adapter(request)
    vitals = {"sleep": [], "mood": [], "energy": [], "stress": [], "exercise": []}
    labels = []

    if adapter and hasattr(adapter.user_model, 'get_daily_data'):
        for days_ago in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=days_ago)).date()
            date_str = date.isoformat()
            labels.append(date.strftime("%a"))
            daily = adapter.user_model.get_daily_data(date_str) or {}
            health = daily.get("health", {})
            emotions = daily.get("emotions", {})
            vitals["sleep"].append(health.get("sleep_hours"))
            vitals["mood"].append(emotions.get("mood"))
            vitals["energy"].append(emotions.get("energy"))
            vitals["stress"].append(emotions.get("stress"))
            vitals["exercise"].append(health.get("exercise_minutes"))

    return templates.TemplateResponse("partials/vitals_sparklines.html", {
        "request": request, "vitals": vitals, "labels": labels,
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


# ─── Goals Partials ───


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
        "all_goals": goals,
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


# ─── Me Partials ───


@router.get("/partials/me-vitals", response_class=HTMLResponse)
def me_vitals_partial(request: Request):
    """Vitals + weekly averages for Me page."""
    adapter = _get_adapter(request)
    vitals = {"sleep": [], "mood": [], "energy": [], "stress": [], "exercise": []}
    averages = {}

    if adapter and hasattr(adapter.user_model, 'get_daily_data'):
        values = {"sleep": [], "mood": [], "energy": [], "stress": [], "exercise": []}
        for days_ago in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=days_ago)).date()
            daily = adapter.user_model.get_daily_data(d.isoformat()) or {}
            health = daily.get("health", {})
            emotions = daily.get("emotions", {})
            s = health.get("sleep_hours")
            vitals["sleep"].append(s)
            if s is not None: values["sleep"].append(s)
            m = emotions.get("mood")
            vitals["mood"].append(m)
            if m is not None: values["mood"].append(m)
            e = emotions.get("energy")
            vitals["energy"].append(e)
            if e is not None: values["energy"].append(e)
            st = emotions.get("stress")
            vitals["stress"].append(st)
            if st is not None: values["stress"].append(st)
            ex = health.get("exercise_minutes")
            vitals["exercise"].append(ex)
            if ex is not None: values["exercise"].append(ex)

        for key, vals in values.items():
            if vals:
                averages[key] = round(sum(vals) / len(vals), 1)

    return templates.TemplateResponse("partials/me_vitals.html", {
        "request": request, "vitals": vitals, "averages": averages,
    })


@router.get("/partials/me-patterns", response_class=HTMLResponse)
def me_patterns_partial(request: Request):
    """Patterns/expectations from world model for Me page."""
    adapter = _get_adapter(request)
    patterns = []
    if adapter:
        try:
            cs = adapter.consciousness_state
            if hasattr(cs, 'world_model') and cs.world_model:
                for exp in cs.world_model.get_all_expectations():
                    patterns.append({
                        "domain": exp.domain,
                        "aspect": exp.aspect,
                        "description": exp.description,
                        "confidence": exp.confidence,
                    })
        except Exception:
            pass
    return templates.TemplateResponse("partials/me_patterns.html", {
        "request": request, "patterns": patterns,
    })


@router.get("/partials/me-world-model", response_class=HTMLResponse)
def me_world_model_partial(request: Request):
    """World model expectations for Me page."""
    adapter = _get_adapter(request)
    expectations = []
    if adapter:
        try:
            cs = adapter.consciousness_state
            if hasattr(cs, 'world_model') and cs.world_model:
                for exp in cs.world_model.get_all_expectations():
                    expectations.append({
                        "domain": exp.domain,
                        "aspect": exp.aspect,
                        "description": exp.description,
                        "confidence": exp.confidence,
                        "numeric_value": getattr(exp, 'numeric_value', None),
                        "numeric_range": getattr(exp, 'numeric_range', None),
                    })
        except Exception:
            pass
    return templates.TemplateResponse("partials/me_world_model.html", {
        "request": request, "expectations": expectations,
    })


@router.get("/partials/me-memories", response_class=HTMLResponse)
def me_memories_partial(request: Request, category: str = "", service: AlterService = Depends(get_service)):
    """Memories for Me page with optional category filter."""
    user_id = _get_user_id(request)
    memories = service.get_parsed_memories(user_id)
    if category:
        memories = [m for m in memories if m.get("category") == category]
    # Get unique categories for filter
    categories = sorted(set(m.get("category", "general") for m in memories))
    return templates.TemplateResponse("partials/me_memories.html", {
        "request": request, "memories": memories, "categories": categories,
        "active_category": category,
    })


# ─── Dashboard Partials ───


@router.get("/partials/dashboard-goals", response_class=HTMLResponse)
def dashboard_goals_partial(request: Request, service: AlterService = Depends(get_service)):
    """Compact goal list for dashboard."""
    user_id = _get_user_id(request)
    goals_data = service.list_goals(user_id, status="active")
    goals = goals_data.get("goals", [])
    return templates.TemplateResponse("partials/dashboard_goals.html", {
        "request": request, "goals": goals,
    })


@router.get("/partials/dashboard-actions", response_class=HTMLResponse)
def dashboard_actions_partial(request: Request):
    """Recent activity for dashboard."""
    adapter = _get_adapter(request)
    activity = []
    if adapter:
        raw = adapter.get_activity(limit=20)
        for item in raw:
            if isinstance(item, dict):
                activity.append(item)
    return templates.TemplateResponse("partials/dashboard_actions.html", {
        "request": request, "activity": activity,
    })


@router.get("/partials/constitution-editor", response_class=HTMLResponse)
def constitution_editor_partial(request: Request, service: AlterService = Depends(get_service)):
    """Constitution editor partial for Settings page."""
    constitution = service.get_constitution()
    return templates.TemplateResponse("partials/constitution_editor.html", {
        "request": request, "constitution": constitution,
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
