"""Consciousness API — Endpoints for the thought stream and engine control."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/consciousness")


def _get_adapter(request: Request):
    """Get the consciousness adapter from app state."""
    adapter = getattr(request.app.state, "consciousness", None)
    if adapter is None:
        raise HTTPException(
            status_code=503,
            detail="Consciousness engine not running. Start server with --consciousness flag.",
        )
    return adapter


class TickRequest(BaseModel):
    tick_type: str = "daily_review"
    context: Optional[str] = None


@router.get("/status")
def consciousness_status(request: Request):
    """Get consciousness engine status."""
    adapter = _get_adapter(request)
    return adapter.get_status()


@router.get("/activity")
def consciousness_activity(request: Request, limit: int = 50):
    """Get recent consciousness activity (thought stream)."""
    adapter = _get_adapter(request)
    return {"activity": adapter.get_activity(limit=limit)}


@router.get("/notifications")
def consciousness_notifications(request: Request):
    """Get pending notifications from the consciousness engine."""
    adapter = _get_adapter(request)
    notifications = adapter.consciousness_state.get_pending_notifications()
    return {"notifications": notifications}


@router.get("/narrative")
def consciousness_narrative(request: Request):
    """Get current narrative — the unified story of the user's life."""
    adapter = _get_adapter(request)
    return {"narrative": adapter.consciousness_state.narrative}


@router.get("/world-model")
def consciousness_world_model(request: Request):
    """Get current world model expectations."""
    adapter = _get_adapter(request)
    wm = adapter.consciousness_state.world_model
    expectations = {}
    for domain in wm.get_domains():
        domain_exps = wm.get_domain_expectations(domain)
        expectations[domain] = [e.to_dict() for e in domain_exps]
    return {"domains": wm.get_domains(), "expectations": expectations}


@router.post("/tick")
async def consciousness_tick(request: Request, body: TickRequest):
    """Manually trigger a consciousness tick."""
    adapter = _get_adapter(request)
    valid_types = ["daily_review", "weekly_reflect", "monthly_deep", "urgent",
                    "goal_analysis", "discovery"]
    if body.tick_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tick_type. Must be one of: {valid_types}",
        )
    result = await adapter.trigger_tick(body.tick_type, context=body.context)
    if result is None:
        return {"status": "completed", "result": None, "detail": "Tick ran but parse failed"}
    return {
        "status": "completed",
        "observations": len(result.observations),
        "insights": len(result.insights),
        "decisions": len(result.decisions),
        "notifications": len(result.notifications),
        "goal_analyses": len(result.goal_analyses),
        "discoveries": len(result.discoveries),
    }


@router.post("/observe")
async def consciousness_observe(request: Request):
    """Manually trigger hourly observation (pre-attentive, no LLM)."""
    adapter = _get_adapter(request)
    observations = await adapter.trigger_observe()
    return {
        "observation_count": len(observations),
        "observations": [
            {
                "domain": o.domain,
                "aspect": o.aspect,
                "severity": o.severity,
                "summary": o.summary,
                "prediction_error": o.prediction_error,
            }
            for o in observations
        ],
    }


@router.get("/questions")
def consciousness_questions(request: Request):
    """Get dormant questions with full detail and readiness."""
    adapter = _get_adapter(request)
    state = adapter.consciousness_state
    unresolved = state.get_unresolved_questions()
    ready = state.get_ready_questions()
    return {
        "total_unresolved": len(unresolved),
        "ready_count": len(ready),
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "domain": q.domain,
                "context": q.context,
                "readiness": round(q.readiness, 2),
                "threshold": q.threshold,
                "ready": q.is_ready(),
                "resolution_signals": q.resolution_signals,
                "created_at": q.created_at,
            }
            for q in unresolved
        ],
    }


@router.get("/observations")
def consciousness_observations(request: Request, limit: int = 20):
    """Get recent observations with prediction errors."""
    adapter = _get_adapter(request)
    state = adapter.consciousness_state
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(hours=48)
    observations = state.get_observations_since(since)
    obs_list = sorted(observations, key=lambda o: o.timestamp, reverse=True)[:limit]
    return {
        "observation_count": len(obs_list),
        "observations": [
            {
                "id": o.id,
                "domain": o.domain,
                "aspect": o.aspect,
                "expected": o.expected,
                "observed": o.observed,
                "prediction_error": o.prediction_error,
                "severity": o.severity,
                "summary": o.summary,
                "timestamp": o.timestamp,
            }
            for o in obs_list
        ],
    }


@router.get("/skills")
def consciousness_skills(request: Request):
    """Get registered skills and their metadata."""
    adapter = _get_adapter(request)
    registry = adapter.skill_registry
    skills = []
    for info in registry.list_skills():
        skills.append({
            "name": info.name,
            "description": info.description,
            "domains": info.domains,
            "metrics": [
                {"name": m.name, "description": m.description, "unit": m.unit}
                for m in info.metrics
            ],
            "version": info.version,
        })
    return {"skills": skills, "domains": registry.domains}


@router.post("/skills/{skill_name}/collect")
async def consciousness_skill_collect(request: Request, skill_name: str):
    """Manually collect data from a specific skill."""
    adapter = _get_adapter(request)
    try:
        data = await adapter.skill_registry.collect_skill(skill_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")
    return {"skill": skill_name, "data": data}


# ------------------------------------------------------------------
# Thought Loop Configuration
# ------------------------------------------------------------------


@router.get("/loops")
def list_thought_loops(request: Request):
    """Get all thought loop configurations."""
    adapter = _get_adapter(request)
    return {"loops": adapter.get_thought_loops()}


class LoopUpdate(BaseModel):
    enabled: bool


@router.put("/loops/{loop_id}")
def update_thought_loop(request: Request, loop_id: str, body: LoopUpdate):
    """Enable or disable a thought loop."""
    adapter = _get_adapter(request)
    result = adapter.update_thought_loop(loop_id, enabled=body.enabled)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Loop not found: {loop_id}")
    return {"loop_id": loop_id, **result}
